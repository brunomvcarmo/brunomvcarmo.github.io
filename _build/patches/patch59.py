"""V59 (9 nov 2026): onde a app discorda da FPL e dos sites — e quem tem razão.
- Dados: DISAGREE no bloco de dados (gerado por _build/pool/discorda.py, chamado pelo gen25.py): consenso (mediana de
  FPL ep_next + FPL Form + FPL Copilot + Onside Arena + FF Pundit), pontos da app completa e da parte só nossa, o porquê
  de cada discordância e a taxa de acerto nas jornadas passadas (_build/research/discorda.json).
- Jogadores › Onde a app discorda (cartões de jogador, próxima jornada ou próximas 5, "gosta mais"/"gosta menos",
  super diferenciais, quem tem razão), linha "App 6,1 · consenso 4,8" na ficha e cartão no Resumo.
Uso (a partir da raiz): py -X utf8 _build/patches/patch59.py   (Linux: python3)"""
from pathlib import Path

H = Path(__file__).resolve().parents[2] / 'index.html'
s = H.read_text(encoding='utf-8')


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)


UI = r'''
  // ===================================================================
  // V59 (9 nov 2026): onde a app discorda da FPL e dos sites (DISAGREE, de _build/pool/discorda.py).
  // Consenso = mediana das fontes de fora. "Só a app" = a parte do modelo que é só nossa (sem os 40% dos sites).
  // ===================================================================
  var DIS59 = {ok: typeof DISAGREE !== 'undefined' && DISAGREE && DISAGREE.p, span: 'one', who: 'all', vs: 'own', more: false};
  const d59 = v => (Math.round(v * 10) / 10).toFixed(1).replace('.', ',');
  const d59pct = (w, n) => n ? Math.round(100 * w / n) + '%' : '—';
  // primeira jornada do horizonte ainda por jogar (depois do deadline da próxima, passa para a seguinte)
  function dis59Start() {
    try { return GW_META.deadline && Date.now() > Date.parse(GW_META.deadline) && HZ.length > 1 ? 1 : 0; } catch (e) { return 0; }
  }
  // valores de um jogador numa jornada (índice do horizonte): app (já com lesões/castigos de hoje), só a app, consenso
  function dis59At(p, i) {
    if (!DIS59.ok || !p) return null;
    const r = DISAGREE.p[p.id]; if (!r || r.c[i] == null) return null;
    const app = epAt(p, i), a0 = r.a[i];
    const own = a0 > 0 ? r.o[i] * Math.min(1.5, app / a0) : r.o[i];
    const off = (DISAGREE.off || [])[i] || 0;
    return {app, own, cons: r.c[i], off, x: r.x[i] || [], w: r.w[i] ? {k: r.w[i][0], t: DISAGREE.t[r.w[i][1]]} : null, g: HZ[i]};
  }
  // discordância numa jornada (só se o gerador a marcou e continuar no mesmo sentido com os valores de hoje)
  function dis59One(p, i, vs) {
    const v = dis59At(p, i); if (!v || !v.w) return null;
    const mine = vs === 'app' ? v.app : v.own, gap = mine - (v.cons + v.off), raw = mine - v.cons;
    if (Math.abs(gap) < 0.8 || gap * raw <= 0) return null;
    return {p, gap, mine, app: v.app, own: v.own, cons: v.cons, off: v.off, x: v.x, k: v.w.k, why: v.w.t, gws: [v.g], g: v.g};
  }
  // próximas 5 (ou as que faltam): soma das jornadas com consenso; o porquê é o da jornada em que a diferença é maior
  function dis59Sum(p, s0, vs) {
    const ks = HZ.map((_, k) => k).filter(k => k >= s0);
    const V = ks.map(k => [k, dis59At(p, k)]).filter(x => x[1]);
    if (V.length < Math.max(2, ks.length - 1)) return null;
    let app = 0, own = 0, cons = 0, off = 0;
    V.forEach(([, v]) => { app += v.app; own += v.own; cons += v.cons; off += v.off; });
    const mine = vs === 'app' ? app : own, gap = mine - (cons + off), raw = mine - cons;
    if (Math.abs(gap) < 3 || Math.abs(gap) < 0.15 * Math.max(mine, cons) || gap * raw <= 0 || Math.max(mine, cons) < 10) return null;
    const best = V.filter(([, v]) => v.w && ((vs === 'app' ? v.app : v.own) - v.cons - v.off) * gap > 0)
      .sort((a, b) => Math.abs((vs === 'app' ? b[1].app : b[1].own) - b[1].cons) - Math.abs((vs === 'app' ? a[1].app : a[1].own) - a[1].cons))[0];
    return {p, gap, mine, app, own, cons, off, x: null, k: best ? best[1].w.k : 'epoca',
      why: best ? `sobretudo na J${best[1].g}: ${best[1].w.t}` : 'a diferença é pequena em cada jornada, mas soma-se ao longo das jornadas',
      gws: V.map(([, v]) => v.g), g: null};
  }
  function dis59Rivals(id) {
    const me = String(CMP_ENTRY[curMgr()]), E = Object.keys(LEAGUE_SQUADS).filter(e => e !== me);
    const n = E.filter(e => { const L = LEAGUE_SQUADS[e]; return (L.s || []).includes(id) || (L.b || []).includes(id); }).length;
    return {n, of: E.length};
  }
  function dis59Super(d) {
    if (d.gap <= 0 || pcMine(d.p.id)) return false;
    const r = dis59Rivals(d.p.id);
    return r.n <= 2 && d.app >= (d.g ? 3.5 : 15);
  }
  function dis59List(span, vs) {
    const s0 = dis59Start(), out = [];
    FULL_POOL.forEach(p => {
      const d = span === 'one' ? dis59One(p, s0, vs) : dis59Sum(p, s0, vs);
      if (d) out.push(d);
    });
    return out;
  }
  function dis59SrcTxt(x) {
    return (DISAGREE.src || []).map(([k, lbl], j) => x[j] != null ? `${lbl} ${d59(x[j])}` : '').filter(Boolean).join(' · ');
  }
  function dis59Note(d) {
    const eo = pcEO(d.p.id), riv = dis59Rivals(d.p.id), mine = pcMine(d.p.id);
    const where = d.g ? `J${d.g}` : `J${d.gws[0]}-J${d.gws[d.gws.length - 1]}`;
    const nums = `<b>App ${d59(d.app)}</b> (só a parte da app ${d59(d.own)}) · <b>consenso ${d59(d.cons)}</b>${d.x ? ` <span class="dis59-src">(${dis59SrcTxt(d.x)})</span>` : ''} · ${where}`;
    const why = `<div class="dis59-why"><b>${d.gap > 0 ? 'A app dá mais' : 'A app dá menos'} porque</b> ${d.why}.</div>`;
    const liga = `<div class="dis59-liga">${mine ? '<b>No teu plantel</b> · ' : ''}Na liga: ${riv.n} de ${riv.of} rivais${eo ? ` · EO ${Math.round(eo.eo * 100)}%` : ''}</div>`;
    return `${nums}${why}${liga}`;
  }
  function dis59Tags(d) {
    return (dis59Super(d) ? '<span class="pc-tag dis59-super" title="A app gosta muito mais do que o consenso e quase nenhum rival o tem">super diferencial</span>' : '')
      + `<span class="pc-tag dis59-k" title="Tipo de razão">${(DISAGREE.types || {})[d.k] || d.k}</span>`;
  }
  // ficha do jogador: "App 6,1 · consenso 4,8"
  function dis59Ficha(p) {
    if (!DIS59.ok) return '';
    const i = dis59Start(), v = dis59At(p, i); if (!v) return '';
    const d = dis59One(p, i, 'own');
    return `<div class="dis59-ficha"><b>J${v.g}: App ${d59(v.app)} · consenso ${d59(v.cons)}</b> <span class="note">(só a parte da app: ${d59(v.own)} · ${dis59SrcTxt(v.x)})</span>${d ? `<div class="dis59-why"><b>${d.gap > 0 ? 'A app dá mais' : 'A app dá menos'} porque</b> ${d.why}.</div>` : ''}</div>`;
  }
  // quem tem razão: taxa de acerto nas discordâncias das jornadas passadas
  function dis59Hist() {
    const H = DISAGREE.hist; if (!H || !H.all || !H.all[0]) return '<p class="note">Ainda não há jornadas medidas. A primeira medição aparece depois da próxima jornada.</p>';
    const bar = (lbl, v, hint) => { const [n, w] = v, pc = n ? w / n : 0; return `<div class="dis59-bar"><span class="l">${lbl}</span><span class="b" aria-hidden="true"><i style="width:${Math.round(pc * 100)}%" class="${pc >= 0.6 ? 'hi' : pc <= 0.4 ? 'lo' : 'mid'}"></i></span><span class="v">${d59pct(w, n)} <span class="note">(${String(w).replace('.', ',')} de ${n})</span>${hint ? ` <span class="note">${hint}</span>` : ''}</span></div>`; };
    const POS = {gk: 'Guarda-redes', def: 'Defesas', mid: 'Médios', fwd: 'Avançados'};
    const T = H.types || {};
    const typ = Object.entries(H.type || {}).sort((a, b) => b[1][0] - a[1][0]);
    const good = typ.filter(([, v]) => v[0] >= 5 && v[1] / v[0] >= 0.6).map(([k]) => T[k] || k);
    const bad = typ.filter(([, v]) => v[0] >= 5 && v[1] / v[0] <= 0.4).map(([k]) => T[k] || k);
    const dir = H.dir || {};
    const ex = (H.ex || []).slice(0, 8).map(e => `<li>J${e.gw} · <span class="player-name" data-pid="${e.id}">${shortName(e.nm)}</span>: app ${d59(e.own)}, consenso ${d59(e.cons)}, fez <b>${e.real}</b> → ${e.win === 1 ? '<span class="up">a app tinha razão</span>' : e.win === 0 ? '<span class="down">o consenso tinha razão</span>' : 'empate'} <span class="note">(${T[e.kind] || e.kind})</span></li>`).join('');
    return `<p class="prose">Em cada jornada guardam-se as discordâncias de antes do deadline; depois da jornada vê-se se os pontos reais ficaram mais perto da app ou do consenso. Amostra ainda pequena: lê como tendência, não como certeza.</p>
      ${bar('<b>No geral</b> (só a parte da app)', H.all)}
      ${bar('App completa (com os sites)', H.full)}
      <h3>Por sentido</h3>${dir.mais ? bar('A app gosta mais', dir.mais) : ''}${dir.menos ? bar('A app gosta menos', dir.menos) : ''}
      <h3>Por posição</h3>${['gk', 'def', 'mid', 'fwd'].filter(k => (H.pos || {})[k]).map(k => bar(POS[k], H.pos[k])).join('')}
      <h3>Por tipo de razão</h3>${typ.map(([k, v]) => bar(T[k] || k, v)).join('')}
      ${good.length || bad.length ? `<p class="dis59-read">${good.length ? `<b>Confia mais</b> quando a razão é: ${good.join(', ')}. ` : ''}${bad.length ? `<b>Desconfia</b> quando a razão é: ${bad.join(', ')}.` : ''} <span class="note">(só tipos com 5 ou mais casos)</span></p>` : ''}
      <h3>Jornada a jornada</h3><ul class="dis59-gws">${(H.gws || []).map(G => `<li>J${G.gw}: app ${d59pct(G.w, G.n)} (${String(G.w).replace('.', ',')} de ${G.n}) · erro médio app ${d59(G.eo)} vs consenso ${d59(G.ec)}${G.final ? '' : ' · provisório'} <span class="note">${/reconstru/.test(G.src) ? '(reconstruído das versões antigas da app)' : ''}</span></li>`).join('')}</ul>
      <details class="dis59-ex"><summary>As maiores discordâncias e o que aconteceu</summary><ul>${ex}</ul></details>`;
  }
  function renderDis59() {
    const el = document.getElementById('dis59-list'); if (!el) return;
    if (!DIS59.ok) { el.innerHTML = '<p class="note">Sem dados do consenso nesta versão.</p>'; return; }
    const s0 = dis59Start(), L0 = dis59List(DIS59.span, DIS59.vs);
    const okWho = d => DIS59.who === 'mine' ? pcMine(d.p.id) : DIS59.who === 'super' ? dis59Super(d) : true;
    const L = L0.filter(okWho);
    const more = L.filter(d => d.gap > 0).sort((a, b) => b.gap - a.gap), less = L.filter(d => d.gap < 0).sort((a, b) => a.gap - b.gap);
    const lim = DIS59.more ? 60 : 12, gi = s0;
    const lbl = DIS59.span === 'one' ? `J${HZ[s0]}` : `J${HZ[s0]}-J${HZ[HZ.length - 1]}`;
    const card = d => ({gi, note: dis59Note(d), tags: dis59Tags(d)});
    const sec = (title, sub, list) => `<section class="card"><div class="card-head"><div><h2>${title} <span class="note">(${list.length})</span></h2><div class="card-sub">${sub}</div></div></div>${list.length ? playerCards(list.slice(0, lim).map(d => d.p), (p, i) => card(list[i])) : '<p class="note">Ninguém nesta lista.</p>'}</section>`;
    const offs = (DISAGREE.off || []).map((o, k) => [HZ[k], o]).filter(([, o]) => o && Math.abs(o) >= 0.25);
    const head = document.getElementById('dis59-head');
    if (head) head.innerHTML = `Consenso de ${lbl} = mediana de ${(DISAGREE.src || []).map(x => x[1]).join(', ')} (só conta com 2 ou mais fontes; a FPL só publica a próxima jornada).`
      + `${offs.length ? ` ${offs.length > 1 ? `Nas J${offs[0][0]}-J${offs[offs.length - 1][0]}` : `Na J${offs[0][0]}`} os sites dão em média ${d59(Math.abs(offs[0][1]))} pontos ${offs[0][1] < 0 ? 'a mais' : 'a menos'} por jogador do que a app: essa diferença geral é descontada, para ficarem só as diferenças de jogador para jogador.` : ''}`
      + `${s0 ? ` O deadline da J${HZ[0]} já passou: a lista começa na J${HZ[s0]} (os dados da J${HZ[s0]} melhoram com a atualização semanal).` : ''}`;
    el.innerHTML = sec('A app gosta mais', `A app dá muito mais do que o consenso (${lbl}). Os <b>super diferenciais</b> são estes com 2 ou menos rivais a tê-los.`, more)
      + sec('A app gosta menos', `A app dá muito menos do que o consenso (${lbl}): cuidado antes de comprar, ou razões para vender.`, less)
      + ((more.length > lim || less.length > lim) && !DIS59.more ? '<div style="text-align:center"><button type="button" class="btn" id="dis59-more">Mostrar mais</button></div>' : '');
    const m = document.getElementById('dis59-more'); if (m) m.addEventListener('click', () => { DIS59.more = true; renderDis59(); });
    const h = document.getElementById('dis59-hist'); if (h) h.innerHTML = dis59Hist();
  }
  // Resumo: os 2-3 super diferenciais da semana
  function renderDis59Resumo() {
    const el = document.getElementById('dis59-resumo'); if (!el) return;
    if (!DIS59.ok) { el.hidden = true; return; }
    const s0 = dis59Start(), L = dis59List('one', 'own').filter(dis59Super).sort((a, b) => b.gap - a.gap).slice(0, 3);
    if (!L.length) { el.hidden = true; return; }
    el.hidden = false;
    const H = DISAGREE.hist || {}, A = H.all || [0, 0], mais = (H.dir || {}).mais;
    el.innerHTML = `<div class="card-head"><div><h2>Super diferenciais da J${HZ[s0]}</h2><div class="card-sub">A app gosta muito mais do que a FPL e os sites, e quase nenhum rival os tem</div></div></div>
      ${playerCards(L.map(d => d.p), (p, i) => ({gi: s0, note: dis59Note(L[i]), tags: dis59Tags(L[i])}))}
      <p class="note">${A[0] ? `Até agora, nas discordâncias medidas, a parte só da app ficou mais perto dos pontos reais em ${d59pct(A[1], A[0])} dos casos${mais && mais[0] ? ` (quando a app gosta mais: ${d59pct(mais[1], mais[0])})` : ''}. ` : ''}<button type="button" class="linklike" data-dis59go>Ver onde a app discorda</button></p>`;
    const b = el.querySelector('[data-dis59go]'); if (b) b.addEventListener('click', () => showView('mercado', 'discorda'));
  }
  function dis59Refresh() {
    try { renderDis59Resumo(); } catch (e) { console.error(e); }
    try { lazyRender('mercado/discorda', renderDis59); } catch (e) { console.error(e); }
  }
  (function dis59Init() {
    document.querySelectorAll('#dis59-span .seg-btn, #dis59-who .seg-btn, #dis59-vs .seg-btn').forEach(b => b.addEventListener('click', () => {
      const g = b.parentElement; g.querySelectorAll('.seg-btn').forEach(x => x.setAttribute('aria-pressed', x === b ? 'true' : 'false'));
      if (g.id === 'dis59-span') DIS59.span = b.dataset.s; else if (g.id === 'dis59-who') DIS59.who = b.dataset.w; else DIS59.vs = b.dataset.v;
      DIS59.more = false; renderDis59();
    }));
    const s0 = dis59Start(), one = document.querySelector('#dis59-span [data-s="one"]'), five = document.querySelector('#dis59-span [data-s="five"]');
    if (one) one.textContent = `Próxima (J${HZ[s0]})`;
    if (five) five.textContent = `Próximas ${HZ.length - s0} (J${HZ[s0]}-J${HZ[HZ.length - 1]})`;
    dis59Refresh();
  })();
'''
rep("  var PC_READY = true;", UI + "  var PC_READY = true;")

# ---------------------------------------------------------------- ficha, Resumo, troca de gestor
rep("      ${(() => { try { return av58Ficha(p, !!mine); } catch (e) { console.error(e); return ''; } })()}\n",
    "      ${(() => { try { return av58Ficha(p, !!mine); } catch (e) { console.error(e); return ''; } })()}\n"
    "      ${(() => { try { return dis59Ficha(p); } catch (e) { console.error(e); return ''; } })()}\n")
rep('      <section class="card" id="alerts" style="margin-bottom:16px"></section>\n',
    '      <section class="card" id="alerts" style="margin-bottom:16px"></section>\n'
    '      <section class="card dis59-card" id="dis59-resumo" style="margin-bottom:16px" hidden></section>\n')
rep("    try { av58Refresh(); } catch (e) {}\n", "    try { av58Refresh(); } catch (e) {}\n    try { dis59Refresh(); } catch (e) {}\n")
rep("    try { av58Refresh(); } catch (e) { console.error(e); }\n  }\n",
    "    try { av58Refresh(); } catch (e) { console.error(e); }\n    try { dis59Refresh(); } catch (e) { console.error(e); }\n  }\n")

# ---------------------------------------------------------------- separador novo em Jogadores
rep('        <button class="subtab" type="button" data-sub="lesoes">Lesões e castigos</button>\n',
    '        <button class="subtab" type="button" data-sub="lesoes">Lesões e castigos</button>\n'
    '        <button class="subtab" type="button" data-sub="discorda">Onde a app discorda</button>\n')
rep('      <div class="subview" data-sub="lesoes" hidden>\n',
    '''      <div class="subview" data-sub="discorda" hidden>
        <section class="card">
          <h2>Onde a app discorda</h2>
          <div class="card-sub">Onde os pontos esperados da app ficam longe dos da FPL e dos sites — é aí que pode estar a vantagem. Com o porquê de cada um, a posse na liga e se acertámos no passado.</div>
          <div class="dis59-filters">
            <div class="seg" role="group" aria-label="Jornadas" id="dis59-span"><button type="button" class="seg-btn" data-s="one" aria-pressed="true">Próxima</button><button type="button" class="seg-btn" data-s="five" aria-pressed="false">Próximas 5</button></div>
            <div class="seg" role="group" aria-label="Quem" id="dis59-who"><button type="button" class="seg-btn" data-w="all" aria-pressed="true">Todos</button><button type="button" class="seg-btn" data-w="mine" aria-pressed="false">Só o meu plantel</button><button type="button" class="seg-btn" data-w="super" aria-pressed="false">Super diferenciais</button></div>
            <div class="seg" role="group" aria-label="Comparar o consenso com" id="dis59-vs"><button type="button" class="seg-btn" data-v="own" aria-pressed="true">Só a parte da app</button><button type="button" class="seg-btn" data-v="app" aria-pressed="false">App completa</button></div>
          </div>
          <p class="note" id="dis59-head"></p>
          <p class="note">"Só a parte da app" = forma recente, modelo da época (xG, assistências esperadas, balizas a zero, odds), leitura própria, descanso e disponibilidade — sem os 40% que a app já vai buscar aos sites. É a comparação que mostra a discordância verdadeira; "App completa" é o número que vês no resto da app.</p>
        </section>
        <div class="stack" id="dis59-list"></div>
        <section class="card"><h2>Quem tem razão?</h2><div class="card-sub">Nas jornadas passadas, quando a app e o consenso discordaram, quem ficou mais perto dos pontos reais (API oficial)</div><div id="dis59-hist"></div></section>
      </div>
      <div class="subview" data-sub="lesoes" hidden>
''')
rep('"Em forma", "Preços e alternativas", "Lesões e castigos"]}', '"Em forma", "Preços e alternativas", "Lesões e castigos", "Onde a app discorda"]}')
rep('"suspensão", "suspensos", "disponibilidade"]}',
    '"suspensão", "suspensos", "disponibilidade"]}, {"v": "mercado", "s": "discorda", "a": "Jogadores", "n": "Onde a app discorda", '
    '"syn": ["discorda", "discordância", "discordâncias", "consenso", "subestimado", "subestimados", "sobrestimado", "sobrestimados", "diferencial", "diferenciais", "super diferencial", "app vs sites", "app vs fpl", "quem tem razão", "vantagem"]}')

# ---------------------------------------------------------------- tutorial e versão
rep("  var APP_VERSION = 'V58';", "  var APP_VERSION = 'V59';")
rep("      {id: 'precos', ix: 'mercado/precos', since: 'V24',",
    "      {id: 'discorda59', ix: 'mercado/discorda', since: 'V59', sel: '#dis59-list, #dis59-span', t: 'Onde a app discorda', d: () => `Os jogadores em que a app dá muito mais (ou muito menos) do que a FPL e os sites — é aí que pode estar a vantagem. Cada cartão diz o porquê (ex.: ${tutSafe(() => { const d = dis59List('one', 'own').sort((a, b) => b.gap - a.gap)[0]; return shortName(d.p.name) + ': app ' + d59(d.app) + ' · consenso ' + d59(d.cons); }, 'app 6,1 · consenso 4,8')}), quantos rivais o têm e, no fim, \"Quem tem razão?\": a taxa de acerto da app nas discordâncias passadas, por posição e por tipo de razão.`},\n"
    "      {id: 'precos', ix: 'mercado/precos', since: 'V24',")
rep("      {id: 'dados57', ix: 'semana/registo', since: 'V57',",
    "      {id: 'superdif59', ix: 'semana/resumo', since: 'V59', opt: true, sel: '#dis59-resumo', t: 'Super diferenciais', d: () => 'Os 2 ou 3 jogadores de que a app gosta muito mais do que a FPL e os sites e que quase nenhum rival tem. \"Comparar\" e \"Pôr no plano\" levam-te logo ao comparador e ao planeador. Na ficha de cada jogador há a mesma comparação: \"App 6,1 · consenso 4,8\".'},\n"
    "      {id: 'dados57', ix: 'semana/registo', since: 'V57',")

# ---------------------------------------------------------------- estilos (claro e escuro pelos tokens)
rep("  .pc-tag.ret { background: var(--good-weak); color: var(--good); }\n",
    "  .pc-tag.ret { background: var(--good-weak); color: var(--good); }\n"
    "  .pc-tag.dis59-super { background: var(--good); color: var(--surface, #fff); }\n"
    "  .pc-tag.dis59-k { background: var(--surface-2); color: var(--muted, inherit); font-weight: 500; }\n"
    "  .dis59-filters { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 6px; }\n"
    "  .dis59-src { color: var(--muted, inherit); font-size: 12px; }\n"
    "  .dis59-why { margin-top: 3px; }\n"
    "  .dis59-liga { margin-top: 3px; font-size: 12px; color: var(--muted, inherit); }\n"
    "  .dis59-ficha { margin: 8px 0 4px; padding: 6px 8px; border-radius: 6px; background: var(--surface-2); font-size: 13px; }\n"
    "  .dis59-bar { display: grid; grid-template-columns: minmax(110px, 190px) minmax(60px, 1fr) auto; gap: 8px; align-items: center; margin: 4px 0; font-size: 13px; }\n"
    "  .dis59-bar .b { height: 8px; border-radius: 4px; background: var(--surface-2); overflow: hidden; }\n"
    "  .dis59-bar .b i { display: block; height: 100%; border-radius: 4px; }\n"
    "  .dis59-bar .b i.hi { background: var(--good); }\n"
    "  .dis59-bar .b i.mid { background: var(--warn); }\n"
    "  .dis59-bar .b i.lo { background: var(--bad); }\n"
    "  @media (max-width: 560px) { .dis59-bar { grid-template-columns: 1fr auto; } .dis59-bar .b { grid-column: 1 / -1; grid-row: 2; } }\n"
    "  .dis59-gws, .dis59-ex ul { margin: 4px 0; padding-left: 18px; font-size: 13px; }\n"
    "  .dis59-read { margin: 8px 0; padding: 6px 8px; border-radius: 6px; background: var(--surface-2); font-size: 13px; }\n")

H.write_text(s, encoding='utf-8', newline='\n')
print('V59 aplicada ao index.html')
