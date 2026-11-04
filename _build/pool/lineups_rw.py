"""Onzes prováveis da próxima jornada a partir do RotoWire (rotowire.com/soccer/lineups.php), cruzados com o estado
oficial da API da FPL. Escreve _build/research/lineups.json no formato de PROBABLE_LINEUPS_GW2 da app.
Uso (a partir da raiz): py -X utf8 _build/pool/lineups_rw.py
Os nomes são passados para os nomes do POOL24 do index.html (para a app os reconhecer); o RotoWire é UMA fonte:
cada onze diz isso no campo 'confidence' e as dúvidas ficam marcadas com "DÚVIDA" (é o que os avisos da app procuram)."""
import html, json, re, sys, time, unicodedata, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from datetime import timedelta

ROOT = Path(__file__).resolve().parents[2]
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'}


def get(url, js=False):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        b = r.read().decode('utf-8', 'replace')
    return json.loads(b) if js else b


def fold(s):
    s = s.translate(str.maketrans({'ø': 'o', 'Ø': 'O', 'ß': 'ss', 'ı': 'i', 'ł': 'l', 'Ł': 'L', 'æ': 'ae', 'đ': 'd'}))
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c)).lower().replace('-', ' ').replace("'", '')


boot = get(f'https://fantasy.premierleague.com/api/bootstrap-static/?t={int(time.time())}', True)
NEXT = next(e['id'] for e in boot['events'] if e['is_next'])
CUR = next((e['id'] for e in boot['events'] if e['is_current'] and not e['finished']), None)
fx = [f for g in ([CUR] if CUR else []) + [NEXT] for f in get(f'https://fantasy.premierleague.com/api/fixtures/?event={g}&t={int(time.time())}', True)]
SHORT = {t['short_name']: t['id'] for t in boot['teams']}
SHORT.update({'NOT': SHORT.get('NFO'), 'BRI': SHORT.get('BHA')})
# nomes da app (POOL24 do index.html), por id
s = (ROOT / 'index.html').read_text(encoding='utf-8')
i0 = s.index('const POOL24 = [\n') + len('const POOL24 = [\n')
appname = {r[0]: r[1] for r in (json.loads(l.rstrip(',')) for l in s[i0:s.index('\n]', i0)].split('\n'))}
EL = boot['elements']
byteam = {}
for e in EL:
    byteam.setdefault(e['team'], []).append(e)


ALIAS = {'Chema': 'Andrés', 'Y. Yarmolyuk': 'Yarmoliuk'}   # alcunhas do RotoWire → web_name da FPL


def match(team, nm):
    """RotoWire escreve 'C. Walton', 'Leif Davis', 'Gabriel'… → jogador da FPL dessa equipa."""
    nm = ALIAS.get(nm, nm)
    f = fold(nm.replace('.', ' ')).split()
    best = None
    for e in byteam.get(team, []):
        full = fold(e['first_name'] + ' ' + e['second_name']).split()
        web = fold(e['web_name']).split()
        sc = 0
        if f[-1] in full or f[-1] in web:
            sc = 2
            if len(f) > 1 and full and (f[0] == full[0] or (len(f[0]) == 1 and full[0].startswith(f[0]))):
                sc = 3
        elif ' '.join(f) == ' '.join(web):
            sc = 3
        if sc and e['minutes'] > 0:
            sc += 0.5
        if sc and (best is None or sc > best[0]):
            best = (sc, e)
    return best[1] if best else None


page = get('https://www.rotowire.com/soccer/lineups.php')
t = re.sub(r'<script.*?</script>|<style.*?</style>', '', page, flags=re.S)
t = re.sub(r'<[^>]+>', '|', t); t = html.unescape(t); t = re.sub(r'\s+', ' ', t); t = re.sub(r'\|( ?\|)+', '|', t)
hdr = re.findall(r'\|(\w+ \d+)\| ([\d:]+ [AP]M ET)\|Tickets\|Alerts\|(\w+)\|(\w+)\|', t)
tok = [x.strip() for x in t.split('|') if x.strip()]
POS = {'GK', 'DL', 'DC', 'DR', 'DMC', 'MC', 'ML', 'MR', 'AML', 'AMC', 'AMR', 'FW', 'DML', 'DMR', 'WBL', 'WBR', 'FWL', 'FWR'}
sides = []
k = 0
while k < len(tok):
    if tok[k] in ('Predicted Lineup', 'Confirmed Lineup'):
        kind = tok[k]; xi = []; j = k + 1
        while j < len(tok) and tok[j] in POS:
            q = None; p, n = tok[j], tok[j + 1]; j += 2
            if j < len(tok) and tok[j] in ('QUES', 'OUT', 'SUS'):
                q = tok[j]; j += 1
            xi.append((p, n, q))
        inj = []
        if j < len(tok) and tok[j] == 'Injuries':
            j += 1
            while j + 2 < len(tok) and tok[j + 2] in ('QUES', 'OUT', 'SUS'):
                inj.append((tok[j + 1], tok[j + 2])); j += 3
        sides.append((kind, xi, inj)); k = j
    else:
        k += 1
assert len(sides) == 2 * len(hdr), (len(sides), len(hdr))

def lisbon(dt):
    """Hora de Lisboa (sem tzdata no Windows): UTC+1 do último domingo de março ao último domingo de outubro, 01:00 UTC."""
    def last_sun(m):
        d = datetime(dt.year, m, 31 if m in (3, 10) else 30, 1, tzinfo=timezone.utc)
        return d - timedelta(days=(d.weekday() + 1) % 7)
    return dt + timedelta(hours=1 if last_sun(3) <= dt < last_sun(10) else 0)
DIAS = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
MES = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
ST = {'i': 'lesionado', 'd': 'dúvida', 's': 'castigado', 'u': 'indisponível', 'n': 'indisponível'}
out, miss = [], []
for gi, (_, _, ha, aa) in enumerate(hdr):
    h, a = SHORT[ha], SHORT[aa]
    f = next(x for x in fx if x['team_h'] == h and x['team_a'] == a)
    if gi == 0: NEXT = f['event']
    ko = datetime.strptime(f['kickoff_time'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc); ko = lisbon(ko)
    when = f'{DIAS[ko.weekday()]} {ko.day} {MES[ko.month - 1]}, {ko:%H:%M}'
    entry = dict(when=when, h=h, a=a)
    for side, team in (('home', h), ('away', a)):
        kind, xi, inj = sides[2 * gi + (side == 'away')]
        lines, cnt = [], {'d': 0, 'm': 0, 'am': 0, 'f': 0}
        for p, n, q in xi:
            e = match(team, n)
            grp = 'GK' if p == 'GK' else 'DEF' if p[0] == 'D' and p != 'DMC' or p.startswith('WB') else 'FWD' if p.startswith('FW') else 'MID'
            if p != 'GK':
                cnt['d' if grp == 'DEF' else 'f' if grp == 'FWD' else 'am' if p.startswith('AM') else 'm'] += 1
            name = appname.get(e['id'], f"{e['first_name']} {e['second_name']}") if e else n
            if not e:
                miss.append((team, n))
            off = ''
            if e and e['status'] != 'a':
                off = f"{ST.get(e['status'], e['status'])}{' ' + str(e['chance_of_playing_next_round']) + '%' if e['chance_of_playing_next_round'] is not None else ''} na FPL{': ' + e['news'] if e['news'] else ''}"
            if q or (e and e['status'] in ('i', 's', 'u')):
                note = 'DÚVIDA: ' + (off or 'o RotoWire marca-o como dúvida')
            elif e and e['status'] == 'd':
                note = 'DÚVIDA: ' + off
            else:
                note = 'titular provável' + (' (confirmado)' if kind.startswith('Confirmed') else '')
            lines.append(f"{grp} — {name} — {note}")
        form = '-'.join(str(v) for v in (cnt['d'], cnt['m'], cnt['am'], cnt['f']) if v)
        bench = '; '.join(f"{(appname.get(m['id']) if (m := match(team, n)) else n)} ({ {'QUES': 'dúvida', 'OUT': 'fora', 'SUS': 'castigado'}[q] })" for n, q in inj) or 'Sem lesões nem castigos conhecidos.'
        entry[side] = dict(formation=form, xi=lines, bench='Lesões e dúvidas: ' + bench,
                           confidence=('Confirmado.' if kind.startswith('Confirmed') else f'Previsão do RotoWire lida a {lisbon(datetime.now(timezone.utc)):%d/%m %H:%M}, cruzada com o estado oficial da FPL. Uma só fonte de onzes: confirmar antes do deadline.'),
                           sources='RotoWire (rotowire.com/soccer/lineups.php); estado e notícias oficiais da API da FPL')
    out.append(entry)
json.dump(out, open(ROOT / '_build/research/lineups.json', 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(f'J{NEXT}: {len(out)} jogos; nomes por reconhecer: {miss}')
