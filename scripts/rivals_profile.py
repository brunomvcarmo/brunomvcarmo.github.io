"""Perfil de cada treinador da liga, a partir de rivals.json (previsão dos rivais, fase 2).

Usa só o que está em rivals.json: o histórico jornada a jornada, as transferências, os picks de cada jornada,
o mercado de cada jornada (mais comprados) e o retrato dos jogadores antes de cada deadline (`players[g]`:
estado, chance de jogar, posse FPL em %, pontos esperados da FPL para essa jornada).
Só biblioteca padrão. As jornadas de Wildcard e Free Hit ficam de fora das contas de transferências.
Todos os números levam o tamanho da amostra: com poucas jornadas, um perfil é uma tendência, não uma certeza.
"""
from collections import Counter

CHIPS = ('wildcard', 'freehit', 'bboost', '3xc')
FLAG = lambda st: st and (st[0] in ('i', 's', 'u', 'n') or (st[0] == 'd' and (st[1] if st[1] is not None else 50) <= 50))


def _squad(gw):
    return set(gw['s']) | set(gw['b'])


def profile(x, R):
    gws = {int(g): v for g, v in x['gws'].items()}
    G = sorted(gws)
    hist = {h[0]: h for h in x['history']}
    chip_gw = {g for g, v in gws.items() if v.get('chip') in ('wildcard', 'freehit')}
    P = R.get('players', {})
    M = R.get('market', {})
    # ---------- transferências ----------
    norm = [g for g in G if g >= 2 and g not in chip_gw and g in hist]
    tcount = [hist[g][3] for g in norm]
    hits = [(g, hist[g][4]) for g in norm if hist[g][4] > 0]
    zero = sum(1 for t in tcount if t == 0)
    mean_t = sum(tcount) / len(tcount) if tcount else 0.0
    # ---------- moda ou diferenciais (compras normais) ----------
    buys = [(t[0], t[1]) for t in x['transfers'] if t[0] >= 2 and t[0] not in chip_gw]
    moda = dif = known = 0
    for g, pid in buys:
        mk = M.get(str(g))
        if mk:
            known += 1
            if pid in [i for i, _ in mk['in'][:10]]:
                moda += 1
        snap = (P.get(str(g)) or {}).get(str(pid))
        if snap and snap[2] is not None and snap[2] < 5:
            dif += 1
    # ---------- lesionados: vende logo ou espera? ----------
    inj = []   # (jornadas que esperou até vender, ou None se nunca vendeu enquanto marcado)
    for k, g in enumerate(G):
        if g < 2 or (g - 1) not in gws or g in chip_gw:
            continue
        prev = _squad(gws[g - 1]) if (g - 1) not in chip_gw else (_squad(gws[g - 2]) if (g - 2) in gws else set())
        snap = P.get(str(g)) or {}
        for pid in prev:
            st = snap.get(str(pid))
            if not FLAG(st):
                continue
            # só conta o primeiro aviso de cada episódio (na jornada anterior ele ainda não estava marcado)
            before = (P.get(str(g - 1)) or {}).get(str(pid))
            if FLAG(before) and (g - 1) in gws and pid in _squad(gws[g - 1]):
                continue
            waited = None
            for h in G[k:]:
                if h in chip_gw:
                    continue
                if pid not in _squad(gws[h]):
                    waited = h - g
                    break
                if not FLAG((P.get(str(h)) or {}).get(str(pid))):
                    break   # recuperou antes de ser vendido
            inj.append(waited)
    sold_now = sum(1 for w in inj if w == 0)
    # ---------- capitão ----------
    caps = [(g, gws[g]['c']) for g in G if gws[g].get('c')]
    pop, best, fixed = 0, 0, 0
    modal = Counter(c for _, c in caps).most_common(1)[0][0] if caps else None
    for g, c in caps:
        league = Counter(v['gws'][str(g)]['c'] for v in R['entries'].values() if str(g) in v['gws'] and v['gws'][str(g)].get('c'))
        if league and c == league.most_common(1)[0][0]:
            pop += 1
        snap = P.get(str(g)) or {}
        eps = [(snap.get(str(p), [None, None, None, None])[3] or 0, p) for p in gws[g]['s']]
        if g >= 2 and eps and c == max(eps)[1]:
            best += 1
        if c == modal:
            fixed += 1
    n_cap = len(caps)
    n_cap_ep = sum(1 for g, _ in caps if g >= 2)
    # ---------- chips ----------
    used = [(n, g) for n, g in x['chips']]
    half = [n for n, g in used if g <= 19]
    left = [c for c in CHIPS if c not in half]
    # ---------- rótulos simples ----------
    labels = []
    if mean_t <= 0.8 and not hits:
        labels.append('conservador')
    elif mean_t >= 1.5 or len(hits) >= 2:
        labels.append('mexe muito')
    if hits:
        labels.append('faz hits')
    if zero >= 2 and not hits:
        labels.append('guarda transferências')
    if known >= 3 and moda / known >= 0.6:
        labels.append('segue a moda')
    elif len(buys) >= 3 and dif / len(buys) >= 0.35:
        labels.append('procura diferenciais')
    if len(inj) >= 2:
        if sold_now / len(inj) >= 0.7:
            labels.append('vende logo os lesionados')
        elif sold_now / len(inj) <= 0.3:
            labels.append('espera pelos lesionados')
    if n_cap >= 3:
        if pop / n_cap >= 0.8:
            labels.append('capitão da maioria')
        elif fixed / n_cap >= 0.8:
            labels.append('capitão fixo')
        elif pop / n_cap >= 0.6:
            labels.append('capitão da maioria')
        elif n_cap_ep and best / n_cap_ep >= 0.6:
            labels.append('capitão pelo melhor jogo')
        else:
            labels.append('capitão variável')
    if len(half) >= 2 and max(g for n, g in used if g <= 19) <= 6:
        labels.append('usa as chips cedo')
    elif not half:
        labels.append('guarda as chips')
    if hits and len(buys) >= 3 and dif / len(buys) >= 0.35:
        labels.append('arrisca')
    return {
        'labels': labels,
        'transfers': {'per_gw': round(mean_t, 2), 'gws': len(norm), 'zero_gws': zero, 'hits': len(hits), 'hit_pts': sum(c for _, c in hits)},
        'market': {'buys': len(buys), 'known': known, 'top10': moda, 'own_lt5': dif},
        'injured': {'cases': len(inj), 'sold_same_gw': sold_now, 'sold_later': sum(1 for w in inj if w and w > 0), 'kept': sum(1 for w in inj if w is None)},
        'captain': {'gws': n_cap, 'modal': modal, 'fixed': fixed, 'popular': pop, 'best_ep': best, 'gws_ep': n_cap_ep},
        'chips': {'used': used, 'left_first_half': left},
    }


def build(R):
    return {e: profile(x, R) for e, x in R['entries'].items()}
