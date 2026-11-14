
  // ===================================================================
  // V62 (11 nov 2026) — Laboratório (Jogadores › Laboratório): experiências de equipas que não mexem na equipa
  // verdadeira, comparação lado a lado, equipas fantasma (pontos reais jornada a jornada) e comandos em texto.
  //   Guardado no browser: localStorage "fpl-lab" = {bruno: {list, sel, cmp, seeded}, marco: {…}}.
  //   Do repositório (criadas pelo Claude Code, só de leitura na app): lab/experiments.json.
  //   Fotografias do conselho da app antes de cada deadline: lab/advice.json (_build/pool/lab.py conselho).
  //   Pontos reais: history/points-J<n>.json (GitHub Action) ou, se faltarem, os do bloco de dados (POOL24).
  //   Nada aqui escreve no SQUAD_STATE nem no registo de transferências (sexta lição).
  //   Cópia de partida deste bloco: _build/patches/lab62.js (aplicado por patch62.py).
  // ===================================================================
  var LAB = {store: null, repo: [], advice: {}, hist: {}, remote: 0, lu: {}, simc: {}, trash: null, busy: false,
    ui: {pick: null, move: null, out: null, h: 5, q: '', pos: '', team: '', price: '', fit: false, sort: 'ep5', more: 10, io: '', msg: null, gfrom: null, gmode: 'frozen', plgw: null}};
  var LAB_NEED = {gk: 2, def: 5, mid: 5, fwd: 3};
  var LAB_MODE = {
    frozen: ['Congelada', 'fica como está: os mesmos 15, o mesmo onze, capitão e ordem do banco em todas as jornadas'],
    advice: ['Segue o conselho da app', 'em cada jornada aplica a troca e o capitão que a app aconselhou antes do deadline (as fotografias do conselho); o que não couber nesta equipa fica por fazer, com o motivo'],
    plan: ['Segue um plano meu', 'aplica as trocas que marcares em cada jornada (e o capitão, se o escolheres)']};
  var LAB_COLORS = ['#7B4FB8', '#E08A00', '#1E9E5A', '#2E6FD2', '#C2384A', '#0E8A8A'];
  var LAB_SRC = {raiz: 'de raiz', plantel: 'a partir do plantel', ideal: 'da Equipa ideal', simulada: 'da Equipa simulada', rival: 'do plantel de um rival', claude: 'pelo Claude Code', importada: 'importada de outro dispositivo'};
  var LAB_CLUB = {city: 15, 'man city': 15, 'manchester city': 15, united: 16, 'man utd': 16, 'man united': 16, 'manchester united': 16, spurs: 19, tottenham: 19, forest: 18, nottingham: 18, villa: 2, palace: 8, newcastle: 17, liverpool: 14, arsenal: 1, chelsea: 6, brighton: 5, everton: 9, leeds: 13};

  // ---------- guardar ----------
  function labStore() {
    if (!LAB.store) {
      const a = lsGet('fpl-lab') || {}; LAB.store = {};
      ['bruno', 'marco'].forEach(m => { const s = a[m] || {}; LAB.store[m] = {list: Array.isArray(s.list) ? s.list.filter(x => x && x.id && Array.isArray(x.ids)) : [], sel: s.sel || null, cmp: Array.isArray(s.cmp) ? s.cmp : [], seeded: !!s.seeded}; });
    }
    return LAB.store;
  }
  function labS(mgr) { return labStore()[mgr || curMgr()]; }
  function labSave() { lsSet('fpl-lab', labStore()); }
  function labRepo() { const m = curMgr(); return LAB.repo.filter(x => !x.mgr || x.mgr === m || x.mgr === 'ambos'); }
  function labList() { return [...labS().list, ...labRepo()]; }
  function labGet(id) { return labList().find(x => x.id === id) || null; }
  function labCur() { return labGet(labS().sel) || labList()[0] || null; }
  function labNewId() { return 'x' + Date.now().toString(36) + Math.floor(Math.random() * 46656).toString(36); }
  function labToday() { return new Date().toISOString().slice(0, 10); }
  function labName(n) { const L = labList().map(x => x.name); if (!L.includes(n)) return n; let k = 2; while (L.includes(`${n} (${k})`)) k++; return `${n} (${k})`; }
  function labPn(id) { const p = FULL_POOL_BY_ID[id]; return p ? shortName(p.name) : 'jogador ' + id; }
  function labPct(v) { return Math.round((v || 0) * 100) + '%'; }
  function labM(v) { return (Math.abs(v) < 0.05 ? 0 : v).toFixed(1); }   // £M sem "-0.0"
  function labNew(o) {
    const x = Object.assign({id: labNewId(), name: 'Experiência', gw: GW_META.next, created: labToday(), budget: 100, bmode: 'livre', ids: [], locked: [], cap: null, vice: null, xi: null, bench: null, auto: true, note: '', src: 'raiz', ghost: null}, o || {});
    x.ids = [...new Set(x.ids)].filter(id => FULL_POOL_BY_ID[id]).slice(0, 15); x.locked = (x.locked || []).filter(id => x.ids.includes(id));
    x.name = labName(String(x.name || 'Experiência').slice(0, 60)); x.budget = +(+x.budget || 100).toFixed(1);
    const S = labS(); S.list.unshift(x); S.sel = x.id; LAB.ui.pick = LAB.ui.move = LAB.ui.out = null; labSave(); return x;
  }
  function labCopyOf(x, keepGhost) {
    const c = JSON.parse(JSON.stringify(x)); delete c.repo; delete c.mgr;
    c.id = labNewId(); c.name = labName(x.name + ' (cópia)'); c.created = labToday(); if (!keepGhost) c.ghost = null; if (x.repo) c.src = 'claude';
    const S = labS(); S.list.unshift(c); S.sel = c.id; LAB.ui.pick = LAB.ui.move = LAB.ui.out = null; labSave(); return c;
  }
  function labMyBudget(mgr) {
    mgr = mgr || curMgr();
    try { const B = budgetOf(CMP_ENTRY[mgr], LEAGUE_SQUADS); return {market: B.market, real: B.real}; }
    catch (e) { const v = +(labCost(squadOf(mgr).filter(Boolean)) + (SQUAD_STATE[mgr].bank || 0)).toFixed(1); return {market: v, real: v}; }
  }
  function labFromSquad() { const mgr = curMgr(); return labNew({name: 'O meu plantel (cópia)', ids: squadOf(mgr).filter(Boolean).map(p => p.id), budget: labMyBudget(mgr).market, bmode: 'mercado', src: 'plantel'}); }
  function labFromIdeal() {
    const mgr = curMgr(), s = idlState().s, budget = idlBudget(s);
    let r = IDL.res[idlKey(s)] || (IDL.shown[mgr] && IDL.shown[mgr].h === s.h ? IDL.shown[mgr].r : null);
    if (!r) r = optimizeTeam({budget, locked: s.locked, gis: s.h === 5 ? HZ.map((g, i) => i) : [0], seeds: [squadOf(mgr).filter(Boolean).map(p => p.id)], iters: 3});
    if (!r) return null;
    return labNew({name: `Equipa ideal ${s.h === 5 ? `J${HZ[0]}-J${HZ[HZ.length - 1]}` : 'J' + HZ[0]}`, ids: r.ids.slice(), locked: s.locked.filter(id => r.ids.includes(id)), budget, src: 'ideal'});
  }
  function labFromSim() { const st = STORE.sim && STORE.sim[curMgr()]; if (!st || !st.ids || !st.ids.length) return null; return labNew({name: 'Equipa simulada', ids: st.ids.slice(), budget: st.budget, src: 'simulada'}); }
  function labFromRival(e) {
    const L = LEAGUE_SQUADS[e]; if (!L) return null;
    const ids = [...L.s, ...L.b], ps = ids.map(id => FULL_POOL_BY_ID[id]).filter(Boolean);
    return labNew({name: `${L.tn} (${L.m})`, ids, budget: +(labCost(ps) + (L.bank || 0)).toFixed(1), bmode: 'mercado', src: 'rival', from: +e});
  }
  // primeira visita: passa a Equipa simulada que já exista para o Laboratório e cria uma cópia do plantel para começar
  function labSeed() {
    const S = labS(); if (S.seeded || window.__LAB_TOOL) return;
    S.seeded = true;
    try { if (!S.list.length) { labFromSim(); labFromSquad(); } } catch (e) { console.error(e); }
    labSave();
  }

  // ---------- regras da FPL: 2-5-5-3, máximo 3 por clube, orçamento — sempre com o motivo ----------
  function labPs(x) { return (x.ids || []).map(id => FULL_POOL_BY_ID[id]).filter(Boolean); }
  function labCost(ps) { return ps.reduce((s, p) => s + p.price, 0); }
  function labWhyNot(p, ps, budget) {
    if (ps.some(q => q.id === p.id)) return 'já está na equipa';
    if (ps.filter(q => q.cls === p.cls).length >= LAB_NEED[p.cls]) return `já tens ${LAB_NEED[p.cls]} ${POS_SHORT[p.cls]} (a regra é 2-5-5-3)`;
    if (ps.filter(q => q.team === p.team).length >= 3) return `já tens 3 do ${SHORT(p.team)} (máximo 3 por clube)`;
    const over = labCost(ps) + p.price - budget;
    if (over > 1e-9) return `não cabe no orçamento: faltam £${over.toFixed(1)}M`;
    return '';
  }
  function labProblems(x) {
    const ps = labPs(x), out = [], n = {gk: 0, def: 0, mid: 0, fwd: 0}, cl = {};
    ps.forEach(p => { n[p.cls]++; cl[p.team] = (cl[p.team] || 0) + 1; });
    const miss = Object.keys(LAB_NEED).filter(c => n[c] < LAB_NEED[c]).map(c => `${LAB_NEED[c] - n[c]} ${POS_SHORT[c]}`);
    if (miss.length) out.push(`faltam ${miss.join(', ')}`);
    Object.keys(LAB_NEED).filter(c => n[c] > LAB_NEED[c]).forEach(c => out.push(`tem ${n[c]} ${POS_SHORT[c]} (o máximo são ${LAB_NEED[c]})`));
    Object.keys(cl).filter(t => cl[t] > 3).forEach(t => out.push(`tem ${cl[t]} jogadores do ${SHORT(+t)} (o máximo são 3 por clube)`));
    const over = labCost(ps) - x.budget;
    if (over > 1e-9) out.push(`passa o orçamento em £${over.toFixed(1)}M`);
    return out;
  }
  function labShapeOk(x) { const ps = labPs(x); return ps.length === 15 && new Set(x.ids).size === 15 && Object.keys(LAB_NEED).every(c => ps.filter(p => p.cls === c).length === LAB_NEED[c]); }
  function labFormOk(xi) { if (xi.length !== 11 || xi.some(p => !p)) return false; const c = {gk: 0, def: 0, mid: 0, fwd: 0}; xi.forEach(p => c[p.cls]++); return c.gk === 1 && c.def >= 3 && c.mid >= 2 && c.fwd >= 1; }
  // onze, banco, capitão e vice à mão: quem entra herda o lugar de quem sai; se deixar de ser válido volta ao automático
  function labFixLineup(x, outId, inId) {
    if (x.auto !== false) { x.xi = x.bench = null; x.cap = x.vice = null; x.auto = true; return; }
    const rep = a => (a || []).map(i => (i === outId ? inId : i)).filter(i => i != null);
    x.xi = rep(x.xi); x.bench = rep(x.bench);
    if (x.cap === outId) x.cap = inId; if (x.vice === outId) x.vice = inId;
    const ok = x.xi.length === 11 && x.bench.length === 4 && labFormOk(x.xi.map(id => FULL_POOL_BY_ID[id])) && [...x.xi, ...x.bench].every(id => x.ids.includes(id));
    if (!ok) { x.auto = true; x.xi = x.bench = null; x.cap = x.vice = null; }
  }
  function labAdd(x, p) { const why = labWhyNot(p, labPs(x), x.budget); if (why) return why; x.ids.push(p.id); labFixLineup(x, null, null); return ''; }
  function labRemove(x, id) { x.ids = x.ids.filter(i => i !== id); x.locked = x.locked.filter(i => i !== id); labFixLineup(x, id, null); }
  function labSwap(x, outId, p) {
    if (!x.ids.includes(outId)) return `${labPn(outId)} não está nesta equipa`;
    const why = labWhyNot(p, labPs(x).filter(q => q.id !== outId), x.budget); if (why) return why;
    x.ids[x.ids.indexOf(outId)] = p.id; x.locked = x.locked.filter(i => i !== outId); labFixLineup(x, outId, p.id); return '';
  }
  // pôr um jogador na equipa: num lugar vazio ou, se a equipa estiver cheia, no lugar do mais fraco (não trancado) da posição
  function labForceIn(x, p) {
    if (x.ids.includes(p.id)) return {why: ''};
    let why = labAdd(x, p); if (!why) return {why: ''};
    const cands = labPs(x).filter(q => q.cls === p.cls && !x.locked.includes(q.id)).sort((a, b) => sum5(a) - sum5(b));
    for (const q of cands) { if (!labSwap(x, q.id, p)) return {why: '', out: q}; }
    if (cands.length) why = labWhyNot(p, labPs(x).filter(q => q.id !== cands[0].id), x.budget) || why;
    return {why};
  }
  function labLock(x, p) { const r = labForceIn(x, p); if (r.why) return r; if (!x.locked.includes(p.id)) x.locked.push(p.id); return r; }
  function labManual(x) {
    const L = labLineup(x); if (!L) return false;
    x.auto = false; x.xi = L.xi.map(p => p.id); x.bench = L.bench.map(p => p.id); x.cap = L.cap.id; x.vice = L.vice.id; return true;
  }
  function labSetCap(x, id, vice) {
    if (!x.ids.includes(id)) return `${labPn(id)} não está nesta equipa`;
    if (!labShapeOk(x)) return 'completa primeiro a equipa (15 jogadores)';
    if (x.auto !== false && !labManual(x)) return 'não consegui montar o onze';
    if (!x.xi.includes(id)) return `${labPn(id)} está no banco: ${vice ? 'o vice' : 'o capitão'} tem de estar no onze (usa «Mudar de lugar»)`;
    if (vice) { if (x.cap === id) x.cap = x.vice; x.vice = id; } else { if (x.vice === id) x.vice = x.cap; x.cap = id; }
    return '';
  }
  function labMovePos(x, a, b) {
    if (a === b) return '';
    if (!labShapeOk(x)) return 'completa primeiro a equipa (15 jogadores)';
    if (x.auto !== false && !labManual(x)) return 'não consegui montar o onze';
    const inA = x.xi.includes(a), inB = x.xi.includes(b), P = id => FULL_POOL_BY_ID[id];
    if (inA && inB) return 'os dois já estão no onze: escolhe um do onze e um do banco, ou dois do banco para mudar a ordem';
    if (!inA && !inB) {
      if (P(a).cls === 'gk' || P(b).cls === 'gk') return 'o guarda-redes suplente só entra pelo guarda-redes: não tem ordem no banco';
      const i = x.bench.indexOf(a), j = x.bench.indexOf(b); x.bench[i] = b; x.bench[j] = a; return '';
    }
    const on = inA ? a : b, off = inA ? b : a;
    const xi = x.xi.map(i => (i === on ? off : i)), c = {gk: 0, def: 0, mid: 0, fwd: 0};
    xi.forEach(i => c[P(i).cls]++);
    if (c.gk !== 1) return 'o onze tem de ter exatamente 1 guarda-redes';
    if (c.def < 3) return `o onze ficava com ${c.def} defesas: o mínimo são 3`;
    if (c.mid < 2) return `o onze ficava com ${c.mid} médios: o mínimo são 2`;
    if (c.fwd < 1) return 'o onze ficava sem avançados: o mínimo é 1';
    x.xi = xi; x.bench = x.bench.map(i => (i === off ? on : i));
    if (x.cap === on) x.cap = off; if (x.vice === on) x.vice = off;
    if (x.cap === x.vice) x.vice = x.xi.filter(i => i !== x.cap).sort((p, q) => epAt(P(q), 0) - epAt(P(p), 0))[0];
    return '';
  }
  // "Completar com os melhores": o otimizador da Equipa ideal, com os trancados (ou com todos os que já lá estão)
  function labFill(x, onlyGaps, gis) {
    gis = gis || (LAB.ui.h === 1 ? [0] : HZ.map((g, i) => i));
    const locked = onlyGaps ? x.ids.slice() : x.locked.filter(id => x.ids.includes(id));
    const seeds = labShapeOk(x) ? [x.ids.slice()] : [];
    let r = null; try { r = optimizeTeam({budget: x.budget, locked, gis, seeds, iters: 3}); } catch (e) { console.error(e); }
    if (!r) {
      const pr = labProblems({ids: locked, budget: x.budget}).filter(t => !/^faltam/.test(t));
      return `não há equipa possível com ${onlyGaps ? 'estes jogadores' : 'os trancados'} e £${x.budget.toFixed(1)}M: ${pr.length ? pr.join('; ') : 'o que sobra não chega para os lugares que faltam — tira um trancado ou aumenta o orçamento'}`;
    }
    x.ids = r.ids.slice(); x.auto = true; x.xi = x.bench = null; x.cap = x.vice = null;
    return '';
  }

  // ---------- onze, capitão e banco (automáticos pela simulação do banco, ou à mão) ----------
  function labLineup(x) {
    if (!labShapeOk(x)) return null;
    const ps = labPs(x), k = [x.ids.join(','), x.auto === false ? 'm' : 'a', (x.xi || []).join(','), (x.bench || []).join(','), x.cap, x.vice].join('|');
    if (LAB.lu[k]) return LAB.lu[k];
    const by = new Map(ps.map(p => [p.id, p])), ep = (a, b) => epAt(b, 0) - epAt(a, 0);
    let L = null;
    if (x.auto === false && x.xi && x.bench) {
      const xi = x.xi.map(id => by.get(id)), bench = x.bench.map(id => by.get(id));
      if (bench.length === 4 && bench.every(Boolean) && new Set([...x.xi, ...x.bench]).size === 15 && labFormOk(xi)) {
        const cap = x.xi.includes(x.cap) ? by.get(x.cap) : xi.slice().sort(ep)[0];
        const vice = x.xi.includes(x.vice) && x.vice !== cap.id ? by.get(x.vice) : xi.filter(p => p !== cap).sort(ep)[0];
        L = {xi, bench: [...bench.filter(p => p.cls === 'gk'), ...bench.filter(p => p.cls !== 'gk')], cap, vice, auto: false};
      }
    }
    if (!L) {
      const r = pickXi(ps, 0); let ob = r.benchOut;
      if (!r.real) { try { const B = bestBench(r, 0); ob = B.orders[B.best]; } catch (e) {} }
      L = {xi: r.xi, bench: [...r.benchGk, ...ob], cap: r.cap, vice: r.vice, auto: true, real: !!r.real};
    }
    const cnt = c => L.xi.filter(p => p.cls === c).length; L.form = [cnt('def'), cnt('mid'), cnt('fwd')];
    L.key = L.xi.map(p => p.id).join(',') + '|' + L.bench.map(p => p.id).join(',') + '|' + L.cap.id + '|' + L.vice.id;
    if (Object.keys(LAB.lu).length > 80) LAB.lu = {};
    return (LAB.lu[k] = L);
  }
  function labTeamOf(x) { const L = labLineup(x); return L ? {ps: labPs(x), L} : null; }
  function labRealTeam(mgr) { return labTeamOf({ids: squadOf(mgr || curMgr()).filter(Boolean).map(p => p.id), auto: true}); }
  function labNums(T) {
    const ep1 = T.L.xi.reduce((s, p) => s + epAt(p, 0), 0) + epAt(T.L.cap, 0);
    let ep5 = ep1; for (let gi = 1; gi < HZ.length; gi++) ep5 += pickXi(T.ps, gi).total;
    return {ep1, ep5, p10: pAtLeast(T.L.cap, 0, 10), cost: labCost(T.ps)};
  }
  // simulação da próxima jornada com as regras da FPL (substituições automáticas, capitão/vice) e números aleatórios
  // comuns: o mesmo jogador faz os mesmos pontos em todas as equipas em cada cenário
  function labSim(teams, seed) {
    const N = 3000, rnd = mulberry(seed || 6262);
    const ids = [...new Set(teams.flatMap(t => [...t.xi, ...t.bench].map(p => p.id)))], M = ids.length, ix = new Map(ids.map((id, i) => [id, i]));
    const PP = new Float32Array(M), CC = new Float32Array(M), CL = [];
    ids.forEach((id, i) => { const p = FULL_POOL_BY_ID[id], ok = p && epAt(p, 0) > 0 && fixturesFor(p.team, HZ[0]).length; PP[i] = ok ? pPlay(p) : 0; CC[i] = ok ? ppCond(p, 0) : 0; CL[i] = p ? p.cls : 'mid'; });
    const TI = teams.map(t => ({xi: t.xi.map(p => ix.get(p.id)), gk2: (g => (g ? ix.get(g.id) : -1))(t.bench.find(p => p.cls === 'gk')), ob: t.bench.filter(p => p.cls !== 'gk').map(p => ix.get(p.id)),
      caps: t.caps.map(c => ({c: ix.get(c.cap.id), v: c.vice && ix.has(c.vice.id) ? ix.get(c.vice.id) : -1, w: c.w || 1})), ws: t.caps.reduce((s, c) => s + (c.w || 1), 0)}));
    const pts = new Float32Array(M), play = new Uint8Array(M), out = teams.map(() => new Float32Array(N));
    const fits = (cnt, o, b) => { const d = cnt.def - (CL[o] === 'def') + (CL[b] === 'def'), m = cnt.mid - (CL[o] === 'mid') + (CL[b] === 'mid'), f = cnt.fwd - (CL[o] === 'fwd') + (CL[b] === 'fwd'); return d >= 3 && m >= 2 && f >= 1; };
    for (let s = 0; s < N; s++) {
      for (let i = 0; i < M; i++) { const a = rnd(), b = rnd(); if (a < PP[i]) { play[i] = 1; pts[i] = Math.round(CC[i] * empDraw(CL[i], b)); } else { play[i] = 0; pts[i] = 0; } }
      const u = rnd();
      for (let k = 0; k < TI.length; k++) {
        const t = TI[k], cnt = {gk: 0, def: 0, mid: 0, fwd: 0}, absent = []; let tot = 0;
        for (const i of t.xi) { cnt[CL[i]]++; if (play[i]) tot += pts[i]; else absent.push(i); }
        if (absent.length) {
          const g = absent.findIndex(i => CL[i] === 'gk');
          if (g >= 0) { if (t.gk2 >= 0 && play[t.gk2]) tot += pts[t.gk2]; absent.splice(g, 1); }
          for (const b of t.ob) {
            if (!absent.length) break; if (!play[b]) continue;
            const j = absent.findIndex(i => fits(cnt, i, b)); if (j < 0) continue;
            cnt[CL[absent[j]]]--; cnt[CL[b]]++; absent.splice(j, 1); tot += pts[b];
          }
        }
        let c = t.caps[0]; if (t.caps.length > 1) { let a = u * t.ws; for (const q of t.caps) { c = q; a -= q.w; if (a <= 0) break; } }
        if (play[c.c]) tot += pts[c.c]; else if (c.v >= 0 && play[c.v]) tot += pts[c.v];
        out[k][s] = tot;
      }
    }
    return out;
  }
  function labVs(A, B) { let w = 0, d = 0, sa = 0, sb = 0; const N = A.length; for (let s = 0; s < N; s++) { if (A[s] > B[s]) w++; else if (A[s] === B[s]) d++; sa += A[s]; sb += B[s]; } return {pw: w / N, pd: d / N, pl: 1 - (w + d) / N, ma: sa / N, mb: sb / N}; }
  function labSimTeam(T) { return {xi: T.L.xi, bench: T.L.bench, caps: [{cap: T.L.cap, vice: T.L.vice, w: 1}]}; }
  function labOppTeam(e) {
    const L = LEAGUE_SQUADS[e]; if (!L) return null;
    const xi = L.s.map(id => FULL_POOL_BY_ID[id]).filter(Boolean), bench = L.b.map(id => FULL_POOL_BY_ID[id]).filter(Boolean);
    if (xi.length !== 11) return null;
    let caps = null; try { caps = winCapsOf(L, xi, 0); } catch (err) { caps = null; }
    if (!caps || !caps.length) { const o = xi.slice().sort((a, b) => epAt(b, 0) - epAt(a, 0)); caps = [{cap: o[0], vice: o[1], w: 1}]; }
    return {xi, bench, caps, L};
  }
  // probabilidade de ganhar ao próximo adversário do H2H (e a da equipa real, para comparar)
  function labH2H(T, mgr) {
    mgr = mgr || curMgr();
    const oe = h2hOppEntry(mgr), O = oe && labOppTeam(oe); if (!O) return null;
    const R = labRealTeam(mgr), k = ['h', mgr, oe, T.L.key, R ? R.L.key : ''].join('#');
    if (LAB.simc[k]) return LAB.simc[k];
    const S = labSim([labSimTeam(T), O, ...(R ? [labSimTeam(R)] : [])], 6262 + oe % 997);
    if (Object.keys(LAB.simc).length > 80) LAB.simc = {};
    return (LAB.simc[k] = {oe, L: O.L, x: labVs(S[0], S[1]), me: R ? labVs(S[2], S[1]) : null});
  }
  function labDuel(Ta, Tb) { const S = labSim([labSimTeam(Ta), labSimTeam(Tb)], 7117); return labVs(S[0], S[1]); }
  // diferenciais (no onze, quase ninguém na liga os tem a jogar) e ameaças (a liga tem-nos e esta equipa não)
  function labEO(x, T) {
    const have = new Set(x.ids), eo = id => leagueEO(id);
    const diffs = T.L.xi.map(p => ({p, e: eo(p.id)})).filter(d => d.e.eo < 0.15 && epAt(d.p, 0) >= 2).sort((a, b) => epAt(b.p, 0) - epAt(a.p, 0));
    const seen = new Set(), th = [];
    Object.values(LEAGUE_SQUADS).forEach(L => L.s.forEach(id => { if (seen.has(id) || have.has(id)) return; seen.add(id); const p = FULL_POOL_BY_ID[id]; if (!p) return; const e = eo(id); if (e.eo >= 0.3) th.push({p, e, w: e.eo * epAt(p, 0)}); }));
    th.sort((a, b) => b.w - a.w);
    return {diffs, threats: th};
  }
  // lesões e castigos previstos (V58) nos 15: texto, jogos que deve falhar nas próximas 5 e pontos esperados perdidos
  function labAvail(x) {
    const out = []; let miss = 0, lost = 0;
    labPs(x).forEach(p => {
      let r = null, txt = '', m = 0, l = 0;
      try { r = av58(p); txt = av58RetTxt(p); } catch (e) {}
      try { if (!txt) { const nt = av58Next(p); if (nt && nt.need === 1) txt = `${av58Cards(p).yc} amarelos: a 1 de ${av58BanTxt(nt.ban)} de castigo`; } } catch (e) {}
      if (!txt && p.status && p.status !== 'a') txt = p.news || (STATUS_TXT[p.status] || ['Indisponível'])[0];
      if (!txt) return;
      try { if (r && r.av && (r.inj || r.sus || r.pend)) { m = r.show.slice(0, 5).reduce((s, g) => s + (1 - (r.av[g] == null ? 1 : r.av[g])), 0); const b = AVAIL_PRED.p[p.id]; if (b && b.f) l = HZ.reduce((s, g, k) => s + Math.max(0, (b.f[k] || 0) - epAt(p, k)), 0); } } catch (e) {}
      miss += m; lost += l; out.push({p, txt, miss: m, lost: l});
    });
    return {list: out.sort((a, b) => b.miss - a.miss), miss, lost};
  }

  // ---------- equipas fantasma: pontos reais jornada a jornada ----------
  // pontos e minutos oficiais de uma jornada: history/points-J<n>.json; se faltar, os do bloco de dados (espelho validado)
  function labPtsGw(g) {
    const F = LAB.hist[g];
    if (F && F.points) return {final: !!F.final, get: id => F.points[id] || null};
    const n = Math.max(0, ...FULL_POOL.slice(0, 40).map(p => (p.ptsGw || []).length));
    if (g >= 1 && g <= Math.min(GW_META.last, n)) return {final: !(g === GW_META.last && GW_META.lastProvisional), get: id => { const p = FULL_POOL_BY_ID[id]; return p && p.ptsGw ? [p.ptsGw[g - 1] || 0, (p.minsGw || [])[g - 1] || 0] : null; }};
    return null;
  }
  function labLastGw() { let g = Math.max(0, ...Object.keys(LAB.hist).map(Number)); while (labPtsGw(g + 1)) g++; return g; }
  // pontos de uma equipa numa jornada como na FPL: quem não jogou sai (o GR só pelo GR; os outros pela ordem do banco,
  // se a formação continuar válida) e, se o capitão não jogou, o vice conta a dobrar. Numa jornada ainda por fechar
  // não há substituições (a FPL só as faz no fim).
  function labScore(T, H) {
    const P = id => H.get(id) || [0, 0], cls = id => (FULL_POOL_BY_ID[id] || {}).cls || 'mid';
    const xi = T.xi.slice(), subs = [];
    if (H.final) {
      const cnt = {gk: 0, def: 0, mid: 0, fwd: 0}; xi.forEach(id => cnt[cls(id)]++);
      const gkOut = xi.find(id => cls(id) === 'gk' && !(P(id)[1] > 0)), gk2 = T.bench.find(id => cls(id) === 'gk');
      if (gkOut != null && gk2 != null && P(gk2)[1] > 0) { xi[xi.indexOf(gkOut)] = gk2; subs.push([gk2, gkOut]); }
      T.bench.filter(id => cls(id) !== 'gk').forEach(b => {
        if (!(P(b)[1] > 0)) return;
        const tgt = xi.find(id => cls(id) !== 'gk' && !(P(id)[1] > 0) && (() => { const c = Object.assign({}, cnt); c[cls(id)]--; c[cls(b)]++; return c.def >= 3 && c.mid >= 2 && c.fwd >= 1; })());
        if (tgt == null) return;
        cnt[cls(tgt)]--; cnt[cls(b)]++; xi[xi.indexOf(tgt)] = b; subs.push([b, tgt]);
      });
    }
    let capUsed = T.cap;
    if (H.final && !(P(T.cap)[1] > 0)) capUsed = P(T.vice)[1] > 0 ? T.vice : null;
    return {total: xi.reduce((s, id) => s + P(id)[0], 0) + (capUsed != null ? P(capUsed)[0] : 0), subs, capUsed, capPts: capUsed != null ? P(capUsed)[0] : 0};
  }
  // o conselho da app para uma jornada: a fotografia guardada antes do deadline; para a próxima jornada, o de agora
  function labLiveAdvice(mgr) {
    try {
      const orig = (typeof SUG_ORIG !== 'undefined' ? SUG_ORIG : SUGGESTED_MOVES)[mgr] || {}, now = (SUGGESTED_MOVES[mgr] || {}).transfers || [];
      const T = labTeamOf({ids: applyMoves(squadOf(mgr).filter(Boolean), now).map(p => p.id), auto: true});
      const P = id => (FULL_POOL_BY_ID[id] || {}).price || 0;
      return {live: true, transfers: (orig.transfers || []).map(m => ({out: m.out, in: m.in, po: P(m.out), pi: P(m.in)})),
        xi: T ? T.L.xi.map(p => p.id) : null, bench: T ? T.L.bench.map(p => p.id) : null, cap: T ? T.L.cap.id : null, vice: T ? T.L.vice.id : null};
    } catch (e) { return null; }
  }
  function labAdvice(g, mgr) { const A = (LAB.advice[g] || {})[mgr]; return A || (g === GW_META.next ? labLiveAdvice(mgr) : null); }
  function labMoveCheck(T, m) {
    const o = FULL_POOL_BY_ID[m.out], n = FULL_POOL_BY_ID[m.in];
    if (!T.ids.includes(m.out)) return `${labPn(m.out)} não está na equipa`;
    if (T.ids.includes(m.in)) return `${labPn(m.in)} já está na equipa`;
    if (!n) return 'quem entra já não está na lista da FPL';
    if (o && o.cls !== n.cls) return `${shortName(n.name)} não joga na posição de ${shortName(o.name)}`;
    if (T.ids.filter(id => id !== m.out && (FULL_POOL_BY_ID[id] || {}).team === n.team).length >= 3) return `ficava com 4 do ${SHORT(n.team)} (máximo 3 por clube)`;
    const po = m.po != null ? m.po : (o ? o.price : 0), pi = m.pi != null ? m.pi : n.price;
    if (T.bank + po - pi < -1e-9) return `não cabe no orçamento: faltam £${(pi - po - T.bank).toFixed(1)}M`;
    return '';
  }
  function labGhostRun(x, mgr, upto) {
    const G = x.ghost; if (!G || !G.ids0) return null;
    mgr = mgr || x.mgr || curMgr();
    const T = {ids: G.ids0.slice(), xi: G.xi0.slice(), bench: G.bench0.slice(), cap: G.cap0, vice: G.vice0, bank: G.bank0 || 0, ft: G.ft0 || 1};
    const rows = [], states = {}; let total = 0;
    const planMax = G.mode === 'plan' ? Math.max(0, ...Object.keys(G.plan || {}).filter(g => (G.plan[g] || []).length).map(Number), ...Object.keys(G.caps || {}).map(Number)) : 0;
    const end = Math.min(38, Math.max(labLastGw(), GW_META.next, planMax, upto || 0));
    for (let g = G.from; g <= end; g++) {
      states[g] = {ids: T.ids.slice(), bank: T.bank, xi: T.xi.slice()};
      const row = {g, done: [], skip: [], hits: 0, note: ''};
      let A = null, moves = [];
      if (G.mode === 'advice') { A = labAdvice(g, mgr); if (A) { moves = A.transfers || []; row.live = !!A.live; } else row.note = 'sem conselho guardado'; }
      else if (G.mode === 'plan') { moves = (G.plan || {})[g] || []; const c = (G.caps || {})[g]; if (c) A = {cap: c.c, vice: c.v}; }
      moves.forEach(m => {
        const why = labMoveCheck(T, m); if (why) { row.skip.push({m, why}); return; }
        const o = FULL_POOL_BY_ID[m.out], n = FULL_POOL_BY_ID[m.in];
        T.bank = +(T.bank + (m.po != null ? m.po : (o ? o.price : 0)) - (m.pi != null ? m.pi : n.price)).toFixed(1);
        ['ids', 'xi', 'bench'].forEach(k => { const i = T[k].indexOf(m.out); if (i >= 0) T[k][i] = m.in; });
        if (T.cap === m.out) T.cap = m.in; if (T.vice === m.out) T.vice = m.in;
        row.done.push(m);
      });
      row.hits = Math.max(0, row.done.length - T.ft) * 4;
      T.ft = Math.min(5, Math.max(0, T.ft - row.done.length) + 1);
      if (A) {
        if (A.xi && A.bench && A.xi.length === 11 && A.bench.length === 4 && T.ids.every(id => A.xi.includes(id) || A.bench.includes(id))) { T.xi = A.xi.slice(); T.bench = A.bench.slice(); }
        if (A.cap && T.xi.includes(A.cap)) { if (T.vice === A.cap) T.vice = T.cap; T.cap = A.cap; }
        if (A.vice && T.xi.includes(A.vice) && A.vice !== T.cap) T.vice = A.vice;
      }
      row.cap = T.cap; row.vice = T.vice;
      const H = labPtsGw(g);
      if (!H) { row.pending = true; rows.push(row); continue; }
      const sc = labScore(T, H);
      total += sc.total - row.hits;
      Object.assign(row, {raw: sc.total, pts: sc.total - row.hits, subs: sc.subs, capUsed: sc.capUsed, capPts: sc.capPts, final: H.final, cum: total});
      rows.push(row);
    }
    states[end + 1] = {ids: T.ids.slice(), bank: T.bank, xi: T.xi.slice()};
    return {rows, total, T, states, played: rows.filter(r => !r.pending)};
  }
  function labGhostOn(x, from, mode) {
    const pr = labProblems(x); if (pr.length) return `para a seguir, a equipa tem de estar completa e dentro das regras (${pr.join('; ')})`;
    const L = labLineup(x); if (!L) return 'para a seguir, a equipa tem de estar completa (15 jogadores)';
    const mgr = curMgr();
    x.ghost = {from, mode: mode || 'frozen', on: labToday(), ids0: x.ids.slice(), xi0: L.xi.map(p => p.id), bench0: L.bench.map(p => p.id), cap0: L.cap.id, vice0: L.vice.id,
      bank0: +(x.budget - labCost(labPs(x))).toFixed(1), ft0: x.src === 'plantel' && from === GW_META.next ? Math.max(1, SQUAD_STATE[mgr].ft || 1) : 1, plan: {}, caps: {}};
    return '';
  }
  // pontos da equipa verdadeira em cada jornada (já sem os −4, quando o live.json os traz)
  function labRealHist(mgr) {
    const e = CMP_ENTRY[mgr], LD = window.__LIVE, out = {};
    if (LD && LD.entries && LD.entries[e] && (LD.entries[e].history || []).length) LD.entries[e].history.forEach(h => { out[h.event] = h.points - (h.event_transfers_cost || 0); });
    else (mgr === 'marco' ? MARCO_HISTORY : HISTORY).forEach(h => { out[h.gw] = h.points; });
    return out;
  }

  // ---------- o que vem do repositório: experiências do Claude Code, fotografias do conselho e pontos por jornada ----------
  function labApplyRemote(ex, ad) {
    if (ex && Array.isArray(ex.experiments)) LAB.repo = ex.experiments.filter(x => x && x.id && Array.isArray(x.ids)).map(x => Object.assign({locked: [], auto: true, note: '', budget: 100}, x, {repo: true}));
    if (ad && ad.gws) LAB.advice = ad.gws;
  }
  async function labLoadRemote() {
    if (LAB.remote) return; LAB.remote = 1;
    const inj = window.__LAB_DATA;   // testes e _build/pool/lab.py: {experiments: {…}, advice: {…}, history: {n: {…}}}
    if (inj) { labApplyRemote(inj.experiments, inj.advice); Object.assign(LAB.hist, inj.history || {}); LAB.remote = 2; return; }
    if (!/^https?:$/.test(location.protocol) || !(/github\.io$/.test(location.hostname) || new URLSearchParams(location.search).has('live'))) { LAB.remote = 2; return; }
    const get = async u => { try { const r = await fetch(u + '?t=' + Date.now(), {cache: 'no-store'}); return r.ok ? await r.json() : null; } catch (e) { return null; } };
    const [ex, ad, ixd] = await Promise.all([get('lab/experiments.json'), get('lab/advice.json'), get('history/index.json')]);
    labApplyRemote(ex, ad);
    if (ixd && ixd.gws) {
      // só é preciso ir buscar as jornadas que o bloco de dados ainda não tem (ou que tem como provisórias)
      const gs = Object.keys(ixd.gws).map(Number).filter(g => g > GW_META.last || (g === GW_META.last && GW_META.lastProvisional));
      const files = await Promise.all(gs.map(g => get(`history/points-J${g}.json`)));
      files.forEach((f, i) => { if (f && f.points) LAB.hist[gs[i]] = f; });
    }
    LAB.remote = 2;
    try { labDraw(); } catch (e) { console.error(e); }
  }

  // ---------- comandos em linguagem simples (sem IA: expressões fixas) ----------
  function labNorm(t) {
    return String(t == null ? '' : t).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ß/g, 'ss').replace(/ø/g, 'o').replace(/æ/g, 'ae').replace(/[đð]/g, 'd').replace(/ł/g, 'l').replace(/ı/g, 'i')
      .replace(/->|→/g, ' por ').replace(/[^a-z0-9.,'+\- ]/g, ' ').replace(/\s+/g, ' ').trim();
  }
  function labFindPlayer(q, among) {
    const t = labNorm(q).replace(/^(o|a|os|as|do|da|de|ao)\s+/, ''); if (t.length < 2) return null;
    let best = null, bs = 0;
    (among || FULL_POOL).forEach(p => {
      const sn = labNorm(shortName(p.name)), n = labNorm(p.name), w = n.split(' ');
      let s = sn === t || n === t ? 100 : w.includes(t) ? 80 : sn.startsWith(t) ? 70 : (t.length >= 3 && w.some(v => v.startsWith(t))) ? 55 : (t.length >= 4 && n.includes(t)) ? 40 : 0;
      if (!s) return;
      s += Math.min(12, (p.total || 0) / 12) + Math.min(6, (p.own || 0) / 8);
      if (s > bs) { bs = s; best = p; }
    });
    return best;
  }
  function labFindTeam(q) {
    const t = labNorm(q).replace(/^(o|a|os|as|do|da|de)\s+/, ''); if (!t) return null;
    if (LAB_CLUB[t]) return LAB_CLUB[t];
    const ids = Object.keys(TEAMS).map(Number);
    return ids.find(id => labNorm(TEAMS[id]) === t || labNorm(SHORT(id)) === t) || ids.find(id => labNorm(TEAMS[id]).startsWith(t)) || ids.find(id => t.length >= 4 && labNorm(TEAMS[id]).includes(t)) || null;
  }
  function labFindEntry(q) {
    const t = labNorm(q); if (t.length < 2) return null;
    const E = Object.keys(LEAGUE_SQUADS).map(Number), nm = e => [labNorm(LEAGUE_SQUADS[e].m), labNorm(LEAGUE_SQUADS[e].tn)];
    return E.find(e => nm(e).includes(t)) || E.find(e => nm(e).some(n => n.split(' ').includes(t))) || E.find(e => nm(e).some(n => n.startsWith(t))) || E.find(e => t.length >= 4 && nm(e).some(n => n.includes(t))) || null;
  }
  function labFindExp(q) {
    const t = labNorm(q); if (!t) return null; const L = labList();
    return L.find(x => labNorm(x.name) === t) || L.find(x => labNorm(x.name).startsWith(t)) || L.find(x => t.length >= 3 && labNorm(x.name).includes(t)) || null;
  }
  function labExamples() {
    const x = labCur(), ps = x ? labPs(x) : [];
    const mid = ps.filter(p => p.cls === 'mid').sort((a, b) => epAt(a, 0) - epAt(b, 0))[0];
    const alt = mid && FULL_POOL.filter(p => p.cls === 'mid' && !ps.includes(p) && p.status === 'a' && p.price <= mid.price + 0.5).sort((a, b) => sum5(b) - sum5(a))[0];
    const top = ps.slice().sort((a, b) => epAt(b, 0) - epAt(a, 0)), riv = (LEAGUE_SQUADS[h2hOppEntry(curMgr())] || {}).m;
    return [mid && alt ? `troca ${shortName(mid.name)} por ${shortName(alt.name)}` : 'troca Saka por Cherki',
      top.length >= 2 ? `tranca ${shortName(top[0].name)} e ${shortName(top[1].name)}` : 'tranca Haaland e Groß', 'orçamento 101',
      top.length ? `capitão ${shortName(top[0].name)}` : 'capitão Haaland', `melhor equipa para a J${HZ[Math.min(1, HZ.length - 1)]}`,
      `copia a equipa do ${riv ? riv.split(' ')[0] : 'Frederico'}`, 'compara com a minha', 'completa com os melhores', `segue a partir da J${GW_META.next}`];
  }
  function labHelp() { return `Não percebi. Sei fazer coisas como: ${labExamples().map(e => `<button type="button" class="lab-exb" data-lab="ex">${nwEsc(e)}</button>`).join(' ')} — e ainda «nova experiência Ataque», «tira Saka», «mete Rice», «vice Saka», «destranca todos», «orçamento real», «duplica», «apaga», «renomeia para …», «nota: …», «equipa com 3 do Arsenal e o Haaland».`; }
  function labDuelMsg(a, b) {
    const Ta = labTeamOf(a), Tb = labTeamOf(b); if (!Ta || !Tb) return 'para comparar, as duas equipas têm de estar completas (15 jogadores)';
    const Na = labNums(Ta), Nb = labNums(Tb), v = labDuel(Ta, Tb), common = a.ids.filter(id => b.ids.includes(id)).length;
    return `<b>${nwEsc(a.name)}</b> contra <b>${nwEsc(b.name)}</b>: na J${HZ[0]} ${f1(Na.ep1)} contra ${f1(Nb.ep1)} pts esperados (capitães ${shortName(Ta.L.cap.name)} e ${shortName(Tb.L.cap.name)}); nas J${HZ[0]}-J${HZ[HZ.length - 1]} ${f1(Na.ep5)} contra ${f1(Nb.ep5)}; num confronto direto na J${HZ[0]} ganhava ${labPct(v.pw)}, empatava ${labPct(v.pd)} e perdia ${labPct(v.pl)}; ${common} de 15 jogadores em comum. Vê «Lado a lado» mais abaixo.`;
  }
  function labCmpAdd(id) { const S = labS(); if (!S.cmp.includes(id)) S.cmp = [...S.cmp, id].slice(-4); }
  function labCmdOne(raw) {
    const t = labNorm(raw), ok = msg => ({ok: true, msg}), no = msg => ({ok: false, msg});
    const items = s => s.split(/\s*,\s*|\s+e\s+|\s*\+\s*/).map(v => v.trim()).filter(Boolean);
    const gwOf = s => { const m = /\bj\s?(\d{1,2})\b/.exec(s); return m ? +m[1] : null; };
    let m, x = labCur();
    const edit = () => { if (!x) x = labFromSquad(); else if (x.repo) x = labCopyOf(x, true); return x; };
    const rawTail = n => String(raw).trim().split(/\s+/).slice(n).join(' ').trim();
    if (!t || /^(ajuda|exemplos|help|o que sabes)/.test(t)) return no(labHelp().replace('Não percebi. Sei', 'Sei'));
    // trocar um jogador por outro
    if ((m = /^(?:troca|trocar|substitui|muda)\s+(.+?)\s+(?:por|pelo|pela)\s+(.+)$/.exec(t)) || (m = /^(?:tira|vende)\s+(.+?)\s+e\s+(?:mete|poe|compra|entra)\s+(.+)$/.exec(t))) {
      edit(); const out = labFindPlayer(m[1], labPs(x)), inn = labFindPlayer(m[2]);
      if (!out) { const g = labFindPlayer(m[1]); return no(`${g ? shortName(g.name) : '«' + nwEsc(m[1]) + '»'} não está em «${nwEsc(x.name)}».`); }
      if (!inn) return no(`Não encontrei nenhum jogador chamado «${nwEsc(m[2])}».`);
      const b = labCost(labPs(x)), why = labSwap(x, out.id, inn);
      if (why) return no(`Não troquei ${shortName(out.name)} por ${shortName(inn.name)}: ${why}.`);
      return ok(`Troquei <b>${shortName(out.name)}</b> por <b>${shortName(inn.name)}</b> (${SHORT(inn.team)}, £${inn.price.toFixed(1)}M) em «${nwEsc(x.name)}». Custo £${labCost(labPs(x)).toFixed(1)}M (${sgn(labCost(labPs(x)) - b)}), sobra £${labM(x.budget - labCost(labPs(x)))}M.`);
    }
    // nova equipa "com 3 do Arsenal e o Haaland" (tranca e completa)
    if ((m = /^(?:nova|novo|cria|criar|faz|quero)?\s*(?:uma\s+)?(?:experiencia|equipa)\s+com\s+(.+)$/.exec(t))) {
      const ri = String(raw).toLowerCase().indexOf(' com '), nx = labNew({name: 'Equipa com ' + (ri >= 0 ? String(raw).slice(ri + 5).trim() : m[1]).slice(0, 44), budget: x && x.src !== 'rival' ? x.budget : labMyBudget().market}); x = nx;
      const r = labCmdLock(x, items(m[1])); const why = labFill(x, false, HZ.map((g, i) => i));
      if (why) return no(`Criei «${nwEsc(x.name)}» (${r.txt}), mas ${why}.`);
      return ok(`Criei «${nwEsc(x.name)}»: ${r.txt} e completei-a com os melhores para as J${HZ[0]}-J${HZ[HZ.length - 1]} dentro de £${x.budget.toFixed(1)}M.${r.bad ? ' ' + r.bad : ''} ${labSumMsg(x)}`);
    }
    if ((m = /^(?:tranca|trancar|fixa|bloqueia|segura)\s+(.+)$/.exec(t))) { edit(); const r = labCmdLock(x, items(m[1])); return r.n ? ok(`Em «${nwEsc(x.name)}» ${r.txt}.${r.bad ? ' ' + r.bad : ''}`) : no(r.bad || 'Não tranquei ninguém.'); }
    if ((m = /^(?:destranca|destrancar|solta|desbloqueia|liberta)\s+(.+)$/.exec(t))) {
      edit(); if (/^(todos|tudo|todas)$/.test(m[1])) { x.locked = []; return ok(`Destranquei todos em «${nwEsc(x.name)}».`); }
      const done = []; items(m[1]).forEach(q => { const p = labFindPlayer(q, labPs(x)); if (p && x.locked.includes(p.id)) { x.locked = x.locked.filter(i => i !== p.id); done.push(shortName(p.name)); } });
      return done.length ? ok(`Destranquei ${done.join(', ')}.`) : no('Nenhum desses está trancado.');
    }
    if ((m = /^orcamento\s*(?:de\s+|do\s+|para\s+)?(real|mercado|valor de mercado|\d+(?:[.,]\d+)?)/.exec(t))) {
      edit(); const B = labMyBudget(); let v = m[1] === 'real' ? B.real : /mercado/.test(m[1]) ? B.market : parseFloat(m[1].replace(',', '.'));
      if (!(v >= 60 && v <= 130)) return no('O orçamento tem de ficar entre £60M e £130M.');
      x.budget = +v.toFixed(1); x.bmode = m[1] === 'real' ? 'real' : /mercado/.test(m[1]) ? 'mercado' : 'livre';
      const pr = labProblems(x).filter(p => /orçamento/.test(p));
      return ok(`Orçamento de «${nwEsc(x.name)}»: <b>£${x.budget.toFixed(1)}M</b>${x.bmode === 'real' ? ' (o teu orçamento real: preços de venda + banco)' : x.bmode === 'mercado' ? ' (o valor de mercado do teu plantel + banco)' : ''}. Custo £${labCost(labPs(x)).toFixed(1)}M${pr.length ? ` — <b>${pr[0]}</b>` : `, sobra £${labM(x.budget - labCost(labPs(x)))}M`}.`);
    }
    if (/^(?:capitao|banco|onze)?.*\bautomatic/.test(t)) { edit(); x.auto = true; x.xi = x.bench = null; x.cap = x.vice = null; const L = labLineup(x); return ok(`Capitão e banco automáticos${L ? `: capitão ${shortName(L.cap.name)}, vice ${shortName(L.vice.name)}, banco ${L.bench.map(p => shortName(p.name)).join(' → ')}` : ''}.`); }
    if ((m = /^(capitao|cap|c|vice|vice-capitao|v)\s+(.+)$/.exec(t))) {
      edit(); const vice = m[1][0] === 'v', p = labFindPlayer(m[2], labPs(x));
      if (!p) { const g = labFindPlayer(m[2]); return no(`${g ? shortName(g.name) : '«' + nwEsc(m[2]) + '»'} não está em «${nwEsc(x.name)}».`); }
      const why = labSetCap(x, p.id, vice); if (why) return no(`Não mudei ${vice ? 'o vice' : 'o capitão'}: ${why}.`);
      return ok(`${vice ? 'Vice' : 'Capitão'} de «${nwEsc(x.name)}»: <b>${shortName(p.name)}</b> (≈${f1(epAt(p, 0))} pts na J${HZ[0]}, 10+ pts ${pctR(pAtLeast(p, 0, 10))}). O onze e o banco passaram a «à mão».`);
    }
    if ((m = /^(?:a\s+)?(?:melhor equipa|equipa ideal|otimiza|optimiza)\b(.*)$/.exec(t))) {
      const g = gwOf(m[1]); if (g && !HZ.includes(g)) return no(`Só tenho pontos esperados da J${HZ[0]} à J${HZ[HZ.length - 1]}.`);
      const src = x; x = labNew({name: g ? `Melhor equipa J${g}` : `Melhor equipa J${HZ[0]}-J${HZ[HZ.length - 1]}`, budget: src && src.src !== 'rival' ? src.budget : labMyBudget().market, ids: src ? src.locked.slice() : [], locked: src ? src.locked.slice() : [], src: 'ideal'});
      const why = labFill(x, false, g ? [HZ.indexOf(g)] : HZ.map((q, i) => i));
      if (why) return no(`Criei «${nwEsc(x.name)}», mas ${why}.`);
      return ok(`Criei «${nwEsc(x.name)}»: os 15 com mais pontos esperados ${g ? 'na J' + g : `nas J${HZ[0]}-J${HZ[HZ.length - 1]}`} dentro de £${x.budget.toFixed(1)}M${x.locked.length ? `, com ${x.locked.map(labPn).join(', ')} trancado${x.locked.length === 1 ? '' : 's'}` : ''}. ${labSumMsg(x)}`);
    }
    if ((m = /^(?:completa|completar|preenche|preencher|enche)\b(.*)$/.exec(t))) {
      edit(); const g = gwOf(m[1]); if (g && !HZ.includes(g)) return no(`Só tenho pontos esperados da J${HZ[0]} à J${HZ[HZ.length - 1]}.`);
      const gaps = /vazi|falt/.test(m[1]), why = labFill(x, gaps, g ? [HZ.indexOf(g)] : null);
      if (why) return no(`Não completei «${nwEsc(x.name)}»: ${why}.`);
      return ok(`Completei «${nwEsc(x.name)}» com os melhores${gaps ? ' nos lugares vazios' : x.locked.length ? `, mantendo os ${x.locked.length} trancados` : ''}. ${labSumMsg(x)}`);
    }
    if ((m = /^(?:copia|copiar|clona)\s+(?:a\s+|o\s+)?(?:equipa\s+|plantel\s+)?(?:do\s+|da\s+|de\s+|dos\s+)?(.+)$/.exec(t))) {
      const u = m[1]; let n = null;
      if (/^(minha|meu|real|verdadeira)/.test(u)) n = labFromSquad();
      else if (/ideal/.test(u)) { n = labFromIdeal(); if (!n) return no('Ainda não há Equipa ideal calculada com esse orçamento.'); }
      else if (/simulad/.test(u)) { n = labFromSim(); if (!n) return no('A Equipa simulada está vazia.'); }
      else { const e = labFindEntry(u); if (e) n = labFromRival(e); else { const ex = labFindExp(u); if (ex) n = labCopyOf(ex); } }
      if (!n) return no(`Não encontrei nenhum gestor, equipa ou experiência chamado «${nwEsc(u)}».`);
      x = n; return ok(`Criei «${nwEsc(n.name)}» (£${n.budget.toFixed(1)}M). ${labSumMsg(n)}`);
    }
    if ((m = /^(?:compara|comparar)\s+(?:com\s+)?(?:a\s+|o\s+)?(?:equipa\s+|plantel\s+)?(?:do\s+|da\s+|de\s+)?(.+)$/.exec(t))) {
      if (!x) x = labFromSquad(); const u = m[1];
      labCmpAdd(x.id); LAB.ui.scroll = 'lab-cmp';
      if (/^(minha|meu|real|verdadeira)/.test(u)) {
        const T = labTeamOf(x), R = labRealTeam(); if (!T || !R) return no('Para comparar, a equipa tem de estar completa (15 jogadores).');
        const a = labNums(T), b = labNums(R), n = x.ids.filter(id => !R.ps.some(p => p.id === id)).length;
        return ok(`«${nwEsc(x.name)}» contra a tua equipa real: J${HZ[0]} ${f1(a.ep1)} contra ${f1(b.ep1)} (${sgn(a.ep1 - b.ep1)}); J${HZ[0]}-J${HZ[HZ.length - 1]} ${f1(a.ep5)} contra ${f1(b.ep5)} (${sgn(a.ep5 - b.ep5)}); ${n} jogador${n === 1 ? '' : 'es'} diferente${n === 1 ? '' : 's'}. Vê «Lado a lado» mais abaixo.`);
      }
      let o = labFindExp(u);
      if (!o || o.id === x.id) { const e = labFindEntry(u); if (e) { o = labList().find(y => y.src === 'rival' && y.from === e && !y.ghost) || null; if (!o) { const keep = x.id; o = labFromRival(e); labS().sel = keep; } } }
      if (!o || o.id === x.id) return no(`Não encontrei nenhuma experiência nem gestor chamado «${nwEsc(u)}».`);
      labCmpAdd(o.id); return ok(labDuelMsg(x, o));
    }
    if ((m = /^(?:nova|novo|cria|criar)\b\s*(?:uma\s+)?(?:experiencia|equipa)?\s*(?:de raiz|vazia|chamada)?\s*(.*)$/.exec(t))) {
      const words = String(raw).trim().split(/\s+/), k = words.length - (m[1] ? m[1].split(' ').length : 0);
      x = labNew({name: m[1] ? words.slice(k).join(' ') : 'Experiência', budget: 100});
      return ok(`Criei «${nwEsc(x.name)}», vazia, com £100.0M. Escreve «completa com os melhores», «tranca …» ou escolhe os jogadores em baixo.`);
    }
    if (/^(desfaz|anula|recupera)/.test(t)) { if (!LAB.trash) return no('Não há nada para recuperar.'); const S = labS(); S.list.unshift(LAB.trash); S.sel = LAB.trash.id; const n = LAB.trash.name; LAB.trash = null; return ok(`Recuperei «${nwEsc(n)}».`); }
    if ((m = /^(?:apaga|apagar|elimina)\s*(?:a\s+)?(?:experiencia\s*)?(.*)$/.exec(t))) {
      const y = m[1] ? labFindExp(m[1]) : x; if (!y) return no('Não encontrei essa experiência.');
      if (y.repo) return no(`«${nwEsc(y.name)}» foi criada pelo Claude Code e vive no repositório: pede-lhe para a apagar.`);
      const S = labS(); S.list = S.list.filter(e => e.id !== y.id); S.cmp = S.cmp.filter(i => i !== y.id); LAB.trash = y; if (S.sel === y.id) S.sel = null;
      return ok(`Apaguei «${nwEsc(y.name)}». Escreve «desfaz» se foi engano.`);
    }
    if (/^(duplica|duplicar)/.test(t)) { if (!x) return no('Não há nenhuma experiência para duplicar.'); const c = labCopyOf(x); return ok(`Criei «${nwEsc(c.name)}».`); }
    if ((m = /^(?:renomeia|muda o nome|nome)\s+(?:para\s+)?(.+)$/.exec(t))) { edit(); const n = rawTail(String(raw).trim().split(/\s+/).length - m[1].split(' ').length).slice(0, 60); x.name = ''; x.name = labName(n || 'Experiência'); return ok(`Agora chama-se «${nwEsc(x.name)}».`); }
    if (/^nota\b/.test(t)) { edit(); x.note = String(raw).replace(/^\s*nota\s*:?\s*/i, '').slice(0, 400); return ok(`Nota guardada em «${nwEsc(x.name)}».`); }
    if (/^(para de seguir|nao segue|nao seguir|deixa de seguir|desliga)/.test(t)) { edit(); x.ghost = null; return ok(`«${nwEsc(x.name)}» deixou de ser seguida.`); }
    if ((m = /^(?:segue|seguir|acompanha)\b(.*)$/.exec(t))) {
      edit(); const g = gwOf(m[1]) || GW_META.next; if (g < 1 || g > GW_META.next) return no(`Só dá para seguir a partir de uma jornada entre a J1 e a J${GW_META.next}.`);
      const mode = /conselh/.test(m[1]) ? 'advice' : /plano/.test(m[1]) ? 'plan' : 'frozen', why = labGhostOn(x, g, mode);
      if (why) return no(`Não liguei o «Seguir»: ${why}.`);
      LAB.ui.scroll = 'lab-ghost'; const r = labGhostRun(x);
      return ok(`«${nwEsc(x.name)}» passa a ser seguida a partir da J${g} (${LAB_MODE[mode][0].toLowerCase()}).${r && r.played.length ? ` Nas ${r.played.length} jornadas já jogadas faria ${r.total} pts.` : ' Os pontos aparecem quando a jornada for jogada.'}`);
    }
    if ((m = /^(?:na\s+)?j\s?(\d{1,2})\s*:?\s*(?:troca\s+)?(.+?)\s+por\s+(.+)$/.exec(t))) {
      edit(); const G = x.ghost; if (!G || G.mode !== 'plan') return no('Primeiro liga «Seguir» com o modo «segue um plano meu» (ex.: «segue o plano a partir da J' + GW_META.next + '»).');
      const why = labPlanAdd(x, +m[1], m[2], m[3]); return why ? no(`Não marquei a troca: ${why}.`) : ok(`Marquei na J${+m[1]}: ${(x.ghost.plan[+m[1]] || []).slice(-1).map(v => `${labPn(v.out)} → ${labPn(v.in)}`).join('')}.`);
    }
    if ((m = /^(?:tira|remove|vende)\s+(.+)$/.exec(t))) {
      edit(); const done = [], bad = [];
      items(m[1]).forEach(q => { const p = labFindPlayer(q, labPs(x)); if (p) { labRemove(x, p.id); done.push(shortName(p.name)); } else bad.push(q); });
      return done.length ? ok(`Tirei ${done.join(', ')} de «${nwEsc(x.name)}» (${x.ids.length}/15).${bad.length ? ` Não estavam lá: ${nwEsc(bad.join(', '))}.` : ''}`) : no(`Não encontrei ${nwEsc(bad.join(', '))} nesta equipa.`);
    }
    if ((m = /^(?:mete|poe|adiciona|compra|junta|entra)\s+(.+)$/.exec(t))) {
      edit(); const done = [], bad = [];
      items(m[1]).forEach(q => { const p = labFindPlayer(q); if (!p) { bad.push(`não encontrei «${nwEsc(q)}»`); return; } const r = labForceIn(x, p); if (r.why) bad.push(`${shortName(p.name)}: ${r.why}`); else done.push(shortName(p.name) + (r.out ? ` (saiu ${shortName(r.out.name)})` : '')); });
      return done.length ? ok(`Entrou ${done.join(', ')} em «${nwEsc(x.name)}».${bad.length ? ' Não coube — ' + bad.join('; ') + '.' : ''}`) : no(`Não coube — ${bad.join('; ')}.`);
    }
    if (/^(limpa|limpar|esvazia)/.test(t)) { edit(); x.ids = []; x.locked = []; labFixLineup(x, null, null); return ok(`«${nwEsc(x.name)}» ficou vazia.`); }
    if ((m = /^(?:abre|mostra|escolhe|usa|vai para)\s+(?:a\s+)?(?:experiencia\s+)?(.+)$/.exec(t))) { const y = labFindExp(m[1]); if (!y) return no(`Não encontrei a experiência «${nwEsc(m[1])}».`); labS().sel = y.id; x = y; return ok(`Aberta: «${nwEsc(y.name)}». ${labSumMsg(y)}`); }
    if (/^export/.test(t)) { LAB.ui.io = 'exp'; return ok('O código está na lista de experiências: copia-o e cola-o no outro dispositivo, em «Importar».'); }
    if (/^import/.test(t)) { LAB.ui.io = 'imp'; return ok('Cola o código na caixa «Importar», na lista de experiências.'); }
    return no(labHelp());
  }
  function labCmdLock(x, list) {
    const done = [], bad = [];
    list.forEach(q => {
      const c = /^(\d)\s+(?:do|da|de|dos|das)\s+(.+)$/.exec(q.replace(/^(o|a|os|as)\s+/, ''));
      if (c) {
        const team = labFindTeam(c[2]); if (!team) { bad.push(`não conheço o clube «${nwEsc(c[2])}»`); return; }
        let n = 0; FULL_POOL.filter(p => p.team === team && (p.status === 'a' || x.ids.includes(p.id))).sort((a, b) => sum5(b) - sum5(a)).forEach(p => { if (n >= Math.min(3, +c[1])) return; const r = labLock(x, p); if (!r.why) { n++; done.push(shortName(p.name)); } });
        if (n < +c[1]) bad.push(`só couberam ${n} do ${SHORT(team)}${+c[1] > 3 ? ' (o máximo são 3 por clube)' : ''}`);
        return;
      }
      const p = labFindPlayer(q); if (!p) { bad.push(`não encontrei «${nwEsc(q)}»`); return; }
      const r = labLock(x, p); if (r.why) bad.push(`${shortName(p.name)} não coube: ${r.why}`); else done.push(shortName(p.name) + (r.out ? ` (entrou por ${shortName(r.out.name)})` : ''));
    });
    return {n: done.length, txt: done.length ? `tranquei ${done.join(', ')}` : 'sem trancados', bad: bad.length ? bad.join('; ') + '.' : ''};
  }
  function labSumMsg(x) {
    const T = labTeamOf(x); if (!T) { const pr = labProblems(x); return pr.length ? `Ainda ${pr[0]}.` : ''; }
    const N = labNums(T), pr = labProblems(x);
    return `J${HZ[0]}: ${f1(N.ep1)} pts esperados (capitão ${shortName(T.L.cap.name)}), J${HZ[0]}-J${HZ[HZ.length - 1]}: ${f1(N.ep5)}; custo £${N.cost.toFixed(1)}M.${pr.length ? ' Atenção: ' + pr.join('; ') + '.' : ''}`;
  }
  function labCmd(raw) {
    const parts = String(raw || '').split(/[;\n]+/).map(s => s.trim()).filter(Boolean);
    if (!parts.length) return {ok: false, msg: labHelp().replace('Não percebi. Sei', 'Sei')};
    const R = parts.map(p => { try { return labCmdOne(p); } catch (e) { console.error(e); return {ok: false, msg: 'Não consegui fazer isso (erro interno).'}; } });
    labSave();
    return {ok: R.every(r => r.ok), msg: R.map(r => r.msg).join('<br>')};
  }
  function labPlanAdd(x, g, outQ, inQ) {
    const G = x.ghost; if (!G || G.mode !== 'plan') return 'liga primeiro o modo «segue um plano meu»';
    if (!(g >= G.from && g <= 38)) return `a jornada tem de ficar entre a J${G.from} e a J38`;
    const st = labGhostRun(x, null, g).states[g]; if (!st) return 'não consegui ver a equipa nessa jornada';
    const ids = (G.plan[g] || []).reduce((a, m) => a.map(i => (i === m.out ? m.in : i)), st.ids.slice());
    const out = typeof outQ === 'number' ? FULL_POOL_BY_ID[outQ] : labFindPlayer(outQ, ids.map(id => FULL_POOL_BY_ID[id]).filter(Boolean));
    const inn = typeof inQ === 'number' ? FULL_POOL_BY_ID[inQ] : labFindPlayer(inQ);
    if (!out) return 'quem sai não está na equipa nessa jornada';
    if (!inn) return 'não encontrei quem entra';
    const mv = {out: out.id, in: inn.id, po: out.price, pi: inn.price};
    // o banco depois das trocas já marcadas nessa jornada
    let bank = st.bank; (G.plan[g] || []).forEach(m => { bank = +(bank + (m.po || 0) - (m.pi || 0)).toFixed(1); });
    const why = labMoveCheck({ids, bank}, mv); if (why) return why;
    (G.plan[g] = G.plan[g] || []).push(mv); return '';
  }
  // relatório em texto simples (para o _build/pool/lab.py e para quem pede no telemóvel)
  function labReport(id) {
    const x = labGet(id) || labCur(); if (!x) return null;
    const T = labTeamOf(x), mgr = curMgr(), out = {id: x.id, name: x.name, gw: x.gw, budget: x.budget, n: x.ids.length, problems: labProblems(x), locked: x.locked.map(labPn), note: x.note || ''};
    if (!T) return out;
    const N = labNums(T), R = labRealTeam(mgr), RN = R ? labNums(R) : null, H = labH2H(T, mgr), E = labEO(x, T), A = labAvail(x);
    Object.assign(out, {xi: T.L.xi.map(p => shortName(p.name)), bench: T.L.bench.map(p => shortName(p.name)), form: T.L.form.join('-'), cap: shortName(T.L.cap.name), vice: shortName(T.L.vice.name),
      ep1: +N.ep1.toFixed(1), ep5: +N.ep5.toFixed(1), p10: Math.round(N.p10 * 100), cost: +N.cost.toFixed(1), left: +labM(x.budget - N.cost),
      real: RN ? {ep1: +RN.ep1.toFixed(1), ep5: +RN.ep5.toFixed(1), dif: x.ids.filter(i => !R.ps.some(p => p.id === i)).length} : null,
      h2h: H ? {opp: H.L.m, team: H.L.tn, win: Math.round(H.x.pw * 100), draw: Math.round(H.x.pd * 100), lose: Math.round(H.x.pl * 100), realWin: H.me ? Math.round(H.me.pw * 100) : null} : null,
      diffs: E.diffs.slice(0, 5).map(d => `${shortName(d.p.name)} (EO ${labPct(d.e.eo)})`), threats: E.threats.slice(0, 5).map(d => `${shortName(d.p.name)} (EO ${labPct(d.e.eo)})`),
      avail: A.list.map(a => `${shortName(a.p.name)}: ${a.txt}`), miss: +A.miss.toFixed(1)});
    const r = labGhostRun(x, mgr);
    if (r) { const real = labRealHist(mgr), gs = r.played.map(q => q.g); out.ghost = {from: x.ghost.from, mode: x.ghost.mode, pts: r.total, real: gs.reduce((s, g) => s + (real[g] || 0), 0), gws: r.played.map(q => [q.g, q.pts])}; }
    return out;
  }

  // ---------- exportar / importar (um código para copiar e colar) ----------
  function labExportCode() {
    const s = JSON.stringify({v: 1, m: curMgr(), d: labToday(), list: labS().list});
    return 'FPLLAB1.' + btoa(unescape(encodeURIComponent(s))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }
  function labImportCode(code) {
    const c = String(code || '').replace(/\s+/g, ''); if (!/^FPLLAB1\./.test(c)) return {ok: false, msg: 'Isto não parece um código do Laboratório (começa por FPLLAB1.).'};
    let d = null; try { d = JSON.parse(decodeURIComponent(escape(atob(c.slice(8).replace(/-/g, '+').replace(/_/g, '/'))))); } catch (e) { d = null; }
    if (!d || !Array.isArray(d.list)) return {ok: false, msg: 'O código está incompleto ou estragado: copia-o outra vez, inteiro.'};
    const S = labS(); let add = 0, upd = 0;
    d.list.filter(x => x && x.id && Array.isArray(x.ids)).forEach(x => {
      x.ids = x.ids.filter(id => typeof id === 'number'); x.locked = (x.locked || []).filter(id => x.ids.includes(id)); x.name = String(x.name || 'Experiência').slice(0, 60); x.budget = +x.budget || 100; delete x.repo;
      const i = S.list.findIndex(y => y.id === x.id);
      if (i >= 0) { S.list[i] = x; upd++; } else { S.list.push(x); add++; }
    });
    labSave();
    return {ok: add + upd > 0, msg: add + upd ? `Importei ${add + upd} experiência${add + upd === 1 ? '' : 's'}${upd ? ` (${upd} já existia${upd === 1 ? '' : 'm'} e ${upd === 1 ? 'foi atualizada' : 'foram atualizadas'})` : ''}${d.m && d.m !== curMgr() ? ` — atenção: foram exportadas na equipa do ${d.m === 'marco' ? 'Marco' : 'Bruno'}` : ''}.` : 'O código não tinha experiências.'};
  }

  // ---------- desenhar ----------
  function labSay(ok, msg) { LAB.ui.msg = msg ? {ok, msg} : null; }
  function labTok(p, x, L, slotLbl) {
    const sel = LAB.ui.pick === p.id, lk = x.locked.includes(p.id), mv = LAB.ui.move && LAB.ui.move !== p.id;
    const tok = pitchToken(p, 0, {cap: L && p === L.cap, vice: L && p === L.vice}).replace(`data-pid="${p.id}"`, `data-lab="tok" data-id="${p.id}" aria-pressed="${sel}"`);
    return `<div class="idl-tok lab-tok${sel ? ' sel' : ''}${mv ? ' mv' : ''}">${slotLbl ? `<span class="lbl">${slotLbl}</span>` : ''}${tok}${lk ? '<span class="lab-lk" title="Trancado">🔒</span>' : ''}</div>`;
  }
  function labDrawCmd() {
    const el = document.getElementById('lab-cmd'); if (!el || el.dataset.mgr === curMgr()) return;
    el.dataset.mgr = curMgr();
    el.innerHTML = `
      <div class="card-head"><div><h2>Laboratório</h2><div class="card-sub">Experimenta equipas sem mexer na tua equipa verdadeira e vê, jornada a jornada, se as ideias resultam. ${curMgr() === 'marco' ? 'Xarola Team' : 'Brunorussia FC'}.</div></div></div>
      <form class="lab-cmdf" id="lab-cmdf" autocomplete="off"><input type="text" id="lab-cmd-in" placeholder="Escreve o que queres fazer, por ex.: troca Saka por Cherki" aria-label="Comando em linguagem simples" enterkeyhint="go"><button type="submit" class="btn primary">Fazer</button></form>
      <div class="lab-ex" id="lab-ex"></div>
      <div class="lab-out" id="lab-cmd-out" role="status" aria-live="polite" hidden></div>
      <div class="lab-go"><span class="note">Ir para:</span> ${[['lab-list', 'Experiências'], ['lab-edit', 'A equipa'], ['lab-eval', 'O que mostra'], ['lab-cmp', 'Lado a lado'], ['lab-ghost', 'Fantasmas']].map(([k, n]) => `<button type="button" class="linklike" data-lab="go" data-to="${k}">${n}</button>`).join(' · ')}</div>`;
  }
  function labDrawEx() { const el = document.getElementById('lab-ex'); if (el) el.innerHTML = `<span class="note">Exemplos (toca para escrever):</span> ${labExamples().slice(0, 7).map(e => `<button type="button" class="lab-exb" data-lab="ex">${nwEsc(e)}</button>`).join('')}`; }
  function labDrawList() {
    const el = document.getElementById('lab-list'); if (!el) return;
    const S = labS(), L = labList(), cur = labCur(), E = Object.keys(LEAGUE_SQUADS).map(Number).sort((a, b) => (cmpRank(a) || 99) - (cmpRank(b) || 99)), me = CMP_ENTRY[curMgr()];
    const item = x => {
      const T = labTeamOf(x), pr = labProblems(x), ps = labPs(x);
      const tags = `${x.repo ? '<span class="status-chip alt">Claude Code · todos os dispositivos</span>' : ''}${x.ghost ? `<span class="status-chip insquad">fantasma desde a J${x.ghost.from}</span>` : ''}${pr.length ? `<span class="status-chip watch">${ps.length < 15 ? ps.length + '/15' : 'fora das regras'}</span>` : ''}`;
      return `<div class="lab-it${cur && cur.id === x.id ? ' sel' : ''}">
        <button type="button" class="lab-it-b" data-lab="sel" data-id="${x.id}" aria-pressed="${!!(cur && cur.id === x.id)}">
          <span class="lab-it-n">${nwEsc(x.name)} ${tags}</span>
          <span class="lab-it-m">Criada na J${x.gw} · orçamento £${(+x.budget).toFixed(1)}M · ${T ? `C ${shortName(T.L.cap.name)} · V ${shortName(T.L.vice.name)}${T.L.auto ? '' : ' (à mão)'}` : `${ps.length}/15 jogadores`}</span>
          ${T ? `<span class="lab-it-s"><b>Onze</b> ${T.L.xi.map(p => shortName(p.name)).join(', ')} · <b>Banco</b> ${T.L.bench.map(p => shortName(p.name)).join(' → ')}</span>` : ps.length ? `<span class="lab-it-s">${ps.map(p => shortName(p.name)).join(', ')}</span>` : ''}
          ${x.note ? `<span class="lab-it-s lab-it-t">“${nwEsc(x.note)}”</span>` : ''}
        </button>
        <label class="lab-it-c"><input type="checkbox" data-labc="cmp" value="${x.id}"${S.cmp.includes(x.id) ? ' checked' : ''}> comparar</label>
      </div>`;
    };
    const io = LAB.ui.io === 'exp' ? `<div class="lab-io"><label for="lab-code">Código das ${S.list.length} experiências deste browser (${curMgr() === 'marco' ? 'Marco' : 'Bruno'}). Copia-o e cola-o em «Importar» no outro dispositivo.</label><textarea id="lab-code" readonly rows="4">${S.list.length ? labExportCode() : ''}</textarea><div class="plan-actions"><button type="button" class="btn primary" data-lab="copy"${S.list.length ? '' : ' disabled'}>Copiar o código</button><button type="button" class="btn ghost" data-lab="ioclose">Fechar</button></div></div>`
      : LAB.ui.io === 'imp' ? `<div class="lab-io"><label for="lab-code-in">Cola aqui o código que copiaste no outro dispositivo (começa por FPLLAB1.). As experiências juntam-se às que já cá estão.</label><textarea id="lab-code-in" rows="4" placeholder="FPLLAB1.…"></textarea><div class="plan-actions"><button type="button" class="btn primary" data-lab="impgo">Importar</button><button type="button" class="btn ghost" data-lab="ioclose">Fechar</button></div></div>` : '';
    el.innerHTML = `
      <div class="card-head"><div><h2>Experiências <span class="note">(${L.length})</span></h2><div class="card-sub">As tuas ficam guardadas neste browser, separadas para o Bruno e para o Marco. As criadas pelo Claude Code vêm do site e aparecem em todos os dispositivos.</div></div></div>
      <div class="lab-new">
        <label for="lab-src">Nova experiência</label>
        <select id="lab-src" aria-label="De onde parte a nova experiência"><option value="raiz">de raiz (vazia)</option><option value="plantel" selected>a partir do meu plantel</option><option value="ideal">a partir da Equipa ideal</option><option value="simulada">a partir da Equipa simulada</option>
          <optgroup label="A partir do plantel de um rival">${E.filter(e => e !== me).map(e => `<option value="r:${e}">${cmpRank(e) || '–'}.º · ${nwEsc(LEAGUE_SQUADS[e].tn)} (${nwEsc(LEAGUE_SQUADS[e].m)})</option>`).join('')}</optgroup></select>
        <button type="button" class="btn primary" data-lab="new">Criar</button>
        <span class="lab-new-io"><button type="button" class="btn ghost" data-lab="exp" aria-expanded="${LAB.ui.io === 'exp'}">Exportar</button><button type="button" class="btn ghost" data-lab="imp" aria-expanded="${LAB.ui.io === 'imp'}">Importar</button></span>
      </div>
      ${io}
      <div class="lab-items">${L.map(item).join('') || '<p class="note">Ainda não há experiências. Escolhe de onde partir e carrega em «Criar», ou escreve um comando na caixa de cima.</p>'}</div>
      ${LAB.trash ? `<p class="note">Apagaste «${nwEsc(LAB.trash.name)}». <button type="button" class="linklike" data-lab="undo">Recuperar</button></p>` : ''}`;
  }
  function labDrawEdit() {
    const el = document.getElementById('lab-edit'); if (!el) return;
    const x = labCur(), msg = LAB.ui.msg ? `<div class="lab-out ${LAB.ui.msg.ok ? 'ok' : 'bad'}" role="status">${LAB.ui.msg.msg}</div>` : '';
    if (!x) { el.innerHTML = `<div class="card-head"><div><h2>A equipa</h2></div></div>${msg}<p class="note">Cria ou escolhe uma experiência na lista de cima.</p>`; return; }
    const ps = labPs(x), cost = labCost(ps), left = x.budget - cost, pr = labProblems(x), L = labLineup(x), B = labMyBudget(), ro = !!x.repo, dis = ro ? ' disabled' : '';
    if (LAB.ui.pick && !x.ids.includes(LAB.ui.pick)) LAB.ui.pick = null;
    if (LAB.ui.move && !x.ids.includes(LAB.ui.move)) LAB.ui.move = null;
    let body;
    if (L) {
      const rows = ['fwd', 'mid', 'def', 'gk'].map(c => L.xi.filter(p => p.cls === c));
      let k = 0;
      body = `<div class="pitch idl-pitch lab-pitch${LAB.busy ? ' is-busy' : ''}"><span class="box top"></span><span class="box bottom"></span>${rows.map(r => `<div class="pitch-row">${r.map(p => labTok(p, x, L)).join('')}</div>`).join('')}</div>
        <div class="bench"><div class="bench-head">Banco (pela ordem em que entram)</div><div class="bench-row">${L.bench.map(p => labTok(p, x, L, p.cls === 'gk' ? 'GR' : (++k) + '.º')).join('')}</div></div>`;
    } else {
      body = `<div class="sim-squad">${['gk', 'def', 'mid', 'fwd'].map(c => { const l = ps.filter(p => p.cls === c).sort((a, b) => b.price - a.price), n = Math.max(0, LAB_NEED[c] - l.length);
        return `<div class="sim-pos"><div class="sim-pos-h">${SIM_LBL[c]} <span class="note">${l.length}/${LAB_NEED[c]}</span></div><div class="sim-row">${l.map(p => `<button type="button" class="sim-p lab-sp${LAB.ui.pick === p.id ? ' sel' : ''}" data-lab="tok" data-id="${p.id}" aria-pressed="${LAB.ui.pick === p.id}">${shirtSvg(p.team, p.cls)}<span class="sim-n">${x.locked.includes(p.id) ? '🔒 ' : ''}${shortName(p.name)}</span><span class="sim-m">£${p.price.toFixed(1)} · ≈${f1(sum5(p))}</span></button>`).join('')}${ro ? '' : Array.from({length: n}, () => `<button type="button" class="sim-empty" data-lab="slot" data-pos="${c}">＋<span>${POS_SHORT[c]}</span></button>`).join('')}</div></div>`; }).join('')}</div>`;
    }
    const p = LAB.ui.pick ? FULL_POOL_BY_ID[LAB.ui.pick] : null, mvP = LAB.ui.move ? FULL_POOL_BY_ID[LAB.ui.move] : null;
    const act = mvP ? `<div class="lab-act" role="group"><span><b>Mudar ${shortName(mvP.name)} de lugar:</b> toca no jogador com quem troca (um do onze e um do banco, ou dois do banco para mudar a ordem).</span><button type="button" class="btn small ghost" data-lab="movex">Cancelar</button></div>`
      : p ? `<div class="lab-act" role="group" aria-label="O que fazer com ${nwEsc(p.name)}"><span><b>${shortName(p.name)}</b> <span class="note">${POS_SHORT[p.cls]} · ${SHORT(p.team)} · £${p.price.toFixed(1)}M · ≈${f1(epAt(p, 0))} pts na J${HZ[0]}</span></span>
          ${ro ? '' : `<button type="button" class="btn small primary" data-lab="swapout">Trocar por outro…</button><button type="button" class="btn small" data-lab="lock">${x.locked.includes(p.id) ? '🔓 Destrancar' : '🔒 Trancar'}</button>${L ? `<button type="button" class="btn small" data-lab="cap">Capitão</button><button type="button" class="btn small" data-lab="vice">Vice</button><button type="button" class="btn small" data-lab="move">Mudar de lugar</button>` : ''}<button type="button" class="btn small" data-lab="rm">Tirar</button>`}
          <button type="button" class="btn small ghost" data-lab="ficha">Ficha</button></div>`
      : `<p class="note lab-hint">${ro ? 'Toca num jogador para veres a ficha.' : 'Toca num jogador para o trocar, trancar, fazer capitão ou vice, mudar de lugar (onze ↔ banco e ordem do banco) ou tirar.'}</p>`;
    el.innerHTML = `
      <div class="card-head"><div><h2>${nwEsc(x.name)}</h2><div class="card-sub">Criada na J${x.gw} (${x.created || '—'}) ${LAB_SRC[x.src] || ''}${x.src === 'rival' && LEAGUE_SQUADS[x.from] ? ': ' + nwEsc(LEAGUE_SQUADS[x.from].m) : ''} · não mexe na tua equipa verdadeira</div></div></div>
      ${ro ? `<div class="callout info"><span class="icon">i</span><div class="body"><p><b>Criada pelo Claude Code:</b> vive no site e aparece em todos os dispositivos, por isso não se muda aqui. <button type="button" class="linklike" data-lab="copyrepo">Copiar para as minhas experiências</button> para a poderes mexer.</p></div></div>` : ''}
      ${msg}
      <div class="lab-meta">
        <label><span>Nome</span><input type="text" id="lab-name" maxlength="60" value="${nwEsc(x.name)}"${dis}></label>
        <label><span>Nota minha</span><textarea id="lab-note" rows="2" maxlength="400" placeholder="A ideia desta experiência…"${dis}>${nwEsc(x.note || '')}</textarea></label>
      </div>
      <div class="sim-bar">
        <label>Orçamento £<input type="number" id="lab-budget" min="60" max="130" step="0.1" value="${(+x.budget).toFixed(1)}"${dis}>M</label>
        <button type="button" class="btn small${x.bmode === 'mercado' ? ' primary' : ''}" data-lab="bud" data-m="mercado" title="O que o teu plantel vale aos preços de hoje, mais o banco"${dis}>Valor de mercado £${B.market.toFixed(1)}M</button>
        <button type="button" class="btn small${x.bmode === 'real' ? ' primary' : ''}" data-lab="bud" data-m="real" title="O que podes mesmo gastar: preços de venda (a FPL só devolve metade de cada subida) mais o banco"${dis}>Orçamento real £${B.real.toFixed(1)}M</button>
        <span class="sim-chip ${left < -1e-9 ? 'bad' : ''}">Custo £${cost.toFixed(1)}M · ${left < -1e-9 ? `passa £${(-left).toFixed(1)}M` : `sobra <b>£${labM(left)}M</b>`}</span>
        <span class="sim-chip${ps.length < 15 ? ' bad' : ''}">${ps.length}/15</span>
      </div>
      ${pr.length ? `<div class="idl-flag bad" role="status"><b>Ainda não cumpre as regras da FPL:</b> ${pr.join('; ')}.</div>` : ''}
      ${ro ? '' : `<div class="lab-bar">
        <div class="seg" role="group" aria-label="Capitão e banco"><button type="button" class="seg-btn" data-lab="auto" data-v="1" aria-pressed="${x.auto !== false}">Capitão e banco automáticos</button><button type="button" class="seg-btn" data-lab="auto" data-v="0" aria-pressed="${x.auto === false}">À mão</button></div>
        <div class="seg" role="group" aria-label="Completar a pensar em"><button type="button" class="seg-btn" data-lab="hz" data-v="1" aria-pressed="${LAB.ui.h === 1}">Só a J${HZ[0]}</button><button type="button" class="seg-btn" data-lab="hz" data-v="5" aria-pressed="${LAB.ui.h !== 1}">J${HZ[0]}-J${HZ[HZ.length - 1]}</button></div>
        <button type="button" class="btn primary" data-lab="fill"${LAB.busy ? ' disabled' : ''}>${LAB.busy ? 'A calcular…' : 'Completar com os melhores'}</button>
        ${ps.length && ps.length < 15 ? `<button type="button" class="btn" data-lab="fillgaps"${LAB.busy ? ' disabled' : ''}>Só os lugares vazios</button>` : ''}
        <button type="button" class="btn ghost" data-lab="dup">Duplicar</button><button type="button" class="btn ghost" data-lab="del">Apagar</button>
      </div>
      <p class="note">«Completar com os melhores» usa o otimizador da Equipa ideal: mantém os ${x.locked.length} trancados (🔒) e escolhe os outros${x.auto === false ? '' : '. Automático = capitão com mais pontos esperados e a ordem do banco que a simulação das substituições dá como melhor'}.</p>`}
      ${body}
      ${act}`;
  }
  function labPickList(x) {
    const U = LAB.ui, out = U.out && x.ids.includes(U.out) ? FULL_POOL_BY_ID[U.out] : null, base = labPs(x).filter(q => !out || q.id !== out.id);
    const need = Object.keys(LAB_NEED).filter(c => base.filter(p => p.cls === c).length < LAB_NEED[c]);
    const pos = out ? out.cls : (U.pos || (need.length && need.length < 4 ? need[0] : ''));
    const q = labNorm(U.q), maxP = parseFloat(String(U.price).replace(',', '.')) || 0, full = base.length === 15, weak = {};
    if (full) ['gk', 'def', 'mid', 'fwd'].forEach(c => { weak[c] = base.filter(p => p.cls === c && !x.locked.includes(p.id)).sort((a, b) => sum5(a) - sum5(b)); });
    const sorters = {ep1: (a, b) => epAt(b, 0) - epAt(a, 0), ep5: (a, b) => sum5(b) - sum5(a), val: (a, b) => sum5(b) / b.price - sum5(a) / a.price, price: (a, b) => a.price - b.price || sum5(b) - sum5(a), form: (a, b) => sumRecent(b.ptsGw || [], 3) - sumRecent(a.ptsGw || [], 3)};
    const list = FULL_POOL.filter(p => (!pos || p.cls === pos) && (!U.team || p.team === +U.team) && (!maxP || p.price <= maxP + 1e-9) && (!q || labNorm(p.name).includes(q) || labNorm(TEAMS[p.team]).includes(q)) && !x.ids.includes(p.id))
      .map(p => {
        let why = labWhyNot(p, base, x.budget), sw = null;
        if (why && !out && full) {   // equipa completa e ninguém escolhido para sair
          const cs = weak[p.cls] || [];
          sw = cs.find(o => !labWhyNot(p, base.filter(q => q.id !== o.id), x.budget)) || null;
          why = sw ? '' : cs.length ? labWhyNot(p, base.filter(q => q.id !== cs[0].id), x.budget) : `os ${LAB_NEED[p.cls]} ${POS_SHORT[p.cls]} estão trancados`;
        }
        return {p, why, sw};
      }).filter(r => !U.fit || !r.why).sort((a, b) => (sorters[U.sort] || sorters.ep5)(a.p, b.p));
    return {out, pos, need, list};
  }
  function labDrawPick() {
    const el = document.getElementById('lab-pick'); if (!el) return;
    const x = labCur();
    if (!x || x.repo) { el.hidden = true; el.innerHTML = ''; return; }
    el.hidden = false;
    const U = LAB.ui, K = labPickList(x), out = K.out, left = x.budget - labCost(labPs(x)) + (out ? out.price : 0);
    const head = out ? `Quem entra para o lugar de <b>${shortName(out.name)}</b> (${POS_SHORT[out.cls]}, £${out.price.toFixed(1)}M)? Tens £${left.toFixed(1)}M para ele. <button type="button" class="linklike" data-lab="outx">Cancelar</button>`
      : K.need.length ? `Lugares vazios: ${K.need.map(c => `${LAB_NEED[c] - labPs(x).filter(p => p.cls === c).length} ${POS_SHORT[c]}`).join(', ')}. Tens £${left.toFixed(1)}M para gastar.` : 'A equipa está completa: cada jogador diz por quem entrava (o mais fraco da posição que não esteja trancado). Para escolheres tu quem sai, toca nele no campo e em «Trocar por outro…».';
    const extra = r => { const o = out || r.sw; return r.why ? `<span class="lab-no">Não cabe: ${r.why}</span>` : `<button type="button" class="btn small primary" data-lab="in" data-id="${r.p.id}"${o ? ` data-out="${o.id}"` : ''}>${o ? 'Entra por ' + shortName(o.name) : 'Entra'}</button>${o ? `<span class="note">${sgn(epAt(r.p, 0) - epAt(o, 0))} J${HZ[0]} · ${sgn(sum5(r.p) - sum5(o))} em 5</span>` : ''}`; };
    const show = K.list.slice(0, U.more);
    el.innerHTML = `
      <div class="card-head"><div><h2>Trocar jogadores</h2><div class="card-sub">${head}</div></div></div>
      <div class="filters lab-filters">
        <label class="f-q"><span>Nome ou clube</span><input type="search" id="lab-f-q" placeholder="ex.: Saka" value="${nwEsc(U.q)}" autocomplete="off"></label>
        <label><span>Posição</span><select id="lab-f-pos"${out ? ' disabled' : ''}><option value="">Todas</option>${['gk', 'def', 'mid', 'fwd'].map(c => `<option value="${c}"${K.pos === c ? ' selected' : ''}>${SIM_LBL[c]}</option>`).join('')}</select></label>
        <label><span>Clube</span><select id="lab-f-team"><option value="">Todos</option>${Object.keys(TEAMS).map(Number).sort((a, b) => TEAMS[a].localeCompare(TEAMS[b])).map(t => `<option value="${t}"${+U.team === t ? ' selected' : ''}>${TEAMS[t]}</option>`).join('')}</select></label>
        <label><span>Preço até (£M)</span><input type="search" id="lab-f-price" inputmode="decimal" placeholder="qualquer" value="${nwEsc(U.price)}"></label>
        <label><span>Ordenar por</span><select id="lab-f-sort">${[['ep5', `Pts esperados J${HZ[0]}-J${HZ[HZ.length - 1]}`], ['ep1', 'Pts esperados J' + HZ[0]], ['val', 'Pts esperados por £M'], ['form', 'Pontos nas últimas 3'], ['price', 'Mais baratos']].map(([k, n]) => `<option value="${k}"${U.sort === k ? ' selected' : ''}>${n}</option>`).join('')}</select></label>
        <label class="f-chk"><input type="checkbox" id="lab-f-fit"${U.fit ? ' checked' : ''}> <span>Só os que cabem</span></label>
      </div>
      ${show.length ? playerCards(show.map(r => r.p), (pp, i) => ({acts: false, extra: extra(show[i])})) : '<p class="note">Ninguém com estes filtros.</p>'}
      ${K.list.length > U.more ? `<div style="text-align:center;margin-top:10px"><button type="button" class="btn" data-lab="more">Mostrar mais (${K.list.length - U.more})</button></div>` : ''}
      <p class="note">Quem não cabe mostra o motivo (posição cheia, 3 do mesmo clube ou orçamento). Toca num cartão para abrir a ficha.</p>`;
  }
  function labDrawEval() {
    const el = document.getElementById('lab-eval'); if (!el) return;
    const x = labCur(), mgr = curMgr(), T = x && labTeamOf(x);
    if (!T) { el.innerHTML = `<section class="card"><h2>O que esta experiência mostra</h2><p class="note">${x ? `Completa a equipa (faltam ${15 - labPs(x).length} jogadores) para veres os pontos esperados, a probabilidade de ganhar o H2H, os diferenciais e as ameaças.` : 'Escolhe ou cria uma experiência.'}</p></section>`; return; }
    const N = labNums(T), R = labRealTeam(mgr), RN = R ? labNums(R) : null, H = labH2H(T, mgr), E = labEO(x, T), A = labAvail(x);
    const ins = R ? T.ps.filter(p => !R.ps.includes(p)) : [], outs = R ? R.ps.filter(p => !T.ps.includes(p)) : [];
    const chip = p => `<button type="button" data-pid="${p.id}">${shortName(p.name)} · ${SHORT(p.team)}</button>`;
    const ud = v => `<span class="${v > 0.05 ? 'up' : v < -0.05 ? 'down' : ''}">${sgn(v)}</span>`;
    el.innerHTML = `
      <section class="card">
        <div class="card-head"><div><h2>O que «${nwEsc(x.name)}» mostra</h2><div class="card-sub">Formação ${T.L.form.join('-')} · capitão ${shortName(T.L.cap.name)}, vice ${shortName(T.L.vice.name)} · ${T.L.auto ? 'onze, capitão e banco automáticos' : 'onze, capitão e banco à mão'}</div></div></div>
        <div class="kpis" style="margin:6px 0 12px">
          <div class="kpi"><div class="label">Pts esperados J${HZ[0]}</div><div class="value">${f1(N.ep1)}</div><div class="hint">${RN ? `a tua equipa real ${f1(RN.ep1)} · ${ud(N.ep1 - RN.ep1)}` : 'onze + capitão'}</div></div>
          <div class="kpi"><div class="label">Próximas 5 (J${HZ[0]}-J${HZ[HZ.length - 1]})</div><div class="value">${f1(N.ep5)}</div><div class="hint">${RN ? `a tua equipa real ${f1(RN.ep5)} · ${ud(N.ep5 - RN.ep5)}` : 'melhor onze + capitão em cada jornada'}</div></div>
          <div class="kpi"><div class="label">Capitão com 10+ pts</div><div class="value">${pctR(N.p10)}</div><div class="hint">${shortName(T.L.cap.name)} ≈${f1(epAt(T.L.cap, 0))} pts${R ? ` · o teu (${shortName(R.L.cap.name)}) ${pctR(RN.p10)}` : ''}</div></div>
          <div class="kpi"><div class="label">Ganhar o H2H da J${HZ[0]}</div><div class="value">${H ? labPct(H.x.pw) : '—'}</div><div class="hint">${H ? `contra ${nwEsc(H.L.m)}${H.me ? ` · a tua equipa real ${labPct(H.me.pw)}` : ''}` : 'sem adversário nos dados'}</div></div>
          <div class="kpi"><div class="label">Custo</div><div class="value">£${N.cost.toFixed(1)}M</div><div class="hint">orçamento £${x.budget.toFixed(1)}M · ${x.budget - N.cost < -1e-9 ? `<span class="down">passa £${(N.cost - x.budget).toFixed(1)}M</span>` : `sobra £${labM(x.budget - N.cost)}M`}</div></div>
        </div>
        ${H ? `<div class="winbar" role="img" aria-label="Contra ${nwEsc(H.L.m)}: ganhar ${labPct(H.x.pw)}, empatar ${labPct(H.x.pd)}, perder ${labPct(H.x.pl)}"><span class="w" style="width:${H.x.pw * 100}%"></span><span class="d" style="width:${H.x.pd * 100}%"></span><span class="l" style="width:${H.x.pl * 100}%"></span></div>
        <div class="winlbl"><span>Ganha ${labPct(H.x.pw)}</span><span>Empata ${labPct(H.x.pd)}</span><span>Perde ${labPct(H.x.pl)}</span></div>
        <p class="note">Contra ${nwEsc(H.L.tn)} (${nwEsc(H.L.m)}), o teu próximo adversário do H2H: 3 000 simulações da J${HZ[0]} com as substituições automáticas da FPL, ${shortName(T.L.cap.name)} de capitão e o onze dele da última jornada. Em média ${f1(H.x.ma)} contra ${f1(H.x.mb)} pts.</p>` : ''}
      </section>
      <section class="card">
        <h2>Diferença para a tua equipa real</h2>
        ${!R ? '<p class="note">Sem o teu plantel nos dados.</p>' : ins.length ? `<div class="card-sub">${ins.length} jogador${ins.length === 1 ? '' : 'es'} diferente${ins.length === 1 ? '' : 's'} · custa ${sgn(N.cost - RN.cost)}M · ${sgn(N.ep1 - RN.ep1)} pts esperados na J${HZ[0]} e ${sgn(N.ep5 - RN.ep5)} nas próximas 5</div>
          <div class="riv-lbl" style="margin-top:8px">Entram (${ins.length})</div><div class="cmp-common">${ins.sort((a, b) => epAt(b, 0) - epAt(a, 0)).map(chip).join('')}</div>
          <div class="riv-lbl">Saem (${outs.length})</div><div class="cmp-common">${outs.sort((a, b) => epAt(b, 0) - epAt(a, 0)).map(chip).join('')}</div>
          <p class="note">É só uma comparação: nada disto foi feito na tua equipa. Para chegar aqui precisavas de ${ins.length} transferência${ins.length === 1 ? '' : 's'}.</p>` : `<p class="note">Tem os mesmos 15 jogadores da tua equipa real${T.L.cap !== R.L.cap ? `, mas com ${shortName(T.L.cap.name)} de capitão em vez de ${shortName(R.L.cap.name)}` : ''}.</p>`}
      </section>
      <div class="grid-2">
        <section class="card"><h2>Diferenciais <span class="note">(${E.diffs.length})</span></h2><div class="card-sub">Titulares que quase ninguém na liga tem a jogar (EO abaixo de 15%): se pontuarem, ganhas terreno a quase todos</div>
          ${E.diffs.length ? playerCards(E.diffs.slice(0, 5).map(d => d.p), (p, i) => ({acts: false, note: `EO na liga ${labPct(E.diffs[i].e.eo)} · ${Math.round(E.diffs[i].e.own * E.diffs[i].e.n)} de ${E.diffs[i].e.n} têm-no`})) : '<p class="note">Nenhum: todos os titulares são comuns na liga.</p>'}</section>
        <section class="card"><h2>Ameaças <span class="note">(${E.threats.length})</span></h2><div class="card-sub">Jogadores que muitos rivais têm a jogar (EO de 30% ou mais) e esta equipa não: se pontuarem, perdes terreno</div>
          ${E.threats.length ? playerCards(E.threats.slice(0, 5).map(d => d.p), (p, i) => ({acts: false, note: `EO na liga ${labPct(E.threats[i].e.eo)} · ${H && [...H.L.s, ...H.L.b].includes(p.id) ? 'o teu adversário do H2H tem-no' : 'fora desta equipa'}`})) : '<p class="note">Nenhuma: tens todos os jogadores populares da liga.</p>'}</section>
      </div>
      <section class="card"><h2>Lesões e castigos previstos</h2><div class="card-sub">${A.list.length ? `${A.list.length} jogador${A.list.length === 1 ? '' : 'es'} com aviso${A.miss >= 0.05 ? ` · devem falhar ≈${f1(A.miss)} jogos nas próximas 5 jornadas${A.lost >= 0.05 ? `, ≈${f1(A.lost)} pts esperados a menos` : ''}` : ''} · são probabilidades, não certezas` : 'Nos 15 desta equipa'}</div>
        ${A.list.length ? playerCards(A.list.map(a => a.p), (p, i) => ({acts: false, note: A.list[i].txt})) : '<p class="note">Nenhum dos 15 tem lesão, dúvida ou castigo à vista.</p>'}</section>`;
  }
  function labCmpTeams() {
    const S = labS(), cur = labCur(), ids = S.cmp.filter(id => labGet(id));
    if (!ids.length && cur) ids.push(cur.id);
    return ids.slice(0, 4).map(id => labGet(id));
  }
  function labDrawCmp() {
    const el = document.getElementById('lab-cmp'); if (!el) return;
    const mgr = curMgr(), R = labRealTeam(mgr), X = labCmpTeams();
    const cols = [...(R ? [{n: 'A tua equipa real', s: 'real', T: R, x: {ids: R.ps.map(p => p.id), budget: labMyBudget(mgr).market}, c: 'var(--ink-2)'}] : []), ...X.map((x, i) => ({n: x.name, s: x.name, T: labTeamOf(x), x, c: LAB_COLORS[i]}))];
    const okc = cols.filter(c => c.T);
    if (okc.length < 2) { el.innerHTML = `<div class="card-head"><div><h2>Lado a lado</h2><div class="card-sub">Até 4 experiências mais a tua equipa real</div></div></div><p class="note">${X.length ? 'A experiência escolhida ainda não está completa (15 jogadores).' : 'Marca «comparar» em até 4 experiências na lista de cima.'}</p>`; return; }
    const D = okc.map(c => { const N = labNums(c.T), H = labH2H(c.T, mgr), E = labEO(c.x, c.T), A = labAvail(c.x); return {N, H, E, A, common: R ? c.x.ids.filter(id => R.ps.some(p => p.id === id)).length : null}; });
    const opp = D[0].H ? D[0].H.L.m : null;
    // [rótulo, valor, formato, melhor: 1 maior, -1 menor, 0 sem vencedor]
    const M = [
      [`Pts esperados J${HZ[0]}`, d => d.N.ep1, f1, 1], [`Pts esperados J${HZ[0]}-J${HZ[HZ.length - 1]}`, d => d.N.ep5, f1, 1],
      ['Capitão', (d, c) => shortName(c.T.L.cap.name), null, 0], ['Capitão com 10+ pts', d => d.N.p10 * 100, v => Math.round(v) + '%', 1],
      ...(opp ? [[`Ganhar o H2H a ${opp.split(' ')[0]}`, d => (d.H ? d.H.x.pw * 100 : null), v => Math.round(v) + '%', 1]] : []),
      ['Custo', d => d.N.cost, v => '£' + v.toFixed(1) + 'M', -1], ['Diferenciais no onze', d => d.E.diffs.length, v => v, 0], ['Ameaças fora da equipa', d => d.E.threats.length, v => v, -1],
      ['Jogos que deve falhar (lesões e castigos)', d => +d.A.miss.toFixed(1), v => (v ? '≈' + f1(v) : '0'), -1], ['Em comum com a tua equipa real', d => d.common, v => v + '/15', 0],
    ];
    const wins = okc.map(() => 0); let scored = 0;
    const rows = M.map(([lbl, f, fmt, dir]) => {
      const vals = okc.map((c, i) => f(D[i], c)), num = vals.map((v, i) => [v, i]).filter(([v]) => typeof v === 'number' && !Number.isNaN(v));
      let best = null, margin = null;
      if (dir && num.length >= 2) { const s = num.slice().sort((a, b) => dir * (b[0] - a[0])); scored++; if (Math.abs(s[0][0] - s[1][0]) > 1e-9) { best = s[0][1]; margin = Math.abs(s[0][0] - s[1][0]); wins[best]++; } }
      return {lbl, vals, fmt, best, margin, dir};
    });
    const order = okc.map((c, i) => i).sort((a, b) => wins[b] - wins[a] || D[b].N.ep5 - D[a].N.ep5), bestEp = okc.map((c, i) => i).sort((a, b) => D[b].N.ep5 - D[a].N.ep5);
    const mfmt = (r, m) => (r.fmt === f1 ? f1(m) : /%/.test(r.fmt(1)) ? Math.round(m) + ' p.p.' : /£/.test(r.fmt(1)) ? '£' + m.toFixed(1) + 'M' : f1(m));
    el.innerHTML = `
      <div class="card-head"><div><h2>Lado a lado</h2><div class="card-sub">Até 4 experiências mais a tua equipa real: a verde, quem ganha cada linha e por quanto (a margem para o 2.º). Escolhe-as com «comparar» na lista.</div></div></div>
      <div class="ld-verdict">${order.map((i, k) => `<div class="ld-v${k === 0 ? ' win' : ''}" style="--c:${okc[i].c}"><span class="ld-vn">${nwEsc(okc[i].n)}</span><span class="ld-vw"><b>${wins[i]}</b> de ${scored}</span><span class="ld-vbar"><i style="width:${scored ? wins[i] / scored * 100 : 0}%"></i></span></div>`).join('')}</div>
      <p class="prose" style="margin:10px 0 0"><b>${nwEsc(okc[order[0]].n)}</b> ganha em mais linhas (${wins[order[0]]} de ${scored}). O que mais conta: nas próximas 5 jornadas <b>${nwEsc(okc[bestEp[0]].n)}</b> tem mais pontos esperados, <b>+${f1(D[bestEp[0]].N.ep5 - D[bestEp[1]].N.ep5)}</b> que ${nwEsc(okc[bestEp[1]].n)}.</p>
      <div class="lab-cg" style="--n:${okc.length}">
        <div class="lab-cr lab-ch"><div class="lab-cl"></div>${okc.map(c => `<div class="lab-cv" style="--c:${c.c}"><span class="ld-h">${nwEsc(c.n)}</span></div>`).join('')}</div>
        ${rows.map(r => `<div class="lab-cr"><div class="lab-cl">${r.lbl}</div>${r.vals.map((v, i) => `<div class="lab-cv${r.best === i ? ' win' : ''}${v == null ? ' na' : ''}" data-n="${nwEsc(okc[i].s)}" style="--c:${okc[i].c}"><span>${v == null ? '—' : r.fmt ? r.fmt(v) : v}</span>${r.best === i ? `<span class="ld-m">${r.dir > 0 ? '+' : '−'}${mfmt(r, r.margin)}</span>` : ''}</div>`).join('')}</div>`).join('')}
      </div>
      <p class="note">Pontos esperados com o onze, o capitão e o banco de cada equipa (os da tua equipa real são os que a app sugere em «Onze e banco»). H2H: probabilidade de ganhar ao teu próximo adversário, na mesma simulação para todas.</p>`;
  }
  function labGhostChart(runs, real) {
    const pl = runs.filter(o => o.r && o.r.played.length); if (!pl.length) return '';
    const g0 = Math.min(...pl.map(o => o.e.ghost.from)), g1 = Math.max(...pl.map(o => o.r.played[o.r.played.length - 1].g));
    const gs = []; for (let g = g0; g <= g1; g++) gs.push(g);
    const RC = {}; let acc = 0; gs.forEach(g => { acc += real[g] || 0; RC[g] = acc; });
    const lines = pl.map((o, k) => { const base = o.e.ghost.from > g0 ? (RC[o.e.ghost.from - 1] || 0) : 0; return {n: o.e.name, c: o.c, pts: o.r.played.map(q => [q.g, base + q.cum])}; });
    const hasReal = gs.some(g => real[g] != null);
    const all = [...lines.flatMap(l => l.pts.map(p => p[1])), ...(hasReal ? gs.map(g => RC[g]) : [])], max = Math.max(10, ...all) * 1.08;
    const W = 560, Hh = 220, P = 34, x = g => P + (gs.length > 1 ? (g - g0) * ((W - P - 14) / (gs.length - 1)) : (W - P - 14) / 2), y = v => Hh - 24 - v / max * (Hh - 40);
    const step = Math.max(1, Math.ceil(gs.length / 12));
    const line = (pts, c, dash, name) => (pts.length > 1 ? `<polyline fill="none" stroke="${c}" stroke-width="2.5"${dash ? ' stroke-dasharray="5 4"' : ''} points="${pts.map(p => `${x(p[0])},${y(p[1])}`).join(' ')}"/>` : '') + pts.map(p => `<circle cx="${x(p[0])}" cy="${y(p[1])}" r="3.5" fill="${c}"><title>${nwEsc(name)} · J${p[0]}: ${p[1]} pts acumulados</title></circle>`).join('');
    return `<div class="pc-legend">${hasReal ? '<span><i style="background:var(--ink)"></i>A tua equipa real</span>' : ''}${lines.map(l => `<span><i style="background:${l.c}"></i>${nwEsc(l.n)}</span>`).join('')}</div>
      <svg class="cmp-chart lab-chart" viewBox="0 0 ${W} ${Hh}" role="img" aria-label="Pontos acumulados das equipas fantasma e da tua equipa real">
        ${[0, 0.5, 1].map(t => `<line x1="${P}" x2="${W - 10}" y1="${y(max / 1.08 * t)}" y2="${y(max / 1.08 * t)}" stroke="var(--line)"/><text x="2" y="${y(max / 1.08 * t) + 4}" font-size="10" fill="var(--muted)">${Math.round(max / 1.08 * t)}</text>`).join('')}
        ${gs.filter((g, i) => i % step === 0 || g === g1).map(g => `<text x="${x(g)}" y="${Hh - 6}" font-size="11" text-anchor="middle" fill="var(--muted)">J${g}</text>`).join('')}
        ${hasReal ? line(gs.filter(g => real[g] != null).map(g => [g, RC[g]]), 'var(--ink)', true, 'A tua equipa real') : ''}${lines.map(l => line(l.pts, l.c, false, l.n)).join('')}
      </svg>`;
  }
  function labDrawGhost() {
    const el = document.getElementById('lab-ghost'); if (!el) return;
    const x = labCur(), mgr = curMgr(), next = GW_META.next, U = LAB.ui, real = labRealHist(mgr);
    const runs = labList().filter(e => e.ghost && e.ghost.ids0).slice(0, 6).map((e, k) => ({e, c: LAB_COLORS[k % LAB_COLORS.length], r: labGhostRun(e, mgr)}));
    const G = x && x.ghost, ro = !x || !!x.repo, from = G ? G.from : (U.gfrom && U.gfrom <= next ? U.gfrom : next), mode = G ? G.mode : U.gmode;
    const mine = x && runs.find(o => o.e.id === x.id), ok = x && !labProblems(x).length;
    const stale = G && !ro && (G.ids0.slice().sort((a, b) => a - b).join() !== x.ids.slice().sort((a, b) => a - b).join());
    const set = !x ? '<p class="note">Escolhe uma experiência na lista para a seguires.</p>' : `
      <div class="lab-gh">
        <label class="lab-sw"><input type="checkbox" id="lab-gh-on"${G ? ' checked' : ''}${ro || (!G && !ok) ? ' disabled' : ''}> <span>Seguir <b>${nwEsc(x.name)}</b> a partir da</span></label>
        <select id="lab-gh-from" aria-label="Jornada a partir da qual a equipa é seguida"${ro ? ' disabled' : ''}>${Array.from({length: next}, (_, i) => i + 1).map(g => `<option value="${g}"${g === from ? ' selected' : ''}>J${g}${g === next ? ' (a próxima)' : ''}</option>`).join('')}</select>
        <div class="seg" role="group" aria-label="Modo da equipa fantasma">${Object.keys(LAB_MODE).map(k => `<button type="button" class="seg-btn" data-lab="ghmode" data-v="${k}" aria-pressed="${mode === k}"${ro ? ' disabled' : ''}>${LAB_MODE[k][0]}</button>`).join('')}</div>
      </div>
      <p class="note"><b>${LAB_MODE[mode][0]}:</b> ${LAB_MODE[mode][1]}.${!G && !ok && !ro ? ' <b>Para ligar, a equipa tem de estar completa e dentro das regras.</b>' : ''}${from < next ? ` A começar numa jornada já jogada, a app faz as contas como se esta equipa existisse desde a J${from} (com os jogadores e os preços de hoje).` : ''}${ro && x.repo ? ' Esta experiência é do Claude Code: copia-a para as tuas para mudares isto.' : ''}</p>
      ${stale ? `<div class="idl-flag">Mudaste a equipa depois de ligares o «Seguir»: a fantasma continua com os 15 que tinha nessa altura. <button type="button" class="linklike" data-lab="ghrestart">Recomeçar com a equipa de agora, a partir da J${next}</button> ou usa «Duplicar» para seguir as duas.</div>` : ''}
      ${G && G.mode === 'advice' && !Object.keys(LAB.advice).length ? `<p class="note">Neste dispositivo ainda não há fotografias do conselho de jornadas passadas (vêm do site): para a J${next} uso o conselho que a app dá agora.</p>` : ''}
      ${G && G.mode === 'plan' && !ro ? labPlanHtml(x, mine && mine.r) : ''}`;
    const played = runs.filter(o => o.r && o.r.played.length);
    let table = '', sum = '', detail = '';
    if (runs.length) {
      sum = `<div class="lab-gsum">${runs.map(o => { const gs = o.r.played.map(q => q.g), rl = gs.reduce((s, g) => s + (real[g] || 0), 0), d = o.r.total - rl;
        return `<div class="lab-gs" style="--c:${o.c}"><b>${nwEsc(o.e.name)}</b><span class="note">${LAB_MODE[o.e.ghost.mode][0]} · desde a J${o.e.ghost.from}</span><span>${gs.length ? `<b>${o.r.total}</b> pts em ${gs.length} jornada${gs.length === 1 ? '' : 's'} · a tua equipa real ${rl} · <b class="${d > 0 ? 'up' : d < 0 ? 'down' : ''}">${d > 0 ? '+' : d < 0 ? '−' : ''}${Math.abs(d)}</b>` : `ainda sem jornadas jogadas: a primeira é a J${o.e.ghost.from}`}</span></div>`; }).join('')}</div>`;
    }
    if (played.length) {
      const g0 = Math.min(...played.map(o => o.e.ghost.from)), g1 = Math.max(...played.map(o => o.r.played[o.r.played.length - 1].g)), gs = [];
      for (let g = g0; g <= g1; g++) gs.push(g);
      const cell = (o, g) => { const q = o.r.rows.find(r => r.g === g && !r.pending); if (!q) return `<td class="num" data-label="${nwEsc(o.e.name)}" data-cv="1"><span class="cv">—</span></td>`; const d = real[g] != null ? q.pts - real[g] : null;
        return `<td class="num" data-label="${nwEsc(o.e.name)}" data-cv="1"><span class="cv"><b>${q.pts}</b>${q.hits ? ` <span class="down" title="Transferências a mais">(−${q.hits})</span>` : ''}${q.final ? '' : ' <span class="note">prov.</span>'}${d != null ? ` <span class="note ${d > 0 ? 'up' : d < 0 ? 'down' : ''}">${d > 0 ? '+' : d < 0 ? '−' : '='}${d ? Math.abs(d) : ''}</span>` : ''}</span></td>`; };
      table = `<div class="table-scroll"><table class="form lab-gt cardify"><thead><tr><th>Jornada</th><th class="num">A tua equipa real</th>${played.map(o => `<th class="num">${nwEsc(o.e.name)}</th>`).join('')}</tr></thead><tbody>
        ${gs.map(g => `<tr><td data-label="">J${g}</td><td class="num" data-label="A tua equipa real" data-cv="1"><span class="cv">${real[g] != null ? real[g] : '—'}</span></td>${played.map(o => cell(o, g)).join('')}</tr>`).join('')}
        <tr><td data-label=""><b>Total</b></td><td class="num" data-label="A tua equipa real" data-cv="1"><span class="cv"><b>${gs.reduce((s, g) => s + (real[g] || 0), 0)}</b></span></td>${played.map(o => `<td class="num" data-label="${nwEsc(o.e.name)}" data-cv="1"><span class="cv"><b>${o.r.total}</b> <span class="note">desde a J${o.e.ghost.from}</span></span></td>`).join('')}</tr>
      </tbody></table></div>`;
    }
    if (mine && mine.r && mine.r.rows.length) {
      const mv = m => `${labPn(m.out)} → ${labPn(m.in)}`;
      detail = `<details class="lab-gd"${mine.r.rows.length <= 6 ? ' open' : ''}><summary>Jornada a jornada de «${nwEsc(x.name)}»</summary><ul>${mine.r.rows.filter(q => !q.pending || q.done.length || q.skip.length || q.g === next).map(q => `<li><b>J${q.g}${q.pending ? '' : ` — ${q.pts} pts`}</b>${q.pending ? ' (por jogar)' : q.final ? '' : ' (provisória, sem substituições)'}: ${[
        q.pending ? `capitão ${labPn(q.cap)}, vice ${labPn(q.vice)}` : q.capUsed != null ? `capitão ${labPn(q.capUsed)}${q.capUsed !== q.cap ? ' (o vice: o capitão não jogou)' : ''} ${q.capPts} × 2` : 'capitão e vice não jogaram',
        ...(q.subs || []).map(s => `entrou ${labPn(s[0])} por ${labPn(s[1])}`),
        q.done.length ? `troca${q.done.length === 1 ? '' : 's'}${q.live ? ' (conselho de agora)' : ''}: ${q.done.map(mv).join(', ')}` : '', q.hits ? `−${q.hits} pts por transferências a mais` : '',
        ...q.skip.map(s => `não fez ${mv(s.m)} (${s.why})`), q.note].filter(Boolean).join('; ')}.</li>`).join('')}</ul></details>`;
    }
    el.innerHTML = `
      <div class="card-head"><div><h2>Equipas fantasma</h2><div class="card-sub">Liga «Seguir» numa experiência e a app soma os pontos reais que essa equipa faria em cada jornada, com as regras da FPL: substituições automáticas pela ordem do banco, capitão a dobrar (ou o vice, se o capitão não jogar) e −4 por cada transferência a mais.</div></div></div>
      ${set}
      ${runs.length ? `<h3 class="lab-h3">As tuas fantasmas contra a tua equipa real</h3>${sum}${labGhostChart(runs, real)}${played.length ? '<p class="note">Acumulado desde que cada fantasma começou a ser seguida. Uma fantasma que começou mais tarde parte dos pontos que a tua equipa real tinha nessa jornada: a distância entre as duas linhas é o que ganhaste ou perdeste.</p>' : ''}${table}${detail}` : '<p class="note">Ainda não segues nenhuma experiência.</p>'}
      <p class="note">Pontos e minutos oficiais da FPL, guardados jornada a jornada (history/points-J…). Uma jornada ainda por fechar aparece como provisória e sem substituições automáticas. Transferências grátis: 1 por jornada (acumulam até 5); os preços das trocas são os do dia em que foram marcadas ou aconselhadas.</p>`;
  }
  function labPlanHtml(x, run) {
    const G = x.ghost, next = GW_META.next, g = Math.min(38, Math.max(G.from, LAB.ui.plgw || Math.max(G.from, next)));
    const r = labGhostRun(x, null, g), st = r.states[g] || {ids: G.ids0, bank: G.bank0 || 0};
    const ids = (G.plan[g] || []).reduce((a, m) => a.map(i => (i === m.out ? m.in : i)), st.ids.slice());
    const sq = ids.map(id => FULL_POOL_BY_ID[id]).filter(Boolean).sort((a, b) => POS_ORDER[a.cls] - POS_ORDER[b.cls] || b.price - a.price);
    const all = Object.keys(G.plan).map(Number).sort((a, b) => a - b).filter(k => (G.plan[k] || []).length);
    return `<div class="lab-plan">
      <div class="riv-lbl">O teu plano de trocas</div>
      <div class="lab-plan-add">
        <label>Jornada <select id="lab-pl-gw">${Array.from({length: 38 - G.from + 1}, (_, i) => G.from + i).map(k => `<option value="${k}"${k === g ? ' selected' : ''}>J${k}</option>`).join('')}</select></label>
        <label>Sai <select id="lab-pl-out">${sq.map(p => `<option value="${p.id}">${POS_SHORT[p.cls]} · ${shortName(p.name)} £${p.price.toFixed(1)}</option>`).join('')}</select></label>
        <label>Entra <input list="lab-pl-dl" id="lab-pl-in" placeholder="Nome do jogador" autocomplete="off"></label>
        <datalist id="lab-pl-dl">${FULL_POOL.slice().sort((a, b) => b.total - a.total).slice(0, 450).map(p => `<option value="${p.name}">${TEAMS[p.team]} · ${POS_SHORT[p.cls]} · £${p.price.toFixed(1)}</option>`).join('')}</datalist>
        <button type="button" class="btn primary" data-lab="pladd">Marcar troca</button>
        <label>Capitão na J${g} <select id="lab-pl-cap"><option value="">o mesmo</option>${sq.filter(p => p.cls !== 'gk').map(p => `<option value="${p.id}"${(G.caps[g] || {}).c === p.id ? ' selected' : ''}>${shortName(p.name)}</option>`).join('')}</select></label>
      </div>
      ${all.length ? `<ul class="lab-plan-l">${all.map(k => G.plan[k].map((m, i) => { const sk = run && (run.rows.find(q => q.g === k) || {skip: []}).skip.find(s => s.m === m); return `<li>J${k}: <b>${labPn(m.out)} → ${labPn(m.in)}</b> <span class="note">£${(m.po || 0).toFixed(1)} → £${(m.pi || 0).toFixed(1)}</span>${sk ? ` <span class="down">não cabe: ${sk.why}</span>` : ''} <button type="button" class="linklike" data-lab="pldel" data-g="${k}" data-i="${i}" aria-label="Apagar esta troca">apagar</button></li>`; }).join('')).join('')}</ul>` : `<p class="note">Ainda sem trocas marcadas. Banco da fantasma na J${g}: £${st.bank.toFixed(1)}M.</p>`}
    </div>`;
  }
  function labDraw() {
    labDrawEx();
    [labDrawList, labDrawEdit, labDrawPick, labDrawEval, labDrawCmp, labDrawGhost].forEach(f => { try { f(); } catch (e) { console.error(e); } });
    if (LAB.ui.scroll) { const t = document.getElementById(LAB.ui.scroll); LAB.ui.scroll = null; if (t && t.offsetParent !== null) t.scrollIntoView({block: 'start'}); }
  }
  function renderLab() {
    if (!document.getElementById('lab-root')) return;
    labSeed(); labLoadRemote(); labDrawCmd(); labDraw();
  }
  // caches fora quando mudam os dados (live.json) ou o gestor
  function labReset() { LAB.lu = {}; LAB.simc = {}; LAB.ui.pick = LAB.ui.move = LAB.ui.out = null; LAB.ui.msg = null; LAB.ui.io = ''; lazyRender('mercado/lab', renderLab); }
  // "Guardar como experiência" (Equipa ideal, Equipa simulada, Comparar equipas)
  function labSaveFrom(kind, e) {
    const x = kind === 'ideal' ? labFromIdeal() : kind === 'simulada' ? labFromSim() : kind === 'rival' ? (+e === CMP_ENTRY[curMgr()] ? labFromSquad() : labFromRival(+e)) : null;
    if (!x) return null;
    labSay(true, `Guardei «${nwEsc(x.name)}» como experiência. ${labSumMsg(x)}`);
    showView('mercado', 'lab'); renderLab(); return x;
  }

  // ---------- cliques e mudanças (um só sítio) ----------
  function labRun(fn, heavy) {   // heavy: mostra "A calcular…" antes de um cálculo de 1-4 segundos
    const go = () => { let r = null; try { r = fn(); } catch (e) { console.error(e); r = 'erro interno'; } LAB.busy = false; if (typeof r === 'string' && r) labSay(false, r.charAt(0).toUpperCase() + r.slice(1) + '.'); labSave(); labDraw(); };
    if (heavy) { LAB.busy = true; labDrawEdit(); setTimeout(go, 40); } else go();
  }
  function labClick(ev) {
    const b = ev.target.closest('[data-lab]'); if (!b || b.disabled) return;
    const a = b.dataset.lab, id = +b.dataset.id || 0, S = labS(), U = LAB.ui; let x = labCur();
    if (a !== 'ex' && a !== 'go' && a !== 'copy') labSay(null);
    if (a === 'ex') { const i = document.getElementById('lab-cmd-in'); if (i) { i.value = b.textContent; i.focus(); } return; }
    if (a === 'go') { const t = document.getElementById(b.dataset.to); if (t) t.scrollIntoView({behavior: 'smooth', block: 'start'}); return; }
    if (a === 'sel') { S.sel = b.dataset.id; U.pick = U.move = U.out = null; U.more = 10; labSave(); labDraw(); return; }
    if (a === 'new') {
      const v = (document.getElementById('lab-src') || {}).value || 'plantel';
      labRun(() => { const n = v === 'raiz' ? labNew({name: 'Experiência', budget: 100}) : v === 'plantel' ? labFromSquad() : v === 'ideal' ? labFromIdeal() : v === 'simulada' ? labFromSim() : labFromRival(+v.slice(2));
        if (!n) return v === 'simulada' ? 'a Equipa simulada está vazia: monta-a primeiro ou escolhe outra origem' : 'não consegui criar a experiência';
        labSay(true, `Criei «${nwEsc(n.name)}». ${labSumMsg(n)}`); U.scroll = 'lab-edit'; }, v === 'ideal');
      return;
    }
    if (a === 'exp' || a === 'imp') { U.io = U.io === a ? '' : a; labDrawList(); return; }
    if (a === 'ioclose') { U.io = ''; labDrawList(); return; }
    if (a === 'copy') { const ta = document.getElementById('lab-code'); if (!ta) return; ta.select(); const done = () => { b.textContent = 'Copiado ✓'; }; try { navigator.clipboard.writeText(ta.value).then(done, () => { document.execCommand('copy'); done(); }); } catch (e) { try { document.execCommand('copy'); done(); } catch (e2) {} } return; }
    if (a === 'impgo') { const r = labImportCode((document.getElementById('lab-code-in') || {}).value); if (r.ok) U.io = ''; labSay(r.ok, r.msg); labDraw(); return; }
    if (a === 'undo') { labRun(() => { if (LAB.trash) { S.list.unshift(LAB.trash); S.sel = LAB.trash.id; LAB.trash = null; } }); return; }
    if (!x) return;
    if (a === 'copyrepo') { labRun(() => { const c = labCopyOf(x, true); labSay(true, `Criei «${nwEsc(c.name)}» nas tuas experiências.`); }); return; }
    if (a === 'ficha') { const pp = b.closest('.lab-act') && U.pick; if (pp) openPlayer(pp, b); return; }
    if (a === 'tok') {
      if (U.move && U.move !== id && !x.repo) { const from = U.move; U.move = null; U.pick = null; labRun(() => { const why = labMovePos(x, from, id); if (why) return `Não mudei: ${why}`; labSay(true, `${labPn(from)} e ${labPn(id)} trocaram de lugar. O onze e o banco passaram a «à mão».`); }); return; }
      U.move = null; U.pick = U.pick === id ? null : id; labDrawEdit(); return;
    }
    if (x.repo) return;
    const pick = U.pick;
    switch (a) {
      case 'dup': labRun(() => { const c = labCopyOf(x); labSay(true, `Criei «${nwEsc(c.name)}».`); }); break;
      case 'del': labRun(() => { S.list = S.list.filter(e => e.id !== x.id); S.cmp = S.cmp.filter(i => i !== x.id); S.sel = null; LAB.trash = x; U.pick = U.out = U.move = null; labSay(true, `Apaguei «${nwEsc(x.name)}».`); }); break;
      case 'bud': labRun(() => { const B = labMyBudget(); x.budget = b.dataset.m === 'real' ? B.real : B.market; x.bmode = b.dataset.m; }); break;
      case 'auto': labRun(() => { if (b.dataset.v === '1') { x.auto = true; x.xi = x.bench = null; x.cap = x.vice = null; } else if (!labManual(x)) return 'completa primeiro a equipa (15 jogadores) para escolheres o capitão e o banco à mão'; }); break;
      case 'hz': U.h = +b.dataset.v; labDrawEdit(); break;
      case 'fill': case 'fillgaps': labRun(() => { const why = labFill(x, a === 'fillgaps'); if (why) return why; labSay(true, `Completei «${nwEsc(x.name)}» com os melhores. ${labSumMsg(x)}`); }, true); break;
      case 'slot': U.pos = b.dataset.pos; U.out = null; U.more = 10; U.scroll = 'lab-pick'; labDraw(); break;
      case 'swapout': if (pick) { U.out = pick; U.more = 10; U.scroll = 'lab-pick'; labDraw(); } break;
      case 'outx': U.out = null; labDrawPick(); break;
      case 'lock': if (pick) labRun(() => { x.locked = x.locked.includes(pick) ? x.locked.filter(i => i !== pick) : [...x.locked, pick]; }); break;
      case 'cap': case 'vice': if (pick) labRun(() => { const why = labSetCap(x, pick, a === 'vice'); if (why) return `Não mudei: ${why}`; labSay(true, `${a === 'vice' ? 'Vice' : 'Capitão'}: ${labPn(pick)}. O onze e o banco passaram a «à mão».`); }); break;
      case 'move': if (pick) { U.move = pick; labDrawEdit(); } break;
      case 'movex': U.move = null; labDrawEdit(); break;
      case 'rm': if (pick) labRun(() => { labRemove(x, pick); U.pick = null; }); break;
      case 'in': labRun(() => { const p = FULL_POOL_BY_ID[id]; if (!p) return ''; const od = +b.dataset.out || 0, out = U.out && x.ids.includes(U.out) ? U.out : (od && x.ids.includes(od) ? od : null); const why = out ? labSwap(x, out, p) : labAdd(x, p); if (why) return `${shortName(p.name)} não entrou: ${why}`; labSay(true, out ? `Entrou ${shortName(p.name)} por ${labPn(out)}.` : `Entrou ${shortName(p.name)}.`); U.out = null; U.pick = null; U.scroll = 'lab-edit'; }); break;
      case 'more': U.more += 10; labDrawPick(); break;
      case 'ghmode': labRun(() => { if (x.ghost) x.ghost.mode = b.dataset.v; else U.gmode = b.dataset.v; }); break;
      case 'ghrestart': labRun(() => { const why = labGhostOn(x, GW_META.next, x.ghost ? x.ghost.mode : U.gmode); if (why) return why; }); break;
      case 'pladd': labRun(() => { const g = +(document.getElementById('lab-pl-gw') || {}).value, o = +(document.getElementById('lab-pl-out') || {}).value, n = FULL_POOL_BY_NAME[((document.getElementById('lab-pl-in') || {}).value || '').trim()] || labFindPlayer((document.getElementById('lab-pl-in') || {}).value);
        if (!n) return 'escolhe quem entra (um nome da lista)'; const why = labPlanAdd(x, g, o, n.id); if (why) return `Não marquei a troca: ${why}`; U.plgw = g; }); break;
      case 'pldel': labRun(() => { const g = +b.dataset.g; if (x.ghost && x.ghost.plan[g]) x.ghost.plan[g].splice(+b.dataset.i, 1); }); break;
    }
  }
  var labQt = null;
  function labChange(ev) {
    const t = ev.target, U = LAB.ui, S = labS(), x = labCur();
    if (t.dataset.labc === 'cmp') { if (t.checked) { if (S.cmp.filter(id => labGet(id)).length >= 4) { t.checked = false; labSay(false, 'Dá para comparar até 4 experiências de cada vez: desmarca uma primeiro.'); labDrawEdit(); return; } S.cmp = [...S.cmp.filter(id => labGet(id)), t.value]; } else S.cmp = S.cmp.filter(id => id !== t.value); labSave(); labDrawCmp(); return; }
    if (t.id === 'lab-f-pos') { U.pos = t.value; U.more = 10; labDrawPick(); return; }
    if (t.id === 'lab-f-team') { U.team = t.value; U.more = 10; labDrawPick(); return; }
    if (t.id === 'lab-f-sort') { U.sort = t.value; labDrawPick(); return; }
    if (t.id === 'lab-f-fit') { U.fit = t.checked; labDrawPick(); return; }
    if (t.id === 'lab-f-price') { U.price = t.value; labDrawPick(); return; }
    if (t.id === 'lab-gh-from') { labRun(() => { if (x && x.ghost && !x.repo) x.ghost.from = +t.value; else U.gfrom = +t.value; }); return; }
    if (t.id === 'lab-pl-gw') { U.plgw = +t.value; labDrawGhost(); return; }
    if (!x || x.repo) return;
    if (t.id === 'lab-name') { labRun(() => { const n = t.value.trim().slice(0, 60); if (n && n !== x.name) { x.name = ''; x.name = labName(n); } }); return; }
    if (t.id === 'lab-note') { x.note = t.value.slice(0, 400); labSave(); labDrawList(); return; }
    if (t.id === 'lab-budget') { labRun(() => { x.budget = +Math.max(60, Math.min(130, +t.value || 100)).toFixed(1); x.bmode = 'livre'; }); return; }
    if (t.id === 'lab-gh-on') { labRun(() => { if (!t.checked) { x.ghost = null; return ''; } return labGhostOn(x, U.gfrom && U.gfrom <= GW_META.next ? U.gfrom : GW_META.next, U.gmode); }); return; }
    if (t.id === 'lab-pl-cap') { labRun(() => { const g = +(document.getElementById('lab-pl-gw') || {}).value, G = x.ghost; if (!G) return ''; if (t.value) G.caps[g] = {c: +t.value, v: (G.caps[g] || {}).v || null}; else delete G.caps[g]; }); return; }
  }
  (function labInit() {
    const root = document.getElementById('lab-root'); if (!root) return;
    root.addEventListener('click', labClick);
    root.addEventListener('change', labChange);
    root.addEventListener('input', ev => { if (ev.target.id !== 'lab-f-q') return; clearTimeout(labQt); const v = ev.target.value; labQt = setTimeout(() => { LAB.ui.q = v; LAB.ui.more = 10; labDrawPick(); const i = document.getElementById('lab-f-q'); if (i) { i.focus(); try { i.setSelectionRange(v.length, v.length); } catch (e) {} } }, 220); });
    root.addEventListener('submit', ev => {
      if (ev.target.id !== 'lab-cmdf') return; ev.preventDefault();
      const inp = document.getElementById('lab-cmd-in'), out = document.getElementById('lab-cmd-out'), v = inp.value.trim(); if (!v) return;
      out.hidden = false; out.className = 'lab-out'; out.textContent = 'A fazer…'; labSay(null);
      setTimeout(() => { const r = labCmd(v); out.className = 'lab-out ' + (r.ok ? 'ok' : 'bad'); out.innerHTML = r.msg; if (r.ok) inp.value = ''; LAB.ui.pick = LAB.ui.move = LAB.ui.out = null; labDraw(); }, 30);
    });
  })();
  var LAB_READY = true;
  window.labCmd = labCmd; window.labReport = labReport;
  lazyRender('mercado/lab', renderLab);
