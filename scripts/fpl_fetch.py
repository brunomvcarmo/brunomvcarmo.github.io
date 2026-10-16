"""Recolhe da API oficial da FPL o que a app precisa para se atualizar sozinha no GitHub Pages
e escreve live.json na raiz do repositório. Escreve também rivals.json (previsão dos rivais): histórico completo
de transferências, capitão/vice/chip/onze de cada jornada jogada, chips e o mercado da semana (mais comprados).

Corre numa GitHub Action (ver .github/workflows/fpl-update.yml). Só usa a biblioteca padrão do Python.
Para testar contra outro servidor: FPL_BASE=http://localhost:8000/api/ python scripts/fpl_fetch.py

Liga clássica 457722 e H2H 457789 (Mitras Fantasy League 26/27).
Nota (nona lição das notas da app): alguns URLs "simples" da API devolvem cópias em cache muito antigas;
por isso todos os pedidos levam um parâmetro inofensivo extra.
"""
import json, os, sys, time, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rivals_profile, rivals_predict, rivals_chips
from datetime import datetime, timezone

BASE = os.environ.get('FPL_BASE', 'https://fantasy.premierleague.com/api/')
CLASSIC = int(os.environ.get('FPL_CLASSIC', '457722'))
H2H = int(os.environ.get('FPL_H2H', '457789'))
OUT = os.environ.get('FPL_OUT', 'live.json')
RIVALS = os.environ.get('FPL_RIVALS', 'rivals.json')
UA = {'User-Agent': 'Mozilla/5.0 (fpl-app updater; github actions)', 'Accept': 'application/json'}


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


def main():
    stamp = int(time.time())
    boot = get(f'bootstrap-static/?t={stamp}')
    events = boot['events']
    cur = next((e['id'] for e in events if e.get('is_current')), None)
    finished = [e['id'] for e in events if e.get('finished') or e.get('data_checked')]
    last_finished = max(finished) if finished else None
    if cur is None:
        cur = last_finished or 1

    elements = {e['id']: [e['now_cost'], e['status'], e.get('chance_of_playing_next_round'), e.get('news', ''),
                          e.get('selected_by_percent', '0'), e.get('event_points', 0), e.get('total_points', 0),
                          e.get('transfers_in_event', 0), e.get('transfers_out_event', 0)]
                for e in boot['elements']}

    st = get(f'leagues-classic/{CLASSIC}/standings/?page_new_entries=1&page_standings=1&phase=1&t={stamp}')
    results = st['standings']['results']
    standings = [{'entry': r['entry'], 'entry_name': r['entry_name'], 'player_name': r['player_name'],
                  'rank': r['rank'], 'last_rank': r.get('last_rank'), 'total': r['total'], 'event_total': r['event_total']}
                 for r in results]
    # verificação: a classificação tem de estar na jornada atual (senão é uma cópia antiga em cache)
    if not standings:
        raise RuntimeError('classificação vazia')

    entries, raw = {}, {}
    for r in standings:
        e = r['entry']
        hist = get(f'entry/{e}/history/?gw={cur}&t={stamp}')
        try:
            picks = get(f'entry/{e}/event/{cur}/picks/?t={stamp}')
        except RuntimeError:
            picks = None
        try:
            trans = get(f'entry/{e}/transfers/?t={stamp}')
        except RuntimeError:
            trans = []
        p = None
        if picks and picks.get('picks'):
            ps = sorted(picks['picks'], key=lambda x: x['position'])
            p = {'event': cur,
                 'starters': [x['element'] for x in ps if x['position'] <= 11],
                 'bench': [x['element'] for x in ps if x['position'] > 11],
                 'captain': next((x['element'] for x in ps if x.get('is_captain')), None),
                 'vice': next((x['element'] for x in ps if x.get('is_vice_captain')), None),
                 'active_chip': picks.get('active_chip')}
        entries[e] = {
            'history': [{'event': h['event'], 'points': h['points'], 'total_points': h['total_points'],
                         'bank': h['bank'], 'value': h['value'], 'event_transfers': h.get('event_transfers', 0),
                         'event_transfers_cost': h.get('event_transfers_cost', 0), 'points_on_bench': h.get('points_on_bench', 0)}
                        for h in hist.get('current', [])],
            'chips': [{'name': c['name'], 'event': c['event']} for c in hist.get('chips', [])],
            'picks': p,
            'transfers': [{'event': t['event'], 'in': t['element_in'], 'out': t['element_out'],
                           'in_cost': t.get('element_in_cost'), 'out_cost': t.get('element_out_cost'), 'time': t.get('time')}
                          for t in sorted(trans, key=lambda t: t.get('time') or '', reverse=True)[:10]],
        }
        raw[e] = {'r': r, 'hist': hist, 'trans': trans, 'picks': picks}
        # verificação: o total do histórico tem de bater com a classificação
        hs = entries[e]['history']
        if hs and hs[-1]['total_points'] != r['total'] and hs[-1]['event'] == cur:
            print(f'aviso: total do histórico de {e} ({hs[-1]["total_points"]}) difere da classificação ({r["total"]})', file=sys.stderr)
        time.sleep(0.4)

    h2h = None
    try:
        hs = get(f'leagues-h2h/{H2H}/standings/?page_standings=1&t={stamp}')
        h2h = [{'entry': r['entry'], 'rank': r['rank'], 'points': r['total'], 'won': r['matches_won'],
                'drawn': r['matches_drawn'], 'lost': r['matches_lost'], 'points_for': r.get('points_for')}
               for r in hs['standings']['results']]
    except (RuntimeError, KeyError):
        pass

    # pontos de cada jogador na última jornada fechada (para medir o modelo)
    event_live = None
    if last_finished:
        try:
            lv = get(f'event/{last_finished}/live/?t={stamp}')
            event_live = {'event': last_finished,
                          'points': {x['id']: [x['stats'].get('total_points', 0), x['stats'].get('minutes', 0)] for x in lv.get('elements', [])}}
        except RuntimeError:
            pass

    out = {
        'generated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'current_event': cur, 'last_finished': last_finished, 'picks_event': cur,
        'events': [{'id': e['id'], 'avg': e.get('average_entry_score'), 'finished': e.get('finished'),
                    'deadline': e.get('deadline_time')} for e in events],
        'elements': elements, 'standings': standings, 'entries': entries, 'h2h': h2h, 'event_live': event_live,
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print(f'live.json: J{cur} (última fechada J{last_finished}), {len(standings)} gestores, {len(elements)} jogadores')
    write_rivals(stamp, events, cur, last_finished, boot, raw)


def pick_summary(pk):
    ps = sorted(pk['picks'], key=lambda x: x['position'])
    return {'c': next((x['element'] for x in ps if x.get('is_captain')), None),
            'v': next((x['element'] for x in ps if x.get('is_vice_captain')), None),
            'chip': pk.get('active_chip'),
            's': [x['element'] for x in ps if x['position'] <= 11],
            'b': [x['element'] for x in ps if x['position'] > 11],
            'auto': [[a['element_in'], a['element_out']] for a in pk.get('automatic_subs', [])]}


def write_rivals(stamp, events, cur, last_finished, boot, raw):
    """rivals.json: o que é preciso para prever o que cada rival vai fazer.
    As jornadas já fechadas e confirmadas (data_checked) ficam guardadas e não voltam a ser pedidas à API."""
    try:
        old = json.load(open(RIVALS, encoding='utf-8'))
    except (OSError, ValueError):
        old = {}
    checked = {e['id'] for e in events if e.get('data_checked')}
    started = [e['id'] for e in events if e.get('finished') or e.get('is_current') or e.get('data_checked')]
    out_e = {}
    for e, x in raw.items():
        prev = (old.get('entries') or {}).get(str(e), {})
        gws = {int(k): v for k, v in (prev.get('gws') or {}).items() if v.get('final')}
        for g in started:
            if g in gws:
                continue
            pk = x['picks'] if g == cur and x['picks'] else None
            if pk is None:
                try:
                    pk = get(f'entry/{e}/event/{g}/picks/?t={stamp}')
                except RuntimeError:
                    continue
                time.sleep(0.3)
            if pk and pk.get('picks'):
                gws[g] = dict(pick_summary(pk), final=g in checked)
        hist = x['hist']
        h_rows = [[h['event'], h['points'], h['total_points'], h.get('event_transfers', 0), h.get('event_transfers_cost', 0),
                   h['bank'], h['value'], h.get('points_on_bench', 0), h.get('overall_rank')] for h in hist.get('current', [])]
        tr = sorted(x['trans'] or [], key=lambda t: (t.get('event') or 0, t.get('time') or ''))
        tr_rows = [[t['event'], t['element_in'], t['element_out'], t.get('element_in_cost'), t.get('element_out_cost'), t.get('time')] for t in tr]
        if not tr_rows and prev.get('transfers'):
            tr_rows = prev['transfers']   # o pedido falhou ou veio vazio: fica a lista da última vez
        # nas jornadas de Wildcard e Free Hit o histórico da FPL mostra 0 transferências, mas a lista tem-nas todas
        chip_gw = {g for g, v in gws.items() if v.get('chip') in ('wildcard', 'freehit')}
        n_hist = sum(h[3] for h in h_rows)
        n_list = sum(1 for t in tr_rows if t[0] not in chip_gw)
        out_e[str(e)] = {
            'name': x['r']['entry_name'], 'player': x['r']['player_name'],
            'history': h_rows,
            'chips': [[c['name'], c['event']] for c in hist.get('chips', [])],
            'transfers': tr_rows,
            'gws': {str(g): v for g, v in sorted(gws.items())},
            # verificação (nona lição): o número de transferências da lista tem de bater com o histórico
            'check': {'transfers_api': len(tr_rows), 'transfers_api_sem_wc_fh': n_list, 'transfers_history': n_hist},
        }
        if n_list != n_hist:
            print(f'aviso: {e} tem {n_list} transferências na lista (sem Wildcard/Free Hit) e {n_hist} no histórico', file=sys.stderr)
    # mercado: transferências desde o último deadline contam para a próxima jornada (fica a leitura mais recente)
    nxt = next((ev['id'] for ev in events if ev.get('is_next')), (cur or 0) + 1)
    market = dict(old.get('market') or {})
    els = boot['elements']
    market[str(nxt)] = {'at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'src': 'api',
                        'in': [[x['id'], x.get('transfers_in_event', 0)] for x in sorted(els, key=lambda x: -x.get('transfers_in_event', 0))[:40]],
                        'out': [[x['id'], x.get('transfers_out_event', 0)] for x in sorted(els, key=lambda x: -x.get('transfers_out_event', 0))[:40]]}
    # retrato dos jogadores antes do deadline da próxima jornada: estado, chance, posse FPL (%), pontos esperados da FPL
    # (só os que andam nos plantéis da liga ou no mercado) — serve para o perfil (lesionados, diferenciais, capitão)
    players = dict(old.get('players') or {})
    ids = {p for v in out_e.values() for gw in v['gws'].values() for p in gw['s'] + gw['b']}
    ids |= {i for side in ('in', 'out') for i, _ in market[str(nxt)][side]}
    for t in (1, 2, 3, 4):   # candidatos a entrar: os 15 de mais pontos esperados da FPL em cada posição
        ids |= {x['id'] for x in sorted([x for x in els if x['element_type'] == t], key=lambda x: -float(x.get('ep_next') or 0))[:15]}
    byid = {x['id']: x for x in els}
    # [estado, chance, posse %, ep_next da FPL, preço £M, clube, posição (1-4), forma, preço inicial £M]
    players[str(nxt)] = {str(i): [byid[i]['status'], byid[i].get('chance_of_playing_next_round'), float(byid[i].get('selected_by_percent') or 0),
                                  float(byid[i].get('ep_next') or 0), byid[i]['now_cost'] / 10, byid[i]['team'], byid[i]['element_type'],
                                  float(byid[i].get('form') or 0), (byid[i]['now_cost'] - byid[i].get('cost_change_start', 0)) / 10]
                         for i in sorted(ids) if i in byid}
    # dificuldade oficial dos jogos, por clube, da próxima jornada até ao fim da 1.ª metade (para o radar de chips)
    fdr = dict(old.get('fdr') or {})
    try:
        fx = get(f'fixtures/?t={stamp}')
        for g in range(nxt, max(nxt, 19) + 1):
            d = {}
            for f in fx:
                if f.get('event') == g:
                    d.setdefault(str(f['team_h']), []).append(f['team_h_difficulty']); d.setdefault(str(f['team_a']), []).append(f['team_a_difficulty'])
            fdr[str(g)] = d
    except RuntimeError:
        pass
    out = {'generated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'current_event': cur, 'last_finished': last_finished,
           'next_event': nxt, 'entries': out_e, 'market': dict(sorted(market.items(), key=lambda kv: int(kv[0]))),
           'players': dict(sorted(players.items(), key=lambda kv: int(kv[0]))), 'fdr': dict(sorted(fdr.items(), key=lambda kv: int(kv[0]))),
           'deadlines': {str(ev['id']): ev.get('deadline_time') for ev in events}}
    out['profiles'] = rivals_profile.build(out)
    # previsão para a próxima jornada (transferências, capitão, plantel e onze prováveis) — probabilidades, não certezas
    out['predictions'] = {str(nxt): rivals_predict.predict_all(out, nxt)}
    # radar de chips: probabilidade de cada chip que falta em cada jornada até à J19
    out['chips_radar'] = {str(nxt): rivals_chips.radar_all(out, nxt)}
    with open(RIVALS, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    bad = [e for e, v in out_e.items() if v['check']['transfers_api_sem_wc_fh'] != v['check']['transfers_history']]
    print(f'rivals.json: {len(out_e)} gestores, jornadas {min(started) if started else "-"}-{max(started) if started else "-"}, '
          f'{sum(len(v["transfers"]) for v in out_e.values())} transferências, mercado da J{nxt}' + (f', {len(bad)} com contagem diferente' if bad else ''))


if __name__ == '__main__':
    main()
