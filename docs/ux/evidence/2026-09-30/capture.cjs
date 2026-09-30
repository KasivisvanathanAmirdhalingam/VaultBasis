const {chromium} = require('playwright');
const fs = require('fs');
const out = process.env.VB_AUDIT_OUTPUT;
if (!out || fs.existsSync(out)) throw new Error('Set VB_AUDIT_OUTPUT to a new directory; existing evidence must not be overwritten.');
const routes = ['/', '/trust-assurance', '/about', '/contact', '/verifier-access', '/verifier', '/privacy-policy', '/terms-of-service', '/security-disclosure', '/docs/scope_and_limitations_v0.1.html', '/faq', '/ux-audit-missing-page'];
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true});
 const results=[];
 for(const width of [1440,390]) {
  const context=await browser.newContext({viewport:{width,height:900}});
  for(const route of routes){
   const page=await context.newPage(); const errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   page.on('console',m=>{if(m.type()==='error') errors.push(m.text());});
   const id=(route==='/'?'home':route.replaceAll('/','_').replaceAll('.','_'))+'-'+width;
   try{
    const response=await page.goto('https://vaultbasis.com'+route,{waitUntil:'networkidle',timeout:30000});
    const observation=await page.evaluate(()=>({title:document.title,headings:[...document.querySelectorAll('h1,h2,h3')].map(e=>e.textContent.trim()),links:[...document.querySelectorAll('a')].map(e=>({text:e.textContent.trim(),href:e.getAttribute('href')})),buttons:[...document.querySelectorAll('button')].map(e=>e.textContent.trim()),horizontalOverflow:document.documentElement.scrollWidth>innerWidth,build:document.documentElement.outerHTML.match(/VaultBasis Build:[^<]*/)?.[0]||null}));
    await page.screenshot({path:out+'/'+id+'.png',fullPage:true});
    results.push({route,width,status:response.status(),url:page.url(),...observation,errors,screenshot:id+'.png'});
    if(route==='/'&&width===1440){
      await page.getByRole('button',{name:'Request Design-Partner Access',exact:true}).first().click();
      await page.waitForTimeout(100);
      const focus=[];
      for(let i=0;i<8;i++){focus.push(await page.evaluate(()=>({id:document.activeElement.id,text:document.activeElement.textContent.trim().slice(0,70),inDialog:!!document.activeElement.closest('[role="dialog"]')})));await page.keyboard.press('Tab');}
      await page.screenshot({path:out+'/access-open-1440.png',fullPage:false});
      await page.keyboard.press('Escape');
      results.push({route:'access-modal',width,focus,focusAfterEscape:await page.evaluate(()=>({id:document.activeElement.id,tag:document.activeElement.tagName,text:document.activeElement.textContent.trim().slice(0,70)}))});
    }
   }catch(e){results.push({route,width,error:e.message});}
   await page.close();
  }
  await context.close();
 }
 fs.writeFileSync(out+'/production-observations.json',JSON.stringify({capturedAt:new Date().toISOString(),browser:browser.version(),boundary:'Live public URLs; anonymous; read-only; no form submissions',results},null,2));
 await browser.close();
 console.log(JSON.stringify(results.map(({route,width,status,url,horizontalOverflow,error,focus,focusAfterEscape,build})=>({route,width,status,url,horizontalOverflow,error,focus,focusAfterEscape,build})),null,2));
})().catch(e=>{console.error(e);process.exit(1)});
