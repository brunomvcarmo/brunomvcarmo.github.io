"""J11 (10 nov 2026, pausa das seleções): recomendações e textos escritos à mão para a J11 (deadline sáb 21 nov, 11:00 em Lisboa).
Os números vêm dos dados (epAt…); as frases (quem entra/sai, porquê) são desta semana.
Pausa: as trocas só devem ser feitas na quinta 19 / sexta 20, depois dos jogos das seleções (lesões) e das conferências de imprensa.
Uso (a partir da raiz): py -X utf8 _build/patches/patch_j11.py"""
import re
from pathlib import Path

H = Path(__file__).resolve().parents[2] / 'index.html'
s = H.read_text(encoding='utf-8')


def rep_re(pat, b):
    global s
    m = re.search(pat, s, re.S)
    assert m, pat[:90]
    s = s[:m.start()] + b + s[m.end():]


# ---------- trocas sugeridas (medidas com xiValueW: Bruno +3,4 J11 / +15,7 em 5; Marco +3,2 / +10,7) ----------
rep_re(r"  const SUGGESTED_MOVES = \{\n.*?\n  \};\n",
       "  const SUGGESTED_MOVES = {\n"
       "    bruno: {transfers: [{out: 399, in: 15}, {out: 176, in: 31}], optional: []},\n"
       "    marco: {transfers: [{out: 173, in: 112}], optional: []},\n"
       "  };\n")
rep_re(r"  // J\d+ \([^)]*\): RECOMENDAÇÕES.*?\n  const SUBS = \[\n.*?\n  \];\n",
       "  // J11 (10 nov 2026, pausa das seleções): RECOMENDAÇÕES — nada disto está aplicado ao plantel (sexta lição).\n"
       "  const SUBS = [\n"
       "    {type:'transfer', out:'Rayan Cherki', in:'Martin Ødegaard', note:'£7.9M → £6.7M · Cherki a rodar no City (45, 35 e 90 min); Ødegaard titular no Arsenal, vai a Newcastle'},\n"
       "    {type:'transfer', out:'Jay Dasilva', in:'Ezri Konsa Ngoyo', note:'£4.0M → £4.8M · Konsa titular no Arsenal; o Dasilva fica no banco'},\n"
       "  ];\n")
rep_re(r"  const CAPTAIN_CHANGE = \{.*?\};\n",
       "  const CAPTAIN_CHANGE = {out:'Erling Haaland', in:'Erling Haaland', note:'mantém: o Haaland (100% na FPL) recebe o Fulham no primeiro jogo da jornada (sáb 12:30) e é o capitão de quase todos os sites; confirmar que volta bem da seleção'};\n")
rep_re(r"  const CAPTAIN_RISK = \[\n.*?\n  \];\n",
       "  const CAPTAIN_RISK = [\n"
       "    {name:\"Erling Haaland\", profile:\"Aposta de \\\"tudo ou nada\\\"\", note:\"o capitão dos dois plantéis e de quase toda a liga. Recebe o Fulham no jogo que abre a jornada (sáb 12:30), poucos dias depois de voltar da Noruega.\"},\n"
       "    {name:\"Morgan Rogers / Cole Palmer\", profile:\"Diferencial no Chelsea\", note:\"o Chelsea recebe o Leeds; o The Fantasy Tool põe-nos em 2.º e 3.º lugar para capitão. O Rogers é teu, o Palmer é do Marco.\"},\n"
       "    {name:\"Alexander Isak\", profile:\"Meio-termo\", note:\"titular em todos os jogos, recebe o Man Utd (dom 16:30). O Liverpool tem o Van Dijk e o Szoboszlai em dúvida depois das seleções.\"},\n"
       "  ];\n")

# ---------- textos da semana (v53Texts) ----------
PAUSA = ("Pausa das seleções: não faças as trocas já. Espera pela quinta 19 ou sexta 20, depois dos jogos das seleções "
         "(lesões) e das conferências de imprensa. O deadline é <b>sábado às 11:00</b>, mais cedo do que o costume, "
         "porque o City–Fulham começa às 12:30. Os preços quase não mexem na pausa.")
a = s.index("      { const P = id => FULL_POOL_BY_ID[id], e = id => v53f1(epAt(P(id), 0)), e5 = id => v53f1(P(id).epH.reduce((a, b) => a + b, 0)), el = document.getElementById('bruno-todo-list');")
b = s.index("    } catch (e) { console.error(e); }\n  }\n  v53Texts();")
NEW = r'''      { const P = id => FULL_POOL_BY_ID[id], e = id => v53f1(epAt(P(id), 0)), e5 = id => v53f1(P(id).epH.reduce((a, b) => a + b, 0)), el = document.getElementById('bruno-todo-list');
      const bAfter = (() => { const st = SQUAD_STATE.bruno, sell = id => (st.players.find(q => q.id === id) || {}).sell || 0; return (st.bank + sell(399) + sell(176) - P(15).price - P(31).price).toFixed(1); })();
      if (el) el.innerHTML = `
        <li><b>Quando: quinta 19 ou sexta 20, não antes.</b><span>__PAUSA__</span></li>
        <li><b>Transferências (tens ${SQUAD_STATE.bruno.ft} grátis): Cherki → Ødegaard e Dasilva → Konsa.</b><span>O Cherki tem rodado no City (45, 35 e 90 minutos nas últimas três). O Ødegaard (£6.7M, titular no Arsenal, vai a Newcastle) tem ≈${e(15)} pts esperados na J${GW_META.next} contra ≈${e(399)} (≈${e5(15)} vs ≈${e5(399)} nas próximas cinco). O Konsa (£4.8M) é titular no Arsenal e entra no onze no lugar do Dasilva (≈${e(31)} contra ≈${e(176)}). As duas juntas valem ≈+3,4 pts na J${GW_META.next} e ≈+16 em cinco jornadas; ficas com £${bAfter}M no banco e com 3 do Arsenal (o máximo).</span></li>
        <li><b>Capitão: Haaland (≈${e(411)}).</b><span>Recebe o Fulham no jogo que abre a jornada. Vice: van Hecke (≈${e(112)}) ou Isak (≈${e(379)}).</span></li>
        <li><b>Onze: ${(() => { const r = pickXi(applyMoves(squadOf('bruno').filter(Boolean), SUGGESTED_MOVES.bruno.transfers), 0); return `com as trocas, banco ${[...r.benchGk, ...r.benchOut].map(p => shortName(p.name)).join(' → ')}`; })()}.</b><span>Antes do deadline, vê os onzes prováveis em Jogos › Onzes prováveis: quem se lesionar nas seleções muda tudo.</span></li>`;
      const n = document.getElementById('bruno-todo-note'); if (n) n.textContent = `Deadline: ${GW_META.deadlineLabel} em Lisboa (sábado de manhã). Nenhum chip esta semana; o Free Hit fica para a J12 (Arsenal–Man City).`; }
  { const P = id => FULL_POOL_BY_ID[id], e = (id, g = 0) => v53f1(epAt(P(id), g)), e5 = id => v53f1(P(id).epH.reduce((a, b) => a + b, 0));
  document.getElementById('transfer-advice').innerHTML = `Tens <b>${FREE_TRANSFERS} transferências grátis</b> para a J${GW_META.next} (pela regra da FPL: na J10 fizeste uma, Solanke → Evanilson, e guardaste a outra — confirma no site). Sugestão: <b>Cherki → Ødegaard</b> e <b>Dasilva → Konsa</b>. O Ødegaard dá ≈${e(15)} contra ≈${e(399)} do Cherki na J${GW_META.next} (≈${e5(15)} vs ≈${e5(399)} em cinco jornadas); o Konsa dá ≈${e(31)} contra ≈${e(176)} do Dasilva. As duas sem custo; juntas ≈+3,4 na J${GW_META.next}. <b>Faz as trocas só na quinta ou sexta</b>, depois dos jogos das seleções: se alguém se lesionar, a troca certa pode mudar.`; }
  { const P = id => FULL_POOL_BY_ID[id], e = id => v53f1(epAt(P(id), 0)), H = HISTORY.find(h => h.gw === GW_META.last) || {};
  document.getElementById('gw2-suggestion').innerHTML = `
    <b>O que aconteceu na J${GW_META.last}:</b> ${H.points} pts (média ${H.avgPoints}). Trocaste o Solanke pelo Evanilson; capitão Haaland. No H2H ganhaste 61-49 ao Renato Pinela.
    <br><br>
    <b>Para a J${GW_META.next} (deadline ${GW_META.deadlineLabel} em Lisboa):</b> há duas semanas de pausa (seleções) antes desta jornada. Depois dela vêm três jornadas em dez dias: J${GW_META.next} (21-23 nov), J${GW_META.next + 1} (27-29 nov, com a Europa a meio da semana, 24-26 nov) e J${GW_META.next + 2} a meio da semana (1-3 dez). O Haaland recebe o Fulham (≈${e(411)}).
    <br><br>
    Recomendação: <b>Cherki → Ødegaard</b> e <b>Dasilva → Konsa</b> (duas grátis), feitas na quinta ou sexta; capitão <b>Haaland</b>, vice <b>van Hecke</b> ou <b>Isak</b>.
  `; }
    { const P = id => FULL_POOL_BY_ID[id], e = id => v53f1(epAt(P(id), 0)), e5 = id => v53f1(P(id).epH.reduce((a, b) => a + b, 0));
    const mAfter = (() => { const st = SQUAD_STATE.marco, sell = id => (st.players.find(q => q.id === id) || {}).sell || 0; return (st.bank + sell(173) - P(112).price).toFixed(1); })();
    document.getElementById('marco-todo-list').innerHTML = `
      <li><b>Quando: quinta 19 ou sexta 20, não antes.</b><span>__PAUSA__</span></li>
      <li><b>Transferência (${SQUAD_STATE.marco.ft} grátis): Bobby Thomas → van Hecke.</b><span>O Bobby Thomas está a 50% (barriga da perna) e não jogou nas duas últimas. O van Hecke (£5.1M) tem ≈${e(112)} pts esperados na J${GW_META.next} contra ≈${e(173)} e entra no onze (≈${e5(112)} vs ≈${e5(173)} em cinco jornadas); ficas com £${mAfter}M no banco. Uma 2.ª troca com −4 (Maguire → Konsa) não compensa: o plano tem o Free Hit na J12 e o Wildcard na J13, por isso só conta a J${GW_META.next}.</span></li>
      <li><b>Capitão: Haaland (≈${e(411)}).</b><span>Recebe o Fulham no primeiro jogo da jornada. Vice: Nicolas Jackson (≈${e(166)}).</span></li>
      <li><b>Onze: o Maguire tem 4 amarelos.</b><span>Se levar um na J${GW_META.next}, falha a J${GW_META.next + 1} (castigo). Confirma os onzes prováveis antes do deadline (Jogos › Onzes prováveis).</span></li>
    `;
    document.getElementById('marco-todo-note').textContent = `Nenhum chip esta semana. Plano: Free Hit na J12, Wildcard na J13 e Bench Boost na J16 (o Triple Captain foi gasto na J3); os chips da 1.ª metade perdem-se depois da J19. Deadline: ${GW_META.deadlineLabel} em Lisboa (sábado de manhã).`;
    document.getElementById('marco-subs-note').innerHTML = `<b>O que mudou na J10 (confirmado na API):</b> <b>Saka → Palmer</b>, sem hits; capitão Haaland; 71 pts, mas perdeste o H2H 71-73 com o Luis Pico. <b>A vigiar:</b> o <b>Bobby Thomas</b> (50%), o <b>Maguire</b> (4 amarelos, 45 minutos na J10) e o <b>Sangare</b> (90, 61 e 58 minutos). Ver a tabela de pontos esperados abaixo.`; }
'''.replace('__PAUSA__', PAUSA)
s = s[:a] + NEW + s[b:]

# ---------- plano de chips: a J10 já passou; a J11 é a da pausa ----------
s = re.sub(r"    10: \{why: 'Sem chip\..*?'\},\n", "", s)
rep_re(r"    11: \{why: 'Sem chip\..*?'\},\n",
       "    11: {why: 'Sem chip. Primeira jornada depois da pausa das seleções (deadline sáb 21 nov às 11:00): fazer as trocas só na quinta ou sexta, depois das notícias das seleções.'},\n")
rep_re(r"  document\.getElementById\('chip-advice'\)\.innerHTML = `.*?`;\n",
       "  document.getElementById('chip-advice').innerHTML = `<b>Nenhum chip esta semana.</b> Já usaste o Triple Captain (J3) e o Wildcard (J7). Restam o <b>Free Hit</b> e o <b>Bench Boost</b> da 1.ª metade, até ao deadline da J19 (sex 1 jan 2027, 18:30) — depois perdem-se. Plano: <b>Free Hit na J12</b> (Arsenal–Man City, sex 27 a dom 29 nov, logo a seguir à Europa) e <b>Bench Boost na J16</b> — ver a linha do tempo acima. Como o Free Hit só vale para a J12, as trocas desta semana devem pensar na J11 e na J13 em diante.`;\n")
H.write_text(s, encoding='utf-8', newline='\n')
print('J11 aplicado')
