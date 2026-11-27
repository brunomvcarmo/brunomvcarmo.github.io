"""J12 (27 nov 2026, dia do deadline): a sugestão do Bruno passa de "usar as 2 grátis" para "usar 1 e guardar 1".
Pedido do Bruno: "não quero que me aconselhes sempre a fazer todas as transferências; às vezes pode ser melhor
guardar". Medido com o planeador (autoPlan com o valor das grátis guardadas, V66), J12-J16:
  usar 2 (Cherki → Ødegaard, Doku → Wirtz) ≈307,5 · usar 1 (Cherki → Wirtz) ≈305,9 · usar 1 (Doku → Wirtz, fica o
  Cherki) ≈304,9 · usar 2 ficando com o Cherki (Doku → Wirtz, Dasilva → Justin) ≈304,8 · guardar as 2 ≈302,8.
  Com o planeador da app (V66, beam 10) a 2.ª troca rende +2,0 em 5 jornadas = empate na regra FT_RULE (só se usa se
  render MAIS de 2) → usar 1 e guardar 1; ficam 2 grátis para a J13
  (a meio da semana). Alternativa à vista: Doku → Wirtz e guardar (fica o Cherki; ≈1 pt a menos em 5 jornadas).
Correr depois de patch_j12.py e patch66.py. Uso: py -X utf8 _build/patches/patch_j12b.py"""
import re
from pathlib import Path

H = Path(__file__).resolve().parents[2] / 'index.html'
s = H.read_text(encoding='utf-8')


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:100], s.count(a))
    s = s.replace(a, b)


rep_from = s.index("    bruno: {transfers: [{out: 399, in: 15}, {out: 400, in: 366}], optional: [],")
rep_to = s.index("    marco: {transfers: [], optional: [], cap: 426")
s = s[:rep_from] + ("    bruno: {transfers: [{out: 399, in: 366}], optional: [],   // J12: usar 1 e guardar 1 (a 2.ª troca só rendia ≈+2 em 5 jornadas: empate → guardar)\n"
                    "      alt: {why: 'Se preferires ficar com o Cherki (marcou ao Napoli; o RotoWire põe-no no banco no Emirates, outros sites dão-no como titular)', transfers: [{out: 400, in: 366}]}},\n") + s[rep_to:]
rep("    {type:'transfer', out:'Rayan Cherki', in:'Martin Ødegaard', note:'£7.8M → £6.7M · Cherki a rodar no City; Ødegaard titular no Arsenal, recebe o City'},\n"
    "    {type:'transfer', out:'Jérémy Doku', in:'Florian Wirtz', note:'£7.5M → £7.4M · Wirtz titular no Liverpool (vai a Everton); o Doku vai ao Emirates'},\n",
    "    {type:'transfer', out:'Rayan Cherki', in:'Florian Wirtz', note:'£7.8M → £7.4M · Wirtz titular no Liverpool (vai a Everton); Cherki a rodar no City (RotoWire: banco no Emirates). Guarda a outra grátis: ficas com 2 para a J13'},\n")

# textos do Bruno (lista "Antes do deadline", conselho de transferência e resumo da jornada)
a = s.index("      { const P = id => FULL_POOL_BY_ID[id], e = id => v53f1(epAt(P(id), 0)), e5 = id => v53f1(P(id).epH.reduce((a, b) => a + b, 0)), el = document.getElementById('bruno-todo-list');")
b = s.index("    { const P = id => FULL_POOL_BY_ID[id], e = id => v53f1(epAt(P(id), 0));\n    const FH =")
NEW = r'''      { const P = id => FULL_POOL_BY_ID[id], e = id => v53f1(epAt(P(id), 0)), e5 = id => v53f1(P(id).epH.reduce((a, b) => a + b, 0)), el = document.getElementById('bruno-todo-list');
      const bAfter = (() => { const st = SQUAD_STATE.bruno, sell = id => (st.players.find(q => q.id === id) || {}).sell || 0; return (st.bank + sell(399) - P(366).price).toFixed(1); })();
      const X = pickXi(applyMoves(squadOf('bruno').filter(Boolean), SUGGESTED_MOVES.bruno.transfers), 0);
      if (el) el.innerHTML = `
        <li><b>Quando: sexta, até às 18:30.</b><span>Os jogos europeus já acabaram (City ter, Liverpool qua). Vê os onzes prováveis e as últimas notícias antes de confirmar; a J${GW_META.next + 1} vem logo a seguir, a meio da semana (deadline terça 1 dez às 18:30).</span></li>
        <li><b>Transferências (tens ${SQUAD_STATE.bruno.ft} grátis): Cherki → Wirtz, e guarda a outra.</b><span>O Wirtz (£${P(366).price.toFixed(1)}M, titular no Liverpool, vai a Everton) tem ≈${e(366)} pts esperados na J${GW_META.next} contra ≈${e(399)} do Cherki (≈${e5(366)} vs ≈${e5(399)} nas próximas cinco); ficas com £${bAfter}M no banco. A app comparou usar as 2, usar 1 e guardar: usar as duas só renderia ≈+2 pts a mais em cinco jornadas (vê «Usar ou guardar?» no cartão roxo) — um empate pela regra da app, e no empate não vale a pena perder a margem de ter <b>2 grátis na J${GW_META.next + 1}</b>, a meio da semana. Se preferires ficar com o Cherki: Doku → Wirtz, ≈1 pt a menos em cinco jornadas.</span></li>
        <li><b>Capitão: ${shortName(X.cap.name)} (≈${v53f1(epAt(X.cap, 0))}), vice ${shortName(X.vice.name)} (≈${v53f1(epAt(X.vice, 0))}).</b><span>O Haaland (≈${e(411)}) vai ao Emirates, cinco dias depois do Napoli. Quase toda a liga o tem de capitão (o Sergio Casinha, teu adversário no H2H, também): se preferires não arriscar, a diferença é de ≈${v53f1(epAt(X.cap, 0) - epAt(P(411), 0))} pts.</span></li>
        <li><b>Onze: com a troca, banco ${[...X.benchGk, ...X.benchOut].map(p => shortName(p.name)).join(' → ')}.</b><span>Sem chip esta semana: o Free Hit passa para a J14 (ver Chips).</span></li>`;
      const n = document.getElementById('bruno-todo-note'); if (n) n.textContent = `Deadline: ${GW_META.deadlineLabel} em Lisboa. Uma troca e guarda a outra (2 grátis na J${GW_META.next + 1}); nenhum chip esta semana; plano: Free Hit na J14 e Bench Boost na J16.`; }
  { const P = id => FULL_POOL_BY_ID[id], e = (id, g = 0) => v53f1(epAt(P(id), g)), e5 = id => v53f1(P(id).epH.reduce((a, b) => a + b, 0));
  document.getElementById('transfer-advice').innerHTML = `Tens <b>${FREE_TRANSFERS} transferências grátis</b> para a J${GW_META.next} (na J${GW_META.last} não fizeste nenhuma; confirmado no site). Sugestão: <b>Cherki → Wirtz e guarda a outra</b>. O Wirtz dá ≈${e(366)} contra ≈${e(399)} do Cherki na J${GW_META.next} (≈${e5(366)} vs ≈${e5(399)} em cinco jornadas). Usar as duas grátis só daria ≈+2 pts a mais em cinco jornadas — um empate pela regra da app, que não compensa chegar à J${GW_META.next + 1}, a meio da semana, com 2 grátis. Se preferires ficar com o Cherki, faz Doku → Wirtz (≈1 pt a menos em cinco jornadas). No cartão roxo do Resumo, «Usar ou guardar? Comparar» refaz estas contas com os dados do momento.`; }
  { const P = id => FULL_POOL_BY_ID[id], e = id => v53f1(epAt(P(id), 0)), H = HISTORY.find(h => h.gw === GW_META.last) || {};
  document.getElementById('gw2-suggestion').innerHTML = `
    <b>O que aconteceu na J${GW_META.last}:</b> ${H.points} pts (média ${H.avgPoints}). Sem transferências; capitão Haaland (2 pts). No H2H ganhaste 34-24 ao Tiago Guerreiro.
    <br><br>
    <b>Para a J${GW_META.next} (deadline ${GW_META.deadlineLabel} em Lisboa):</b> a Europa jogou-se a meio da semana (24-26 nov) e a J${GW_META.next + 1} vem logo a seguir, a meio da semana seguinte (deadline terça 1 dez às 18:30). O jogo grande é o Arsenal–Man City (dom 16:30): o Haaland tem só ≈${e(411)}. No H2H defrontas o Sergio Casinha.
    <br><br>
    Recomendação: <b>Cherki → Wirtz</b> e <b>guardar a outra grátis</b> (ficas com 2 para a J${GW_META.next + 1}); capitão <b>Isak</b>; <b>sem chip</b> — o Free Hit fica para a J14.
  `; }
'''
s = s[:a] + NEW + s[b:]

rep("e usá-lo agora obrigava a deixar as duas trocas boas (Cherki → Ødegaard e Doku → Wirtz, ≈+16 em cinco jornadas) para a J13, ficando uma troca atrasado. Com as duas trocas, o teu onze fica com três jogadores no Arsenal–City (Haaland, Calafiori e Ødegaard) e, como diz a OneFPL,",
    "e usá-lo agora atrasava a troca boa desta semana (Cherki → Wirtz) e as grátis guardadas. O teu onze tem três jogadores no Arsenal–City (Haaland, Calafiori e Doku) e, como diz a OneFPL,")
rep("bruno: {why: 'Sem chip (Bruno). O Free Hit daria ≈+4,8 pts a mais do que as duas trocas grátis, quase o mesmo que na J14 (≈+5,4), e usá-lo agora atrasaria as duas trocas boas (Cherki e Doku). Passa para a J14.'}},",
    "bruno: {why: 'Sem chip (Bruno). O Free Hit daria ≈+4,8 pts a mais do que as duas trocas grátis, quase o mesmo que na J14 (≈+5,4), e usá-lo agora atrasaria a troca boa desta semana (Cherki → Wirtz). Passa para a J14.'}},")
rep("  const CAPTAIN_CHANGE = {out:'Erling Haaland', in:'Alexander Isak',", "  const CAPTAIN_CHANGE = {out:'Erling Haaland', in:'Alexander Isak',")
H.write_text(s, encoding='utf-8', newline='\n')
print('J12b aplicado')
