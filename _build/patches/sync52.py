"""V52 (17 out 2026): as tabelas antigas que eram escritas à mão para a J6 passam a ser calculadas a partir dos
plantéis atuais (SQUAD_STATE + LEAGUE_SQUADS), no arranque e sempre que o live.json traz plantéis novos:
SQUAD/ALL_PLAYERS (o teu plantel nas vistas antigas: jogador a jogador, preços, orçamento), MARCO_SQUAD_CURRENT,
CAPTAIN_DIST (capitães da liga), MY/MARCO_LEAGUE_OWNERSHIP (plantel vs liga), TEMPLATE_GAPS (picks em falta),
LEAGUE_BUDGETS (orçamentos e chips), H2H_SHARED/MINE_ONLY/THEIRS_ONLY (+ texto do adversário), CHIPS_USED,
ALT, ENABLERS e a nota das chips do Marco. Depois do deadline, as sugestões da jornada fechada ficam marcadas.
Uso (a partir da raiz): py _build/patches/sync52.py"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
H = ROOT / 'index.html'
s = H.read_text(encoding='utf-8')
assert 'V52' not in s, 'já aplicado'


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:100], s.count(a))
    s = s.replace(a, b)


# 1) LEAGUE_SQUADS passa para o início do 2.º script (as vistas antigas, mais acima, precisam dele)
m = re.search(r'\n(  const LEAGUE_SQUADS = \{.*?\};)\n', s)
ls_line = m.group(1)
s = s.replace('\n' + ls_line + '\n', '\n  // (V52) LEAGUE_SQUADS passou para o início deste script\n', 1)
anchor = "  const TEAMS = {"
assert s.count(anchor) == 1
s = s.replace(anchor, "  // LEAGUE_SQUADS: plantéis, capitães, banco, valor e chips dos 20 (atualizado por _build/pool/apply_picks.py\n  // depois de cada deadline e, no site, pelo live.json). (V52: aqui no início para todas as vistas o poderem ler.)\n" + ls_line + "\n" + anchor, 1)

# 2) construtores (só usam o que já existe neste ponto: FULL_POOL_BY_ID, LEAGUE_SQUADS, SQUAD_STATE, GW_META, TEAMS, FIX_AHEAD)
V52 = r"""
  // ===================================================================
  // V52 (17 out 2026): tabelas antigas calculadas a partir dos plantéis atuais (antes eram escritas à mão para a J6).
  // ===================================================================
  var V52 = {me: {bruno: 5191766, marco: 1973102}};
  const v52Ep = (p, i) => (p && p.epH ? (p.epH[i || 0] || 0) : 0);
  const v52Name = id => (FULL_POOL_BY_ID[id] || {}).name || String(id);
  function v52After() {   // o deadline da jornada já passou e há plantéis dessa jornada
    const g = (window.__LIVE && window.__LIVE.picks_event) || GW_META.squadsGw;
    return g === GW_META.next && Date.now() >= new Date(GW_META.deadline).getTime();
  }
  function v52Fx(p) {
    const fx = (FIX_AHEAD[GW_META.next] || []).filter(f => f.h === p.team || f.a === p.team);
    if (!fx.length) return 'sem jogo';
    return fx.map(f => { const home = f.h === p.team, d = home ? (f.th ?? f.dh) : (f.ta ?? f.da); return `${home ? 'em casa com' : 'fora, no'} ${TEAMS[home ? f.a : f.h]} (dificuldade ${(+d).toFixed(1)})`; }).join(' e ');
  }
  function v52Why(p) {
    const L = GW_META.last, pts = p.ptsGw || [], mins = p.minsGw || [], g = [L - 2, L - 1, L].filter(x => x >= 1);
    const st = {d: 'dúvida', i: 'lesionado', s: 'suspenso', u: 'indisponível'}[p.status];
    return `J${g.join('/J')}: ${g.map(x => pts[x - 1] ?? 0).join('/')} pts (${g.map(x => mins[x - 1] ?? 0).join('/')} min). J${GW_META.next}: ${v52Fx(p)} · ≈${v52Ep(p).toFixed(1)} pts esperados.${st ? ` <b>${st}${p.chance != null ? ' ' + p.chance + '%' : ''}</b>${p.news ? ' — ' + p.news : ''}.` : ''}`;
  }
  function v52BestXi(ps) {
    const by = c => ps.filter(p => p.cls === c).sort((a, b) => v52Ep(b) - v52Ep(a));
    const g = by('gk'), d = by('def'), m = by('mid'), f = by('fwd'); let best = null;
    [[3,5,2],[3,4,3],[4,5,1],[4,4,2],[4,3,3],[5,4,1],[5,3,2],[5,2,3]].forEach(([nd, nm, nf]) => {
      if (!g.length || d.length < nd || m.length < nm || f.length < nf) return;
      const xi = [g[0], ...d.slice(0, nd), ...m.slice(0, nm), ...f.slice(0, nf)], v = xi.reduce((s, p) => s + v52Ep(p), 0);
      if (!best || v > best.v) best = {xi, v};
    });
    return best ? best.xi : ps.slice(0, 11);
  }
  // o plantel atual de um gestor, com titular/capitão/vice reais depois do deadline (antes: os do modelo)
  function v52Lineup(mgr) {
    const ps = SQUAD_STATE[mgr].players.map(x => FULL_POOL_BY_ID[x.id]).filter(Boolean);
    const L = LEAGUE_SQUADS[V52.me[mgr]], key = a => a.slice().sort((x, y) => x - y).join(',');
    if (L && v52After() && key([...L.s, ...L.b]) === key(ps.map(p => p.id)))
      return {ps, xi: new Set(L.s), cap: L.c, vice: L.vc, bench: L.b, real: true};
    const xi = v52BestXi(ps), order = xi.slice().sort((a, b) => v52Ep(b) - v52Ep(a));
    return {ps, xi: new Set(xi.map(p => p.id)), cap: order[0] && order[0].name, vice: order[1] && order[1].name, bench: ps.filter(p => !xi.includes(p)).map(p => p.id), real: false};
  }
  function v52Fill(arr, items) { arr.splice(0, arr.length, ...items); return arr; }
  // SQUAD (o teu plantel nas vistas antigas): grupos GK/DEF/MID/FWD
  function v52FillSquad(SQ) {
    const Lu = v52Lineup('bruno'), old = Object.values(SQ).flatMap(g => g.players);
    const G = {GK: 'gk', DEF: 'def', MID: 'mid', FWD: 'fwd'};
    Object.entries(G).forEach(([k, cls]) => {
      if (!SQ[k]) return;
      const ps = Lu.ps.filter(p => p.cls === cls).sort((a, b) => (Lu.xi.has(b.id) - Lu.xi.has(a.id)) || v52Ep(b) - v52Ep(a));
      v52Fill(SQ[k].players, ps.map(p => {
        const o = old.find(x => x.name === p.name), start = Lu.xi.has(p.id);
        return {name: p.name, club: TEAMS[p.team], team: p.team, price: '£' + p.price.toFixed(1) + 'M', tag: p.name === Lu.cap ? 'cap' : p.name === Lu.vice ? 'vice' : start ? '' : 'bench', start,
                ep1: (p.ptsGw || [])[GW_META.last - 1] ?? 0, ep2: v52Ep(p), why: v52Why(p) + (o && o.why && !Lu.real ? '' : '')};
      }));
    });
  }
  function v52MarcoSquad() {
    const Lu = v52Lineup('marco');
    return Lu.ps.slice().sort((a, b) => ({gk: 0, def: 1, mid: 2, fwd: 3})[a.cls] - ({gk: 0, def: 1, mid: 2, fwd: 3})[b.cls] || (Lu.xi.has(b.id) - Lu.xi.has(a.id))).map(p => ({
      name: p.name, club: TEAMS[p.team], team: p.team, cls: p.cls, price: p.price, start: Lu.xi.has(p.id),
      tag: p.name === Lu.cap ? 'cap' : p.name === Lu.vice ? 'vice' : Lu.xi.has(p.id) ? '' : 'bench', ep2: v52Ep(p), why: v52Why(p)}));
  }
  const v52Entries = () => Object.keys(LEAGUE_SQUADS).map(Number);
  const v52Own = id => v52Entries().filter(e => { const L = LEAGUE_SQUADS[e]; return L.s.includes(id) || L.b.includes(id); }).length;
  const v52Pct = id => Math.round(100 * v52Own(id) / v52Entries().length);
  function v52Captains() {
    const c = {}; v52Entries().forEach(e => { const L = LEAGUE_SQUADS[e]; (c[L.c] = c[L.c] || []).push(L); });
    const gw = GW_META.squadsGw || GW_META.last;
    return Object.entries(c).sort((a, b) => b[1].length - a[1].length).map(([name, Ls]) => {
      const p = Object.values(FULL_POOL_BY_ID).find(x => x.name === name), tc = Ls.filter(L => L['chip' + gw] === '3xc');
      return {name, count: Ls.length, note: `${Ls.map(L => L.m).join(', ')}${tc.length ? ` · Triple Captain: ${tc.map(L => L.m).join(', ')}` : ''}${p ? ` · ≈${v52Ep(p).toFixed(1)} pts esperados na J${GW_META.next}` : ''}`};
    });
  }
  function v52MyOwnership(mgr) {
    const Lu = v52Lineup(mgr);
    return Lu.ps.map(p => ({name: p.name, pct: v52Pct(p.id), note: `${p.name === Lu.cap ? 'capitão' : p.name === Lu.vice ? 'vice' : Lu.xi.has(p.id) ? 'titular' : 'banco'} · ≈${v52Ep(p).toFixed(1)} pts esp.`}))
      .sort((a, b) => b.pct - a.pct);
  }
  function v52Gaps() {
    const mine = new Set(SQUAD_STATE.bruno.players.map(x => x.id)), ids = new Set(v52Entries().flatMap(e => [...LEAGUE_SQUADS[e].s, ...LEAGUE_SQUADS[e].b]));
    return [...ids].filter(id => !mine.has(id) && FULL_POOL_BY_ID[id]).map(id => FULL_POOL_BY_ID[id]).map(p => ({p, pct: v52Pct(p.id)})).filter(x => x.pct >= 25)
      .sort((a, b) => b.pct - a.pct).slice(0, 10).map(({p, pct}) => ({name: p.name, club: TEAMS[p.team], pos: {gk: 'GR', def: 'DEF', mid: 'MED', fwd: 'AV'}[p.cls], price: p.price, pct,
        note: `≈${v52Ep(p).toFixed(1)} pts esp. na J${GW_META.next}; ${(p.epH || []).reduce((s, v) => s + v, 0).toFixed(1)} nas próximas 5.`}));
  }
  function v52Budgets() { return v52Entries().map(e => { const L = LEAGUE_SQUADS[e]; return {entry: e, bank: L.bank, value: L.val, chips: (L.chips || []).map(([name, event]) => ({name, event}))}; }); }
  function v52H2H() {
    const opp = v52Entries().find(e => LEAGUE_SQUADS[e].m === GW_META.h2h.bruno.next), O = opp && LEAGUE_SQUADS[opp];
    const Lu = v52Lineup('bruno'); if (!O) return {shared: [], mine: [], theirs: [], O: null};
    const oIds = [...O.s, ...O.b], mIds = Lu.ps.map(p => p.id);
    const row = (id, side) => { const p = FULL_POOL_BY_ID[id]; if (!p) return null;
      const benchM = side !== 'theirs' && !Lu.xi.has(id), benchO = side !== 'mine' && O.b.includes(id), capO = side !== 'mine' && O.c === p.name, capM = side !== 'theirs' && Lu.cap === p.name;
      const bits = [capM ? 'o teu capitão' : '', capO ? 'capitão dele' : '', side === 'shared' ? (benchM && benchO ? 'banco dos dois' : benchM ? 'no teu banco' : benchO ? 'no banco dele' : '') : (side === 'mine' ? (benchM ? 'banco' : '') : (benchO ? 'banco dele' : '')), v52Fx(p)].filter(Boolean);
      return {name: p.name, cls: p.cls, ep2: v52Ep(p), note: bits.join(' · ')}; };
    return {O, opp, shared: mIds.filter(id => oIds.includes(id)).map(id => row(id, 'shared')).filter(Boolean),
            mine: mIds.filter(id => !oIds.includes(id)).map(id => row(id, 'mine')).filter(Boolean),
            theirs: oIds.filter(id => !mIds.includes(id)).map(id => row(id, 'theirs')).filter(Boolean)};
  }
  function v52ChipsUsed() {
    const out = {}, code = {wildcard: 'wc', freehit: 'fh', bboost: 'bb', '3xc': 'tc'};
    ((LEAGUE_SQUADS[V52.me.bruno] || {}).chips || []).forEach(([n, g]) => { if (code[n]) out[code[n] + (g <= 19 ? 1 : 2)] = {gw: g}; });
    return out;
  }
  const v52ChipTxt = mgr => { const ch = ((LEAGUE_SQUADS[V52.me[mgr]] || {}).chips || []), N = {wildcard: 'Wildcard', freehit: 'Free Hit', bboost: 'Bench Boost', '3xc': 'Triple Captain'};
    const used = ch.filter(([, g]) => g <= 19), left = Object.keys(N).filter(k => !used.some(([n]) => n === k));
    return `${used.length ? 'Já usado: ' + used.map(([n, g]) => `${N[n]} (J${g})`).join(', ') + '.' : 'Ainda nenhum chip usado.'} ${left.length ? 'Por usar até à J19: ' + left.map(k => N[k]).join(', ') + '.' : 'Sem chips da 1.ª metade por usar.'}`; };
  function v52Alt() {
    const mine = new Set(SQUAD_STATE.bruno.players.map(x => x.id)), s5 = p => (p.epH || []).reduce((a, b) => a + b, 0);
    return Object.values(FULL_POOL_BY_ID).filter(p => !mine.has(p.id) && p.status === 'a').sort((a, b) => s5(b) - s5(a)).slice(0, 8)
      .map(p => ({name: p.name, club: TEAMS[p.team], note: `≈${s5(p).toFixed(1)} pts esperados nas J${GW_META.horizon[0]}-J${GW_META.horizon[GW_META.horizon.length - 1]} · ${v52Pct(p.id)}% da liga tem.`}));
  }
  function v52Enablers() {
    const mine = new Set(SQUAD_STATE.bruno.players.map(x => x.id)), s5 = p => (p.epH || []).reduce((a, b) => a + b, 0);
    return Object.values(FULL_POOL_BY_ID).filter(p => p.price <= 5.0 && p.status === 'a' && (p.mins || 0) >= 120).sort((a, b) => s5(b) / b.price - s5(a) / a.price).slice(0, 8)
      .map(p => ({pos: {gk: 'GK', def: 'DEF', mid: 'MID', fwd: 'FWD'}[p.cls], name: p.name, club: TEAMS[p.team], price: '£' + p.price.toFixed(1) + 'M', inSquad: mine.has(p.id),
        why: `≈${s5(p).toFixed(1)} pts esperados nas próximas 5 por £${p.price.toFixed(1)}M${mine.has(p.id) ? ' · já tens' : ''}.`}));
  }
"""
anchor = "  const FULL_POOL_BY_ID = Object.fromEntries(FULL_POOL.map(p => [p.id, p]));\n"
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + V52, 1)

# 3) cada tabela antiga é preenchida logo a seguir à definição (no arranque)
rep("  const ALL_PLAYERS = Object.values(SQUAD).flatMap(", "  v52FillSquad(SQUAD);   // V52: o plantel atual (com o onze real depois do deadline)\n  const ALL_PLAYERS = Object.values(SQUAD).flatMap(")
rep("  MARCO_SQUAD_CURRENT.forEach(p => { const fp = FULL_POOL_BY_NAME[p.name]; if (fp) { p.price = fp.price; if (fp.epH) p.ep2 = fp.epH[0]; } });",
    "  v52Fill(MARCO_SQUAD_CURRENT, v52MarcoSquad());   // V52\n  MARCO_SQUAD_CURRENT.forEach(p => { const fp = FULL_POOL_BY_NAME[p.name]; if (fp) { p.price = fp.price; if (fp.epH) p.ep2 = fp.epH[0]; } });")
rep("  TEMPLATE_GAPS.forEach(g => { const fp = FULL_POOL_BY_NAME[g.name]; if (fp) g.price = fp.price; });",
    "  v52Fill(TEMPLATE_GAPS, v52Gaps());   // V52: a partir dos plantéis atuais\n  TEMPLATE_GAPS.forEach(g => { const fp = FULL_POOL_BY_NAME[g.name]; if (fp) g.price = fp.price; });")
# CAPTAIN_DIST e as posses: a seguir à definição de cada uma
def after_const(name, fill):
    global s
    m = re.search(r'\n  const %s = [\[\{]' % name, s)
    assert m, name
    i = m.start() + 1
    end = s.index('\n  ];\n', i) + len('\n  ];\n')
    s = s[:end] + fill + '\n' + s[end:]
after_const('CAPTAIN_DIST', "  v52Fill(CAPTAIN_DIST, v52Captains());   // V52: capitães reais da última jornada com plantéis")
after_const('MY_LEAGUE_OWNERSHIP', "  v52Fill(MY_LEAGUE_OWNERSHIP, v52MyOwnership('bruno'));   // V52")
after_const('MARCO_LEAGUE_OWNERSHIP', "  v52Fill(MARCO_LEAGUE_OWNERSHIP, v52MyOwnership('marco'));   // V52")
after_const('LEAGUE_BUDGETS', "  v52Fill(LEAGUE_BUDGETS, v52Budgets());   // V52")
rep("  H2H_SHARED.forEach(x => { const fp = FULL_POOL_BY_NAME[x.name]; if (fp && fp.epH) x.ep2 = fp.epH[0]; });",
    "  { const h = v52H2H(); v52Fill(H2H_SHARED, h.shared); V52.h2h = h; }   // V52\n  H2H_SHARED.forEach(x => { const fp = FULL_POOL_BY_NAME[x.name]; if (fp && fp.epH) x.ep2 = fp.epH[0]; });")
rep("  H2H_MINE_ONLY.forEach(x => {", "  v52Fill(H2H_MINE_ONLY, V52.h2h.mine);   // V52\n  H2H_MINE_ONLY.forEach(x => {")
rep("  H2H_THEIRS_ONLY.forEach(x => {", "  v52Fill(H2H_THEIRS_ONLY, V52.h2h.theirs);   // V52\n  H2H_THEIRS_ONLY.forEach(x => {")
rep("  ALT.forEach(a => {", "  v52Fill(ALT, v52Alt());   // V52\n  ALT.forEach(a => {")
rep("  ENABLERS.forEach(a => {", "  v52Fill(ENABLERS, v52Enablers());   // V52\n  ENABLERS.forEach(a => {")
rep("  const CHIPS_USED = {tc1: {gw: 3}};", "  const CHIPS_USED = v52ChipsUsed();   // V52: a partir das chips reais (antes: {tc1: {gw: 3}})")

# 4) textos fixos sobre a J6 / o adversário
rep("""document.getElementById('marco-chips-summary').textContent = "Triple Captain""", """document.getElementById('marco-chips-summary').textContent = v52ChipTxt('marco') || "Triple Captain""")
m = re.search(r"    document.getElementById\('h2h-opponent-intro'\).innerHTML = `.*?`;\n", s, re.S)
assert m
s = s.replace(m.group(0), """    { const h = V52.h2h || {}, O = h.O, row = O ? LEAGUE_STANDINGS.find(r => r.team === O.tn) : null, me = LEAGUE_STANDINGS.find(r => r.mine) || {}, gw = GW_META.squadsGw || GW_META.last;
      document.getElementById('h2h-opponent-intro').innerHTML = O ? `O <b>${O.m} (${O.tn})</b> é o teu adversário na J${GW_META.next}${row ? `. Está ${row.rank}.º na liga clássica (${row.pts} pts, ${row.pts >= me.pts ? (row.pts - me.pts) + ' à tua frente' : (me.pts - row.pts) + ' atrás de ti'})` : ''}. Plantel ${v52After() ? 'e capitão reais' : ''} da J${gw}: capitão <b>${O.c}</b>${O['chip' + gw] ? `, chip <b>${({wildcard: 'Wildcard', freehit: 'Free Hit', bboost: 'Bench Boost', '3xc': 'Triple Captain'})[O['chip' + gw]]}</b>` : ''}. Em baixo: os jogadores que só um de vocês tem decidem o jogo.` : ''; }
""")
rep("""      <p class="prose">5 dos 15 jogadores de cada plantel são os mesmos.""", """      <p class="prose">${H2H_SHARED.length} dos 15 jogadores de cada plantel são os mesmos.""")
rep("""          <thead><tr><th>Só o Frederico Borges tem</th><th>Pts esp.</th></tr></thead>""", """          <thead><tr><th>Só ${(V52.h2h && V52.h2h.O) ? V52.h2h.O.m : 'ele'} tem</th><th>Pts esp.</th></tr></thead>""")

# 5) depois do deadline: as sugestões da jornada fechada ficam marcadas como tal
JS2 = r"""
  // V52: depois do deadline, avisar no separador Transferências que as sugestões eram para a jornada que já começou
  function v52DeadlineNote() {
    const sv = document.querySelector('.view[data-view="semana"] > .subview[data-sub="transferencias"]'); if (!sv) return;
    let n = document.getElementById('v52-note');
    if (!v52After()) { if (n) n.remove(); return; }
    if (!n) { n = document.createElement('div'); n.id = 'v52-note'; n.className = 'callout info'; sv.insertBefore(n, sv.firstChild); }
    n.innerHTML = `<span class="icon">i</span><div class="body"><p><b>O deadline da J${GW_META.next} já passou.</b> As sugestões em baixo eram para a J${GW_META.next}; as da J${GW_META.next + 1} chegam com a atualização da jornada (depois de a J${GW_META.next} fechar). O plano automático e o manual já partem do plantel que tens agora.</p></div>`;
  }
  // no site, quando o live.json traz plantéis novos, refazer tudo o que depende deles
  function v52Rebuild() {
    try {
      window.__RL = null;
      v52FillSquad(SQUAD); v52Fill(ALL_PLAYERS, Object.values(SQUAD).flatMap(g => g.players.map(p => ({...p, pos: g.label, cls: g.cls}))));
      v52Fill(MARCO_SQUAD_CURRENT, v52MarcoSquad());
      v52Fill(CAPTAIN_DIST, v52Captains()); v52Fill(MY_LEAGUE_OWNERSHIP, v52MyOwnership('bruno')); v52Fill(MARCO_LEAGUE_OWNERSHIP, v52MyOwnership('marco'));
      v52Fill(TEMPLATE_GAPS, v52Gaps()); v52Fill(LEAGUE_BUDGETS, v52Budgets());
      const h = v52H2H(); V52.h2h = h; v52Fill(H2H_SHARED, h.shared); v52Fill(H2H_MINE_ONLY, h.mine); v52Fill(H2H_THEIRS_ONLY, h.theirs);
      v52Fill(ALT, v52Alt()); v52Fill(ENABLERS, v52Enablers());
      Object.keys(CHIPS_USED).forEach(k => delete CHIPS_USED[k]); Object.assign(CHIPS_USED, v52ChipsUsed());
    } catch (e) { console.error(e); }
    [() => renderLiga(), () => renderLigaBudgets(), () => renderH2H(), () => renderChips(), () => renderMarcoOwnership(), () => renderAlt(), () => renderEnablers(), () => renderOverview(), () => renderChipPlan(), () => renderTodo(), () => v52DeadlineNote(),
     () => { document.getElementById('marco-chips-summary').textContent = v52ChipTxt('marco'); }].forEach(f => { try { f(); } catch (e) { console.error(e); } });
  }
  v52DeadlineNote();
"""
rep("  renderRivals();\n  loadLive();\n", "  renderRivals();\n  loadLive();\n" + JS2)
# applyLive: no fim, refazer as tabelas
rep("    try { CMP.a = null; renderCompare(); } catch (e) {}\n", "    try { CMP.a = null; renderCompare(); } catch (e) {}\n    try { v52Rebuild(); } catch (e) { console.error(e); }\n")
H.write_text(s, encoding='utf-8', newline='\n')
print('ok')
