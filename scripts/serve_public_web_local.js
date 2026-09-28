const express = require('express');
const path = require('path');
const app = express();

app.use(express.json());

const DIST_DIR = path.join(__dirname, '..', 'dist', 'public-web');

// Mock Vercel API Routes
app.post('/api/request-access', (req, res) => {
    require(path.join(DIST_DIR, 'api', 'request-access.js'))(req, res);
});

app.get('/api/download', (req, res) => {
    require(path.join(DIST_DIR, 'api', 'download.js'))(req, res);
});

// Serve the static frontend
app.use(express.static(DIST_DIR));

// Fallback to 404
app.use((req, res) => {
    res.status(404).sendFile(path.join(DIST_DIR, '404.html'));
});

const PORT = 3000;
app.listen(PORT, () => {
    console.log(`=======================================================`);
    console.log(` Marketing Portal (Local UAT) running at:`);
    console.log(` http://localhost:${PORT}`);
    console.log(`=======================================================`);
});
