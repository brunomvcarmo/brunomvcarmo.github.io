"""J12 (24 nov 2026): recomendações e textos escritos à mão para a J12 (deadline sex 27 nov, 18:30 em Lisboa).
Os números vêm dos dados (epAt…); as frases (quem entra/sai, porquê) são desta semana.
Medido com o planeador da app (autoPlan 'pontos', xiValueW) e com o otimizador da Equipa ideal (optimizeTeam, 1 jornada):
  Bruno (2 grátis): Cherki → Ødegaard + Doku → Wirtz = +4,2 na J12 / +15,9 em 5; Free Hit J12 ≈60,4 vs ≈55,6 com as trocas
         (+4,8), mas na J14 o Free Hit dá ≈+5,4 e usá-lo agora atrasa as duas trocas → Free Hit passa para a J14.
  Marco (2 grátis): Free Hit J12 ≈60,4 vs ≈55,8 com as 2 trocas (Maguire → Hill, Sangare → Ødegaard; +3,1) → +4,6;
         com o Wildcard na J13 as trocas da J12 só contavam uma jornada, e o Free Hit e o Wildcard não gastam as 2 guardadas.
Uso (a partir da raiz): py -X utf8 _build/patches/patch_j12.py"""
import re
from pathlib import Path

H = Path(__file__).resolve().parents[2] / 'index.html'
s = H.read_text(encoding='utf-8')


def rep_re(pat, b):
    global s
    m = re.search(pat, s, re.S)
    assert m, pat[:90]
    s = s[:m.start()] + b + s[m.end():]


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:90]
    s = s.replace(a, b)


# ---------- trocas sugeridas ----------
rep_re(r"  const SUGGESTED_MOVES = \{\n.*?\n  \};\n",
       "  const SUGGESTED_MOVES = {\n"
       "    bruno: {transfers: [{out: 399, in: 15}, {out: 400, in: 366}], optional: []},\n"
       "    marco: {transfers: [], optional: []},  // J12: Free Hit (o plantel verdadeiro não muda)\n"
       "  };\n")
rep_re(r"  // J\d+ \([^)]*\): RECOMENDAÇÕES.*?\n  const SUBS = \[\n.*?\n  \];\n",
       "  // J12 (24 nov 2026): RECOMENDAÇÕES — nada disto está aplicado ao plantel (sexta lição).\n"
       "  const SUBS = [\n"
       "    {type:'transfer', out:'Rayan Cherki', in:'Martin Ødegaard', note:'£7.8M → £6.7M · Cherki a rodar no City; Ødegaard titular no Arsenal, recebe o City'},\n"
       "    {type:'transfer', out:'Jérémy Doku', in:'Florian Wirtz', note:'£7.5M → £7.4M · Wirtz titular no Liverpool (vai a Everton); o Doku vai ao Emirates'},\n"
       "  ];\n")
rep_re(r"  const CAPTAIN_CHANGE = \{.*?\};\n",
       "  const CAPTAIN_CHANGE = {out:'Erling Haaland', in:'Alexander Isak', note:'o Isak vai a Everton (dom 12:00) e tem mais pontos esperados do que o Haaland, que vai ao Emirates depois do Napoli; o Copilot põe o Haaland só em 6.º para capitão'};\n")
rep_re(r"  const CAPTAIN_RISK = \[\n.*?\n  \];\n",
       "  const CAPTAIN_RISK = [\n"
       "    {name:\"Erling Haaland\", profile:\"Aposta de \\\"tudo ou nada\\\"\", note:\"quase toda a liga o tem de capitão. Vai ao Emirates (dom 16:30), cinco dias depois do Napoli: jogo difícil, mas se marcar e não o tiveres de capitão perdes terreno para quase todos.\"},\n"
       "    {name:\"Alexander Isak\", profile:\"Meio-termo\", note:\"o capitão sugerido ao Bruno. Dérbi em Everton (dom 12:00), três dias e meio depois de Bruges; foi convocado para a Liga dos Campeões.\"},\n"
       "    {name:\"Bruno Fernandes\", profile:\"Diferencial (Free Hit do Marco)\", note:\"o Man Utd recebe o Brentford (sáb 15:00); é o capitão n.º 1 do Copilot (≈6,2). Só faz sentido para quem o mete no Free Hit.\"},\n"
       "  ];\n")

# ---------- plano de chips: Bruno passa o Free Hit para a J14; o Marco mantém J12 + Wildcard J13 ----------
rep_re(r"  const CHIP_PLAN = \{\n.*?\n  \};\n",
       "  const CHIP_PLAN = {\n"
       "    12: {chip: 'fh', why: 'Free Hit (Marco): o Arsenal–Man City e o Raya em dúvida prendem o plantel; a equipa do Free Hit dá ≈+4,6 pts a mais do que as duas trocas grátis (contas de 24 nov) e o plantel volta ao que era na J13, onde entra o Wildcard.',\n"
       "         bruno: {why: 'Sem chip (Bruno). O Free Hit daria ≈+4,8 pts a mais do que as duas trocas grátis, quase o mesmo que na J14 (≈+5,4), e usá-lo agora atrasaria as duas trocas boas (Cherki e Doku). Passa para a J14.'}},\n"
       "    13: {chip: 'wc', why: 'Wildcard (Marco): jornada a meio da semana (deadline ter 1 dez às 18:30 em Lisboa). Refaz o plantel a pensar nas J13-J19 e no Bench Boost da J16; as 2 grátis guardadas ficam.'},\n"
       "    14: {why: 'Sem chip. Afinar o plantel do Wildcard e garantir quatro suplentes que joguem, para o Bench Boost da J16.',\n"
       "         bruno: {chip: 'fh', why: 'Free Hit (Bruno): pelas contas de 24 nov é a jornada em que o Free Hit mais rende (≈+5,4 pts sobre o plantel com as trocas planeadas). Confirmar na semana, com lesões e rotação.'}},\n"
       "    15: {why: 'Sem chip. Última jornada para acertar o banco antes do Bench Boost.'},\n"
       "    16: {chip: 'bb', why: 'Bench Boost: o Haaland recebe o Hull e as duas jornadas à volta não são a meio da semana (a Premier League também aponta a J16). Os 4 suplentes contam pontos.'},\n"
       "    17: {why: 'Sem chip. Época festiva com muita rotação: evitar o Bench Boost aqui e na J18.'},\n"
       "    18: {why: 'Sem chip. Terceira jornada em pouco mais de uma semana — rotação alta.'},\n"
       "    19: {end: true, why: 'Último prazo dos chips da 1.ª metade: deadline sex 1 jan 2027, 18:30 em Lisboa (valor da API; alguns artigos dizem sáb 2 jan). Os chips que sobrarem perdem-se — não passam para a 2.ª metade.'},\n"
       "  };\n")
rep("    const P = JSON.parse(JSON.stringify(CHIP_PLAN));\n",
    "    const P = JSON.parse(JSON.stringify(CHIP_PLAN));\n"
    "    // J12: o plano pode ser diferente para cada gestor (ex.: 12: {chip: 'fh', …, bruno: {why: …}})\n"
    "    Object.keys(P).forEach(k => { const o = P[k][mgr]; delete P[k].bruno; delete P[k].marco; if (o) P[k] = o; });\n")
rep("const KNOWN_CHIP_PLAN = {5191766: {freehit: 12, bboost: 16}, 1973102: {freehit: 12, wildcard: 13, bboost: 16}};",
    "const KNOWN_CHIP_PLAN = {5191766: {freehit: 14, bboost: 16}, 1973102: {freehit: 12, wildcard: 13, bboost: 16}};")
rep_re(r"  document\.getElementById\('chip-advice'\)\.innerHTML = `.*?`;\n",
       "  document.getElementById('chip-advice').innerHTML = `<b>Nenhum chip esta semana: o Free Hit passa da J12 para a J14.</b> Medido com a app (24 nov): com o Free Hit, a melhor equipa da J12 daria ≈60,4 pts esperados contra ≈55,6 do teu plantel com as duas trocas grátis — <b>≈+4,8</b>. Mas na J14 o Free Hit rende o mesmo ou mais (≈+5,4), e usá-lo agora obrigava a deixar as duas trocas boas (Cherki → Ødegaard e Doku → Wirtz, ≈+16 em cinco jornadas) para a J13, ficando uma troca atrasado. Com as duas trocas, o teu onze fica com três jogadores no Arsenal–City (Haaland, Calafiori e Ødegaard) e, como diz a OneFPL, gastar o Free Hit para ganhar pouco mais do que duas trocas não compensa. Restam o <b>Free Hit</b> (plano: J14) e o <b>Bench Boost</b> (J16), até ao deadline da J19 (sex 1 jan 2027, 18:30) — depois perdem-se. Se até sexta houver más notícias (Isak, Wirtz ou Ødegaard fora), revê: o Free Hit na J12 volta a fazer sentido.`;\n")

# ---------- textos da semana (v53Texts) ----------
QUANDO = ("A Europa joga-se de terça a quinta (City ter, Liverpool qua). Faz as trocas na <b>quinta à noite ou sexta de manhã</b>, "
          "depois dos onzes e das notícias da Liga dos Campeões. Deadline <b>sexta 27 às 18:30</b>; a J13 vem logo a seguir, a meio da semana (deadline terça 1 dez às 18:30).")
FH_IDS = [385, 115, 112, 334, 426, 366, 124, 15, 379, 166, 249, 109, 332, 68, 60]
a = s.index("      { const P = id => FULL_POOL_BY_ID[id], e = id => v53f1(epAt(P(id), 0)), e5 = id => v53f1(P(id).epH.reduce((a, b) => a + b, 0)), el = document.getElementById('bruno-todo-list');")
b = s.index("    } catch (e) { console.error(e); }\n  }\n  v53Texts();")
NEW = r'''      { const P = id => FULL_POOL_BY_ID[id], e = id => v53f1(epAt(P(id), 0)), e5 = id => v53f1(P(id).epH.reduce((a, b) => a + b, 0)), el = document.getElementById('bruno-todo-list');
      const bAfter = (() => { const st = SQUAD_STATE.bruno, sell = id => (st.players.find(q => q.id === id) || {}).sell || 0; return (st.bank + sell(399) + sell(400) - P(15).price - P(366).price).toFixed(1); })();
      if (el) el.innerHTML = `
        <li><b>Quando: quinta à noite ou sexta de manhã.</b><span>__QUANDO__</span></li>
        <li><b>Transferências (tens ${SQUAD_STATE.bruno.ft} grátis): Cherki → Ødegaard e Doku → Wirtz.</b><span>Os dois do City vão ao Emirates e o Cherki continua a rodar. O Ødegaard (£${P(15).price.toFixed(1)}M, titular no Arsenal) tem ≈${e(15)} pts esperados na J${GW_META.next} contra ≈${e(399)} do Cherki (≈${e5(15)} vs ≈${e5(399)} nas próximas cinco); o Wirtz (£${P(366).price.toFixed(1)}M, vai a Everton) tem ≈${e(366)} contra ≈${e(400)} do Doku (≈${e5(366)} vs ≈${e5(400)}). Juntas valem ≈+4,2 pts na J${GW_META.next} e ≈+16 em cinco jornadas, sem custo; ficas com £${bAfter}M no banco.</span></li>
        <li><b>Capitão: Isak (≈${e(379)}), vice Wirtz (≈${e(366)}).</b><span>O Haaland (≈${e(411)}) vai ao Emirates, cinco dias depois do Napoli. Quase toda a liga o tem de capitão (o Sergio Casinha, teu adversário no H2H, também): se preferires não arriscar, a diferença é de ≈${v53f1(epAt(P(379), 0) - epAt(P(411), 0))} pts.</span></li>
        <li><b>Onze: ${(() => { const r = pickXi(applyMoves(squadOf('bruno').filter(Boolean), SUGGESTED_MOVES.bruno.transfers), 0); return `com as trocas, banco ${[...r.benchGk, ...r.benchOut].map(p => shortName(p.name)).join(' → ')}`; })()}.</b><span>Sem chip esta semana: o Free Hit passa para a J14 (ver Chips). Antes do deadline vê os onzes prováveis em Jogos › Onzes prováveis — depois da Europa há sempre rotação.</span></li>`;
      const n = document.getElementById('bruno-todo-note'); if (n) n.textContent = `Deadline: ${GW_META.deadlineLabel} em Lisboa. Nenhum chip esta semana; plano: Free Hit na J14 e Bench Boost na J16.`; }
  { const P = id => FULL_POOL_BY_ID[id], e = (id, g = 0) => v53f1(epAt(P(id), g)), e5 = id => v53f1(P(id).epH.reduce((a, b) => a + b, 0));
  document.getElementById('transfer-advice').innerHTML = `Tens <b>${FREE_TRANSFERS} transferências grátis</b> para a J${GW_META.next} (na J${GW_META.last} não fizeste nenhuma; confirmado no site). Sugestão: <b>Cherki → Ødegaard</b> e <b>Doku → Wirtz</b>. O Ødegaard dá ≈${e(15)} contra ≈${e(399)} do Cherki na J${GW_META.next} (≈${e5(15)} vs ≈${e5(399)} em cinco jornadas); o Wirtz dá ≈${e(366)} contra ≈${e(400)} do Doku (≈${e5(366)} vs ≈${e5(400)}). As duas sem custo; juntas ≈+4,2 na J${GW_META.next} e ≈+16 em cinco. É também o que o planeador automático escolhe para a J${GW_META.next}. Faz as trocas depois da Europa (quinta à noite ou sexta de manhã).`; }
  { const P = id => FULL_POOL_BY_ID[id], e = id => v53f1(epAt(P(id), 0)), H = HISTORY.find(h => h.gw === GW_META.last) || {};
  document.getElementById('gw2-suggestion').innerHTML = `
    <b>O que aconteceu na J${GW_META.last}:</b> ${H.points} pts (média ${H.avgPoints}). Sem transferências; capitão Haaland (2 pts). No H2H ganhaste 34-24 ao Tiago Guerreiro.
    <br><br>
    <b>Para a J${GW_META.next} (deadline ${GW_META.deadlineLabel} em Lisboa):</b> a Europa joga-se a meio da semana (24-26 nov) e a J${GW_META.next + 1} vem logo a seguir, a meio da semana seguinte (deadline terça 1 dez às 18:30). O jogo grande é o Arsenal–Man City (dom 16:30): o Haaland tem só ≈${e(411)}. No H2H defrontas o Sergio Casinha.
    <br><br>
    Recomendação: <b>Cherki → Ødegaard</b> e <b>Doku → Wirtz</b> (duas grátis); capitão <b>Isak</b>, vice <b>Wirtz</b>; <b>sem chip</b> — o Free Hit fica para a J14.
  `; }
    { const P = id => FULL_POOL_BY_ID[id], e = id => v53f1(epAt(P(id), 0));
    const FH = __FH_IDS__.map(P), fhX = pickXi(FH, 0), fhV = v53f1(xiValueW(FH, 0));
    const mSq = squadOf('marco').filter(Boolean), mV = v53f1(xiValueW(mSq, 0)), mV2 = v53f1(xiValueW(applyMoves(mSq, [{out: 418, in: 60}, {out: 565, in: 15}]), 0));
    const fhCost = FH.reduce((t, p) => t + p.price, 0).toFixed(1), mBud = (SQUAD_STATE.marco.bank + SQUAD_STATE.marco.players.reduce((t, x) => t + x.sell, 0)).toFixed(1);
    document.getElementById('marco-todo-list').innerHTML = `
      <li><b>Chip: Free Hit nesta jornada.</b><span>Medido com a app: a melhor equipa de Free Hit da J${GW_META.next} dá ≈${fhV} pts esperados, contra ≈${mV2} com as duas trocas grátis (Maguire → Hill e Sangare → Ødegaard) e ≈${mV} sem mexer. Como o plano tem o Wildcard na J${GW_META.next + 1}, as trocas desta semana só contavam uma jornada. Livras-te do Raya (50%, ombro), do Haaland no Emirates e do Maguire (4 amarelos) só por uma semana, e as ${SQUAD_STATE.marco.ft} grátis ficam guardadas (o Free Hit e o Wildcard não as gastam).</span></li>
      <li><b>A equipa do Free Hit (£${fhCost}M de £${mBud}M):</b><span>${fhX.xi.map(p => shortName(p.name)).join(', ')}; banco ${[...fhX.benchGk, ...fhX.benchOut].map(p => shortName(p.name)).join(', ')}. É a Equipa ideal de 1 jornada (Jogadores › Equipa ideal) com os dados de 24 nov — confirma lá antes de a montar, porque muda com as notícias.</span></li>
      <li><b>Capitão: Bruno Fernandes (≈${e(426)}), vice Isak (≈${e(379)}).</b><span>O Man Utd recebe o Brentford (sáb 15:00); é o capitão n.º 1 do Copilot. O Haaland fica de fora do Free Hit (≈${e(411)} no Emirates).</span></li>
      <li><b>Sem Free Hit?</b><span>Se preferires guardá-lo, as duas grátis seriam Maguire → Hill e Sangare → Ødegaard (≈+${v53f1(xiValueW(applyMoves(mSq, [{out: 418, in: 60}, {out: 565, in: 15}]), 0) - xiValueW(mSq, 0))} na J${GW_META.next}), com capitão Groß ou Jackson. Mas o Free Hit agora rende mais.</span></li>
    `;
    document.getElementById('marco-todo-note').textContent = `Plano de chips: Free Hit na J12, Wildcard na J13 (deadline terça 1 dez às 18:30) e Bench Boost na J16 (o Triple Captain foi gasto na J3); os chips da 1.ª metade perdem-se depois da J19. Deadline: ${GW_META.deadlineLabel} em Lisboa.`;
    document.getElementById('marco-subs-note').innerHTML = `<b>O que mudou na J${GW_META.last} (confirmado na API):</b> sem transferências; capitão Haaland (2 pts ×2); ${(MARCO_HISTORY.find(h => h.gw === GW_META.last) || {}).points} pts, e perdeste o H2H 27-28 com o rui moreira. Na J${GW_META.next} defrontas o Pedro Guerreiro. <b>A vigiar:</b> o <b>Raya</b> (50%, ombro; dúvida para o City), o <b>Maguire</b> (4 amarelos) e o <b>Sangare</b> (poucos pontos). Com o Free Hit nada disto conta na J${GW_META.next}; conta para o Wildcard da J${GW_META.next + 1}.`; }
'''.replace('__QUANDO__', QUANDO).replace('__FH_IDS__', str(FH_IDS))
s = s[:a] + NEW + s[b:]
H.write_text(s, encoding='utf-8', newline='\n')
print('J12 aplicado')
