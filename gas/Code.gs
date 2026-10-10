// 第20回 Halu杯 点数報告 API（Google Apps Script ウェブアプリ）
// ドライブは使わない。スクリプト プロパティ（このスクリプト専用の保存領域）に JSON を持つ。
// 配置手順は gas/README.md を見る。
//
// 受け口は2つ:
//   点数報告（参加者）… キーなし。{player, round, score, chombo?} / {action:'clear', player, round}
//     chombo はその半荘のチョンボ回数（0〜9。省くと変えない）。CHOMBO に player→round→回数 で持つ（2026-09-25）
//   チェック共有（幹部）… キーなし（幹部用ページは公開のため）。{action:'check', k, v, by}（受付の出席 k='出席_…' は ATTEND に分けて持つ）
//   打ち上げ希望（参加者）… キーなし。{action:'party', name, no, choice:'1'|'2'|'3'|'4'|'5'|''}（'' は取り消し）
//   出席者一覧（幹部）… キーなし。{action:'roster', names:{P1:'名前', ...}}（'' で消す。渡したキーだけ更新）
//     名前はここ（スクリプト プロパティ ROSTER）にだけ置く。公開リポにはファイルとして置かない（2026-09-17）
//   閲覧ログ（参加者ページ）… キーなし。{action:'view', page:'sanka', who:'名前'|''}。日ごとの回数と直近 VIEW_MAX 件を VIEWS に持つ
//   本田プロ確認事項（プロ用ページ）… キーなし。{action:'pro', who:'名前（立場）', items:{'1':{c:'選択', n:'補足'}, …}}（2026-10-10）
//     中身は PRO_ANS に持ち、GET では返さない（到着時刻・前後の予定を公開しない）。返すのは項目ごとの最終送信時刻だけ。
//     届いたら、このスクリプトの持ち主へメールで知らせる（1日 PRO_MAIL_MAX 通まで）
//   生年月日（幹部用ページ）… キーなし。{action:'birth', player:'P12'|'本田プロ'|'ゆうこママ', date:'YYYY-MM-DD'|''}（'' で消す。2026-10-11）
//     同点（年齢が上の方が上位）のときだけ入れる。BIRTH に持ち、生年月日そのものは GET でも返事でも返さない。
//     返すのは入れた人どうしの年上からの順 agerank（1 が最年長・同じ日は同じ数）だけ

const ROUNDS = ['1', '2', '3', '4', 'S', 'F'];   // 予選1〜4・準決勝・決勝
const PLAYERS = (function () {
  const a = ['本田プロ', 'ゆうこママ'];
  for (let i = 1; i <= 30; i++) a.push('P' + i);
  return a;
})();
const LOG_MAX = 120;   // 保存領域の上限（1項目9KB）に収める
const VIEW_MAX = 100;  // 閲覧ログの直近件数
// 本田プロ確認事項（幹部用MD 14章の連-1〜8）。キーは番号、値はメールに出す見出し
const PRO_ITEMS = { '1': '進行表のご了承', '2': '撮影・SNS投稿', '3': 'サイン色紙', '4': '休憩の長さ', '5': '軽食のご希望', '6': '前後のご予定', '7': '当日の到着時刻', '8': '打ち上げ' };
const PRO_LOG_MAX = 50;   // 送信履歴（時刻・名前・項目番号だけ）
const PRO_MAIL_MAX = 30;  // 1日に送る知らせメールの上限

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
  let players, log, checks, party, roster, views, chombo;
  try { players = JSON.parse(p.getProperty('PLAYERS') || 'null'); } catch (e) { players = null; }
  try { log = JSON.parse(p.getProperty('LOG') || '[]'); } catch (e) { log = []; }
  checks = loadChecks_();
  try { party = JSON.parse(p.getProperty('PARTY') || '{}'); } catch (e) { party = {}; }
  try { roster = JSON.parse(p.getProperty('ROSTER') || '{}'); } catch (e) { roster = {}; }
  try { views = JSON.parse(p.getProperty('VIEWS') || 'null'); } catch (e) { views = null; }
  try { chombo = JSON.parse(p.getProperty('CHOMBO') || '{}'); } catch (e) { chombo = {}; }
  if (!views || typeof views !== 'object') views = { daily: {}, recent: [] };
  if (!views.daily) views.daily = {}; if (!views.recent) views.recent = [];
  if (!players) players = emptyPlayers_();
  PLAYERS.forEach(function (q) { if (!players[q]) players[q] = emptyPlayers_()[q]; });
  let partyLog = []; try { partyLog = loadPartyLog_(); } catch (e) { partyLog = []; }
  return { updated: p.getProperty('UPDATED') || null, players: players, log: log, checks: checks || {}, party: party || {}, roster: roster || {}, views: views, chombo: chombo || {}, partyLog: partyLog, pro: proStatus_(loadPro_()), agerank: ageRankOut_() };
}

// 生年月日。birth[プレイヤー] = 'YYYY-MM-DD'（公開しない。返すのは ageRank_ の順だけ）
function loadBirth_() {
  try { return JSON.parse(props_().getProperty('BIRTH') || '{}') || {}; } catch (e) { return {}; }
}
// 入れた人どうしの年上からの順。早く生まれた人ほど小さい数（1 が最年長）。同じ日は同じ数
function ageRank_(birth) {
  const keys = Object.keys(birth), r = {};
  keys.forEach(function (p) { r[p] = 1 + keys.filter(function (q) { return birth[q] < birth[p]; }).length; });
  return r;
}
// 返す agerank。大会後に resetBirth で生年月日を消したら、消す前の順（AGERANK_FROZEN）を返し続ける（順位が元に戻らないように）
function ageRankOut_() {
  const frozen = props_().getProperty('AGERANK_FROZEN');
  if (frozen !== null) { try { return JSON.parse(frozen) || {}; } catch (e) { return {}; } }
  return ageRank_(loadBirth_());
}
// 'YYYY-MM-DD' で、実在する日付で、1900-01-01〜大会の日の範囲
function validBirth_(s) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s);
  if (!m) return false;
  const y = Number(m[1]), mo = Number(m[2]), d = Number(m[3]);
  const dt = new Date(Date.UTC(y, mo - 1, d));
  if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== mo - 1 || dt.getUTCDate() !== d) return false;
  return s >= '1900-01-01' && s <= '2026-10-24';
}

// 本田プロ確認事項の回答。ans[番号] = {c, n, who, ts}（同じ番号を送り直すと上書き）
function loadPro_() {
  try { return JSON.parse(props_().getProperty('PRO_ANS') || '{}') || {}; } catch (e) { return {}; }
}
// 公開してよいのは項目ごとの最終送信時刻だけ
function proStatus_(ans) {
  const st = {};
  Object.keys(ans).forEach(function (k) { if (ans[k] && ans[k].ts) st[k] = ans[k].ts; });
  return st;
}

function saveViews_(views) {
  props_().setProperty('VIEWS', JSON.stringify(views));
}

function saveRoster_(roster) {
  props_().setProperty('ROSTER', JSON.stringify(roster));
}

function save_(d) {
  const p = props_();
  p.setProperty('PLAYERS', JSON.stringify(d.players));
  p.setProperty('LOG', JSON.stringify(d.log.slice(-LOG_MAX)));
  p.setProperty('UPDATED', d.updated || '');
  p.setProperty('CHOMBO', JSON.stringify(d.chombo || {}));
}

// チェック共有。1項目9KBの上限に収めるため、置き場を分ける（2026-10-11）。
// 受付の出席（キー「出席_…」）は ATTEND、それ以外はキーから決まる CHECKS・CHECKS_2〜4 のどれか1つ。
// 読むとき・返すときは全部を合わせた1つの表にする（ページは分かれていることを知らない）
const ATTEND_PREFIX = '出席_';
const CHECK_BUCKETS = ['CHECKS', 'CHECKS_2', 'CHECKS_3', 'CHECKS_4'];
const CHECK_STORES = CHECK_BUCKETS.concat(['ATTEND']);
const PROP_BYTES = 8500;   // 1項目の上限（9KB）より少し小さく
function readJson_(name) {
  try { return JSON.parse(props_().getProperty(name) || '{}') || {}; } catch (e) { return {}; }
}
function checkHome_(k) {
  if (k.indexOf(ATTEND_PREFIX) === 0) return 'ATTEND';
  let h = 0;
  for (let i = 0; i < k.length; i++) h = (h + k.charCodeAt(i)) % CHECK_BUCKETS.length;
  return CHECK_BUCKETS[h];
}
function loadChecks_() {
  const all = {};
  CHECK_STORES.forEach(function (name) { Object.assign(all, readJson_(name)); });
  return all;
}

function saveParty_(party) {
  props_().setProperty('PARTY', JSON.stringify(party));
}

// 打ち上げ希望の履歴（2026-10-08）。送信のたびに1件足すだけで、消す処理は置かない（上書き・取り消しの前の回答も残す）。
// 1項目9KBの上限に収めるため PARTY_LOG_1, _2, … に分けて積み、今の番号を PARTY_LOG_N に持つ。
const PLOG_BYTES = 7000;
function appendPartyLog_(entry) {
  const p = props_();
  let n = parseInt(p.getProperty('PARTY_LOG_N') || '1', 10); if (!(n >= 1)) n = 1;
  let arr;
  try { arr = JSON.parse(p.getProperty('PARTY_LOG_' + n) || '[]'); } catch (e) { arr = []; }
  arr.push(entry);
  let s = JSON.stringify(arr);
  if (arr.length > 1 && Utilities.newBlob(s).getBytes().length > PLOG_BYTES) {
    n += 1; s = JSON.stringify([entry]);
    p.setProperty('PARTY_LOG_N', String(n));
  }
  p.setProperty('PARTY_LOG_' + n, s);
}
function loadPartyLog_() {
  const p = props_();
  const n = parseInt(p.getProperty('PARTY_LOG_N') || '1', 10);
  let all = [];
  for (let i = 1; i <= n; i++) {
    try { all = all.concat(JSON.parse(p.getProperty('PARTY_LOG_' + i) || '[]')); } catch (e) {}
  }
  return all;
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
//   {player:'P12', round:'1'..'4'|'S'|'F', score: 32000, chombo: 0..9}   … chombo は省略可
//   {action:'clear', player, round}   … 取り消し（null に戻す）
//   {action:'check', k:'項目キー', v:true|false, by:'名前'}   … 幹部のチェック共有（キー不要）
//   {action:'party', name:'名前', no:'P12'|'', choice:'1'|'2'|'3'|'4'|'5'|''}   … 打ち上げ希望（キー不要。'' で取り消し）
//   {action:'birth', player:'P12', date:'YYYY-MM-DD'|''}   … 生年月日（同点のときだけ。返事は agerank だけ）
function doPost(e) {
  let body;
  try { body = JSON.parse(e.postData.contents); } catch (err) { return out_({ ok: false, error: 'bad_json' }); }

  if (body.action === 'check') return doCheck_(body);
  if (body.action === 'party') return doParty_(body);
  if (body.action === 'roster') return doRoster_(body);
  if (body.action === 'view') return doView_(body);
  if (body.action === 'pro') return doPro_(body);
  if (body.action === 'birth') return doBirth_(body);

  const player = String(body.player || '');
  const round = String(body.round || '');
  if (PLAYERS.indexOf(player) < 0) return out_({ ok: false, error: 'player' });
  if (ROUNDS.indexOf(round) < 0) return out_({ ok: false, error: 'round' });

  let score = null;
  if (body.action !== 'clear') {
    score = Number(body.score);
    if (!Number.isInteger(score) || score < -200000 || score > 999900) return out_({ ok: false, error: 'score' });
  }
  let chombo = null;
  if (body.action !== 'clear' && body.chombo !== undefined && body.chombo !== null) {
    chombo = Number(body.chombo);
    if (!Number.isInteger(chombo) || chombo < 0 || chombo > 9) return out_({ ok: false, error: 'chombo' });
  }

  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const d = load_();
    d.players[player][round] = score;
    const c = d.chombo[player] || {};
    if (body.action === 'clear' || chombo === 0) delete c[round];
    else if (chombo !== null) c[round] = chombo;
    if (Object.keys(c).length) d.chombo[player] = c; else delete d.chombo[player];
    d.updated = now_();
    const entry = { ts: d.updated, player: player, round: round, score: score };
    if (chombo) entry.chombo = chombo;
    d.log.push(entry);
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
    // 付けるときは決まった置き場へ入れ、ほかの置き場に古い同じキーがあれば消す。外すときは全部から消す
    const home = checkHome_(k), store = {}, changed = {};
    CHECK_STORES.forEach(function (name) {
      store[name] = readJson_(name);
      if ((name !== home || !body.v) && store[name][k]) { delete store[name][k]; changed[name] = true; }
    });
    if (body.v) { store[home][k] = { by: by, ts: now_() }; changed[home] = true; }
    const text = {};
    Object.keys(changed).forEach(function (name) { text[name] = JSON.stringify(store[name]); });
    // 大きさは付けるときだけ見る（外すときは小さくなるだけ）
    if (body.v && Utilities.newBlob(text[home]).getBytes().length > PROP_BYTES) return out_({ ok: false, error: 'size' });
    if (Object.keys(text).length) props_().setProperties(text);
    const all = {};
    CHECK_STORES.forEach(function (name) { Object.assign(all, store[name]); });
    return out_({ ok: true, checks: all });
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
  if (['', '1', '2', '3', '4', '5'].indexOf(choice) < 0) return out_({ ok: false, error: 'choice' });

  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const party = load_().party;
    const prev = party[name] ? party[name].choice : '';
    const ts = now_();
    if (choice) party[name] = { no: no, choice: choice, ts: ts }; else delete party[name];
    saveParty_(party);
    try { appendPartyLog_({ ts: ts, name: name, no: no, choice: choice, prev: prev }); } catch (e) {}   // 履歴が書けなくても回答の保存は止めない
    let partyLog = []; try { partyLog = loadPartyLog_(); } catch (e) {}
    return out_({ ok: true, party: party, partyLog: partyLog });
  } finally {
    lock.releaseLock();
  }
}

// 出席者一覧。roster[P番号] = 名前。渡した names のキーだけ更新し、'' なら消す（P1〜P30 のみ）
function doRoster_(body) {
  const names = body.names;
  if (!names || typeof names !== 'object') return out_({ ok: false, error: 'names' });
  const keys = Object.keys(names);
  if (!keys.length || keys.length > 30) return out_({ ok: false, error: 'names' });
  for (let i = 0; i < keys.length; i++) {
    if (!/^P([1-9]|[12]\d|30)$/.test(keys[i])) return out_({ ok: false, error: 'player' });
  }
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const d = load_(), roster = d.roster, party = d.party;
    const moved = [];
    keys.forEach(function (k) {
      const v = String(names[k] || '').replace(/[<>"'\n\r\t]/g, '').trim().slice(0, 20);
      const old = roster[k];
      if (v) roster[k] = v; else delete roster[k];
      // 名前を変えたら打ち上げ希望も新しい名前へ移す（回答時刻は据え置き）。新しい名前に回答が既にあれば移さない
      if (v && old && old !== v && party[old] && !party[v]) {
        party[v] = { no: k, choice: party[old].choice, ts: party[old].ts };
        delete party[old];
        moved.push({ name: v, no: k, choice: party[v].choice, from: old });
      }
    });
    saveRoster_(roster);
    if (moved.length) {
      saveParty_(party);
      const ts = now_();
      moved.forEach(function (m) { try { appendPartyLog_({ ts: ts, name: m.name, no: m.no, choice: m.choice, prev: m.choice, from: m.from }); } catch (e) {} });
    }
    let partyLog = []; try { partyLog = loadPartyLog_(); } catch (e) {}
    return out_({ ok: true, roster: roster, party: party, partyLog: partyLog });
  } finally {
    lock.releaseLock();
  }
}

// 閲覧ログ（参加者ページ）。views = {daily:{'YYYY-MM-DD': 回数}, recent:[{ts, who}]}（直近 VIEW_MAX 件）
function doView_(body) {
  const page = String(body.page || '');
  if (page !== 'sanka') return out_({ ok: false, error: 'page' });
  const who = String(body.who || '').replace(/[<>"'\n\r\t]/g, '').trim().slice(0, 20);
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const views = load_().views;
    const ts = now_(), day = ts.slice(0, 10);
    views.daily[day] = (views.daily[day] || 0) + 1;
    views.recent.push({ ts: ts, who: who });
    views.recent = views.recent.slice(-VIEW_MAX);
    saveViews_(views);
    return out_({ ok: true });
  } finally {
    lock.releaseLock();
  }
}

// 本田プロ確認事項。答えのある項目だけ上書きし、送信履歴（時刻・名前・番号だけ）を PRO_LOG に積み、持ち主へメールで知らせる
function doPro_(body) {
  const who = String(body.who || '').replace(/[<>"'\n\r\t]/g, '').trim().slice(0, 40);
  if (!who) return out_({ ok: false, error: 'who' });
  const items = body.items;
  if (!items || typeof items !== 'object') return out_({ ok: false, error: 'items' });
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const p = props_(), ans = loadPro_(), ts = now_(), got = [];
    Object.keys(PRO_ITEMS).forEach(function (k) {
      const it = items[k];
      if (!it || typeof it !== 'object') return;
      const c = String(it.c || '').replace(/[<>"'\n\r\t]/g, '').trim().slice(0, 20);
      const n = String(it.n || '').replace(/[<>\r\t]/g, '').trim().slice(0, 200);
      if (!c && !n) return;
      ans[k] = { c: c, n: n, who: who, ts: ts };
      got.push(k);
    });
    if (!got.length) return out_({ ok: false, error: 'items' });
    p.setProperty('PRO_ANS', JSON.stringify(ans));
    let log; try { log = JSON.parse(p.getProperty('PRO_LOG') || '[]'); } catch (e) { log = []; }
    log.push({ ts: ts, who: who, items: got });
    p.setProperty('PRO_LOG', JSON.stringify(log.slice(-PRO_LOG_MAX)));
    try { mailPro_(who, got, ans, ts); } catch (e) {}   // メールが送れなくても回答の保存は止めない
    return out_({ ok: true, pro: proStatus_(ans) });
  } finally {
    lock.releaseLock();
  }
}

// 生年月日（同点のときだけ幹部用ページで入れる）。date '' で消す。返事は agerank だけ（生年月日は返さない）
function doBirth_(body) {
  const player = String(body.player || '');
  if (PLAYERS.indexOf(player) < 0) return out_({ ok: false, error: 'player' });
  const date = String(body.date || '');
  if (date && !validBirth_(date)) return out_({ ok: false, error: 'date' });
  if (props_().getProperty('AGERANK_FROZEN') !== null) return out_({ ok: false, error: 'closed' });   // 大会後（resetBirth の後）は受け付けない
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const birth = loadBirth_();
    if (date) birth[player] = date; else delete birth[player];
    props_().setProperty('BIRTH', JSON.stringify(birth));
    return out_({ ok: true, agerank: ageRank_(birth) });
  } finally {
    lock.releaseLock();
  }
}

function mailPro_(who, got, ans, ts) {
  const p = props_(), day = ts.slice(0, 10);
  let m; try { m = JSON.parse(p.getProperty('PRO_MAIL') || '{}'); } catch (e) { m = {}; }
  if (m.day !== day) m = { day: day, n: 0 };
  if (m.n >= PRO_MAIL_MAX) return;
  m.n += 1;
  p.setProperty('PRO_MAIL', JSON.stringify(m));
  const lines = ['第20回 Halu杯 本田プロ確認用ページから回答が届きました。', '', '送った人: ' + who, '時刻: ' + ts, ''];
  got.forEach(function (k) {
    lines.push(k + '. ' + PRO_ITEMS[k]);
    if (ans[k].c) lines.push('  選択: ' + ans[k].c);
    if (ans[k].n) lines.push('  補足: ' + ans[k].n);
  });
  lines.push('', '名前を確かめる仕組みはありません。心当たりのない送信は無視してください。');
  MailApp.sendEmail(Session.getEffectiveUser().getEmail(), '[Halu杯] 本田プロ確認事項に回答（' + who + '）', lines.join('\n'));
}

// 全消去（エディタから手で実行する用。ウェブからは呼べない）。点数とチョンボ回数を消す。チェック・打ち上げ希望・出席者一覧・閲覧ログは消さない
function resetAll() {
  const p = props_();
  p.deleteProperty('PLAYERS');
  p.deleteProperty('CHOMBO');
  p.deleteProperty('LOG');
  p.deleteProperty('UPDATED');
}

// 幹部のチェックだけ全消去（エディタから手で実行する用）。CHECKS〜CHECKS_4 と受付の出席チェック（ATTEND）を消す
function resetChecks() {
  CHECK_STORES.forEach(function (name) { props_().deleteProperty(name); });
}

// 打ち上げ希望だけ全消去（エディタから手で実行する用）
function resetParty() {
  props_().deleteProperty('PARTY');
}

// 出席者一覧だけ全消去（エディタから手で実行する用。大会後に名前を消すときもこれ）
function resetRoster() {
  props_().deleteProperty('ROSTER');
}

// 閲覧ログだけ全消去（エディタから手で実行する用）
function resetViews() {
  props_().deleteProperty('VIEWS');
}

// 生年月日だけ全消去（エディタから手で実行する用。大会後に消すときもこれ）
// 消す前の上下の順（日付は入らない・公開の順位で分かることだけ）を AGERANK_FROZEN に固定し、以後の入力を断る
function resetBirth() {
  const p = props_();
  p.setProperty('AGERANK_FROZEN', JSON.stringify(ageRank_(loadBirth_())));
  p.deleteProperty('BIRTH');
}
// resetBirth の後に、もう一度生年月日を受け付けたいとき（固定した順を捨てる。エディタから手で実行する用）
function reopenBirth() {
  props_().deleteProperty('AGERANK_FROZEN');
}

// 本田プロ確認事項の回答・送信履歴だけ全消去（エディタから手で実行する用）
function resetPro() {
  const p = props_();
  p.deleteProperty('PRO_ANS');
  p.deleteProperty('PRO_LOG');
  p.deleteProperty('PRO_MAIL');
}
