"""Pontos ao vivo da jornada para a área "Ao vivo" da app: escreve aovivo.json na raiz do repositório.

Corre numa GitHub Action de 15 em 15 minutos (ver .github/workflows/fpl-live.yml), mas só vai buscar os dados
quando há jogos da jornada a decorrer ou prestes a começar; fora disso termina sem escrever nada.
Só usa a biblioteca padrão do Python.

Traz: estado dos jogos, pontos e minutos ao vivo de cada jogador escolhido pelos 20 gestores, bónus provisório
(calculado pelo BPS enquanto a FPL não confirma o bónus de cada jogo), picks dos 20 gestores (titulares, banco,
capitão, chip, hits), confrontos H2H da jornada e a classificação H2H.
As substituições automáticas e o total de cada gestor são calculados na app (como na FPL).

Forçar (para testar ou fora dos dias de jogo): FPL_FORCE=1 python scripts/fpl_live.py
Outra jornada: FPL_EVENT=6. Outro servidor: FPL_BASE=http://localhost:8000/api/
"""
import json, os, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

BASE = os.environ.get('FPL_BASE', 'https://fantasy.premierleague.com/api/')
CLASSIC = int(os.environ.get('FPL_CLASSIC', '457722'))
H2H = int(os.environ.get('FPL_H2H', '457789'))
OUT = os.environ.get('FPL_LIVE_OUT', 'aovivo.json')
FORCE = os.environ.get('FPL_FORCE', '') not in ('', '0', 'false')
UA = {'User-Agent': 'Mozilla/5.0 (fpl-app live updater; github actions)', 'Accept': 'application/json'}


def get(path, tries=3):
    url = BASE + path
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.loads(r.read().decode('utf-8'))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if k == tries - 1:
                raise RuntimeError(f'falhou {url}: {e}')
            time.sleep(2 + 3 * k)


def ts(s):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc) if s else None


def bonus_from_bps(rows):
    """Bónus provisório de um jogo a partir do BPS (regra da FPL: 3-2-1; empatados recebem o mesmo
    e ocupam os lugares seguintes)."""
    rows = sorted(rows, key=lambda r: -r['value'])
    out, place, i = {}, 0, 0
    while i < len(rows) and place < 3:
        j = i
        while j < len(rows) and rows[j]['value'] == rows[i]['value']:
            j += 1
        for r in rows[i:j]:
            out[r['element']] = 3 - place
        place += j - i
        i = j
    return out


def main():
    stamp = int(time.time())
    now = datetime.now(timezone.utc)
    boot = get(f'bootstrap-static/?t={stamp}')
    events = boot['events']
    if os.environ.get('FPL_EVENT'):
        cur = int(os.environ['FPL_EVENT'])
    else:
        cur = next((e['id'] for e in events if e.get('is_current')), None)
    if cur is None:
        print('Época ainda sem jornada atual: nada a fazer.')
        return
    ev = next(e for e in events if e['id'] == cur)
    fixtures = [f for f in get(f'fixtures/?event={cur}&t={stamp}') if f.get('kickoff_time')]

    try:
        old = json.load(open(OUT, encoding='utf-8'))
    except (OSError, ValueError):
        old = None

    # só trabalha quando há jogos a decorrer (ou a começar daqui a 10 min) — ou para fechar a jornada
    # quando o último ficheiro ainda tinha jogos por confirmar
    active = any(not f.get('finished') and now - timedelta(hours=14) <= ts(f['kickoff_time']) <= now + timedelta(minutes=10)
                 for f in fixtures)
    closing = bool(old and old.get('event') == cur and any(not x['f'] for x in old.get('fixtures', []))
                   and all(f.get('finished') or ts(f['kickoff_time']) > now for f in fixtures))
    if not (active or closing or FORCE):
        print(f'J{cur}: sem jogos a decorrer — nada a fazer.')
        return

    # ---------- jogos ----------
    fx_out, bonus_prov, team_fx = [], {}, {}
    for f in sorted(fixtures, key=lambda f: (f['kickoff_time'], f['id'])):
        st = {s['identifier']: s for s in f.get('stats', [])}
        confirmed = bool(st.get('bonus') and (st['bonus']['h'] or st['bonus']['a']))
        if f.get('started') and not confirmed and st.get('bps'):
            for el, b in bonus_from_bps(st['bps']['h'] + st['bps']['a']).items():
                bonus_prov[el] = bonus_prov.get(el, 0) + b
        done = bool(f.get('finished') or f.get('finished_provisional'))
        for t in (f['team_h'], f['team_a']):
            team_fx.setdefault(t, []).append((bool(f.get('started')), done))
        fx_out.append({'id': f['id'], 'h': f['team_h'], 'a': f['team_a'], 'hs': f.get('team_h_score'), 'as': f.get('team_a_score'),
                       'ko': f['kickoff_time'], 'min': f.get('minutes', 0), 's': bool(f.get('started')), 'd': done,
                       'f': bool(f.get('finished')), 'b': confirmed})

    # ---------- pontos ao vivo ----------
    live = {x['id']: x['stats'] for x in get(f'event/{cur}/live/?t={stamp}').get('elements', [])}
    info = {e['id']: e for e in boot['elements']}

    # ---------- picks dos 20 gestores ----------
    st = get(f'leagues-classic/{CLASSIC}/standings/?page_new_entries=1&page_standings=1&phase=1&t={stamp}')
    managers = st['standings']['results']
    if not managers:
        raise RuntimeError('classificação vazia')
    entries, used = {}, set()
    for r in managers:
        e = r['entry']
        try:
            pk = get(f'entry/{e}/event/{cur}/picks/?t={stamp}')
        except RuntimeError:
            pk = None
        if not pk or not pk.get('picks'):
            continue
        h = pk.get('entry_history') or {}
        ps = sorted(pk['picks'], key=lambda x: x['position'])
        used.update(x['element'] for x in ps)
        entries[e] = {
            'name': r['entry_name'], 'player': r['player_name'],
            'picks': [[x['element'], x['position'], x['multiplier'], int(bool(x.get('is_captain'))), int(bool(x.get('is_vice_captain')))] for x in ps],
            'chip': pk.get('active_chip'),
            'cost': h.get('event_transfers_cost', 0),
            'transfers': h.get('event_transfers', 0),
            # total antes desta jornada (o total da FPL já inclui a jornada atual, descontados os hits)
            'prev': h.get('total_points', r['total']) - h.get('points', 0) + h.get('event_transfers_cost', 0),
            'api': h.get('points', 0),
            'auto': [[a['element_in'], a['element_out']] for a in pk.get('automatic_subs', [])],
        }
        time.sleep(0.3)

    # top da jornada (para "quem está a fazer pontos") + todos os escolhidos pelos 20
    top = sorted(live, key=lambda i: -(live[i].get('total_points', 0) + bonus_prov.get(i, 0)))[:12]
    el = {}
    for i in used | set(top):
        s, p = live.get(i, {}), info.get(i, {})
        fx = team_fx.get(p.get('team'), [])
        # 0 = sem jogo nesta jornada, 1 = por jogar, 2 = a jogar, 3 = já acabou
        state = 0 if not fx else 3 if all(d for _, d in fx) else 2 if any(s_ and not d for s_, d in fx) else 1
        el[i] = [s.get('total_points', 0), s.get('minutes', 0), bonus_prov.get(i, 0), s.get('bps', 0),
                 p.get('team'), p.get('element_type'), p.get('web_name', str(i)), state,
                 s.get('goals_scored', 0), s.get('assists', 0), s.get('clean_sheets', 0)]

    # ---------- H2H: confrontos da jornada e classificação ----------
    h2h_matches, h2h_table = [], None
    try:
        hm = get(f'leagues-h2h-matches/league/{H2H}/?event={cur}&page=1&t={stamp}')
        h2h_matches = [[m['entry_1_entry'], m['entry_2_entry']] for m in hm.get('results', [])]
    except (RuntimeError, KeyError):
        pass
    try:
        hs = get(f'leagues-h2h/{H2H}/standings/?page_standings=1&t={stamp}')
        h2h_table = [{'entry': r['entry'], 'rank': r['rank'], 'points': r['total'], 'won': r['matches_won'],
                      'drawn': r['matches_drawn'], 'lost': r['matches_lost'], 'pf': r.get('points_for')}
                     for r in hs['standings']['results']]
    except (RuntimeError, KeyError):
        pass

    out = {
        'generated': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'event': cur, 'deadline': ev.get('deadline_time'),
        'finished': bool(ev.get('finished')), 'checked': bool(ev.get('data_checked')),
        'fixtures': fx_out, 'el': el, 'top': top, 'entries': entries,
        'h2h': h2h_matches, 'h2h_table': h2h_table,
    }
    # não grava (nem cria commit) se nada mudou desde a última vez além da hora
    if old and {k: v for k, v in old.items() if k != 'generated'} == json.loads(json.dumps({k: v for k, v in out.items() if k != 'generated'})):
        print(f'J{cur}: sem alterações desde {old.get("generated")}.')
        return
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    playing = sum(1 for x in fx_out if x['s'] and not x['d'])
    print(f'aovivo.json: J{cur}, {len(entries)} gestores, {len(el)} jogadores, {playing} jogos a decorrer')


if __name__ == '__main__':
    main()
