// server.js
const express = require('express');
const app = express();

const fs = require('fs');

// Fetch the dynamic flag from /flag.txt (written by entrypoint.sh) or process.env.FLAG
let FLAG;
try {
  FLAG = fs.readFileSync('/flag.txt', 'utf8').trim();
} catch (err) {
  FLAG = process.env.FLAG || "NECROX{DEFAULT_FALLBACK_FLAG_FOR_LOCAL_DEV}";
}
const PORT = process.env.PORT || 80;

app.get('/', (req, res) => {
  res.send(`
    <html>
      <head><title>Secure Vault Challenge</title></head>
      <body style="font-family: sans-serif; background: #0f172a; color: #f8fafc; text-align: center; padding-top: 50px;">
        <h1>Welcome to the Cyberanzen Vault</h1>
        <p>Can you exploit the secret endpoint to get the flag?</p>
        <!-- Secret debugging endpoint: /api/secret -->
      </body>
    </html>
  `);
});

// Vulnerable / target endpoint that exposes or requires exploitation to reach
app.get('/api/secret', (req, res) => {
  res.json({
    message: "Vault access granted!",
    flag: FLAG
  });
});

app.listen(PORT, () => {
  console.log(`[Challenge] Server listening on port ${PORT}`);
  console.log(`[Challenge] Loaded flag: ${FLAG}`);
});
