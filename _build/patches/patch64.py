"""V64 (26 nov 2026): arrumação — 40 separadores em 17, 5 áreas, sem o Avançado no menu (a pedido: "a app está muito
confusa; coisas que façam coisas meio parecidas podem ser fundidas").
Cada separador antigo passa a ser uma "parte" (data-part="área/separador antigo") de um separador novo: aberta, ou
fechada num <details> que se abre ao tocar. A arrumação é feita ao abrir a app (v64Arrange, logo a seguir ao
VIEW_ALIAS): o conteúdo de cada ferramenta não muda. Endereços, ligações, passos do tutorial, atalhos guardados e
pesquisas antigas continuam a funcionar: o showView reencaminha-os (V64_REMAP), abre a parte e rola até ela.
Também: o Resumo fica curto (sem os gráficos, a previsão, a estratégia e os super diferenciais, que já estão noutros
separadores), as duplas e brancas só nas Chips, e as Regras e fontes no ⚙ e no rodapé.
Uso (a partir da raiz): py -X utf8 _build/patches/patch64.py   (Linux: python3)"""
import re
from pathlib import Path

H = Path(__file__).resolve().parents[2] / 'index.html'
s = H.read_text(encoding='utf-8')


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:100], s.count(a))
    s = s.replace(a, b)


CSS = r'''
  /* ===================== V64: arrumação — partes dentro de um separador ===================== */
  .parts-nav { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
  .parts-nav .note { margin-right: 2px; }
  .parts-go { font: inherit; font-size: 12.5px; font-weight: 600; border: 1px solid var(--line); background: var(--surface); color: var(--ink-2); border-radius: 999px; padding: 5px 12px; cursor: pointer; }
  .parts-go:hover { border-color: var(--accent-mid); color: var(--accent-strong); }
  .part { display: grid; gap: 16px; min-width: 0; scroll-margin-top: 12px; }
  .part > .subview { min-width: 0; }
  details.part { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--shadow); }
  details.part > summary { list-style: none; cursor: pointer; padding: 14px 18px; display: grid; grid-template-columns: 1fr auto; gap: 2px 10px; align-items: center; border-radius: var(--radius); }
  details.part > summary::-webkit-details-marker { display: none; }
  details.part > summary:hover { background: var(--surface-2); }
  details.part > summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .part-t { font-family: var(--font-display); font-size: 17px; font-weight: 700; color: var(--ink); }
  .part-d { grid-column: 1; font-size: 13px; color: var(--muted); }
  .part-i { grid-column: 2; grid-row: 1 / span 2; font-size: 12.5px; font-weight: 600; color: var(--accent); white-space: nowrap; }
  .part-i::after { content: " ▾"; }
  details.part:not([open]) { gap: 0; }
  details.part[open] { background: transparent; border-color: transparent; box-shadow: none; }
  details.part[open] > summary { padding: 8px 2px 0; }
  details.part[open] > summary:hover { background: transparent; }
  details.part[open] .part-i::after { content: " ▴"; }
  .v64-off { display: none !important; }
  .nav-adv, .nav-item.adv { display: none !important; }
'''
rep('</style>', CSS + '</style>')

# ---------- 1. o mapa novo e a arrumação (logo a seguir ao VIEW_ALIAS, antes de tudo o resto) ----------
JS = r'''
  // ===== V64 (26 nov 2026): arrumação — 40 separadores em 17, 5 áreas (o Avançado sai do menu) =====
  // Cada separador antigo é agora uma "parte" (data-part="área/separador antigo") de um separador novo: aberta, ou
  // fechada num <details> (1 no 3.º campo). Os endereços antigos continuam a funcionar: o showView reencaminha-os
  // (V64_REMAP), abre a parte e rola até ela; o lazyRender e os passos do tutorial usam as chaves antigas.
  var V64_TABS = {
    semana: [['resumo', 'Resumo', [['semana/resumo', 'Resumo']]],
      ['onze', 'Onze e capitão', [['semana/onze', 'Onze e banco'], ['semana/capitao', 'Capitão']]],
      ['transferencias', 'Transferências', [['semana/transferencias', 'Transferências'], ['semana/registo', 'Registar o que fiz']]],
      ['chips', 'Chips', [['semana/chips', 'Chips']]],
      ['noticias', 'Notícias', [['semana/noticias', 'Notícias']]]],
    jogos: [['jornada', 'Esta jornada', [['jogos/jornada', 'Jogos da jornada'], ['jogos/onzes', 'Onzes prováveis']]],
      ['aovivo', 'Ao vivo', [['jogos/aovivo', 'Ao vivo']]],
      ['calendario', 'Calendário', [['avancado/equipas', 'Calendário e equipas'], ['jogos/europa', 'Europa e descanso', 1, 'Quem jogou a meio da semana e quanto descansa antes de cada jornada']]]],
    competicao: [['classificacao', 'Classificação', [['competicao/classificacao', 'Classificação'],
        ['competicao/previsao', 'Previsão da classificação', 1, 'Onde deves acabar daqui a 5 jornadas, com simulações'],
        ['competicao/orcamentos', 'Orçamentos e chips', 1, 'O orçamento e as chips que cada gestor ainda tem']]],
      ['adversario', 'Adversário', [['competicao/h2h', 'H2H'],
        ['competicao/comparar', 'Comparar com qualquer gestor', 1, 'Lado a lado, jogador a jogador, com qualquer gestor da liga'],
        ['competicao/ganhar', 'Equipa para ganhar a…', 1, 'A equipa com mais hipóteses de ganhar a um rival ou de o apanhar']]],
      ['liga', 'A liga', [['competicao/vigiar', 'Vigiar rivais'],
        ['avancado/capitaes', 'Capitães da liga', 1, 'Quem os outros 19 puseram de capitão'],
        ['avancado/lacunas', 'Picks em falta', 1, 'Jogadores que muitos rivais têm e tu não'],
        ['avancado/posse', 'O plantel vs. a liga', 1, 'Quantos rivais têm cada jogador do teu plantel']]]],
    mercado: [['pesquisa', 'Pesquisa', [['mercado/pesquisa', 'Pesquisa'],
        ['mercado/forma', 'Em forma', 1, 'Quem mais pontuou nas últimas jornadas'],
        ['mercado/precos', 'Preços e alternativas', 1, 'Quem vai subir ou descer de preço e alternativas mais baratas'],
        ['mercado/lesoes', 'Lesões e castigos', 1, 'Quem está lesionado ou castigado e quando volta'],
        ['mercado/discorda', 'Onde a app discorda', 1, 'Onde a app e os sites não estão de acordo, e quem tem tido razão'],
        ['avancado/hot', 'Diferenciais', 1, 'Jogadores que pouca gente tem e que podem surpreender']]],
      ['comparador', 'Comparador', [['mercado/comparador', 'Comparador']]],
      ['lab', 'Laboratório', [['mercado/lab', 'Laboratório'],
        ['mercado/ideal', 'Equipa ideal', 1, 'Os 15 com mais pontos esperados dentro do orçamento'],
        ['mercado/simulada', 'Equipa simulada', 1, 'Uma equipa montada de raiz, comparada com a liga'],
        ['avancado/simulador', 'Simulador de trocas', 1, 'Testa trocas no teu plantel e vê as melhores para as próximas 5']]]],
    epoca: [['evolucao', 'Evolução', [['epoca/evolucao', 'Evolução e ranking']]],
      ['jornada', 'Jornada a jornada', [['epoca/jornada', 'Por jornada'], ['epoca/detalhe', 'Jogador a jogador'],
        ['epoca/orcamento', 'Orçamento do plantel', 1, 'Para onde vai o dinheiro do plantel e quem liberta orçamento']]],
      ['acerto', 'Acerto da app', [['epoca/previsoes', 'Previsões contra o real'],
        ['avancado/calibracao', 'Calibração automática', 1, 'Como a app corrige sozinha as previsões']]]],
    avancado: [['regras', 'Regras e fontes', [['avancado/regras', 'Regras e fontes']]]],
  };
  var V64_DESC = {
    semana: 'O que fazer antes do deadline: o resumo, o onze e o capitão, as transferências, as chips e as notícias.',
    jogos: 'Os jogos da jornada com os onzes prováveis, os pontos ao vivo e o calendário das próximas jornadas.',
    competicao: 'A liga clássica e o H2H: a classificação (agora e prevista), o teu adversário e o que a liga anda a fazer.',
    mercado: 'Procurar, comparar e experimentar jogadores e equipas.',
    epoca: 'Como tem corrido a tua época: a evolução, jornada a jornada e quanto a app acerta.',
    avancado: 'Como funcionam os pontos, de onde vem cada número e o histórico de versões da app.'};
  var V64_REMAP = {};
  Object.keys(V64_TABS).forEach(v => V64_TABS[v].forEach(([s, n, parts]) => parts.forEach(([key, title, det], i) => { V64_REMAP[key] = {v, s, part: key, i, det: !!det, title: title || n}; })));
  function v64Key(v, s) { const R = V64_REMAP[v + '/' + (s || '')]; return R ? R.v + '/' + R.s : v + '/' + (s || ''); }
  function v64Tok(tok) { if (!tok) return tok; const i = tok.indexOf('-'); if (i < 0) return tok; const R = V64_REMAP[tok.slice(0, i) + '/' + tok.slice(i + 1)]; return R ? R.v + '-' + R.s : tok; }
  function v64PartEl(key) { return document.querySelector(`[data-part="${key}"]`); }
  function v64PartVisible(key) {
    const el = v64PartEl(key); if (!el) return null;
    const view = el.closest('.view'), sv = el.parentElement;
    return !!(view && !view.hidden && sv && !sv.hidden && (el.tagName !== 'DETAILS' || el.open));
  }
  // o que corria quando o separador antigo era aberto (lazyRender e as duas ferramentas pesadas)
  var V64_HOOK = {'competicao/previsao': () => renderPrevisao(), 'mercado/ideal': () => idealOpen()};
  function v64PartOpened(key) {
    const el = v64PartEl(key); if (el) el._v64 = Date.now();
    const LZ = window.__LAZY && window.__LAZY[key];
    if (LZ) { delete window.__LAZY[key]; LZ.forEach(f => { try { f(); } catch (e) { console.error(e); } }); }
    if (V64_HOOK[key]) { try { V64_HOOK[key](); } catch (e) { console.error(e); } }
  }
  function v64OpenPart(key, scroll) {
    const el = v64PartEl(key); if (!el) return;
    if (el.tagName === 'DETAILS' && !el.open) { el._v64 = Date.now(); el.open = true; }
    v64PartOpened(key);
    if (scroll) setTimeout(() => el.scrollIntoView({block: 'start'}), 60);
  }
  function v64Arrange() {
    const OLD = {}, BADGE = {};
    document.querySelectorAll('.view[data-view] > .subview[data-sub]').forEach(sv => { OLD[sv.closest('.view').dataset.view + '/' + sv.dataset.sub] = sv; });
    document.querySelectorAll('.view[data-view] > .subtabs .subtab').forEach(t => { const k = t.closest('.view').dataset.view + '/' + t.dataset.sub, L = [...t.querySelectorAll('[id]')]; if (L.length) BADGE[k] = L; });
    Object.keys(V64_TABS).forEach(v => {
      const view = document.querySelector(`.view[data-view="${v}"]`); if (!view) return;
      const bar = view.querySelector(':scope > .subtabs');
      if (bar) bar.innerHTML = V64_TABS[v].map(([s, n]) => `<button class="subtab" type="button" data-sub="${s}">${n}</button>`).join('');
      // contadores que viviam dentro dos botões antigos (ex.: #cmp-count) passam para o botão do separador novo
      if (bar) V64_TABS[v].forEach(([s, n, parts]) => parts.forEach(([k]) => (BADGE[k] || []).forEach(e => { const t = bar.querySelector(`.subtab[data-sub="${s}"]`); if (t) { t.append(' '); t.appendChild(e); } })));
      const hp = view.querySelector(':scope > .view-head p'); if (hp && V64_DESC[v]) hp.textContent = V64_DESC[v];
      V64_TABS[v].forEach(([s, n, parts]) => {
        const sv = document.createElement('div'); sv.className = 'subview'; sv.dataset.sub = s; sv.hidden = true;
        if (parts.length > 1) sv.insertAdjacentHTML('beforeend', `<div class="parts-nav" role="group" aria-label="Nesta página"><span class="note">Nesta página:</span>${parts.map(([k, t]) => `<button type="button" class="parts-go" data-part-go="${k}">${t}</button>`).join('')}</div>`);
        parts.forEach(([key, title, det, desc], i) => {
          const old = OLD[key]; if (!old) { console.warn('V64: falta o separador', key); return; }
          const w = document.createElement(det ? 'details' : 'section');
          w.className = 'part'; w.dataset.part = key; w.id = 'part-' + key.replace('/', '-');
          if (det) w.innerHTML = `<summary><span class="part-t">${title}</span><span class="part-i">Abrir</span>${desc ? `<span class="part-d">${desc}</span>` : ''}</summary>`;
          else if (i > 0) w.innerHTML = `<div class="sec-div">${title}</div>`;
          old.hidden = false; w.appendChild(old); sv.appendChild(w);
        });
        view.appendChild(sv);
      });
    });
    // o Avançado fica só com as Regras e fontes (no ⚙ e no rodapé)
    const av = document.querySelector('.view[data-view="avancado"]');
    if (av) { av.dataset.title = 'Regras e fontes'; const h = av.querySelector(':scope > .view-head h1'); if (h) h.textContent = 'Regras e fontes'; }
    // Resumo curto: o que já está noutros separadores sai daqui; as duplas e brancas ficam só nas Chips
    ['glance', 'glance2', 'dis59-resumo', 'dgw-jogos'].forEach(id => { const e = document.getElementById(id); if (e) e.classList.add('v64-off'); });
    // no Calendário, a tabela das próximas 6 jornadas vem primeiro
    const fx = document.getElementById('fixture-swing-body'), eq = v64PartEl('avancado/equipas');
    if (fx && eq) { const card = fx.closest('section.card'), body = eq.querySelector(':scope > .subview'); if (card && body) { const d = card.previousElementSibling; body.insertBefore(card, body.firstChild); if (d && d.classList.contains('sec-div')) body.insertBefore(d, card); } }
    // abrir/fechar as partes e a linha "Nesta página"
    document.addEventListener('click', ev => { const b = ev.target.closest('[data-part-go]'); if (b) { ev.preventDefault(); v64OpenPart(b.dataset.partGo, true); } });
    document.addEventListener('toggle', ev => { const d = ev.target; if (d && d.matches && d.matches('details.part') && d.open && !(d._v64 && Date.now() - d._v64 < 600)) v64PartOpened(d.dataset.part); }, true);
  }
  v64Arrange();
  // índice (menu, Procurar, atalhos): um item por separador novo; as partes ficam com o nome delas e "onde" estão agora
  (function v64Index() {
    const aName = v => v === 'avancado' ? 'Regras e fontes' : ((APP_AREAS.find(a => a.v === v) || {}).n || v);
    const tabN = {}; Object.keys(V64_TABS).forEach(v => V64_TABS[v].forEach(([s, n]) => { tabN[v + '/' + s] = n; }));
    const out = [], plain = x => !x.h && !x.act && x.v;
    Object.keys(V64_TABS).forEach(v => V64_TABS[v].forEach(([s, n, parts]) => {
      const main = APP_INDEX.find(x => plain(x) && x.v + '/' + x.s === parts[0][0]) || {syn: []};
      const syn = [...new Set([...(main.syn || []), n.toLowerCase(), String(main.n || '').toLowerCase()].filter(Boolean))];
      out.push(Object.assign({}, main, {v, s, a: aName(v), n, syn}));
      parts.slice(1).forEach(([k]) => { const e = APP_INDEX.find(x => plain(x) && x.v + '/' + x.s === k); if (e) out.push(Object.assign({}, e, {a: aName(v) + ' › ' + n})); });
    }));
    APP_INDEX.filter(x => !plain(x)).forEach(x => { const R = x.v ? V64_REMAP[x.v + '/' + x.s] : null; out.push(R ? Object.assign({}, x, {a: aName(R.v) + ' › ' + tabN[R.v + '/' + R.s]}) : x); });
    APP_INDEX.splice(0, APP_INDEX.length, ...out);
    APP_AREAS.forEach(A => { if (V64_TABS[A.v]) { A.subs = V64_TABS[A.v].map(t => t[1]); if (V64_DESC[A.v]) A.d = V64_DESC[A.v]; } if (A.v === 'avancado') A.n = 'Regras e fontes'; });
  })();
'''
m = re.search(r"\n  const VIEW_ALIAS = \{.*?\};\n", s)
assert m and s.count('\n  const VIEW_ALIAS = {') == 1
s = s[:m.end()] + JS + s[m.end():]

# ---------- 2. showView: reencaminhar, correr o que as partes abertas precisam, migalhas com a parte ----------
rep("    if (!viewNames.includes(name)) name = 'semana';\n    const view = views.find(v => v.dataset.view === name);",
    "    let openPart = null;   // V64: separadores antigos → separador novo + parte\n"
    "    { const R = V64_REMAP[name + '/' + (sub || '')]; if (R) { openPart = R; name = R.v; sub = R.s; } }\n"
    "    if (!viewNames.includes(name)) name = 'semana';\n    const view = views.find(v => v.dataset.view === name);")
rep("    [name, name + '/' + sub].forEach(k => { const LZ = window.__LAZY && window.__LAZY[k]; if (LZ) { delete window.__LAZY[k]; LZ.forEach(f => { try { f(); } catch (e) { console.error(e); } }); } });\n"
    "    if (name === 'competicao' && sub === 'previsao') { try { renderPrevisao(); } catch (e) { console.error(e); } }\n"
    "    if (name === 'mercado' && sub === 'ideal') { try { idealOpen(); } catch (e) { console.error(e); } }\n",
    "    { const LZ = window.__LAZY && window.__LAZY[name]; if (LZ) { delete window.__LAZY[name]; LZ.forEach(f => { try { f(); } catch (e) { console.error(e); } }); } }\n"
    "    // V64: cada parte aberta do separador corre o que o separador antigo corria (lazyRender, Previsão, Equipa ideal)\n"
    "    if (openPart && openPart.det) { const pe = v64PartEl(openPart.part); if (pe && !pe.open) { pe._v64 = Date.now(); pe.open = true; } }\n"
    "    { const svNow = view.querySelector(`:scope > .subview[data-sub=\"${sub}\"]`); if (svNow) svNow.querySelectorAll(':scope > [data-part]').forEach(pe => { if (pe.tagName !== 'DETAILS' || pe.open) v64PartOpened(pe.dataset.part); }); }\n")
rep("    document.getElementById('crumbs').innerHTML = subLabel ? `${title} <span aria-hidden=\"true\">›</span> <b>${subLabel}</b>` : `<b>${title}</b>`;",
    "    document.getElementById('crumbs').innerHTML = subLabel ? `${title} <span aria-hidden=\"true\">›</span> <b>${subLabel}</b>${openPart && openPart.i > 0 ? ` <span aria-hidden=\"true\">›</span> <b>${openPart.title}</b>` : ''}` : `<b>${title}</b>`;")
rep("    if (!opts.keepScroll) window.scrollTo(0, 0);\n",
    "    if (!opts.keepScroll) window.scrollTo(0, 0);\n"
    "    if (openPart && openPart.i > 0) { const pe = v64PartEl(openPart.part); if (pe) setTimeout(() => pe.scrollIntoView({block: 'start'}), 60); }   // V64: rola até à parte\n")

# ---------- 3. lazyRender e os sítios que procuravam o separador antigo diretamente ----------
rep("    const sv = b && v ? v.querySelector(`:scope > .subview[data-sub=\"${b}\"]`) : null;\n"
    "    if (v && !v.hidden && (!b || (sv && !sv.hidden))) { fn(); return; }\n",
    "    const sv = b && v ? v.querySelector(`:scope > .subview[data-sub=\"${b}\"]`) : null;\n"
    "    const pv = b ? v64PartVisible(view) : null;   // V64: as chaves antigas são partes de um separador novo\n"
    "    if (pv === true || (pv === null && v && !v.hidden && (!b || (sv && !sv.hidden)))) { fn(); return; }\n")
rep("document.querySelector('.view[data-view=\"semana\"] > .subview[data-sub=\"transferencias\"]')",
    "document.querySelector('[data-part=\"semana/transferencias\"] > .subview')", 2)
rep("  const prevVisible = () => { const v = document.querySelector('.view[data-view=\"competicao\"]'), sv = v && v.querySelector(':scope > .subview[data-sub=\"previsao\"]'); return !!(v && !v.hidden && sv && !sv.hidden); };",
    "  const prevVisible = () => v64PartVisible('competicao/previsao') === true;   // V64: a previsão é uma parte da Classificação")
rep("document.querySelector(`.view[data-view=\"semana\"] > .subview[data-sub=\"${sub}\"]`)",
    "document.querySelector(`[data-part=\"semana/${sub}\"] > .subview`)")

# ---------- 4. modo simples, atalhos guardados, ⚙ e rodapé ----------
rep("  const SIMPLE_KEEP = {semana: ['resumo', 'noticias', 'onze', 'capitao', 'transferencias', 'registo'], competicao: ['classificacao', 'vigiar'], mercado: ['pesquisa', 'lesoes']};",
    "  const SIMPLE_KEEP = {semana: ['resumo', 'onze', 'transferencias', 'noticias'], competicao: ['classificacao', 'liga'], mercado: ['pesquisa']};   // V64")
rep("  const favList = () => lsGet(favK()) || [];\n  const recList = () => lsGet(recK()) || [];",
    "  // V64: os atalhos guardados com separadores antigos passam para o separador novo\n"
    "  const v64Toks = L => (L || []).map(v64Tok).filter((t, i, a) => a.indexOf(t) === i);\n"
    "  const favList = () => v64Toks(lsGet(favK()));\n  const recList = () => v64Toks(lsGet(recK()));")
rep("  const inSimple = (v, sub) => !!(SIMPLE_KEEP[v] && (!sub || SIMPLE_KEEP[v].includes(sub)));",
    "  const inSimple = (v, sub) => { if (sub) [v, sub] = v64Key(v, sub).split('/'); return !!(SIMPLE_KEEP[v] && (!sub || SIMPLE_KEEP[v].includes(sub))); };")
rep('      <div class="set-row"><button type="button" class="btn ghost" id="set-tour">Ver o tutorial</button></div>',
    '      <div class="set-row"><button type="button" class="btn ghost" id="set-tour">Ver o tutorial</button> <button type="button" class="btn ghost" id="set-rules">Regras e fontes</button></div>')
rep("    pop.querySelector('#set-tour').addEventListener('click', () => { closeSettings(); startTour(true); });",
    "    pop.querySelector('#set-tour').addEventListener('click', () => { closeSettings(); startTour(true); });\n"
    "    pop.querySelector('#set-rules').addEventListener('click', () => { closeSettings(); showView('avancado', 'regras'); });")
rep('data-goto="avancado">Avançado (simulador, tabelas, regras)</button>', 'data-goto="avancado">Regras e fontes</button>')

# ---------- 5. tutorial ----------
s, k = re.subn(r"\n      \{id: 'dgwjogos', ix: 'jogos/jornada'[^\n]*", '', s)
assert k == 1
rep("      {id: 'avanc', since: 'V47', noSimple: true, sel: '.nav-item.adv, .page-foot .adv-link', t: 'Avançado', d: () => 'O que se usa pouco: simulador, hot takes, picks em falta, capitães da liga, tabelas das equipas, regras e calibração.'},",
    "      {id: 'avanc', since: 'V47', noSimple: true, sel: '.nav-item.adv, .page-foot .adv-link', t: 'Regras e fontes', d: () => 'Como funcionam os pontos, de onde vem cada número e o histórico de versões da app. Estão aqui no rodapé e no ⚙ Definições.'},")
m = re.search(r"\n      \{id: 'menu', ix: 'semana/resumo'[^\n]*", s)
assert m
s = s[:m.end()] + ("\n      {id: 'arruma64', ix: 'semana/resumo', since: 'V64', sel: '.mnav, .nav', t: 'Menos separadores', d: () => 'A app foi arrumada: 5 áreas e 17 separadores. O que fazia quase o mesmo ficou junto — a Equipa ideal, a Equipa simulada e o Simulador estão dentro do Laboratório; Em forma, Preços, Lesões e Onde a app discorda estão na Pesquisa; o H2H e o Comparar equipas estão no Adversário. Nos separadores com várias partes, a linha «Nesta página» leva-te a cada uma, e as partes fechadas abrem-se ao tocar. As regras e fontes estão no ⚙.'},") + s[m.end():]

rep("  var APP_VERSION = 'V63';", "  var APP_VERSION = 'V64';")
H.write_text(s, encoding='utf-8', newline='\n')
print('V64 aplicado')
