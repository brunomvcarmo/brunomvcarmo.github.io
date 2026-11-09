from pathlib import Path as _P
_BD = str(_P(__file__).resolve().parents[1]) + '/'   # pasta _build
"""V25 expected-points model: blends three views per player and gameweek.
   F = recent form (V22 formula, last 3 GWs)                      weight 0.25
   U = underlying model (season xG/xA per 90, minutes, team strength from match xG,
       bookmaker odds for the next GW, clean-sheet probability, saves, defcon, bonus)  weight 0.35
   X = published projections from FPL sites (fplform, fplcopilot, onside, pundit)      weight 0.40
   Without X: 0.40 F + 0.60 U.  Then × availability × 'leitura' (own reading, with a reason)."""
import csv, glob, json, math
import ticker26
TK = ticker26.build()
from collections import defaultdict
M = _BD + 'mirror/'; R = _BD + 'research/'

def num(x, d=0.0):
    try: return float(x)
    except: return d

GOAL = {'gk': 6, 'def': 6, 'mid': 5, 'fwd': 4}
CSPTS = {'gk': 4, 'def': 4, 'mid': 1, 'fwd': 0}
DC_TH = {'def': 10, 'mid': 12, 'fwd': 12}
HOME = 1.12

def team_ratings():
    code2id = {r['code']: int(r['id']) for r in csv.DictReader(open(M + 'teams.csv', encoding='utf-8'))}
    gf = defaultdict(float); ga = defaultdict(float); n = defaultdict(int)
    for f in sorted(glob.glob(M + 'matches_gw*.csv')):
        for r in csv.DictReader(open(f, encoding='utf-8')):
            h = code2id.get(str(int(num(r['home_team'])))) if r['home_team'] else None
            a = code2id.get(str(int(num(r['away_team'])))) if r['away_team'] else None
            if not h or not a or r['finished'] != 'True': continue
            hx, ax = num(r['home_expected_goals_xg']), num(r['away_expected_goals_xg'])
            gf[h] += hx; ga[h] += ax; n[h] += 1
            gf[a] += ax; ga[a] += hx; n[a] += 1
    avg = sum(gf.values()) / sum(n.values())
    # shrink towards the average (6 games is a small sample)
    att = {t: ((gf[t] / n[t]) * n[t] + avg * 3) / (n[t] + 3) / avg for t in n}
    dfn = {t: ((ga[t] / n[t]) * n[t] + avg * 3) / (n[t] + 3) / avg for t in n}
    return avg, att, dfn, {t: n[t] for t in n}

TEAMNAME = {r['name']: int(r['id']) for r in csv.DictReader(open(M + 'teams.csv', encoding='utf-8'))}

def poisson_fit_from_odds(m):
    """Team goal expectations (lh, la) matching 1X2 and over 2.5 (grid search, Poisson)."""
    o = m['odds']; ph, pd, pa = 1 / o['home'], 1 / o['draw'], 1 / o['away']; s = ph + pd + pa
    ph, pd, pa = ph / s, pd / s, pa / s
    po = None
    if m.get('over25') and m.get('under25'):
        a, b = 1 / m['over25'], 1 / m['under25']; po = a / (a + b)
    elif m.get('over25'):
        po = min(0.85, 1 / m['over25'] / 1.06)
    best = None
    def pmf(l, k): return math.exp(-l) * l ** k / math.factorial(k)
    for lh10 in range(3, 45):
        for la10 in range(2, 40):
            lh, la = lh10 / 10, la10 / 10
            P = [[pmf(lh, i) * pmf(la, j) for j in range(10)] for i in range(10)]
            h = sum(P[i][j] for i in range(10) for j in range(10) if i > j)
            d = sum(P[i][i] for i in range(10)); a = 1 - h - d
            ov = 1 - sum(P[i][j] for i in range(10) for j in range(10) if i + j <= 2)
            err = (h - ph) ** 2 + (d - pd) ** 2 + (a - pa) ** 2 + ((ov - po) ** 2 if po else 0)
            if best is None or err < best[0]: best = (err, lh, la)
    return best[1], best[2]

def match_lambdas(FIXG, horizon, nextgw):
    avg, att, dfn, n = team_ratings()
    lam = {}  # (gw, team) -> list of (lam_for, lam_against, home, opp)
    odds = json.load(open(R + 'odds.json', encoding='utf-8'))
    odd_l = {}
    for m in odds['matches']:
        h, a = TEAMNAME.get(m['home']), TEAMNAME.get(m['away'])
        if h and a and m.get('odds') and m['odds'].get('home'):
            odd_l[(h, a)] = poisson_fit_from_odds(m)
    for g in horizon:
        for team, fxs in FIXG[g].items():
            out = []
            for f in fxs:
                opp = f['opp']; home = f['home']
                lf = avg * att.get(team, 1) * dfn.get(opp, 1) * (HOME if home else 1 / HOME)
                la = avg * att.get(opp, 1) * dfn.get(team, 1) * (1 / HOME if home else HOME)
                tk = next((x for x in TK.get(g, {}).get(team, []) if x['opp'] == opp), None)
                if tk and tk['xgf'] is not None:  # V26: fixture-ticker projected xG (OddAlerts)
                    lf, la = 0.5 * lf + 0.5 * tk['xgf'], 0.5 * la + 0.5 * tk['xga']
                if g == nextgw:
                    key = (team, opp) if home else (opp, team)
                    if key in odd_l:
                        lh, lA = odd_l[key]
                        of, oa = (lh, lA) if home else (lA, lh)
                        lf, la = 0.5 * of + 0.5 * lf, 0.5 * oa + 0.5 * la  # odds 50%, ticker xG + team ratings 50%
                out.append((lf, la, home, opp))
            lam[(g, team)] = out
    return lam, avg, att

def underlying(p, s, lam_list, team_avg_for, last=6):
    """Points if the player plays, for one gameweek (sum over its fixtures)."""
    r = s.get(last)
    if not r: return 0.0
    mins = num(r['minutes']); starts = num(r['starts'])
    apps = sum(1 for g in range(1, last + 1) if p['mn'][g - 1])
    if mins < 90 or apps == 0: return 0.0
    mpg = mins / apps
    per90 = lambda k: num(r[k]) / mins * 90
    xg90, xa90 = per90('expected_goals'), per90('expected_assists')
    bonus_pa = num(r['bonus']) / apps
    yc_pa = num(r['yellow_cards']) / apps
    share = min(1.0, mpg / 90)
    start_share = min(1.0, starts / apps) if apps else 0
    total = 0.0
    for lf, la, home, opp in lam_list:
        scale = lf / team_avg_for  # this match vs the team's average attack
        pts = 1 + (1 if mpg >= 60 else mpg / 60)
        pts += xg90 * share * scale * GOAL[p['c']]
        pts += xa90 * share * scale * 3
        p60 = start_share * (0.92 if mpg >= 70 else 0.6)
        cs = math.exp(-la)
        pts += cs * CSPTS[p['c']] * p60
        if p['c'] in ('gk', 'def'):
            pts -= (la / 2) * share * 0.85
        if p['c'] == 'gk':
            pts += per90('saves') * share / 3 * (la / 1.35) ** 0.5
        else:
            dc90 = per90('defensive_contribution')
            th = DC_TH[p['c']]
            pdc = max(0.0, min(0.85, (dc90 / th - 0.55) / 0.7))
            pts += 2 * pdc * share
        pts += bonus_pa * (0.8 + 0.4 * scale if p['c'] in ('mid', 'fwd') else 0.8 + 0.4 * cs)
        pts -= yc_pa
        total += pts
    return total

def external(pid, g, X):
    e = X.get(str(pid))
    if not e: return None
    vals = []
    for key in ('fplform', 'fplcopilot', 'onside', 'pundit'):
        v = (e.get(key) or {}).get(str(g))
        if v is not None: vals.append(v)
    return sum(vals) / len(vals) if vals else None

# ---- own reading for the next gameweek (availability / minutes), each with a reason shown in the app ----
# J10 (3 nov 2026): fontes = API oficial (estado, minutos J7-J9), RotoWire (onzes prováveis), FF Scout, The False 9.
READING = {
    'Rayan Cherki': (0.7, 'Está a rodar no City: 0, 45 e 35 minutos nas últimas três jornadas (API oficial).'),
    'Matheus Santos Carneiro da Cunha': (0.85, 'Voltou ao onze aos poucos: 6, 45 e 65 minutos nas últimas três (API oficial).'),
    'Dominic Solanke-Mitchell': (0.85, '25 e 65 minutos nas duas últimas: o Spurs tem rodado o ponta de lança.'),
    'Martin Dubravka': (0.05, '2.º guarda-redes: só joga se o titular falhar.'),
}
READ_KIND = {'Martin Dubravka': 'role', 'Rayan Cherki': 'role'}
# ---- V27 (15 out): descanso depois de jogos a meio da semana (Europa e Taça da Liga), para todas as jornadas ----
# Substitui o antigo EURO_THU (só Palace/Sunderland/Bournemouth na J7). Fator por jogo da PL, conforme as horas
# desde o jogo a meio da semana anterior da equipa: Europa <72 h ×0.95, 72-96 h ×0.98; Taça da Liga metade do
# efeito (as equipas rodam mais na taça). Só para titulares habituais (≥180 min nas últimas 3); guarda-redes metade.
# Quem tem leitura própria que já conta com o jogo europeu (REST_EXEMPT) fica de fora nessa jornada.
MIDWEEK = json.load(open(R + 'midweek.json', encoding='utf-8'))['rows']
PLKO = json.load(open(_BD + 'data/fixtures.json', encoding='utf-8'))
REST_EXEMPT = set()
COMP_PT = {'UCL': 'Liga dos Campeões', 'UEL': 'Liga Europa', 'UECL': 'Liga Conferência', 'EFL': 'Taça da Liga'}
from datetime import datetime
def _t(s): return datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
def rest_info(team, g):
    """(fator, horas, competição) para a jornada g da equipa; fator 1 sem jogo a meio da semana."""
    pl = sorted(f['kickoff'] for f in PLKO.get(str(g), []) if team in (f['h'], f['a']))
    if not pl: return 1.0, None, None
    k = pl[0]
    prev_pl = max([f['kickoff'] for gg, l in PLKO.items() for f in l if team in (f['h'], f['a']) and f['kickoff'] < k] or ['1900-01-01T00:00:00Z'])
    mw = [r for r in MIDWEEK if r[0] == team and prev_pl < r[3] < k]
    if not mw: return 1.0, None, None
    r = max(mw, key=lambda x: x[3]); hours = (_t(k) - _t(r[3])).total_seconds() / 3600
    f = 0.95 if hours < 72 else (0.98 if hours < 96 else 1.0)
    if r[1] == 'EFL': f = 1 - (1 - f) / 2
    return f, hours, r[1]
def rest_factor(p, g):
    f, hours, comp = rest_info(p['t'], g)
    if f >= 1 or p['m3'] < 180: return 1.0, ''
    if p['c'] == 'gk': f = 1 - (1 - f) / 2
    f = round(f, 3)
    return f, 'Descanso: %s dias depois de jogar na %s (×%.2f).' % (('%.1f' % (hours / 24)).replace('.', ','), COMP_PT[comp], f)

def apply(pool, snap, FIXG, horizon, nextgw, avail_fn, last=6):
    X = json.load(open(R + 'proj-numeric.json', encoding='utf-8'))['players']
    lam, avg, att = match_lambdas(FIXG, horizon, nextgw)
    for p in pool:
        s = snap[p['id']]
        team_avg_for = avg * att.get(p['t'], 1)
        F, U, Xs, A, RR, E, BL = [], [], [], [], [], [], []
        raw = p.pop('_raw')
        for gi, g in enumerate(horizon):
            ll = lam.get((g, p['t']), [])
            tks = TK.get(g, {}).get(p['t'], [])
            if tks:  # V26: difficulty from the fixture tickers, attack or defence side by position
                pick = (lambda x: x['dfn']) if p['c'] in ('gk', 'def') else ((lambda x: x['att']) if p['c'] == 'fwd' else (lambda x: (x['att'] + x['dfn']) / 2))
                mult = sum(ticker26.mult(pick(x)) for x in tks)
            else:
                mult = sum({1: 1.30, 2: 1.15, 3: 1.00, 4: 0.85, 5: 0.70}[f['diff']] for f in FIXG[g].get(p['t'], []))
            f_ = raw * mult
            u_ = underlying(p, s, ll, team_avg_for, last) if ll else 0.0
            x_ = external(p['id'], g, X) if ll else None
            a_ = avail_fn(p, g)
            r_ = 1.0; note = ''
            if g == nextgw:
                if p['n'] in READING: r_, note = READING[p['n']]
            kind = READ_KIND.get(p['n'], 'gw')
            if g > nextgw and p['n'] in READING:
                k = g - nextgw
                if kind == 'role': r_ = READING[p['n']][0]
                elif kind == 'inj': a_ = min(a_, 0.6 if k == 1 else 0.9)
                elif kind == 'long': a_ = min(a_, 0.2 if k == 1 else (0.5 if k == 2 else 0.8))
            if not (g == nextgw and p['n'] in REST_EXEMPT):
                rf, rnote = rest_factor(p, g)
                if rf < 1:
                    r_ = r_ * rf
                    if g == nextgw: note = (note + ' ' + rnote).strip()
            blend = (0.25 * f_ + 0.35 * u_ + 0.40 * x_) if x_ is not None else (0.40 * f_ + 0.60 * u_)
            v = blend * a_ * r_
            BL.append(blend)
            if ll and a_ * r_ > 0 and (p['m3'] > 0) : v = max(v, 0.3)
            F.append(round(f_, 1)); U.append(round(u_, 1)); Xs.append(None if x_ is None else round(x_, 1))
            A.append(round(a_, 2)); RR.append(r_); E.append(round(v, 1))
            if g == nextgw: p['rd'] = note
        p['ep'] = E
        # V59: partes de cada jornada para o discorda.py (só a parte "nossa" = 0.40 F + 0.60 U, sem os sites)
        p['_cmp'] = dict(F=F, U=U, X=Xs, bl=BL)
        p['k'] = [F[0], U[0], Xs[0], round(A[0] * RR[0], 2)]  # components for the next gameweek
    return lam
