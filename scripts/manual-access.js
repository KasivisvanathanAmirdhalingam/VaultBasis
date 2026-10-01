#!/usr/bin/env node
'use strict';
// Trusted operator workstation only. No public admin endpoint, no email sending.
const fs = require('fs');
const intake = require('../api/access-request-store');
const { issue, revoke } = require('./lib/manual-provisioning');
async function main() {
  const [command, ...args] = process.argv.slice(2);
  const options = {};
  for (let i = 0; i < args.length; i += 2) {
    if (!args[i].startsWith('--') || !args[i + 1]) throw new Error('Invalid options');
    options[args[i].slice(2)] = args[i + 1];
  }
  if (command === 'purge') { await intake.transact(() => null); return; }
  if (command === 'revoke') { await revoke(options.id, options.operator); return; }
  if (!['review', 'approve-preview', 'approve-artifact'].includes(command) || !options.out) throw new Error('Use review --out FILE; approve-preview --id ID --operator NAME --out FILE; approve-artifact adds --platform PLATFORM --qualification FILE; revoke --id ID --operator NAME; purge');
  // Exclusive creation prevents overwriting a previous credential packet.
  const fd = fs.openSync(options.out, 'wx', 0o600);
  function save(data) { fs.ftruncateSync(fd, 0); fs.writeSync(fd, JSON.stringify(data, null, 2) + '\n', 0, 'utf8'); fs.fsyncSync(fd); }
  try {
    if (command === 'review') {
      const { data } = await intake.read();
      save({ requests: data.requests.map(({ retryKey, fingerprint, ...request }) => request) });
    } else {
      if (command === 'approve-artifact' && (!options.platform || !options.qualification)) throw new Error('Platform and exact qualification record required');
      const packet = await issue({ id: options.id, operator: options.operator,
        ...(command === 'approve-artifact' ? { platform: options.platform, qualification: JSON.parse(fs.readFileSync(options.qualification, 'utf8')) } : {}) }, save);
      save(packet);
    }
  } finally { fs.closeSync(fd); }
}
if (require.main === module) main().catch(() => {
  console.error('Manual access operation incomplete. Keep any private output packet; inspect the request state before retrying. No delivery was performed.');
  process.exitCode = 1;
});
module.exports = { main };
