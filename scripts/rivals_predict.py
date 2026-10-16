"""Previsão do que cada rival vai fazer na jornada g (previsão dos rivais, fase 3).

Só usa o que estava em rivals.json antes do deadline da jornada g (por isso serve também para o backtest):
o plantel e o banco depois da jornada g-1, as transferências e capitães anteriores, o perfil calculado só com
jornadas < g, o retrato dos jogadores antes do deadline (`players[g]`: estado, chance, posse, pontos esperados da
FPL, preço, clube, posição, forma, preço inicial), o mercado da semana (`market[g]`) e a dificuldade dos jogos
(`fdr[g]`). Não usa o modelo de pontos da app: os rivais veem o que a FPL mostra.
Tudo em probabilidades: nada aqui é uma certeza.
"""
import math
from collections import Counter
import rivals_profile

FORMATIONS = [(3, 5, 2), (3, 4, 3), (4, 5, 1), (4, 4, 2), (4, 3, 3), (5, 4, 1), (5, 3, 2), (5, 2, 3)]
POS = {1: 'gk', 2: 'def', 3: 'mid', 4: 'fwd'}
CAP_W = {'capitão fixo': (0.6, 0.2, 0.2), 'capitão da maioria': (0.2, 0.6, 0.2), 'capitão pelo melhor jogo': (0.2, 0.2, 0.6)}


def truncate(R, g):
    """rivals.json só com o que se sabia antes do deadline da jornada g."""
    E = {}
    for e, x in R['entries'].items():
        E[e] = dict(x, history=[h for h in x['history'] if h[0] < g], chips=[c for c in x['chips'] if c[1] < g],
                    transfers=[t for t in x['transfers'] if t[0] < g], gws={k: v for k, v in x['gws'].items() if int(k) < g})
    return dict(R, entries=E, market={k: v for k, v in R.get('market', {}).items() if int(k) < g},
                players={k: v for k, v in R.get('players', {}).items() if int(k) <= g})


def softmax(scores, temp=1.0):
    if not scores:
        return {}
    m = max(scores.values())
    w = {k: math.exp((v - m) / temp) for k, v in scores.items()}
    s = sum(w.values())
    return {k: v / s for k, v in w.items()}


def best_xi(ids, P):
    ep = lambda i: (P.get(str(i)) or [None] * 9)[3] or 0
    pos = lambda i: POS.get((P.get(str(i)) or [None] * 9)[6], 'mid')
    by = {c: sorted([i for i in ids if pos(i) == c], key=lambda i: -ep(i)) for c in ('gk', 'def', 'mid', 'fwd')}
    best = None
    for nd, nm, nf in FORMATIONS:
        if not by['gk'] or len(by['def']) < nd or len(by['mid']) < nm or len(by['fwd']) < nf:
            continue
        xi = by['gk'][:1] + by['def'][:nd] + by['mid'][:nm] + by['fwd'][:nf]
        v = sum(ep(i) for i in xi)
        if best is None or v > best[0]:
            best = (v, xi)
    return best[1] if best else list(ids)[:11]


def squad_before(x, g):
    """Plantel com que o rival chega ao deadline da jornada g (depois de um Free Hit volta o plantel anterior)."""
    gws = {int(k): v for k, v in x['gws'].items() if int(k) < g}
    for k in sorted(gws, reverse=True):
        if gws[k].get('chip') != 'freehit':
            return gws[k]['s'] + gws[k]['b']
    return []


def free_transfers(x, g):
    """Transferências grátis para a jornada g pela regra da FPL (1 por jornada, até 5; Wildcard/Free Hit não gastam)."""
    hist = {h[0]: h for h in x['history']}
    chips = {int(k): v.get('chip') for k, v in x['gws'].items()}
    ft = 1
    for k in range(2, g):
        used = 0 if chips.get(k) in ('wildcard', 'freehit') else (hist[k][3] if k in hist else 0)
        ft = min(5, max(0, ft - used) + 1)
    return ft


def sell_price(x, pid, now, start):
    """Preço de venda: compra + metade da subida (arredondada para baixo a 0,1); se desceu, o preço atual."""
    buy = None
    for t in x['transfers']:
        if t[1] == pid and t[3] is not None:
            buy = t[3] / 10
    if buy is None:
        buy = start if start is not None else now
    return now if now <= buy else round(buy + math.floor(round((now - buy) * 10) / 2) / 10, 1)


def predict(R, e, g):
    T = truncate(R, g)
    x = T['entries'][e]
    P = T['players'].get(str(g)) or {}
    if not P:
        return None
    prof = rivals_profile.profile(x, T)
    S = squad_before(x, g)
    if len(S) != 15:
        return None
    hist = x['history']
    bank = hist[-1][5] / 10 if hist else 0.0
    ft = free_transfers(x, g)
    fdr = (R.get('fdr') or {}).get(str(g), {})
    mk = R.get('market', {}).get(str(g)) or {'in': [], 'out': []}
    rank_in = {i: k for k, (i, _) in enumerate(mk['in'])}
    rank_out = {i: k for k, (i, _) in enumerate(mk['out'])}
    snap = lambda i: P.get(str(i)) or [None, None, 0, 0, 0, None, None, 0, None]
    labels = set(prof['labels'])
    last_xi = set(x['gws'][max(x['gws'], key=int)]['s']) if x['gws'] else set()

    def inj(i):
        st, ch = snap(i)[0], snap(i)[1]
        if st in ('i', 's', 'u', 'n'):
            return 1.0 if ch is None else 1 - ch / 100
        if st == 'd':
            return 0.5 if ch is None else 1 - ch / 100
        return 0.0

    def hard(i):
        d = fdr.get(str(snap(i)[5]))
        return (sum(d) / len(d) - 3) if d else 0.0

    # ---------- quem sai ----------
    out_s = {}
    for i in S:
        s = snap(i)
        ep, price = s[3] or 0, s[4] or 0
        sc = 3.0 * inj(i)
        sc += 0.35 * max(0.0, 4 - ep) * (1.0 if (i in last_xi or price >= 5.5) else 0.3)
        sc += 1.0 * (1 - rank_out[i] / 40) if i in rank_out else 0.0
        sc += 0.3 * max(0.0, hard(i))
        sc += 0.25 * max(0.0, 3 - (s[7] or 0)) * (1.0 if i in last_xi else 0.3)
        out_s[i] = sc
    p_out = softmax(out_s, 0.8)
    # ---------- quem entra (para cada saída provável) ----------
    clubs = Counter(snap(i)[5] for i in S)
    moda_w = 1.5 if 'segue a moda' in labels else (0.5 if 'procura diferenciais' in labels else 1.0)
    diff_w = 0.8 if 'procura diferenciais' in labels else 0.0
    pairs = []
    for o, po in sorted(p_out.items(), key=lambda kv: -kv[1])[:5]:
        so = snap(o)
        money = bank + sell_price(x, o, so[4] or 0, so[8])
        cand = {}
        for k, s in P.items():
            q = int(k)
            if q in S or s[6] != so[6] or (s[4] or 99) > money + 1e-6 or s[0] not in ('a', 'd') or (s[0] == 'd' and (s[1] or 0) < 75):
                continue
            if s[5] != so[5] and clubs.get(s[5], 0) >= 3:
                continue
            sc = 0.6 * (s[3] or 0) + 0.15 * (s[7] or 0) - 0.3 * hard(q)
            sc += moda_w * 3.0 * (1 - rank_in[q] / 40) if q in rank_in else 0.0
            sc += diff_w * (1.0 if (s[2] or 0) < 5 else 0.0)
            cand[q] = sc
        p_in = softmax(cand, 0.9)
        for q, pq in p_in.items():
            pairs.append((po * pq, o, q))
    # ---------- fazer ou não transferências ----------
    tf = prof['transfers']
    base0 = (tf['zero_gws'] + 0.35) / (tf['gws'] + 1) if tf['gws'] else 0.35   # 0,35 ≈ média da liga
    urgent = sum(1 for i in last_xi if inj(i) >= 0.75)
    p0 = base0 * (0.35 ** urgent) * (0.75 if ft >= 2 else 1.0)
    p0 = min(0.9, max(0.03, p0))
    pairs.sort(reverse=True)
    top = [{'out': o, 'in': q, 'p': round((1 - p0) * p, 3)} for p, o, q in pairs[:3]]
    # ---------- plantel previsto e onze ----------
    squad = list(S)
    if p0 < 0.5 and pairs:
        _, o, q = pairs[0]
        squad = [q if i == o else i for i in squad]
    xi = best_xi(squad, P)
    # ---------- capitão ----------
    ep = {i: snap(i)[3] or 0 for i in xi if inj(i) < 0.75}
    gws = {int(k): v for k, v in x['gws'].items()}
    caps_hist = [v['c'] for k, v in sorted(gws.items()) if v.get('c')]
    hist_d = Counter()
    if caps_hist:
        hist_d[caps_hist[-1]] += 0.7
        hist_d[Counter(caps_hist).most_common(1)[0][0]] += 0.3
    league = Counter()
    for v in T['entries'].values():
        last = max((int(k) for k in v['gws']), default=None)
        if last is not None and v['gws'][str(last)].get('c'):
            league[v['gws'][str(last)]['c']] += 1
    pop_d = {league.most_common(1)[0][0]: 1.0} if league else {}
    ep_d = softmax(ep, 1.0)
    wh, wp, we = next((CAP_W[l] for l in prof['labels'] if l in CAP_W), (0.34, 0.33, 0.33))
    capp = Counter()
    for i in ep:
        capp[i] = wh * hist_d.get(i, 0) + wp * pop_d.get(i, 0) + we * ep_d.get(i, 0)
    tot = sum(capp.values()) or 1
    caps = [{'id': i, 'p': round(v / tot, 3)} for i, v in capp.most_common(4) if v > 0]
    return {'p_none': round(p0, 3), 'ft': ft, 'bank': round(bank, 1), 'top': top, 'caps': caps,
            'squad': squad, 'xi': xi, 'labels': prof['labels']}


def predict_all(R, g):
    out = {}
    for e in R['entries']:
        try:
            p = predict(R, e, g)
        except (KeyError, ValueError, IndexError):
            p = None
        if p:
            out[e] = p
    return out
