'use strict';
const { test, beforeEach } = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('crypto');
const Module = require('module');
const originalLoad = Module._load;
let records, version, fail, unknown;
const storage = {
  async get(path, options) {
    assert.equal(options.access, 'private');
    const entry = records.get(path);
    if (!entry) return null;
    return { stream: new ReadableStream({ start(c) { c.enqueue(Buffer.from(entry.body)); c.close(); } }), blob: { etag: entry.etag } };
  },
  async put(path, body, options) {
    assert.equal(options.access, 'private');
    if (fail) throw new Error('sensitive-storage-error@example.invalid');
    const current = records.get(path);
    if (options.ifMatch ? current?.etag !== options.ifMatch : current && options.allowOverwrite === false) throw new Error('precondition');
    records.set(path, { body, etag: String(++version) });
    if (unknown) { unknown = false; throw new Error('write completed but response lost'); }
    return { pathname: path };
  },
};
Module._load = function(name, ...args) { if (name === '@vercel/blob') return storage; if (name === 'nodemailer') throw new Error('SMTP must never be loaded'); return originalLoad.call(this, name, ...args); };
const store = require('../../api/access-request-store');
const handler = require('../../api/request-access');
const operator = require('../../scripts/lib/manual-provisioning');
const preview = require('../../api/preview-access-store');
const entitlement = require('../../api/entitlement-store');
const input = (email = 'reviewer@example.invalid') => ({ name: 'Synthetic Reviewer', email, context: 'Evaluate sample', requestId: crypto.randomUUID() });
function response() { return { headers: {}, setHeader(k,v) { this.headers[k]=v; }, status(s) { this.code=s; return this; }, json(b) { this.body=b; return this; } }; }
async function call(body, headers = {}) { const res=response(); await handler({method:'POST',body,headers:{'content-type':'application/json',...headers},socket:{remoteAddress:'192.0.2.1'}},res);return res; }
beforeEach(() => { records=new Map();version=0;fail=false;unknown=false;process.env.ACCESS_REQUEST_NAMESPACE='test-only';process.env.ACCESS_REQUEST_SECRET='x'.repeat(64);process.env.PUBLIC_BASE_URL='https://preview.example.invalid';delete process.env.VERCEL; });
test('durably records pending request and grants no capability', async () => {
 const res=await call(input());assert.equal(res.code,202);assert.deepEqual(res.body,{status:'pending_review'});
 const {data}=await store.read();assert.equal(data.requests.length,1);assert.equal(data.requests[0].state,'PENDING_REVIEW');
 assert.equal([...records.keys()].filter(k=>!k.startsWith('access-requests/')).length,0);
 assert.ok(!JSON.stringify(data).includes('192.0.2.1'));assert.ok(!JSON.stringify(data).includes('marketing'));
});
test('same retry and lost write acknowledgement create one request', async()=>{
 const body=input();unknown=true;assert.equal((await call(body)).code,202);assert.equal((await call(body)).code,202);
 assert.equal((await store.read()).data.requests.length,1);
 assert.equal((await call({...body,name:'Changed'})).code,409);
});
test('duplicate address does not overwrite original or grant access',async()=>{
 await call(input());await call({...input(),name:'Different'});const {data}=await store.read();assert.equal(data.requests.length,1);assert.equal(data.requests[0].name,'Synthetic Reviewer');
});
test('concurrent requests enforce shared IP budget without lost records',async()=>{
 const results=await Promise.all(Array.from({length:8},(_,i)=>call(input(`reviewer${i}@example.invalid`))));
 assert.equal(results.filter(r=>r.code===202).length,5);assert.equal((await store.read()).data.requests.length,5);
 assert.ok(results.every(r=>[202,429,503].includes(r.code)));
});
test('email and global budgets survive changed network identity',async()=>{
 const body=input();await store.submit(body,'a');await store.submit(input(),'b');assert.equal((await store.submit(input(),'c')).code,429);
 await store.transact(data=>{data.limits.global={count:60,until:Date.now()+10000};});assert.equal((await store.submit(input('new@example.invalid'),'d')).code,429);
});
test('malformed input denied before storage and API methods bounded',async()=>{
 for(const body of [null,{}, { ...input(),email:'no-at' }, {...input(),name:'x'.repeat(201)}, {...input(),context:'x'.repeat(501)}, {...input(),context:'a\nb'}, {...input(),requestId:'bad'}]) assert.equal((await call(body)).code,400);
 assert.equal(records.size,0);assert.equal((await call(input(),{'content-type':'text/plain'})).code,415);
 const res=response();await handler({method:'GET'},res);assert.equal(res.code,405);
});
test('storage/config failures do not leak data or pretend success',async()=>{
 fail=true;let logs=[];const old=console.error;console.error=(s)=>logs.push(s);
 try{assert.equal((await call(input())).code,503);delete process.env.ACCESS_REQUEST_SECRET;assert.equal((await call(input())).code,503);}finally{console.error=old;}
 assert.ok(logs.every(s=>s==='[access-request] storage_or_configuration_unavailable'));assert.equal(records.size,0);
});
test('platform identity required; spoofed generic forwarding headers ignored',async()=>{
 process.env.VERCEL='1';const old=console.error;console.error=()=>{};
 try{assert.equal((await call(input(),{'x-forwarded-for':'192.0.2.2'})).code,503);}finally{console.error=old;}
 assert.equal((await call(input(),{'x-vercel-forwarded-for':'192.0.2.2'})).code,202);
});
test('manual preview approval creates only preview credential and records operator',async()=>{
 await call(input());const id=(await store.read()).data.requests[0].id;let packet;
 const issued=await operator.issue({id,operator:'test-operator'},async p=>{packet=p;});
 assert.equal(packet.state,'PREPARED_NOT_DELIVERED');assert.equal(issued.state,'ISSUED_NOT_DELIVERED');
 assert.equal((await preview.validatePreviewAccess(issued.token,issued.accessId)).ok,true);
 assert.equal((await entitlement.validateEntitlement(issued.token,issued.accessId,'a'.repeat(64))).ok,false);
 assert.equal((await store.read()).data.requests[0].grants[0].operator,'test-operator');
 await assert.rejects(operator.issue({id,operator:'test-operator'},async()=>{}));
 await operator.revoke(id,'test-operator');assert.equal((await preview.validatePreviewAccess(issued.token,issued.accessId)).ok,false);
});
test('unqualified artifact cannot be issued even by manual approval',async()=>{
 await call(input());const id=(await store.read()).data.requests[0].id;
 await assert.rejects(operator.issue({id,operator:'test-operator',platform:'mac-arm64',qualification:{state:'BUILD_VERIFIED'}},async()=>{}));
 assert.equal((await store.read()).data.requests[0].state,'PENDING_REVIEW');
});
test('retention removes aged requests and expired rate keys on purge',async()=>{
 await call(input());await store.transact(data=>{data.requests[0].createdAt=new Date(Date.now()-91*86400000).toISOString();data.limits.old={count:1,until:1};});
 await store.transact(()=>null);assert.equal((await store.read()).data.requests.length,0);assert.equal((await store.read()).data.limits.old,undefined);
});
