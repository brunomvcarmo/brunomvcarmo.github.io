"""V53 (20 out 2026): atualização da J8 — textos e tabelas escritos à mão que ficavam presos à J7.
Os números dos conselhos passam a ser lidos do bloco de dados (epAt, FULL_POOL_BY_ID…), para baterem sempre com ele.
Uso (a partir da raiz): py -X utf8 _build/patches/patch53.py"""
import re
from pathlib import Path

H = Path(__file__).resolve().parents[2] / 'index.html'
s = H.read_text(encoding='utf-8')


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:120], s.count(a))
    s = s.replace(a, b)


def rep_re(pat, b, flags=re.S):
    global s
    m = re.search(pat, s, flags)
    assert m, pat[:80]
    s = s[:m.start()] + b + s[m.end():]


# ---------- fichas de jornada no HTML estático (tokens preenchidos por fillGwTokens) ----------
rep("set('gw-n', GW_META.next); set('gw-l', GW_META.last); set('gw-l3', GW_META.last - 2);",
    "set('gw-n', GW_META.next); set('gw-l', GW_META.last); set('gw-l2', GW_META.last - 1); set('gw-l3', GW_META.last - 2);")
rep('(explicação escrita, depois da J6, atalhos)', '(explicação escrita, depois da J<span class="gw-l">7</span>, atalhos)')
rep('<div class="sec-div">Plano J7-J11</div>', '<div class="sec-div">Plano J<span class="gw-n">8</span>-J<span class="gw-n4">12</span></div>')
rep('Confirmado à mão para os 20 gestores: total da J3 mais os pontos das J4, J5 e J<span class="gw-l">6</span> bate com a API.',
    'Totais e pontos da jornada lidos da API oficial (classificação da liga).')
rep('<div class="sec-div">Adversário da J7</div>', '<div class="sec-div">Adversário da J<span class="gw-n">8</span></div>')
rep('Pontos reais nas J4, J5 e J<span class="gw-l">6</span>, por posição. Cobre os jogadores seguidos nesta app (os dois plantéis, adversários H2H e candidatos a transferência), não a liga int',
    'Pontos reais nas J<span class="gw-l3">5</span>, J<span class="gw-l2">6</span> e J<span class="gw-l">7</span>, por posição, entre todos os jogadores com 180+ minutos nessas jornadas (os mais pontuados), não a liga int')
rep('Soma das J4, J5 e J<span class="gw-l">6</span> · jogadores seguidos nesta app', 'Soma das J<span class="gw-l3">5</span>, J<span class="gw-l2">6</span> e J<span class="gw-l">7</span> · os 24 com mais xG + xA (todos os jogadores)')
rep('<div class="sec-div">Calendário J7-J12</div>', '<div class="sec-div">Calendário J<span class="gw-n">8</span>-J<span class="gw-n5">13</span></div>')
rep('Barnes na J<span class="gw-l">6</span>', 'Barnes na J6')
# opções da pesquisa (um <option> não aceita <span>): preenchidas no arranque
rep('<option value="ep1">Pts esperados J7</option>', '<option value="ep1" class="opt-ep1">Pts esperados J8</option>')
m = re.search(r'<option value="([a-z0-9]+)">Probabilidade de 10\+ pts J7</option>', s)
if m:
    s = s.replace(m.group(0), f'<option value="{m.group(1)}" class="opt-p10">Probabilidade de 10+ pts J8</option>')
rep("    const dl = document.getElementById('deadline-label'); if (dl) dl.textContent = GW_META.deadlineLabel;",
    "    const dl = document.getElementById('deadline-label'); if (dl) dl.textContent = GW_META.deadlineLabel;\n"
    "    document.querySelectorAll('.opt-ep1').forEach(o => { o.textContent = 'Pts esperados J' + GW_META.next; });\n"
    "    document.querySelectorAll('.opt-p10').forEach(o => { o.textContent = 'Probabilidade de 10+ pts J' + GW_META.next; });")

# ---------- H2H: quadros e calendário a partir de GW_META.h2h (gerado pelo h2h_week.py) ----------
H2H_FN = r'''  // V53: quadros e calendário H2H a partir de GW_META.h2h[mgr] (resultados até à última jornada, h2h_week.py)
  var H2H_EXTRA = {bruno: {4: '(final)', 6: '(ele teve um hit de −4)'}, marco: {4: '(final)', 5: '(o Tiago jogou o Free Hit)'}};
  function h2hTiles(mgr) {
    const R = (GW_META.h2h[mgr] || {}).results || [], last = R[R.length - 1] || {};
    const pts = R.reduce((s, r) => s + (r.mine > r.theirs ? 3 : r.mine === r.theirs ? 1 : 0), 0);
    return `
      <div class="stat-tile accent"><div class="label">Registo H2H (até J${GW_META.last})</div><div class="value mono">${h2hRecord(mgr === 'marco' ? H2H_RESULTS_MARCO : H2H_RESULTS_BRUNO)}</div></div>
      <div class="stat-tile"><div class="label">Jornada ${last.gw}${GW_META.lastProvisional ? ' (provisória)' : ''}</div><div class="value mono">${last.mine}-${last.theirs}</div></div>
      <div class="stat-tile"><div class="label">Posição na H2H</div><div class="value mono">${GW_META.h2h[mgr].pos}.º de 20 (${pts} pts)</div></div>`;
  }
  function h2hPlayedRows(mgr) {
    const R = (GW_META.h2h[mgr] || {}).results || [], me = mgr === 'marco';
    return R.map(r => {
      const v = r.mine > r.theirs ? (me ? 'ganhou' : 'ganhaste') : r.mine < r.theirs ? (me ? 'perdeu' : 'perdeste') : (me ? 'empatou' : 'empataste');
      const prov = r.gw === GW_META.last && GW_META.lastProvisional;
      return `<tr><td>J${r.gw} (jogada${prov ? ', provisória' : ''})</td><td>${r.opp} (${r.team})</td><td>${r.team}</td><td class="note">${v} ${r.mine}-${r.theirs}${H2H_EXTRA[mgr][r.gw] ? ' ' + H2H_EXTRA[mgr][r.gw] : ''}</td></tr>`;
    }).join('');
  }
  function h2hNextNote(mgr) {
    const e = h2hOppEntry(mgr), O = e && LEAGUE_SQUADS[e]; if (!O) return 'análise completa em baixo';
    const row = LEAGUE_STANDINGS.find(r => r.team === O.tn), gw = GW_META.squadsGw || GW_META.last;
    return `${row ? row.rank + '.º na clássica (' + row.pts + ' pts); ' : ''}capitão na J${gw}: ${O.c}${(O.chips || []).length ? ' · chips usadas: ' + O.chips.map(([c, g]) => ({wildcard: 'WC', freehit: 'FH', bboost: 'BB', '3xc': 'TC'}[c] || c) + ' J' + g).join(', ') : ''}`;
  }
'''
rep("  function renderH2H() {\n", H2H_FN + "  function renderH2H() {\n")
rep_re(r"    document\.getElementById\('h2h-stats'\)\.innerHTML = `.*?`;\n", "    document.getElementById('h2h-stats').innerHTML = h2hTiles('bruno');\n")
rep_re(r"            <tr><td>J1 \(jogada\)</td><td>\$\{H2H_RESULT_GW1\.opponent\}.*?ele teve um hit de −4\)</td></tr>\n", "            ${h2hPlayedRows('bruno')}\n")
rep_re(r"    document\.getElementById\('marco-h2h-stats'\)\.innerHTML = `.*?`;\n", "    document.getElementById('marco-h2h-stats').innerHTML = h2hTiles('marco');\n")
rep_re(r"            <tr><td>J1 \(jogada\)</td><td>\$\{MARCO_H2H_RESULT_GW1\.opponent\}.*?perdeu 61-74</td></tr>\n", "            ${h2hPlayedRows('marco')}\n")
rep_re(r'<td class="note">\$\{s\.detail \? "adversário na J7: .*?" : \'—\'\}</td>', '<td class="note">${s.detail ? h2hNextNote(\'marco\') : \'\'}</td>')
rep("                <td class=\"note\">${s.detail ? 'análise completa em baixo' : ''}</td>", "                <td class=\"note\">${s.detail ? h2hNextNote('bruno') + ' · análise completa em baixo' : ''}</td>")

# ---------- Bruno: transferência, capitão e chips da J8 ----------
rep_re(r"  const SUBS = \[\n.*?\n  \];\n  const CAPTAIN_CHANGE = \{.*?\};\n",
       "  // V53 (20 out 2026): RECOMENDAÇÕES para a J8 — nada disto está aplicado ao plantel (sexta lição).\n"
       "  const SUBS = [\n"
       "    {type:'transfer', out:'Matheus Santos Carneiro da Cunha', in:'Bryan Mbeumo', note:'£7.9M → £7.8M · Cunha 6 min na J7 e fora do onze provável do RotoWire; Mbeumo 4 golos em 7 jornadas, recebe o Bournemouth'},\n"
       "    {type:'transfer', out:'Jan Paul van Hecke', in:'Luka Vušković', note:'opcional (2.ª grátis) · £4.9M → £5.1M · Vušković 27 pts nas J5-J7; seria o 3.º do Brighton'},\n"
       "  ];\n"
       "  const CAPTAIN_CHANGE = {out:'Erling Haaland', in:'Bryan Mbeumo', note:'renhido: Mbeumo ≈' + f1(epAt(FULL_POOL_BY_ID[427], 0)) + ' (Bournemouth em casa) vs Haaland ≈' + f1(epAt(FULL_POOL_BY_ID[411], 0)) + ' (Villa fora, 75% na FPL). Se o Haaland treinar sem limitações na quinta, ele é o capitão com mais teto'};\n")
rep_re(r"  // 13 out 2026 \(V22\): usaste 1 transferência em cada uma das J4, J5 e J6.*?\n  const FREE_TRANSFERS = 1;\n  const NEXT_GW_FREE_TRANSFERS = 2;[^\n]*\n",
       "  // V53: grátis pela regra da FPL depois do Wildcard da J7 (1 + 1 = 2; o Wildcard não gasta). ESTIMATIVA: confirma no site.\n"
       "  const FREE_TRANSFERS = SQUAD_STATE.bruno.ft;\n  const NEXT_GW_FREE_TRANSFERS = Math.min(5, SQUAD_STATE.bruno.ft + 1); // se não usares nenhuma\n")
rep_re(r"  document\.getElementById\('transfer-advice'\)\.innerHTML = `.*?`;\n",
       "  { const P = id => FULL_POOL_BY_ID[id], e = (id, g = 0) => f1(epAt(P(id), g)), e5 = id => f1(P(id).epH.reduce((a, b) => a + b, 0));\n"
       "  document.getElementById('transfer-advice').innerHTML = `Tens <b>${FREE_TRANSFERS} transferências grátis</b> para a J${GW_META.next} (pela regra da FPL depois do Wildcard: confirma no site). "
       "Sugestão: <b>Cunha → Mbeumo</b>. O Cunha jogou 6 minutos na J7 sem lesão marcada e o RotoWire não o põe no onze contra o Bournemouth; "
       "o Mbeumo (£7.8M) marcou 4 golos em 7 jornadas e é o médio com mais pontos esperados na J${GW_META.next}: ≈${e(427)} contra ≈${e(428)} do Cunha (≈${e5(427)} vs ≈${e5(428)} nas próximas cinco). "
       "A 2.ª grátis é opcional: <b>van Hecke → Vušković</b> (£5.1M, ≈${e5(504)} vs ≈${e5(112)} em cinco jornadas; seria o 3.º do Brighton). "
       "Se só fizeres uma, ficas com ${Math.min(5, FREE_TRANSFERS)} grátis para a J${GW_META.next + 1}. O Cherki (0 minutos na J7) fica a vigiar: se voltar a ficar no banco, é o próximo a sair.`; }\n")
rep_re(r"  document\.getElementById\('chip-advice'\)\.innerHTML = `.*?`;\n",
       "  document.getElementById('chip-advice').innerHTML = `<b>Nenhum chip esta semana.</b> Já usaste o Triple Captain (J3) e o Wildcard (J7). Restam o <b>Free Hit</b> e o <b>Bench Boost</b> da 1.ª metade, até ao deadline da J19 (sex 1 jan 2027, 18:30) — depois perdem-se. Plano: <b>Free Hit na J12</b> (Arsenal–Man City) e <b>Bench Boost na J16</b> — ver a linha do tempo acima. Na tua liga, ${Object.values(LEAGUE_SQUADS).filter(L => (L.chips || []).some(([c, g]) => c === 'wildcard' && g === GW_META.last)).length} gestores usaram o Wildcard na J${GW_META.last}.`;\n")
rep_re(r"  document\.getElementById\('gw2-suggestion'\)\.innerHTML = `.*?`;\n",
       "  { const P = id => FULL_POOL_BY_ID[id], e = id => f1(epAt(P(id), 0));\n"
       "  document.getElementById('gw2-suggestion').innerHTML = `\n"
       "    <b>O que aconteceu na J${GW_META.last}:</b> ${(HISTORY.find(h => h.gw === GW_META.last) || {}).points} pts com o <b>Wildcard</b> (média ${(HISTORY.find(h => h.gw === GW_META.last) || {}).avgPoints}). O Haaland capitão fez 13 (×2 = 26), o resto do onze rendeu pouco: o Cherki ficou 0 minutos no banco do City e o Cunha jogou 6. No H2H perdeste 60-76 com o Frederico Borges.\n"
       "    <br><br>\n"
       "    <b>Para a J${GW_META.next} (deadline ${GW_META.deadlineLabel} em Lisboa):</b> o melhor jogo do plantel é o do <b>Saka</b> e do <b>Calafiori</b> (Arsenal recebe o Everton, favorito a 1.38). O <b>Haaland</b> vai a Villa Park e está a 75% na FPL (pancada no pé): ≈${e(411)} pts esperados, já com esse risco. O Brighton (De Cuyper, Verbruggen) vai a Anfield.\n"
       "    <br><br>\n"
       "    Recomendação: transferência <b>Cunha → Mbeumo</b>; capitão <b>Mbeumo</b> (≈${e(427)}) ou <b>Haaland</b> (≈${e(411)}) — quase empatados: se o City disser na quinta que o Haaland está bem, fica com ele (tem mais teto). Vice: o outro dos dois.\n"
       "  `; }\n")

# ---------- Marco: conselhos da J8 ----------
rep_re(r"    document\.getElementById\('marco-todo-list'\)\.innerHTML = `.*?`;\n    document\.getElementById\('marco-todo-note'\)\.textContent = \".*?\";\n",
       "    { const P = id => FULL_POOL_BY_ID[id], e = id => f1(epAt(P(id), 0)), e5 = id => f1(P(id).epH.reduce((a, b) => a + b, 0));\n"
       "    document.getElementById('marco-todo-list').innerHTML = `\n"
       "      <li><b>Capitão: Mbeumo (≈${e(427)}) ou Haaland (≈${e(411)}).</b><span>Quase empatados nos pontos esperados. O Haaland está a 75% na FPL (pancada no pé no fim do jogo com o Ipswich) e vai a Villa Park; o Mbeumo recebe o Bournemouth e marcou 4 golos em 7 jornadas. Se o City disser na quinta que o Haaland está bem, fica com ele (tem mais teto); senão, Mbeumo capitão e Haaland vice.</span></li>\n"
       "      <li><b>Transferências: Neco Williams → Luka Vušković e Bruno Fernandes → Bukayo Saka.</b><span>Tens <strong>${SQUAD_STATE.marco.ft} grátis</strong> (pela regra da FPL: confirma no site). O Bruno Fernandes fez 2, 1 e 1 pts nas últimas jornadas e vários sites sugerem vendê-lo; o Saka (£9.6M) tem ≈${e5(12)} pts esperados nas próximas cinco contra ≈${e5(426)}. O Vušković (£5.1M, 27 pts nas J5-J7) tem ≈${e5(504)} contra ≈${e5(469)} do Neco Williams; seria o 3.º do Brighton, o limite. As duas juntas valem ≈+10 pts nas próximas cinco jornadas (+1 na J${GW_META.next}) e cabem no orçamento (sobram ≈£${(SQUAD_STATE.marco.bank + 5.0 - P(504).price + 11.8 - P(12).price).toFixed(1)}M). Atenção: o Saka também vem de 2, 2 e 3 pts, mas tem os penáltis do Arsenal e o melhor jogo da semana (Everton em casa).</span></li>\n"
       "      <li><b>Onze: o modelo põe o Maguire, o Egan e o Sangare no banco.</b><span>Com as trocas, o Vušković e o Saka entram diretamente no onze. Confirma os onzes prováveis antes do deadline (Jogos › Onzes prováveis).</span></li>\n"
       "    `;\n"
       "    document.getElementById('marco-todo-note').textContent = `Nenhum chip esta semana: o Wildcard, o Free Hit e o Bench Boost continuam disponíveis até à J19 (o Triple Captain foi gasto na J3). Deadline: ${GW_META.deadlineLabel} em Lisboa.`; }\n")
rep_re(r"    document\.getElementById\('marco-subs-note'\)\.innerHTML = `.*?`;\n",
       "    document.getElementById('marco-subs-note').innerHTML = `<b>O que mudou na J${GW_META.last} (confirmado na API):</b> uma transferência real, <b>Igor Jesus → Thierno Barry</b>, sem hits. Capitão Haaland (13×2 = 26); ${(MARCO_HISTORY.find(h => h.gw === GW_META.last) || {}).points} pts no total. <b>A vigiar:</b> o <b>Bruno Fernandes</b> (2, 1 e 1 pts nas últimas três), o <b>Sangare</b> (a perder minutos no Brentford) e o <b>Haaland</b> (75% na FPL). Ver a tabela de pontos esperados abaixo para o detalhe de cada um.`;\n")
rep_re(r"    document\.getElementById\('marco-budget-stats'\)\.innerHTML = `.*?`;\n",
       "    { const st = SQUAD_STATE.marco, val = st.players.reduce((a, q) => a + (FULL_POOL_BY_ID[q.id] || {price: 0}).price, 0);\n"
       "    document.getElementById('marco-budget-stats').innerHTML = `\n"
       "      <div class=\"stat-tile\"><div class=\"label\">Total (hoje)</div><div class=\"value mono\">£${(val + st.bank).toFixed(1)}M</div></div>\n"
       "      <div class=\"stat-tile\"><div class=\"label\">No banco</div><div class=\"value mono\">£${st.bank.toFixed(1)}M</div></div>\n"
       "      <div class=\"stat-tile\"><div class=\"label\">Valor do plantel</div><div class=\"value mono\">£${val.toFixed(1)}M</div></div>\n"
       "    `; }\n")
rep_re(r"    document\.getElementById\('marco-fixture-note'\)\.innerHTML = `.*?`;\n",
       "    { const sq = MARCO_SQUAD_CURRENT.map(p => ({p, t: (FULL_POOL_BY_NAME[p.name] || {}).team})).filter(x => x.t), sw = id => FIXTURE_SWING.find(t => t.id === id);\n"
       "      const by = sq.map(x => ({n: x.p.name, a: (sw(x.t) || {avg: 3}).avg})).sort((a, b) => a.a - b.a), best = by.slice(0, 3), worst = by.slice(-3).reverse();\n"
       "      document.getElementById('marco-fixture-note').innerHTML = `Melhores sequências do plantel nas J${HZ[0]}-J${HZ[0] + 5} (fixture tickers): ${best.map(x => `<b>${shortName(x.n)}</b> (${x.a.toFixed(2)})`).join(', ')}. As mais difíceis: ${worst.map(x => `<b>${shortName(x.n)}</b> (${x.a.toFixed(2)})`).join(', ')}. Tabela completa em Avançado › Tabelas das equipas.`; }\n")

# ---------- perfil de risco dos capitães ----------
rep_re(r"  const CAPTAIN_RISK = \[\n.*?\n  \];\n",
       "  const CAPTAIN_RISK = [\n"
       "    {name:\"Erling Haaland\", profile:\"Aposta de \\\"tudo ou nada\\\"\", note:\"8 golos em 7 jornadas e capitão de 16 dos 20 da tua liga na J7 (13 pts). Esta semana tem uma pancada no pé (75% na FPL) e vai a Villa Park: se não jogar, a braçadeira passa ao vice.\"},\n"
       "    {name:\"Bryan Mbeumo\", profile:\"Retorno mais estável\", note:\"4 golos em 7 jornadas, marca nos jogos fáceis em casa e recebe o Bournemouth. Menos teto do que o Haaland, mas sem dúvida física.\"},\n"
       "    {name:\"João Pedro / Cole Palmer\", profile:\"Meio-termo\", note:\"o Chelsea recebe o Spurs (favorito a 1.67); penáltis e muita bola na área. O The False 9 e o Stats Zone falam deles como alternativas de capitão.\"},\n"
       "  ];\n")

# ---------- trocas sugeridas (campo, avisos, planeador) ----------
rep_re(r"  const SUGGESTED_MOVES = \{\n.*?\n  \};\n",
       "  const SUGGESTED_MOVES = {\n"
       "    bruno: {transfers: [{out: 428, in: 427}], optional: [{out: 112, in: 504}]},\n"
       "    marco: {transfers: [{out: 469, in: 504}, {out: 426, in: 12}], optional: []},\n"
       "  };\n")

# ---------- plano de chips: a J7 já passou; Bruno sem Wildcard (usado na J7) ----------
rep_re(r"    7:  \{why: 'Sem chip\..*?'\},\n", "")
rep("    8:  {why: 'Sem chip. Todas as equipas têm um só jogo até à J19, por isso não há dupla jornada para aproveitar.'},",
    "    8:  {why: 'Sem chip. Todas as equipas têm um só jogo até à J19, por isso não há dupla jornada para aproveitar. O Haaland está a 75%: nunca um Triple Captain numa dúvida.'},")
rep("const KNOWN_CHIP_PLAN = {5191766: {freehit: 12, wildcard: 13, bboost: 16}", "const KNOWN_CHIP_PLAN = {5191766: {freehit: 12, bboost: 16}")

H.write_text(s, encoding='utf-8', newline='\n')
print('V53 aplicado')
