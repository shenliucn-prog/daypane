import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { openDb } from '../src/db.js';
import { createServer } from '../src/server.js';
import { config } from '../src/config.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const FIXTURE = join(__dirname, 'fixtures', 'workbuddy.db');

function listen(server) {
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server.address().port)));
}

test('/api/status returns JSON with token data', async () => {
  const db = openDb(FIXTURE);
  const server = createServer({ db, cfg: { ...config, cwdFilter: '' } });
  const port = await listen(server);
  try {
    const res = await fetch(`http://127.0.0.1:${port}/api/status`);
    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(body.ok, true);
    assert.equal(body.data.token.remaining, 900);
  } finally {
    server.close();
    db.close();
  }
});

test('/ returns an HTML page', async () => {
  const db = openDb(FIXTURE);
  const server = createServer({ db });
  const port = await listen(server);
  try {
    const res = await fetch(`http://127.0.0.1:${port}/`);
    assert.equal(res.status, 200);
    const html = await res.text();
    assert.match(html, /DayPane/i);
  } finally {
    server.close();
    db.close();
  }
});

test('/api/dashboard returns aggregated payload', async () => {
  const db = openDb(FIXTURE);
  const server = createServer({ db });
  const port = await listen(server);
  try {
    const res = await fetch(`http://127.0.0.1:${port}/api/dashboard`);
    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(body.ok, true);
    assert.ok(body.quotas && body.quotas.workbuddy);
    assert.ok(Array.isArray(body.clocks.items));
    assert.ok(body.stocks && Array.isArray(body.stocks.items));
  } finally {
    server.close();
    db.close();
  }
});

test('unknown route returns 404', async () => {
  const server = createServer({ db: null });
  const port = await listen(server);
  try {
    const res = await fetch(`http://127.0.0.1:${port}/nope`);
    assert.equal(res.status, 404);
  } finally {
    server.close();
  }
});
