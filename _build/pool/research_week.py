"""Pesquisa semanal automática (V53, 20 out 2026): descarrega e lê as páginas que alimentam o modelo de pontos
esperados e escreve os ficheiros de _build/research/. Escrito a partir do que funcionou na atualização da J8.
Uso (a partir da raiz): py -X utf8 _build/pool/research_week.py

Escreve:
  research/proj-numeric.json — projeções por jogador e jornada: FPL Form (pp1..pp5 = próximas 5, "se jogar"),
      FPL Copilot (top 25, já com minutos), Onside Arena (próxima jornada), Fantasy Football Pundit (6 jornadas).
  research/odds.json         — odds 1X2, +/-2.5, ambas marcam e vitória sem sofrer (bet365, páginas do kickoff.co.uk).
  research/ticker.json       — dificuldade dos jogos (xgstat, 1-5) + xG projetado a favor/contra (OddAlerts), próximas 6.
  research/xgstat.json       — grelha completa do xgstat (próxima jornada até +14), usada também pelo plano de chips.
O que NÃO faz (é leitura humana, ver notas): opiniões dos especialistas (expert.json/expert_pt.json), a leitura própria
(READING no model25.py) e os onzes prováveis (lineups_rw.py). Se um site mudar de formato, o passo falha com uma
mensagem clara e os ficheiros antigos ficam como estavam."""
import csv, html, json, os, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R = Path(os.environ.get('FPL_RESEARCH_OUT') or ROOT / '_build/research')   # para testar noutra pasta
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36', 'Accept-Language': 'en-GB,en'}
TODAY = time.strftime('%Y-%m-%d')


def get(url, js=False, tries=3):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                b = r.read().decode('utf-8', 'replace')
            return json.loads(b) if js else b
        except Exception as e:
            if '429' in str(e):   # o xgstat recusa o urllib (429) mas aceita o curl com cabeçalhos de navegador
                import subprocess
                r = subprocess.run(['curl', '-s', '-L', '--max-time', '90', '-A', UA['User-Agent'], '-H', 'Accept: text/html', '-H', 'Accept-Language: en-GB,en', url],
                                   capture_output=True)
                b = r.stdout.decode('utf-8', 'replace')
                if r.returncode == 0 and len(b) > 50000: return json.loads(b) if js else b
            if k == tries - 1: raise RuntimeError(f'falhou {url}: {e}')
            time.sleep((30 if "429" in str(e) else 5) * (k + 1))


def text(page):
    t = re.sub(r'<script.*?</script>|<style.*?</style>', '', page, flags=re.S)
    t = re.sub(r'<[^>]+>', '|', t); t = html.unescape(t); t = re.sub(r'\s+', ' ', t)
    return re.sub(r'\|( ?\|)+', '|', t)


boot = get(f'https://fantasy.premierleague.com/api/bootstrap-static/?t={int(time.time())}', True)
NEXT = next(e['id'] for e in boot['events'] if e['is_next'])
G5 = [str(g) for g in range(NEXT, NEXT + 5)]
CODE = {e['code']: e['id'] for e in boot['elements']}
NAME = {str(e['id']): f"{e['first_name']} {e['second_name']}" for e in boot['elements']}
SHORT = {t['short_name']: t['id'] for t in boot['teams']}
TEAMNAME = {int(r['id']): r['name'] for r in csv.DictReader(open(ROOT / '_build/mirror/teams.csv', encoding='utf-8'))}
fx = get(f'https://fantasy.premierleague.com/api/fixtures/?event={NEXT}&t={int(time.time())}', True)
print(f'J{NEXT}: {len(fx)} jogos')

# ---------- projeções ----------
P = {}
s = get('https://www.fplform.com/fpl-predicted-points')
for pid, row in re.findall(r"<tr class='(\d+) [^']*'>(.*?)</tr>", s, re.S):
    pp = {int(k): float(v) for k, v in re.findall(r"class='pp pp(\d) [^']*'>([\d.]+)<", row)}
    pr = re.search(r"class='prob[^']*'>([\d.]+)<", row)
    P.setdefault(pid, {})['fplform'] = {str(NEXT - 1 + k): v for k, v in pp.items() if k <= 5}
    P[pid]['fplform_prob_appearing'] = float(pr.group(1)) if pr else None
assert len(P) > 300, 'FPL Form: formato mudou'
s = get('https://www.fantasyfootballpundit.com/fpl-points-predictor/').replace('\\"', '"')
n = 0
for g, c, pp in re.findall(r'\{"gw":(\d+),"player_code":(\d+),"web_name":"[^"]*".*?"predicted_points":"([\d.]+)"', s):
    i = CODE.get(int(c))
    if i and g in G5: P.setdefault(str(i), {}).setdefault('pundit', {})[g] = round(float(pp), 1); n += 1
assert n > 500, 'Pundit: formato mudou'
s = get('https://fplcopilot.com/expected-points').replace('\\"', '"')
for i, gws in re.findall(r'\{"id":(\d+),"name":"[^"]+","position":"\w+","team":"\w+".*?"gameweeks":(\[[^\]]*\])', s):
    P.setdefault(i, {})['fplcopilot'] = {str(x['gw']): round(x['points'], 1) for x in json.loads(gws) if str(x['gw']) in G5}
s = get(f'https://onsidearena.com/fpl/predicted-points?gw={NEXT}').replace('\\"', '"')
for i, xp in re.findall(r'\{"id":(\d+),"name":"[^"]+","team":"\w+","pos":"\w+","price":[\d.]+,"owned":[\d.]+,"xp":([\d.]+)', s):
    P.setdefault(i, {})['onside'] = {str(NEXT): round(float(xp), 1)}
for i in P: P[i]['name'] = NAME.get(i, i)
src = [dict(key='fplform', url='https://www.fplform.com/fpl-predicted-points', page_date=f'lido a {TODAY} (J{G5[0]}-J{G5[-1]}; pontos se jogar)'),
       dict(key='fplcopilot', url='https://fplcopilot.com/expected-points', page_date=f'lido a {TODAY} (top 25, já com minutos)'),
       dict(key='onside', url=f'https://onsidearena.com/fpl/predicted-points?gw={NEXT}', page_date=f'lido a {TODAY} (J{NEXT})'),
       dict(key='pundit', url='https://www.fantasyfootballpundit.com/fpl-points-predictor/', page_date=f'lido a {TODAY} (odds + estimativa)')]
json.dump(dict(sources=src, players=P), open(R / 'proj-numeric.json', 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=0)
print('projeções:', len(P), 'jogadores;', sum('fplcopilot' in v for v in P.values()), 'Copilot;', sum('onside' in v for v in P.values()), 'Onside')

# ---------- odds (bet365 no kickoff.co.uk) ----------
idx = get('https://www.kickoff.co.uk/english-premier-league-predictions-stats-odds/')
slugs = set(re.findall(r'english-premier-league-predictions-stats-odds/([a-z0-9-]+-vs-[a-z0-9-]+)/', idx))
def slug_name(n): return re.sub(r'[^a-z0-9]+', '-', n.lower().replace("'", '').replace('&', 'and')).strip('-')
ALIAS = {"nott'm forest": 'nottingham-forest', 'man utd': 'man-united', 'spurs': 'tottenham', 'coventry city': 'coventry', 'hull city': 'hull',
         'ipswich town': 'ipswich', 'leeds': 'leeds-united'}
matches = []
for f in fx:
    h, a = TEAMNAME[f['team_h']], TEAMNAME[f['team_a']]
    sl = f"{ALIAS.get(h.lower(), slug_name(h))}-vs-{ALIAS.get(a.lower(), slug_name(a))}"
    if sl not in slugs: print('  sem página de odds:', sl); continue
    seg = re.sub(r'\s+', ' ', text(get(f'https://www.kickoff.co.uk/english-premier-league-predictions-stats-odds/{sl}/')).replace('|', ' '))
    i = seg.find('Predictions Add ')
    if i < 0: print('  página sem tabela de odds:', sl); continue
    seg = seg[i:i + 3000]
    dec = lambda x: round(1 + int(x.split('/')[0]) / int(x.split('/')[1]), 2) if '/' in x else float(x)   # a página pode vir em odds fracionárias
    od = re.findall(r"([A-Za-z' .]+?) (\d+) % ([\d.]+(?:/\d+)?)", seg)
    if len(od) < 3: print('  odds 1X2 por ler:', sl, seg[:120]); continue
    g = lambda lab: (lambda m: dec(m.group(1)) if m else None)(re.search(re.escape(lab) + r' \d+ % ([\d.]+(?:/\d+)?)', seg))
    wn = [dec(x) for x in re.findall(r'win to nil \d+ % ([\d.]+(?:/\d+)?)', seg)]
    matches.append(dict(home=h, away=a, odds=dict(home=dec(od[0][2]), draw=dec(od[1][2]), away=dec(od[2][2])), over25=g('Over 2.5 Goals'), under25=g('Under 2.5 Goals'),
                        btts_yes=g('BTTS - Yes'), btts_no=g('BTTS - No'), cs_home=None, cs_away=None, win_to_nil_home=wn[0] if wn else None,
                        win_to_nil_away=wn[1] if len(wn) > 1 else None, source='bet365 via kickoff.co.uk', url=f'https://www.kickoff.co.uk/english-premier-league-predictions-stats-odds/{sl}/', date=TODAY))
    time.sleep(1)
assert len(matches) >= 8, 'odds: menos de 8 jogos lidos'
od = json.load(open(R / 'odds.json', encoding='utf-8'))
od.update(_meta=dict(collected=TODAY, gameweek=NEXT, notes=[f'Odds decimais da bet365 nas páginas de cada jogo do kickoff.co.uk, lidas a {TODAY}.', 'cs_home/cs_away sem preço direto; win_to_nil como aproximação.']),
          matches=matches, scorers=[], scorers_model=[])
json.dump(od, open(R / 'odds.json', 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print('odds:', len(matches), 'jogos')

# ---------- dificuldade: xgstat (grelha) + OddAlerts (xG projetado) ----------
def curl_get(url):   # o xgstat só responde bem ao curl com cabeçalhos de navegador
    import subprocess
    r = subprocess.run(['curl', '-s', '-L', '--max-time', '90', '-A', UA['User-Agent'], '-H', 'Accept: text/html', '-H', 'Accept-Language: en-GB,en', url], capture_output=True)
    return r.stdout.decode('utf-8', 'replace')
t = text(curl_get('https://www.xgstat.com/competitions/premier-league/fixtures/fixture-difficulty'))
upd = re.search(r'Ratings updated\|?(\d+ \w+ \d{4})', t)
t0 = t.find('|Team|GW')   # a grelha começa no cabeçalho "Team|GW…" e acaba na legenda seguinte
t = t[t0:]; t1 = t.find('|Easier|') if t.find('|Easier|') > 0 else t.find('|How fixture difficulty')
gws = [int(x) for x in re.findall(r'\|GW(\d+)(?=\|)', t[:t.find('|', t.find('|GW') + 1) + 400])]
gws = sorted(set(gws)); first, last = gws[0], max(gws)
tok = [x for x in t[t.find(f'|GW{last}|') + len(f'|GW{last}|'):t1].split('|') if x and x not in '▲▼']
tok = tok[:tok.index('·')] if '·' in tok else tok
X, k = {}, 0
while k < len(tok) and (tok[k] in SHORT or tok[k] == 'NOT') and len(X.get(str(first), [])) < 20:   # 20 linhas de equipas; o resto é a legenda
    tm = SHORT.get(tok[k]) or {'NOT': SHORT.get('NFO')}.get(tok[k]); k += 1
    for g in range(first, last + 1):
        X.setdefault(str(g), []).append(dict(team=tm, opp=SHORT.get(tok[k + 1]), home=tok[k] == 'H', d=float(tok[k + 2]))); k += 3
assert all(len(v) == 20 for v in X.values()), 'xgstat: grelha incompleta'
json.dump(X, open(R / 'xgstat.json', 'w', encoding='utf-8', newline='\n'), indent=0)
t = text(get('https://www.oddalerts.com/fpl/fixture-ticker')).replace('–', '-')
tok = [x.strip() for x in t[t.find('|Clean sheet|') + 13:].split('|') if x.strip()]
TN = {v: k for k, v in TEAMNAME.items()}
TN.update({'Tottenham': TN.get('Spurs'), 'Nottingham Forest': TN.get("Nott'm Forest"), 'Coventry': TN.get('Coventry City'), 'Hull': TN.get('Hull City'),
           'Ipswich': TN.get('Ipswich Town'), 'Leeds United': TN.get('Leeds'), 'Newcastle United': TN.get('Newcastle'), 'Manchester United': TN.get('Man Utd'), 'Manchester City': TN.get('Man City')})
O, k, n = {}, 0, 0
while k < len(tok) and n < 20:
    tm = TN.get(tok[k]); assert tm, f'OddAlerts: equipa desconhecida {tok[k]}'
    k += 1
    while k < len(tok) and re.match(r'\w{3} \((H|A)\) [\d.]+-[\d.]+', tok[k]):
        m = re.match(r'(\w{3}) \((H|A)\) ([\d.]+)-([\d.]+)', tok[k]); k += 1
        g = str(NEXT + sum(1 for r in O.values() for x in r if x['team'] == tm))
        O.setdefault(g, []).append(dict(team=tm, opp=SHORT.get(m.group(1)), home=m.group(2) == 'H', xgf=float(m.group(3)), xga=float(m.group(4))))
    k += 3; n += 1
FX = json.load(open(ROOT / '_build/data/fixtures.json', encoding='utf-8'))
TK = json.load(open(R / 'ticker.json', encoding='utf-8'))
fixtures = {}
for g in range(NEXT, NEXT + 6):
    rows = []
    for f in FX[str(g)]:
        for team, opp, home, fdr in ((f['h'], f['a'], True, f['dh']), (f['a'], f['h'], False, f['da'])):
            xg = next((r['d'] for r in X.get(str(g), []) if r['team'] == team and r['opp'] == opp and r['home'] == home), None)
            oa = next((r for r in O.get(str(g), []) if r['team'] == team and r['opp'] == opp and r['home'] == home), None)
            rows.append(dict(team=team, opp=opp, home=home, fpl_fdr=fdr, ratings=dict(xgstat=xg, oddalerts_xgf=oa and oa['xgf'], oddalerts_xga=oa and oa['xga'])))
    fixtures[str(g)] = rows
TK['fixtures'] = fixtures
TK['sources'] = [dict(key='xgstat', url='https://www.xgstat.com/competitions/premier-league/fixtures/fixture-difficulty', date=f"{TODAY} (página: 'Ratings updated {upd.group(1) if upd else '?'}')"),
                 dict(key='oddalerts', url='https://www.oddalerts.com/fpl/fixture-ticker', date=f'{TODAY} (xG projetado a favor-contra, do mercado de apostas)')] + [x for x in TK['sources'] if x['key'] not in ('xgstat', 'oddalerts')]
json.dump(TK, open(R / 'ticker.json', 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=0)
miss = sum(1 for g in fixtures.values() for r in g if r['ratings']['xgstat'] is None or r['ratings']['oddalerts_xgf'] is None)
print(f'ticker: J{NEXT}-J{NEXT + 5}, {miss} jogos sem as duas fontes; xgstat atualizado a {upd.group(1) if upd else "?"}')
