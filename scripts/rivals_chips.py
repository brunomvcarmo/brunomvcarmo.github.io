"""Radar de chips (previsão dos rivais, fase 4): para cada rival e cada chip que ainda tem na 1.ª metade da
época, a probabilidade de a usar em cada jornada até à J19 (depois perdem-se).

Valor da chip em cada jornada, com o plantel dele (o previsto para a próxima jornada):
  Bench Boost   = pontos esperados do banco
  Triple Captain = pontos esperados do capitão (o de mais pontos esperados do onze)
  Free Hit      = melhor onze possível nessa jornada (orçamento ≈ valor do plantel dele − £17M de banco) menos o onze dele
  Wildcard      = sem valor por jornada: conta a pausa de seleções (usar logo a seguir a uma pausa) e o perfil
Pontos esperados de um jogador na jornada k = (ep_next da FPL ÷ multiplicador do próximo jogo) × multiplicador dos
jogos da jornada k (dificuldade oficial: 1 → ×1,30 … 5 → ×0,70; dupla soma, branca dá 0).
Probabilidade: 8% de nunca usar (esquecer ou guardar de mais); dos restantes 92%, metade repartida só pelo hábito
dele (quem usa cedo puxa para as primeiras jornadas, quem guarda para as últimas) e metade pelo hábito × o valor da
chip (exp(0,7 × valor normalizado); Wildcard: 2,5× logo a seguir a uma pausa de seleções). É uma estimativa grosseira: com 6 jornadas de dados o hábito de cada um ainda diz pouco.
"""
import math
import rivals_profile, rivals_predict

DIFF_MULT = {1: 1.30, 2: 1.15, 3: 1.00, 4: 0.85, 5: 0.70}
LAST = 19
NEVER = 0.08
NAMES = {'wildcard': 'Wildcard', 'freehit': 'Free Hit', 'bboost': 'Bench Boost', '3xc': 'Triple Captain'}


def breaks(R):
    """Jornadas que vêm logo a seguir a uma pausa (12+ dias desde o deadline anterior)."""
    from datetime import datetime
    dl = {int(k): datetime.strptime(v[:19], '%Y-%m-%dT%H:%M:%S') for k, v in (R.get('deadlines') or {}).items() if v}
    return {k for k in dl if k - 1 in dl and (dl[k] - dl[k - 1]).days >= 12}


def ep_at(R, i, k, g0):
    P = R['players'].get(str(g0)) or {}
    s = P.get(str(i))
    if not s:
        return 0.0
    if s[0] == 'u' or (s[0] in ('i', 's') and k <= g0 + 1):
        return 0.0
    fd = R.get('fdr') or {}
    nxt = fd.get(str(g0), {}).get(str(s[5]))
    per = (s[3] or 0) / sum(DIFF_MULT[d] for d in nxt) if nxt else (s[7] or 0)
    dk = fd.get(str(k), {}).get(str(s[5]))
    return per * sum(DIFF_MULT[d] for d in dk) if dk else 0.0


def ideal_xi(R, k, g0, cap):
    P = R['players'].get(str(g0)) or {}
    cands = sorted(((ep_at(R, int(i), k, g0), int(i), s) for i, s in P.items() if s[6]), reverse=True)
    best = 0.0
    for nd, nm, nf in rivals_predict.FORMATIONS:
        need = {1: 1, 2: nd, 3: nm, 4: nf}
        got, clubs, cost, tot, mx = {1: 0, 2: 0, 3: 0, 4: 0}, {}, 0.0, 0.0, 0.0
        left = 11
        for v, i, s in cands:
            t = s[6]
            if got[t] >= need[t] or clubs.get(s[5], 0) >= 3:
                continue
            if cost + (s[4] or 0) + 4.0 * (left - 1) > cap:
                continue
            got[t] += 1; clubs[s[5]] = clubs.get(s[5], 0) + 1; cost += s[4] or 0; tot += v; mx = max(mx, v); left -= 1
            if not left:
                break
        if not left:
            best = max(best, tot + mx)
    return best


def radar(R, e, g0):
    """Probabilidades de cada chip que falta, nas jornadas g0+1 … 19 (a próxima jornada fica de fora: já é a da semana)."""
    pred = (R.get('predictions') or {}).get(str(g0), {}).get(e)
    prof = (R.get('profiles') or {}).get(e) or rivals_profile.profile(R['entries'][e], R)
    left = prof['chips']['left_first_half']
    if not pred or not left or g0 >= LAST:
        return {}
    P = R['players'].get(str(g0)) or {}
    squad = pred['squad']
    value = sum((P.get(str(i)) or [0] * 9)[4] or 0 for i in squad) + pred['bank']
    labels = set(prof['labels'])
    beta = 0.15 if 'usa as chips cedo' in labels else (-0.10 if 'guarda as chips' in labels else 0.0)
    K = list(range(g0 + 1, LAST + 1))
    brk = breaks(R)
    out = {}
    for chip in left:
        vals = []
        for k in K:
            ep = {i: ep_at(R, i, k, g0) for i in squad}
            xi = rivals_predict.best_xi(squad, {str(i): (P.get(str(i)) or [None] * 9)[:3] + [ep[i]] + (P.get(str(i)) or [None] * 9)[4:] for i in squad})
            xv = sum(ep[i] for i in xi) + max((ep[i] for i in xi), default=0)
            if chip == 'bboost':
                v = sum(ep[i] for i in squad if i not in xi)
            elif chip == '3xc':
                v = max((ep[i] for i in xi), default=0)
            elif chip == 'freehit':
                v = max(0.0, ideal_xi(R, k, g0, value - 17.0) - xv)
            else:
                v = 1.0 if k in brk else 0.0
            vals.append(v)
        habit = [math.exp(-beta * (k - K[0])) for k in K]
        if chip == 'wildcard':
            fit = [1 + 1.5 * v for v in vals]   # logo a seguir a uma pausa: 2,5× mais provável
        else:
            m = sum(vals) / len(vals)
            sd = (sum((v - m) ** 2 for v in vals) / len(vals)) ** 0.5 or 1.0
            fit = [math.exp(0.7 * (v - m) / sd) for v in vals]
        hw = [h / sum(habit) for h in habit]
        fw = [h * f for h, f in zip(habit, fit)]; fs = sum(fw)
        # metade só pelo hábito, metade também pelo valor da chip: com tão poucos dados não há certezas
        probs = {k: round((1 - NEVER) * (0.5 * a + 0.5 * b / fs), 3) for k, a, b in zip(K, hw, fw)}
        peak = max(probs, key=probs.get)
        out[chip] = {'p': probs, 'peak': peak, 'by19': round(1 - NEVER, 2), 'value': {k: round(v, 1) for k, v in zip(K, vals)}}
    return out


def radar_all(R, g0):
    return {e: r for e in R['entries'] if (r := radar(R, e, g0))}
