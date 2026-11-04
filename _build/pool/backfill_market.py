from pathlib import Path as _P
_BD = str(_P(__file__).resolve().parents[1]) + '/'   # pasta _build
"""Preenche o mercado e o retrato dos jogadores (players[g]: estado, chance, posse, ep_next antes do deadline g) (mais comprados e vendidos) das jornadas passadas em rivals.json a partir do espelho da API:
o retrato do fim da jornada g-1 (playerstats.csv, gw = g-1) tem as transferências feitas para a jornada g.
A API só dá o mercado da semana atual; a GitHub Action guarda-o daqui para a frente e não apaga estas jornadas.
Uso (a partir da raiz do repositório): py _build/pool/backfill_market.py rivals.json"""
import csv, json, sys
from collections import defaultdict
path = sys.argv[1]
R = json.load(open(path, encoding='utf-8'))
snap = defaultdict(list); full = defaultdict(dict)
code2id = {r['code']: int(r['id']) for r in csv.DictReader(open(_BD + 'mirror/teams.csv', encoding='utf-8'))}
pinfo = {r['player_id']: r for r in csv.DictReader(open(_BD + 'mirror/players.csv', encoding='utf-8'))}
POSN = {'Goalkeeper': 1, 'Defender': 2, 'Midfielder': 3, 'Forward': 4}
for r in csv.DictReader(open(_BD + 'mirror/playerstats.csv', encoding='utf-8')):
    snap[int(r['gw'])].append((int(r['id']), int(float(r['transfers_in_event'] or 0)), int(float(r['transfers_out_event'] or 0))))
    pi = pinfo.get(r['id'])
    full[int(r['gw'])][r['id']] = [r['status'], int(float(r['chance_of_playing_next_round'])) if r['chance_of_playing_next_round'] not in ('', None) else None,
                                   float(r['selected_by_percent'] or 0), float(r['ep_next'] or 0), float(r['now_cost'] or 0),
                                   code2id.get(pi['team_code']) if pi else None, POSN.get(pi['position']) if pi else None,
                                   float(r['form'] or 0), round(float(r['now_cost'] or 0) - float(r['cost_change_start'] or 0) / 10, 1)]
added = []
for g in range(2, int(R['next_event']) + 1):
    if str(g) in R['market'] or (g - 1) not in snap:
        continue
    rows = snap[g - 1]
    R['market'][str(g)] = {'at': None, 'src': 'espelho', 'in': [[i, a] for i, a, _ in sorted(rows, key=lambda x: -x[1])[:40]],
                           'out': [[i, b] for i, _, b in sorted(rows, key=lambda x: -x[2])[:40]]}
    added.append(g)
R['market'] = dict(sorted(R['market'].items(), key=lambda kv: int(kv[0])))
# retrato dos jogadores: os que andam nos plantéis da liga ou no mercado dessa jornada
R.setdefault('players', {})
ids = {str(p) for v in R['entries'].values() for gw in v['gws'].values() for p in gw['s'] + gw['b']}
padded = []
for g in range(2, int(R['next_event']) + 1):
    old = R['players'].get(str(g))
    if (old and len(next(iter(old.values()))) >= 9 and R['market'].get(str(g), {}).get('src') == 'api') or (g - 1) not in full:
        continue   # retrato já completo vindo da API (a Action) — não substituir
    keep = ids | {str(i) for side in ('in', 'out') for i, _ in R['market'].get(str(g), {}).get(side, [])}
    for t in (1, 2, 3, 4):
        keep |= {i for i, v in sorted(((i, v) for i, v in full[g - 1].items() if v[6] == t), key=lambda kv: -kv[1][3])[:15]}
    R['players'][str(g)] = {i: full[g - 1][i] for i in sorted(keep, key=int) if i in full[g - 1]}
    padded.append(g)
R['players'] = dict(sorted(R['players'].items(), key=lambda kv: int(kv[0])))
# dificuldade oficial dos jogos de cada jornada (da API fixtures/, guardada em _build/pool/fixtures_api.json)
FX = json.load(open(_BD + 'pool/fixtures_api.json', encoding='utf-8'))
R.setdefault('fdr', {})
for g in range(2, max(int(R['next_event']), 19) + 1):
    if str(g) in R['fdr'] and g < int(R['next_event']):
        continue
    d = {}
    for f in FX:
        if f.get('event') == g:
            d.setdefault(str(f['team_h']), []).append(f['team_h_difficulty']); d.setdefault(str(f['team_a']), []).append(f['team_a_difficulty'])
    R['fdr'][str(g)] = d
R['fdr'] = dict(sorted(R['fdr'].items(), key=lambda kv: int(kv[0])))
sys.path.insert(0, str(_P(__file__).resolve().parents[2] / 'scripts'))
import rivals_profile
R['profiles'] = rivals_profile.build(R)
import rivals_predict
R['predictions'] = {str(R['next_event']): rivals_predict.predict_all(R, int(R['next_event']))}
if not R.get('deadlines'):
    LV = json.load(open(_BD + '../live.json', encoding='utf-8'))
    R['deadlines'] = {str(ev['id']): ev['deadline'] for ev in LV['events']}
import rivals_chips
R['chips_radar'] = {str(R['next_event']): rivals_chips.radar_all(R, int(R['next_event']))}
print('retrato dos jogadores acrescentado:', padded)
json.dump(R, open(path, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print('mercado acrescentado:', added, '| jornadas no ficheiro:', list(R['market']))
