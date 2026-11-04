"""J10 (3 nov 2026): recomendações e textos escritos à mão para a J10 (deadline sex 6 nov, 18:30 em Lisboa).
Os números vêm dos dados (epAt…); as frases (quem entra/sai, porquê) são desta semana.
Uso (a partir da raiz): py -X utf8 _build/patches/patch_j10.py"""
import re
from pathlib import Path

H = Path(__file__).resolve().parents[2] / 'index.html'
s = H.read_text(encoding='utf-8')


def rep_re(pat, b):
    global s
    m = re.search(pat, s, re.S)
    assert m, pat[:90]
    s = s[:m.start()] + b + s[m.end():]


# ---------- trocas sugeridas ----------
rep_re(r"  const SUGGESTED_MOVES = \{\n.*?\n  \};\n",
       "  const SUGGESTED_MOVES = {\n"
       "    bruno: {transfers: [{out: 399, in: 68}, {out: 176, in: 31}], optional: []},\n"
       "    marco: {transfers: [{out: 12, in: 68}], optional: [{out: 277, in: 31}]},\n"
       "  };\n")
rep_re(r"  // V53 \(20 out 2026\): RECOMENDAÇÕES para a J8.*?\n  const SUBS = \[\n.*?\n  \];\n",
       "  // J10 (3 nov 2026): RECOMENDAÇÕES — nada disto está aplicado ao plantel (sexta lição).\n"
       "  const SUBS = [\n"
       "    {type:'transfer', out:'Rayan Cherki', in:'Marcus Tavernier', note:'£7.9M → £6.6M · Cherki 0, 45 e 35 min nas últimas três (roda no City); Tavernier 10+10+3 pts, bolas paradas do Bournemouth'},\n"
       "    {type:'transfer', out:'Jay Dasilva', in:'Ezri Konsa Ngoyo', note:'£4.0M → £4.7M · Konsa titular no Arsenal (9+14+10 pts), recebe o Hull'},\n"
       "  ];\n")
rep_re(r"  const CAPTAIN_CHANGE = \{.*?\};\n",
       "  const CAPTAIN_CHANGE = {out:'Erling Haaland', in:'Erling Haaland', note:'mantém: o Haaland (100% na FPL) vai a Nottingham e é o capitão de quase todos os sites; alternativa diferencial sem o ter: Gabriel (Arsenal recebe o Hull)'};\n")
rep_re(r"  const CAPTAIN_RISK = \[\n.*?\n  \];\n",
       "  const CAPTAIN_RISK = [\n"
       "    {name:\"Erling Haaland\", profile:\"Aposta de \\\"tudo ou nada\\\"\", note:\"o capitão de 78,9% dos gestores e dos dois plantéis: o mais xG da liga (6,56). Vai a Nottingham (dificuldade 2,6 no xgstat).\"},\n"
       "    {name:\"Gabriel / Konsa\", profile:\"Defesas com golo\", note:\"o Arsenal recebe o Hull (o jogo mais fácil da jornada, 1,1): baliza a zero provável e bolas paradas. O The False 9 dá o Gabriel como capitão diferencial.\"},\n"
       "    {name:\"Alexander Isak\", profile:\"Meio-termo\", note:\"2.º maior xG da época (4,27), titular em todos os jogos; vai ao Palace.\"},\n"
       "  ];\n")

# ---------- textos da semana (v53Texts) ----------
a = s.index("      { const P = id => FULL_POOL_BY_ID[id], e = id => v53f1(epAt(P(id), 0)), e5 = id => v53f1(P(id).epH.reduce((a, b) => a + b, 0)), el = document.getElementById('bruno-todo-list');")
b = s.index("    } catch (e) { console.error(e); }\n  }\n  v53Texts();")
NEW = r'''      { const P = id => FULL_POOL_BY_ID[id], e = id => v53f1(epAt(P(id), 0)), e5 = id => v53f1(P(id).epH.reduce((a, b) => a + b, 0)), el = document.getElementById('bruno-todo-list');
      const bAfter = (() => { const st = SQUAD_STATE.bruno, sell = id => (st.players.find(q => q.id === id) || {}).sell || 0; return (st.bank + sell(399) + sell(176) - P(68).price - P(31).price).toFixed(1); })();
      if (el) el.innerHTML = `
        <li><b>Transferências (tens ${SQUAD_STATE.bruno.ft} grátis): Cherki → Tavernier e Dasilva → Konsa.</b><span>O Cherki está a rodar no City (0, 45 e 35 minutos nas últimas três) e foi o 2.º mais vendido da semana. O Tavernier (£6.6M, bolas paradas do Bournemouth) tem ≈${e(68)} pts esperados na J${GW_META.next} contra ≈${e(399)} (≈${e5(68)} vs ≈${e5(399)} nas próximas cinco). O Konsa (£4.7M) é titular no Arsenal, que recebe o Hull: ≈${e(31)} contra ≈${e(176)} do Dasilva. As duas juntas valem ≈+6,6 pts na J${GW_META.next} e ≈+26 em cinco jornadas; ficas com £${bAfter}M no banco.</span></li>
        <li><b>Capitão: Haaland (≈${e(411)}).</b><span>100% na FPL, vai a Nottingham; é o capitão de quase todos os sites. Vice: Isak (≈${e(379)}).</span></li>
        <li><b>Onze: ${(() => { const r = pickXi(applyMoves(squadOf('bruno').filter(Boolean), SUGGESTED_MOVES.bruno.transfers), 0); return `com as trocas, banco ${[...r.benchGk, ...r.benchOut].map(p => shortName(p.name)).join(' → ')}`; })()}.</b><span>O Henderson está a 75% (doença). Confirma os onzes prováveis em Jogos › Onzes prováveis antes do deadline.</span></li>`;
      const n = document.getElementById('bruno-todo-note'); if (n) n.textContent = `Deadline: ${GW_META.deadlineLabel} em Lisboa (o primeiro jogo é sexta à noite). Nenhum chip esta semana.`; }
  { const P = id => FULL_POOL_BY_ID[id], e = (id, g = 0) => v53f1(epAt(P(id), g)), e5 = id => v53f1(P(id).epH.reduce((a, b) => a + b, 0));
  document.getElementById('transfer-advice').innerHTML = `Tens <b>${FREE_TRANSFERS} transferências grátis</b> para a J${GW_META.next} (pela regra da FPL: 1 por jornada, guardaste uma na J8 — confirma no site). Sugestão: <b>Cherki → Tavernier</b> e <b>Dasilva → Konsa</b>. O Cherki tem jogado pouco (0, 45 e 35 minutos) e o Tavernier marca as bolas paradas do Bournemouth: ≈${e(68)} contra ≈${e(399)} na J${GW_META.next}, ≈${e5(68)} vs ≈${e5(399)} em cinco jornadas. O Konsa (Arsenal, recebe o Hull) dá ≈${e(31)} contra ≈${e(176)} do Dasilva. As duas sem custo; juntas ≈+6,6 na J${GW_META.next}. A seguir na lista de saídas: o Solanke (25 e 65 minutos nas duas últimas).`; }
  { const P = id => FULL_POOL_BY_ID[id], e = id => v53f1(epAt(P(id), 0)), H = HISTORY.find(h => h.gw === GW_META.last) || {};
  document.getElementById('gw2-suggestion').innerHTML = `
    <b>O que aconteceu na J${GW_META.last}:</b> ${H.points} pts (média ${H.avgPoints}). Trocaste o João Pedro (lesionado) pelo Isak; capitão Haaland. No H2H perdeste 54-55 com o Paulo Couceiro. Na J8: Saka → Doku, 29 pts, mas ganhaste o H2H 29-17.
    <br><br>
    <b>Para a J${GW_META.next} (deadline ${GW_META.deadlineLabel} em Lisboa):</b> o melhor jogo é o do Arsenal (recebe o Hull: Calafiori, e o Konsa se o comprares). O Haaland vai a Nottingham (≈${e(411)}). Depois da J${GW_META.next} há duas semanas de pausa (seleções).
    <br><br>
    Recomendação: <b>Cherki → Tavernier</b> e <b>Dasilva → Konsa</b> (duas grátis); capitão <b>Haaland</b>, vice <b>Isak</b>.
  `; }
    { const P = id => FULL_POOL_BY_ID[id], e = id => v53f1(epAt(P(id), 0)), e5 = id => v53f1(P(id).epH.reduce((a, b) => a + b, 0));
    const mAfter = (() => { const st = SQUAD_STATE.marco, sell = id => (st.players.find(q => q.id === id) || {}).sell || 0; return (st.bank + sell(12) - P(68).price).toFixed(1); })();
    document.getElementById('marco-todo-list').innerHTML = `
      <li><b>Transferência (${SQUAD_STATE.marco.ft} grátis): Saka → Tavernier.</b><span>O Saka tem uma lesão na coxa e vai falhar "semanas" (Arteta); a FPL dá 0%. O Tavernier (£6.6M) tem ≈${e5(68)} pts esperados nas próximas cinco jornadas e ≈${e(68)} na J${GW_META.next}; ficas com £${mAfter}M no banco. Uma 2.ª troca (Egan → Konsa) custaria −4: só compensa a 5 jornadas (≈+6), por isso fica para depois da pausa, com a grátis nova.</span></li>
      <li><b>Capitão: Haaland (≈${e(411)}).</b><span>100% na FPL, vai a Nottingham. Vice: Barry (≈${e(249)}).</span></li>
      <li><b>Onze: o Bobby Thomas está a 50% (gémeo).</b><span>O modelo deixa-o no banco com o Egan; o Saka sai do plantel. Confirma os onzes prováveis antes do deadline (Jogos › Onzes prováveis).</span></li>
    `;
    document.getElementById('marco-todo-note').textContent = `Nenhum chip esta semana: o Wildcard, o Free Hit e o Bench Boost continuam disponíveis até à J19 (o Triple Captain foi gasto na J3). Deadline: ${GW_META.deadlineLabel} em Lisboa.`;
    document.getElementById('marco-subs-note').innerHTML = `<b>O que mudou nas J8 e J9 (confirmado na API):</b> J8 <b>Neco Williams → Vušković</b> e <b>Bruno Fernandes → Saka</b> (as duas sugeridas), J9 <b>João Pedro → Nicolas Jackson</b>, sem hits. <b>A vigiar:</b> o <b>Saka</b> (lesionado, semanas), o <b>Bobby Thomas</b> (50%) e o <b>Sangare</b> (45, 90 e 61 minutos). Ver a tabela de pontos esperados abaixo.`; }
'''
s = s[:a] + NEW + s[b:]

# ---------- plano de chips: J8 e J9 já passaram ----------
s = re.sub(r"    8:  \{why: 'Sem chip\..*?'\},\n", "", s)
s = re.sub(r"    9:  \{why: 'Sem chip\..*?'\},\n", "", s)
rep_re(r"  document\.getElementById\('chip-advice'\)\.innerHTML = `.*?`;\n",
       "  document.getElementById('chip-advice').innerHTML = `<b>Nenhum chip esta semana.</b> Já usaste o Triple Captain (J3) e o Wildcard (J7). Restam o <b>Free Hit</b> e o <b>Bench Boost</b> da 1.ª metade, até ao deadline da J19 (sex 1 jan 2027, 18:30) — depois perdem-se. Plano: <b>Free Hit na J12</b> (Arsenal–Man City) e <b>Bench Boost na J16</b> — ver a linha do tempo acima. Depois da J10 há duas semanas de pausa: boa altura para preparar a J11 e a J12 com calma.`;\n")
H.write_text(s, encoding='utf-8', newline='\n')
print('J10 aplicado')
