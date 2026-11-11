"""V60 (11 nov 2026): ficha do jogador corrigida e app com melhor aspeto (mesmo estilo, mais cuidada).
- Bug: "Pontos por jornada" na ficha do jogador estava feito para 6 jornadas; com 10 as barras passavam para uma
  2.ª linha e ficavam por cima do texto. Agora é uma só fila que desliza (mostra as últimas) com os minutos por baixo.
- Telemóvel: cabeçalho numa só linha e menu das 5 áreas fixo em baixo (o conteúdo começa logo no topo do ecrã).
- Ícones desenhados (definições, procurar, avisos, áreas) em vez de emojis.
- "Os teus atalhos" vazio passa a uma linha; os separadores mostram que há mais para o lado.
- Textos parados: data do rodapé da barra lateral e "(provisória)" do rodapé.
Uso (a partir da raiz): py -X utf8 _build/patches/patch60.py   (Linux: python3)"""
from pathlib import Path
from urllib.parse import quote

H = Path(__file__).resolve().parents[2] / 'index.html'
s = H.read_text(encoding='utf-8')


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)


def ic(body):
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' "
           "stroke-linecap='round' stroke-linejoin='round'>" + body + "</svg>")
    return 'url("data:image/svg+xml,' + quote(svg, safe="/:='") + '")'


ICONS = {
    'set': "<path d='M4 7h9M17 7h3M4 17h3M11 17h9'/><circle cx='15' cy='7' r='2'/><circle cx='9' cy='17' r='2'/>",
    'srch': "<circle cx='11' cy='11' r='6.5'/><path d='m20 20-4.2-4.2'/>",
    'bell': "<path d='M6 10a6 6 0 0 1 12 0c0 4.5 1.5 6 2 6.5H4c.5-.5 2-2 2-6.5'/><path d='M10 19.5a2 2 0 0 0 4 0'/>",
    'semana': "<rect x='3.5' y='5' width='17' height='15.5' rx='2.5'/><path d='M8 3v4M16 3v4M3.5 10h17M9 15.2l2 2 4-4'/>",
    'jogos': "<rect x='3' y='5' width='18' height='14' rx='2'/><path d='M12 5v14M3 9.5h2.5v5H3M21 9.5h-2.5v5H21'/><circle cx='12' cy='12' r='2.3'/>",
    'competicao': "<path d='M8 4h8v5a4 4 0 0 1-8 0zM8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8.5 20h7M10 17h4'/>",
    'mercado': "<circle cx='9' cy='8' r='3.2'/><path d='M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6M16 5.2a3.2 3.2 0 0 1 0 5.6M17.5 14.3c2.1.8 3.5 2.9 3.5 5.7'/>",
    'epoca': "<path d='M4 4v16h16'/><path d='m7.5 15 3.5-4 3 2.5L19 8'/>",
    'avancado': "<rect x='4' y='4' width='6.5' height='6.5' rx='1.5'/><rect x='13.5' y='4' width='6.5' height='6.5' rx='1.5'/><rect x='4' y='13.5' width='6.5' height='6.5' rx='1.5'/><rect x='13.5' y='13.5' width='6.5' height='6.5' rx='1.5'/>",
}

CSS = r'''
  /* ===================== V60 (11 nov 2026): acabamentos — mesmo estilo, mais cuidado ===================== */
  :root {
    --radius: 12px;
    --shadow: 0 1px 2px rgba(28, 21, 40, 0.05), 0 10px 24px -14px rgba(28, 21, 40, 0.16);
__ICVARS__
  }
  body { -moz-osx-font-smoothing: grayscale; text-rendering: optimizeLegibility; }
  /* botões e separadores: resposta ao toque e ao rato */
  .btn, .subtab, .nav-item, .mswitch-btn, .theme-btn, .seg-btn, .fav-chip, .mnav-btn { transition: background-color .12s ease, border-color .12s ease, color .12s ease, box-shadow .12s ease; }
  .btn:hover { border-color: var(--accent-mid); }
  .btn:active, .theme-btn:active { transform: translateY(1px); }
  .btn.primary { box-shadow: 0 1px 2px rgba(28, 21, 40, .18); }
  .subtabs { border-radius: 10px; position: relative; }
  .subtabs.more-r { -webkit-mask-image: linear-gradient(90deg, #000 calc(100% - 40px), transparent); mask-image: linear-gradient(90deg, #000 calc(100% - 40px), transparent); }
  .subtabs.more-l { -webkit-mask-image: linear-gradient(270deg, #000 calc(100% - 40px), transparent); mask-image: linear-gradient(270deg, #000 calc(100% - 40px), transparent); }
  .subtabs.more-l.more-r { -webkit-mask-image: linear-gradient(90deg, transparent, #000 40px, #000 calc(100% - 40px), transparent); mask-image: linear-gradient(90deg, transparent, #000 40px, #000 calc(100% - 40px), transparent); }
  .view-head h1 { letter-spacing: 0; }
  .fav-star { color: var(--muted); font-size: 18px; }
  .fav-star[aria-pressed="true"] { color: var(--warn); }
  .fav-sub { font-size: 12.5px; }
  thead th { font-size: 10.5px; letter-spacing: .07em; }
  .kpi, .card { border-color: color-mix(in srgb, var(--line) 80%, transparent); }
  details.more-week > summary { border-radius: var(--radius); }
  details.more-week > summary:hover { border-color: var(--accent-mid); color: var(--ink); }
  /* ícones desenhados em vez de emojis */
  .set-btn, .bell, .srch-btn { font-size: 0 !important; position: relative; }
  .set-btn, .bell { display: inline-grid; place-items: center; }
  .set-btn::before, .bell::before, .srch-btn::before { content: ""; width: 18px; height: 18px; background: var(--ink-2); -webkit-mask: var(--ic) center / contain no-repeat; mask: var(--ic) center / contain no-repeat; }
  .set-btn { --ic: var(--ic-set); } .bell { --ic: var(--ic-bell); } .srch-btn { --ic: var(--ic-srch); }
  .theme-btn:hover::before { background: var(--accent); }
  /* barra lateral (computador): ícone por área e marca na área aberta */
  .brand-mark { border-radius: 9px; box-shadow: inset 0 0 0 1px rgba(255, 255, 255, .12), 0 2px 6px rgba(65, 32, 95, .25); }
  .nav-item[data-view] { justify-content: flex-start; gap: 10px; }
  .nav-item[data-view]::before { content: ""; flex: none; width: 18px; height: 18px; background: currentColor; opacity: .75; -webkit-mask: var(--ic) center / contain no-repeat; mask: var(--ic) center / contain no-repeat; }
  .nav-item[data-view] > :first-child { margin-left: auto; }
  .nav-item[aria-current="page"] { box-shadow: inset 3px 0 0 var(--accent); }
  .nav-item[aria-current="page"]::before { opacity: 1; }
  .nav-item[data-view="semana"], .mnav-btn[data-v="semana"] { --ic: var(--ic-semana); } .nav-item[data-view="jogos"], .mnav-btn[data-v="jogos"] { --ic: var(--ic-jogos); }
  .nav-item[data-view="competicao"], .mnav-btn[data-v="competicao"] { --ic: var(--ic-competicao); } .nav-item[data-view="mercado"], .mnav-btn[data-v="mercado"] { --ic: var(--ic-mercado); }
  .nav-item[data-view="epoca"], .mnav-btn[data-v="epoca"] { --ic: var(--ic-epoca); } .nav-item[data-view="avancado"] { --ic: var(--ic-avancado); }
  /* "Os teus atalhos" sem atalhos: uma linha só */
  .fav-card.fav-min { padding: 9px 14px; box-shadow: none; background: transparent; border-style: dashed; border-color: var(--line-strong); }
  .fav-card.fav-min .fav-rec { margin-top: 0; }
  .fav-card.fav-min .fav-chips { display: inline; }
  .fav-min-row { display: flex; flex-wrap: wrap; gap: 6px 10px; align-items: center; }
  /* ficha do jogador */
  .pc-sheet { border-radius: 16px; }
  .pc-kpis > div { border: 1px solid var(--line); border-radius: 10px; }
  .pc-close { display: grid; place-items: center; z-index: 2; }
  .pc-close:hover { border-color: var(--accent-mid); color: var(--accent); }
  .pc-fx div { border-radius: 8px; }

  /* ---------- telemóvel e tablet: cabeçalho numa linha e menu fixo em baixo ---------- */
  @media (max-width: 960px) {
    body { padding-bottom: calc(60px + env(safe-area-inset-bottom, 0px)); }
    .sidebar { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 8px 10px; padding: 10px 16px; }
    .brand { grid-area: 1 / 1; padding: 0; }
    .team-card { grid-area: 1 / 2; background: none; border: 0; padding: 0; }
    .team-card > div:not(.manager-switch) { display: none; }
    .mswitch-btn { padding: 8px 6px; overflow: hidden; text-overflow: ellipsis; }
    .mfav { grid-row: 2; grid-column: 1 / -1; padding-bottom: 2px; }
    .tour-again { grid-area: 1 / 3; margin: 0; width: 36px; height: 36px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); font-size: 0; text-decoration: none; display: grid; place-items: center; }
    .tour-again::before { content: "?"; font-family: var(--font-display); font-size: 17px; font-weight: 700; color: var(--ink-2); }
    .mnav { position: fixed; left: 0; right: 0; bottom: 0; z-index: 60; gap: 0 !important; padding: 4px 6px calc(4px + env(safe-area-inset-bottom, 0px));
      background: color-mix(in srgb, var(--surface) 94%, transparent); -webkit-backdrop-filter: blur(10px); backdrop-filter: blur(10px);
      border-top: 1px solid var(--line); box-shadow: 0 -6px 20px -12px rgba(28, 21, 40, .25); }
    .mnav-btn { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; border: 0 !important; background: none !important;
      min-height: 50px; padding: 6px 2px 4px !important; font-size: 11px !important; font-weight: 600; color: var(--muted); white-space: nowrap; border-radius: 10px; }
    .mnav-btn::before { content: ""; width: 22px; height: 22px; background: currentColor; -webkit-mask: var(--ic) center / contain no-repeat; mask: var(--ic) center / contain no-repeat; }
    .mnav-btn.here { color: var(--accent); }
    .mnav-btn.here::after { content: ""; position: absolute; top: -4px; left: 50%; width: 28px; height: 3px; margin-left: -14px; border-radius: 0 0 3px 3px; background: var(--accent); }
    .mnav-btn:active { background: var(--accent-weak) !important; }
    .mnav-btn .al-dot { top: 1px; right: auto; left: calc(50% + 4px); }
    .mnav-btn .av-dot { top: 0; right: auto; left: calc(50% + 6px); background: none; }
    .view { padding-top: 18px; }
    .view-head { margin-bottom: 14px; }
    .page-foot { margin-bottom: 8px; }
  }
  @media (max-width: 520px) {
    .brand-text { display: none; }
    .view-head p { font-size: 13.5px; }
    h1 { font-size: 24px; }
    .status-items { width: 100%; align-items: stretch; }
    .status-item { flex-direction: column; align-items: flex-start; justify-content: center; gap: 0; padding: 4px 10px; min-height: 40px; }
    .status-item.deadline { flex: 1 1 auto; }
    .status-item .k { font-size: 9.5px; white-space: nowrap; line-height: 1.3; }
    .status-item .v, .status-item.deadline #countdown { font-size: 14.5px !important; line-height: 1.2; color: var(--ink); }
    .status-item.deadline #countdown { color: var(--accent-strong) !important; font-weight: 700; }
    .theme-btn { width: 40px; height: 40px; flex: none; }
    .btn { min-height: 36px; }
    .btn.small { min-height: 30px; }
    .subtab { padding: 8px 13px; }
  }
'''.replace('__ICVARS__', '\n'.join(f'    --ic-{k}: {ic(v)};' for k, v in ICONS.items()))

rep('</style>', CSS + '</style>')

# 1. Ficha do jogador: "Pontos por jornada" numa só fila (antes: grelha de 6 colunas, feita quando a época ia na J6)
rep("  .pc-bars { display: grid; grid-template-columns: repeat(6, 1fr); gap: 6px; align-items: end; height: 96px; }\n"
    "  .pc-bar { display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; gap: 2px; font-size: 11px; }\n",
    "  .pc-bars { display: flex; gap: 4px; align-items: flex-end; overflow-x: auto; padding: 2px 0 6px; scrollbar-width: thin; }\n"
    "  .pc-bar { flex: 1 0 28px; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 112px; gap: 2px; font-size: 11px; }\n"
    "  .pc-bar .m { color: var(--muted); font-size: 10px; font-variant-numeric: tabular-nums; line-height: 1.1; }\n"
    "  .pc-bar.neg .v { color: var(--bad); }\n")
rep("""${pts.map((v, i) => `<div class="pc-bar${(mins[i] || 0) === 0 ? ' nomin' : ''}" title="J${i + 1}: ${v} pts, ${mins[i] || 0} min"><span class="v">${v}</span><span class="b" style="height:${Math.max(2, Math.max(0, v) / maxP * 64)}px"></span><span class="g">J${i + 1}</span></div>`).join('')}""",
    """${pts.map((v, i) => `<div class="pc-bar${(mins[i] || 0) === 0 ? ' nomin' : ''}${v < 0 ? ' neg' : ''}" title="J${i + 1}: ${v} pts, ${mins[i] || 0} min"><span class="v">${v}</span><span class="b" style="height:${Math.max(2, Math.max(0, v) / maxP * 60)}px"></span><span class="g">J${i + 1}</span><span class="m">${mins[i] || 0}'</span></div>`).join('')}""")
rep("""<p class="note" style="margin:6px 0 0">Minutos: ${mins.map((m, i) => `J${i + 1} ${m}`).join(' · ')}. Últimas 3 jornadas:""",
    """<p class="note" style="margin:6px 0 0">Por baixo de cada jornada: minutos jogados (barra cinzenta = não jogou)${pts.length > 12 ? '; desliza para ver as primeiras jornadas' : ''}. Últimas 3 jornadas:""")
rep("    bd.querySelector('.pc-sheet').scrollTop = 0;\n",
    "    bd.querySelector('.pc-sheet').scrollTop = 0;\n"
    "    const pb = bd.querySelector('.pc-bars'); if (pb) pb.scrollLeft = pb.scrollWidth;   // V60: as últimas jornadas à vista\n")

# 2. "Os teus atalhos" sem atalhos: uma linha
rep("""    if (card) card.innerHTML = `<div class="card-head"><div><h2>Os teus atalhos</h2>""",
    """    if (card) card.classList.toggle('fav-min', !F.length);
    if (card && !F.length) card.innerHTML = `<div class="fav-min-row"><span class="note fav-chips"><b>Os teus atalhos</b> · toca na ☆ ao lado de um título ou separador para o guardares aqui.</span>${R.length ? `<span class="fav-rec"><span class="note">Recentes:</span> ${R.map(t => chipBtn(t, 'fav-chip ghost')).join('')}</span>` : ''}</div>`;
    else if (card) card.innerHTML = `<div class="card-head"><div><h2>Os teus atalhos</h2>""")

# 3. separadores: sombra do lado onde há mais para ver
rep("    if (st && st.parentElement.scrollWidth > st.parentElement.clientWidth) { const r = st.parentElement; r.scrollLeft = st.offsetLeft - (r.clientWidth - st.clientWidth) / 2; }\n  }\n",
    "    if (st && st.parentElement.scrollWidth > st.parentElement.clientWidth) { const r = st.parentElement; r.scrollLeft = st.offsetLeft - (r.clientWidth - st.clientWidth) / 2; }\n"
    "    try { v60Tabs(); } catch (e) { console.error(e); }\n  }\n"
    "  // V60: os separadores que não cabem no ecrã esbatem-se do lado onde há mais\n"
    "  function v60Fade(t) { t.classList.toggle('more-r', t.scrollLeft + t.clientWidth < t.scrollWidth - 6); t.classList.toggle('more-l', t.scrollLeft > 6); }\n"
    "  function v60Tabs() { document.querySelectorAll('.view:not([hidden]) > .subtabs').forEach(v60Fade); }\n"
    "  document.querySelectorAll('.subtabs').forEach(t => t.addEventListener('scroll', () => v60Fade(t), {passive: true}));\n"
    "  window.addEventListener('resize', () => { try { v60Tabs(); } catch (e) {} });\n")

# 4. textos parados
rep("Dados da API oficial da FPL · atualizado a 13 out 2026.", 'Dados da API oficial da FPL · atualizado a <span class="gw-date">13 out 2026</span>.')
rep('dados até à J<span class="gw-l">6</span> (provisória), recolhidos a', 'dados até à J<span class="gw-l">6</span><span class="gw-prov"> (provisória)</span>, recolhidos a')

# 5. tutorial e versão
# o menu do telemóvel passou a estar fixo em baixo: um elemento "fixed" tem offsetParent null mas está visível
rep("find(x => x.offsetParent !== null && x.getBoundingClientRect().height > 0)",
    "find(x => (x.offsetParent !== null || getComputedStyle(x).position === 'fixed') && x.getBoundingClientRect().height > 0)")
rep("      {id: 'rotina56', ix: 'semana/resumo',",
    "      {id: 'visual60', ix: 'semana/resumo', since: 'V60', opt: true, sel: '.mnav, .nav', t: 'Menu sempre à mão', d: () => 'No telemóvel, as 5 áreas ficam agora numa barra fixa em baixo e o cabeçalho ocupa uma só linha (o «?» abre este tutorial). Na ficha de um jogador, os pontos por jornada estão numa só fila que desliza, com os minutos por baixo.'},\n"
    "      {id: 'rotina56', ix: 'semana/resumo',")
rep("  var APP_VERSION = 'V59';", "  var APP_VERSION = 'V60';")
H.write_text(s, encoding='utf-8', newline='\n')
print('V60 aplicado')
