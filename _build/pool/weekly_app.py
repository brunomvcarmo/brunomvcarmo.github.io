"""Atualização semanal das tabelas da app (2.º <script> do index.html) que antes eram escritas à mão a cada jornada.
Correr DEPOIS de: fpl_fetch.py (live.json/rivals.json), h2h_week.py (_build/data/h2h.json), lineups_rw.py
(_build/research/lineups.json), gen25.py + swapdata.py (bloco de dados novo, com GW_META.next/last).
Uso (a partir da raiz): py -X utf8 _build/pool/weekly_app.py

Tabelas refeitas: FIXTURES_GW1 (última jornada) e FIXTURES_GW2 (próxima), RESULTS_BY_GW (+ última jornada),
FIXTURES_BY_GW/UPCOMING_GWS, LEAGUE_STANDINGS, H2H_RESULT_GWn/H2H_RESULTS_* e H2H_SCHEDULE dos dois,
HISTORY/MARCO_HISTORY (+ entrada da última jornada, texto gerado a partir dos números oficiais), MARCO_SQUAD_GWn,
PROBABLE_LINEUPS_GW2, XG_LEADERS e HOT_PLAYERS (últimas 3 jornadas).
NÃO mexe nas recomendações (SUGGESTED_MOVES, SUBS, CAPTAIN_CHANGE, CHIP_PLAN): essas são decisões, revêem-se à mão."""
import csv, json, re
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / '_build'
H = ROOT / 'index.html'
s = H.read_text(encoding='utf-8')
LV = json.load(open(ROOT / 'live.json', encoding='utf-8'))
RV = json.load(open(ROOT / 'rivals.json', encoding='utf-8'))
FX = json.load(open(B / 'data/fixtures.json', encoding='utf-8'))
H2H = json.load(open(B / 'data/h2h.json', encoding='utf-8'))
LU = json.load(open(B / 'research/lineups.json', encoding='utf-8'))


def const(name, pat=r'(\{.*?\})'):
    return json.loads(re.search(r'const %s = %s;\n' % (name, pat), s).group(1))


META = const('GW_META'); NEXT, LAST = META['next'], META['last']
KEYS = const('POOL_KEYS', r'(\[.*?\])')
i0 = s.index('const POOL24 = [\n') + len('const POOL24 = [\n')
POOL = [dict(zip(KEYS, json.loads(l.rstrip(',')))) for l in s[i0:s.index('\n]', i0)].split('\n')]
BYID = {p['id']: p for p in POOL}
TEAMS = {int(r['id']): r['name'] for r in csv.DictReader(open(B / 'mirror/teams.csv', encoding='utf-8'))}
TEAMS_APP = {1: 'Arsenal', 2: 'Aston Villa', 3: 'Bournemouth', 4: 'Brentford', 5: 'Brighton', 6: 'Chelsea', 7: 'Coventry City', 8: 'Crystal Palace',
             9: 'Everton', 10: 'Fulham', 11: 'Hull City', 12: 'Ipswich Town', 13: 'Leeds', 14: 'Liverpool', 15: 'Man City', 16: 'Man Utd',
             17: 'Newcastle', 18: "Nott'm Forest", 19: 'Spurs', 20: 'Sunderland'}
ENTRY = {'bruno': '5191766', 'marco': '1973102'}
STATE = const('SQUAD_STATE')
DIAS = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']; MES = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
js = lambda o: json.dumps(o, ensure_ascii=False)


def lis(t):
    d = datetime.strptime(t[:19], '%Y-%m-%dT%H:%M:%S')
    def last_sun(m):
        x = datetime(d.year, m, 31, 1); return x - timedelta(days=(x.weekday() + 1) % 7)
    return d + timedelta(hours=1 if last_sun(3) <= d < last_sun(10) else 0)


def when(t):
    k = lis(t); return f'{DIAS[k.weekday()]} {k.day} {MES[k.month - 1]}, {k:%H:%M}'


def block(name, opener):
    """(início, fim) do bloco '  const NAME = [ ... ];' (ou { ... };) com a indentação de 2 espaços da app."""
    a = s.index(f'  const {name} = {opener}')
    close = '\n  ];\n' if opener == '[' else '\n  };\n'
    b = s.index(close, a) + len(close)
    return a, b


def put_block(name, opener, text):
    global s
    a, b = block(name, opener)
    s = s[:a] + text + s[b:]


def fx_rows(g):
    return sorted(FX[str(g)], key=lambda f: (f['kickoff'], f['id']))


# ---------- jogos da última e da próxima jornada ----------
for name, g in (('FIXTURES_GW1', LAST), ('FIXTURES_GW2', NEXT)):
    rows = ''.join(f'    {{h:{f["h"]}, a:{f["a"]}, dh:{f["dh"]}, da:{f["da"]}, when:"{when(f["kickoff"])}"}},\n' for f in fx_rows(g))
    put_block(name, '[', f'  const {name} = [\n{rows}  ];\n')

# ---------- resultados + xG (resultado oficial; xG do espelho FPL-Elo-Insights) ----------
code2id = {r['code']: int(r['id']) for r in csv.DictReader(open(B / 'mirror/teams.csv', encoding='utf-8'))}
a, b = block('RESULTS_BY_GW', '[')
have = {int(g) for g in re.findall(r'\{gw:(\d+), matches:\[', s[a:b])}
add = ''
for g in range(1, LAST + 1):
    if g in have: continue
    xg = {}
    for r in csv.DictReader(open(B / f'mirror/matches_gw{g}.csv', encoding='utf-8')):
        if not r['home_team'] or not r['away_team'] or 'prem' not in r['match_id']: continue
        h, aw = code2id.get(str(int(float(r['home_team'])))), code2id.get(str(int(float(r['away_team']))))
        xg[(h, aw)] = (float(r['home_expected_goals_xg'] or 0), float(r['away_expected_goals_xg'] or 0))
    lines = []
    for f in fx_rows(g):
        hx, ax = xg[(f['h'], f['a'])]
        lines.append(f'      {{h:{f["h"]}, a:{f["a"]}, hs:{f["hs"]}, as:{f["as"]}, hxg:{hx:.2f}, axg:{ax:.2f}}}, // {TEAMS_APP[f["h"]]} {f["hs"]}-{f["as"]} {TEAMS_APP[f["a"]]}\n')
    add += f'    {{gw:{g}, matches:[\n' + ''.join(lines) + '    ]},\n'
if add:
    s = s[:b - len('  ];\n')] + add + s[b - len('  ];\n'):]

# ---------- calendário das próximas jornadas ----------
def short_fx(g):
    return '[' + ','.join(f'{{h:{f["h"]},a:{f["a"]},dh:{f["dh"]},da:{f["da"]}}}' for f in fx_rows(g)) + ']'
put_block('FIXTURES_BY_GW', '{', f'  const FIXTURES_BY_GW = {{\n    {NEXT}: FIXTURES_GW2,\n    {NEXT + 1}: {short_fx(NEXT + 1)},\n    {NEXT + 2}: {short_fx(NEXT + 2)},\n  }};\n')
s = re.sub(r'  const UPCOMING_GWS = \[[^\]]*\];', f'  const UPCOMING_GWS = [{NEXT}, {NEXT + 1}, {NEXT + 2}];', s)

# ---------- classificação da liga clássica ----------
st = sorted(LV['standings'], key=lambda r: r['rank'])
rows = ''.join(f'    {{rank:{r["rank"]:<2}, manager:{js(r["player_name"]):<38}, team:{js(r["entry_name"]):<24}, pts:{r["total"]}, gw:{r["event_total"]}, mine:{"true" if str(r["entry"]) == ENTRY["bruno"] else "false"}, marco:{"true" if str(r["entry"]) == ENTRY["marco"] else "false"}}},\n' for r in st)
put_block('LEAGUE_STANDINGS', '[', f'  const LEAGUE_STANDINGS = [\n{rows}  ];\n')
# totais e pontos da última jornada também nos plantéis da liga (Comparar equipas, Previsão da classificação…)
m = re.search(r'  const LEAGUE_SQUADS = (\{.*?\});\n', s)
LSQ = json.loads(m.group(1))
for r in st:
    L = LSQ.get(str(r['entry']))
    if L: L['tot'], L['p6'] = r['total'], r['event_total']
POOLNAME = {p['id']: p['n'] for p in POOL}
for e, x in LV['entries'].items():
    L, pk = LSQ.get(str(e)), x.get('picks')
    if not L or not pk or pk['event'] > LAST: continue   # depois do deadline da próxima é o apply_picks.py que trata
    L['s'], L['b'] = pk['starters'], pk['bench']
    L['c'], L['vc'] = POOLNAME.get(pk['captain'], L.get('c')), POOLNAME.get(pk['vice'], L.get('vc'))
    L['chip' + str(pk['event'])] = pk.get('active_chip')
    h = next((r for r in x['history'] if r['event'] == pk['event']), None)
    if h: L['bank'], L['val'] = h['bank'] / 10, h['value'] / 10
    L['chips'] = [[c['name'], c['event']] for c in x.get('chips', [])]
s = s[:m.start()] + '  const LEAGUE_SQUADS = ' + json.dumps(LSQ, ensure_ascii=False, separators=(',', ':')) + ';\n' + s[m.end():]

# ---------- H2H: resultados até à última jornada e adversário da próxima ----------
def res_txt(m, t, g):
    r = 'ganhaste' if m > t else 'perdeste' if m < t else 'empataste'
    return r + (' (provisório)' if g == LAST and META.get('lastProvisional') else '')
for mgr, pre, arr in (('bruno', 'H2H_RESULT_GW', 'H2H_RESULTS_BRUNO'), ('marco', 'MARCO_H2H_RESULT_GW', 'H2H_RESULTS_MARCO')):
    M = H2H['managers'][mgr]
    for r in M['results']:
        line = f'  const {pre}{r["gw"]} = {{opponent:{js(r["opp"] + " (" + r["team"] + ")")}, mine:{r["mine"]}, theirs:{r["theirs"]}, result:"{res_txt(r["mine"], r["theirs"], r["gw"])}"}};'
        m = re.search(rf'  const {pre}{r["gw"]} = \{{.*?\}};', s)
        if m:
            s = s[:m.start()] + line + s[m.end():]
        else:   # acrescenta a seguir à jornada anterior
            prev = re.search(rf'  const {pre}{r["gw"] - 1} = \{{.*?\}};', s)
            s = s[:prev.end()] + '\n' + line + s[prev.end():]
    s = re.sub(rf'  const {arr} = \[[^\]]*\];', f'  const {arr} = [' + ', '.join(f'{pre}{r["gw"]}' for r in M['results']) + '];', s)
    sched = 'H2H_SCHEDULE' if mgr == 'bruno' else 'MARCO_H2H_SCHEDULE'
    put_block(sched, '[', f'  const {sched} = [\n    {{gw:{NEXT}, opponent:{js(M["next"])}, team:{js(M["nextTeam"])}, detail:true}},\n  ];\n')

# ---------- histórico jornada a jornada (Bruno: HISTORY; Marco: MARCO_HISTORY + MARCO_SQUAD_GWn) ----------
avg = {e['id']: e['avg'] for e in LV['events']}
def rank_txt(e, g):
    h = next((x for x in RV['entries'][e]['history'] if x[0] == g), None)
    if not h or not h[8]: return '—'
    r = h[8]
    return f'≈{r / 1e6:.2f}M' if r >= 1e6 else f'≈{round(r / 1000)} mil'
def picks_for(e, g):
    """Escolhas reais do gestor na jornada g: do live.json se for a jornada dos picks, senão do rivals.json."""
    pk = LV['entries'][e]['picks']
    if pk['event'] == g: return pk
    gg = RV['entries'][e]['gws'][str(g)]
    return dict(event=g, starters=gg['s'], bench=gg['b'], captain=gg['c'], vice=gg['v'], active_chip=gg.get('chip'))
def squad_items(pk, num=False):
    out = []
    for i in pk['starters'] + pk['bench']:
        p = BYID[i]
        tag = 'cap' if i == pk['captain'] else 'vc' if i == pk['vice'] else ('bench' if i in pk['bench'] else '')
        out.append(f'        {{name:{js(p["n"])}, club:{js(TEAMS_APP[p["t"]])}, price:{p["p"] if num else chr(34) + f"£{p['p']:.1f}M" + chr(34)}, tag:"{tag}", start:{"true" if i in pk["starters"] else "false"}, cls:"{p["c"]}"}},\n')
    return ''.join(out)
CHIP = {'wildcard': 'Wildcard', 'freehit': 'Free Hit', 'bboost': 'Bench Boost', '3xc': 'Triple Captain'}
def hist_note(mgr, e, g):
    """Texto da jornada g a partir dos pontos e minutos oficiais de cada jogador (POOL24, espelho validado)."""
    x = LV['entries'][e]; pk = picks_for(e, g); h = next(r for r in x['history'] if r['event'] == g)
    pts, av = h['points'], avg.get(g) or 0
    P = lambda i: (BYID[i]['pts'][g - 1] or 0) if i in BYID and len(BYID[i]['pts']) >= g else 0
    Mn = lambda i: (BYID[i]['mn'][g - 1] or 0) if i in BYID and len(BYID[i]['mn']) >= g else 0
    cap = BYID[pk['captain']]['n']; cp = P(pk['captain'])
    trs = [t for t in RV['entries'][e]['transfers'] if t[0] == g]
    chip = pk.get('active_chip')
    tr_txt = (f'<b>{CHIP[chip]}</b> nesta jornada: plantel refeito ({len(trs)} trocas, sem custo).' if chip in ('wildcard', 'freehit')
              else ('Transferências reais: ' + ', '.join(f'<b>saiu {BYID[t[2]]["n"] if t[2] in BYID else t[2]}, entrou {BYID[t[1]]["n"] if t[1] in BYID else t[1]}</b>' for t in trs) + '.' if trs else 'Sem transferências nesta jornada.'))
    if h['event_transfers_cost']: tr_txt += f' Custo: −{h["event_transfers_cost"]}.'
    if chip in ('bboost', '3xc'): tr_txt += f' Chip: <b>{CHIP[chip]}</b>.'
    xi = pk['starters'] + (pk['bench'] if chip == 'bboost' else [])
    tot = sum(P(i) for i in xi) + cp * (2 if chip == '3xc' else 1)
    top = sorted(xi, key=lambda i: -P(i))[:4]
    who = ' · '.join(f'{BYID[i]["n"]} <b>{P(i)}</b>' for i in top)
    low = [BYID[i]['n'] for i in pk['starters'] if Mn(i) == 0]
    bench = sum(P(i) for i in pk['bench']) if chip != 'bboost' else 0
    diff = pts - av
    t = (f'<b>{pts} pontos</b>, {"acima" if diff > 0 else "abaixo" if diff < 0 else "igual à"} da média ({av}){" — " + ("+" if diff > 0 else "") + str(diff) if diff else ""}. '
         + (f'Validado por soma jogador a jogador: bate com os {pts} da API oficial.' if tot == pts else f'(A soma jogador a jogador dá {tot}: diferença por confirmar.)')
         + f'<br><br>{tr_txt} Capitão: <b>{cap}</b> — {cp} pts (×{3 if chip == "3xc" else 2} = {cp * (3 if chip == "3xc" else 2)}).<br><br>'
         f'<b>Os que mais pontuaram:</b> {who}.')
    if low: t += ' Sem minutos no onze: ' + ', '.join(low) + '.'
    t += f' Pontos no banco: <b>{bench}</b>.'
    if g == LAST and META.get('lastProvisional'): t += f'<br><br><i>Jornada ainda sem o fecho oficial da FPL (bónus por confirmar): pode mexer 1-2 pontos.</i>'
    return t, pts, av, bench
for mgr, arr in (('bruno', 'HISTORY'), ('marco', 'MARCO_HISTORY')):
    e = ENTRY[mgr]
    a, b = block(arr, '[')
    have = [int(x) for x in re.findall(r'\n      gw: ?(\d+),', s[a:b])]
    for g in range(max(have) + 1, LAST + 1):   # todas as jornadas em falta (ex.: uma semana sem atualização)
        note, pts, av, bench = hist_note(mgr, e, g)
        pk = picks_for(e, g)
        label = f'Jornada {g}' + (' (provisória)' if g == LAST and META.get('lastProvisional') else '')
        if mgr == 'marco':
            sq = f'  const MARCO_SQUAD_GW{g} = [\n' + squad_items(pk, True) + '  ];\n'
            prev = s.index(f'  const MARCO_SQUAD_GW{g - 1} = [')
            pe = s.index('\n  ];\n', prev) + len('\n  ];\n')
            s = s[:pe] + sq + s[pe:]
            squad = f'MARCO_SQUAD_GW{g}'
            note_js = '`' + note.replace('`', "'") + '`'
        else:
            squad = '[\n' + squad_items(pk) + '      ]'
            note_js = js(note)
        entry = (f'    {{\n      gw: {g},\n      label: {js(label)},\n      points: {pts},\n      avgPoints: {av},\n      rank: {js(rank_txt(e, g))},\n'
                 f'      benchPoints: {bench},\n      note: {note_js},\n      squad: {squad},\n    }},\n')
        a, b = block(arr, '[')
        s = s[:b - len('  ];\n')] + entry + s[b - len('  ];\n'):]
# a jornada anterior deixa de ser provisória quando a FPL a fecha
for ev in LV['events']:
    if (ev['id'] < LAST or (ev['id'] == LAST and not META.get('lastProvisional'))) and ev.get('finished'):
        s = s.replace(f'label: "Jornada {ev["id"]} (provisória)"', f'label: "Jornada {ev["id"]}"')

if not META.get('lastProvisional'):   # a FPL fechou a jornada: tirar o aviso de provisória do texto
    s = s.replace('<br><br><i>Jornada ainda sem o fecho oficial da FPL (bónus por confirmar): pode mexer 1-2 pontos.</i>', '')

# ---------- detalhe jogador a jogador do Bruno: a entrada da última jornada vem do bloco de dados ----------
if 'GW_DETAIL.push(BRUNO_GW_DETAIL)' not in s:
    a, b = block('GW_DETAIL', '[')
    s = s[:b] + '  if (typeof BRUNO_GW_DETAIL !== \'undefined\' && !GW_DETAIL.some(d => d.gw === BRUNO_GW_DETAIL.gw)) GW_DETAIL.push(BRUNO_GW_DETAIL);   // V53: gerado pelo gen25.py\n' + s[b:]

# ---------- onzes prováveis ----------
m = re.search(r'const PROBABLE_LINEUPS_GW2 = \[.*?\];\n', s)
s = s[:m.start()] + 'const PROBABLE_LINEUPS_GW2 = ' + json.dumps(LU, ensure_ascii=False) + ';\n' + s[m.end():]

# ---------- líderes de xG e jogadores em forma (últimas 3 jornadas, todos os jogadores) ----------
mine = {q['id'] for k in STATE for q in STATE[k]['players']}
L3 = list(range(LAST - 2, LAST + 1))
def pts3(p): return [p['pts'][g - 1] or 0 for g in L3]
xgl = sorted([p for p in POOL if p['c'] != 'gk'], key=lambda p: -(p['xg'] + p['xa']))[:24]
rows = ''.join(f'    {{name:{js(p["n"])}, club:{js(TEAMS_APP[p["t"]])}, price:{p["p"]}, xg:{p["xg"]:.2f}, xa:{p["xa"]:.2f}, pts:{sum(pts3(p))}, mine:{"true" if p["id"] in mine else "false"}}},\n' for p in xgl)
a, b = block('XG_LEADERS', '[')
s = s[:a] + f'  const XG_LEADERS = [\n{rows}  ];\n' + s[b:]
hot = {}
for c, n in (('gk', 3), ('def', 4), ('mid', 6), ('fwd', 4)):
    ps = sorted([p for p in POOL if p['c'] == c and p['m3'] >= 180], key=lambda p: -sum(pts3(p)))[:n]
    lines = []
    for p in ps:
        r = pts3(p); nt = f'{"+".join(map(str, r))} = {sum(r)} pts nas J{L3[0]}-J{L3[-1]}'
        if p['s'] != 'a': nt += f' · {p["nw"] or "estado: " + p["s"]}'
        lines.append(f'      {{name:{js(p["n"])}, club:{js(TEAMS_APP[p["t"]])}, recentGwPoints:{js(r)}, sources:2, inSquad:{"true" if p["id"] in mine else "false"}, note:{js(nt)}}},\n')
    hot[c] = ''.join(lines)
txt = '  const HOT_PLAYERS = {\n' + ''.join(f'    {c}: [\n{hot[c]}    ],\n' for c in ('gk', 'def', 'mid', 'fwd')) + '  };\n'
put_block('HOT_PLAYERS', '{', txt)

# ---------- horários e dificuldade (xgstat) das jornadas além do horizonte, até à J19 (plano de chips, Europa e descanso) ----------
import os
XGS = B / 'research/xgstat.json'   # escrito pelo research_week.py
for name, key in (('LATE_KO', 'ko'), ('LATE_KICKOFF', 'k0'), ('LATE_FIX', 'fix')):
    m = re.search(rf'const {name} = (\{{.*?\}});', s)
    if not m: continue
    D = json.loads(m.group(1))
    for g in list(D):
        if str(g) not in FX: continue
        rows = FX[str(g)]
        if key == 'ko': D[g] = [[f['h'], f['a'], f['kickoff']] for f in sorted(rows, key=lambda f: f['kickoff'])]
        elif key == 'k0': D[g] = min(f['kickoff'] for f in rows)
        elif key == 'fix' and XGS.exists():
            X = json.load(open(XGS, encoding='utf-8'))
            if str(g) in X: D[g] = [[r['team'], r['opp'], 1 if r['home'] else 0, r['d']] for r in X[str(g)]]
    s = s[:m.start()] + f'const {name} = ' + json.dumps(D, separators=(',', ':')) + ';' + s[m.end():]

H.write_text(s, encoding='utf-8', newline='\n')
print(f'J{LAST} → J{NEXT}: tabelas da app atualizadas')
