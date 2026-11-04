"""Gera _build/redesign/cartao-teste.html: a app (index.html) com o cartão de jogador (pcard.css + pcard.js)
e uma área extra "Cartão (teste)" com exemplos reais. Não mexe no index.html.
Uso (a partir da raiz do repositório):  py _build/patches/make_cartao_teste.py  (Linux: python3)"""
from pathlib import Path
R = Path(__file__).resolve().parent
ROOT = R.parents[1]
s = (ROOT / 'index.html').read_text(encoding='utf-8')
css = (R / 'pcard.css').read_text(encoding='utf-8')
js = (R / 'pcard.js').read_text(encoding='utf-8')

def put(s, anchor, text, before=True):
    assert s.count(anchor) >= 1, anchor
    i = s.index(anchor)
    return s[:i] + text + s[i:] if before else s[:i + len(anchor)] + text + s[i + len(anchor):]

s = put(s, '</style>', css)
s = put(s, '        <button class="nav-item" data-view="aovivo"',
        '        <button class="nav-item" data-view="pcteste" type="button">Cartão (teste)</button>\n')
s = put(s, '    <!-- ========== REGRAS E FONTES ========== -->', '''    <!-- ========== CARTÃO DE JOGADOR (teste) ========== -->
    <section class="view" data-view="pcteste" data-title="Cartão (teste)" hidden>
      <div class="view-head">
        <div class="eyebrow">Página de teste · não publicada</div>
        <h1>Cartão de jogador</h1>
        <p>Um só componente, em versão compacta (para as listas) e completa. Toca num cartão compacto para abrir a ficha. Experimenta o modo escuro (botão ☾) e o seletor Bruno/Marco.</p>
      </div>
      <div class="stack">
        <section class="card"><div class="card-head"><div><h2>Compacto · o teu plantel</h2><div class="card-sub">Melhor onze da J<span class="gw-n">7</span> com capitão e vice, depois o banco.</div></div></div><div id="pct-squad"></div></section>
        <section class="card"><div class="card-head"><div><h2>Compacto · estados</h2><div class="card-sub">Lesionado, dúvida, preço a subir e a descer, diferencial na liga, e uma troca sugerida com coluna extra.</div></div></div><div id="pct-states"></div></section>
        <section class="card"><div class="card-head"><div><h2>Compacto · em colunas estreitas</h2><div class="card-sub">Como fica em espaços apertados (ex.: Vigiar rivais, duas colunas).</div></div></div><div id="pct-narrow"></div></section>
        <section class="card"><div class="card-head"><div><h2>Versão completa</h2><div class="card-sub">Para destaques (capitão, compra sugerida) e para a ficha.</div></div></div><div id="pct-full"></div></section>
      </div>
    </section>

''')
demo = '''
  // ---------- página de teste do cartão ----------
  function renderPcTest() {
    if (!document.getElementById('pct-squad')) return;
    const mgr = curMgr(), sq = squadOf(mgr).filter(Boolean), X = pickXi(sq, 0);
    const inXi = new Set(X.xi.map(p => p.id));
    const order = [...X.xi.slice().sort((a, b) => POS_ORDER[a.cls] - POS_ORDER[b.cls]), ...X.benchGk, ...X.benchOut];
    document.getElementById('pct-squad').innerHTML = playerCards(order, p => ({cap: p.id === X.cap.id, vice: p.id === X.vice.id, mine: false, note: inXi.has(p.id) ? '' : 'banco'}));
    const mine = new Set(sq.map(p => p.id)), by = (f, k) => FULL_POOL.filter(f).sort(k)[0];
    const ep = p => epAt(p, 0);
    const inj = by(p => p.status === 'i' && p.price >= 6, (a, b) => b.price - a.price);
    const dbt = by(p => p.status === 'd', (a, b) => ep(b) - ep(a));
    const up = by(p => pricePressure(p).lvl >= 1, (a, b) => ep(b) - ep(a));
    const down = by(p => pricePressure(p).lvl <= -1, (a, b) => (b.own || 0) - (a.own || 0));
    const dif = by(p => !mine.has(p.id) && (pcEO(p.id) || {eo: 1}).eo < 0.15, (a, b) => ep(b) - ep(a));
    const mv = (SUGGESTED_MOVES[mgr].transfers || [])[0];
    const list = [[inj, {}], [dbt, {}], [up, {}], [down, {}], [dif, {}]];
    if (mv) {
      const pin = FULL_POOL_BY_ID[mv.in], pout = FULL_POOL_BY_ID[mv.out];
      const g = ep(pin) - ep(pout), g5 = HZ.reduce((s, _, k) => s + epAt(pin, k) - epAt(pout, k), 0);
      list.push([pin, {note: `troca sugerida: entra para o lugar de ${shortName(pout.name)}`, extra: `<b class="up">${sgn(g)}</b> J${HZ[0]}<br><span class="note">${sgn(g5)} em ${HZ.length}</span>`}]);
    }
    document.getElementById('pct-states').innerHTML = playerCards(list.map(x => x[0]), (p, i) => list.filter(x => x[0])[i][1]);
    document.getElementById('pct-narrow').innerHTML = `<div class="riv-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px">${[X.xi.slice(0, 3), [X.cap, dif, up]].map(L => `<div>${playerCards(L, p => ({cap: p.id === X.cap.id}))}</div>`).join('')}</div>`;
    document.getElementById('pct-full').innerHTML = `<div class="pc-list cols-2">${[[X.cap, {cap: true, note: 'o capitão sugerido para a J' + HZ[0]}], [dif, {note: 'diferencial: quase ninguém na liga o tem'}], [inj, {}]].filter(x => x[0]).map(([p, o]) => playerCard(p, Object.assign({full: true}, o))).join('')}</div>`;
  }
  renderPcTest();
  document.querySelectorAll('.mswitch-btn').forEach(b => b.addEventListener('click', () => setTimeout(renderPcTest, 0)));
'''
s = put(s, '  // ===== Navegação: menu lateral', js + demo + '\n')
out = ROOT / '_build' / 'redesign' / 'cartao-teste.html'; out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(s, encoding='utf-8', newline='\n')
print('escrito', out)
