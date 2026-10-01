const blob = require('@vercel/blob');

module.exports = exports = async function (req, res) {
  try {
    const config = { pathname: `test-blob-${Date.now()}.json` };
    
    // 1. Create
    await blob.put(config.pathname, JSON.stringify({ version: 1 }), {
      access: 'private', contentType: 'application/json', addRandomSuffix: false, allowOverwrite: true,
    });

    // 2. Read
    const getRes = await blob.get(config.pathname, { access: 'private', useCache: false });
    const etag = getRes.blob.etag;

    let results = [];

    // 3. Update without explicit allowOverwrite
    try {
      await blob.put(config.pathname, JSON.stringify({ version: 2 }), {
        access: 'private', contentType: 'application/json', addRandomSuffix: false,
        ifMatch: etag,
      });
      results.push('SUCCESS_NO_OVERWRITE');
    } catch (err) {
      results.push(`FAIL_NO_OVERWRITE: ${err.name} - ${err.message}`);
    }

    // 4. Read again
    const getRes2 = await blob.get(config.pathname, { access: 'private', useCache: false });
    const etag2 = getRes2.blob.etag;

    // 5. Update WITH explicit allowOverwrite: true
    try {
      await blob.put(config.pathname, JSON.stringify({ version: 3 }), {
        access: 'private', contentType: 'application/json', addRandomSuffix: false,
        ifMatch: etag2, allowOverwrite: true,
      });
      results.push('SUCCESS_WITH_OVERWRITE');
    } catch (err) {
      results.push(`FAIL_WITH_OVERWRITE: ${err.name} - ${err.message}`);
    }

    res.status(200).json({ results, etag1: etag, etag2: etag2 });
  } catch (err) {
    res.status(500).json({ error: err.message, stack: err.stack });
  }
};
