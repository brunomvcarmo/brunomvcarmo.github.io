from pathlib import Path as _P
_BD = str(_P(__file__).resolve().parents[1]) + '/'   # pasta _build
"""V24 data block: fresh player pool (official API copy), multi-GW expected points,
squad state (bank, free transfers, estimated selling prices), league ownership, prediction log."""
import csv, json, math
from collections import defaultdict
M = _BD + 'mirror/'; D = _BD + 'data/'; P = _BD + 'pool/'
import os as _os; _os.makedirs(_BD + 'redesign', exist_ok=True)   # pasta dos ficheiros gerados (fora do GitHub)

def num(x, d=0.0):
    try: return float(x)
    except: return d

# ---------- mirror snapshots ----------
rows = list(csv.DictReader(open(M + 'playerstats.csv', encoding='utf-8')))
snap = defaultdict(dict)
for r in rows: snap[int(r['id'])][int(r['gw'])] = r
teams = {r['code']: int(r['id']) for r in csv.DictReader(open(M + 'teams.csv', encoding='utf-8'))}
pinfo = {int(r['player_id']): r for r in csv.DictReader(open(M + 'players.csv', encoding='utf-8'))}
POSMAP = {'Goalkeeper': 'gk', 'Defender': 'def', 'Midfielder': 'mid', 'Forward': 'fwd'}
hist = json.load(open(P + 'hist.json', encoding='utf-8'))
oldnames = {int(i): n for i, n in hist['poolNames']}

# Jornadas: a próxima é a primeira com jogos por acabar (fixtures.json vem da API oficial); a última é a anterior.
FX = json.load(open(D + 'fixtures.json', encoding='utf-8'))
NEXT = min(int(g) for g, l in FX.items() if not all(f['finished'] for f in l))
LAST = NEXT - 1; HORIZON = list(range(NEXT, NEXT + 5))
ROOT = _P(__file__).resolve().parents[2]
LV = json.load(open(ROOT / 'live.json', encoding='utf-8'))
import re as _re
_HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
def _const(name, pat=r'(\{.*?\})'):
    return json.loads(_re.search(r'const %s = %s;\n' % (name, pat), _HTML).group(1))
OLD_META = _const('GW_META'); OLD_STATE = _const('SQUAD_STATE'); OLD_LOG = _const('PRED_LOG', r'(\[.*?\])')
OLD_OTP = _const('OFFICIAL_TEAM_PTS')
def gw_fix(gw):
    out = defaultdict(list)
    for f in FX[str(gw)]:
        out[f['h']].append(dict(opp=f['a'], home=True, diff=f['dh']))
        out[f['a']].append(dict(opp=f['h'], home=False, diff=f['da']))
    return out
FIXG = {g: gw_fix(g) for g in HORIZON}

DIFF_MULT = {1: 1.30, 2: 1.15, 3: 1.00, 4: 0.85, 5: 0.70}
BASE = {'gk': 3.2, 'def': 3.0, 'mid': 3.4, 'fwd': 3.6}
RECENT = (LAST - 2, LAST - 1, LAST)   # forma = as últimas 3 jornadas

def avail(st, ch, g):
    """Official status -> availability for gameweek g (documented assumption)."""
    ch = None if ch in ('', None) else num(ch)
    if st == 'a': return 1.0
    if st == 'd': return (ch / 100 if ch is not None else 0.75) if g == NEXT else 1.0
    if st == 'i': return (ch / 100 if ch is not None else 0.0) if g == NEXT else (0.25 if g == NEXT + 1 else 0.5)
    if st == 's': return 0.0 if g == NEXT else 1.0
    return 0.0  # 'u' / 'n': saiu da liga ou indisponível

pool = []
for pid, s in snap.items():
    last = s.get(LAST)
    if not last: continue
    info = pinfo.get(pid)
    if not info: continue
    cls = POSMAP.get(info['position'])
    team = teams.get(info['team_code'])
    if not cls or not team: continue
    name = oldnames.get(pid) or f"{last['first_name']} {last['second_name']}".strip()
    pts, mins = [], []
    pm = pt = 0.0
    for g in range(1, LAST + 1):
        r = s.get(g)
        if not r: pts.append(None); mins.append(None); continue
        m = num(r['minutes']); t = num(r['total_points'])
        pts.append(int(num(r['event_points']))); mins.append(int(m - pm)); pm, pt = m, t
    def cum(g, k):
        r = s.get(g); return num(r[k]) if r else 0.0
    xg3 = cum(LAST, 'expected_goals') - cum(LAST - 3, 'expected_goals')
    xa3 = cum(LAST, 'expected_assists') - cum(LAST - 3, 'expected_assists')
    dc3 = cum(LAST, 'defensive_contribution') - cum(LAST - 3, 'defensive_contribution')
    rec = [(pts[g - 1], mins[g - 1]) for g in RECENT if pts[g - 1] is not None]
    price = num(last['now_cost'])
    if rec:
        avg = sum(p for p, _ in rec) / len(rec)
        share = sum(min(m, 90) for _, m in rec) / (90 * len(rec))
    else:
        avg = 0.0; share = 0.0
    base = BASE[cls] + (max(0, price - 6.5) * 0.4 if cls in ('mid', 'fwd') else 0)
    raw = 0.55 * avg + 0.45 * base * share
    ep = []
    for g in HORIZON:
        fx = FIXG[g].get(team, [])
        a = avail(last['status'], last['chance_of_playing_next_round'], g)
        v = sum(raw * DIFF_MULT[f['diff']] for f in fx) * a
        if fx and a > 0 and share > 0: v = max(v, 0.3)
        ep.append(round(v, 1))
    m3 = sum(m for _, m in rec)
    start_price = round(price - num(last['cost_change_start']) / 10, 1)
    pool.append(dict(id=pid, n=name, t=team, c=cls, p=price, sp=start_price,
                     s=last['status'], ch=(None if last['chance_of_playing_next_round'] in ('', None) else int(num(last['chance_of_playing_next_round']))),
                     nw=last['news'] or '', o=num(last['selected_by_percent']), ti=int(num(last['transfers_in_event'])),
                     to=int(num(last['transfers_out_event'])), cc=int(num(last['cost_change_event'])), cs=int(num(last['cost_change_start'])),
                     en=num(last['ep_next']), tp=int(num(last['total_points'])), pts=pts, mn=mins,
                     xg=round(xg3, 2), xa=round(xa3, 2), dc=round(dc3 / (m3 / 90), 1) if m3 >= 90 else 0.0, m3=m3, ep=ep, _raw=raw))
import model25
# V58: disponibilidade prevista (lesões: jornada provável de regresso; castigos: confirmados e risco por amarelos).
# Para quem tem uma previsão, o modelo calcula os pontos "se jogar" (f) e depois multiplica pelo fator de cada
# jornada (ef: probabilidade de estar disponível, com 70% dos minutos na 1.ª jornada depois de voltar).
import disponibilidade
AVAIL = disponibilidade.compute(NEXT)
def _avail(p, g):
    if g == NEXT and p['n'] in model25.READING: return 1.0
    if p['id'] in AVAIL['p']: return 1.0
    return avail(p['s'], '' if p['ch'] is None else p['ch'], g)
LAMBDAS = model25.apply(pool, snap, FIXG, HORIZON, NEXT, _avail, LAST)
for p in pool:
    r = AVAIL['p'].get(p['id'])
    if not r: continue
    r['f'] = p['ep'][:]
    r['rd0'] = 1 if p['n'] in model25.READING else 0
    fac = [1.0 if (i == 0 and r['rd0']) else r['ef'].get(str(g), 1.0) for i, g in enumerate(HORIZON)]
    p['ep'] = [round(v * f, 1) for v, f in zip(p['ep'], fac)]
    p['k'][3] = round(p['k'][3] * fac[0], 2)
pool.sort(key=lambda x: (x['t'], ['gk', 'def', 'mid', 'fwd'].index(x['c']), -x['p']))
byname = {p['n']: p for p in pool}; byid = {p['id']: p for p in pool}

# ---------- posse na liga (os 20 plantéis mais recentes, do live.json) ----------
lown = defaultdict(int); nsq = 0
for e, x in LV['entries'].items():
    pk = x.get('picks')
    if not pk: continue
    nsq += 1
    for i in pk['starters'] + pk['bench']: lown[i] += 1
for p in pool: p['lo'] = round(100 * lown.get(p['id'], 0) / nsq) if nsq else 0

# ---------- plantel do Bruno e do Marco ----------
# Base = SQUAD_STATE do index.html (atualizado pelo apply_picks.py depois de cada deadline, com os preços de compra
# reais das transferências); aqui só se refazem os preços de venda com os preços novos, o banco e as grátis.
ENTRY = {'bruno': '5191766', 'marco': '1973102'}
STATE = {}
for mgr, e in ENTRY.items():
    st = json.loads(json.dumps(OLD_STATE[mgr]))
    x = LV['entries'][e]
    ids = x['picks']['starters'] + x['picks']['bench']
    if sorted(ids) != sorted(q['id'] for q in st['players']):
        # houve transferências desde a última atualização: entradas com o preço de compra oficial (rivals.json)
        RV = json.load(open(ROOT / 'rivals.json', encoding='utf-8'))['entries'][e]
        old = {q['id']: q for q in st['players']}
        buys = {}
        for t in sorted(RV['transfers'], key=lambda t: t[0]):
            if t[3]: buys[t[1]] = (t[3] / 10, t[0])
        st['players'] = [old.get(i) or dict(id=i, buy=buys.get(i, (byid[i]['p'], x['picks']['event']))[0], since=buys.get(i, (0, x['picks']['event']))[1]) for i in ids]
        print(f'{mgr}: plantel refeito a partir dos picks da J{x["picks"]["event"]} ({sum(1 for i in ids if i not in old)} entradas)')
    for q in st['players']:
        now = byid[q['id']]['p']
        q['sell'] = now if now <= q['buy'] else round(q['buy'] + math.floor(round((now - q['buy']) * 10) / 2) / 10, 1)
    h = next((r for r in x['history'] if r['event'] == x['picks']['event']), None) or next((r for r in x['history'] if r['event'] == LAST), None)
    if h: st['bank'] = h['bank'] / 10
    # grátis para a próxima jornada pela regra da FPL (1 por jornada, até 5; Wildcard/Free Hit não gastam). ESTIMATIVA.
    wcfh = {c['event'] for c in x.get('chips', []) if c['name'] in ('wildcard', 'freehit')}
    ft, H = 1, {r['event']: r for r in x['history']}
    for g in range(2, NEXT):
        used = 0 if g in wcfh else H.get(g, {}).get('event_transfers', 0)
        ft = min(5, max(0, ft - used) + 1)
    st['ft'] = ft
    STATE[mgr] = st

# ---------- registo de previsões ----------
def actual(name, gw):
    p = byname.get(name)
    return None if not p else p['pts'][gw - 1]
FORMS = [(3, 5, 2), (3, 4, 3), (4, 5, 1), (4, 4, 2), (4, 3, 3), (5, 4, 1), (5, 3, 2), (5, 2, 3)]
def best_xi(ids, gi=0):
    """Melhor onze por pontos esperados (formações válidas da FPL) e capitão = maior ep do onze."""
    ps = [byid[i] for i in ids]
    by = {c: sorted([p for p in ps if p['c'] == c], key=lambda p: -p['ep'][gi]) for c in ('gk', 'def', 'mid', 'fwd')}
    best = None
    for d, m, f in FORMS:
        xi = by['gk'][:1] + by['def'][:d] + by['mid'][:m] + by['fwd'][:f]
        v = sum(p['ep'][gi] for p in xi)
        if best is None or v > best[0]: best = (v, xi)
    xi = best[1]; cap = max(xi, key=lambda p: p['ep'][gi])
    return xi, cap
LOG = []
for entry in OLD_LOG:
    if entry['gw'] >= NEXT: continue      # a previsão da próxima jornada é refeita em baixo
    for rows in entry['teams'].values():
        for r in rows:
            if entry['gw'] <= LAST and r.get('real') is None: r['real'] = actual(r['n'], entry['gw'])
    LOG.append(entry)
nxt = dict(gw=NEXT, model='V53 (forma das últimas 3 + xG/xA da época e odds + projeções de 4 sites + leitura própria + descanso); onze = melhor onze do plantel atual, sem trocas', teams={})
for mgr in ENTRY:
    ids = [q['id'] for q in STATE[mgr]['players']]
    xi, cap = best_xi(ids)
    xs = {p['id'] for p in xi}
    nxt['teams'][mgr] = [dict(n=byid[i]['n'], ep=byid[i]['ep'][0], xi=i in xs, c=i == cap['id'], real=None) for i in ids]
LOG.append(nxt)
OFFICIAL_TEAM_PTS = {int(k): v for k, v in OLD_OTP.items()}
for g in range(1, LAST + 1):
    pts = {mgr: next((r['points'] for r in LV['entries'][e]['history'] if r['event'] == g), None) for mgr, e in ENTRY.items()}
    if all(v is not None for v in pts.values()) and any(x['gw'] == g for x in LOG): OFFICIAL_TEAM_PTS[g] = pts

# ---------- GW_META ----------
import datetime as _dt
def _lis(t):   # hora de Lisboa (UTC+1 entre o último domingo de março e o último de outubro, 01:00 UTC)
    d = _dt.datetime.strptime(t, '%Y-%m-%dT%H:%M:%SZ')
    def last_sun(m):
        x = _dt.datetime(d.year, m, 31, 1); return x - _dt.timedelta(days=(x.weekday() + 1) % 7)
    return d + _dt.timedelta(hours=1 if last_sun(3) <= d < last_sun(10) else 0)
DIAS = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']; MES = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
ko = sorted(f['kickoff'] for f in FX[str(NEXT)])
deadline = (_dt.datetime.strptime(ko[0], '%Y-%m-%dT%H:%M:%SZ') - _dt.timedelta(minutes=90)).strftime('%Y-%m-%dT%H:%M:%SZ')
dl = _lis(deadline); k0, k1 = _lis(ko[0]), _lis(ko[-1])
window = f'{k0.day}-{k1.day} {MES[k1.month - 1].lower()}' if k0.month == k1.month else f'{k0.day} {MES[k0.month - 1].lower()}-{k1.day} {MES[k1.month - 1].lower()}'
H2H = json.load(open(D + 'h2h.json', encoding='utf-8'))   # escrito por h2h_week.py (tabela depois da última jornada + adversários)
_today = _dt.date.today()
META = dict(next=NEXT, last=LAST, lastProvisional=not H2H.get('lastFinal', False), horizon=HORIZON,
            deadline=deadline, deadlineLabel=f'{DIAS[dl.weekday()]} {dl.day} {MES[dl.month - 1]} · {dl:%H:%M}', window=window,
            dataDate=f'{_today.day} {MES[_today.month - 1].lower()} {_today.year}',
            poolSource='cópia pública da API oficial (FPL-Elo-Insights, atualizada 2×/dia), validada contra a API oficial',
            h2h={mgr: H2H['managers'][mgr] for mgr in ENTRY}, ftConfirmed=False, squadsGw=LV['picks_event'] if LV['picks_event'] <= LAST else OLD_META.get('squadsGw', LAST))

KEYS = ['id','n','t','c','p','sp','s','ch','nw','o','lo','ti','to','cc','cs','en','tp','pts','mn','xg','xa','dc','m3','ep','k','rd']
js = []
js.append('// ======================= DADOS DA JORNADA (V24) =======================')
js.append('// Gerado por _build/pool/gen25.py. Tudo o que muda de semana para semana e não é texto vive aqui.')
_AUTO = ROOT / '_build' / 'rotina' / 'auto.json'   # V56: última atualização automática (rotina.py marcar)
if _AUTO.exists(): js.append('const AUTO_UPDATE = ' + json.dumps(json.load(open(_AUTO, encoding='utf-8')), ensure_ascii=False, separators=(',', ':')) + ';')
js.append('const GW_META = ' + json.dumps(META, ensure_ascii=False) + ';')
js.append('const POOL_KEYS = ' + json.dumps(KEYS) + ';')
js.append('const POOL24 = [\n' + ',\n'.join(json.dumps([p[k] for k in KEYS], ensure_ascii=False, separators=(',', ':')) for p in pool) + '\n].map(r => Object.fromEntries(POOL_KEYS.map((k, i) => [k, r[i]])));')
import ticker26
_TK = ticker26.build()
def _tk(g, t, o):
    return next((x for x in _TK.get(g, {}).get(t, []) if x['opp'] == o), None)
def _fx(f, g):
    th, ta = _tk(g, f['h'], f['a']), _tk(g, f['a'], f['h'])
    d = dict(h=f['h'], a=f['a'], fh=f['dh'], fa=f['da'], k=f['kickoff'])
    d.update(dh=round(th['ovr']) if th else f['dh'], da=round(ta['ovr']) if ta else f['da'],
             th=th['ovr'] if th else f['dh'], ta=ta['ovr'] if ta else f['da'],
             hA=th and th['att'], hD=th and th['dfn'], aA=ta and ta['att'], aD=ta and ta['dfn'])
    return d
fa = {g: [_fx(f, g) for f in FX[str(g)]] for g in HORIZON + [HORIZON[-1] + 1]}
js.append('const FIX_AHEAD = ' + json.dumps(fa, separators=(',', ':')) + ';')
js.append('const TICKER_SOURCES = ' + json.dumps([s for s in ticker26.T['sources'] if s['key'] in ('xgstat', 'oddalerts')], ensure_ascii=False) + ';')
js.append('const SQUAD_STATE = ' + json.dumps(STATE, ensure_ascii=False, separators=(',', ':')) + ';')
js.append('const PRED_LOG = ' + json.dumps(LOG, ensure_ascii=False, separators=(',', ':')) + ';')
js.append('const OFFICIAL_TEAM_PTS = ' + json.dumps(OFFICIAL_TEAM_PTS) + ';')
open(_BD + 'redesign/data25.js', 'w', encoding='utf-8', newline='\n').write('\n'.join(js) + '\n')

# ---------- report ----------
print('pool', len(pool), 'kb', round(len('\n'.join(js)) / 1024))
for mgr in ('bruno', 'marco'):
    st = STATE[mgr]
    print(mgr, 'bank', st['bank'], 'ft', st['ft'])
    for x in st['players']:
        p = byid[x['id']]
        print(f"   {p['n'][:22]:22} since J{x['since']} buy {x['buy']} now {p['p']} sell {x['sell']} ep {p['ep']}")
for n in ('Pascal Groß', 'Erling Haaland', 'Antoine Semenyo', 'Bukayo Saka', 'Dominik Szoboszlai'):
    p = byname.get(n); print(n, p and (p['ep'], p['pts'], p['xg'], p['lo']))

# ---------- Marco: J6 player by player (official element-summary; mirror fills the gaps) ----------
def gw_row(pid, gw):
    s = snap.get(pid, {}); a = s.get(gw); b = s.get(gw - 1)
    def dif(k): return num(a[k]) - (num(b[k]) if b else 0) if a else 0
    return dict(pts=int(num(a['event_points'])) if a else 0, mins=int(dif('minutes')), g=int(dif('goals_scored')), a=int(dif('assists')),
                bonus=int(dif('bonus')), xg=round(dif('expected_goals'), 2), xa=round(dif('expected_assists'), 2))
def gw_detail(mgr):
    x = LV['entries'][ENTRY[mgr]]; pk = x['picks']
    if pk['event'] != LAST:   # o live.json já tem os picks da jornada seguinte: os da última vêm do rivals.json
        gg = json.load(open(ROOT / 'rivals.json', encoding='utf-8'))['entries'][ENTRY[mgr]]['gws'][str(LAST)]
        pk = dict(event=LAST, starters=gg['s'], bench=gg['b'], captain=gg['c'], vice=gg['v'], active_chip=gg.get('chip'))
    chip = pk.get('active_chip')
    players = [dict(name=byid[i]['n'], cls=byid[i]['c'], started=i in pk['starters'] or chip == 'bboost', **gw_row(i, LAST)) for i in pk['starters'] + pk['bench']]
    cap = byid[pk['captain']]['n']
    tot = sum(p['pts'] for p in players if p['started']) + next(p['pts'] for p in players if p['name'] == cap) * (2 if chip == '3xc' else 1)
    off = next(r['points'] for r in x['history'] if r['event'] == LAST)
    print(f'{mgr} J{LAST}: soma jogador a jogador {tot} · oficial {off}')
    assert tot == off, 'a soma não bate com a API oficial (oitava lição)'
    return dict(gw=LAST, captain=cap, vice=byid[pk['vice']]['n'], chip=chip, players=players)
MGD = gw_detail('marco'); BGD = gw_detail('bruno')
TEAM_SHORT = {int(r['id']): r['short_name'] for r in csv.DictReader(open(M + 'teams.csv', encoding='utf-8'))}
with open(_BD + 'redesign/data25.js', 'a', encoding='utf-8', newline='\n') as fh:
    fh.write('const MARCO_GW_DETAIL = ' + json.dumps(MGD, ensure_ascii=False, separators=(',', ':')) + ';\n')
    fh.write('const BRUNO_GW_DETAIL = ' + json.dumps(BGD, ensure_ascii=False, separators=(',', ':')) + ';\n')
    fh.write('const TEAM_SHORT = ' + json.dumps(TEAM_SHORT, ensure_ascii=False, separators=(',', ':')) + ';\n')

# ---------- V25: what the FPL sites say ----------
R = _BD + 'research/'
EX = json.load(open(R + 'expert.json', encoding='utf-8'))
NUMR = json.load(open(R + 'proj-numeric.json', encoding='utf-8'))
ODDS = json.load(open(R + 'odds.json', encoding='utf-8'))
POS_ST = {'buy', 'start', 'differential', 'captain'}
agg = {}
PT = json.load(open(R + 'expert_pt.json', encoding='utf-8'))
for i, m in enumerate(EX['mentions']):
    m = dict(m, note=PT[i])
    pid = m.get('id')
    if pid is None or pid not in byid: continue
    a = agg.setdefault(pid, dict(pos=0, neg=0, cap=0, notes=[]))
    if m['stance'] in POS_ST: a['pos'] += 1
    else: a['neg'] += 1
    if m['stance'] == 'captain': a['cap'] += 1
    if len(a['notes']) < 4: a['notes'].append([m['source'], m['stance'], m['note']])
SRC_LABEL = {'ffhub_guide': 'Fantasy Football Hub', 'rotowire_rankings': 'RotoWire', 'ffs_gw7_hub': 'Fantasy Football Scout',
             'ffs_early_scout_picks': 'FFS Scout Picks', 'ffs_brentfordfc': 'FFS (brentfordfc.com)', 'fffix_transfer_tips': 'Fantasy Football Fix',
             'fplpage_buy': 'fpl.page', 'statszone_captain': 'The Stats Zone', 'fplcopilot_tc': 'FPL Copilot', 'false9_captain': 'The False 9',
             'false9_chips': 'The False 9', 'false9_transfers': 'The False 9', 'false9_defenders': 'The False 9',
             'onefpl_targets': 'OneFPL', 'statszone_captain': 'The Stats Zone', 'ffhub_guide': 'Fantasy Football Hub'}
EXPERT = dict(players={str(k): v for k, v in agg.items()},
              captains=EX['captain_rankings'],
              sources=[dict(key=s['key'], label=SRC_LABEL.get(s['key'], s['key']), url=s['url'], date=s.get('page_date')) for s in EX['sources']],
              teamNotes=EX.get('team_notes', []))
EXT7 = {}
for pid, e in NUMR['players'].items():
    d = {}
    for k in ('fplform', 'fplcopilot', 'onside', 'pundit'):
        v = (e.get(k) or {}).get(str(NEXT))
        if v is not None: d[k] = v
    if d: EXT7[pid] = d
PROJ_SOURCES = [dict(key=s['key'], url=s['url'], date=s.get('page_date')) for s in NUMR['sources']]
import model25 as _m
MATCH_ODDS = []
for m in ODDS['matches']:
    h, a = _m.TEAMNAME.get(m['home']), _m.TEAMNAME.get(m['away'])
    lh, la = _m.poisson_fit_from_odds(m)
    MATCH_ODDS.append(dict(h=h, a=a, o=m['odds'], lh=round(lh, 1), la=round(la, 1), cs_h=round(math.exp(-la) * 100), cs_a=round(math.exp(-lh) * 100)))
with open(_BD + 'redesign/data25.js', 'a', encoding='utf-8', newline='\n') as fh:
    fh.write('const EXPERT = ' + json.dumps(EXPERT, ensure_ascii=False, separators=(',', ':')) + ';\n')
    fh.write('const EXT7 = ' + json.dumps(EXT7, separators=(',', ':')) + ';\n')
    fh.write('const PROJ_SOURCES = ' + json.dumps(PROJ_SOURCES, ensure_ascii=False) + ';\n')
    fh.write('const MATCH_ODDS = ' + json.dumps(MATCH_ODDS, separators=(',', ':')) + ';\n')
    fh.write('const READING_NOTE = ' + json.dumps({k: v[1] for k, v in _m.READING.items()}, ensure_ascii=False) + ';\n')
print('expert players', len(agg), 'ext7', len(EXT7))
for m in MATCH_ODDS: print(m)

# ---------- V35 (15 out): estatísticas da época por jogador, para o comparador "lado a lado" ----------
# Do snapshot mais recente do espelho (acumulado da época até à última jornada).
SS_KEYS = ['minutes', 'starts', 'goals_scored', 'assists', 'expected_goals', 'expected_assists', 'expected_goals_conceded',
           'clean_sheets', 'goals_conceded', 'saves', 'penalties_saved', 'bonus', 'bps', 'defensive_contribution',
           'clearances_blocks_interceptions', 'recoveries', 'tackles', 'penalties_order', 'corners_and_indirect_freekicks_order', 'ict_index']
SEASON = {}
for pid, by in snap.items():
    g = max([x for x in by if x <= LAST] or [0]); r = by.get(g)
    if not r: continue
    row = []
    for k in SS_KEYS:
        v = r.get(k, '')
        row.append(None if v in ('', None) else (round(num(v), 2) if k.startswith('expected') or k == 'ict_index' else int(num(v))))
    SEASON[pid] = row
with open(_BD + 'redesign/data25.js', 'a', encoding='utf-8', newline='\n') as fh:
    fh.write('const SEASON_KEYS = ' + json.dumps(SS_KEYS) + ';\n')
    fh.write('const SEASON_STATS = ' + json.dumps(SEASON, separators=(',', ':')) + ';\n')
print('season stats', len(SEASON))

# ---------- Fase 2 (15 out): distribuição empírica dos pontos face à média de cada jogador ----------
# X = pontos numa jornada em que jogou / média do próprio jogador nas jornadas em que jogou (≥3 jogos, média ≥1,5).
# 101 quantis por posição; a app multiplica pelos "pontos quando joga" para tirar probabilidades e simular.
import collections as _col
_pos = {int(r['player_id']): r['position'] for r in csv.DictReader(open(M + 'players.csv', encoding='utf-8'))}
_map = {'Goalkeeper': 'gk', 'Defender': 'def', 'Midfielder': 'mid', 'Forward': 'fwd'}
_by = _col.defaultdict(dict)
for r in csv.DictReader(open(M + 'playerstats.csv', encoding='utf-8')):
    g = int(r['gw'])
    if g <= LAST: _by[int(r['id'])][g] = r
_X = {k: [] for k in _map.values()}
for pid, gws in _by.items():
    prev, apps = 0, []
    for g in sorted(gws):
        m = int(num(gws[g]['minutes'])); dm = m - prev; prev = m
        if dm > 0: apps.append(num(gws[g]['event_points']))
    c = _map.get(_pos.get(pid))
    if c and len(apps) >= 3:
        mu = sum(apps) / len(apps)
        if mu >= 1.5: _X[c].extend(a / mu for a in apps)
EMP_X = {}
for c, v in _X.items():
    v.sort(); n = len(v)
    EMP_X[c] = [round(v[int(i / 100 * (n - 1))], 3) for i in range(101)]
with open(_BD + 'redesign/data25.js', 'a', encoding='utf-8', newline='\n') as fh:
    fh.write('const EMP_X = ' + json.dumps(EMP_X, separators=(',', ':')) + ';\n')
    fh.write('const EMP_N = ' + json.dumps({c: len(v) for c, v in _X.items()}) + ';\n')

# ---------- V54 (20 out): jornadas duplas e brancas da 2.ª metade (dgw_model.py) ----------
import dgw_model
DGW = dgw_model.build()
with open(_BD + 'redesign/data25.js', 'a', encoding='utf-8', newline='\n') as fh:
    fh.write('const AVAIL_PRED = ' + json.dumps(AVAIL, ensure_ascii=False, separators=(',', ':')) + ';\n')
    fh.write('const DGW_DATA = ' + json.dumps(DGW, ensure_ascii=False, separators=(',', ':')) + ';\n')
print('DGW_DATA', len(DGW['events']), 'rondas de taça com jornada em conflito')

# ---------- V59 (9 nov): onde a app discorda da FPL e dos sites (discorda.py) ----------
# Consenso = mediana de FPL (ep_next) + sites; compara com a app completa e com a parte só nossa. Guarda as
# discordâncias da próxima jornada em _build/research/discorda.json (antes do deadline) para medir quem tem razão.
import discorda
DIS = discorda.build(pool, None, FX, HORIZON, NEXT, deadline, LV)
with open(_BD + 'redesign/data25.js', 'a', encoding='utf-8', newline='\n') as fh:
    fh.write('const DISAGREE = ' + json.dumps(DIS, ensure_ascii=False, separators=(',', ':')) + ';\n')
