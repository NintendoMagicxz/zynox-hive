// ZynoX Jarvis — Master Server
// Reads everything from .env
// Run: node server.js

const http  = require('http');
const https = require('https');
const fs    = require('fs');
const path  = require('path');

// ── Load .env ─────────────────────────────────────────────────────────────────
const envPath = path.join(__dirname, '.env');
const env = {};
if (fs.existsSync(envPath)) {
  fs.readFileSync(envPath, 'utf-8').split('\n').forEach(line => {
    line = line.trim();
    if (!line || line.startsWith('#')) return;
    const idx = line.indexOf('=');
    if (idx < 0) return;
    const key = line.slice(0, idx).trim();
    const val = line.slice(idx + 1).trim();
    env[key] = val;
  });
}

// ── Config from .env ──────────────────────────────────────────────────────────
const PASSWORD    = env.ZYNOX_PASSWORD    || 'ZynoX123';
const API_KEY     = env.ANTHROPIC_API_KEY || '';
const ZAPIER_URL  = env.ZAPIER_WEBHOOK_URL || '';
const TG_TOKEN    = env.TELEGRAM_BOT_TOKEN || '';
const TG_CHAT     = env.TELEGRAM_CHAT_ID   || '';
const SHEET_ID    = env.GOOGLE_SHEET_ID    || '';
const GOOGLE_KEY  = env.GOOGLE_CLIENT_SECRET || '';
const PORT        = 3131;
const sessions    = new Set();

// ── Load agents from .env ─────────────────────────────────────────────────────
const agents = [];
let i = 1;
while (env[`AGENT_${i}_NAME`]) {
  agents.push({
    name:  env[`AGENT_${i}_NAME`],
    role:  env[`AGENT_${i}_ROLE`],
    model: env[`AGENT_${i}_MODEL`] || 'claude-sonnet-4-20250514'
  });
  i++;
}

// ── Startup check ─────────────────────────────────────────────────────────────
console.log('\n  ╔══════════════════════════════════════════╗');
console.log('  ║     ZynoX Jarvis — Master Server         ║');
console.log('  ╚══════════════════════════════════════════╝\n');
console.log('  Config loaded from .env:');
console.log('  API Key:    ' + (API_KEY    ? 'OK' : 'MISSING'));
console.log('  Zapier:     ' + (ZAPIER_URL ? 'OK' : 'not set'));
console.log('  Telegram:   ' + (TG_TOKEN   ? 'OK' : 'not set'));
console.log('  Google:     ' + (SHEET_ID   ? 'OK' : 'not set'));
console.log('  Agents:     ' + agents.length + ' loaded');
console.log('\n  Open: http://localhost:' + PORT + '\n');

if (!API_KEY) {
  console.log('  ERROR: ANTHROPIC_API_KEY missing from .env\n');
  process.exit(1);
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function makeToken() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function httpsPost(hostname, path, headers, body) {
  return new Promise((resolve, reject) => {
    const data = typeof body === 'string' ? body : JSON.stringify(body);
    const opts = {
      hostname, path, method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data), ...headers }
    };
    const req = https.request(opts, res => {
      let result = '';
      res.on('data', c => result += c);
      res.on('end', () => resolve({ status: res.statusCode, body: result }));
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

// ── Integrations ──────────────────────────────────────────────────────────────

// Send to Zapier webhook
async function sendToZapier(data) {
  if (!ZAPIER_URL) return;
  try {
    const url = new URL(ZAPIER_URL);
    await httpsPost(url.hostname, url.pathname + url.search, {}, data);
    console.log('  Zapier: sent');
  } catch (e) {
    console.log('  Zapier error:', e.message);
  }
}

// Send Telegram message to Tim
async function sendTelegram(text) {
  if (!TG_TOKEN || !TG_CHAT) return;
  try {
    await httpsPost(
      'api.telegram.org',
      `/bot${TG_TOKEN}/sendMessage`,
      {},
      { chat_id: TG_CHAT, text, parse_mode: 'Markdown' }
    );
    console.log('  Telegram: sent');
  } catch (e) {
    console.log('  Telegram error:', e.message);
  }
}

// Log to local JSON file (always works, no setup needed)
function logToFile(entry) {
  const logPath = path.join(__dirname, 'zynox_log.json');
  let log = [];
  try { log = JSON.parse(fs.readFileSync(logPath, 'utf-8')); } catch {}
  log.push(entry);
  fs.writeFileSync(logPath, JSON.stringify(log, null, 2));
}

// ── Claude API call ───────────────────────────────────────────────────────────
async function callClaude(system, user, model) {
  const data = JSON.stringify({
    model: model || 'claude-sonnet-4-20250514',
    max_tokens: 600,
    system,
    messages: [{ role: 'user', content: user }]
  });
  const res = await httpsPost('api.anthropic.com', '/v1/messages', {
    'x-api-key': API_KEY,
    'anthropic-version': '2023-06-01'
  }, data);
  const parsed = JSON.parse(res.body);
  if (res.status !== 200) throw new Error(parsed.error?.message || 'API error ' + res.status);
  return parsed.content[0].text.trim();
}

// ── HTTP Server ───────────────────────────────────────────────────────────────
const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, x-session-token');

  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

  function readBody(cb) {
    let body = '';
    req.on('data', c => body += c);
    req.on('end', () => { try { cb(JSON.parse(body)); } catch { res.writeHead(400); res.end(); } });
  }

  function json(code, data) {
    res.writeHead(code, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(data));
  }

  function authCheck() {
    const token = req.headers['x-session-token'];
    if (!token || !sessions.has(token)) {
      json(401, { error: { message: 'Not authenticated' } });
      return false;
    }
    return true;
  }

  // LOGIN
  if (req.method === 'POST' && req.url === '/api/login') {
    readBody(({ password }) => {
      if (password === PASSWORD) {
        const token = makeToken();
        sessions.add(token);
        json(200, { ok: true, token });
      } else {
        json(401, { ok: false, error: 'Wrong password' });
      }
    });
    return;
  }

  // STATUS — what's connected
  if (req.method === 'GET' && req.url === '/api/status') {
    json(200, {
      zapier:   !!ZAPIER_URL,
      telegram: !!(TG_TOKEN && TG_CHAT),
      google:   !!SHEET_ID,
      agents:   agents.map(a => ({ name: a.name, role: a.role })),
      version:  '2.0'
    });
    return;
  }

  // AI CHAT — single agent call
  if (req.method === 'POST' && req.url === '/api/chat') {
    if (!authCheck()) return;
    readBody(async ({ system, user, model }) => {
      try {
        const result = await callClaude(system, user, model);
        json(200, { result });
      } catch (e) {
        json(500, { error: { message: e.message } });
      }
    });
    return;
  }

  // HIVE RUN — full 6-agent pipeline with auto-save
  if (req.method === 'POST' && req.url === '/api/hive') {
    if (!authCheck()) return;
    readBody(async ({ objective, mode }) => {
      const modeHint = {
        post:   'Output must be an X post under 280 chars.',
        reply:  'Output must be an X reply under 220 chars.',
        pitch:  'Output must be a DM pitch under 320 chars.',
        thread: 'Output must be a 4-post X thread, numbered, each under 280 chars.',
        free:   'Output format is open.'
      }[mode] || '';

      const HIVE = [
        { id:'scout',      sys:'You are Scout. Analyse the topic: find the sharpest angle, the tension, why Elon Musk would care. Output 3 bullet points max.' },
        { id:'strategist', sys:'You are Strategist. Given topic and Scout research, define best content strategy: format, hook, outcome. 3 bullets max.' },
        { id:'writer',     sys:'You are Writer. Write the content based on strategy. Bold, crisp, no filler. Respect character limits.' },
        { id:'edge',       sys:'You are Edge. Make the draft 30% bolder, more memorable. Cut weak words. Output improved version only.' },
        { id:'nintendo',   sys:'You are Nintendo — Tim Cato Nintendo Henriksen brand voice. Inject his voice: creative, bold, visionary. Output final version only.' },
        { id:'judge',      sys:'You are Judge. Score: Hook/10, Elon/10, Brand/10, Viral/10. PASS or REVISE. Respond ONLY with JSON: {"hook":8,"elon":9,"brand":8,"viral":7,"verdict":"PASS","feedback":"..."}' },
      ];

      const results = {};
      try {
        for (const agent of HIVE) {
          let prompt = '';
          if (agent.id === 'scout')      prompt = `Topic: ${objective}\nFormat: ${modeHint}\nAnalyse.`;
          if (agent.id === 'strategist') prompt = `Topic: ${objective}\nScout:\n${results.scout}\nBuild strategy.`;
          if (agent.id === 'writer')     prompt = `Topic: ${objective}\nStrategy:\n${results.strategist}\n${modeHint}\nWrite it.`;
          if (agent.id === 'edge')       prompt = `Draft:\n${results.writer}\n${modeHint}\nMake it bolder.`;
          if (agent.id === 'nintendo')   prompt = `Content:\n${results.edge}\nBrand: Tim Cato Nintendo Henriksen — bold, visionary, unconventional.`;
          if (agent.id === 'judge')      prompt = `Objective: ${objective}\nFinal:\n${results.nintendo}\nScore and judge. JSON only.`;
          results[agent.id] = await callClaude(agent.sys, prompt);
        }

        const entry = {
          timestamp: new Date().toISOString(),
          objective, mode,
          final: results.nintendo || '',
          judge: results.judge || '',
          results
        };

        // Save locally always
        logToFile(entry);

        // Send to Zapier (saves to Google Sheets/Docs via Zapier)
        await sendToZapier({
          timestamp: entry.timestamp,
          objective, mode,
          final: results.nintendo,
          judge: results.judge
        });

        // Notify Tim on Telegram
        await sendTelegram(
          `*ZynoX Hive complete*\n\n*Objective:* ${objective}\n*Mode:* ${mode}\n\n${results.nintendo}`
        );

        json(200, { results });
      } catch (e) {
        json(500, { error: { message: e.message } });
      }
    });
    return;
  }

  // HISTORY — return local log
  if (req.method === 'GET' && req.url === '/api/history') {
    try {
      const log = JSON.parse(fs.readFileSync(path.join(__dirname, 'zynox_log.json'), 'utf-8'));
      json(200, log.slice(-20).reverse());
    } catch {
      json(200, []);
    }
    return;
  }

  // SERVE FILES
  const file = (req.url === '/' || req.url === '/index.html') ? 'index.html' : req.url.slice(1);
  fs.readFile(path.join(__dirname, file), (err, content) => {
    if (err) { res.writeHead(404); res.end('Not found'); return; }
    res.writeHead(200);
    res.end(content);
  });
});

server.listen(PORT);
