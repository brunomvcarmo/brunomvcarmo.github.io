from pathlib import Path as _P
_ROOT = _P(__file__).resolve().parents[2]
"""Backtest da previsão dos rivais (fase 5), J2-J6: para cada jornada g refaz as previsões só com o que se sabia antes
do deadline de g (rivals_predict.truncate) e compara com o que cada um fez. Compara com regras simples:
  compras:  "compra o mais comprado da semana" (o primeiro do mercado que ainda não tem)
  capitão:  "repete o capitão da jornada anterior" e "o mais capitaneado da liga na jornada anterior"
  trocas:   "toda a gente faz uma troca" (probabilidade de nenhuma = 0)
  chips:    "a mesma probabilidade em todas as jornadas que faltam até à J19"
Jornadas de Wildcard e Free Hit ficam de fora das contas de transferências (aí muda o plantel quase todo).
Uso: py _build/pool/backtest_rivals.py   (escreve _build/pool/backtest_rivals.json)"""
import json, sys
from collections import Counter
sys.path.insert(0, str(_ROOT / 'scripts'))
import rivals_predict, rivals_chips

R = json.load(open(_ROOT / 'rivals.json', encoding='utf-8'))
G = [2, 3, 4, 5, 6]
rows = []
for g in G:
    for e, x in R['entries'].items():
        gw = x['gws'].get(str(g))
        if not gw:
            continue
        chip = gw.get('chip')
        p = rivals_predict.predict(R, e, g)
        if not p:
            continue
        act = [(t[2], t[1]) for t in x['transfers'] if t[0] == g]
        T = rivals_predict.truncate(R, g)
        prev = T['entries'][e]['gws'].get(str(g - 1), {})
        league = Counter(v['gws'][str(g - 1)]['c'] for v in T['entries'].values() if str(g - 1) in v['gws'] and v['gws'][str(g - 1)].get('c'))
        squad = set(rivals_predict.squad_before(T['entries'][e], g))
        mk = [i for i, _ in (R['market'].get(str(g)) or {'in': []})['in'] if i not in squad]
        rows.append(dict(g=g, e=e, chip=chip, p=p, act=act, cap=gw.get('c'), prev_cap=prev.get('c'),
                         pop_cap=league.most_common(1)[0][0] if league else None, rule_in=mk[:3]))

def pct(a, b):
    return f'{a}/{b} ({round(100 * a / b) if b else 0}%)'

res = {}
# ---------- fazer ou não transferências ----------
N = [r for r in rows if r['chip'] not in ('wildcard', 'freehit')]
none_act = [1 if not r['act'] else 0 for r in N]
brier = lambda ps: sum((p - y) ** 2 for p, y in zip(ps, none_act)) / len(ps)
acc = sum(1 for r, y in zip(N, none_act) if (r['p']['p_none'] >= 0.5) == bool(y))
res['nenhuma'] = {'casos': len(N), 'sem_trocas_reais': sum(none_act), 'acerto_modelo': acc, 'acerto_regra': sum(1 for y in none_act if not y),
                  'brier_modelo': round(brier([r['p']['p_none'] for r in N]), 3), 'brier_regra': round(brier([0.0] * len(N)), 3),
                  'brier_media_liga': round(brier([sum(none_act) / len(none_act)] * len(N)), 3)}
# ---------- que transferência ----------
T_ = [r for r in N if r['act']]
ins = lambda r: {i for _, i in r['act']}
outs = lambda r: {o for o, _ in r['act']}
res['transferencias'] = {
    'casos': len(T_),
    'entra_top1_modelo': sum(1 for r in T_ if r['p']['top'] and r['p']['top'][0]['in'] in ins(r)),
    'entra_top3_modelo': sum(1 for r in T_ if ins(r) & {t['in'] for t in r['p']['top']}),
    'entra_regra_top1': sum(1 for r in T_ if r['rule_in'][:1] and r['rule_in'][0] in ins(r)),
    'entra_regra_top3': sum(1 for r in T_ if ins(r) & set(r['rule_in'][:3])),
    'sai_top1_modelo': sum(1 for r in T_ if r['p']['top'] and r['p']['top'][0]['out'] in outs(r)),
    'par_top1_modelo': sum(1 for r in T_ if r['p']['top'] and (r['p']['top'][0]['out'], r['p']['top'][0]['in']) in set(r['act'])),
    'par_top3_modelo': sum(1 for r in T_ if {(t['out'], t['in']) for t in r['p']['top']} & set(r['act'])),
}
# ---------- capitão ----------
C = [r for r in rows if r['cap']]
pa = lambda r: next((c['p'] for c in r['p']['caps'] if c['id'] == r['cap']), 0.0)
res['capitao'] = {'casos': len(C), 'top1_modelo': sum(1 for r in C if r['p']['caps'] and r['p']['caps'][0]['id'] == r['cap']),
                  'regra_repete': sum(1 for r in C if r['prev_cap'] == r['cap']), 'regra_mais_popular': sum(1 for r in C if r['pop_cap'] == r['cap']),
                  'prob_media_no_real': round(sum(pa(r) for r in C) / len(C), 3)}
# ---------- chips (J3-J6: o radar calculado no deadline da jornada anterior) ----------
ev = []
for g in G[1:]:
    Rb = rivals_predict.truncate(R, g)
    Rb.pop('profiles', None)
    Rb['predictions'] = {str(g - 1): {e: rivals_predict.predict(R, e, g - 1) for e in R['entries']}}
    for e, x in R['entries'].items():
        if not Rb['predictions'][str(g - 1)].get(e):
            continue
        rad = rivals_chips.radar(Rb, e, g - 1)
        used = x['gws'].get(str(g), {}).get('chip')
        for chip, v in rad.items():
            left = len(v['p'])
            ev.append((v['p'].get(g, 0.0), (1 - rivals_chips.NEVER) / left, 1 if used == chip else 0, g, e, chip))
if ev:
    bm = sum((p - y) ** 2 for p, _, y, *_ in ev) / len(ev); br = sum((q - y) ** 2 for _, q, y, *_ in ev) / len(ev)
    hits = [(p, q) for p, q, y, *_ in ev if y]
    res['chips'] = {'casos': len(ev), 'usos_reais': len(hits), 'brier_modelo': round(bm, 4), 'brier_regra': round(br, 4),
                    'prob_media_quando_usou_modelo': round(sum(p for p, _ in hits) / len(hits), 3) if hits else None,
                    'prob_media_quando_usou_regra': round(sum(q for _, q in hits) / len(hits), 3) if hits else None}
json.dump(res, open(_ROOT / '_build/pool/backtest_rivals.json', 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
n = res['nenhuma']; t = res['transferencias']; c = res['capitao']
print(f"Fazer ou não trocas ({n['casos']} casos, {n['sem_trocas_reais']} sem trocas): acerto modelo {pct(n['acerto_modelo'], n['casos'])} vs regra 'troca sempre' {pct(n['acerto_regra'], n['casos'])}; "
      f"Brier modelo {n['brier_modelo']} vs regra {n['brier_regra']} vs média da liga {n['brier_media_liga']} (mais baixo é melhor)")
print(f"Quem entra ({t['casos']} jornadas com trocas): 1.ª opção do modelo {pct(t['entra_top1_modelo'], t['casos'])} vs regra 'o mais comprado' {pct(t['entra_regra_top1'], t['casos'])}; "
      f"nas 3 primeiras: modelo {pct(t['entra_top3_modelo'], t['casos'])} vs regra {pct(t['entra_regra_top3'], t['casos'])}")
print(f"Quem sai, 1.ª opção: {pct(t['sai_top1_modelo'], t['casos'])} · troca exata (sai e entra): 1.ª {pct(t['par_top1_modelo'], t['casos'])}, nas 3 primeiras {pct(t['par_top3_modelo'], t['casos'])}")
print(f"Capitão ({c['casos']}): modelo {pct(c['top1_modelo'], c['casos'])} vs 'repete o último' {pct(c['regra_repete'], c['casos'])} vs 'o mais popular da liga' {pct(c['regra_mais_popular'], c['casos'])}; probabilidade média dada ao capitão real {c['prob_media_no_real']}")
if 'chips' in res:
    k = res['chips']
    print(f"Chips ({k['casos']} casos rival×chip×jornada, {k['usos_reais']} usos): Brier modelo {k['brier_modelo']} vs regra {k['brier_regra']}; quando usou, o modelo dava {k['prob_media_quando_usou_modelo']} e a regra {k['prob_media_quando_usou_regra']}")
