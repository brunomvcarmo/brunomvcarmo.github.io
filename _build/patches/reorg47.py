"""V47 (16 out 2026): reorganiza a app em 5 áreas + Avançado, um só nível de separadores, com pesquisa.
Move os blocos de conteúdo das áreas antigas para as novas (os ids ficam iguais, por isso o JS continua a
funcionar), reescreve o menu, o showView (com os endereços antigos em VIEW_ALIAS), o lazyRender (por separador),
o menu do telemóvel e o guia, e acrescenta o índice único (APP_INDEX) usado pela pesquisa e pelo guia.
Uso (a partir da raiz do repositório): py _build/patches/reorg47.py"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
H = ROOT / 'index.html'
s = H.read_text(encoding='utf-8')
assert 'APP_INDEX' not in s, 'já reorganizado'


def match_end(text, start, tag):
    """Fim (exclusivo) do elemento <tag ...> que começa em start, contando aninhamentos."""
    depth = 0
    for m in re.finditer(r'<%s\b|</%s>' % (tag, tag), text[start:]):
        depth += 1 if m.group(0).startswith('<' + tag) else -1
        if depth == 0:
            return start + m.end()
    raise ValueError('sem fim para ' + tag)


def inner(text, start, tag):
    end = match_end(text, start, tag)
    open_end = text.index('>', start) + 1
    return text[open_end:end - len('</%s>' % tag)], end


# ---------- 1. áreas antigas ----------
OLD = {}
first_start = None
pos = 0
while True:
    m = re.search(r'<section class="view" data-view="([^"]+)" data-title="([^"]+)"[^>]*>', s[pos:])
    if not m:
        break
    a = pos + m.start()
    b = match_end(s, a, 'section')
    if first_start is None:
        first_start = a
    body, _ = inner(s, a, 'section')
    v = m.group(1)
    head = re.search(r'<div class="view-head">', body)
    head_html = ''
    if head:
        hi, he = inner(body, head.start(), 'div')
        head_html = body[head.start():he]
        body = body[:head.start()] + body[he:]
    labels, subs = {}, {}
    st = re.search(r'<div class="subtabs"[^>]*>', body)
    if st:
        sti, ste = inner(body, st.start(), 'div')
        for mm in re.finditer(r'<button class="subtab"[^>]*data-sub="([^"]+)"[^>]*>(.*?)</button>', sti, re.S):
            labels[mm.group(1)] = mm.group(2).strip()
        body = body[:st.start()] + body[ste:]
    while True:
        sv = re.search(r'<div class="subview" data-sub="([^"]+)"[^>]*>', body)
        if not sv:
            break
        svi, sve = inner(body, sv.start(), 'div')
        subs[sv.group(1)] = svi
        body = body[:sv.start()] + body[sve:]
    OLD[v] = {'title': m.group(2), 'head': head_html, 'labels': labels, 'subs': subs, 'rest': body.strip(), 'span': (a, b)}
    pos = b
last_end = max(o['span'][1] for o in OLD.values())
for v, o in OLD.items():
    ids = re.findall(r'\bid="([^"]+)"', o['head'])
    if ids:
        print('aviso: ids no cabeçalho de', v, ids)

# a calibração sai de "Medir o modelo" para o Avançado
CALIB = '<section class="card" id="calib-card" style="margin-bottom:16px"></section>'
assert CALIB in OLD['historico']['subs']['modelo']
OLD['historico']['subs']['modelo'] = OLD['historico']['subs']['modelo'].replace(CALIB, '')

# ---------- 2. áreas novas: (separador, nome, fragmentos [(área antiga, separador antigo | None = conteúdo sem separadores)]) ----------
AREAS = [
    ('semana', 'Esta semana', 'Jornada <span class="gw-n">7</span>', 'O que fazer antes do deadline: o resumo, o onze e o banco, o capitão, as transferências e as chips.', [
        ('resumo', 'Resumo', [('resumo', None)]),
        ('onze', 'Onze e banco', [('campo', 'campo'), ('campo', 'jornada'), ('campo', 'plano')]),
        ('capitao', 'Capitão', [('decisoes', 'capitao'), ('decisoes', 'estrategia')]),
        ('transferencias', 'Transferências', [('decisoes', 'trocas'), ('planeador', 'plano')]),
        ('registo', 'Registar o que fiz', [('planeador', 'registo')]),
        ('chips', 'Chips', [('decisoes', 'chips')]),
    ]),
    ('jogos', 'Jogos', 'Jornada <span class="gw-n">7</span>', 'Os jogos da jornada, os onzes prováveis, os pontos ao vivo e quem jogou a meio da semana.', [
        ('jornada', 'Jogos da jornada', [('calendario', 'jogos'), ('calendario', 'plantel')]),
        ('onzes', 'Onzes prováveis', [('onzes', None)]),
        ('aovivo', 'Ao vivo', [('aovivo', 'equipa'), ('aovivo', 'h2h'), ('aovivo', 'liga')]),
        ('europa', 'Europa e descanso', [('equipas', 'europa'), ('equipas', 'europa-eq')]),
    ]),
    ('competicao', 'Rivais', 'Mitras Fantasy League 26/27', 'A liga clássica e o H2H: classificação, previsões, adversários e o que os rivais devem fazer.', [
        ('classificacao', 'Classificação', [('liga', 'classificacao')]),
        ('previsao', 'Previsão da classificação', [('previsao', '__rest__'), ('previsao', 'tabela'), ('previsao', 'frente'), ('previsao', 'metodo')]),
        ('h2h', 'H2H', [('h2h', 'calendario'), ('h2h', 'adversario')]),
        ('comparar', 'Comparar equipas', [('comparar', '__rest__'), ('comparar', 'resumo'), ('comparar', 'grafico'), ('comparar', 'pontos'), ('comparar', 'jogadores'), ('comparar', 'orcamento')]),
        ('vigiar', 'Vigiar rivais', [('rivais', None)]),
        ('ganhar', 'Equipa para ganhar a…', [('ganhar', None)]),
        ('orcamentos', 'Orçamentos e chips', [('liga', 'orcamentos')]),
    ]),
    ('mercado', 'Jogadores', 'Mercado', 'Procurar, comparar e escolher jogadores.', [
        ('pesquisa', 'Pesquisa', [('jogadores', 'pesquisa')]),
        ('comparador', None, [('jogadores', 'comparar')]),
        ('ideal', 'Equipa ideal', [('jogadores', 'ideal')]),
        ('simulada', 'Equipa simulada', [('liga', 'simulacao')]),
        ('forma', 'Em forma', [('plantel', 'forma')]),
        ('precos', 'Preços e alternativas', [('plantel', 'precos'), ('plantel', 'alternativas')]),
    ]),
    ('epoca', 'A minha época', 'Época 2026/27', 'Como tem corrido a tua época: pontos, ranking, jornada a jornada, previsões e orçamento.', [
        ('evolucao', 'Evolução e ranking', [('historico', 'evolucao')]),
        ('jornada', 'Por jornada', [('historico', 'jornada')]),
        ('detalhe', 'Jogador a jogador', [('historico', 'detalhe')]),
        ('previsoes', 'Previsões vs real', [('historico', 'previsoes'), ('historico', 'modelo')]),
        ('orcamento', 'Orçamento do plantel', [('plantel', 'orcamento')]),
    ]),
    ('avancado', 'Avançado', 'Ferramentas que se usam menos', 'Simulador, tabelas e referência. Tudo continua a funcionar como antes.', [
        ('simulador', 'Simulador', [('decisoes', 'simulador')]),
        ('hot', 'Hot takes', [('decisoes', 'hot')]),
        ('lacunas', 'Picks em falta', [('liga', 'lacunas')]),
        ('capitaes', 'Capitães da liga', [('liga', 'capitaes')]),
        ('posse', 'Plantel vs liga', [('liga', 'posse')]),
        ('equipas', 'Tabelas das equipas', [('equipas', 'saldo'), ('equipas', 'forma'), ('equipas', 'criadores'), ('equipas', 'sequencia'), ('equipas', 'capitao')]),
        ('regras', 'Regras e fontes', [('regras', 'pontuacao'), ('regras', 'fontes')]),
        ('calibracao', 'Calibração', [('__calib__', None)]),
    ]),
]
used = set()
strip = lambda h: re.sub(r'<[^>]+>', '', h).strip()


def frag(v, sub):
    if v == '__calib__':
        return CALIB, None
    o = OLD[v]
    if sub is None:
        used.add((v, None))
        return o['rest'], None
    if sub == '__rest__':
        used.add((v, '__rest__'))
        return o['rest'], None
    used.add((v, sub))
    return o['subs'][sub], strip(o['labels'].get(sub, sub))


views_html = []
for aid, aname, eyebrow, intro, subs in AREAS:
    tabs, panes = [], []
    for k, (sid, label, frags) in enumerate(subs):
        if label is None:   # Comparador: mantém o rótulo antigo (tem o contador de jogadores escolhidos)
            label = OLD['jogadores']['labels']['comparar']
        tabs.append(f'<button class="subtab" type="button" data-sub="{sid}">{label}</button>')
        parts = []
        if aid == 'jogos' and sid == 'aovivo':
            parts.append('<div class="eyebrow" id="av-eyebrow">Jornada em direto</div>')
        shown = 0
        for v, sub in frags:
            html, lbl = frag(v, sub)
            if not html.strip():
                continue
            if shown and lbl and len([f for f in frags if f[1] not in (None, '__rest__')]) > 1:
                parts.append(f'<div class="sec-div">{lbl}</div>')
            parts.append(html)
            shown += 1
        panes.append(f'      <div class="subview" data-sub="{sid}"{" hidden" if k else ""}>\n{chr(10).join(parts)}\n      </div>')
    views_html.append(f'''    <!-- ========== {aname.upper()} (V47) ========== -->
    <section class="view" data-view="{aid}" data-title="{aname}"{" hidden" if aid != "semana" else ""}>
      <div class="view-head">
        <div class="eyebrow">{eyebrow}</div>
        <h1>{aname}</h1>
        <p>{intro}</p>
      </div>
      <div class="subtabs" role="tablist" aria-label="{aname}">
        {(chr(10) + "        ").join(tabs)}
      </div>
{chr(10).join(panes)}
    </section>
''')
# tudo usado?
for v, o in OLD.items():
    for sub in o['subs']:
        if (v, sub) not in used:
            print('ERRO: separador antigo sem lugar:', v, sub); sys.exit(1)
    if o['rest'] and (v, None) not in used and (v, '__rest__') not in used:
        print('ERRO: conteúdo antigo sem lugar:', v, o['rest'][:80]); sys.exit(1)

# substitui todas as áreas antigas pelas novas (entre a 1.ª e a última, só há áreas e comentários)
between = s[first_start:last_end]
leftover = between
for o in OLD.values():
    a, b = o['span']
    leftover = leftover.replace(s[a:b], '')
assert not re.sub(r'<!--.*?-->', '', leftover, flags=re.S).strip(), 'há conteúdo entre as áreas: ' + leftover[:200]
s = s[:first_start] + '\n'.join(views_html) + s[last_end:]

# ---------- 3. endereços antigos ----------
ALIAS = {
    'resumo': ['semana', 'resumo'], 'campo': ['semana', 'onze'], 'pontos': ['semana', 'onze'],
    'decisoes': ['semana', 'transferencias'], 'decisoes-trocas': ['semana', 'transferencias'], 'decisoes-capitao': ['semana', 'capitao'],
    'decisoes-estrategia': ['semana', 'capitao'], 'decisoes-simulador': ['avancado', 'simulador'], 'decisoes-chips': ['semana', 'chips'],
    'decisoes-hot': ['avancado', 'hot'], 'planeador': ['semana', 'transferencias'], 'planeador-plano': ['semana', 'transferencias'],
    'planeador-registo': ['semana', 'registo'], 'calendario': ['jogos', 'jornada'], 'onzes': ['jogos', 'onzes'], 'aovivo': ['jogos', 'aovivo'],
    'europa': ['jogos', 'europa'], 'equipas': ['avancado', 'equipas'], 'equipas-europa': ['jogos', 'europa'], 'equipas-europa-eq': ['jogos', 'europa'],
    'historico': ['epoca', 'evolucao'], 'historico-evolucao': ['epoca', 'evolucao'], 'historico-jornada': ['epoca', 'jornada'],
    'historico-detalhe': ['epoca', 'detalhe'], 'historico-previsoes': ['epoca', 'previsoes'], 'historico-modelo': ['epoca', 'previsoes'],
    'plantel': ['mercado', 'forma'], 'plantel-forma': ['mercado', 'forma'], 'plantel-orcamento': ['epoca', 'orcamento'],
    'plantel-precos': ['mercado', 'precos'], 'plantel-alternativas': ['mercado', 'precos'],
    'liga': ['competicao', 'classificacao'], 'liga-classificacao': ['competicao', 'classificacao'], 'liga-posse': ['avancado', 'posse'],
    'liga-lacunas': ['avancado', 'lacunas'], 'liga-capitaes': ['avancado', 'capitaes'], 'liga-orcamentos': ['competicao', 'orcamentos'],
    'liga-simulacao': ['mercado', 'simulada'], 'h2h': ['competicao', 'h2h'], 'comparar': ['competicao', 'comparar'],
    'previsao': ['competicao', 'previsao'], 'jogadores': ['mercado', 'pesquisa'], 'jogadores-pesquisa': ['mercado', 'pesquisa'],
    'jogadores-comparar': ['mercado', 'comparador'], 'jogadores-ideal': ['mercado', 'ideal'], 'ideal': ['mercado', 'ideal'],
    'rivais': ['competicao', 'vigiar'], 'ganhar': ['competicao', 'ganhar'], 'regras': ['avancado', 'regras'],
}
for v in OLD:
    for sub in OLD[v]['subs']:
        ALIAS.setdefault(f'{v}-{sub}', ALIAS[v])


def remap(v, sub):
    k = f'{v}-{sub}' if sub else v
    return ALIAS.get(k) or ALIAS.get(v)


# atributos data-goto no HTML e chamadas literais no JS passam a apontar para os sítios novos
def rep_attr(m):
    v, sub = m.group(1), m.group(3)
    r = remap(v, sub)
    if not r:
        return m.group(0)
    return f'data-goto="{r[0]}" data-goto-sub="{r[1]}"'
s = re.sub(r'data-goto="([a-z0-9-]+)"( data-goto-sub="([a-z0-9-]+)")?', rep_attr, s)


def rep_call(m):
    v, sub = m.group(1), m.group(3)
    r = remap(v, sub)
    return f"showView('{r[0]}', '{r[1]}'" if r else m.group(0)
s = re.sub(r"showView\('([a-z0-9]+)'(, '([a-z0-9-]+)')?", rep_call, s)


def rep_goto(m):
    v, sub = m.group(1), m.group(3)
    r = remap(v, sub)
    return f"goto: '{r[0]}', gotoSub: '{r[1]}'" if r else m.group(0)
s = re.sub(r"goto: '([a-z0-9]+)'(, gotoSub: '([a-z0-9-]+)')?", rep_goto, s)

# ---------- 4. lazyRender por separador ----------
LZ = {"lazyRender('decisoes', renderSimulator)": "lazyRender('avancado/simulador', renderSimulator)",
      "lazyRender('decisoes', renderCapH2H)": "lazyRender('semana/capitao', renderCapH2H)",
      "lazyRender('decisoes', renderStrategy)": "lazyRender('semana/capitao', renderStrategy)",
      "lazyRender('campo', renderPitch)": "lazyRender('semana/onze', renderPitch)",
      "lazyRender('h2h', renderH2HVis)": "lazyRender('competicao/h2h', renderH2HVis)",
      "lazyRender('ganhar', renderWin)": "lazyRender('competicao/ganhar', renderWin)"}
for a, b in LZ.items():
    assert a in s, a
    s = s.replace(a, b)
assert re.findall(r"lazyRender\('([a-z]+)'", s) == [], re.findall(r"lazyRender\('([a-z]+)'", s)
old_lr = re.search(r"  function lazyRender\(view, fn\) \{.*?\n  \}\n", s, re.S).group(0)
s = s.replace(old_lr, """  function lazyRender(view, fn) {
    // V47: 'area' ou 'area/separador' — calcula já se estiver à vista, senão quando for aberto
    const [a, b] = view.split('/');
    const v = document.querySelector(`.view[data-view="${a}"]`);
    const sv = b && v ? v.querySelector(`:scope > .subview[data-sub="${b}"]`) : null;
    if (v && !v.hidden && (!b || (sv && !sv.hidden))) { fn(); return; }
    window.__LAZY = window.__LAZY || {};
    (window.__LAZY[view] = window.__LAZY[view] || new Set()).add(fn);
  }
""")
s = s.replace("""  const prevVisible = () => { const v = document.querySelector('.view[data-view="previsao"]'); return v && !v.hidden; };""",
              """  const prevVisible = () => { const v = document.querySelector('.view[data-view="competicao"]'), sv = v && v.querySelector(':scope > .subview[data-sub="previsao"]'); return !!(v && !v.hidden && sv && !sv.hidden); };""")
s = s.replace("""document.querySelector('.nav-item[data-view="resumo"] .nav-meta')""", """document.querySelector('.nav-item[data-view="semana"] .nav-meta')""")

# ---------- 5. showView ----------
old_sv = re.search(r"  function showView\(name, sub, opts\) \{.*?\n  \}\n(?=  function parseToken)", s, re.S).group(0)
s = s.replace(old_sv, """  function showView(name, sub, opts) {
    opts = opts || {};
    // V47: as áreas antigas (e os endereços #area-separador antigos) abrem o sítio novo
    if (!viewNames.includes(name)) { const al = VIEW_ALIAS[sub ? name + '-' + sub : name] || VIEW_ALIAS[name]; if (al) { [name, sub] = al; } }
    if (!viewNames.includes(name)) name = 'semana';
    const view = views.find(v => v.dataset.view === name);
    views.forEach(v => { v.hidden = v !== view; });
    document.querySelectorAll('.nav-item[data-view]').forEach(b => {
      if (b.dataset.view === name) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current');
    });
    const tabs = subsOf(view);
    let subLabel = '';
    if (tabs.length) {
      if (!tabs.some(t => t.dataset.sub === sub)) sub = tabs[0].dataset.sub;
      tabs.forEach(t => {
        t.setAttribute('role', 'tab');
        t.setAttribute('aria-selected', String(t.dataset.sub === sub));
        if (t.dataset.sub === sub) subLabel = t.textContent.trim();
      });
      view.querySelectorAll(':scope > .subview[data-sub]').forEach(sv => { sv.hidden = sv.dataset.sub !== sub; });
    } else {
      sub = '';
    }
    // o que é pesado só é calculado quando a área/o separador é aberto
    [name, name + '/' + sub].forEach(k => { const LZ = window.__LAZY && window.__LAZY[k]; if (LZ) { delete window.__LAZY[k]; LZ.forEach(f => { try { f(); } catch (e) { console.error(e); } }); } });
    if (name === 'competicao' && sub === 'previsao') { try { renderPrevisao(); } catch (e) { console.error(e); } }
    if (name === 'mercado' && sub === 'ideal') { try { idealOpen(); } catch (e) { console.error(e); } }
    const title = view.dataset.title || name;
    document.getElementById('crumbs').innerHTML = subLabel ? `${title} <span aria-hidden="true">›</span> <b>${subLabel}</b>` : `<b>${title}</b>`;
    const token = sub ? `${name}-${sub}` : name;
    try { history.replaceState(null, '', '#' + token); } catch (e) {}
    try { localStorage.setItem('fpl-view', token); } catch (e) {}
    if (!opts.keepScroll) window.scrollTo(0, 0);
    // ao mudar de separador no telemóvel, o separador escolhido fica à vista
    const st = view.querySelector(':scope > .subtabs .subtab[aria-selected="true"]');
    if (st && st.parentElement.scrollWidth > st.parentElement.clientWidth) { const r = st.parentElement; r.scrollLeft = st.offsetLeft - (r.clientWidth - st.clientWidth) / 2; }
  }
""")
s = s.replace("""  showView(startTok ? startTok[0] : 'resumo', startTok ? startTok[1] : '', {keepScroll: true});""",
              """  showView(startTok ? startTok[0] : 'semana', startTok ? startTok[1] : '', {keepScroll: true});""")
s = s.replace("""  if (!startTok || !viewNames.includes(startTok[0])) {""", """  if (!startTok || !(viewNames.includes(startTok[0]) || VIEW_ALIAS[startTok[0]])) {""")

# ---------- 6. menu lateral ----------
nav_old = re.search(r'    <nav class="nav" aria-label="Áreas">.*?</nav>\n', s, re.S).group(0)
s = s.replace(nav_old, """    <nav class="nav" aria-label="Áreas">
      <div class="nav-group">
        <button class="nav-item" data-view="semana" type="button">Esta semana <span class="nav-meta">J<span class="gw-n">7</span></span></button>
        <button class="nav-item" data-view="jogos" type="button">Jogos <span class="nav-meta" id="av-nav-meta"></span></button>
        <button class="nav-item" data-view="competicao" type="button">Rivais</button>
        <button class="nav-item" data-view="mercado" type="button">Jogadores</button>
        <button class="nav-item" data-view="epoca" type="button">A minha época</button>
      </div>
      <div class="nav-group nav-adv">
        <button class="nav-item adv" data-view="avancado" type="button">Avançado</button>
      </div>
    </nav>
""")
# rodapé: entrada discreta para o Avançado (é a única no telemóvel)
s = s.replace('<div class="page-foot">Painel FPL', '<div class="page-foot"><button type="button" class="linklike adv-link" data-goto="avancado">Avançado (simulador, tabelas, regras)</button> · Painel FPL', 1)

# ---------- 7. menu do telemóvel ----------
old_mn = re.search(r"  \(function mobileNav\(\) \{.*?\n  \}\)\(\);\n", s, re.S).group(0)
s = s.replace(old_mn, """  (function mobileNav() {
    // V47: 5 botões (as 5 áreas); os separadores da área aparecem dentro dela. O Avançado fica no rodapé.
    const nav = document.querySelector('.nav'); if (!nav) return;
    const items = [...nav.querySelectorAll('.nav-item[data-view]:not(.adv)')];
    const SHORT_LBL = {semana: 'Esta semana', jogos: 'Jogos', competicao: 'Rivais', mercado: 'Jogadores', epoca: 'Época'};
    const bar = document.createElement('div');
    bar.className = 'mnav'; bar.setAttribute('role', 'group'); bar.setAttribute('aria-label', 'Áreas');
    items.forEach(it => {
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'mnav-btn'; b.dataset.v = it.dataset.view;
      b.textContent = SHORT_LBL[it.dataset.view] || it.textContent.trim();
      b.addEventListener('click', () => showView(it.dataset.view));
      bar.appendChild(b);
    });
    nav.parentNode.insertBefore(bar, nav);
    function sync() {
      const cur = nav.querySelector('.nav-item[aria-current="page"]');
      bar.querySelectorAll('.mnav-btn').forEach(b => { const on = cur && b.dataset.v === cur.dataset.view; b.classList.toggle('here', !!on); b.setAttribute('aria-pressed', String(!!on)); });
      // avisos importantes e "ao vivo" também nos botões
      [['semana', '.al-dot'], ['jogos', '.av-dot']].forEach(([v, sel]) => {
        const src = nav.querySelector(`.nav-item[data-view="${v}"] ${sel}`), dst = bar.querySelector(`.mnav-btn[data-v="${v}"]`);
        if (!dst) return; const old = dst.querySelector(sel); if (old) old.remove();
        if (src) dst.insertAdjacentHTML('beforeend', src.outerHTML);
      });
    }
    new MutationObserver(sync).observe(nav, {subtree: true, attributes: true, childList: true, characterData: true});
    sync();
  })();
""")

# ---------- 8. índice único (pesquisa e guia) ----------
SYN = {
    'semana/resumo': ['resumo', 'avisos', 'alertas', 'o que fazer', 'início', 'inicio', 'números', 'gráficos'],
    'semana/onze': ['onze', 'banco', 'campo', 'titulares', 'formação', 'pontos esperados', 'jogador a jogador', 'próximas 5', 'substituições'],
    'semana/capitao': ['capitão', 'braçadeira', 'vice', 'capitão h2h', 'estratégia', 'diferenciais', 'triple captain'],
    'semana/transferencias': ['transferências', 'trocas', 'compras', 'vendas', 'planeador', 'plano automático', 'plano manual', 'hits', 'sugestão'],
    'semana/registo': ['registar', 'registo', 'o que fiz', 'confirmar troca'],
    'semana/chips': ['chips', 'wildcard', 'free hit', 'bench boost', 'triple captain', 'plano de chips'],
    'jogos/jornada': ['jogos', 'calendário', 'fixtures', 'odds', 'casas de apostas', 'dificuldade'],
    'jogos/onzes': ['onzes prováveis', 'titulares prováveis', 'lesões', 'escalações', 'line-ups'],
    'jogos/aovivo': ['ao vivo', 'direto', 'live', 'pontos ao vivo', 'tempo real'],
    'jogos/europa': ['europa', 'liga dos campeões', 'champions', 'descanso', 'taça da liga', 'rotação'],
    'competicao/classificacao': ['classificação', 'liga', 'tabela', 'mini-liga', 'liga clássica'],
    'competicao/previsao': ['previsão da classificação', 'previsão', 'quem ganha a liga', 'top 3', 'simulação da liga'],
    'competicao/h2h': ['h2h', 'confronto', 'adversário', 'head to head', 'resultados'],
    'competicao/comparar': ['comparar equipas', 'lado a lado', 'comparar gestores'],
    'competicao/vigiar': ['vigiar rivais', 'rivais', 'previsão dos rivais', 'o que os rivais vão fazer'],
    'competicao/ganhar': ['equipa para ganhar', 'ganhar a', 'probabilidade de ganhar', 'bater rivais'],
    'competicao/orcamentos': ['orçamentos', 'budget', 'dinheiro', 'valor da equipa', 'chips da liga'],
    'mercado/pesquisa': ['pesquisa', 'procurar jogador', 'jogadores', 'filtros'],
    'mercado/comparador': ['comparador', 'comparar jogadores'],
    'mercado/ideal': ['equipa ideal', 'equipa perfeita', 'melhor equipa', 'otimizador', 'dream team'],
    'mercado/simulada': ['equipa simulada', 'simular equipa', 'montar equipa'],
    'mercado/forma': ['em forma', 'forma', 'quentes'],
    'mercado/precos': ['preços', 'subidas', 'descidas', 'alternativas', 'substitutos'],
    'epoca/evolucao': ['evolução', 'ranking', 'ranking geral', 'gráfico de pontos'],
    'epoca/jornada': ['por jornada', 'jornadas anteriores', 'histórico'],
    'epoca/detalhe': ['jogador a jogador', 'onze ótimo', 'pontos perdidos no banco'],
    'epoca/previsoes': ['previsões vs real', 'medir o modelo', 'erro do modelo', 'acerto'],
    'epoca/orcamento': ['orçamento do plantel', 'budget', 'dinheiro', 'valor do plantel', 'banco'],
    'avancado/simulador': ['simulador', 'testar trocas', 'simular transferências'],
    'avancado/hot': ['hot takes', 'diferenciadores', 'podem surpreender'],
    'avancado/lacunas': ['picks em falta', 'lacunas', 'template'],
    'avancado/capitaes': ['capitães da liga', 'capitães'],
    'avancado/posse': ['plantel vs liga', 'posse', 'ownership', 'eo'],
    'avancado/equipas': ['equipas', 'saldo de xg', 'xg', 'forma das equipas', 'criadores', 'sequência', 'perfil do capitão'],
    'avancado/regras': ['regras', 'pontuação', 'fontes', 'como funciona'],
    'avancado/calibracao': ['calibração', 'ajustar o modelo'],
}
INDEX, AREAS_JS = [], []
for aid, aname, eyebrow, intro, subs in AREAS:
    names = []
    for sid, label, frags in subs:
        n = 'Comparador' if label is None else label
        INDEX.append({'v': aid, 's': sid, 'a': aname, 'n': n, 'syn': SYN.get(f'{aid}/{sid}', [])})
        names.append(n)
    AREAS_JS.append({'v': aid, 'n': aname, 'd': intro, 'subs': names})
index_js = ('  // ===== V47 (16 out 2026): índice único das áreas e separadores — menu, pesquisa e guia =====\n'
            f'  const APP_AREAS = {json.dumps(AREAS_JS, ensure_ascii=False)};\n'
            f'  const APP_INDEX = {json.dumps(INDEX, ensure_ascii=False)};\n'
            f'  const VIEW_ALIAS = {json.dumps(ALIAS, ensure_ascii=False)};\n')
anchor = '  // ===== Navegação: menu lateral (áreas) + sub-abas (temas dentro de cada área) ====='
assert anchor in s
s = s.replace(anchor, index_js + anchor)

# ---------- 9. guia a partir do índice ----------
old_tour = re.search(r"  const TOUR = \[.*?\n  \];\n", s, re.S).group(0)
s = s.replace(old_tour, """  const TOUR = [
    {sel: '#todo', t: 'O que fazer esta semana', d: 'Começa sempre aqui: a transferência, o capitão e o onze sugeridos para a próxima jornada, com botões para ver os detalhes.'},
    {sel: '.mnav, .nav', t: 'As cinco áreas', d: APP_AREAS.filter(a => a.v !== 'avancado').map(a => `<b>${a.n}</b>: ${a.subs.join(', ')}.`).join('<br>') + '<br>O <b>Avançado</b> (simulador, tabelas e regras) fica no fim do menu e no rodapé.'},
    {sel: '#srch', t: 'Procurar', d: 'Escreve o que procuras: uma ferramenta ("capitão", "wildcard", "dinheiro"), um jogador (abre a ficha) ou um gestor da liga (abre Comparar equipas). No computador, a tecla / abre a pesquisa.'},
    {sel: '.mswitch', t: 'Bruno ou Marco', d: 'Troca aqui entre as duas equipas. Tudo na app passa a ser sobre a equipa escolhida.'},
    {sel: '#theme-btn', t: 'Modo noite e nomes', d: 'Este botão muda entre claro e escuro. E em qualquer sítio da app, toca no nome de um jogador para abrires a ficha dele.'},
  ];
""")
s = s.replace("""    showView('semana', 'resumo');
    let i = 0;
    const ov = document.createElement('div'); ov.className = 'tour-ov';""", """    showView('semana', 'resumo');
    let i = 0;
    const ov = document.createElement('div'); ov.className = 'tour-ov';""")
H.write_text(s, encoding='utf-8', newline='\n')
print('ok: áreas', [a[0] for a in AREAS], '| separadores', len(INDEX), '| endereços antigos', len(ALIAS))
