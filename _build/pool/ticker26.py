from pathlib import Path as _P
_BD = str(_P(__file__).resolve().parents[1]) + '/'   # pasta _build
"""V26: fixture difficulty from FPL fixture tickers (xgstat overall + OddAlerts projected xG for/against).
ATT = difficulty for attackers, DEF = difficulty for defenders/GK, both 1 (easiest) .. 5 (hardest)."""
import json, statistics
T = json.load(open(_BD + 'research/ticker.json', encoding='utf-8'))

def build():
    rows = [r for g in T['fixtures'] for r in T['fixtures'][g]]
    xf = [r['ratings']['oddalerts_xgf'] for r in rows if r['ratings'].get('oddalerts_xgf') is not None]
    xa = [r['ratings']['oddalerts_xga'] for r in rows if r['ratings'].get('oddalerts_xga') is not None]
    mf, sf = statistics.mean(xf), statistics.pstdev(xf)
    ma, sa = statistics.mean(xa), statistics.pstdev(xa)
    clip = lambda v: max(1.0, min(5.0, v))
    out = {}
    for g, lst in T['fixtures'].items():
        for r in lst:
            rt = r['ratings']; xg = rt.get('xgstat')
            att_o = clip(3 - (rt['oddalerts_xgf'] - mf) / sf * 1.2) if rt.get('oddalerts_xgf') is not None else None
            def_o = clip(3 + (rt['oddalerts_xga'] - ma) / sa * 1.2) if rt.get('oddalerts_xga') is not None else None
            parts_a = [v for v in (att_o, xg) if v is not None]
            parts_d = [v for v in (def_o, xg) if v is not None]
            att = sum(parts_a) / len(parts_a) if parts_a else r['fpl_fdr']
            dfn = sum(parts_d) / len(parts_d) if parts_d else r['fpl_fdr']
            out.setdefault(int(g), {}).setdefault(r['team'], []).append(dict(
                opp=r['opp'], home=r['home'], att=round(att, 1), dfn=round(dfn, 1), ovr=round((att + dfn) / 2, 1),
                xgf=rt.get('oddalerts_xgf'), xga=rt.get('oddalerts_xga'), xgstat=xg, fpl=r['fpl_fdr']))
    return out

def mult(d):  # continuous version of DIFF_MULT {1:1.30, 2:1.15, 3:1.00, 4:0.85, 5:0.70}
    return 1.45 - 0.15 * d

if __name__ == '__main__':
    TK = build()
    names = {1:'ARS',2:'AVL',3:'BOU',4:'BRE',5:'BHA',6:'CHE',7:'COV',8:'CRY',9:'EVE',10:'FUL',11:'HUL',12:'IPS',13:'LEE',14:'LIV',15:'MCI',16:'MUN',17:'NEW',18:'NFO',19:'TOT',20:'SUN'}
    for t in sorted(TK[7]):
        f = TK[7][t][0]
        print(names[t], 'v', names[f['opp']], 'H' if f['home'] else 'A', 'FPL', f['fpl'], 'att', f['att'], 'def', f['dfn'], 'ovr', f['ovr'], f['xgf'], f['xga'], f['xgstat'])
