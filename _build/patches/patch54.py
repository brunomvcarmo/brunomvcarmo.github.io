"""V54 (20 out 2026): detetor de jornadas duplas e brancas da 2.ª metade (J20-J38) na app.
Esta semana › Chips: grelha equipas × jornadas, o teu plantel jornada a jornada, plano de chips da 2.ª metade.
Jogos › Jogos da jornada: resumo + ligação. Avisos no Resumo. Procurar e tutorial.
Uso (a partir da raiz): py -X utf8 _build/patches/patch54.py"""
import json, re
from pathlib import Path

H = Path(__file__).resolve().parents[2] / 'index.html'
s = H.read_text(encoding='utf-8')


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:100], s.count(a))
    s = s.replace(a, b)


CSS = r'''
  /* ===== V54: jornadas duplas e brancas (J20-J38) ===== */
  .dgw-legend { display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: 12px; color: var(--muted); margin-top: 10px; }
  .dgw-legend i { display: inline-block; width: 14px; height: 14px; border-radius: 3px; vertical-align: -2px; margin-right: 5px; }
  .dgw-scroll { overflow-x: auto; margin-top: 12px; padding-bottom: 4px; }
  .dgw-grid { display: grid; gap: 2px; min-width: 760px; font: 600 11px/1.1 'IBM Plex Mono', monospace; }
  .dgw-grid .h { color: var(--muted); text-align: center; padding: 4px 0; }
  .dgw-grid .t { padding: 6px 4px 6px 0; white-space: nowrap; color: var(--ink-2); display: flex; align-items: center; gap: 4px; }
  .dgw-grid .t.mine { color: var(--accent); font-weight: 700; }
  .dgw-grid .t small { color: var(--muted); font-weight: 600; }
  .dgw-grid .me { padding: 6px 4px 6px 0; color: var(--accent); font-weight: 700; border-top: 1px solid var(--line); }
  .dgw-grid .mec { text-align: center; padding: 4px 0; border-top: 1px solid var(--line); color: var(--ink-2); line-height: 1.25; }
  .dgw-c { display: flex; align-items: center; justify-content: center; min-height: 26px; border-radius: 4px; color: var(--ink); background: var(--surface-2); cursor: default; }
  .dgw-c.off { box-shadow: inset 0 0 0 2px var(--ink); font-weight: 800; }
  .dgw-cards { display: none; }
  @media (max-width: 560px) {
    .dgw-scroll.has-cards { display: none; }
    .dgw-cards { display: grid; gap: 8px; margin-top: 12px; }
  }
  .dgw-gw { border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px; background: var(--surface); }
  .dgw-gw h4 { margin: 0 0 4px; font-size: 14px; }
  .dgw-gw p { margin: 2px 0; font-size: 13px; color: var(--ink-2); }
  .dgw-plan-list { list-style: none; padding: 0; margin: 12px 0 0; display: grid; gap: 10px; }
  .dgw-plan-list li { border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px; background: var(--surface); }
  .dgw-plan-list li b.g { font-family: 'IBM Plex Mono', monospace; }
  .dgw-path { margin-top: 12px; padding: 10px 12px; border-radius: 10px; background: var(--accent-weak); color: var(--ink); font-size: 14px; }
'''
i = s.index('</style>')
s = s[:i] + CSS + s[i:]

# ---------- HTML: Chips (os dois gestores) e Jogos ----------
rep('        <section class="card" id="chip-plan" style="margin-bottom:16px"></section>\n',
    '        <section class="card" id="chip-plan" style="margin-bottom:16px"></section>\n'
    '        <section class="card" id="dgw-card" style="margin-bottom:16px"></section>\n'
    '        <section class="card" id="dgw-plan" style="margin-bottom:16px"></section>\n')
m = re.search(r'(<div class="subview" data-sub="jornada">\n.*?)(\n      </div>\n      <div class="subview" data-sub="onzes")', s, re.S)
assert m
s = s[:m.end(1)] + '''
        <section class="card" id="dgw-jogos" style="margin-top:16px">
          <h2>Duplas e brancas da 2.ª metade</h2>
          <div class="card-sub">Jornadas J20-J38 em que as equipas podem ficar sem jogo (taças) ou ter dois jogos (jogos adiados remarcados)</div>
          <p class="prose" id="dgw-jogos-sum"></p>
          <button class="btn" type="button" data-dgw-go>Ver a grelha e o plano de chips →</button>
        </section>''' + s[m.end(1):]

JS = r'''
  // ===================================================================
  // V54 (20 out 2026) — Jornadas duplas e brancas da 2.ª metade (J20-J38).
  // Dados: DGW_DATA (_build/pool/dgw_model.py: taças e Europa de research/cups.json, Monte Carlo com Elo).
  // O oficial (calendário da FPL; no site vem do live.json 'fixtures') manda sempre sobre a previsão.
  // Tudo com function/var: refreshForManager pode chamar renderDgw() antes deste bloco.
  // ===================================================================
  function dgwData() {
    const D = JSON.parse(JSON.stringify(DGW_DATA)), G = D.gws;
    const fx = (window.__LIVE || {}).fixtures;
    if (fx && fx.length) {
      const cnt = {}; for (let t = 1; t <= 20; t++) cnt[t] = G.map(() => 0);
      D.postponed = [];
      fx.forEach(([id, ev, h, a]) => { if (ev == null) { D.postponed.push({id, h, a}); return; } const i = G.indexOf(ev); if (i >= 0) { cnt[h][i]++; cnt[a][i]++; } });
      for (let t = 1; t <= 20; t++) {
        D.ob[t] = cnt[t].map(c => c === 0 ? 1 : 0); D.od[t] = cnt[t].map(c => c >= 2 ? 1 : 0);
        G.forEach((g, i) => { if (D.ob[t][i]) D.b[t][i] = 1; if (D.od[t][i]) D.d[t][i] = 1; });
      }
    }
    return D;
  }
  function dgwTeam(t) { return (typeof TEAM_SHORT !== 'undefined' && TEAM_SHORT[t]) || TEAMS[t] || String(t); }
  function dgwWhy(D, t, i) {
    const g = D.gws[i], out = [];
    if (D.ob[t][i]) out.push('branca oficial (sem jogo no calendário da FPL)');
    if (D.od[t][i]) out.push('dupla oficial (dois jogos no calendário da FPL)');
    D.events.forEach(ev => {
      if (ev.gw !== g) return;
      const f = ev.fixtures.find(x => x.h === t || x.a === t); if (!f) return;
      const me = (ev.teams[t] || 0), op = f.h === t ? f.a : f.h;
      out.push(`${ev.round} da ${ev.name} (${ev.date.slice(8, 10)}/${ev.date.slice(5, 7)}): ${dgwTeam(t)} lá ${Math.round(me * 100)}%, ${dgwTeam(op)} ${Math.round((ev.teams[op] || 0) * 100)}% → jogo adiado ${Math.round(f.p * 100)}%`);
    });
    if (!D.od[t][i] && D.d[t][i] >= 0.03) out.push(`dupla ${Math.round(D.d[t][i] * 100)}%: um jogo adiado da J${D.events.map(e => e.gw).join('/J')} remarcado numa semana livre desta jornada`);
    return out.join(' · ');
  }
  function dgwRows(D, mgr) {
    const sq = squadOf(mgr).filter(Boolean);
    const sum = (k, i) => Object.keys(D[k]).reduce((s, t) => s + D[k][t][i], 0);
    const mine = (k, i) => sq.reduce((s, p) => s + ((D[k][p.team] || [])[i] || 0), 0);
    return D.gws.map((g, i) => ({g, i, lb: sum('b', i), ld: sum('d', i), sb: mine('b', i), sd: mine('d', i),
      pb: sq.filter(p => (D.b[p.team] || [])[i] >= 0.2), pd: sq.filter(p => (D.d[p.team] || [])[i] >= 0.2),
      off: Object.keys(D.ob).some(t => D.ob[t][i] || D.od[t][i])}));
  }
  function dgwPlan(mgr) {
    const D = dgwData(), R = dgwRows(D, mgr), sq = squadOf(mgr).filter(Boolean), plan = {};
    const used = {};
    try { (LEAGUE_SQUADS[CMP_ENTRY[mgr]].chips || []).filter(([, g]) => g >= 20).forEach(([n, g]) => { used[{wildcard: 'wc', freehit: 'fh', bboost: 'bb', '3xc': 'tc'}[n]] = g; }); } catch (e) {}
    const fh = R.filter(r => r.lb >= 0.5).sort((a, b) => (b.sb + 0.3 * b.lb) - (a.sb + 0.3 * a.lb))[0];
    if (fh) plan.fh = fh;
    const bb = R.filter(r => r.ld >= 0.5 && (!fh || r.g !== fh.g)).sort((a, b) => (b.ld + 0.5 * b.sd) - (a.ld + 0.5 * a.sd))[0];
    if (bb) plan.bb = bb;
    if (bb) { const w = [bb.g - 2, bb.g - 1, bb.g - 3].find(g => g >= 20 && (!fh || g !== fh.g)); if (w) plan.wc = R.find(r => r.g === w); }
    const star = sq.slice().sort((a, b) => (b.epH || []).reduce((s, v) => s + v, 0) - (a.epH || []).reduce((s, v) => s + v, 0))[0];
    const taken = [plan.fh, plan.bb, plan.wc].filter(Boolean).map(r => r.g);
    if (star) {
      const opts = R.filter(r => !taken.includes(r.g)).map(r => ({r, p: (D.d[star.team] || [])[r.i] || 0})).sort((a, b) => b.p - a.p);
      if (opts[0] && opts[0].p >= 0.15) plan.tc = Object.assign({}, opts[0].r, {star, p: opts[0].p});
      else { const o = R.filter(r => !taken.includes(r.g) && r.ld >= 0.3).sort((a, b) => b.ld - a.ld)[0]; if (o) plan.tc = Object.assign({}, o, {star: null, p: 0}); }
    }
    return {D, R, plan, used, star};
  }
  function dgwEvTxt(D, g) {
    const ev = D.events.filter(e => e.gw === g);
    return ev.map(e => `${e.round} da ${e.name} (${e.date.slice(8, 10)}/${e.date.slice(5, 7)})`).join(' e ');
  }
  function renderDgw() {
    const el = document.getElementById('dgw-card'); if (!el || typeof DGW_DATA === 'undefined') return;
    const mgr = curMgr(), D = dgwData(), G = D.gws, R = dgwRows(D, mgr), sq = squadOf(mgr).filter(Boolean);
    const cnt = {}; sq.forEach(p => { cnt[p.team] = (cnt[p.team] || 0) + 1; });
    const teams = Object.keys(D.b).map(Number).sort((a, b) => dgwTeam(a).localeCompare(dgwTeam(b)));
    const cell = (t, i) => {
      const b = D.b[t][i], d = D.d[t][i], ob = D.ob[t][i], od = D.od[t][i], p = Math.max(b, d);
      if (p < 0.03) return '<span class="dgw-c"></span>';
      const isB = ob || (!od && b >= d), pct = Math.round(p * 100);
      const col = isB ? 'var(--muted)' : 'var(--good)', a = Math.round(18 + 70 * Math.min(1, p));
      return `<span class="dgw-c${ob || od ? ' off' : ''}" style="background:color-mix(in srgb, ${col} ${a}%, var(--surface-2))" title="${dgwTeam(t)} · J${G[i]}: ${dgwWhy(D, t, i).replace(/"/g, "'")}">${ob ? 'B' : od ? 'D' : pct}</span>`;
    };
    const cols = `grid-template-columns: 74px repeat(${G.length}, minmax(32px, 1fr))`;
    const grid = `<div class="dgw-grid" style="${cols}"><span class="h"></span>${G.map(g => `<span class="h">J${g}</span>`).join('')}
      ${teams.map(t => `<span class="t${cnt[t] ? ' mine' : ''}">${dgwTeam(t)}${cnt[t] ? ` <small>${cnt[t]}</small>` : ''}</span>${G.map((g, i) => cell(t, i)).join('')}`).join('')}
      <span class="me">Os teus</span>${R.map(r => `<span class="mec" title="J${r.g}: ≈${r.sb.toFixed(1)} jogadores teus sem jogo, ≈${r.sd.toFixed(1)} com dois jogos">${r.sb >= 0.1 ? `−${r.sb.toFixed(1)}` : ''}${r.sb >= 0.1 && r.sd >= 0.1 ? '<br>' : ''}${r.sd >= 0.1 ? `+${r.sd.toFixed(1)}` : ''}</span>`).join('')}</div>`;
    const notable = R.filter(r => r.off || r.lb >= 0.3 || r.ld >= 0.3);
    const top = (k, i) => teams.map(t => [t, D[k][t][i]]).filter(x => x[1] >= 0.1).sort((a, b) => b[1] - a[1]);
    const cards = notable.map(r => {
      const bl = top('b', r.i), db = top('d', r.i);
      return `<div class="dgw-gw"><h4>J${r.g}${dgwEvTxt(D, r.g) ? ` · ${dgwEvTxt(D, r.g)}` : ''}</h4>
        ${bl.length ? `<p><b>Brancas</b> (≈${r.lb.toFixed(1)} equipas): ${bl.slice(0, 8).map(([t, p]) => `${dgwTeam(t)} ${D.ob[t][r.i] ? 'oficial' : Math.round(p * 100) + '%'}`).join(', ')}</p>` : ''}
        ${db.length ? `<p><b>Duplas</b> (≈${r.ld.toFixed(1)} equipas): ${db.slice(0, 8).map(([t, p]) => `${dgwTeam(t)} ${D.od[t][r.i] ? 'oficial' : Math.round(p * 100) + '%'}`).join(', ')}</p>` : ''}
        <p>Os teus: ${r.sb >= 0.1 ? `≈${r.sb.toFixed(1)} sem jogo` : 'nenhum sem jogo'}${r.sd >= 0.1 ? `, ≈${r.sd.toFixed(1)} com dois jogos` : ''}</p></div>`;
    }).join('');
    const offN = D.postponed.length + teams.reduce((s, t) => s + D.ob[t].reduce((a, v) => a + v, 0) + D.od[t].reduce((a, v) => a + v, 0), 0);
    const squadRows = R.filter(r => r.sb >= 0.05 || r.sd >= 0.05).map(r => `<tr><td>J${r.g}</td>
        <td class="num">${r.sb >= 0.05 ? `≈${r.sb.toFixed(1)}` : '—'}</td><td class="num">${r.sd >= 0.05 ? `≈${r.sd.toFixed(1)}` : '—'}</td>
        <td class="note">${[...r.pb.map(p => `${shortName(p.name)} sem jogo ${D.ob[p.team][r.i] ? '(oficial)' : Math.round(D.b[p.team][r.i] * 100) + '%'}`), ...r.pd.map(p => `${shortName(p.name)} 2 jogos ${D.od[p.team][r.i] ? '(oficial)' : Math.round(D.d[p.team][r.i] * 100) + '%'}`)].join(' · ') || 'probabilidades pequenas'}</td></tr>`).join('');
    el.innerHTML = `<div class="card-head"><div><h2>Duplas e brancas da 2.ª metade (J20-J38)</h2>
        <div class="card-sub">${offN ? `<b>Oficial:</b> ${D.postponed.length ? `${D.postponed.length} jogo(s) adiado(s) sem data nova; ` : ''}as células com contorno já estão no calendário da FPL. ` : 'Nada oficial ainda: o calendário da FPL tem 10 jogos em todas as jornadas. '}O resto é previsão, com a probabilidade em %.</div></div></div>
      <p class="prose">Uma equipa fica <b>sem jogo</b> (branca) quando tem uma ronda de taça no fim de semana da jornada: na 2.ª metade isso deve acontecer na <b>J30</b> (final da Taça da Liga, dom 21 mar) e na <b>J33</b> (meias-finais da Taça de Inglaterra, 24-25 abr). O jogo adiado (o adversário também fica sem jogo) é remarcado numa semana livre a meio e cria uma <b>dupla</b>. As % juntam a probabilidade de cada equipa chegar lá (simulação das taças com a força Elo das equipas) e as semanas livres de cada uma (sem Europa).</p>
      <div class="dgw-legend"><span><i style="background:color-mix(in srgb, var(--muted) 70%, var(--surface-2))"></i>branca (cinzento; mais escuro = mais provável)</span><span><i style="background:color-mix(in srgb, var(--good) 70%, var(--surface-2))"></i>dupla (verde)</span><span><i style="box-shadow:inset 0 0 0 2px var(--ink);background:var(--surface-2)"></i>B/D com contorno = oficial</span><span>número = % · passa o rato numa célula para ver porquê · "Os teus": −sem jogo / +dois jogos (esperado)</span></div>
      <div class="dgw-scroll${cards ? ' has-cards' : ''}">${grid}</div>
      <div class="dgw-cards">${cards}</div>
      <h3 style="margin-top:16px">O teu plantel, jornada a jornada</h3>
      ${squadRows ? `<div class="table-scroll"><table class="form"><thead><tr><th>Jornada</th><th class="num">Sem jogo (esperado)</th><th class="num">Com dois jogos</th><th>Quem</th></tr></thead><tbody>${squadRows}</tbody></table></div>`
        : '<p class="prose">Nenhum jogador do plantel tem uma probabilidade relevante de branca ou dupla.</p>'}
      <p class="note">Atualizado com os dados das taças a ${D.updated} (sorteios, quem continua em prova). Fontes: calendário oficial da FPL, datas das rondas da FA Cup, Taça da Liga e UEFA (research/cups.json). Os números mexem com cada sorteio e resultado.</p>`;
    renderDgwPlan();
    const sum = document.getElementById('dgw-jogos-sum');
    if (sum) {
      const bs = R.filter(r => r.lb >= 0.5).map(r => `J${r.g} (≈${r.lb.toFixed(1)} equipas; ${dgwEvTxt(D, r.g) || 'calendário oficial'})`);
      const ds = R.filter(r => r.ld >= 0.8).sort((a, b) => b.ld - a.ld).slice(0, 3).sort((a, b) => a.g - b.g).map(r => `J${r.g}`);
      sum.innerHTML = `${bs.length ? `Brancas previstas: ${bs.join(' e ')}.` : 'Sem brancas previstas.'} ${ds.length ? `Duplas mais prováveis: ${ds.join(', ')}.` : ''} ${D.postponed.length ? `<b>${D.postponed.length} jogo(s) já adiado(s) pela FPL.</b>` : 'Ainda nada oficial.'}`;
    }
  }
  function renderDgwPlan() {
    const el = document.getElementById('dgw-plan'); if (!el) return;
    const mgr = curMgr(), {D, R, plan, used, star} = dgwPlan(mgr);
    const items = [];
    const usedTxt = c => used[c] ? ` <span class="note">(já usado na J${used[c]})</span>` : '';
    if (plan.fh) items.push({c: 'fh', g: plan.fh.g, t: `É a jornada com mais brancas previstas: ≈${plan.fh.lb.toFixed(1)} equipas sem jogo (${dgwEvTxt(D, plan.fh.g) || 'calendário oficial'})${plan.fh.sb >= 0.3 ? ` e ≈${plan.fh.sb.toFixed(1)} jogadores teus (${plan.fh.pb.map(p => shortName(p.name)).join(', ')})` : ''}. O Free Hit faz uma equipa só com quem joga nessa semana e o plantel volta ao que era na jornada seguinte.`});
    if (plan.wc) items.push({c: 'wc', g: plan.wc.g, t: `Para preparar o Bench Boost da dupla J${plan.bb.g}: com o Wildcard trocas o plantel inteiro e enches os 15 lugares de jogadores das equipas com dois jogos${plan.fh && plan.fh.g > plan.wc.g && plan.fh.g < plan.bb.g ? `; o Free Hit da J${plan.fh.g} resolve a branca pelo meio sem estragar esse plantel` : ''}.`});
    if (plan.bb) items.push({c: 'bb', g: plan.bb.g, t: `A dupla mais provável: ≈${plan.bb.ld.toFixed(1)} equipas com dois jogos (jogos adiados da J${D.events.map(e => e.gw).join(' e da J')} remarcados nas semanas livres). Com o plantel do Wildcard, os 4 suplentes também jogam duas vezes.`});
    if (plan.tc) items.push({c: 'tc', g: plan.tc.g, t: plan.tc.star ? `O teu jogador de mais pontos esperados é o ${shortName(plan.tc.star.name)} (${dgwTeam(plan.tc.star.team)}): é na J${plan.tc.g} que a equipa dele tem mais hipóteses de jogar duas vezes (${Math.round(plan.tc.p * 100)}%). Capitão triplo num jogador com dois jogos.` : `Numa dupla: a J${plan.tc.g} é a 2.ª jornada com mais duplas previstas (≈${plan.tc.ld.toFixed(1)} equipas). Escolher o capitão nessa semana.`});
    items.sort((a, b) => a.g - b.g);
    const name = {fh: 'Free Hit', wc: 'Wildcard', bb: 'Bench Boost', tc: 'Triple Captain'};
    const path = items.map(x => `${name[x.c]} J${x.g}`).join(' → ');
    const fa = (D.reach.facup || {}).SF || {}, efl = (D.reach.eflcup || {}).F || {};
    const topP = o => Object.entries(o).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([t, p]) => `${dgwTeam(+t)} ${Math.round(p * 100)}%`).join(', ');
    el.innerHTML = `<div class="card-head"><div><h2>Plano de chips da 2.ª metade</h2><div class="card-sub">${mgr === 'marco' ? 'Xarola Team' : 'Brunorussia FC'} · as 4 chips voltam na J20 e duram até à J38</div></div></div>
      ${items.length ? `<ul class="dgw-plan-list">${items.map(x => `<li><span class="cp-tag ${x.c}">${({fh: 'FH', wc: 'WC', bb: 'BB', tc: 'TC'})[x.c]}</span><b>${name[x.c]} na <b class="g">J${x.g}</b></b>${usedTxt(x.c)}<br><span class="note">${x.t}</span></li>`).join('')}</ul>
        <div class="dgw-path"><b>O caminho:</b> ${path}.${plan.wc && plan.bb ? ` Wildcard na J${plan.wc.g} para preparar o Bench Boost da dupla J${plan.bb.g}.` : ''}</div>` : '<p class="prose">Ainda não há brancas nem duplas com probabilidade suficiente para fazer um plano.</p>'}
      <p class="note" style="margin-top:12px"><b>Ainda é cedo:</b> as probabilidades vão mudar com os sorteios e resultados. Quem deve chegar à final da Taça da Liga (J30): ${topP(efl) || '—'}. Às meias da FA Cup (J33): ${topP(fa) || '—'}. Decidir de vez depois das meias da Taça da Liga (fev) e dos quartos da FA Cup (3 abr). Previsões publicadas antes da época (Ben Crellin): brancas J30/J33, duplas J32 e J35-36.</p>`;
  }
  // avisos no Resumo: adiamentos oficiais e jornadas que devem ficar brancas para jogadores teus
  function dgwAlerts(add, squad) {
    if (typeof DGW_DATA === 'undefined') return;
    const D = dgwData(), G = D.gws, nm = t => TEAMS[t] || dgwTeam(t);
    D.postponed.forEach(f => {
      const n = squad.filter(p => p.team === f.h || p.team === f.a).length;
      add(n ? 2 : 1, 'Duplas e brancas', `A FPL adiou o ${nm(f.h)}-${nm(f.a)} (sem jornada, data nova por marcar)${n ? ` — ${n} jogador${n > 1 ? 'es' : ''} teu${n > 1 ? 's' : ''}` : ''}.`, {goto: 'semana', gotoSub: 'chips'});
    });
    const seen = lsGet('fpl-dgw-seen') || {}, now = {};
    const out = [];
    G.forEach((g, i) => {
      if (g < GW_META.next) return;
      const tb = Object.keys(D.b).map(Number).filter(t => D.b[t][i] >= 0.25 && squad.some(p => p.team === t));
      Object.keys(D.b).forEach(t => { now[t + '-' + g] = Math.round(Math.max(D.b[t][i], D.d[t][i]) * 100); });
      if (!tb.length) return;
      const n = squad.filter(p => tb.includes(p.team)).length, pmax = Math.max(...tb.map(t => D.b[t][i])), off = tb.some(t => D.ob[t][i]);
      const changed = tb.some(t => seen[t + '-' + g] != null && Math.abs(seen[t + '-' + g] - Math.round(D.b[t][i] * 100)) >= 15);
      out.push({g, n, pmax, off, changed, txt: `A J${g} ${off ? 'fica' : pmax >= 0.5 ? 'deve ficar' : 'pode ficar'} branca para ${tb.sort((a, b) => D.b[b][i] - D.b[a][i]).map(t => `o ${nm(t)}${D.ob[t][i] ? '' : ` (${Math.round(D.b[t][i] * 100)}%)`}`).join(', ').replace(/, ([^,]*)$/, ' e $1')} — ${n} jogador${n > 1 ? 'es' : ''} teu${n > 1 ? 's' : ''}${changed ? '. As probabilidades mudaram desde a tua última visita' : ''}.`});
    });
    out.sort((a, b) => (b.off - a.off) || (b.changed - a.changed) || (b.n * b.pmax - a.n * a.pmax)).slice(0, 2)
      .forEach(o => add(o.off ? 2 : o.changed ? 2 : 1, 'Duplas e brancas', o.txt, {goto: 'semana', gotoSub: 'chips', isNew: o.changed}));
    if (Object.keys(now).length) lsSet('fpl-dgw-seen', now);
  }
  document.addEventListener('click', e => {
    const b = e.target.closest && e.target.closest('[data-dgw-go]'); if (!b) return;
    showView('semana', 'chips');
    setTimeout(() => { const c = document.getElementById('dgw-card'); if (c) c.scrollIntoView({behavior: 'smooth', block: 'start'}); }, 60);
  });
'''
rep("  // V53: conselhos da semana com números lidos dos dados; correm no fim do arranque (depois da calibração)\n",
    JS + "  // V53: conselhos da semana com números lidos dos dados; correm no fim do arranque (depois da calibração)\n")
rep("  function v53Texts() {\n    try {\n", "  function v53Texts() {\n    try { renderDgw(); } catch (e) { console.error(e); }\n    try {\n")
rep("  function refreshForManager(mgr) {\n    document.body.classList.toggle('mgr-marco', mgr === 'marco');\n",
    "  function refreshForManager(mgr) {\n    document.body.classList.toggle('mgr-marco', mgr === 'marco');\n    try { if (typeof dgwData === 'function') renderDgw(); } catch (e) {}\n")
rep("    return A.sort((a, b) => b.sev - a.sev || (b.isNew ? 1 : 0) - (a.isNew ? 1 : 0));",
    "    try { dgwAlerts(add, squad); } catch (e) { console.error(e); }\n    return A.sort((a, b) => b.sev - a.sev || (b.isNew ? 1 : 0) - (a.isNew ? 1 : 0));")

# ---------- Procurar ----------
m = re.search(r'const APP_INDEX = (\[.*?\]);', s)
IDX = json.loads(m.group(1))
k = next(i for i, x in enumerate(IDX) if x['v'] == 'semana' and x['s'] == 'chips')
IDX.insert(k + 1, {'v': 'semana', 's': 'chips', 'a': 'Esta semana', 'n': 'Duplas e brancas (J20-J38)', 'h': 'dgw-card',
                   'syn': ['dupla', 'duplas', 'branca', 'brancas', 'dgw', 'bgw', 'jornada dupla', 'jornada branca', 'double gameweek', 'blank gameweek',
                           'chips segunda metade', 'chips 2.ª metade', 'segunda metade', 'jogos adiados', 'adiado', 'taças']})
s = s[:m.start()] + 'const APP_INDEX = ' + json.dumps(IDX, ensure_ascii=False) + ';' + s[m.end():]
rep("go: () => x.act === 'tour' ? tutWelcome(true) : showView(x.v, x.s)}",
    "go: () => x.act === 'tour' ? tutWelcome(true) : (showView(x.v, x.s), x.h && setTimeout(() => { const e = document.getElementById(x.h); if (e) e.scrollIntoView({block: 'start'}); }, 60))}")

# ---------- tutorial ----------
rep("      {id: 'chips', ix: 'semana/chips', since: 'V27', sel: '#chip-plan', t: 'Chips', d: () => 'O plano de chips até à J19 (as da 1.ª metade perdem-se depois). Toca numa jornada para ver o porquê.'},",
    "      {id: 'chips', ix: 'semana/chips', since: 'V27', sel: '#chip-plan', t: 'Chips', d: () => 'O plano de chips até à J19 (as da 1.ª metade perdem-se depois). Toca numa jornada para ver o porquê.'},\n"
    "      {id: 'dgw', ix: 'semana/chips', since: 'V54', noSimple: true, sel: '#dgw-card', t: 'Duplas e brancas (J20-J38)', d: () => `As jornadas em que as equipas ficam sem jogo (cinzento) ou jogam duas vezes (verde), com a probabilidade. ${tutSafe(() => { const R = dgwRows(dgwData(), curMgr()).filter(r => r.lb >= 0.5); return R.length ? 'Brancas previstas: ' + R.map(r => 'J' + r.g).join(' e ') + '. ' : ''; })}Por baixo, quantos jogadores teus ficam sem jogo ou com dois.`},\n"
    "      {id: 'dgwplan', ix: 'semana/chips', since: 'V54', noSimple: true, sel: '#dgw-plan', t: 'Chips da 2.ª metade', d: () => `Um plano para o Wildcard, Free Hit, Bench Boost e Triple Captain a partir da J20, com o porquê e o caminho. ${tutSafe(() => { const P = dgwPlan(curMgr()).plan; return [P.wc && 'WC J' + P.wc.g, P.fh && 'FH J' + P.fh.g, P.bb && 'BB J' + P.bb.g, P.tc && 'TC J' + P.tc.g].filter(Boolean).join(' · '); })}`},")
rep("      {id: 'jornada', ix: 'jogos/jornada', since: 'V23', sel: '#gw2-body', t: 'Jogos da jornada', d: () => `Os 10 jogos da J${GW_META.next}, com a dificuldade e as odds.`},",
    "      {id: 'jornada', ix: 'jogos/jornada', since: 'V23', sel: '#gw2-body', t: 'Jogos da jornada', d: () => `Os 10 jogos da J${GW_META.next}, com a dificuldade e as odds.`},\n"
    "      {id: 'dgwjogos', ix: 'jogos/jornada', since: 'V54', noSimple: true, sel: '#dgw-jogos', t: 'Duplas e brancas', d: () => 'O resumo das jornadas duplas e brancas da 2.ª metade, com a ligação para a grelha e o plano de chips.'},")
rep("  var APP_VERSION = 'V49';", "  var APP_VERSION = 'V54';")
H.write_text(s, encoding='utf-8', newline='\n')
print('V54 aplicado')
