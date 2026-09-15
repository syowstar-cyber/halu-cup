// 第20回 Halu杯 点数報告 API（Google Apps Script ウェブアプリ）
// ドライブは使わない。スクリプト プロパティ（このスクリプト専用の保存領域）に JSON を持つ。
// 配置手順は gas/README.md を見る。

const ROUNDS = ['1', '2', '3', '4', 'S', 'F'];   // 予選1〜4・準決勝・決勝
const PLAYERS = (function () {
  const a = ['本田プロ', 'ゆうこママ'];
  for (let i = 1; i <= 30; i++) a.push('P' + i);
  return a;
})();
const LOG_MAX = 120;   // 保存領域の上限（1項目9KB）に収める

function props_() { return PropertiesService.getScriptProperties(); }

function emptyPlayers_() {
  const players = {};
  PLAYERS.forEach(function (p) {
    players[p] = { '1': null, '2': null, '3': null, '4': null, 'S': null, 'F': null };
  });
  return players;
}

function load_() {
  const p = props_();
  let players, log;
  try { players = JSON.parse(p.getProperty('PLAYERS') || 'null'); } catch (e) { players = null; }
  try { log = JSON.parse(p.getProperty('LOG') || '[]'); } catch (e) { log = []; }
  if (!players) players = emptyPlayers_();
  PLAYERS.forEach(function (q) { if (!players[q]) players[q] = emptyPlayers_()[q]; });
  return { updated: p.getProperty('UPDATED') || null, players: players, log: log };
}

function save_(d) {
  const p = props_();
  p.setProperty('PLAYERS', JSON.stringify(d.players));
  p.setProperty('LOG', JSON.stringify(d.log.slice(-LOG_MAX)));
  p.setProperty('UPDATED', d.updated || '');
}

function out_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

function now_() {
  return Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd HH:mm:ss');
}

// 読み取り: GET（誰でも）
function doGet(e) {
  return out_({ ok: true, data: load_() });
}

// 書き込み: POST（本文は JSON。報告キーが要る）
//   {key, player:'P12', round:'1'..'4'|'S'|'F', score: 32000}
//   {key, action:'clear', player, round}   … 取り消し（null に戻す）
function doPost(e) {
  let body;
  try { body = JSON.parse(e.postData.contents); } catch (err) { return out_({ ok: false, error: 'bad_json' }); }

  const key = props_().getProperty('REPORT_KEY') || '';
  if (!key || String(body.key || '') !== key) return out_({ ok: false, error: 'key' });

  const player = String(body.player || '');
  const round = String(body.round || '');
  if (PLAYERS.indexOf(player) < 0) return out_({ ok: false, error: 'player' });
  if (ROUNDS.indexOf(round) < 0) return out_({ ok: false, error: 'round' });

  let score = null;
  if (body.action !== 'clear') {
    score = Number(body.score);
    if (!Number.isInteger(score) || score < -200000 || score > 300000) return out_({ ok: false, error: 'score' });
  }

  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const d = load_();
    d.players[player][round] = score;
    d.updated = now_();
    d.log.push({ ts: d.updated, player: player, round: round, score: score });
    save_(d);
    return out_({ ok: true, data: d });
  } finally {
    lock.releaseLock();
  }
}

// 全消去（エディタから手で実行する用。ウェブからは呼べない）
function resetAll() {
  const p = props_();
  p.deleteProperty('PLAYERS');
  p.deleteProperty('LOG');
  p.deleteProperty('UPDATED');
}
