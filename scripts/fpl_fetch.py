
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

    entries = {}
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


if __name__ == '__main__':
    main()
