"""V66 (27 nov 2026): usar ou guardar transferências (a pedido: "não quero que me aconselhes sempre a fazer todas as
transferências; às vezes pode ser melhor guardar").
- autoPlan: as grátis que sobram no fim das 5 jornadas passam a valer pontos (ftKeep: 2.ª ≈2, 3.ª ≈1,5, 4.ª ≈1,
  5.ª ≈0,5) — antes valiam 0 e o planeador tendia a gastá-las só porque o horizonte acabava. Aceita opt.firstN
  (número de trocas na 1.ª jornada) e opt.force (trocas fixas na 1.ª jornada) e devolve ftEnd, keep, j1 e first.
- ftCompare(mgr): guardar todas · usar 1 · usar 2 (cada uma com o melhor plano para as jornadas seguintes) e a regra
  FT_RULE: uma troca a mais só é recomendada se render MAIS de 2 pts nas 5 jornadas (contando o valor de guardar;
  no empate, guarda).
- Cartão da sugestão: «Faz esta troca e guarda 1» quando a sugestão não usa todas as grátis, quantas ficam para a
  jornada seguinte, e o botão «Usar ou guardar? Comparar» (contas feitas na hora, com os dados da app).
Uso (a partir da raiz): py -X utf8 _build/patches/patch66.py   (Linux: python3)"""
import re
from pathlib import Path

H = Path(__file__).resolve().parents[2] / 'index.html'
s = H.read_text(encoding='utf-8')


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:100], s.count(a))
    s = s.replace(a, b)


CSS = r'''
  /* ===================== V66: usar ou guardar ===================== */
  .sh-ft { margin-top: 12px; }
  .sh-ft table { width: 100%; border-collapse: collapse; font-size: 13.5px; color: #fff; }
  .sh-ft th { text-align: left; font-size: 10.5px; letter-spacing: .06em; text-transform: uppercase; color: #D9C6F0; font-weight: 700; padding: 0 8px 6px 0; border-bottom: 1px solid rgba(255, 255, 255, .25); }
  .sh-ft td { padding: 7px 8px 7px 0; border-bottom: 1px solid rgba(255, 255, 255, .12); vertical-align: top; }
  .sh-ft td.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; font-family: inherit; font-size: 13.5px; }
  .sh-ft tr.rec td { font-weight: 700; }
  .sh-ft .rec-tag { display: inline-block; font-size: 10.5px; font-weight: 700; color: #41205F; background: #fff; border-radius: 999px; padding: 1px 7px; margin-left: 4px; }
  .sh-ft .note { color: #D9C6F0; }
  .sh-ft tbody tr:hover td { background: transparent; }
'''
rep('</style>', CSS + '</style>')

# ---------- autoPlan: valor das grátis guardadas no fim, trocas fixas na 1.ª jornada ----------
rep("  function autoPlan(mgr, mode) {\n    const st0 = SQUAD_STATE[mgr], strat = stratFor(mgr);",
    "  // V66: valor (em pts) de chegar ao fim das 5 jornadas com ft grátis em vez de 1 — sem isto o planeador gastava-as\n"
    "  // só porque o horizonte acabava. FT_RULE: uma troca a mais só é sugerida se render mais de 2 pts nas 5 jornadas (no empate, guarda).\n"
    "  function ftKeep(ft) { return [0, 0, 2, 3.5, 4.5, 5][Math.min(5, Math.max(0, ft || 0))]; }\n"
    "  var FT_RULE = 2;\n"
    "  function autoPlan(mgr, mode, opt) {\n    opt = opt || {};\n    const st0 = SQUAD_STATE[mgr], strat = stratFor(mgr);")
rep("        opts.forEach(o => {\n          const n = o.moves.length, hits = Math.max(0, n - s.ft) * 4;",
    "        // V66: na 1.ª jornada, um número de trocas fixo (opt.firstN) ou trocas fixas (opt.force)\n"
    "        const forced = k === 0 && opt.force ? (() => { const ids = s.ids.slice(); let cost = 0; opt.force.forEach(m => { const i = ids.indexOf(m.out); if (i >= 0) { ids[i] = m.in; cost += FULL_POOL_BY_ID[m.in].price - s.sell[m.out]; } }); return [{moves: opt.force.filter(m => s.ids.includes(m.out)), ids, cost}]; })() : null;\n"
    "        (forced || opts.filter(o => k > 0 || opt.firstN == null || o.moves.length === opt.firstN)).forEach(o => {\n"
    "          const n = o.moves.length, hits = Math.max(0, n - s.ft) * 4;")
rep("          next.push({ids: o.ids, sell, bank: +(s.bank - o.cost).toFixed(1), ft: Math.min(5, Math.max(0, s.ft - n) + 1), acc: s.acc + pts,\n"
    "            h: s.acc + pts + (k + 1 < HZ.length ? fut(o.ids, k + 1) : 0),",
    "          const ftN = Math.min(5, Math.max(0, s.ft - n) + 1);\n"
    "          next.push({ids: o.ids, sell, bank: +(s.bank - o.cost).toFixed(1), ft: ftN, acc: s.acc + pts,\n"
    "            h: s.acc + pts + (k + 1 < HZ.length ? fut(o.ids, k + 1) : ftKeep(ftN)),")
rep("    const best = beam.sort((a, b) => b.acc - a.acc)[0];\n    const base = HZ.reduce(",
    "    const best = beam.sort((a, b) => (b.acc + ftKeep(b.ft)) - (a.acc + ftKeep(a.ft)))[0];\n    const base = HZ.reduce(")
rep("    let ids = st0.players.map(x => x.id), real = 0, hitsTot = 0;\n",
    "    let ids = st0.players.map(x => x.id), real = 0, hitsTot = 0, j1 = 0;\n")
rep("      real += bestXiValue(ids.map(id => FULL_POOL_BY_ID[id]), k) - h;\n    });\n"
    "    return {moves: best.moves, gain: real - base, hits: hitsTot, bank: best.bank, mode, plainVal};",
    "      real += bestXiValue(ids.map(id => FULL_POOL_BY_ID[id]), k) - h;\n"
    "      if (k === 0) j1 = bestXiValue(ids.map(id => FULL_POOL_BY_ID[id]), 0) - h - bestXiValue(squadOf(mgr).filter(Boolean), 0);\n    });\n"
    "    return {moves: best.moves, gain: real - base, hits: hitsTot, bank: best.bank, mode, plainVal, ftEnd: best.ft, keep: ftKeep(best.ft), j1, first: best.moves.filter(m => m.gw === HZ[0])};")

# o Plano automático também segue a regra: escolhe o nº de trocas da 1.ª jornada com o ftCompare
rep("      setTimeout(() => { try { AUTO.res[mgr + '|' + AUTO.mode] = autoPlan(mgr, AUTO.mode); } catch (e) { console.error(e); }",
    "      setTimeout(() => { try { AUTO.res[mgr + '|' + AUTO.mode] = autoPlanRule(mgr, AUTO.mode); } catch (e) { console.error(e); }")
# ---------- comparar usar e guardar ----------
JS = r'''
  // ---------- V66: usar ou guardar? (guardar todas · usar 1 · usar 2, cada uma com o melhor plano a seguir) ----------
  function ftCompare(mgr) {
    const st = SQUAD_STATE[mgr], R = [];
    [0, 1, 2].forEach(n => { const r = autoPlan(mgr, 'pontos', {firstN: n}); R.push({n, first: r.first, tot: r.gain + r.keep, j1: r.j1, ftEnd: r.ftEnd, hits: Math.max(0, n - st.ft) * 4, next: Math.min(5, Math.max(0, st.ft - n) + 1)}); });
    // a recomendada: começa em guardar todas e só sobe uma troca se ela render MAIS de FT_RULE pts (no empate, guarda)
    let rec = R[0]; R.slice(1).forEach(r => { if (Math.round((r.tot - rec.tot) * 10) / 10 > FT_RULE) rec = r; });   // no empate, guarda
    return {R, rec, ft: st.ft};
  }
  // o Plano automático com a regra: na 1.ª jornada usa o nº de trocas que o ftCompare recomenda (no empate, guarda)
  function autoPlanRule(mgr, mode) {
    const C = ftCompare(mgr); FTC[mgr] = C;
    return autoPlan(mgr, mode, {firstN: C.rec.n});
  }
  var FTC = {};
  function ftCompareHtml(mgr) {
    const C = FTC[mgr]; if (!C) return '';
    const P = id => shortName(FULL_POOL_BY_ID[id].name), g0 = C.R[0].tot;
    const name = r => r.n === 0 ? `Guardar ${C.ft === 1 ? 'a grátis' : C.ft > 1 ? 'as ' + C.ft : ''}` : `Usar ${r.n}${r.hits ? ` (−${r.hits})` : ''}: ${r.first.map(m => `${P(m.out)} → ${P(m.in)}`).join(', ')}`;
    return `<table><thead><tr><th>Opção na J${GW_META.next}</th><th class="num">J${GW_META.next}</th><th class="num">5 jornadas</th></tr></thead><tbody>
      ${C.R.map(r => `<tr${r === C.rec ? ' class="rec"' : ''}><td>${name(r)}${r === C.rec ? '<span class="rec-tag">recomendado</span>' : ''}<br><span class="note">ficas com ${r.next} grátis para a J${GW_META.next + 1}</span></td><td class="num">${sgn(r.j1)}</td><td class="num">${r.n ? sgn(r.tot - g0) : '—'}</td></tr>`).join('')}
      </tbody></table>
      <p class="note" style="margin:6px 0 0">Pontos esperados face a não mexer, com o melhor plano para as jornadas seguintes; «5 jornadas» compara com guardar e já conta o valor de chegar ao fim com grátis guardadas. Uma troca a mais só é recomendada se render mais de ${FT_RULE} pts nas 5 jornadas (no empate, guarda): abaixo disso é ruído, e uma grátis guardada dá margem para lesões e jornadas a meio da semana.</p>`;
  }
  document.addEventListener('click', ev => {
    const b = ev.target.closest('[data-shft]'); if (!b) return;
    const box = b.closest('.sh-ft'), mgr = curMgr(); if (!box) return;
    box.innerHTML = '<p class="note">A calcular as três opções (uns segundos)…</p>';
    setTimeout(() => { try { FTC[mgr] = ftCompare(mgr); } catch (e) { console.error(e); } document.querySelectorAll('.sug-hero .sh-ft').forEach(x => { x.innerHTML = ftCompareHtml(mgr) || '<p class="note">Não consegui fazer as contas.</p>'; }); }, 40);
  });
'''
rep("  // ---------- V65: a sugestão da semana em destaque (Resumo e Transferências) ----------\n",
    JS + "  // ---------- V65: a sugestão da semana em destaque (Resumo e Transferências) ----------\n")

# ---------- cartão: «e guarda 1», quantas ficam, botão de comparar ----------
rep("    const hits = Math.max(0, mv.length - (st.ft || 0)) * 4;\n",
    "    const hits = Math.max(0, mv.length - (st.ft || 0)) * 4;\n"
    "    const save = !fh && !done ? Math.max(0, (st.ft || 0) - mv.length) : 0, ftNext = Math.min(5, Math.max(0, (st.ft || 0) - mv.length) + 1);   // V66\n")
rep("      : mv.length ? `<div class=\"sh-tot\"><span class=\"sh-big\">≈${sgn(G.g1)}</span><span class=\"note\">pts na J${GW_META.next} · ≈${sgn(G.g5)} nas próximas ${HZ.length} · ${hits ? `custa −${hits}` : `usa ${mv.length} de ${st.ft} grátis, sem custo`}</span></div>` : '';",
    "      : mv.length ? `<div class=\"sh-tot\"><span class=\"sh-big\">≈${sgn(G.g1)}</span><span class=\"note\">pts na J${GW_META.next} · ≈${sgn(G.g5)} nas próximas ${HZ.length} · ${hits ? `custa −${hits}` : `usa ${mv.length} de ${st.ft} grátis, sem custo`}${save ? ` · guarda ${save}: ficas com ${ftNext} grátis para a J${GW_META.next + 1}` : ''}</span></div>`\n"
    "      : !fh && !done ? `<div class=\"sh-tot\"><span class=\"note\">Guarda ${st.ft === 1 ? 'a grátis' : 'as ' + st.ft + ' grátis'}: ficas com ${ftNext} para a J${GW_META.next + 1}.</span></div>` : '';")
rep("      <h2>${done ? 'Trocas sugeridas feitas ✓' : fh ? 'Usa o Free Hit' : mv.length ? `Faz ${mv.length === 1 ? 'esta troca' : 'estas ' + mv.length + ' trocas'}` : 'Não mexas no plantel'}",
    "      <h2>${done ? 'Trocas sugeridas feitas ✓' : fh ? 'Usa o Free Hit' : mv.length ? `Faz ${mv.length === 1 ? 'esta troca' : 'estas ' + mv.length + ' trocas'}${save ? ` e guarda ${save === 1 ? '1 transferência' : save + ' transferências'}` : ''}` : 'Guarda as transferências'}")
rep("<button type=\"button\" class=\"btn\" data-goto=\"semana\" data-goto-sub=\"onze\">Ver o onze</button></div>${alt}`;",
    "<button type=\"button\" class=\"btn\" data-goto=\"semana\" data-goto-sub=\"onze\">Ver o onze</button></div>${alt}${!fh && !done && (st.ft || 0) > 0 ? `<div class=\"sh-ft\">${ftCompareHtml(mgr) || '<button type=\"button\" class=\"btn\" data-shft>Usar ou guardar? Comparar</button>'}</div>` : ''}`;")

# ---------- tutorial e versão ----------
m = re.search(r"\n      \{id: 'sughero65', [^\n]*", s); assert m
s = s[:m.end()] + "\n      {id: 'guardar66', ix: 'semana/resumo', since: 'V66', opt: true, sel: '#sug-hero .sh-ft', t: 'Usar ou guardar?', d: () => `Nem sempre compensa usar todas as transferências grátis. O botão «Usar ou guardar? Comparar» faz as contas na hora: guardar todas, usar 1 ou usar 2, cada uma com o melhor plano para as jornadas seguintes. Uma troca a mais só é recomendada se render mais de ${FT_RULE} pontos nas 5 jornadas — até lá (empate incluído), guardar dá mais margem.`}," + s[m.end():]
rep("  var APP_VERSION = 'V65';", "  var APP_VERSION = 'V66';")
H.write_text(s, encoding='utf-8', newline='\n')
print('V66 aplicado')
