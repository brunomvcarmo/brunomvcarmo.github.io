"""Liga H2H (457789): todos os confrontos até à última jornada jogada, a tabela calculada depois dela e os
adversários da próxima. Escreve _build/data/h2h.json (lido pelo gen25.py e pelo weekly_app.py).
A tabela oficial da FPL só conta a jornada quando ela fecha (data_checked); por isso é calculada aqui a partir
dos confrontos (3 pontos por vitória, 1 por empate; desempate pelos pontos marcados, como na FPL).
Uso (a partir da raiz): py -X utf8 _build/pool/h2h_week.py"""
import json, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEAGUE = 457789
UA = {'User-Agent': 'Mozilla/5.0 (fpl-app)', 'Accept': 'application/json'}


def get(path, tries=4):
    for k in range(tries):
        try:
            return _get(path)
        except Exception:
            if k == tries - 1: raise
            time.sleep(3 + 3 * k)


def _get(path):
    url = f'https://fantasy.premierleague.com/api/{path}{"&" if "?" in path else "?"}t={int(time.time() * 1000)}'
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


boot = get('bootstrap-static/')
ev = {e['id']: e for e in boot['events']}
# última jornada com os jogos todos acabados (a seguinte pode já ter começado: aí conta como "próxima" com picks reais)
LAST = max(e['id'] for e in boot['events'] if e['finished'])
cur = next((e['id'] for e in boot['events'] if e['is_current']), LAST)
if cur > LAST and all(f['finished_provisional'] for f in get(f'fixtures/?event={cur}')): LAST = cur
NEXT = LAST + 1

matches = {}
for g in range(1, NEXT + 1):
    res, page = [], 1
    while True:
        d = get(f'leagues-h2h-matches/league/{LEAGUE}/?event={g}&page={page}')
        res += d['results']
        if not d.get('has_next'): break
        page += 1
    matches[g] = [dict(a=m['entry_1_entry'], an=m['entry_1_player_name'], at=m['entry_1_name'], ap=m['entry_1_points'],
                       b=m['entry_2_entry'], bn=m['entry_2_player_name'], bt=m['entry_2_name'], bp=m['entry_2_points']) for m in res]
    time.sleep(0.3)

# os pontos H2H das jornadas que ainda não fecharam podem vir a 0: confirmar com o histórico (pontos − hits)
names, hist = {}, {}
for m in matches[LAST]:
    for e, n, t in ((m['a'], m['an'], m['at']), (m['b'], m['bn'], m['bt'])):
        names[e] = (n, t)
LV = json.load(open(ROOT / 'live.json', encoding='utf-8'))   # histórico dos 20 (fpl_fetch.py)
for e in names:
    hist[e] = {r['event']: r['points'] - r['event_transfers_cost'] for r in LV['entries'][str(e)]['history']}
for g in range(1, LAST + 1):
    for m in matches[g]:
        for side in ('a', 'b'):
            real = hist[m[side]].get(g)
            if real is not None and m[side + 'p'] != real:
                print(f'J{g}: {names[m[side]][0]} {m[side + "p"]} → {real} (histórico − hits)')
                m[side + 'p'] = real

tab = {e: dict(entry=e, name=names[e][0], team=names[e][1], w=0, d=0, l=0, pts=0, pf=0) for e in names}
for g in range(1, LAST + 1):
    for m in matches[g]:
        A, B = tab[m['a']], tab[m['b']]
        A['pf'] += m['ap']; B['pf'] += m['bp']
        if m['ap'] > m['bp']: A['w'] += 1; B['l'] += 1; A['pts'] += 3
        elif m['ap'] < m['bp']: B['w'] += 1; A['l'] += 1; B['pts'] += 3
        else: A['d'] += 1; B['d'] += 1; A['pts'] += 1; B['pts'] += 1
table = sorted(tab.values(), key=lambda r: (-r['pts'], -r['pf']))
for i, r in enumerate(table): r['rank'] = i + 1

ME = {'bruno': 5191766, 'marco': 1973102}
def opp(e, g):
    m = next(m for m in matches[g] if e in (m['a'], m['b']))
    return (m['b'], m['bp'], m['ap']) if m['a'] == e else (m['a'], m['ap'], m['bp'])
managers = {}
for k, e in ME.items():
    o, _, _ = opp(e, NEXT)
    managers[k] = dict(pos=tab[e]['rank'], next=names[o][0], nextEntry=o, nextTeam=names[o][1],
                       results=[dict(gw=g, opp=names[opp(e, g)[0]][0], team=names[opp(e, g)[0]][1], mine=opp(e, g)[2], theirs=opp(e, g)[1]) for g in range(1, LAST + 1)],
                       schedule=[dict(gw=g, opp=names[opp(e, g)[0]][0], team=names[opp(e, g)[0]][1]) for g in range(NEXT, NEXT + 1)])
out = dict(last=LAST, next=NEXT, lastFinal=bool(ev[LAST]['finished'] and ev[LAST]['data_checked']), table=table, managers=managers,
           matches={g: matches[g] for g in matches})
json.dump(out, open(ROOT / '_build/data/h2h.json', 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
for r in table: print(r['rank'], r['name'], r['w'], r['d'], r['l'], r['pts'], r['pf'])
for k, v in managers.items(): print(k, 'pos', v['pos'], 'próximo', v['next'], '|', v['results'][-1])
