"""V65 (27 nov 2026): a sugestão da semana em destaque (a pedido: "quero que as sugestões estejam mais evidenciadas").
- Cartão «A sugestão da app para a J__» no topo de Esta semana › Resumo e de Esta semana › Transferências: as trocas
  (camisola, nome, pontos esperados de quem sai e de quem entra), o capitão e o vice, a chip, o ganho total na
  jornada e nas próximas 5, e os botões «Já fiz — registar» e «Porquê». Os números são lidos dos dados (xiValueW,
  epAt), não escritos à mão. Depois do deadline não aparece.
- Alternativa opcional (SUGGESTED_MOVES[mgr].alt = {why, transfers}): aparece por baixo, com os mesmos números.
  J12: o Bruno acha que o Cherki rende mais do que o Ødegaard esta semana → alternativa a ficar com o Cherki:
  Doku → Wirtz e Dasilva → James Justin (≈+3,9 na J12 contra ≈+4,2 da sugestão; ≈+12,1 contra ≈+15,9 em 5).
- Free Hit (SUGGESTED_MOVES[mgr].fh = [15 ids], .cap / .vice): o cartão mostra a equipa do Free Hit e o capitão dela.
Uso (a partir da raiz): py -X utf8 _build/patches/patch65.py   (Linux: python3)"""
import re
from pathlib import Path

H = Path(__file__).resolve().parents[2] / 'index.html'
s = H.read_text(encoding='utf-8')


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:100], s.count(a))
    s = s.replace(a, b)


CSS = r'''
  /* ===================== V65: a sugestão da semana em destaque ===================== */
  .sug-hero { border: 0; color: #fff; background: linear-gradient(135deg, #5B2C83 0%, #41205F 70%); box-shadow: 0 10px 28px -14px rgba(65, 32, 95, .65); padding: 20px 22px; }
  .sug-hero h2, .sug-hero b, .sug-hero strong { color: #fff; }
  .sug-hero .sh-eye { font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #D9C6F0; margin-bottom: 4px; }
  .sug-hero h2 { font-size: 22px; margin: 0 0 12px; }
  .sh-rows { display: grid; gap: 8px; }
  .sh-row { display: grid; grid-template-columns: 92px minmax(0, 1fr); gap: 10px; align-items: center; background: rgba(255, 255, 255, .09); border: 1px solid rgba(255, 255, 255, .14); border-radius: 12px; padding: 10px 12px; }
  .sh-k { font-size: 11px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: #D9C6F0; }
  .sh-v { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 12px; font-size: 15px; }
  .sh-mv { display: inline-flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .sh-p { display: inline-flex; align-items: center; gap: 6px; font: inherit; color: #fff; background: none; border: 0; padding: 0; cursor: pointer; text-align: left; }
  .sh-p svg { width: 30px; height: 30px; flex: none; filter: drop-shadow(0 1px 1px rgba(0, 0, 0, .25)); }
  .sh-p .nm { font-family: var(--font-display); font-weight: 700; font-size: 18px; line-height: 1.1; }
  .sh-p .ep { font-size: 12px; color: #D9C6F0; font-variant-numeric: tabular-nums; }
  .sh-p.out .nm { opacity: .75; text-decoration: line-through; text-decoration-thickness: 1.5px; }
  .sh-arrow { font-size: 20px; color: #C9A9F0; }
  .sh-tot { margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px 18px; align-items: baseline; }
  .sh-big { font-family: var(--font-display); font-size: 30px; font-weight: 700; line-height: 1; font-variant-numeric: tabular-nums; }
  .sh-tot .note { color: #D9C6F0; }
  .sh-acts { margin-top: 14px; display: flex; flex-wrap: wrap; gap: 8px; }
  .sh-acts .btn { border-color: rgba(255, 255, 255, .45); background: rgba(255, 255, 255, .1); color: #fff; }
  .sh-acts .btn.primary { background: #fff; border-color: #fff; color: #41205F; }
  .sh-acts .btn:hover { background: rgba(255, 255, 255, .2); }
  .sh-acts .btn.primary:hover { background: #EFE8F7; }
  .sh-alt { margin-top: 14px; padding-top: 12px; border-top: 1px dashed rgba(255, 255, 255, .3); font-size: 13.5px; color: #EEE6F8; line-height: 1.55; }
  .sh-alt b { color: #fff; }
  .sh-fh { font-size: 13.5px; color: #EEE6F8; line-height: 1.55; }
  @media (max-width: 520px) {
    .sug-hero { padding: 16px; }
    .sh-row { grid-template-columns: 1fr; gap: 6px; }
    .sh-p .nm { font-size: 16.5px; }
  }
'''
rep('</style>', CSS + '</style>')

# contentores: topo do Resumo e topo das Transferências
rep('<section class="card fav-card" id="fav-card"></section>',
    '<section class="card sug-hero" id="sug-hero" aria-label="A sugestão da app para esta jornada" hidden></section>\n<section class="card fav-card" id="fav-card"></section>')
rep('      <div class="subview" data-sub="transferencias" hidden>\n\n        <div class="mgr-view" data-mgr="bruno">',
    '      <div class="subview" data-sub="transferencias" hidden>\n        <section class="card sug-hero" id="sug-hero-t" aria-label="A sugestão da app para esta jornada" hidden></section>\n\n        <div class="mgr-view" data-mgr="bruno">')

# J12: alternativa para o Bruno (ficar com o Cherki) e a equipa do Free Hit do Marco
rep("    bruno: {transfers: [{out: 399, in: 15}, {out: 400, in: 366}], optional: []},\n"
    "    marco: {transfers: [], optional: []},  // J12: Free Hit (o plantel verdadeiro não muda)\n",
    "    bruno: {transfers: [{out: 399, in: 15}, {out: 400, in: 366}], optional: [],\n"
    "      alt: {why: 'Se preferires ficar com o Cherki (marcou ao Napoli; o RotoWire põe-no no banco no Emirates, outros sites dão-no como titular)', transfers: [{out: 400, in: 366}, {out: 176, in: 332}]}},\n"
    "    marco: {transfers: [], optional: [], cap: 426, vice: 379, fh: [385, 115, 112, 334, 426, 366, 124, 15, 379, 166, 249, 109, 332, 68, 60]},  // J12: Free Hit (o plantel verdadeiro não muda)\n")

JS = r'''
  // ---------- V65: a sugestão da semana em destaque (Resumo e Transferências) ----------
  // Tudo calculado dos dados: pontos esperados de quem sai e de quem entra, ganho na jornada e nas próximas 5.
  function shGain(sq, moves) {
    const a = applyMoves(sq, moves); let g5 = 0; HZ.forEach((g, i) => { g5 += xiValueW(a, i) - xiValueW(sq, i); });
    return {g1: xiValueW(a, 0) - xiValueW(sq, 0), g5, xi: pickXi(a, 0)};
  }
  function shP(p, cls) { return `<button type="button" class="sh-p ${cls || ''}" data-pid="${p.id}">${shirtSvg(p.team, p.cls)}<span><span class="nm">${shortName(p.name)}</span><br><span class="ep">${SHORT(p.team)} · ≈${f1(epAt(p, 0))} pts</span></span></button>`; }
  function shMoves(moves) { return moves.map(m => { const o = FULL_POOL_BY_ID[m.out], n = FULL_POOL_BY_ID[m.in]; return o && n ? `<span class="sh-mv">${shP(o, 'out')}<span class="sh-arrow" aria-label="sai, entra">→</span>${shP(n)}</span>` : ''; }).join(''); }
  function renderSugHero() {
    const els = ['sug-hero', 'sug-hero-t'].map(id => document.getElementById(id)).filter(Boolean); if (!els.length) return;
    const mgr = curMgr(), M = SUGGESTED_MOVES[mgr] || {transfers: []}, st = SQUAD_STATE[mgr];
    const passed = Date.now() >= new Date(GW_META.deadline).getTime();
    if (passed) { els.forEach(e => { e.hidden = true; }); return; }
    const sq = squadOf(mgr).filter(Boolean), mv0 = M.transfers || [], mv = mv0.filter(m => sq.some(p => p.id === m.out)), done = mv0.length && !mv.length, cp = (typeof chipPlanFor === 'function' ? chipPlanFor(mgr) : CHIP_PLAN)[GW_META.next] || {};
    const fh = cp.chip === 'fh' && !cp.used && Array.isArray(M.fh) ? M.fh.map(id => FULL_POOL_BY_ID[id]).filter(Boolean) : null;
    const G = shGain(sq, mv), team = fh && fh.length === 15 ? fh : applyMoves(sq, mv), X = pickXi(team, 0);
    const cap = (M.cap && FULL_POOL_BY_ID[M.cap]) || X.cap, vice = (M.vice && FULL_POOL_BY_ID[M.vice]) || X.vice;
    const hits = Math.max(0, mv.length - (st.ft || 0)) * 4;
    const nextChip = (() => { const P = typeof chipPlanFor === 'function' ? chipPlanFor(mgr) : CHIP_PLAN; const g = Object.keys(P).map(Number).sort((a, b) => a - b).find(k => k > GW_META.next && P[k].chip && !P[k].used); return g ? `${CHIP_NAMES[P[g].chip]} na J${g}` : ''; })();
    const rows = [];
    if (fh) {
      const v = xiValueW(fh, 0), v0 = xiValueW(sq, 0);
      rows.push(`<div class="sh-row"><span class="sh-k">Chip</span><span class="sh-v"><b>Free Hit nesta jornada</b><span class="sh-fh">Uma equipa só para a J${GW_META.next}; o plantel volta ao que era na J${GW_META.next + 1}. As ${st.ft} grátis ficam guardadas.</span></span></div>`);
      rows.push(`<div class="sh-row"><span class="sh-k">Equipa</span><span class="sh-v sh-fh">${X.xi.map(p => shortName(p.name)).join(', ')} · banco ${[...X.benchGk, ...X.benchOut].map(p => shortName(p.name)).join(', ')} · £${fh.reduce((t, p) => t + p.price, 0).toFixed(1)}M · ≈${f1(v)} pts esperados (≈${f1(v0)} sem mexer)</span></div>`);
    } else {
      rows.push(`<div class="sh-row"><span class="sh-k">${mv.length === 1 ? 'Troca' : 'Trocas'}</span><span class="sh-v">${mv.length ? shMoves(mv) : '<b>Nenhuma troca</b>'}</span></div>`);
    }
    rows.push(`<div class="sh-row"><span class="sh-k">Capitão</span><span class="sh-v">${shP(cap)}<span class="sh-fh">vice <b>${shortName(vice.name)}</b> · ${pctR(pAtLeast(cap, 0, 10))} de fazer 10+</span></span></div>`);
    if (!fh) rows.push(`<div class="sh-row"><span class="sh-k">Chip</span><span class="sh-v sh-fh"><b>${cp.chip && !cp.used ? CHIP_NAMES[cp.chip] + ' nesta jornada' : 'Nenhum esta semana'}</b>${nextChip ? ` · a seguir: ${nextChip}` : ''}</span></div>`);
    const tot = fh ? `<div class="sh-tot"><span class="sh-big">≈${sgn(xiValueW(fh, 0) - xiValueW(sq, 0))}</span><span class="note">pts na J${GW_META.next} com o Free Hit, face a não mexer</span></div>`
      : mv.length ? `<div class="sh-tot"><span class="sh-big">≈${sgn(G.g1)}</span><span class="note">pts na J${GW_META.next} · ≈${sgn(G.g5)} nas próximas ${HZ.length} · ${hits ? `custa −${hits}` : `usa ${mv.length} de ${st.ft} grátis, sem custo`}</span></div>` : '';
    let alt = '';
    if (M.alt && (M.alt.transfers || []).length) {
      const A = shGain(sq, M.alt.transfers);
      alt = `<div class="sh-alt">${M.alt.why ? nwEsc(M.alt.why) + ': ' : 'Alternativa: '}<b>${M.alt.transfers.map(m => `${shortName(FULL_POOL_BY_ID[m.out].name)} → ${shortName(FULL_POOL_BY_ID[m.in].name)}`).join(' e ')}</b> — ≈${sgn(A.g1)} na J${GW_META.next} e ≈${sgn(A.g5)} nas próximas ${HZ.length}${mv.length ? ` (a sugestão dá ≈${sgn(G.g1)} e ≈${sgn(G.g5)})` : ''}; capitão ${shortName(A.xi.cap.name)}.</div>`;
    }
    const html = `<div class="sh-eye">A sugestão da app para a J${GW_META.next} · deadline ${GW_META.deadlineLabel}</div>
      <h2>${done ? 'Trocas sugeridas feitas ✓' : fh ? 'Usa o Free Hit' : mv.length ? `Faz ${mv.length === 1 ? 'esta troca' : 'estas ' + mv.length + ' trocas'}` : 'Não mexas no plantel'}${mgr === 'marco' ? ' — Xarola Team' : ''}</h2>
      <div class="sh-rows">${rows.join('')}</div>${tot}
      <div class="sh-acts">${mv.length ? '<button type="button" class="btn primary" data-goto="semana" data-goto-sub="registo">Já fiz — registar</button>' : ''}<button type="button" class="btn" data-goto="semana" data-goto-sub="transferencias">Porquê</button><button type="button" class="btn" data-goto="semana" data-goto-sub="onze">Ver o onze</button></div>${alt}`;
    els.forEach(e => { e.innerHTML = html; e.hidden = false; e.querySelectorAll('[data-goto]').forEach(b => b.addEventListener('click', () => showView(b.dataset.goto, b.dataset.gotoSub))); });
  }
'''
rep("  // o guia antigo passa a abrir as boas-vindas (⚙ \"Ver o tutorial\" chama startTour)\n",
    JS + "  // o guia antigo passa a abrir as boas-vindas (⚙ \"Ver o tutorial\" chama startTour)\n")
# desenhar no arranque e quando muda o gestor ou o registo
rep("    try { renderAoVivo(); } catch (e) { console.error(e); }\n    try { if (typeof NW_READY",
    "    try { renderAoVivo(); } catch (e) { console.error(e); }\n    try { if (typeof SH_READY !== 'undefined' && SH_READY) renderSugHero(); } catch (e) { console.error(e); }   // V65\n    try { if (typeof NW_READY")
rep("  var NW_READY = true;\n", "  var NW_READY = true;\n  var SH_READY = true;\n  try { renderSugHero(); } catch (e) { console.error(e); }   // V65\n")
rep("  function refreshAfterLog() {\n", "  function refreshAfterLog() {\n    try { if (typeof SH_READY !== 'undefined' && SH_READY) setTimeout(renderSugHero, 0); } catch (e) {}   // V65\n")

# tutorial e versão
m = re.search(r"\n      \{id: 'todo', ix: 'semana/resumo'[^\n]*", s); assert m
s = s[:m.start()] + "\n      {id: 'sughero65', ix: 'semana/resumo', since: 'V65', sel: '#sug-hero', t: 'A sugestão da semana', d: () => `O cartão roxo no topo é a sugestão da app para a J${GW_META.next}: as trocas (quem sai, quem entra e os pontos esperados de cada um), o capitão, a chip e quanto se ganha. Quando há uma alternativa razoável, aparece por baixo com os mesmos números. Também está no topo das Transferências. Toca num jogador para abrir a ficha. Depois do deadline desaparece.`}," + s[m.start():]
rep("  var APP_VERSION = 'V64';", "  var APP_VERSION = 'V65';")
H.write_text(s, encoding='utf-8', newline='\n')
print('V65 aplicado')
