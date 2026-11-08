"""V58 (8 nov 2026): disponibilidade prevista — lesões (jornada provável de regresso) e castigos (amarelos e vermelhos).

Entradas
- live.json → elements: estado, chance, notícia, data da notícia (news_added), amarelos, vermelhos, minutos (API oficial).
- _build/mirror/playerstats.csv → amarelos e minutos acumulados por jornada (para saber em que jornada chegou a cada limite).
- _build/data/fixtures.json → calendário oficial (início de cada jogo, jogos acabados).
- _build/research/injuries.json → "durations" (duração típica por tipo de lesão, com fonte) e "manual" (pesquisa na web:
  conferências de imprensa, páginas de lesões — com fonte e data). Este script reescreve só "players" e "updated".
- _build/research/discipline.json → regras de castigo 2026/27 (com fonte). Este script reescreve só "players".

Modelo de lesão (o mesmo que a app usa, em JS, para refazer as contas com a data de hoje e o live.json):
  dias até voltar R = mínimo + X, X log-normal com mediana (normal − mínimo) e percentil 90 (máximo − mínimo).
  Ponto de partida = data da lesão (pesquisa) ou data da notícia da FPL. Se o treinador (ou a FPL, "Expected back …")
  der um prazo, esse prazo manda. Condicionado a ainda não ter voltado: P(R ≤ d | R > dias passados).
  Disponível na jornada g = R ≤ (início do 1.º jogo da equipa na jornada g − 1 dia).
  Dúvida (d) com chance c%: c na jornada seguinte; depois a falta de c desaparece 65% por jornada.
  Para os pontos esperados, a 1.ª jornada depois de voltar conta 70% dos minutos.
Uso: py -X utf8 _build/pool/disponibilidade.py   (Linux: python3) — escreve os dois JSON e mostra um resumo.
O gen25.py chama compute() para pôr a disponibilidade nos pontos esperados e o AVAIL_PRED no bloco de dados."""
import csv, json, math, re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

BD = Path(__file__).resolve().parents[1]
ROOT = BD.parent
R = BD / 'research'
MON = {m: i + 1 for i, m in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])}
TYPE_PT = {'hamstring': 'posterior da coxa', 'thigh': 'coxa', 'calf': 'gémeo', 'groin': 'virilha/adutor', 'ankle': 'tornozelo',
           'knee': 'joelho', 'knee_ligament': 'ligamento do joelho', 'acl': 'ligamento cruzado', 'achilles': 'tendão de Aquiles',
           'foot': 'pé', 'fracture': 'fratura', 'hip': 'anca', 'back': 'costas', 'head': 'cabeça/concussão', 'shin': 'canela',
           'shoulder': 'ombro', 'illness': 'doença', 'knock': 'pancada', 'muscle': 'muscular', 'unknown': 'não especificada'}
TYPE_RX = [('acl', r'acl|cruciate'), ('achilles', r'achilles'), ('fracture', r'fractur|broken|metatarsal'),
           ('knee_ligament', r'ligament|mcl'), ('hamstring', r'hamstring'), ('calf', r'calf'), ('groin', r'groin|adductor'),
           ('thigh', r'thigh|quad'), ('ankle', r'ankle'), ('knee', r'knee'), ('foot', r'foot|toe|heel'), ('hip', r'hip'),
           ('back', r'back'), ('head', r'head|concussion'), ('shin', r'shin'), ('shoulder', r'shoulder'),
           ('illness', r'illness|\bill\b|virus|sick'), ('knock', r'knock'), ('muscle', r'muscle|muscular')]


def classify(news):
    n = re.sub(r'expected back.*|unknown return.*|\d+% chance.*', '', (news or '').lower())
    for k, rx in TYPE_RX:
        if re.search(rx, n): return k
    return 'unknown'


def parse_iso(s):
    if not s: return None
    s = s.replace('Z', '+00:00')
    try: d = datetime.fromisoformat(s)
    except ValueError: d = datetime.fromisoformat(s[:10])
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def news_date(news, ref):
    """'... until 5 Dec' / 'Expected back 22 Nov' → data (ano a seguir a ref)."""
    m = re.search(r'(?:until|back)\s+(\d{1,2})\s+([A-Z][a-z]{2})', news or '')
    if not m or m.group(2) not in MON: return None
    d = datetime(ref.year, MON[m.group(2)], int(m.group(1)), tzinfo=timezone.utc)
    if d < ref - timedelta(days=120): d = d.replace(year=ref.year + 1)
    return d


def phi(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def cdf(x, mn, md, mx):
    """P(R ≤ x) com R = mn + log-normal (mediana md−mn, p90 mx−mn), em dias."""
    if x <= mn: return 0.0
    a, b = max(0.5, md - mn), max(1.0, mx - mn)
    sig = max(0.2, math.log(max(b / a, 1.05)) / 1.2816)
    return phi((math.log(x - mn) - math.log(a)) / sig)


def load():
    L = json.load(open(ROOT / 'live.json', encoding='utf-8'))
    FX = json.load(open(BD / 'data' / 'fixtures.json', encoding='utf-8'))
    INJ = json.load(open(R / 'injuries.json', encoding='utf-8'))
    DIS = json.load(open(R / 'discipline.json', encoding='utf-8'))
    snaps = defaultdict(dict)
    for r in csv.DictReader(open(BD / 'mirror' / 'playerstats.csv', encoding='utf-8')):
        snaps[int(r['id'])][int(r['gw'])] = (int(float(r['yellow_cards'] or 0)), int(float(r['minutes'] or 0)), r.get('web_name') or r['second_name'])
    return L, FX, INJ, DIS, snaps


def team_fixtures(FX):
    tf = defaultdict(list)   # equipa → [(início, jornada, acabou)] por ordem
    for g, l in FX.items():
        if not g.isdigit(): continue
        for f in l:
            for t in (f['h'], f['a']): tf[t].append((parse_iso(f['kickoff']), int(g), bool(f['finished'])))
    for t in tf: tf[t].sort()
    return tf


def inj_params(e, man, now, DUR):
    """Parâmetros da curva de regresso (dias desde t0) para um jogador lesionado/em dúvida."""
    st, ch, news, nadd = e['st'], e['ch'], e['news'], e['nadd']
    ty = (man or {}).get('type') or classify(news)
    if ty not in DUR: ty = 'unknown'
    d = DUR[ty]
    t0 = parse_iso((man or {}).get('injury_date')) or parse_iso(nadd) or now
    src = 'tipo'
    mn, md, mx = d['min'], d['typ'], d['max']
    tl = (man or {}).get('timeline') or {}
    eb, lb = parse_iso(tl.get('back_date_earliest')), parse_iso(tl.get('back_date_latest'))
    if tl.get('min_days') is not None and not eb:
        base = parse_iso((man or {}).get('source_date')) or t0
        eb = base + timedelta(days=tl['min_days']); lb = base + timedelta(days=tl.get('max_days') or tl['min_days'])
    fpl_back = news_date(news, t0) if 'back' in (news or '').lower() else None
    if eb and not lb:
        # prazo só com o mínimo ("não volta antes de …"): a curva do tipo de lesão, mas nunca antes dessa data
        src = 'treinador' if tl.get('from_manager') else 'notícia'
        lo = max(0.0, (eb - t0).total_seconds() / 86400 - 2)
        mn = max(mn, lo); md = max(md, mn + 4); mx = max(mx, md + 14)
    elif eb or fpl_back:
        e1, l1 = (eb, lb or eb) if eb else (fpl_back, fpl_back)
        src = 'treinador' if eb and tl.get('from_manager') else ('notícia' if eb else 'FPL')
        mn = max(0.0, (e1 - t0).total_seconds() / 86400 - 3)
        md = max(mn + 1, ((e1 - t0) + (l1 - e1) / 2).total_seconds() / 86400)
        mx = max(md + 2, (l1 - t0).total_seconds() / 86400 + 7)
    el = (now - t0).total_seconds() / 86400
    late = False
    if st == 'i' and 1 - cdf(el, mn, md, mx) < 0.15 and src == 'tipo':
        # já passou o tempo normal desta lesão (e a FPL continua sem data): é mais grave do que o normal —
        # recomeça a contar a partir de hoje, com um tempo que cresce com o que já esteve parado
        t0, mn, md, mx, late = now, 3, max(10.0, 0.5 * el), max(35.0, 1.5 * el), True
    return dict(ty=ty, t0=t0.strftime('%Y-%m-%dT%H:%M:%SZ'), mn=round(mn, 1), md=round(md, 1), mx=round(mx, 1), src=src, late=late)


def inj_curve(e, P, kos, now):
    """[(jornada, P(disponível))] para as jornadas pedidas (kos = {jornada: início do 1.º jogo da equipa})."""
    st, ch = e['st'], e['ch']
    out = {}
    up = [g for g in sorted(kos) if kos[g] and kos[g] > now]
    if st == 'd' or (st == 'i' and ch not in (None, 0)):
        c = (ch if ch is not None else 75) / 100
        for k, g in enumerate(up): out[g] = 1 - (1 - c) * (0.35 ** k)
        for g in kos:
            if g not in out: out[g] = c
        return out
    t0 = parse_iso(P['t0']); el = max(0.0, (now - t0).total_seconds() / 86400)
    s = max(1e-6, 1 - cdf(el, P['mn'], P['md'], P['mx']))
    for g, k in kos.items():
        if not k or k <= now: out[g] = 0.0; continue
        d = (k - timedelta(days=1) - t0).total_seconds() / 86400
        out[g] = max(0.0, min(1.0, (cdf(d, P['mn'], P['md'], P['mx']) - (1 - s)) / s))
    return out


def ep_factor(gws, av, prev=0.0):
    """Fator dos pontos esperados: na 1.ª jornada depois de voltar conta 70% dos minutos."""
    f = {}
    for g in gws:
        a = av.get(g, 1.0)
        f[g] = prev + max(0.0, a - prev) * 0.7 if a > prev else a
        prev = a
    return f


def compute(NEXT=None, now=None, write=True, verbose=False):
    L, FX, INJ, DIS, snaps = load()
    now = now or datetime.now(timezone.utc)
    DUR = INJ['durations']
    tf = team_fixtures(FX)
    # jornadas: a próxima com jogos por acabar e mais 7
    if NEXT is None: NEXT = min(int(g) for g, l in FX.items() if g.isdigit() and not all(f['finished'] for f in l))
    GWS = list(range(NEXT, min(39, NEXT + 8)))
    upcoming = [g for g in GWS if any(k > now for t in tf for k, gg, _ in tf[t] if gg == g)]
    SHOW = [g for g in upcoming if min((k for t in tf for k, gg, _ in tf[t] if gg == g), default=now) > now][:6]
    teamko = {t: {g: min([k for k, gg, _ in tf[t] if gg == g], default=None) for g in GWS} for t in tf}
    man = INJ.get('manual', {})
    # equipa de cada jogador (bloco de dados não está aqui: usar o espelho players.csv)
    teams = {r['code']: int(r['id']) for r in csv.DictReader(open(BD / 'mirror' / 'teams.csv', encoding='utf-8'))}
    pinfo = {int(r['player_id']): r for r in csv.DictReader(open(BD / 'mirror' / 'players.csv', encoding='utf-8'))}
    POSMAP = {'Goalkeeper': 'gk', 'Defender': 'def', 'Midfielder': 'mid', 'Forward': 'fwd'}
    LAST = NEXT - 1
    out_p, inj_json, dis_json, cards = {}, {}, {}, {}
    thr = DIS['yellow']['thresholds']
    PRIOR = {'gk': 0.04, 'def': 0.17, 'mid': 0.17, 'fwd': 0.12}
    for sid, a in L['elements'].items():
        pid = int(sid)
        info = pinfo.get(pid)
        if not info: continue
        team = teams.get(info['team_code']); pos = POSMAP.get(info['position'])
        if not team or not pos: continue
        e = dict(st=a[1], ch=a[2], news=a[3] or '', nadd=a[9] if len(a) > 9 else None,
                 yc=a[10] if len(a) > 10 else 0, rc=a[11] if len(a) > 11 else 0, mins=a[12] if len(a) > 12 else 0)
        sn = snaps.get(pid, {})
        name = (sn.get(max(sn)) or (0, 0, sid))[2] if sn else sid
        kos = teamko.get(team, {})
        rec = {}
        av = {g: 1.0 for g in GWS}
        # ---------- lesões ----------
        mi = man.get(sid)
        if e['st'] in ('i', 'd') or (mi and e['st'] != 'a' and e['st'] != 's'):
            P = inj_params(e, mi, now, DUR)
            cur = inj_curve(e, P, kos, now)
            for g in GWS: av[g] = min(av[g], cur.get(g, 1.0))
            show = [g for g in SHOW if g in cur]
            ret = next((g for g in show if cur[g] >= 0.5), None)
            rec['inj'] = dict(P, st=e['st'], ch=e['ch'], news=e['news'], nadd=e['nadd'])
            if mi: rec['web'] = dict(s=mi.get('summary_pt'), u=mi.get('source'), d=mi.get('source_date'),
                                     fm=bool((mi.get('timeline') or {}).get('from_manager')))
            inj_json[sid] = dict(name=name, team=team, status=e['st'], chance=e['ch'], news=e['news'], news_added=e['nadd'],
                                 source='API oficial da FPL (bootstrap-static, via live.json)',
                                 type=P['ty'], type_pt=TYPE_PT.get(P['ty'], P['ty']), basis=P['src'], late=P['late'],
                                 model_days=dict(min=P['mn'], typical=P['md'], max=P['mx'], since=P['t0']),
                                 web=mi, prob={('J%d' % g): round(cur[g], 2) for g in show},
                                 likely_return=('J%d' % ret) if ret else None,
                                 likely_return_p=round(cur[ret], 2) if ret else None)
        elif e['st'] in ('u', 'n'):
            for g in GWS: av[g] = 0.0
            rec['out'] = e['news']
        # ---------- castigos: oficiais (FPL "Suspended until …") ----------
        ban_gws = set()
        if e['st'] == 's':
            until = news_date(e['news'], now)
            fut_k = sorted((k, g) for g, k in kos.items() if k and k > now)
            for k, g in fut_k:
                if (until and k < until) or (not until and (k, g) == fut_k[0]): ban_gws.add(g)
            rec['sus'] = dict(until=until.strftime('%Y-%m-%d') if until else None, news=e['news'])
        # castigo por amarelos ainda por cumprir (o limite foi atingido e a FPL ainda não marcou)
        fx_t = tf.get(team, [])
        played = [x for x in fx_t if x[2] or x[0] <= now - timedelta(hours=2)]
        nxt = [x for x in fx_t if not (x[2] or x[0] <= now - timedelta(hours=2))]
        cum = {g: v[0] for g, v in sn.items() if g <= LAST}
        cum[max(cum) + 1 if cum else LAST + 1] = e['yc']
        if e['st'] != 's':
            for t in thr:
                if not t['ban'] or e['yc'] < t['n']: continue
                gk = min((g for g, v in sorted(cum.items()) if v >= t['n']), default=None)
                if gk is None: continue
                idx = sum(1 for x in played if x[1] <= gk)        # jogo da equipa em que chegou ao limite
                if idx > t['cutoff_matches']: continue
                after = [x for x in played if x[1] > gk]
                left = t['ban'] - len(after)
                if left > 0:
                    for x in nxt[:left]: ban_gws.add(x[1])
                    rec['pend'] = dict(n=t['n'], gw=gk, left=left, gws=[x[1] for x in nxt[:left]])
        for g in ban_gws: av[g] = 0.0
        # ---------- risco de castigo por amarelos ----------
        mins3 = (sn.get(LAST, (0, 0))[1] - sn.get(LAST - 3, (0, 0))[1]) if sn else 0
        share = max(0.0, min(1.0, mins3 / 270))
        y90 = (e['yc'] + PRIOR[pos] * 6) / (max(e['mins'], 0) / 90 + 6)
        nm = len(played)
        nt = next((t for t in thr if t['ban'] and t['n'] > e['yc'] and nm < t['cutoff_matches']), None)
        if nt and nt['n'] - e['yc'] <= 2 and share > 0 and e['st'] not in ('u', 'n'):
            need = nt['n'] - e['yc']
            fut = [x for x in nxt if x[1] <= GWS[-1]][: max(0, nt['cutoff_matches'] - nm)]
            # P(amarelo) em cada jogo = disponível × (1 − e^(−y90 × minutos/90)); jogos de castigo oficiais: 0
            pm = [0.0 if x[1] in ban_gws else av.get(x[1], 1.0) * (1 - math.exp(-y90 * share)) for x in fut]
            dist = [1.0] + [0.0] * (need - 1)   # P(k amarelos a mais, ainda sem chegar ao limite)
            reach = []                          # P(chega ao limite neste jogo)
            for p_ in pm:
                reach.append(dist[need - 1] * p_)
                dist = [dist[k] * (1 - p_) + (dist[k - 1] * p_ if k else 0.0) for k in range(need)]
            pban = defaultdict(float)
            for j, r_ in enumerate(reach):
                for x in fut[j + 1: j + 1 + nt['ban']]: pban[x[1]] += r_
                if j + 1 + nt['ban'] > len(fut):   # castigo cai depois da janela da lista: jogos seguintes da equipa
                    extra = nxt[len(fut): len(fut) + (j + 1 + nt['ban'] - len(fut))]
                    for x in extra: pban[x[1]] += r_
            for g in GWS: av[g] = min(av[g], av[g] * (1 - min(1.0, pban.get(g, 0.0))))
            cut_g = fx_t[nt['cutoff_matches'] - 1][1] if len(fx_t) >= nt['cutoff_matches'] else None
            ex = []
            for j, x in enumerate(fut[:4]):
                miss = [y[1] for y in fut[j + 1: j + 1 + nt['ban']]] or [y[1] for y in nxt[j + 1: j + 1 + nt['ban']]]
                if need == 1 and miss: ex.append([x[1], miss])
            tot = sum(reach[:sum(1 for x in fut if x[1] in SHOW)])
            rec['risk'] = dict(yc=e['yc'], n=nt['n'], need=need, ban=nt['ban'], cut=cut_g, y90=round(y90, 3), share=round(share, 2),
                               pm=[[x[1], round(p_, 3)] for x, p_ in zip(fut, pm)][:8],
                               pb={str(g): round(v, 3) for g, v in pban.items() if g in GWS and v >= 0.005},
                               ex=ex, tot=round(tot, 3))
        if e['yc'] or e['rc']: cards[sid] = [e['yc'], e['rc']]
        if e['yc'] or e['rc'] or 'sus' in rec or 'pend' in rec or 'risk' in rec:
            dis_json[sid] = dict(name=name, team=team, yellow=e['yc'], red=e['rc'], minutes=e['mins'],
                                 source='API oficial da FPL (yellow_cards, red_cards, minutes)',
                                 suspended=rec.get('sus'), pending_ban=rec.get('pend'),
                                 next_threshold=(dict(n=nt['n'], ban=nt['ban'], cutoff_matches=nt['cutoff_matches'],
                                                      cutoff_gw=(fx_t[nt['cutoff_matches'] - 1][1] if len(fx_t) >= nt['cutoff_matches'] else None),
                                                      team_matches_played=nm) if nt else None),
                                 risk=rec.get('risk'))
        if rec and (('inj' in rec) or ('sus' in rec) or ('pend' in rec) or ('out' in rec) or ('risk' in rec and rec['risk']['tot'] >= 0.02)):
            rec['av'] = {str(g): round(av[g], 3) for g in GWS}
            rec['ef'] = {str(g): round(v, 3) for g, v in ep_factor(GWS, av, prev=(0.0 if 'inj' in rec and e['st'] == 'i' else 1.0)).items()}
            out_p[pid] = rec
    res = dict(gen=now.strftime('%Y-%m-%dT%H:%M:%SZ'), gws=GWS, show=SHOW,
               ko={str(g): {str(t): (teamko[t][g].strftime('%Y-%m-%dT%H:%M:%SZ') if teamko[t].get(g) else None) for t in teamko} for g in GWS},
               dur={k: [v['min'], v['typ'], v['max']] for k, v in DUR.items()}, tpt=TYPE_PT, rx=TYPE_RX, p=out_p,
               thr=[[t['n'], t['cutoff_matches'], t['ban']] for t in thr if t['ban']],
               tm={str(t): sum(1 for x in tf[t] if x[2] or x[0] <= now - timedelta(hours=2)) for t in tf},
               cut={str(t): {str(c): (tf[t][c - 1][1] if len(tf[t]) >= c else None) for c in (19, 32, 38)} for t in tf},
               cards=cards)
    if write:
        INJ['updated'] = res['gen']; INJ['players'] = inj_json
        json.dump(INJ, open(R / 'injuries.json', 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        DIS['updated'] = res['gen']; DIS['players'] = dis_json
        json.dump(DIS, open(R / 'discipline.json', 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    if verbose:
        print(f'jornadas {GWS[0]}-{GWS[-1]} · mostrar {SHOW} · {len(inj_json)} lesionados/dúvidas · {len(out_p)} com disponibilidade < 100%')
        for sid, x in sorted(inj_json.items(), key=lambda kv: kv[1]['likely_return'] or 'Z'):
            print(f"  {x['name']:<18} {x['status']} {x['type_pt']:<20} {x['basis']:<9} regresso {x['likely_return']} {x['prob']}")
        for sid, x in dis_json.items():
            if x['risk'] or x['pending_ban'] or x['suspended']:
                r = x['risk'] or {}
                print(f"  {x['name']:<18} {x['yellow']}A {x['red']}V susp={x['suspended']} pend={x['pending_ban']} risco={r.get('tot')} pb={r.get('pb')}")
    return res


if __name__ == '__main__':
    compute(verbose=True)
