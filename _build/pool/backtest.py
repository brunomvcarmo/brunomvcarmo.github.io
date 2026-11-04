from pathlib import Path as _P
_BD = str(_P(__file__).resolve().parents[1]) + '/'   # pasta _build
"""Backtest do modelo de pontos esperados nas J2-J6 (16 out 2026).

Para prever a jornada g usa só o que se sabia no fim da jornada g-1: o retrato da API no espelho (playerstats.csv,
campo gw = g-1: pontos, minutos, xG/xA, estado e chance de jogar, preço) e os jogos até g-1 (força das equipas pelo xG).
A dificuldade de cada jogo é a oficial da FPL (API fixtures/), a única que existe para o passado.
Referência: ep_next oficial da FPL no mesmo retrato (é a previsão da FPL para a jornada g).
Pontos reais: event_points do retrato da jornada g (validados contra event/6/live/ da API oficial para a J6).

Modelo (o mesmo de gen25/model25, sem o que não existe para o passado: sites, odds, tickers, leitura própria):
  F = (0.55 × média pts últimas 3 + 0.45 × base da posição × fração de minutos) × Σ DIFF_MULT[dificuldade]^β
  U = model25.underlying (xG/xA por 90, minutos, golos esperados do jogo pela força das equipas, CS, defesas, defcon, bónus)
  ep = (w·F + (1−w)·U) × disponibilidade × fração_minutos^γ × s
Antes: w = 0.40, β = 1, γ = 0, s = 1 (a fórmula atual quando não há projeções dos sites).
Afinação por posição (w, β, γ, s) nas J2-J5 a minimizar o erro quadrático médio (OBJ=mse, o certo para uma média;
OBJ=mae dá a mediana, que fica ~0,8 pts abaixo do real); a J6 fica só para confirmar.
Uso: py _build/pool/backtest.py   (escreve _build/pool/backtest_result_mse.json)"""
import csv, glob, json, math, os, sys, time, urllib.request
from collections import defaultdict
sys.path.insert(0, _BD + 'pool')
import model25

M = _BD + 'mirror/'
num = model25.num
POSMAP = {'Goalkeeper': 'gk', 'Defender': 'def', 'Midfielder': 'mid', 'Forward': 'fwd'}
DIFF_MULT = {1: 1.30, 2: 1.15, 3: 1.00, 4: 0.85, 5: 0.70}
BASE = {'gk': 3.2, 'def': 3.0, 'mid': 3.4, 'fwd': 3.6}
OBJ = os.environ.get('OBJ', 'mse')
TARGETS = [2, 3, 4, 5, 6]; TUNE = [2, 3, 4, 5]; CONFIRM = [6]
OLD = dict(w=0.40, b=1.0, g=0.0, s=1.0)

# ---------- dados ----------
snap = defaultdict(dict)
for r in csv.DictReader(open(M + 'playerstats.csv', encoding='utf-8')):
    snap[int(r['id'])][int(r['gw'])] = r
code2id = {r['code']: int(r['id']) for r in csv.DictReader(open(M + 'teams.csv', encoding='utf-8'))}
pinfo = {int(r['player_id']): r for r in csv.DictReader(open(M + 'players.csv', encoding='utf-8'))}

FXF = _BD + 'pool/fixtures_api.json'
if not os.path.exists(FXF):
    req = urllib.request.Request(f'https://fantasy.premierleague.com/api/fixtures/?t={int(time.time())}', headers={'User-Agent': 'Mozilla/5.0'})
    json.dump(json.load(urllib.request.urlopen(req, timeout=30)), open(FXF, 'w', encoding='utf-8', newline='\n'))
FIX = json.load(open(FXF, encoding='utf-8'))

def fixtures_of(g):
    out = defaultdict(list)
    for f in FIX:
        if f.get('event') != g: continue
        out[f['team_h']].append(dict(opp=f['team_a'], home=True, diff=f['team_h_difficulty']))
        out[f['team_a']].append(dict(opp=f['team_h'], home=False, diff=f['team_a_difficulty']))
    return out

def ratings(upto):
    """Força das equipas pelo xG dos jogos das jornadas 1..upto (como model25.team_ratings, com corte)."""
    gf = defaultdict(float); ga = defaultdict(float); n = defaultdict(int)
    for g in range(1, upto + 1):
        f = M + f'matches_gw{g}.csv'
        if not os.path.exists(f): continue
        for r in csv.DictReader(open(f, encoding='utf-8')):
            if r['finished'] != 'True' or not r['home_team'] or not r['away_team']: continue
            h = code2id.get(str(int(num(r['home_team'])))); a = code2id.get(str(int(num(r['away_team']))))
            if not h or not a: continue
            hx, ax = num(r['home_expected_goals_xg']), num(r['away_expected_goals_xg'])
            gf[h] += hx; ga[h] += ax; n[h] += 1; gf[a] += ax; ga[a] += hx; n[a] += 1
    avg = sum(gf.values()) / sum(n.values())
    att = {t: (gf[t] + avg * 3) / (n[t] + 3) / avg for t in n}
    dfn = {t: (ga[t] + avg * 3) / (n[t] + 3) / avg for t in n}
    return avg, att, dfn

def avail(st, ch):
    ch = None if ch in ('', None) else num(ch)
    if st == 'a': return 1.0
    if st == 'd': return ch / 100 if ch is not None else 0.75
    if st == 'i': return ch / 100 if ch is not None else 0.0
    return 0.0   # s, u, n

# ---------- componentes por jogador e jornada ----------
rows = []   # um por jogador × jornada alvo
for g in TARGETS:
    c = g - 1
    fx = fixtures_of(g)
    avg, att, dfn = ratings(c)
    for pid, s in snap.items():
        r_c, r_g = s.get(c), s.get(g)
        info = pinfo.get(pid)
        if not r_c or not r_g or not info: continue
        cls = POSMAP.get(info['position']); team = code2id.get(info['team_code'])
        if not cls or not team: continue
        pts, mins, pm = {}, {}, 0.0
        for k in range(1, c + 1):
            rk = s.get(k)
            if not rk: continue
            m = num(rk['minutes']); pts[k] = int(num(rk['event_points'])); mins[k] = m - pm; pm = m
        if mins.get(c, 0) <= 0: continue          # população: jogou na jornada anterior
        rec = [(pts[k], mins[k]) for k in range(max(1, c - 2), c + 1) if k in pts]
        a_ = sum(p for p, _ in rec) / len(rec); share = sum(min(m, 90) for _, m in rec) / (90 * len(rec))
        price = num(r_c['now_cost'])
        base = BASE[cls] + (max(0, price - 6.5) * 0.4 if cls in ('mid', 'fwd') else 0)
        raw = 0.55 * a_ + 0.45 * base * share
        F = fx.get(team, [])
        lam = []
        for f in F:
            lf = avg * att.get(team, 1) * dfn.get(f['opp'], 1) * (model25.HOME if f['home'] else 1 / model25.HOME)
            la = avg * att.get(f['opp'], 1) * dfn.get(team, 1) * (1 / model25.HOME if f['home'] else model25.HOME)
            lam.append((lf, la, f['home'], f['opp']))
        p = {'c': cls, 'mn': [mins.get(k, 0) for k in range(1, c + 1)]}
        U = model25.underlying(p, s, lam, avg * att.get(team, 1), last=c) if lam else 0.0
        actual_min = num(r_g['minutes']) - num(r_c['minutes'])
        rows.append(dict(g=g, id=pid, cls=cls, raw=raw, mults=[DIFF_MULT[f['diff']] for f in F], U=U,
                         a=avail(r_c['status'], r_c['chance_of_playing_next_round']), share=share,
                         fpl=num(r_c['ep_next']), y=int(num(r_g['event_points'])), ymin=actual_min,
                         name=r_c['web_name']))

# validação dos pontos reais da J6 contra a API oficial (live.json → event_live)
try:
    LV = json.load(open(_BD + '../live.json', encoding='utf-8'))['event_live']
    if LV['event'] == 6:
        bad = [r for r in rows if r['g'] == 6 and str(r['id']) in LV['points'] and LV['points'][str(r['id'])][0] != r['y']]
        print(f'J6: pontos do espelho vs API oficial — {len(bad)} diferenças em {sum(1 for r in rows if r["g"] == 6)} jogadores')
except (OSError, KeyError):
    pass

def pred(r, P):
    if not r['mults']: return 0.0
    F = r['raw'] * sum(m ** P['b'] for m in r['mults'])
    v = (P['w'] * F + (1 - P['w']) * r['U']) * r['a'] * (r['share'] ** P['g']) * P['s']
    if r['a'] > 0 and r['share'] > 0: v = max(v, 0.3)
    return v

def stats(ys, ps):
    n = len(ys)
    if n < 3: return dict(n=n, mae=None, corr=None, bias=None)
    mae = sum(abs(y - p) for y, p in zip(ys, ps)) / n
    my, mp = sum(ys) / n, sum(ps) / n
    cov = sum((y - my) * (p - mp) for y, p in zip(ys, ps))
    vy = sum((y - my) ** 2 for y in ys); vp = sum((p - mp) ** 2 for p in ps)
    rmse = math.sqrt(sum((y - p) ** 2 for y, p in zip(ys, ps)) / n)
    return dict(n=n, mae=round(mae, 3), rmse=round(rmse, 3), corr=round(cov / math.sqrt(vy * vp), 3) if vy and vp else None, bias=round(mp - my, 2))

def evaluate(sel, params):
    """params: dict pos -> P, ou 'fpl'."""
    R = [r for r in rows if sel(r)]
    ps = [r['fpl'] if params == 'fpl' else pred(r, params[r['cls']]) for r in R]
    return stats([r['y'] for r in R], ps)

# ---------- afinação por posição nas J2-J5 ----------
GRID_W = [i / 10 for i in range(11)]
GRID_B = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0]
GRID_G = [0.0, 0.25, 0.5, 1.0, 1.5]
GRID_S = [round(0.5 + 0.05 * i, 2) for i in range(17)]   # 0.50 .. 1.30
NEW = {}
for pos in ('gk', 'def', 'mid', 'fwd'):
    R = [r for r in rows if r['cls'] == pos and r['g'] in TUNE]
    best = None
    for b in GRID_B:
        Fb = [r['raw'] * sum(m ** b for m in r['mults']) for r in R]
        for w in GRID_W:
            for gm in GRID_G:
                base = [(w * F + (1 - w) * r['U']) * r['a'] * (r['share'] ** gm) if r['mults'] else 0.0 for F, r in zip(Fb, R)]
                for s_ in GRID_S:
                    err = 0.0
                    for v0, r in zip(base, R):
                        v = v0 * s_
                        if r['mults'] and r['a'] > 0 and r['share'] > 0: v = max(v, 0.3)
                        err += abs(r['y'] - v) if OBJ == 'mae' else (r['y'] - v) ** 2
                    if best is None or err < best[0] - 1e-9: best = (err, dict(w=w, b=b, g=gm, s=s_))
    NEW[pos] = best[1]
OLDP = {p: OLD for p in ('gk', 'def', 'mid', 'fwd')}

# ---------- resultados ----------
def block(gws):
    out = {}
    for name, sel in [('todos', lambda r: r['g'] in gws)] + [(p, (lambda p: lambda r: r['g'] in gws and r['cls'] == p)(p)) for p in ('gk', 'def', 'mid', 'fwd')]:
        out[name] = {'antes': evaluate(sel, OLDP), 'depois': evaluate(sel, NEW), 'fpl': evaluate(sel, 'fpl')}
    return out
res = {'params': {'antes': OLD, 'depois': NEW}, 'afinacao_J2_J5': block(TUNE), 'confirmacao_J6': block(CONFIRM),
       'por_jornada': {g: {'antes': evaluate(lambda r, g=g: r['g'] == g, OLDP), 'depois': evaluate(lambda r, g=g: r['g'] == g, NEW),
                           'fpl': evaluate(lambda r, g=g: r['g'] == g, 'fpl')} for g in TARGETS}}
# J6 também só com quem jogou nessa jornada (separa "acertar nos minutos" de "acertar nos pontos")
res['confirmacao_J6_so_quem_jogou'] = {k: evaluate(lambda r: r['g'] == 6 and r['ymin'] > 0, v) for k, v in (('antes', OLDP), ('depois', NEW), ('fpl', 'fpl'))}
json.dump(res, open(_BD + f'pool/backtest_result_{OBJ}.json', 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print('linhas:', len(rows), {g: sum(1 for r in rows if r['g'] == g) for g in TARGETS})
print('pesos novos:', NEW)
for part in ('afinacao_J2_J5', 'confirmacao_J6'):
    print('\n==', part)
    for k, v in res[part].items():
        print(f"  {k:5s} " + '  '.join(f"{m}: erro {v[m]['mae']} eq {v[m]['rmse']} corr {v[m]['corr']} viés {v[m]['bias']:+}" for m in ('antes', 'depois', 'fpl')) + f"  (n={v['antes']['n']})")
print('\n== por jornada')
for g, v in res['por_jornada'].items():
    print(f"  J{g} " + '  '.join(f"{m}: erro {v[m]['mae']} corr {v[m]['corr']}" for m in ('antes', 'depois', 'fpl')))
print('\n== J6 só quem jogou:', {k: (v['mae'], v['corr']) for k, v in res['confirmacao_J6_so_quem_jogou'].items()})
