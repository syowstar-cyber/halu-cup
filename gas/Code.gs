// 第20回 Halu杯 点数報告 API（Google Apps Script ウェブアプリ）
// 1つの JSON（Drive 上の halu-cup-scores.json）に P1〜P30・本田プロ・ゆうこママの点数を持つ。
// 配置手順は gas/README.md を見る。

const FILE_NAME = 'halu-cup-scores.json';
const ROUNDS = ['1', '2', '3', '4', 'S', 'F'];   // 予選1〜4・準決勝・決勝
const PLAYERS = (function () {
  const a = ['本田プロ', 'ゆうこママ'];
  for (let i = 1; i <= 30; i++) a.push('P' + i);
  return a;
})();

function emptyData_() {
  const players = {};
  PLAYERS.forEach(function (p) {
    players[p] = { '1': null, '2': null, '3': null, '4': null, 'S': null, 'F': null };
  });
  return { updated: null, players: players, log: [] };
}

function getFile_() {
  const it = DriveApp.getFilesByName(FILE_NAME);
  if (it.hasNext()) return it.next();
  return DriveApp.createFile(FILE_NAME, JSON.stringify(emptyData_(), null, 1), MimeType.PLAIN_TEXT);
}

function load_() {
  try {
    const d = JSON.parse(getFile_().getBlob().getDataAsString('UTF-8'));
    if (!d.players) throw new Error('shape');
    PLAYERS.forEach(function (p) { if (!d.players[p]) d.players[p] = emptyData_().players[p]; });
    if (!d.log) d.log = [];
    return d;
  } catch (e) {
    return emptyData_();
  }
}

function save_(d) {
  getFile_().setContent(JSON.stringify(d, null, 1));
}

function out_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

function now_() {
  return Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd HH:mm:ss');
}

// 読み取り: GET （誰でも）
function doGet(e) {
  return out_({ ok: true, data: load_() });
}

// 書き込み: POST（本文は JSON。報告キーが要る）
//   {key, player:'P12', round:'1'..'4'|'S'|'F', score: 32000}
//   {key, action:'clear', player, round}   … 取り消し（null に戻す）
function doPost(e) {
  let body;
  try { body = JSON.parse(e.postData.contents); } catch (err) { return out_({ ok: false, error: 'bad_json' }); }

  const key = PropertiesService.getScriptProperties().getProperty('REPORT_KEY') || '';
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
    if (d.log.length > 3000) d.log = d.log.slice(-3000);
    save_(d);
    return out_({ ok: true, data: d });
  } finally {
    lock.releaseLock();
  }
}
