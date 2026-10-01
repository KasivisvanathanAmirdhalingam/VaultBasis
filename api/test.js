const store = require('./access-request-store.js');
const blob = require('@vercel/blob');

module.exports = exports = async function (req, res) {
  try {
    const { data, etag } = await store.read();
    let results = [];

    // 1. Try to put with current etag and NO explicit allowOverwrite
    try {
      await blob.put(`access-requests/${process.env.ACCESS_REQUEST_NAMESPACE}/ledger.json`, JSON.stringify(data), {
        access: 'private', contentType: 'application/json', addRandomSuffix: false,
        ifMatch: etag,
      });
      results.push('SUCCESS_NO_OVERWRITE');
    } catch (err) {
      results.push(`FAIL_NO_OVERWRITE: ${err.name} - ${err.message}`);
    }

    // 2. Read again
    const read2 = await store.read();
    
    // 3. Try to put WITH explicit allowOverwrite
    try {
      await blob.put(`access-requests/${process.env.ACCESS_REQUEST_NAMESPACE}/ledger.json`, JSON.stringify(read2.data), {
        access: 'private', contentType: 'application/json', addRandomSuffix: false,
        ifMatch: read2.etag, allowOverwrite: true,
      });
      results.push('SUCCESS_WITH_OVERWRITE');
    } catch (err) {
      results.push(`FAIL_WITH_OVERWRITE: ${err.name} - ${err.message}`);
    }

    res.status(200).json({ 
      results, 
      namespace: process.env.ACCESS_REQUEST_NAMESPACE,
      etag1: etag, 
      etag2: read2.etag 
    });
  } catch (err) {
    res.status(500).json({ error: err.message, stack: err.stack });
  }
};
