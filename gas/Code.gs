// 第20回 Halu杯 点数報告 API（Google Apps Script ウェブアプリ）
// ドライブは使わない。スクリプト プロパティ（このスクリプト専用の保存領域）に JSON を持つ。
// 配置手順は gas/README.md を見る。
//
// 受け口は2つ:
//   点数報告（参加者）… キーなし。{player, round, score} / {action:'clear', player, round}
//   チェック共有（幹部）… キーなし（幹部用ページは公開のため）。{action:'check', k, v, by}
//   打ち上げ希望（参加者）… キーなし。{action:'party', name, no, choice:'1'|'2'|'3'|'4'|''}（'' は取り消し）

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
  let players, log, checks, party;
  try { players = JSON.parse(p.getProperty('PLAYERS') || 'null'); } catch (e) { players = null; }
  try { log = JSON.parse(p.getProperty('LOG') || '[]'); } catch (e) { log = []; }
  try { checks = JSON.parse(p.getProperty('CHECKS') || '{}'); } catch (e) { checks = {}; }
  try { party = JSON.parse(p.getProperty('PARTY') || '{}'); } catch (e) { party = {}; }
  if (!players) players = emptyPlayers_();
  PLAYERS.forEach(function (q) { if (!players[q]) players[q] = emptyPlayers_()[q]; });
  return { updated: p.getProperty('UPDATED') || null, players: players, log: log, checks: checks || {}, party: party || {} };
}

function save_(d) {
  const p = props_();
  p.setProperty('PLAYERS', JSON.stringify(d.players));
  p.setProperty('LOG', JSON.stringify(d.log.slice(-LOG_MAX)));
  p.setProperty('UPDATED', d.updated || '');
}

function saveChecks_(checks) {
  props_().setProperty('CHECKS', JSON.stringify(checks));
}

function saveParty_(party) {
  props_().setProperty('PARTY', JSON.stringify(party));
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

// 書き込み: POST（本文は JSON。キーは要らない＝2026-09-16 主催の指示で撤去。プレイヤー・対局・点数の範囲だけ検査）
//   {player:'P12', round:'1'..'4'|'S'|'F', score: 32000}
//   {action:'clear', player, round}   … 取り消し（null に戻す）
//   {action:'check', k:'項目キー', v:true|false, by:'名前'}   … 幹部のチェック共有（キー不要）
//   {action:'party', name:'名前', no:'P12'|'', choice:'1'|'2'|'3'|'4'|''}   … 打ち上げ希望（キー不要。'' で取り消し）
function doPost(e) {
  let body;
  try { body = JSON.parse(e.postData.contents); } catch (err) { return out_({ ok: false, error: 'bad_json' }); }

  if (body.action === 'check') return doCheck_(body);
  if (body.action === 'party') return doParty_(body);

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

// 幹部のチェック共有。checks[k] = {by, ts}（外すと項目ごと消す）
function doCheck_(body) {
  const k = String(body.k || '');
  if (!/^[A-Za-z0-9_　-鿿＀-￯]{1,80}$/.test(k)) return out_({ ok: false, error: 'k' });
  const by = String(body.by || '').replace(/[<>"'\n\r]/g, '').slice(0, 20);

  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const checks = load_().checks;
    if (body.v) checks[k] = { by: by, ts: now_() }; else delete checks[k];
    saveChecks_(checks);
    return out_({ ok: true, checks: checks });
  } finally {
    lock.releaseLock();
  }
}

// 打ち上げ希望。party[名前] = {no, choice, ts}（同じ名前で送り直すと上書き。choice '' で消す）
function doParty_(body) {
  const name = String(body.name || '').replace(/[<>"'\n\r]/g, '').trim().slice(0, 20);
  if (!name) return out_({ ok: false, error: 'name' });
  const no = String(body.no || '');
  if (no && PLAYERS.indexOf(no) < 0) return out_({ ok: false, error: 'player' });
  const choice = String(body.choice || '');
  if (['', '1', '2', '3', '4'].indexOf(choice) < 0) return out_({ ok: false, error: 'choice' });

  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const party = load_().party;
    if (choice) party[name] = { no: no, choice: choice, ts: now_() }; else delete party[name];
    saveParty_(party);
    return out_({ ok: true, party: party });
  } finally {
    lock.releaseLock();
  }
}

// 全消去（エディタから手で実行する用。ウェブからは呼べない）。チェックと打ち上げ希望は消さない
function resetAll() {
  const p = props_();
  p.deleteProperty('PLAYERS');
  p.deleteProperty('LOG');
  p.deleteProperty('UPDATED');
}

// 幹部のチェックだけ全消去（エディタから手で実行する用）
function resetChecks() {
  props_().deleteProperty('CHECKS');
}

// 打ち上げ希望だけ全消去（エディタから手で実行する用）
function resetParty() {
  props_().deleteProperty('PARTY');
}
