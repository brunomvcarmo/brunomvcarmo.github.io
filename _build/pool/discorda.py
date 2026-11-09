"""V59 (9 nov 2026): onde a app discorda da FPL e dos sites — e quem tem razão.

Consenso = mediana dos pontos esperados de fora para cada jogador e jornada: FPL (ep_next, só a próxima jornada),
FPL Form (pontos "se jogar" × probabilidade de jogar), FPL Copilot, Onside Arena e Fantasy Football Pundit
(_build/research/proj-numeric.json, lido pelo research_week.py). Só conta com 2 ou mais fontes.

A app mistura os sites (40%) com a parte que é só nossa. Para medir a discordância verdadeira compara-se o consenso
com a parte nossa: (0,40 × forma + 0,60 × modelo base) × disponibilidade × leitura × descanso (ver model25.py).
Mostram-se as duas comparações (app completa e só a parte nossa).

O porquê (tipo): minutos (disponibilidade/leitura/descanso), forma (últimas 3 jornadas), ocasioes (xG+xA da época
contra golos+assistências reais), jogo (dificuldade oficial do adversário) ou epoca (modelo base da época inteira).

Uso (a partir da raiz):
  chamado pelo gen25.py → build(...) devolve o objeto DISAGREE e guarda as discordâncias da próxima jornada em
      _build/research/discorda.json (só antes do deadline; depois fica congelado)
  py -X utf8 _build/pool/discorda.py medir        pontos reais (API oficial event/N/live) das jornadas guardadas
  py -X utf8 _build/pool/discorda.py reconstruir  refaz J7, J8 e J10 a partir das versões antigas do index.html
  py -X utf8 _build/pool/discorda.py resumo       mostra a taxa de acerto
"""
import csv, json, re, statistics, subprocess, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

BD = Path(__file__).resolve().parents[1]
ROOT = BD.parent
RES = BD / 'research'
HIST = RES / 'discorda.json'
SRC = [['fpl', 'FPL'], ['fplform', 'FPL Form'], ['fplcopilot', 'FPL Copilot'], ['onside', 'Onside Arena'], ['pundit', 'FF Pundit']]
DIFF_MULT = {1: 1.30, 2: 1.15, 3: 1.00, 4: 0.85, 5: 0.70}
GOAL = {'gk': 6, 'def': 6, 'mid': 5, 'fwd': 4}
TYPES = {'minutos': 'Minutos e disponibilidade', 'forma': 'Forma recente', 'ocasioes': 'Ocasiões (xG) vs pontos',
         'jogo': 'Adversário', 'epoca': 'Modelo da época toda'}
# discordância numa jornada: |nossa − consenso| ≥ 1,0 e ≥ 20% do maior dos dois, e um dos dois ≥ 2,5 (jogador que conta)
THR_ONE, THR_REL, THR_MIN = 1.0, 0.20, 2.5


def num(x, d=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def _teams():
    T = {}
    for r in csv.DictReader(open(BD / 'mirror' / 'teams.csv', encoding='utf-8')):
        T[int(r['id'])] = (r['short_name'], r['name'])
    return T


def _snap():
    """playerstats do espelho: {id: {gw: linha}} (só as colunas que interessam)."""
    S = {}
    keep = ('goals_scored', 'assists', 'expected_goals', 'expected_assists', 'minutes', 'starts')
    for r in csv.DictReader(open(BD / 'mirror' / 'playerstats.csv', encoding='utf-8')):
        S.setdefault(int(r['id']), {})[int(r['gw'])] = {k: num(r.get(k)) for k in keep}
    return S


def flagged(own, cons, off=0.0):
    """off = diferença geral da jornada (média de nossa − consenso nos jogadores que contam). Desconta-se para ficarem
    só as diferenças de jogador para jogador, e a diferença sem desconto tem de ir no mesmo sentido."""
    g = own - (cons + off)
    return (abs(g) >= THR_ONE and abs(g) >= THR_REL * max(own, cons) and max(own, cons) >= THR_MIN
            and (own - cons) * g > 0)


def offset(pairs):
    """pairs = [(nossa, consenso)]; desvio geral só conta se for ≥ 0,25 (com 2 fontes os sites às vezes vão todos mais alto)."""
    v = [o - c for o, c in pairs if c >= THR_MIN and o >= 1]
    if len(v) < 30:
        return 0.0
    m = statistics.mean(v)
    return round(m, 2) if abs(m) >= 0.25 else 0.0


def consensus(vals):
    v = [x for x in vals if x is not None]
    return round(statistics.median(v), 2) if len(v) >= 2 else None


def ext_vals(X, pid, g, en, nextgw):
    """[fpl, fplform×prob, copilot, onside, pundit] para a jornada g (None quando a fonte não tem)."""
    e = X.get(str(pid)) or {}
    prob = e.get('fplform_prob_appearing')
    out = [round(num(en), 1) if g == nextgw and en is not None else None]
    for k in ('fplform', 'fplcopilot', 'onside', 'pundit'):
        v = (e.get(k) or {}).get(str(g))
        if v is not None and k == 'fplform' and prob is not None:
            v = v * num(prob, 1.0)
        out.append(None if v is None else round(num(v), 1))
    return out


def _pl(n):
    return ('%.1f' % n).replace('.', ',')


def _join(xs):
    xs = [str(x) for x in xs]
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' e ' + xs[-1]


def explain(r):
    """r: pos, own, cons, F, U, AR, pts3, m3, rd, st, season (golos, assist., xg, xa, minutos, jogos), fx [(opp, casa, dif)], g.
    Devolve (tipo, texto) — o texto completa "A app dá mais/menos porque …"."""
    gap = r['own'] - r['cons'] - r.get('off', 0.0)
    sg = 1 if gap > 0 else -1
    base = 0.4 * r['F'] + 0.6 * r['U']
    AR = r['AR']
    c = {'minutos': base * (AR - 1), 'forma': 0.4 * (r['F'] - r['U']) * AR}
    S = r.get('season') or {}
    apps = S.get('apps') or 0
    if apps and r['pos'] != 'gk':
        per = ((S['xg'] - S['g']) * GOAL[r['pos']] + (S['xa'] - S['a']) * 3) / apps
        c['ocasioes'] = 0.5 * 0.6 * AR * per
    fx = r.get('fx') or []
    if fx:
        mult = sum(DIFF_MULT.get(f[2], 1.0) for f in fx) / len(fx)
        c['jogo'] = base * AR * (1 - 1 / mult)
    if sg < 0 and (r['U'] <= 0.05 or base * AR < 0.6):
        # a app quase não o vê a jogar: sem minutos suficientes na época ou fora por lesão/castigo
        return 'minutos', _text('minutos', sg, dict(r, rd=r.get('rd') or ('' if r['U'] > 0.05 else '_semmin')), S, AR)
    cand = sorted([(abs(v), k) for k, v in c.items() if v * sg > 0 and abs(v) >= max(0.3, 0.35 * abs(gap))], reverse=True)
    kind = cand[0][1] if cand else 'epoca'
    return kind, _text(kind, sg, r, S, AR)


def _text(kind, sg, r, S, AR):
    pos = r['pos']
    if kind == 'minutos':
        if r.get('rd') == '_semmin':
            m = int((S or {}).get('mins') or 0)
            return 'a app quase não tem minutos dele nesta época (%d no total): o modelo só conta com quem tem jogado; os sites contam que jogue' % m
        if r.get('rd'):
            return 'a app tem uma leitura própria: ' + r['rd'][0].lower() + r['rd'][1:]
        if r.get('st') in ('i', 'd', 's', 'u', 'n') or AR < 0.9:
            return 'a app só conta com ≈%d%% de o ver jogar (lesão, dúvida, castigo ou previsão de regresso); os sites contam mais com ele' % round(AR * 100)
        return 'a app desconta minutos: jogou %d minutos nas últimas 3 jornadas' % (r.get('m3') or 0)
    if kind == 'forma':
        p3 = [x for x in (r.get('pts3') or []) if x is not None]
        tx = _join(p3) if p3 else '?'
        if sg > 0:
            return 'está em forma (%s pontos nas últimas 3 jornadas) e a app dá peso à forma recente; os sites olham mais para a época toda' % tx
        return 'as últimas 3 jornadas foram fracas (%s pontos) e a app dá peso a isso; os sites dão-lhe o benefício da dúvida' % tx
    if kind == 'ocasioes':
        ga = int(S['g'] + S['a'])
        xga = S['xg'] + S['xa']
        if sg > 0:
            return ('cria muitas ocasiões que ainda não deram pontos: %d golos e assistências na época, quando as ocasiões (xG + xA) '
                    'valiam %s; a app conta com as ocasiões, quem olha para os pontos ainda não' % (ga, _pl(xga)))
        return 'marcou e assistiu mais do que as ocasiões fazem esperar (%d golos e assistências contra %s esperados): a app espera que abrande' % (ga, _pl(xga))
    if kind == 'jogo':
        T = _teams_cache()
        fx = r.get('fx') or []
        txt = ' e '.join(('recebe o %s' if h else 'joga no campo do %s') % T.get(o, ('?', '?'))[1] for o, h, d in fx)
        if sg > 0:
            return 'na J%d %s, um jogo fácil, e a app sobe muito o valor por causa do adversário' % (r['g'], txt)
        return 'na J%d %s, um jogo difícil, e a app baixa muito o valor por causa do adversário' % (r['g'], txt)
    # epoca
    mins = S.get('mins') or 0
    x90 = (S.get('xg', 0) + S.get('xa', 0)) / mins * 90 if mins >= 450 else 0
    if pos in ('gk', 'def'):
        if sg > 0:
            return 'o modelo base da app (época toda) conta mais com balizas a zero, defesas e contribuição defensiva do que os sites'
        return 'o modelo base da app (época toda) espera mais golos sofridos e menos balizas a zero do que os sites'
    if sg > 0:
        return 'o modelo base da app (época toda: %s golos + assistências esperados por 90 minutos, bónus) dá-lhe mais do que os sites' % _pl(x90).replace(',0', '') if x90 else 'o modelo base da app (época toda) dá-lhe mais do que os sites'
    mpg = mins / S['apps'] if S.get('apps') else 0
    if not x90:
        return 'o modelo base da app (época toda) é mais pessimista: jogou pouco (%d minutos)' % mins
    return 'o modelo base da app (época toda) é mais pessimista: %s golos + assistências esperados por 90 minutos%s' % (
        _pl(x90), ' e poucos minutos por jogo (%d)' % mpg if mpg and mpg < 70 else '')


_TC = None


def _teams_cache():
    global _TC
    if _TC is None:
        _TC = _teams()
    return _TC


def season_of(S, pid, upto):
    """Totais da época até à jornada `upto` (snapshot do espelho)."""
    rows = S.get(pid) or {}
    g = max([x for x in rows if x <= upto] or [0])
    if not g:
        return None
    r = rows[g]
    apps = sum(1 for k in range(1, g + 1) if k in rows and (rows[k]['minutes'] - (rows[k - 1]['minutes'] if k - 1 in rows else 0)) > 0)
    return dict(g=r['goals_scored'], a=r['assists'], xg=r['expected_goals'], xa=r['expected_assists'], mins=r['minutes'], apps=apps)


def fx_of(FX, team, g):
    out = []
    for f in FX.get(str(g), []):
        if f['h'] == team:
            out.append((f['a'], True, f.get('dh', 3)))
        elif f['a'] == team:
            out.append((f['h'], False, f.get('da', 3)))
    return out


def load_hist():
    if HIST.exists():
        return json.load(open(HIST, encoding='utf-8'))
    return {'about': 'V59: discordâncias app × consenso guardadas antes de cada deadline e os pontos reais (API oficial). '
                     'Linhas: [id, nome, pos, equipa, app, nossa, consenso, n.º fontes, tipo, posse na liga %, texto].',
            'gws': {}}


def save_hist(H):
    HIST.write_text(json.dumps(H, ensure_ascii=False, indent=1), encoding='utf-8', newline='\n')


def _row(pid, name, pos, team, app, own, cons, n, kind, lo, txt):
    return [pid, name, pos, team, round(app, 1), round(own, 1), round(cons, 1), n, kind, lo, txt]


# ----------------------------------------------------------------- estatísticas (quem tem razão)
def stats(H):
    def add(d, k, w):
        x = d.setdefault(k, [0, 0.0])
        x[0] += 1
        x[1] += w
    allv, full, pos, typ, dr, gws, ex = [0, 0.0], [0, 0.0], {}, {}, {}, [], []
    for g in sorted(H['gws'], key=int):
        G = H['gws'][g]
        real = G.get('real')
        if not real:
            continue
        n = w = 0.0
        eo = ec = 0.0
        for row in G['rows']:
            pid, name, ps, team, app, own, cons, ns, kind, lo, txt = row
            if str(pid) not in real:
                continue
            a = real[str(pid)]
            do, dc, da = abs(a - own), abs(a - cons), abs(a - app)
            win = 1.0 if do < dc else (0.5 if do == dc else 0.0)
            winf = 1.0 if da < dc else (0.5 if da == dc else 0.0)
            allv[0] += 1; allv[1] += win
            full[0] += 1; full[1] += winf
            add(pos, ps, win); add(typ, kind, win); add(dr, 'mais' if own > cons else 'menos', win)
            n += 1; w += win; eo += do; ec += dc
            ex.append(dict(gw=int(g), id=pid, nm=name, own=own, cons=cons, real=a, kind=kind, win=win, gap=abs(own - cons)))
        if n:
            gws.append(dict(gw=int(g), n=int(n), w=w, eo=round(eo / n, 2), ec=round(ec / n, 2), src=G.get('src', ''), final=G.get('final', False)))
    ex.sort(key=lambda e: -e['gap'])
    rnd = lambda d: {k: [v[0], round(v[1], 1)] for k, v in d.items()}
    return dict(all=[allv[0], round(allv[1], 1)], full=[full[0], round(full[1], 1)], pos=rnd(pos), type=rnd(typ), dir=rnd(dr),
                gws=gws, ex=ex[:30], types=TYPES)


# ----------------------------------------------------------------- chamado pelo gen25.py
def build(pool, snap_unused, FX, horizon, nextgw, deadline, LV=None):
    X = json.load(open(RES / 'proj-numeric.json', encoding='utf-8'))['players']
    S = _snap()
    T = _teams_cache()
    out, rows_next, texts, tix = {}, [], [], {}
    base = []
    for p in pool:
        cm = p.get('_cmp')
        if not cm:
            continue
        rec = dict(a=[], o=[], c=[], x=[], w=[], _AR=[])
        for i, g in enumerate(horizon):
            app = p['ep'][i]
            bl = cm['bl'][i]
            AR = min(1.0, app / bl) if bl > 0 else 0.0
            own = (0.4 * cm['F'][i] + 0.6 * cm['U'][i]) * AR
            xv = ext_vals(X, p['id'], g, p.get('en'), nextgw)
            cons = consensus(xv)
            rec['a'].append(round(app, 1)); rec['o'].append(round(own, 1)); rec['c'].append(None if cons is None else round(cons, 1))
            rec['x'].append(xv if cons is not None else None); rec['_AR'].append(AR); rec['w'].append(None)
        base.append((p, rec))
    OFF = [offset([(r['o'][i], r['c'][i]) for p, r in base if r['c'][i] is not None]) for i in range(len(horizon))]
    for p, rec in base:
        cm = p['_cmp']
        season = season_of(S, p['id'], nextgw - 1)
        pts = (p.get('pts') or [])[-3:]
        AR = rec.pop('_AR')
        cs = [c for c in rec['c'] if c is not None]
        if not cs:
            continue
        for i, g in enumerate(horizon):
            own, cons = rec['o'][i], rec['c'][i]
            if cons is None or not flagged(own, cons, OFF[i]):
                continue
            r = dict(pos=p['c'], own=own, cons=cons, off=OFF[i], F=cm['F'][i], U=cm['U'][i], AR=AR[i], pts3=pts, m3=p.get('m3'),
                     rd=p.get('rd') if i == 0 else '', st=p.get('s'), season=season, fx=fx_of(FX, p['t'], g), g=g)
            kind, txt = explain(r)
            if txt not in tix:
                tix[txt] = len(texts); texts.append(txt)
            rec['w'][i] = [kind, tix[txt]]
            if i == 0:
                rows_next.append(_row(p['id'], p['n'], p['c'], T.get(p['t'], ('?',))[0], rec['a'][0], own, cons,
                                      sum(v is not None for v in rec['x'][0]), kind, p.get('lo', 0), txt))
        if max(rec['a'] + rec['o'] + cs) >= 2 or p.get('lo', 0) > 0:
            out[p['id']] = rec
    H = load_hist()
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    G = H['gws'].get(str(nextgw))
    if now < deadline and not (G and G.get('real')):
        H['gws'][str(nextgw)] = dict(saved=now, deadline=deadline, src='guardado antes do deadline', rows=rows_next, off=OFF[0])
        save_hist(H)
        print('discorda: J%d guardada (%d discordâncias)' % (nextgw, len(rows_next)))
    else:
        print('discorda: deadline da J%d já passou — o histórico não muda' % nextgw)
    st = stats(H)
    print('discorda: %d jogadores com consenso; desvio geral por jornada %s; acerto da app nas discordâncias medidas: %s' % (len(out), OFF, st['all']))
    return dict(gws=horizon, next=nextgw, gen=now, deadline=deadline, src=SRC, thr=[THR_ONE, THR_REL, THR_MIN], off=OFF, types=TYPES,
                t=texts, p=out, hist=st)


# ----------------------------------------------------------------- medir (depois de cada jornada)
def _get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (fpl-app)', 'Accept': '*/*'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def medir():
    H = load_hist()
    try:
        ev = {e['id']: e for e in _get('https://fantasy.premierleague.com/api/bootstrap-static/?v=discorda')['events']}
    except Exception as e:
        print('discorda medir: sem acesso à API oficial (%s) — fica para a próxima' % e)
        return
    for g, G in sorted(H['gws'].items(), key=lambda x: int(x[0])):
        e = ev.get(int(g))
        if not e or G.get('final'):
            continue
        if not e.get('finished'):
            # jornada por fechar: mede (provisório) só se todos os jogos já acabaram
            if not (e.get('is_current') or e.get('is_previous')):
                continue
            try:
                fx = _get('https://fantasy.premierleague.com/api/fixtures/?event=%s' % g)
            except Exception:
                continue
            if not fx or not all(f.get('finished_provisional') for f in fx):
                continue
        try:
            live = _get('https://fantasy.premierleague.com/api/event/%s/live/?v=discorda' % g)['elements']
        except Exception as ex:
            print('discorda medir: J%s falhou (%s)' % (g, ex))
            continue
        pts = {x['id']: x['stats']['total_points'] for x in live}
        mins = {x['id']: x['stats']['minutes'] for x in live}
        ids = {r[0] for r in G['rows']}
        G['real'] = {str(i): pts.get(i, 0) for i in ids}
        G['mins'] = {str(i): mins.get(i, 0) for i in ids}
        G['final'] = bool(e.get('finished') and e.get('data_checked'))
        G['measured'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        print('discorda medir: J%s → %d jogadores%s' % (g, len(ids), '' if G['final'] else ' (provisório)'))
    save_hist(H)
    resumo(H)


def resumo(H=None):
    H = H or load_hist()
    st = stats(H)
    n, w = st['all']
    print('Acerto da app (parte nossa) nas discordâncias: %s/%d = %s%%' % (w, n, round(100 * w / n) if n else '-'))
    print('App completa (com os sites): %s/%d' % (st['full'][1], st['full'][0]))
    for k in ('pos', 'type', 'dir'):
        print(' ', k, {a: '%s/%d' % (b[1], b[0]) for a, b in st[k].items()})
    for G in st['gws']:
        print('  J%d: %s/%d · erro médio app %s vs consenso %s · %s' % (G['gw'], G['w'], G['n'], G['eo'], G['ec'], G['src']))


# ----------------------------------------------------------------- reconstruir J7, J8, J10 (versões antigas do index.html)
OLD = {7: ('b15b756', '_build/research_j7/proj-numeric.json'), 8: ('775390c', None), 10: ('d3063a6', 'git:d3063a6:_build/research/proj-numeric.json')}


def _git(*a):
    return subprocess.run(['git', *a], cwd=ROOT, capture_output=True, text=True, encoding='utf-8').stdout


def reconstruir():
    H = load_hist()
    S = _snap()
    T = _teams_cache()
    FX = json.load(open(BD / 'data' / 'fixtures.json', encoding='utf-8'))
    for g, (commit, probsrc) in OLD.items():
        html = _git('show', commit + ':index.html')
        keys = json.loads(re.search(r'const POOL_KEYS = (\[.*?\]);', html).group(1))
        body = re.search(r'const POOL24 = \[\n(.*?)\n\]\.map', html, re.S).group(1)
        pool = [dict(zip(keys, json.loads(l.rstrip(',')))) for l in body.split('\n')]
        ext = json.loads(re.search(r'const EXT7 = (\{.*?\});\n', html).group(1))
        meta = json.loads(re.search(r'const GW_META = (\{.*?\});\n', html).group(1))
        assert meta['next'] == g, (g, meta['next'])
        prob = {}
        if probsrc:
            src = _git('show', probsrc[4:]) if probsrc.startswith('git:') else (ROOT / probsrc).read_text(encoding='utf-8')
            prob = {k: v.get('fplform_prob_appearing') for k, v in json.loads(src)['players'].items()}
        rows, cand = [], []
        for p in pool:
            k = p.get('k')
            if not k or not p.get('ep'):
                continue
            F, U, Xs, AR = k
            e = ext.get(str(p['id']), {})
            vals = [round(num(p.get('en')), 1)]
            for s in ('fplform', 'fplcopilot', 'onside', 'pundit'):
                v = e.get(s)
                if v is not None and s == 'fplform' and prob.get(str(p['id'])) is not None:
                    v = v * num(prob[str(p['id'])], 1.0)
                vals.append(None if v is None else round(num(v), 1))
            cons = consensus(vals)
            if cons is None:
                continue
            own = (0.4 * F + 0.6 * U) * AR
            cand.append((p, F, U, AR, own, cons, vals))
        off = offset([(c[4], c[5]) for c in cand])
        for p, F, U, AR, own, cons, vals in cand:
            app = p['ep'][0]
            if not flagged(own, cons, off):
                continue
            pts = (p.get('pts') or [])[-3:]
            r = dict(pos=p['c'], own=own, cons=cons, off=off, F=F, U=U, AR=AR, pts3=pts, m3=p.get('m3'), rd=p.get('rd') or '', st=p.get('s'),
                     season=season_of(S, p['id'], g - 1), fx=fx_of(FX, p['t'], g), g=g)
            kind, txt = explain(r)
            rows.append(_row(p['id'], p['n'], p['c'], T.get(p['t'], ('?',))[0], app, own, cons, sum(v is not None for v in vals), kind, p.get('lo', 0), txt))
        old = H['gws'].get(str(g), {})
        H['gws'][str(g)] = dict(saved=_git('log', '-1', '--format=%cI', commit).strip(), deadline=meta.get('deadline', ''),
                                src='reconstruído (index.html de %s)' % commit, rows=rows)
        for k2 in ('real', 'mins', 'final', 'measured'):
            if k2 in old:
                H['gws'][str(g)][k2] = old[k2]
        H['gws'][str(g)]['off'] = off
        print('reconstruir: J%d → %d discordâncias (desvio geral %s)' % (g, len(rows), off))
    save_hist(H)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'medir':
        medir()
    elif cmd == 'reconstruir':
        reconstruir()
        medir()
    elif cmd == 'resumo':
        resumo()
    else:
        print(__doc__)
