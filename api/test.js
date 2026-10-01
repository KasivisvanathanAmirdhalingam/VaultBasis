const store = require('./access-request-store.js');
const blob = require('@vercel/blob');

module.exports = exports = async function (req, res) {
  try {
    const { data, etag } = await store.read();
    let results = [];

    const strippedEtag = etag ? etag.replace(/^W\//, '') : etag;

    // 1. Try to put with stripped etag
    try {
      await blob.put(`access-requests/${process.env.ACCESS_REQUEST_NAMESPACE}/ledger.json`, JSON.stringify(data), {
        access: 'private', contentType: 'application/json', addRandomSuffix: false,
        ifMatch: strippedEtag,
      });
      results.push('SUCCESS_STRIPPED');
    } catch (err) {
      results.push(`FAIL_STRIPPED: ${err.name} - ${err.message}`);
    }

    res.status(200).json({ 
      results, 
      namespace: process.env.ACCESS_REQUEST_NAMESPACE,
      etag1: etag, 
      strippedEtag
    });
  } catch (err) {
    res.status(500).json({ error: err.message, stack: err.stack });
  }
};
