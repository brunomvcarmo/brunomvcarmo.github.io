from pathlib import Path as _P
_ROOT = _P(__file__).resolve().parents[2]
"""Aplica à app (index.html) os plantéis reais de uma jornada que já passou o deadline, sem esperar pela
atualização semanal completa. Usar depois do deadline, a seguir a `py -X utf8 scripts/fpl_fetch.py` (que escreve
live.json e rivals.json com os picks da jornada atual).

Atualiza: SQUAD_STATE do Bruno e do Marco (plantel, preço de compra das entradas novas, preço de venda, banco),
LEAGUE_SQUADS dos 20 (onze, banco, capitão, vice, chips, banco £, valor), a posse na liga de cada jogador (POOL24 lo),
GW_META.squadsGw e, no PRED_LOG da jornada, os onzes reais do Bruno e do Marco com os pontos esperados de antes do
deadline (para "Previsões vs real"). Não mexe em pontos nem em pontos esperados.
Uso (a partir da raiz): py -X utf8 _build/pool/apply_picks.py"""
import json, math, re

H = _ROOT / 'index.html'
s = H.read_text(encoding='utf-8')
LV = json.load(open(_ROOT / 'live.json', encoding='utf-8'))
RV = json.load(open(_ROOT / 'rivals.json', encoding='utf-8'))
G = LV['picks_event']


def grab(name, pat=r'(\{.*?\})'):
    m = re.search(r'const %s = %s;\n' % (name, pat), s)
    assert m, name
    return m, json.loads(m.group(1))


def put(m, name, obj):
    global s
    s = s[:m.start()] + f'const {name} = {json.dumps(obj, ensure_ascii=False, separators=(",", ":"))};\n' + s[m.end():]


# ---------- POOL24: nomes, preços e posse na liga ----------
i0 = s.index('const POOL24 = [\n') + len('const POOL24 = [\n')
i1 = s.index('\n]', i0)   # o array acaba em "\n].map(...)"
rows = [json.loads(l.rstrip(',')) for l in s[i0:i1].split('\n')]
byid = {r[0]: r for r in rows}
name = lambda i: byid[i][1] if i in byid else str(i)
price = lambda i: (LV['elements'].get(str(i)) or [None])[0] / 10 if str(i) in LV['elements'] else byid[i][4]
gm, GW = grab('GW_META')
assert GW['next'] == G, f'GW_META.next ({GW["next"]}) não é a jornada dos picks ({G})'

# ---------- LEAGUE_SQUADS ----------
lm, LS = grab('LEAGUE_SQUADS')
own = {}
for e, x in LV['entries'].items():
    p = x.get('picks')
    if not p or p['event'] != G or e not in LS:
        continue
    L = LS[e]
    h = next((r for r in x['history'] if r['event'] == G), None)
    L['s'], L['b'] = p['starters'], p['bench']
    L['c'], L['vc'] = name(p['captain']), name(p['vice'])
    L[f'chip{G}'] = p.get('active_chip')
    if h:
        L['bank'], L['val'] = h['bank'] / 10, h['value'] / 10
    L['chips'] = [[c['name'], c['event']] for c in x.get('chips', [])]
    for i in p['starters'] + p['bench']:
        own[i] = own.get(i, 0) + 1
put(lm, 'LEAGUE_SQUADS', LS)
n = len(LS)
# posse na liga (coluna lo do POOL24)
for r in rows:
    r[10] = round(100 * own.get(r[0], 0) / n)
s = s[:i0] + ',\n'.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) for r in rows) + s[i1:]

# ---------- SQUAD_STATE (Bruno e Marco) ----------
sm, ST = grab('SQUAD_STATE')
for mgr, e in (('bruno', '5191766'), ('marco', '1973102')):
    x, rv = LV['entries'][e], RV['entries'][e]
    p = x['picks']
    if p['event'] != G:
        continue
    old = {q['id']: q for q in ST[mgr]['players']}
    buys = {}
    for t in rv['transfers']:
        if t[0] <= G and t[3]:
            buys[t[1]] = t[3] / 10
    pl = []
    for i in p['starters'] + p['bench']:
        if i in old and not (i in buys and any(t[0] == G and t[1] == i for t in rv['transfers'])):
            q = dict(old[i])
        else:
            q = {'id': i, 'buy': round(buys.get(i, price(i)), 1), 'since': G}
        now = price(i)
        q['sell'] = now if now <= q['buy'] else round(q['buy'] + math.floor(round((now - q['buy']) * 10) / 2) / 10, 1)
        pl.append(q)
    h = next((r for r in x['history'] if r['event'] == G), None)
    ST[mgr]['players'] = pl
    if h:
        ST[mgr]['bank'] = h['bank'] / 10
put(sm, 'SQUAD_STATE', ST)

# ---------- PRED_LOG: onze real com os pontos esperados de antes do deadline ----------
pm, PL = grab('PRED_LOG', r'(\[.*?\])')
entry = next((x for x in PL if x['gw'] == G), None)
if entry:
    for mgr, e in (('bruno', '5191766'), ('marco', '1973102')):
        p = LV['entries'][e]['picks']
        if p['event'] != G:
            continue
        entry['teams'][mgr] = [dict(n=name(i), ep=byid[i][23][0] if i in byid else 0, xi=i in p['starters'], c=i == p['captain'], real=None)
                               for i in p['starters'] + p['bench']]
    entry['note'] = f'onzes reais da J{G} (depois do deadline), pontos esperados de antes do deadline'
    put(pm, 'PRED_LOG', PL)

# ---------- GW_META ----------
gm, GW = grab('GW_META')
GW['squadsGw'] = G
# transferências grátis para a jornada seguinte (regra da FPL: +1 por jornada, até 5; Wildcard/Free Hit não gastam)
ftn = {}
for mgr, e in (('bruno', '5191766'), ('marco', '1973102')):
    x = LV['entries'][e]; p = x['picks']; h = next((r for r in x['history'] if r['event'] == G), None)
    ft = ST[mgr]['ft']
    if p.get('active_chip') in ('wildcard', 'freehit'):
        ftn[mgr] = min(5, ft + 1)
    else:
        ftn[mgr] = min(5, max(0, ft - (h['event_transfers'] if h else 0)) + 1)
GW['ftNext'] = ftn
put(gm, 'GW_META', GW)
H.write_text(s, encoding='utf-8', newline='\n')
print(f'J{G}: {len(own)} jogadores nos plantéis da liga · Bruno {len(ST["bruno"]["players"])} (banco £{ST["bruno"]["bank"]}M) · Marco {len(ST["marco"]["players"])} (banco £{ST["marco"]["bank"]}M)')
