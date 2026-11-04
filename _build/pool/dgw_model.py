"""Detetor de jornadas duplas e brancas da 2.ª metade (J20-J38) — V54, 20 out 2026.

Como funciona:
1. Oficial: calendário da FPL (live.json 'fixtures' ou API). Equipa sem jogo numa jornada = branca oficial; com 2 = dupla
   oficial; jogo com jornada vazia = adiado sem data nova.
2. Brancas previstas: uma ronda de taça ao fim de semana que coincide com uma jornada (research/cups.json: final da Taça
   da Liga a 21 mar → J30; meias da FA Cup a 24-25 abr → J33). O jogo da liga de uma equipa que lá esteja é adiado — e o
   do adversário também. P(branca) = P(a equipa OU o adversário chegar a essa ronda) × fator de adiamento.
3. Quem chega a cada ronda: simulação Monte Carlo das taças (20 000 vezes) com a força Elo das equipas (espelho
   FPL-Elo-Insights; adversários de fora da PL com um Elo médio por divisão). Eliminatória: P(passar) = 1/(1+10^(-d/400)),
   com ±60 de fator casa; 2 mãos = d × 1,3. Europa: igual, contra um adversário médio de cada competição.
4. Duplas previstas: o jogo adiado é remarcado numa semana livre a meio (terça/quarta sem jornada a meio da semana, sem
   pausa de seleções), depois da jornada branca (é o que a liga costuma fazer). Peso de cada semana = 0,6^ordem ×
   P(as duas equipas estarem livres nessa semana, sem Europa nem taça). A semana cai na jornada cujo prazo a antecede.
Saída: const DGW_DATA no bloco de dados (o gen25.py chama build()).
Uso isolado (a partir da raiz): py -X utf8 _build/pool/dgw_model.py   (imprime o resumo)"""
import csv, json, random, time, urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / '_build'
GWS = list(range(20, 39))
N_SIM = 20000


def _get(path):
    url = f'https://fantasy.premierleague.com/api/{path}{"&" if "?" in path else "?"}t={int(time.time() * 1000)}'
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (fpl-app)'}), timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))


def load_fixtures():
    """[(id, jornada, casa, fora, início)] do live.json (escrito pelo fpl_fetch.py) ou, se não tiver, da API."""
    lv = json.load(open(ROOT / 'live.json', encoding='utf-8'))
    if lv.get('fixtures'):
        fx = [tuple(f[:5]) for f in lv['fixtures']]
    else:
        fx = [(f['id'], f['event'], f['team_h'], f['team_a'], f['kickoff_time']) for f in _get('fixtures/')]
    deadlines = {e['id']: e['deadline'] for e in lv['events']}
    return fx, deadlines


def elo_table():
    code2id = {r['code']: int(r['id']) for r in csv.DictReader(open(B / 'mirror/teams.csv', encoding='utf-8'))}
    elo = {}
    for g in range(1, 39):
        p = B / f'mirror/matches_gw{g}.csv'
        if not p.exists(): continue
        for r in csv.DictReader(open(p, encoding='utf-8')):
            if 'prem' not in r['match_id']: continue
            for side in ('home', 'away'):
                if r[f'{side}_team'] and r[f'{side}_team_elo']:
                    elo[code2id[str(int(float(r[f'{side}_team'])))]] = float(r[f'{side}_team_elo'])
    avg = sum(elo.values()) / len(elo)
    for t in range(1, 21): elo.setdefault(t, avg)
    return elo


def p_adv(ea, eb, home=0.0, legs=1):
    d = (ea - eb + home) * (1.3 if legs == 2 else 1.0)
    return 1 / (1 + 10 ** (-d / 400))


def d_(s): return date.fromisoformat(s[:10])


def simulate(cups, elo):
    """P(cada equipa da PL jogar cada ronda) — {comp: {r: {team: p}}}."""
    other = cups['elo_other']; C = cups['competitions']
    rnd = random.Random(54)
    hits = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    fa, efl = C['facup'], C['eflcup']
    for _ in range(N_SIM):
        # ---- FA Cup desde a 3.ª eliminatória: 64 equipas, sorteio aleatório a cada ronda ----
        field = [(t, elo[t]) for t in fa['pl_in']]
        for div, n in fa['field_r3'].items():
            field += [(None, other[div] + rnd.gauss(0, 40)) for _ in range(n)]
        for k, R in enumerate(fa['rounds']):
            for t, _e in field:
                if t: hits['facup'][R['r']][t] += 1
            if len(field) == 1: break
            rnd.shuffle(field); nxt = []
            for i in range(0, len(field) - 1, 2):
                (ta, ea), (tb, eb) = field[i], field[i + 1]
                neutral = R['r'] in ('SF', 'F')
                h = 0 if neutral else (60 if rnd.random() < 0.5 else -60)
                nxt.append(field[i] if rnd.random() < p_adv(ea, eb, h) else field[i + 1])
            field = nxt
        # ---- Taça da Liga: a última ronda já sorteada (efl['ties'], ex. 'QF'), depois sorteio aleatório ----
        val = lambda x: (x, elo[x]) if isinstance(x, int) else (None, other[efl['others'][x]])
        r0 = list(efl['ties'])[-1]; k0 = [R['r'] for R in efl['rounds']].index(r0)
        ties = [(val(a), val(b)) for a, b in efl['ties'][r0]]
        for t in efl['pl_in']: hits['eflcup'][r0][t] += 1
        two = efl['rounds'][k0].get('two_legs')
        field = [a if rnd.random() < p_adv(a[1], b[1], 0 if two else 60, 2 if two else 1) else b for a, b in ties]
        for R in efl['rounds'][k0 + 1:]:
            for t, _e in field:
                if t: hits['eflcup'][R['r']][t] += 1
            if len(field) == 1: break
            rnd.shuffle(field); nxt = []
            for i in range(0, len(field) - 1, 2):
                (ta, ea), (tb, eb) = field[i], field[i + 1]
                legs = 2 if R.get('two_legs') else 1
                h = 0 if (R['r'] == 'F' or legs == 2) else (60 if rnd.random() < 0.5 else -60)
                nxt.append(field[i] if rnd.random() < p_adv(ea, eb, h, legs) else field[i + 1])
            field = nxt
        # ---- Europa: cada clube da PL contra um adversário médio da competição, ronda a ronda ----
        for comp in ('ucl', 'uel', 'uecl'):
            E = C[comp]; oe = other[E['elo_key']]
            for t in E['pl_in']:
                alive = rnd.random() < E['rounds'][0].get('p_from_league', 1.0)
                for R in E['rounds']:
                    if not alive: break
                    hits[comp][R['r']][t] += 1
                    alive = rnd.random() < p_adv(elo[t], oe + rnd.gauss(0, 60), 0, 2 if R['r'] != 'F' else 1)
    return {c: {r: {t: n / N_SIM for t, n in d.items()} for r, d in rs.items()} for c, rs in hits.items()}


def build(verbose=False):
    cups = json.load(open(B / 'research/cups.json', encoding='utf-8'))
    C = cups['competitions']
    fx, deadlines = load_fixtures()
    elo = elo_table()
    P = simulate(cups, elo)
    dl = {g: datetime.fromisoformat(deadlines[g].replace('Z', '+00:00')).date() for g in deadlines}

    def gw_of(day):   # jornada cujo prazo antecede o dia
        g = max([g for g in dl if dl[g] <= day] or [min(dl)])
        return g

    # ---- oficial ----
    cnt = {t: {g: 0 for g in GWS} for t in range(1, 21)}
    postponed = []
    for fid, ev, h, a, ko in fx:
        if ev is None:
            postponed.append(dict(id=fid, h=h, a=a)); continue
        if ev in GWS:
            cnt[h][ev] += 1; cnt[a][ev] += 1
    ob = {t: [1 if cnt[t][g] == 0 else 0 for g in GWS] for t in cnt}
    od = {t: [1 if cnt[t][g] >= 2 else 0 for g in GWS] for t in cnt}

    # ---- dias com jornada (para saber que fins de semana e semanas a meio estão ocupados) ----
    gw_days = defaultdict(set)
    for fid, ev, h, a, ko in fx:
        if ev and ko: gw_days[ev].add(d_(ko))
    busy_mid = set()   # semanas (segunda) com jornada a meio da semana
    for g, days in gw_days.items():
        for x in days:
            if x.weekday() in (1, 2, 3): busy_mid.add(x - timedelta(days=x.weekday()))
    breaks = [(d_(a), d_(b)) for a, b in cups.get('international_breaks', [])]

    # ---- semanas livres a meio (terça), de jan ao fim da época ----
    first = date(2027, 1, 5); last = date(2027, 5, 25)
    slots = []
    x = first - timedelta(days=first.weekday()) + timedelta(days=1)
    while x <= last:
        mon = x - timedelta(days=1)
        if mon not in busy_mid and not any(a <= x <= b for a, b in breaks):
            slots.append(x)
        x += timedelta(days=7)

    def p_busy(team, day):
        """P(a equipa ter um jogo europeu ou de taça na semana desse dia)."""
        mon = day - timedelta(days=day.weekday()); free = 1.0
        for comp, E in C.items():
            if E.get('kind') != 'midweek': continue
            for R in E['rounds']:
                for ds in R['dates']:
                    dd = d_(ds)
                    if mon <= dd <= mon + timedelta(days=6) and dd.weekday() < 5:
                        free *= 1 - P.get(comp, {}).get(R['r'], {}).get(team, 0)
        return 1 - free

    # ---- brancas e duplas previstas ----
    pb = {t: [0.0] * len(GWS) for t in range(1, 21)}
    pd = {t: [0.0] * len(GWS) for t in range(1, 21)}
    events = []
    for comp in ('facup', 'eflcup'):
        E = C[comp]
        for k, R in enumerate(E['rounds']):
            f = R.get('postpone', 1.0 if E['kind'] == 'weekend' else 0.0)
            if not f: continue
            days = [d_(x) for x in R['dates']]
            clash = [g for g in GWS if any(abs((d - x).days) <= 1 for d in gw_days.get(g, ()) for x in days)]
            if not clash: continue
            g = clash[0]; gi = GWS.index(g)
            pr = P.get(comp, {}).get(R['r'], {})
            known = d_(E['rounds'][k - 1]['dates'][-1]) + timedelta(days=2) if k else first   # quando se sabe quem lá vai
            ev = dict(comp=comp, name=E['name'], round=R['name'], date=R['dates'][0], gw=g, teams={}, fixtures=[])
            for fid, fe, h, a, ko in fx:
                if fe != g: continue
                ph, pa = pr.get(h, 0), pr.get(a, 0)
                p = f * (1 - (1 - ph) * (1 - pa))
                if p < 0.005: continue
                ev['fixtures'].append(dict(h=h, a=a, p=round(p, 3)))
                for t in (h, a):
                    pb[t][gi] = 1 - (1 - pb[t][gi]) * (1 - p)
                # remarcação: semanas livres depois de se saber quem vai à ronda, fora da própria jornada
                cand = [s for s in slots if s > max(days) and s >= known and gw_of(s) != g and gw_of(s) in GWS]
                w = [(0.6 ** i) * (1 - p_busy(h, s)) * (1 - p_busy(a, s)) for i, s in enumerate(cand)]
                tot = sum(w)
                if not tot: continue
                for s, wi in zip(cand, w):
                    gj = GWS.index(gw_of(s))
                    for t in (h, a):
                        pd[t][gj] = min(1.0, pd[t][gj] + p * wi / tot)
            ev['teams'] = {t: round(v, 3) for t, v in pr.items() if v >= 0.01}
            events.append(ev)
    # o oficial manda
    for t in range(1, 21):
        for i in range(len(GWS)):
            if ob[t][i]: pb[t][i] = 1.0
            if od[t][i]: pd[t][i] = 1.0
    reach = {comp: {r: {t: round(v, 3) for t, v in d.items() if v >= 0.005} for r, d in rs.items()} for comp, rs in P.items()}
    out = dict(updated=cups['updated'], gws=GWS,
               b={t: [round(v, 3) for v in pb[t]] for t in pb}, d={t: [round(v, 3) for v in pd[t]] for t in pd},
               ob=ob, od=od, postponed=postponed, events=events,
               slots=[dict(date=s.isoformat(), gw=gw_of(s)) for s in slots if gw_of(s) in GWS],
               reach=reach, comps={c: dict(name=E['name'], rounds=[dict(r=R['r'], name=R['name'], dates=R['dates']) for R in E['rounds']]) for c, E in C.items()},
               notes=cups.get('notes', []))
    if verbose:
        T = {r['id']: r['short_name'] for r in csv.DictReader(open(B / 'mirror/teams.csv', encoding='utf-8'))}
        for ev in events:
            print(f"{ev['name']} — {ev['round']} ({ev['date']}) → J{ev['gw']}: " + ', '.join(f"{T[str(t)]} {p:.0%}" for t, p in sorted(ev['teams'].items(), key=lambda x: -x[1])[:8]))
        for i, g in enumerate(GWS):
            bl = sum(pb[t][i] for t in pb); db = sum(pd[t][i] for t in pd)
            if bl > 0.05 or db > 0.05:
                print(f'J{g}: brancas esperadas {bl:.1f} equipas, duplas {db:.1f} | ' +
                      ' '.join(f"{T[str(t)]}{'B' if pb[t][i] >= 0.3 else ''}{'D' if pd[t][i] >= 0.3 else ''}{max(pb[t][i], pd[t][i]):.0%}" for t in range(1, 21) if max(pb[t][i], pd[t][i]) >= 0.2))
        print('semanas livres:', [(s['date'], s['gw']) for s in out['slots']])
    return out


if __name__ == '__main__':
    build(verbose=True)
