"""V61 (11 nov 2026): ícone da app no painel e separador "Notícias" em Esta semana.
- Painel: o quadrado "FPL" passa a ser o ícone da app (icons/icon-192.png; se a imagem faltar, fica o "FPL").
- Esta semana › Notícias: o que os treinadores disseram, lesões, seleções e calendário, com fonte e data.
  Dados em _build/research/noticias.json → const NEWS (escrita por _build/pool/noticias.py e pelo gen25.py).
  As notícias sobre o plantel (ou sobre a troca sugerida) do gestor escolhido aparecem primeiro e marcadas.
- Resumo: linha "Notícias: N importantes" com ligação ao separador.
- "Mais detalhes desta jornada" do Bruno: o cabeçalho tinha um resto de um patch antigo (\\g<1>8\\g<2>).
Uso (a partir da raiz): py -X utf8 _build/patches/patch61.py   (Linux: python3), depois py -X utf8 _build/pool/noticias.py"""
from pathlib import Path

H = Path(__file__).resolve().parents[2] / 'index.html'
s = H.read_text(encoding='utf-8')


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)


CSS = r'''
  /* ===================== V61: ícone da app no painel e Notícias ===================== */
  .brand-mark { position: relative; width: 38px; height: 38px; overflow: hidden; border-radius: 10px; }
  .brand-mark img { position: absolute; inset: 0; width: 100%; height: 100%; display: block; object-fit: cover; }
  .nw-f { display: flex; flex-wrap: wrap; gap: 6px; margin: 2px 0 14px; }
  .nw-list { display: grid; gap: 10px; }
  .nw-it { border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; background: var(--surface); }
  .nw-it.rel { border-color: var(--accent-mid); background: var(--accent-weak); }
  .nw-it.imp3 { box-shadow: inset 3px 0 0 var(--warn); }
  .nw-top { display: flex; flex-wrap: wrap; gap: 6px 8px; align-items: center; font-size: 12px; color: var(--muted); margin-bottom: 4px; }
  .nw-tag { font-size: 10.5px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; padding: 2px 7px; border-radius: 5px; background: var(--surface-2); color: var(--ink-2); border: 1px solid var(--line); }
  .nw-it h3 { margin: 0 0 4px; font-size: 16.5px; line-height: 1.25; }
  .nw-it p { margin: 0; font-size: 14px; line-height: 1.55; color: var(--ink-2); max-width: 78ch; }
  .nw-ft { display: flex; flex-wrap: wrap; gap: 6px 10px; align-items: center; justify-content: space-between; margin-top: 10px; }
  .nw-ps { display: flex; flex-wrap: wrap; gap: 6px; }
  .nw-p { font: inherit; font-size: 12.5px; font-weight: 600; color: var(--ink); background: var(--surface); border: 1px solid var(--line-strong); border-radius: 999px; padding: 3px 10px; cursor: pointer; }
  .nw-p:hover { border-color: var(--accent-mid); color: var(--accent-strong); }
  .nw-p small { font-weight: 500; color: var(--muted); }
  .nw-src { font-size: 12.5px; color: var(--muted); white-space: nowrap; }
  .nw-src:hover { color: var(--accent); }
  .nw-line button { font-size: inherit; }
'''
rep('</style>', CSS + '</style>')

# 1. painel: ícone da app em vez de "FPL"
rep('<div class="brand-mark" aria-hidden="true">FPL</div>',
    '<div class="brand-mark" aria-hidden="true">FPL<img src="icons/icon-192.png" alt="" onerror="this.remove()"></div>')

# 2. separador Notícias (a seguir ao Resumo)
rep('        <button class="subtab" type="button" data-sub="resumo">Resumo</button>\n',
    '        <button class="subtab" type="button" data-sub="resumo">Resumo</button>\n'
    '        <button class="subtab" type="button" data-sub="noticias">Notícias</button>\n')
rep('      </details>\n      </div>\n      <div class="subview" data-sub="onze" hidden>\n',
    '      </details>\n      </div>\n'
    '      <div class="subview" data-sub="noticias" hidden>\n'
    '        <section class="card" id="news-root"></section>\n'
    '        <section class="card" id="news-fpl"></section>\n'
    '      </div>\n'
    '      <div class="subview" data-sub="onze" hidden>\n')
rep('<div class="auto-line" id="auto-line" hidden></div>\n',
    '<div class="auto-line" id="auto-line" hidden></div>\n<div class="auto-line nw-line" id="news-line" hidden></div>\n')
rep('"subs": ["Resumo", "Onze e banco"', '"subs": ["Resumo", "Notícias", "Onze e banco"')
rep('{"v": "semana", "s": "onze", "a": "Esta semana", "n": "Onze e banco"',
    '{"v": "semana", "s": "noticias", "a": "Esta semana", "n": "Notícias", "syn": ["notícias", "noticias", "novidades", "treinador", "treinadores", "conferência de imprensa", "imprensa", "seleções", "selecções", "o que disse", "updates", "lesões da semana"]}, '
    '{"v": "semana", "s": "onze", "a": "Esta semana", "n": "Onze e banco"')
rep("const SIMPLE_KEEP = {semana: ['resumo', 'onze',", "const SIMPLE_KEEP = {semana: ['resumo', 'noticias', 'onze',")

# 3. resto de um patch antigo no cabeçalho do Bruno ("Mais detalhes desta jornada")
rep('              \\g<1>8\\g<2><ol class="todo-list" id="bruno-todo-list"></ol>\\n              <p class="note" id="bruno-todo-note"></p>\n',
    '              <div class="card-head"><div><h2>Antes do deadline — Brunorussia FC</h2><div class="card-sub">Três decisões para a J<span class="gw-n">8</span>.</div></div></div>\n'
    '              <ol class="todo-list" id="bruno-todo-list"></ol>\n              <p class="note" id="bruno-todo-note"></p>\n')

# 4. código do separador
JS = r'''
  // ---------- V61: Notícias da semana (research/noticias.json → const NEWS no bloco de dados) ----------
  var NW_F = 'todas';
  function nwData() { return (typeof NEWS !== 'undefined' && NEWS && Array.isArray(NEWS.items)) ? NEWS : {items: []}; }
  function nwEsc(t) { return String(t == null ? '' : t).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c])); }
  function nwDate(d) { const x = new Date(d + 'T12:00:00Z'); return isNaN(x) ? '' : `${['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'][x.getUTCDay()]} ${x.getUTCDate()} ${['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'][x.getUTCMonth()]}`; }
  // notícias com a marca do gestor: jogadores do plantel (sq) e os que entram na troca sugerida (sug); essas vêm primeiro
  function nwItems(mgr) {
    const sq = new Set(squadOf(mgr).filter(Boolean).map(p => p.id));
    const sug = new Set(((SUGGESTED_MOVES[mgr] || {}).transfers || []).map(m => m.in));
    return nwData().items.map(it => {
      const ids = (it.ids || []).filter(id => FULL_POOL_BY_ID[id]);
      const a = ids.filter(id => sq.has(id)), b = ids.filter(id => sug.has(id) && !sq.has(id));
      return Object.assign({}, it, {ids, sq: a, sug: b, rel: a.length || b.length ? 1 : 0});
    }).sort((x, y) => (y.rel - x.rel) || ((y.imp || 1) - (x.imp || 1)) || (x.d < y.d ? 1 : x.d > y.d ? -1 : 0));
  }
  function renderNews() {
    const el = document.getElementById('news-root'); if (!el) return;
    const mgr = curMgr(), N = nwData(), L = nwItems(mgr);
    const TAG = {selecoes: 'Seleções', lesao: 'Lesões', treinador: 'Treinadores', castigo: 'Castigos', calendario: 'Calendário', mercado: 'Mercado'};
    const tags = Object.keys(TAG).filter(t => L.some(it => it.tag === t));
    const F = NW_F === 'meu' || NW_F === 'todas' || tags.includes(NW_F) ? NW_F : 'todas';
    const show = L.filter(it => F === 'todas' || (F === 'meu' ? it.rel : it.tag === F));
    const nRel = L.filter(it => it.rel).length;
    const fb = (k, lbl) => `<button type="button" class="btn small${F === k ? ' primary' : ''}" data-nwf="${k}" aria-pressed="${F === k}">${lbl}</button>`;
    const upd = N.updated ? nwDate(N.updated) : '';
    const team = mgr === 'marco' ? 'Xarola Team' : 'Brunorussia FC';
    el.innerHTML = `
      <div class="card-head"><div><h2>Notícias da J${GW_META.next}</h2><div class="card-sub">O que os treinadores disseram, lesões, seleções e calendário — só o que pode mexer com a FPL. ${team}${upd ? ' · atualizado a ' + upd : ''}.</div></div></div>
      ${N.gw && N.gw < GW_META.next ? `<div class="callout"><span class="icon">!</span><div class="body"><p>Estas notícias são da J${N.gw}: ainda não foram atualizadas para a J${GW_META.next}.</p></div></div>` : ''}
      ${L.length ? `<div class="nw-f" role="group" aria-label="Filtrar notícias">${fb('todas', `Todas (${L.length})`)}${fb('meu', `Do meu plantel (${nRel})`)}${tags.map(t => fb(t, TAG[t])).join('')}</div>` : ''}
      <div class="nw-list">${show.length ? show.map(it => `
        <article class="nw-it imp${it.imp || 1}${it.rel ? ' rel' : ''}">
          <div class="nw-top"><span class="nw-tag">${TAG[it.tag] || it.tag}</span><span>${nwDate(it.d)}</span>
            ${it.sq.length ? `<span class="status-chip insquad">No ${mgr === 'marco' ? 'plantel do Marco' : 'teu plantel'}</span>` : ''}
            ${it.sug.length ? '<span class="status-chip watch">Troca sugerida (entra)</span>' : ''}
            ${(it.imp || 1) >= 3 ? '<span class="status-chip fall">Pode mudar a decisão</span>' : ''}</div>
          <h3>${nwEsc(it.t)}</h3>
          <p>${nwEsc(it.x)}</p>
          <div class="nw-ft"><span class="nw-ps">${it.ids.map(id => { const p = FULL_POOL_BY_ID[id]; return `<button type="button" class="nw-p" data-pid="${id}">${nwEsc(shortName(p.name))} <small>${SHORT(p.team)}</small></button>`; }).join('')}</span>
            ${/^https?:\/\//.test(it.url || '') ? `<a class="nw-src" href="${nwEsc(it.url)}" target="_blank" rel="noopener noreferrer">Fonte: ${nwEsc(it.src)} ↗</a>` : `<span class="nw-src">Fonte: ${nwEsc(it.src)}</span>`}</div>
        </article>`).join('') : `<p class="note">${L.length ? (F === 'meu' ? 'Nenhuma notícia desta semana fala de jogadores do teu plantel ou da troca sugerida.' : 'Nenhuma notícia neste filtro.') : 'Ainda não há notícias para esta jornada.'}</p>`}</div>
      <p class="note">As notícias vêm de sites e conferências de imprensa e podem mudar até ao deadline (${GW_META.deadlineLabel}). Toca num jogador para abrir a ficha. Os estados oficiais (lesionado, dúvida) e os pontos vêm sempre da FPL.</p>`;
    el.querySelectorAll('[data-nwf]').forEach(b => b.addEventListener('click', () => { NW_F = b.dataset.nwf; renderNews(); const n = el.querySelector(`[data-nwf="${NW_F}"]`); if (n) n.focus(); }));
    // avisos oficiais da FPL no plantel (e em quem entra na troca sugerida)
    const of = document.getElementById('news-fpl');
    if (of) {
      const inIds = ((SUGGESTED_MOVES[mgr] || {}).transfers || []).map(m => m.in);
      const ps = [...squadOf(mgr).filter(Boolean), ...inIds.map(id => FULL_POOL_BY_ID[id]).filter(Boolean)].filter((p, i, a) => a.indexOf(p) === i && p.status && p.status !== 'a');
      of.innerHTML = `<div class="card-head"><div><h2>Avisos oficiais da FPL</h2><div class="card-sub">${team} · jogadores do plantel (e da troca sugerida) com aviso no site da FPL</div></div></div>
        ${ps.length ? playerCards(ps, p => ({note: p.news || (STATUS_TXT[p.status] || ['—'])[0]})) : '<p class="note">Nenhum jogador do plantel tem aviso na FPL neste momento.</p>'}`;
    }
  }
  // Resumo: uma linha a dizer quantas notícias importantes há
  function nwLine() {
    const el = document.getElementById('news-line'); if (!el) return;
    const L = nwItems(curMgr()), rel = L.filter(it => it.rel).length, imp = L.filter(it => (it.imp || 1) >= 3).length;
    el.hidden = !L.length; if (!L.length) return;
    el.innerHTML = `Notícias da semana: <b>${L.length}</b>${rel ? ` · ${rel} sobre o ${curMgr() === 'marco' ? 'plantel do Marco' : 'teu plantel'}` : ''}${imp ? ` · ${imp} que ${imp === 1 ? 'pode' : 'podem'} mudar a decisão` : ''} — <button type="button" class="linklike" id="news-go">ver notícias</button>`;
    el.querySelector('#news-go').addEventListener('click', () => showView('semana', 'noticias'));
  }
  var NW_READY = true;
  lazyRender('semana/noticias', renderNews);
  try { nwLine(); } catch (e) { console.error(e); }
'''
rep("  function startTour(force) { tutWelcome(!!force); }\n", JS + "  function startTour(force) { tutWelcome(!!force); }\n")
rep("    try { renderAoVivo(); } catch (e) { console.error(e); }\n    try { if (typeof renderShortcuts === 'function' && typeof APP_INDEX !== 'undefined') renderShortcuts(); } catch (e) {}\n",
    "    try { renderAoVivo(); } catch (e) { console.error(e); }\n"
    "    try { if (typeof NW_READY !== 'undefined' && NW_READY) { lazyRender('semana/noticias', renderNews); nwLine(); } } catch (e) {}   // V61 (só depois do arranque)\n"
    "    try { if (typeof renderShortcuts === 'function' && typeof APP_INDEX !== 'undefined') renderShortcuts(); } catch (e) {}\n")

# 5. tutorial e versão
rep("      {id: 'avisos', ix: 'semana/resumo', since: 'V31', sel: '#alerts',",
    "      {id: 'noticias61', ix: 'semana/noticias', since: 'V61', sel: '#news-root', t: 'Notícias', d: () => `O que os treinadores disseram, lesões, jogos das seleções e mudanças de calendário desta semana, com a fonte e a data. As que falam do ${curMgr() === 'marco' ? 'plantel do Marco' : 'teu plantel'} ou da troca sugerida aparecem primeiro. Agora há ${tutSafe(() => nwItems(curMgr()).length, 0)}.`},\n"
    "      {id: 'avisos', ix: 'semana/resumo', since: 'V31', sel: '#alerts',")
rep("  var APP_VERSION = 'V60';", "  var APP_VERSION = 'V61';")
H.write_text(s, encoding='utf-8', newline='\n')
print('V61 aplicado')
