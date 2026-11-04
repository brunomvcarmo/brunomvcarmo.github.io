"""V48 (16 out 2026): atalhos (★) e recentes por gestor, botões de ligação entre ferramentas, ⚙ Definições
com modo simples/completo, tema e tutorial. Uso (a partir da raiz): py _build/patches/nav48.py"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
H = ROOT / 'index.html'
s = H.read_text(encoding='utf-8')
assert 'V48' not in s, 'já aplicado'


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:100], s.count(a))
    s = s.replace(a, b)


# ---------- data-go do "O que fazer" para os sítios novos ----------
ALIAS = json.loads(re.search(r'const VIEW_ALIAS = (\{.*?\});', s).group(1))
def go(m):
    v, sub = m.group(1), m.group(2)
    r = ALIAS.get(f'{v}-{sub}') or ALIAS.get(v)
    return f'data-go="{r[0]}|{r[1]}"' if r else m.group(0)
s = re.sub(r'data-go="([a-z]+)\|([a-z-]*)"', go, s)

# ---------- Resumo: cartão dos atalhos ----------
rep('      <div class="subview" data-sub="resumo">\n', '      <div class="subview" data-sub="resumo">\n<section class="card fav-card" id="fav-card"></section>\n')
# ---------- aviso do modo simples + ⚙ na barra ----------
rep('        <button type="button" class="theme-btn srch-btn" id="srch-btn"', '        <span class="set-wrap"><button type="button" class="theme-btn set-btn" id="set-btn" aria-label="Definições" aria-expanded="false" aria-controls="set-pop">⚙</button><div class="set-pop" id="set-pop" role="dialog" aria-label="Definições" hidden></div></span>\n        <button type="button" class="theme-btn srch-btn" id="srch-btn"')
rep('    <div class="statusbar">', '    <div class="statusbar">', 1)
s = s.replace('    <!-- ========== ESTA SEMANA (V47) ========== -->', '    <div class="callout info mode-note" id="mode-note" hidden></div>\n    <!-- ========== ESTA SEMANA (V47) ========== -->', 1)
# ---------- menu: atalhos no início ----------
rep('    <nav class="nav" aria-label="Áreas">\n      <div class="nav-group">', '    <nav class="nav" aria-label="Áreas">\n      <div class="nav-group nav-favs" id="nav-favs"></div>\n      <div class="nav-group">')

# ---------- cartão do jogador e ficha: Comparar / Pôr no plano ----------
rep("""        <div class="pc-id"><div class="pc-name"><span class="pc-nm">${shortName(p.name)}</span>${tags}</div><div class="pc-meta">${meta}</div>${o.note ? `<div class="pc-note">${o.note}</div>` : ''}</div>""",
    """        <div class="pc-id"><div class="pc-name"><span class="pc-nm">${shortName(p.name)}</span>${tags}</div><div class="pc-meta">${meta}</div>${o.note ? `<div class="pc-note">${o.note}</div>` : ''}${o.acts === false ? '' : pcActs(p, o.mine)}</div>""")
rep("""        <div class="pc-id"><div class="pc-name"><span class="pc-nm" data-pid="${p.id}">${p.name}</span></div><div class="pc-meta">${meta}</div>${o.note ? `<div class="pc-note">${o.note}</div>` : ''}</div>""",
    """        <div class="pc-id"><div class="pc-name"><span class="pc-nm" data-pid="${p.id}">${p.name}</span></div><div class="pc-meta">${meta}</div>${o.note ? `<div class="pc-note">${o.note}</div>` : ''}${o.acts === false ? '' : pcActs(p, o.mine)}</div>""")
rep("""      <div class="pc-tags">${tags}</div>
      ${p.news ? `<p class="note" style="margin:6px 0 0">Notícia oficial da FPL:""", """      <div class="pc-tags">${tags}</div>
      ${pcActs(p, !!mine)}
      ${p.news ? `<p class="note" style="margin:6px 0 0">Notícia oficial da FPL:""")
# ---------- rivais: Comparar / Equipa para lhe ganhar ----------
rep("""          <div class="riv-foot">Na J${HZ[0]}: ele ≈${f1(d.X.total)}""", """          <div class="pc-acts"><button type="button" class="pc-act" data-act="rcmp" data-e="${d.e}">Comparar</button><button type="button" class="pc-act" data-act="rwin" data-e="${d.e}">Equipa para lhe ganhar</button></div>
          <div class="riv-foot">Na J${HZ[0]}: ele ≈${f1(d.X.total)}""")
# ---------- avisos: substitutos, pôr no plano, jogadores afetados ----------
rep("""${p.news ? ` — ${p.news}` : ''}.`, {pid: p.id, isNew});""", """${p.news ? ` — ${p.news}` : ''}.`, {pid: p.id, isNew, act: 'subs', actTxt: 'Ver substitutos'});""")
rep("""se vais fazer a troca, faz antes.`, {pid: rising[0].id});""", """se vais fazer a troca, faz antes.`, {pid: rising[0].id, act: 'plan', actTxt: 'Pôr no plano'});""")
rep("""Já descontado nos pontos esperados.`, {goto: 'jogos', gotoSub: 'europa'});""", """Já descontado nos pontos esperados.`, {act: 'eu', actTxt: 'Ver os teus jogadores afetados'});""")
rep("""<span class="al-act">${a.goto ? `<button type="button" class="btn ghost" data-goto2="${a.goto}" data-gsub="${a.gotoSub || ''}">Ver</button>` : ''}</span>""",
    """<span class="al-act">${a.act ? `<button type="button" class="btn ghost" data-act="${a.act}" data-id="${a.pid || ''}">${a.actTxt}</button>` : ''}${a.goto ? `<button type="button" class="btn ghost" data-goto2="${a.goto}" data-gsub="${a.gotoSub || ''}">Ver</button>` : ''}</span>""")
# ---------- "O que fazer": linha das chips ----------
rep("""<div class="todo">${tr}${cap}${xi}</div>`;""", """<div class="todo">${tr}${cap}${xi}${chip || nextChip ? tile(4, 'Chips', chip ? 'todo' : 'ok', chip ? `Plano: <b>${CHIP_NAMES[chip] || chip}</b> nesta jornada (J${GW_META.next}).` : `Nada nesta jornada. A seguir no plano: <b>${CHIP_NAMES[nextChip[1].chip] || nextChip[1].chip}</b> na J${nextChip[0]}.`, `<button type="button" class="btn ghost" data-act="chips">Ver o plano de chips</button>`) : ''}</div>`;""")
# ---------- planeador: abrir com um jogador como entrada ----------
rep("""      const fillIn = () => { const s0 = stateBefore(mgr, PLAN_ADD.gw); inSel.innerHTML = inCandidates(mgr, s0, +outSel.value).map(c => `<option value="${c.p.id}">${c.p.name} · ${SHORT(c.p.team)} · £${c.p.price.toFixed(1)} · ${sgn(c.gain)}</option>`).join('') || '<option value="">Ninguém cabe no orçamento</option>'; };
      outSel.addEventListener('change', fillIn); fillIn();""",
    """      const fillIn = () => { const s0 = stateBefore(mgr, PLAN_ADD.gw); inSel.innerHTML = inCandidates(mgr, s0, +outSel.value).map(c => `<option value="${c.p.id}">${c.p.name} · ${SHORT(c.p.team)} · £${c.p.price.toFixed(1)} · ${sgn(c.gain)}</option>`).join('') || '<option value="">Ninguém cabe no orçamento</option>';
        // V48: "Pôr no plano" a partir de um cartão — o jogador escolhido fica como entrada (mesmo que não esteja entre os 40)
        const want = PLAN_ADD.inId && FULL_POOL_BY_ID[PLAN_ADD.inId];
        if (want && FULL_POOL_BY_ID[+outSel.value] && FULL_POOL_BY_ID[+outSel.value].cls === want.cls) {
          if (![...inSel.options].some(o => +o.value === want.id)) inSel.insertAdjacentHTML('afterbegin', `<option value="${want.id}">${want.name} · ${SHORT(want.team)} · £${want.price.toFixed(1)} (a confirmar o orçamento)</option>`);
          inSel.value = String(want.id);
        } };
      if (PLAN_ADD.inId && FULL_POOL_BY_ID[PLAN_ADD.inId] && !PLAN_ADD.outSet) {
        const want = FULL_POOL_BY_ID[PLAN_ADD.inId], s0 = stateBefore(mgr, PLAN_ADD.gw);
        const outs = s0.squadPrev.map(id => FULL_POOL_BY_ID[id]).filter(p => p && p.cls === want.cls).sort((a, b) => epAt(a, s0.gi) - epAt(b, s0.gi));
        if (outs[0]) outSel.value = String(outs[0].id);
        PLAN_ADD.outSet = true;
      }
      outSel.addEventListener('change', fillIn); fillIn();""")

# ---------- código V48 ----------
JS = r"""
  // ===================================================================
  // V48 (16 out 2026): atalhos (★) e "usaste recentemente" por gestor, botões de ligação entre ferramentas,
  // ⚙ Definições (modo simples/completo, tema, tutorial). Tudo guardado no browser.
  // ===================================================================
  var V48 = {mode: 'completo'};
  const SIMPLE_KEEP = {semana: ['resumo', 'onze', 'capitao', 'transferencias', 'registo'], competicao: ['classificacao', 'vigiar'], mercado: ['pesquisa']};
  const favK = () => 'fpl-favs-' + curMgr(), recK = () => 'fpl-recent-' + curMgr();
  const favList = () => lsGet(favK()) || [];
  const recList = () => lsGet(recK()) || [];
  function tokName(tok) {
    const i = tok.indexOf('-'), v = i < 0 ? tok : tok.slice(0, i), sub = i < 0 ? '' : tok.slice(i + 1);
    const A = APP_AREAS.find(a => a.v === v); if (!A) return null;
    if (!sub) return {v, sub, n: A.n, a: ''};
    const it = APP_INDEX.find(x => x.v === v && x.s === sub);
    return it ? {v, sub, n: it.n.replace(/<[^>]+>|\(\d*\)/g, '').trim(), a: A.n} : null;
  }
  const inSimple = (v, sub) => !!(SIMPLE_KEEP[v] && (!sub || SIMPLE_KEEP[v].includes(sub)));
  function toggleFav(tok) { const L = favList(); lsSet(favK(), L.includes(tok) ? L.filter(t => t !== tok) : [...L, tok]); renderShortcuts(); }
  function pushRecent(tok) { if (!tokName(tok)) return; const L = recList().filter(t => t !== tok); L.unshift(tok); lsSet(recK(), L.slice(0, 4)); }
  function chipBtn(tok, cls) { const t = tokName(tok); if (!t) return ''; return `<button type="button" class="${cls}" data-tok="${tok}" title="${t.a ? t.a + ' › ' : ''}${t.n}">${t.n}${t.a ? `<span class="a"> · ${t.a}</span>` : ''}</button>`; }
  function curTok() { return (location.hash || '').slice(1); }
  function renderShortcuts() {
    const F = favList().filter(tokName), cur = curTok(), R = recList().filter(t => t !== cur && tokName(t)).slice(0, 3);
    const card = document.getElementById('fav-card');
    if (card) card.innerHTML = `<div class="card-head"><div><h2>Os teus atalhos</h2><div class="card-sub">${curMgr() === 'marco' ? 'Xarola Team' : 'Brunorussia FC'} · toca na ☆ ao lado do título de uma área ou de um separador para a guardares aqui</div></div></div>
      <div class="fav-chips">${F.length ? F.map(t => chipBtn(t, 'fav-chip')).join('') : '<span class="note">Ainda não tens atalhos.</span>'}</div>
      ${R.length ? `<div class="fav-rec"><span class="note">Usaste recentemente:</span> ${R.map(t => chipBtn(t, 'fav-chip ghost')).join('')}</div>` : ''}`;
    const nav = document.getElementById('nav-favs');
    if (nav) nav.innerHTML = F.length || R.length ? `${F.length ? `<div class="nav-label">Os teus atalhos</div>${F.map(t => chipBtn(t, 'nav-fav')).join('')}` : ''}${R.length ? `<div class="nav-label">Usaste recentemente</div>${R.map(t => chipBtn(t, 'nav-fav rec')).join('')}` : ''}` : '';
    let mf = document.getElementById('mfav');
    const bar = document.querySelector('.mnav');
    if (!mf && bar) { mf = document.createElement('div'); mf.id = 'mfav'; mf.className = 'mfav'; bar.parentNode.insertBefore(mf, bar); }
    if (mf) { mf.innerHTML = F.map(t => chipBtn(t, 'fav-chip')).join(''); mf.hidden = !F.length; }
    // estrelas: área no título; separador atual ao lado dos separadores
    document.querySelectorAll('.view[data-view]').forEach(v => {
      const a = v.dataset.view, h1 = v.querySelector(':scope > .view-head h1');
      if (h1 && !h1.querySelector('.fav-star')) h1.insertAdjacentHTML('beforeend', ` <button type="button" class="fav-star" data-fav="${a}"></button>`);
      const tabs = v.querySelector(':scope > .subtabs');
      if (tabs && !v.querySelector(':scope > .fav-sub')) tabs.insertAdjacentHTML('afterend', `<button type="button" class="fav-star fav-sub" data-fav=""></button>`);
      const sel = tabs && tabs.querySelector('.subtab[aria-selected="true"]'), fs = v.querySelector(':scope > .fav-sub');
      if (fs) { const tok = sel ? `${a}-${sel.dataset.sub}` : ''; fs.dataset.fav = tok; const on = F.includes(tok), t = tokName(tok); fs.innerHTML = `${on ? '★' : '☆'} <span>${on ? 'Nos atalhos' : 'Guardar'}: ${t ? t.n : ''}</span>`; fs.setAttribute('aria-pressed', String(on)); fs.setAttribute('aria-label', `${on ? 'Tirar dos' : 'Pôr nos'} atalhos: ${t ? t.n : ''}`); }
      const fa = h1 && h1.querySelector('.fav-star');
      if (fa) { const on = F.includes(a); fa.textContent = on ? '★' : '☆'; fa.setAttribute('aria-pressed', String(on)); fa.setAttribute('aria-label', `${on ? 'Tirar dos' : 'Pôr nos'} atalhos: ${v.dataset.title}`); }
    });
  }
  document.addEventListener('click', ev => {
    const f = ev.target.closest('.fav-star[data-fav]'); if (f && f.dataset.fav) { ev.preventDefault(); toggleFav(f.dataset.fav); return; }
    const c = ev.target.closest('[data-tok]'); if (c) { ev.preventDefault(); const t = tokName(c.dataset.tok); if (t) showView(t.v, t.sub || undefined); }
  });
  // ---------- botões de ligação entre ferramentas ----------
  function pcActs(p, mine) {
    return `<div class="pc-acts"><button type="button" class="pc-act" data-act="cmp" data-id="${p.id}">Comparar</button>${mine ? '' : `<button type="button" class="pc-act" data-act="plan" data-id="${p.id}">Pôr no plano</button>`}</div>`;
  }
  function v48Act(act, id, e) {
    try { closePlayer(); } catch (err) {}
    const me = CMP_ENTRY[curMgr()];
    if (act === 'cmp') { if (!PL.sel.includes(id)) PL.sel = [...PL.sel, id].slice(-4); showView('mercado', 'comparador'); renderPc(); renderPlayers(); }
    else if (act === 'plan') { PLAN_ADD = {gw: HZ[0], inId: id}; showView('semana', 'transferencias'); renderPlanner(); const f = document.querySelector('#plan-root .plan-add'); if (f) f.scrollIntoView({block: 'center'}); }
    else if (act === 'rcmp') { CMP.a = me; CMP.b = e; showView('competicao', 'comparar'); renderCompare(); }
    else if (act === 'rwin') { WIN.mode = 'h2h'; WIN.start = 'squad'; WIN.mgr = curMgr(); WIN.oe = e; showView('competicao', 'ganhar'); renderWin(); }
    else if (act === 'subs') {
      const p = FULL_POOL_BY_ID[id]; if (!p) return;
      const st = SQUAD_STATE[curMgr()], x = st.players.find(y => y.id === id), budget = st.bank + (x ? x.sell : p.price);
      showView('mercado', 'pesquisa');
      const set = (sel, v) => { const el = document.getElementById(sel); if (!el) return; if (el.type === 'checkbox') el.checked = v; else el.value = v; };
      set('pl-q', ''); set('pl-pos', p.cls); set('pl-team', ''); set('pl-avail', true); set('pl-mine', false);
      const pr = document.getElementById('pl-price'); if (pr) { pr.value = String(Math.min(+pr.max, Math.max(+pr.min, Math.floor(budget * 2) / 2))); pr.dispatchEvent(new Event('input')); }
      renderPlayers();
      const note = document.getElementById('pl-subs-note');
      const html = `Substitutos de <b>${p.name}</b>: ${POS_SHORT[p.cls]}, disponíveis, até £${budget.toFixed(1)}M (banco £${st.bank.toFixed(1)}M + preço de venda dele). Com o filtro de preço em passos de £0,5M.`;
      if (note) note.innerHTML = html; else { const f = document.getElementById('pl-filters'); if (f) f.insertAdjacentHTML('afterend', `<p class="note" id="pl-subs-note">${html}</p>`); }
    }
    else if (act === 'eu') { EU_SEL = HZ[0]; showView('jogos', 'europa'); renderEuroGw(); }
    else if (act === 'chips') { showView('semana', 'chips'); }
  }
  document.addEventListener('click', ev => {
    const b = ev.target.closest('[data-act]'); if (!b) return;
    ev.preventDefault(); ev.stopPropagation();
    try { v48Act(b.dataset.act, +b.dataset.id || 0, +b.dataset.e || 0); } catch (err) { console.error(err); }
  }, true);
  // ---------- ⚙ Definições: modo simples/completo, tema, tutorial ----------
  function applyMode() {
    V48.mode = lsGet('fpl-mode') === 'simples' ? 'simples' : 'completo';
    const simple = V48.mode === 'simples';
    document.body.classList.toggle('mode-simple', simple);
    document.querySelectorAll('.nav-item[data-view]').forEach(b => { b.hidden = simple && !SIMPLE_KEEP[b.dataset.view]; });
    document.querySelectorAll('.mnav-btn[data-v]').forEach(b => { b.hidden = simple && !SIMPLE_KEEP[b.dataset.v]; });
    const bar = document.querySelector('.mnav'); if (bar) bar.style.gridTemplateColumns = `repeat(${bar.querySelectorAll('.mnav-btn:not([hidden])').length}, minmax(0, 1fr))`;
    document.querySelectorAll('.view[data-view]').forEach(v => v.querySelectorAll(':scope > .subtabs .subtab').forEach(t => { t.hidden = simple && !(SIMPLE_KEEP[v.dataset.view] || []).includes(t.dataset.sub); }));
    document.querySelectorAll('.adv-link').forEach(b => { b.hidden = simple; });
  }
  function modeNote(name, sub) {
    const el = document.getElementById('mode-note'); if (!el) return;
    if (V48.mode === 'simples' && !inSimple(name, sub)) {
      el.hidden = false;
      el.innerHTML = `<span class="icon">i</span><div class="body"><p><b>Esta ferramenta é do modo completo.</b> Abri-a na mesma; no modo simples não aparece no menu. <button type="button" class="linklike" id="mode-full">Mudar para o modo completo</button></p></div>`;
      el.querySelector('#mode-full').addEventListener('click', () => { lsSet('fpl-mode', 'completo'); applyMode(); renderSettings(); showView(name, sub); });
    } else el.hidden = true;
  }
  const isDarkNow = () => { const t = document.documentElement.getAttribute('data-theme'); return t ? t === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches; };
  function renderSettings() {
    const pop = document.getElementById('set-pop'); if (!pop) return;
    const seg = (k, items, cur) => `<div class="seg" role="group" data-k="${k}">${items.map(([v, t]) => `<button type="button" class="seg-btn" data-v="${v}" aria-pressed="${v === cur}">${t}</button>`).join('')}</div>`;
    pop.innerHTML = `<h3>Definições</h3>
      <div class="set-row"><div class="riv-lbl">Modo</div>${seg('mode', [['completo', 'Completo'], ['simples', 'Simples']], V48.mode)}
        <p class="note">${V48.mode === 'simples' ? 'Só o essencial: Esta semana, Classificação, Vigiar rivais e a pesquisa de jogadores.' : 'A app inteira.'} A pesquisa encontra sempre tudo.</p></div>
      <div class="set-row"><div class="riv-lbl">Tema</div>${seg('theme', [['light', 'Claro'], ['dark', 'Escuro']], isDarkNow() ? 'dark' : 'light')}</div>
      <div class="set-row"><button type="button" class="btn ghost" id="set-tour">Ver o tutorial</button></div>
      <p class="note">Guardado neste browser.</p>`;
    pop.querySelectorAll('.seg[data-k="mode"] .seg-btn').forEach(b => b.addEventListener('click', () => {
      lsSet('fpl-mode', b.dataset.v); applyMode(); renderSettings();
      const t = curTok(), i = t.indexOf('-'); const v = i < 0 ? t : t.slice(0, i), sub = i < 0 ? '' : t.slice(i + 1);
      if (V48.mode === 'simples' && !inSimple(v, sub)) showView('semana', 'resumo'); else modeNote(v, sub);
    }));
    pop.querySelectorAll('.seg[data-k="theme"] .seg-btn').forEach(b => b.addEventListener('click', () => {
      const want = b.dataset.v; if ((isDarkNow() ? 'dark' : 'light') !== want) { const tb = document.getElementById('theme-btn'); if (tb) tb.click(); else { document.documentElement.setAttribute('data-theme', want); try { localStorage.setItem('fpl-theme', want); } catch (e) {} } }
      renderSettings();
    }));
    pop.querySelector('#set-tour').addEventListener('click', () => { closeSettings(); startTour(true); });
  }
  function closeSettings() { const pop = document.getElementById('set-pop'), b = document.getElementById('set-btn'); if (pop) pop.hidden = true; if (b) b.setAttribute('aria-expanded', 'false'); }
  (function settingsInit() {
    const b = document.getElementById('set-btn'), pop = document.getElementById('set-pop'); if (!b || !pop) return;
    b.addEventListener('click', ev => { ev.stopPropagation(); const open = pop.hidden; if (open) renderSettings(); pop.hidden = !open; b.setAttribute('aria-expanded', String(open)); });
    document.addEventListener('click', ev => { if (!pop.hidden && !ev.target.closest('.set-wrap')) closeSettings(); });
    document.addEventListener('keydown', ev => { if (ev.key === 'Escape') closeSettings(); });
  })();
"""
anchor = "  // ---------- Pesquisa (V47): ferramentas e separadores (com sinónimos), jogadores e gestores da liga ----------"
rep(anchor, JS + anchor)
# showView: recentes, aviso do modo, estrelas; no modo simples o separador por defeito é o 1.º visível
rep("""      if (!tabs.some(t => t.dataset.sub === sub)) sub = tabs[0].dataset.sub;""", """      if (!tabs.some(t => t.dataset.sub === sub)) sub = (tabs.find(t => !t.hidden) || tabs[0]).dataset.sub;""")
rep("""    try { history.replaceState(null, '', '#' + token); } catch (e) {}
    try { localStorage.setItem('fpl-view', token); } catch (e) {}""", """    try { history.replaceState(null, '', '#' + token); } catch (e) {}
    try { localStorage.setItem('fpl-view', token); } catch (e) {}
    try { pushRecent(token); modeNote(name, sub); renderShortcuts(); } catch (e) { console.error(e); }""")
# arranque: aplicar o modo antes da 1.ª área; mudar de gestor redesenha os atalhos
rep("""  let startTok = parseToken(location.hash.slice(1));""", """  try { applyMode(); } catch (e) { console.error(e); }
  let startTok = parseToken(location.hash.slice(1));""")
rep("""    try { renderAoVivo(); } catch (e) { console.error(e); }""", """    try { renderAoVivo(); } catch (e) { console.error(e); }
    try { if (typeof renderShortcuts === 'function' && typeof APP_INDEX !== 'undefined') renderShortcuts(); } catch (e) {}""")
# guia: o passo do tema passa a ser o das Definições
rep("""    {sel: '#theme-btn', t: 'Modo noite e nomes', d: 'Este botão muda entre claro e escuro. E em qualquer sítio da app, toca no nome de um jogador para abrires a ficha dele.'},""",
    """    {sel: '#set-btn', t: 'Definições e atalhos', d: 'Em ⚙ escolhes o modo simples (só o essencial) ou completo, o tema claro ou escuro, e revês este guia. Toca na ☆ ao lado de um título para o pores nos teus atalhos. E em qualquer sítio, toca no nome de um jogador para abrires a ficha.'},""")

# ---------- estilos ----------
i = s.index('</style>')
s = s[:i] + """  /* V48: atalhos, ligações, definições */
  .fav-star { border: 0; background: none; cursor: pointer; color: var(--warn); font-size: 20px; line-height: 1; padding: 2px 4px; vertical-align: 3px; border-radius: 6px; }
  .fav-star:hover { background: var(--surface-2); }
  .fav-sub { display: inline-flex; align-items: center; gap: 6px; font: inherit; font-size: 12.5px; color: var(--muted); margin: -10px 0 14px; padding: 3px 6px; vertical-align: 0; }
  .fav-sub[aria-pressed="true"] { color: var(--warn); }
  .fav-sub span { color: var(--ink-2); }
  .fav-chips, .fav-rec { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
  .fav-rec { margin-top: 10px; }
  .fav-chip { font: inherit; font-size: 13px; font-weight: 600; border: 1px solid var(--accent-mid); background: var(--accent-weak); color: var(--accent-strong); border-radius: 999px; padding: 4px 11px; cursor: pointer; }
  .fav-chip .a { font-weight: 400; color: var(--muted); }
  .fav-chip.ghost { background: var(--surface); border-color: var(--line-strong); color: var(--ink-2); font-weight: 500; }
  .nav-favs:empty { display: none; }
  .nav-favs { margin-bottom: 10px; }
  .nav-fav { text-align: left; font: inherit; font-size: 13px; border: 0; background: none; color: var(--accent-strong); padding: 5px 10px; border-radius: 7px; cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .nav-fav .a { color: var(--muted); font-size: 11.5px; }
  .nav-fav.rec { color: var(--ink-2); }
  .nav-fav:hover { background: var(--surface-2); }
  .mfav { display: none; }
  .pc-acts { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 5px; }
  .pc-act { font: inherit; font-size: 11.5px; font-weight: 600; border: 1px solid var(--line-strong); background: var(--surface); color: var(--accent-strong); border-radius: 6px; padding: 2px 8px; cursor: pointer; }
  .pc-act:hover { border-color: var(--accent-mid); background: var(--accent-weak); }
  .set-wrap { position: relative; display: inline-flex; }
  .set-pop { position: absolute; right: 0; top: calc(100% + 6px); z-index: 70; width: min(320px, 86vw); background: var(--surface); border: 1px solid var(--line-strong); border-radius: 12px; box-shadow: var(--shadow); padding: 14px; }
  .set-pop h3 { margin: 0 0 8px; }
  .set-row { margin-bottom: 12px; }
  .set-row .seg { margin: 4px 0 0; }
  .mode-note { margin: 12px 0 0; }
  @media (max-width: 960px) {
    .mfav { display: flex; flex-wrap: nowrap; gap: 6px; overflow-x: auto; padding-bottom: 6px; scrollbar-width: thin; }
    .mfav[hidden] { display: none; }
    .mfav .fav-chip { flex: 0 0 auto; font-size: 12.5px; }
  }
""" + s[i:]
H.write_text(s, encoding='utf-8', newline='\n')
print('ok')
