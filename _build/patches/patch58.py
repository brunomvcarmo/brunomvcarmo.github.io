"""V58 (8 nov 2026): lesões e castigos — quando volta cada lesionado e quem pode falhar jogos por castigo.
- Dados: AVAIL_PRED no bloco de dados (gerado por _build/pool/disponibilidade.py, chamado pelo gen25.py), a partir de
  _build/research/injuries.json (durações por tipo + pesquisa na web) e _build/research/discipline.json (regras 2026/27).
- A app refaz as contas com a data de hoje e o live.json (estado, notícia, data da notícia, amarelos): av58Calc.
- Pontos esperados de cada jornada = pontos "se jogar" × disponibilidade prevista (av58Apply) → onze, capitão,
  planeador e plano automático passam a contar com o regresso e com os castigos.
- Ficha do jogador (regresso provável, amarelos, conselho aguentar/vender), etiquetas no cartão, avisos no Resumo,
  nota em Esta semana › Transferências, e a lista nova Jogadores › Lesões e castigos.
Uso (a partir da raiz): py -X utf8 _build/patches/patch58.py   (Linux: python3)"""
from pathlib import Path

H = Path(__file__).resolve().parents[2] / 'index.html'
s = H.read_text(encoding='utf-8')


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)


# ---------------------------------------------------------------- 1. núcleo (logo a seguir ao FULL_POOL)
CORE = r'''
  // ===================================================================
  // V58 (8 nov 2026): lesões e castigos — disponibilidade prevista. As mesmas contas do
  // _build/pool/disponibilidade.py, refeitas aqui com a data de hoje e o estado do live.json.
  // ===================================================================
  var AV58 = {rows: {}, ok: typeof AVAIL_PRED !== 'undefined' && AVAIL_PRED && AVAIL_PRED.p};
  var AV58_MON = {Jan: 0, Feb: 1, Mar: 2, Apr: 3, May: 4, Jun: 5, Jul: 6, Aug: 7, Sep: 8, Oct: 9, Nov: 10, Dec: 11};
  function av58Phi(x) {
    const z = Math.abs(x) / Math.SQRT2, t = 1 / (1 + 0.3275911 * z);
    const y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-z * z);
    return 0.5 * (1 + (x >= 0 ? y : -y));
  }
  function av58Cdf(x, mn, md, mx) {
    if (x <= mn) return 0;
    const a = Math.max(0.5, md - mn), b = Math.max(1, mx - mn), sig = Math.max(0.2, Math.log(Math.max(b / a, 1.05)) / 1.2816);
    return av58Phi((Math.log(x - mn) - Math.log(a)) / sig);
  }
  function av58NewsDate(news, ref) {
    const m = /(?:until|back)\s+(\d{1,2})\s+([A-Z][a-z]{2})/.exec(news || ''); if (!m || !(m[2] in AV58_MON)) return null;
    const y = new Date(ref).getUTCFullYear(); let d = Date.UTC(y, AV58_MON[m[2]], +m[1]);
    if (d < ref - 120 * 864e5) d = Date.UTC(y + 1, AV58_MON[m[2]], +m[1]);
    return d;
  }
  function av58Classify(news) {
    const n = (news || '').toLowerCase().replace(/expected back.*|unknown return.*|\d+% chance.*/g, '');
    for (const [k, rx] of (AVAIL_PRED.rx || [])) if (new RegExp(rx).test(n)) return k;
    return 'unknown';
  }
  function av58Ko(g, team) { const k = ((AVAIL_PRED.ko || {})[g] || {})[team]; return k ? Date.parse(k) : null; }
  function av58Show() {
    const now = Date.now();
    return (AVAIL_PRED.show || []).filter(g => Object.values(AVAIL_PRED.ko[g] || {}).filter(Boolean).every(k => Date.parse(k) > now)).slice(0, 6);
  }
  function av58InjParams(p, base) {
    // a mesma notícia da última atualização → os parâmetros dela (incluem a pesquisa na web e os prazos dos treinadores)
    if (base && base.inj && base.inj.news === (p.news || '') && base.inj.st === p.status) return base.inj;
    const now = Date.now(), ty = av58Classify(p.news), d = AVAIL_PRED.dur[ty] || AVAIL_PRED.dur.unknown;
    const t0 = p.nadd ? Date.parse(p.nadd) : now;
    let [mn, md, mx] = d, src = 'tipo', late = false, T0 = t0;
    if (/back/i.test(p.news || '')) {
      const fb = av58NewsDate(p.news, t0);
      if (fb) { const dd = (fb - t0) / 864e5; mn = Math.max(0, dd - 3); md = Math.max(mn + 1, dd); mx = Math.max(md + 2, dd + 7); src = 'FPL'; }
    }
    const el = (now - t0) / 864e5;
    if (p.status === 'i' && src === 'tipo' && 1 - av58Cdf(el, mn, md, mx) < 0.15) { T0 = now; mn = 3; md = Math.max(10, 0.5 * el); mx = Math.max(35, 1.5 * el); late = true; }
    return {ty, t0: new Date(T0).toISOString(), mn, md, mx, src, late, st: p.status, ch: p.chance, news: p.news || '', fresh: true};
  }
  function av58Calc(p) {
    const base = (AVAIL_PRED.p || {})[p.id] || null, now = Date.now(), G = AVAIL_PRED.gws || [];
    const av = {}; G.forEach(g => { av[g] = 1; });
    const r = {base, av, inj: null, sus: null, pend: null, risk: null, web: base && base.web || null};
    const st = p.status;
    if (st === 'i' || st === 'd') {
      const P = av58InjParams(p, base); r.inj = P;
      const up = G.filter(g => { const k = av58Ko(g, p.team); return k && k > now; });
      if (st === 'd' || (p.chance != null && p.chance > 0)) {
        const c = (p.chance != null ? p.chance : 75) / 100;
        G.forEach(g => { const k = up.indexOf(g); av[g] = k >= 0 ? 1 - (1 - c) * Math.pow(0.35, k) : c; });
      } else {
        const t0 = Date.parse(P.t0), el = Math.max(0, (now - t0) / 864e5), sv = Math.max(1e-6, 1 - av58Cdf(el, P.mn, P.md, P.mx));
        G.forEach(g => {
          const k = av58Ko(g, p.team); if (!k || k <= now) { av[g] = 0; return; }
          const d = (k - 864e5 - t0) / 864e5;
          av[g] = Math.max(0, Math.min(1, (av58Cdf(d, P.mn, P.md, P.mx) - (1 - sv)) / sv));
        });
      }
    } else if (st === 'u' || st === 'n') G.forEach(g => { av[g] = 0; });
    // castigos confirmados pela FPL ("Suspended until …")
    const ban = new Set();
    if (st === 's') {
      const until = av58NewsDate(p.news, now);
      const fut = G.map(g => [av58Ko(g, p.team), g]).filter(x => x[0] && x[0] > now).sort((a, b) => a[0] - b[0]);
      fut.forEach((x, i) => { if ((until && x[0] < until) || (!until && i === 0)) ban.add(x[1]); });
      r.sus = {until, gws: [...ban]};
    }
    // castigo por amarelos ainda por cumprir (limite atingido, a FPL ainda não marcou)
    if (base && base.pend && st !== 's') {
      const gws = base.pend.gws.filter(g => { const k = av58Ko(g, p.team); return k && k > now; });
      gws.forEach(g => ban.add(g)); if (gws.length) r.pend = Object.assign({}, base.pend, {gws});
    }
    // risco de castigo por amarelos (calculado na atualização; se entretanto levou outro amarelo, fica "desatualizado")
    if (base && base.risk) {
      const yc = p.yc != null ? p.yc : base.risk.yc;
      r.risk = Object.assign({}, base.risk, {stale: yc !== base.risk.yc});
      if (r.risk.stale && yc >= base.risk.n && st !== 's') {
        const fut = G.map(g => [av58Ko(g, p.team), g]).filter(x => x[0] && x[0] > now).sort((a, b) => a[0] - b[0]).slice(0, base.risk.ban);
        fut.forEach(x => ban.add(x[1])); r.pend = {n: base.risk.n, gw: null, left: base.risk.ban, gws: fut.map(x => x[1])};
      }
      if (!r.risk.stale) G.forEach(g => { av[g] = av[g] * (1 - Math.min(1, base.risk.pb[g] || 0)); });
    }
    ban.forEach(g => { av[g] = 0; });
    let prev = st === 'i' ? 0 : 1; r.ef = {};
    G.forEach(g => { const a = av[g]; r.ef[g] = a > prev ? prev + (a - prev) * 0.7 : a; prev = a; });
    r.show = av58Show();
    if (r.inj || r.sus || r.pend || st === 'u' || st === 'n') {
      const g = r.show.find(x => av[x] >= 0.5); r.ret = g || null; r.retP = g ? av[g] : null;
    }
    return r;
  }
  function av58(p) {
    if (!p || !AV58.ok) return null;
    return AV58.rows[p.id] || (AV58.rows[p.id] = av58Calc(p));
  }
  // pontos esperados = pontos "se jogar" × disponibilidade (70% dos minutos na 1.ª jornada depois de voltar)
  function av58Apply() {
    if (!AV58.ok) return;
    AV58.rows = {};
    const H = GW_META.horizon;
    FULL_POOL.forEach(p => {
      if (!p.ep0) p.ep0 = (p.epRaw || p.epH).slice();
      if (p.status0 === undefined) p.status0 = p.status;
      const base = AVAIL_PRED.p[p.id];
      if (!base && p.status === p.status0) return;
      const r = av58(p), f = base ? base.f : p.ep0;
      const v = H.map((g, k) => +((f[k] || 0) * (k === 0 && base && base.rd0 ? 1 : (r.ef[g] != null ? r.ef[g] : 1))).toFixed(1));
      if (p.epRaw) p.epRaw = v;
      p.epH = v.slice();
    });
  }
  try { av58Apply(); } catch (e) { console.error(e); }
'''
rep("  const FULL_POOL_BY_ID = Object.fromEntries(FULL_POOL.map(p => [p.id, p]));\n",
    "  const FULL_POOL_BY_ID = Object.fromEntries(FULL_POOL.map(p => [p.id, p]));\n" + CORE)

# ---------------------------------------------------------------- 2. live.json: data da notícia, amarelos, vermelhos, minutos
rep("      const [cost, status, chance, news, own, , total, tin, tout] = a;\n"
    "      p.price = cost / 10; p.status = status; p.chance = chance; p.news = news; p.own = +own; p.total = total;\n"
    "      if (tin != null) { p.tin = tin; p.tout = tout; }\n    });\n",
    "      const [cost, status, chance, news, own, , total, tin, tout, nadd, yc, rc, mins] = a;\n"
    "      p.price = cost / 10; p.status = status; p.chance = chance; p.news = news; p.own = +own; p.total = total;\n"
    "      if (tin != null) { p.tin = tin; p.tout = tout; }\n"
    "      if (yc != null) { p.nadd = nadd; p.yc = yc; p.rc = rc; p.smin = mins; }\n    });\n"
    "    try { av58Apply(); } catch (e) { console.error(e); }   // V58: refaz a disponibilidade com o estado novo\n")
rep("    try { v57PendNote(); } catch (e) { console.error(e); }\n  }\n",
    "    try { v57PendNote(); } catch (e) { console.error(e); }\n    try { av58Refresh(); } catch (e) { console.error(e); }\n  }\n")
rep("    try { if (typeof dgwData === 'function') renderDgw(); } catch (e) {}\n",
    "    try { if (typeof dgwData === 'function') renderDgw(); } catch (e) {}\n    try { av58Refresh(); } catch (e) {}\n")

# ---------------------------------------------------------------- 3. interface (a seguir aos cartões de jogador)
UI = r'''
  // ===================================================================
  // V58: lesões e castigos na interface — textos, ficha, etiquetas, avisos, nota no planeador e lista
  // ===================================================================
  const av58Pct = v => Math.round((v || 0) * 100) + '%';
  function av58Cards(p) {
    const c = (AVAIL_PRED.cards || {})[p.id] || [0, 0];
    return {yc: p.yc != null ? p.yc : c[0], rc: p.rc != null ? p.rc : c[1]};
  }
  // próximo limite de amarelos que ainda conta (5 até ao 19.º jogo da equipa, 10 até ao 32.º, 15 até ao fim)
  function av58Next(p) {
    const {yc} = av58Cards(p), tm = (AVAIL_PRED.tm || {})[p.team] || 0;
    const t = (AVAIL_PRED.thr || []).find(([n, cut]) => n > yc && tm < cut); if (!t) return null;
    return {n: t[0], cut: t[1], ban: t[2], need: t[0] - yc, cutGw: ((AVAIL_PRED.cut || {})[p.team] || {})[t[1]] || null};
  }
  const av58BanTxt = n => n === 1 ? 'um jogo' : n + ' jogos';
  function av58RetTxt(p) {
    const r = av58(p); if (!r || !(r.inj || r.sus || r.pend || ['u', 'n'].includes(p.status))) return '';
    const S = r.show; if (!S.length) return '';
    if (r.sus && !r.inj && !r.pend) {
      const back = S.find(g => !r.sus.gws.includes(g));
      return r.sus.gws.length ? `Castigado: falha a J${r.sus.gws.filter(g => S.includes(g)).join(', J')}${back ? ` · volta na J${back}` : ''}` : `Castigo cumprido: pode jogar na J${S[0]}`;
    }
    if (r.pend && !r.inj) return `Castigo por ${r.pend.n} amarelos: falha a J${r.pend.gws.join(', J')}`;
    const g = r.ret;
    if (!g) { const z = S[S.length - 1]; return `Regresso: provavelmente depois da J${z} (J${z}: ${av58Pct(r.av[z])})`; }
    if (g === S[0] && r.av[g] >= 0.85) return `Deve jogar na J${g} (${av58Pct(r.av[g])})`;
    const nx = S[S.indexOf(g) + 1];
    return `Regresso provável: J${g} (${av58Pct(r.av[g])})${nx ? ` · J${nx} ${av58Pct(r.av[nx])}` : ''}`;
  }
  function av58YcTxt(p, long) {
    const {yc, rc} = av58Cards(p), nt = av58Next(p);
    if (!yc && !rc && !long) return '';
    let s = `Amarelos: ${yc}${rc ? ` · vermelhos: ${rc}` : ''}`;
    if (nt && nt.need <= 2) s += ` · a ${nt.need} de ${av58BanTxt(nt.ban)} de castigo${nt.cutGw ? ` (os ${nt.n} contam até à J${nt.cutGw})` : ''}`;
    else if (nt && long) s += ` · próximo limite: ${nt.n} até à J${nt.cutGw || '?'}`;
    return s;
  }
  // "se levar amarelo na J11 (≈27%), falha a J12"
  function av58RiskTxt(p) {
    const r = av58(p); if (!r || !r.risk || r.risk.stale) return '';
    const R = r.risk, pm = Object.fromEntries(R.pm || []);
    const S0 = r.show[0] || 0;
    const ex = (R.ex || []).filter(([g]) => g >= S0).slice(0, 2).map(([g, miss]) => `se levar amarelo na J${g} (≈${av58Pct(pm[g])}), falha a J${miss.join(' e a J')}`);
    const S = r.show, tot = S.reduce((s, g) => s + (R.pb[g] || 0), 0);
    return (R.need === 1 ? ex.join('; ') + '. ' : `Precisa de mais ${R.need} amarelos para chegar aos ${R.n}. `)
      + `Probabilidade de falhar um jogo por castigo até à J${S[S.length - 1]}: ≈${av58Pct(Math.min(1, tot))}.`;
  }
  function av58Strip(p, kind) {
    const r = av58(p); if (!r) return '';
    const cells = r.show.map(g => {
      const v = kind === 'ban' ? 1 - Math.min(1, (r.risk && r.risk.pb[g]) || 0) * (r.risk && !r.risk.stale ? 1 : 0) : r.av[g];
      const shown = kind === 'ban' ? 1 - v : v;
      const c = kind === 'ban' ? (shown >= 0.2 ? 'lo' : shown >= 0.08 ? 'mid' : 'hi') : (v >= 0.75 ? 'hi' : v >= 0.4 ? 'mid' : 'lo');
      return `<span class="av58-c ${c}" title="J${g}: ${kind === 'ban' ? 'probabilidade de falhar por castigo' : 'probabilidade de estar disponível'} ${av58Pct(shown)}"><b>J${g}</b>${av58Pct(shown)}</span>`;
    }).join('');
    return `<span class="av58-strip" aria-label="${kind === 'ban' ? 'Probabilidade de castigo' : 'Probabilidade de estar disponível'} por jornada">${cells}</span>`;
  }
  // vender já ou aguentar com o banco: jogos que deve falhar e o melhor substituto que cabe no orçamento
  function av58Verdict(p, mgr) {
    const r = av58(p); if (!r || !(r.inj || r.sus || r.pend || ['u', 'n'].includes(p.status))) return null;
    const S = r.show.slice(0, 5); if (!S.length) return null;
    const miss = S.reduce((s, g) => s + (1 - r.av[g]), 0), n = Math.round(miss);
    const st = SQUAD_STATE[mgr] || {players: [], bank: 0};
    const me = st.players.find(x => x.id === p.id), budget = (me ? me.sell : p.price) + (st.bank || 0);
    const have = new Set(st.players.map(x => x.id)), clubs = {};
    st.players.forEach(x => { const q = FULL_POOL_BY_ID[x.id]; if (q && q.id !== p.id) clubs[q.team] = (clubs[q.team] || 0) + 1; });
    const H = GW_META.horizon, ks = H.map((g, k) => k).filter(k => S.includes(H[k]));
    const val = q => ks.reduce((s, k) => s + epAt(q, k), 0);
    let best = null, bv = -1;
    FULL_POOL.forEach(q => {
      if (q.cls !== p.cls || have.has(q.id) || q.price > budget + 1e-9 || (clubs[q.team] || 0) >= 3) return;
      const v = val(q); if (v > bv) { best = q; bv = v; }
    });
    const gain = best ? bv - val(p) : 0, lastG = ks.length ? H[ks[ks.length - 1]] : S[S.length - 1];
    const span = `das J${S[0]}-J${S[S.length - 1]}`;
    if (miss < 1.5) return {kind: 'hold', txt: `${r.ret ? `volta na J${r.ret}` : 'deve voltar já'}: compensa aguentar com o banco`};
    if (miss >= 3 || gain >= 6) return {kind: 'sell', txt: `fora ≈${n} jogo${n === 1 ? '' : 's'} ${span}: vende${best ? ` (ex.: ${shortName(best.name)}, +${f1(gain)} pts esperados até à J${lastG})` : ''}`};
    return {kind: 'maybe', txt: `deve falhar ≈${n} jogo${n === 1 ? '' : 's'} ${span}: aguentar ou vender é renhido — vê o plano automático em Transferências`};
  }
  function av58Ficha(p, mine) {
    const r = av58(p); if (!r) return '';
    const parts = [];
    const ret = av58RetTxt(p);
    if (ret) {
      const I = r.inj, src = I && I.st === 'd' ? `chance de jogar dada pela FPL (${p.chance != null ? p.chance : 75}%)` : I ? ({treinador: 'prazo dado pelo treinador', 'notícia': 'prazo da imprensa', FPL: 'data prevista pela FPL', tipo: 'duração típica deste tipo de lesão'}[I.src] || I.src) : '';
      parts.push(`<div class="av58-row"><b>${ret}</b>${I ? `<div class="note">Lesão: ${(AVAIL_PRED.tpt || {})[I.ty] || I.ty} · base: ${src}${I.late ? ' (já passou o tempo normal: conta-se como mais grave)' : ''}${I.fresh ? ' · calculado com o estado de hoje da FPL' : ''}</div>` : ''}${av58Strip(p)}</div>`);
      if (r.web && r.web.s) parts.push(`<p class="note">${r.web.s} <a href="${r.web.u}" target="_blank" rel="noopener">Fonte</a> (${r.web.d}).</p>`);
      if (mine) { const v = av58Verdict(p, curMgr()); if (v) parts.push(`<p class="av58-verdict ${v.kind}"><b>${v.kind === 'sell' ? 'Vender' : v.kind === 'hold' ? 'Aguentar' : 'Renhido'}:</b> ${v.txt}.</p>`); }
    }
    const yct = av58YcTxt(p, false);
    if (yct) parts.push(`<div class="av58-row"><b>${yct}</b>${av58RiskTxt(p) ? `<div class="note">${av58RiskTxt(p)}</div>${av58Strip(p, 'ban')}` : ''}</div>`);
    if (!parts.length) return '';
    return `<div class="av58-ficha"><h3>Disponibilidade prevista</h3>${parts.join('')}<p class="note">Probabilidades, não certezas: lesões pela data da notícia da FPL, pelo tipo de lesão (estudo UEFA) e pelo que os treinadores disseram; castigos pelas regras da FA para 2026/27.</p></div>`;
  }
  function av58Tags(p) {
    if (!AV58.ok) return '';
    const r = av58(p), T = [];
    if (r && r.inj && r.ret && r.ret !== r.show[0]) T.push(`<span class="pc-tag ret" title="${av58RetTxt(p)}">volta J${r.ret}?</span>`);
    else if (r && r.inj && !r.ret && p.status === 'i') T.push(`<span class="pc-tag inj" title="${av58RetTxt(p)}">fora 6+</span>`);
    const nt = av58Next(p);
    if (nt && nt.need === 1) T.push(`<span class="pc-tag yc" title="${av58Cards(p).yc} amarelos: a 1 de ${av58BanTxt(nt.ban)} de castigo">${av58Cards(p).yc} amar.</span>`);
    if (r && r.pend) T.push(`<span class="pc-tag inj" title="Castigo por amarelos">castigo J${r.pend.gws.join(',')}</span>`);
    return T.join('');
  }
  // avisos do Resumo: o meu plantel, a troca sugerida e os jogadores do meu plano
  function av58Alerts(add, squad, mv, A) {
    if (!AV58.ok) return;
    const mgr = curMgr(), where = new Map();
    squad.forEach(p => where.set(p.id, 'plantel'));
    (mv || []).forEach(m => { if (!where.has(m.in)) where.set(m.in, 'troca sugerida'); });
    ((STORE.plan || {})[mgr] || []).forEach(m => { if (!where.has(m.in)) where.set(m.in, 'no teu plano'); });
    where.forEach((w, id) => {
      const p = FULL_POOL_BY_ID[id]; if (!p) return;
      const r = av58(p); if (!r) return;
      const ret = av58RetTxt(p);
      if (ret) {
        const v = w === 'plantel' ? av58Verdict(p, mgr) : null;
        const extra = `${ret}${v ? ' — ' + v.txt : ''} (probabilidades, não certezas)`;
        const old = A.find(a => a.pid === p.id && a.cat === 'Lesões');
        if (old) old.txt = old.txt.replace(/\.$/, '') + '. ' + extra + '.';
        else add(w === 'plantel' ? 2 : 1, 'Regresso', `${p.name} (${w}): ${extra}.`, {pid: p.id, goto: 'mercado', gotoSub: 'lesoes'});
      }
      const nt = av58Next(p);
      if (nt && nt.need === 1 && r.risk && !r.risk.stale) {
        const S = r.show.slice(0, 3), near = S.reduce((s, g) => s + (r.risk.pb[g] || 0), 0);
        if (near >= 0.1) add(w === 'plantel' ? 2 : 1, 'Castigo', `${p.name} (${w}): ${av58Cards(p).yc} amarelos, a 1 de ${av58BanTxt(nt.ban)} de castigo — ${av58RiskTxt(p)}`, {pid: p.id, goto: 'mercado', gotoSub: 'lesoes'});
      }
    });
  }
  // Esta semana › Transferências: aguentar ou vender os lesionados e castigados do plantel
  function av58PlanNote() {
    const sv = document.querySelector('.view[data-view="semana"] > .subview[data-sub="transferencias"]'); if (!sv || !AV58.ok) return;
    const mgr = curMgr(), L = squadOf(mgr).filter(Boolean).map(p => [p, av58Verdict(p, mgr)]).filter(x => x[1]);
    let n = sv.querySelector('.av58-note');
    if (!L.length) { if (n) n.remove(); return; }
    if (!n) { n = document.createElement('div'); n.className = 'callout info av58-note'; const v57 = sv.querySelector('.v57-note'); sv.insertBefore(n, v57 ? v57.nextSibling : sv.firstChild); }
    n.innerHTML = `<span class="icon">i</span><div class="body"><p><b>Lesionados e castigados do teu plantel</b> (os pontos esperados e o plano automático já contam com o regresso previsto):</p><ul>${L.map(([p, v]) => `<li><span class="player-name" data-pid="${p.id}">${shortName(p.name)}</span>: ${av58RetTxt(p)} — <b>${v.kind === 'sell' ? 'vender' : v.kind === 'hold' ? 'aguentar' : 'renhido'}</b>: ${v.txt}.</li>`).join('')}</ul><p class="note">Probabilidades, não certezas. <button type="button" class="linklike" data-av58go>Ver todos os lesionados e castigos</button></p></div>`;
    const b = n.querySelector('[data-av58go]'); if (b) b.addEventListener('click', () => showView('mercado', 'lesoes'));
  }
  // Jogadores › Lesões e castigos
  var AV58L = {who: 'all', kind: 'all', more: false};
  function av58Rivals() {
    const me = String(CMP_ENTRY[curMgr()]), s = new Set();
    Object.entries(LEAGUE_SQUADS).forEach(([e, L]) => { if (e !== me) [...(L.s || []), ...(L.b || [])].forEach(i => s.add(i)); });
    return s;
  }
  function renderAv58List() {
    const el = document.getElementById('av58-list'); if (!el) return;
    if (!AV58.ok) { el.innerHTML = '<p class="note">Sem dados de disponibilidade nesta versão.</p>'; return; }
    const mine = new Set(squadOf(curMgr()).filter(Boolean).map(p => p.id)), riv = av58Rivals();
    const okWho = p => AV58L.who === 'mine' ? mine.has(p.id) : AV58L.who === 'riv' ? riv.has(p.id) : true;
    const rel = p => mine.has(p.id) || riv.has(p.id) || (p.own || 0) >= 1 || p.price >= 6;
    const score = p => (mine.has(p.id) ? 1000 : 0) + (p.lown || 0) * 5 + (p.own || 0);
    const inj = FULL_POOL.filter(p => ['i', 'd', 'u', 'n'].includes(p.status) && okWho(p) && (AV58L.who !== 'all' || rel(p)) && (p.status !== 'u' || mine.has(p.id) || riv.has(p.id)))
      .sort((a, b) => score(b) - score(a));
    const dis = FULL_POOL.filter(p => {
      if (!okWho(p)) return false;
      const r = av58(p), nt = av58Next(p);
      if (p.status === 's' || (r && r.pend)) return true;
      return nt && nt.need <= (AV58L.who === 'all' ? 1 : 2) && (AV58L.who !== 'all' || rel(p));
    }).sort((a, b) => ((b.status === 's' || (av58(b) || {}).pend) ? 1 : 0) - ((a.status === 's' || (av58(a) || {}).pend) ? 1 : 0)
      || (av58Next(a) || {need: 9}).need - (av58Next(b) || {need: 9}).need || score(b) - score(a));
    const lim = AV58L.more ? 400 : 24;
    const injCard = p => ({note: `${av58RetTxt(p)}${(av58(p) || {}).inj ? ` · ${(AVAIL_PRED.tpt || {})[av58(p).inj.ty] || ''}` : ''}${(av58(p) || {}).web ? ' · com notícias da semana' : ''}${mine.has(p.id) && av58Verdict(p, curMgr()) ? ` · <b>${av58Verdict(p, curMgr()).txt}</b>` : ''}`, extra: av58Strip(p)});
    const disCard = p => {
      const r = av58(p) || {};
      const head = p.status === 's' ? av58RetTxt(p) : r.pend ? av58RetTxt(p) : av58YcTxt(p, false);
      return {note: `${head}${p.status !== 's' && !r.pend && av58RiskTxt(p) ? ' · ' + av58RiskTxt(p) : ''}`, extra: p.status === 's' || r.pend ? av58Strip(p) : av58Strip(p, 'ban')};
    };
    const sec = (title, sub, list, f) => `<section class="card"><div class="card-head"><div><h2>${title} <span class="note">(${list.length})</span></h2><div class="card-sub">${sub}</div></div></div>${list.length ? playerCards(list.slice(0, lim), f) : '<p class="note">Ninguém nesta lista.</p>'}</section>`;
    const S = av58Show();
    el.innerHTML = (AV58L.kind !== 'dis' ? sec('Lesionados e em dúvida', `Probabilidade de estar disponível em cada jornada (J${S[0]}-J${S[S.length - 1]}) e a jornada mais provável de regresso (a primeira com 50% ou mais).`, inj, injCard) : '')
      + (AV58L.kind !== 'inj' ? sec('Castigos e amarelos', 'Castigados agora e quem está a 1 amarelo de um jogo de castigo (com o filtro do plantel ou dos rivais, também a 2). Barras = probabilidade de falhar essa jornada por castigo.', dis, disCard) : '')
      + ((inj.length > lim || dis.length > lim) && !AV58L.more ? '<div style="text-align:center"><button type="button" class="btn" id="av58-more">Mostrar mais</button></div>' : '');
    const m = document.getElementById('av58-more'); if (m) m.addEventListener('click', () => { AV58L.more = true; renderAv58List(); });
  }
  function av58Refresh() {
    try { av58PlanNote(); } catch (e) { console.error(e); }
    try { lazyRender('mercado/lesoes', renderAv58List); } catch (e) { console.error(e); }
  }
  (function av58Init() {
    document.querySelectorAll('#av58-who .seg-btn, #av58-kind .seg-btn').forEach(b => b.addEventListener('click', () => {
      const g = b.parentElement; g.querySelectorAll('.seg-btn').forEach(x => x.setAttribute('aria-pressed', x === b ? 'true' : 'false'));
      if (g.id === 'av58-who') AV58L.who = b.dataset.w; else AV58L.kind = b.dataset.k;
      AV58L.more = false; renderAv58List();
    }));
    const r = document.getElementById('av58-rules');
    if (r && AV58.ok) r.innerHTML = `Castigos (FA, 2026/27): 5 amarelos até ao 19.º jogo da equipa na Premier League = 1 jogo; 10 até ao 32.º = 2 jogos; 15 = 3 jogos. Só contam os amarelos da Premier League e o castigo cumpre-se na Premier League. Vermelho: 1 jogo (2.º amarelo ou impedir uma ocasião de golo), 2 (linguagem ofensiva), 3 (jogo violento ou conduta violenta), 6 (cuspir) — cumpre-se também nas taças inglesas. Lesões: duração típica de cada tipo (estudo UEFA de lesões em clubes de elite), contada desde a notícia da FPL, e os prazos dados pelos treinadores. Calculado ${new Date(AVAIL_PRED.gen).toLocaleDateString('pt-PT', {day: 'numeric', month: 'short'})}; refeito com o estado de hoje da FPL.`;
    av58Refresh();
  })();
'''
rep("  var PC_READY = true;", UI + "  var PC_READY = true;")

# ---------------------------------------------------------------- 4. ficha, cartão, avisos
rep("      ${p.news ? `<p class=\"note\" style=\"margin:6px 0 0\">Notícia oficial da FPL: ${p.news}</p>` : ''}\n",
    "      ${p.news ? `<p class=\"note\" style=\"margin:6px 0 0\">Notícia oficial da FPL: ${p.news}</p>` : ''}\n"
    "      ${(() => { try { return av58Ficha(p, !!mine); } catch (e) { console.error(e); return ''; } })()}\n")
rep("    if (o.tags) T.push(o.tags);\n    return T.join('');",
    "    try { T.push(av58Tags(p)); } catch (e) {}\n    if (o.tags) T.push(o.tags);\n    return T.join('');")
rep("    try { v57StaleAlert(add); } catch (e) { console.error(e); }\n",
    "    try { v57StaleAlert(add); } catch (e) { console.error(e); }\n    try { av58Alerts(add, squad, mv, A); } catch (e) { console.error(e); }\n")

# ---------------------------------------------------------------- 5. separador novo em Jogadores
rep('        <button class="subtab" type="button" data-sub="precos">Preços e alternativas</button>\n',
    '        <button class="subtab" type="button" data-sub="precos">Preços e alternativas</button>\n'
    '        <button class="subtab" type="button" data-sub="lesoes">Lesões e castigos</button>\n')
rep('      <div class="subview" data-sub="precos" hidden>\n',
    '''      <div class="subview" data-sub="lesoes" hidden>
        <section class="card">
          <h2>Lesões e castigos</h2>
          <div class="card-sub">Quando volta cada lesionado e quem pode falhar jogos por castigo. São probabilidades, não certezas.</div>
          <div class="av58-filters">
            <div class="seg" role="group" aria-label="De quem" id="av58-who"><button type="button" class="seg-btn" data-w="all" aria-pressed="true">Todos</button><button type="button" class="seg-btn" data-w="mine" aria-pressed="false">Só o meu plantel</button><button type="button" class="seg-btn" data-w="riv" aria-pressed="false">Só os rivais</button></div>
            <div class="seg" role="group" aria-label="O quê" id="av58-kind"><button type="button" class="seg-btn" data-k="all" aria-pressed="true">Tudo</button><button type="button" class="seg-btn" data-k="inj" aria-pressed="false">Lesões</button><button type="button" class="seg-btn" data-k="dis" aria-pressed="false">Castigos</button></div>
          </div>
          <p class="note" id="av58-rules"></p>
        </section>
        <div class="stack" id="av58-list"></div>
      </div>
      <div class="subview" data-sub="precos" hidden>
''')
rep('"Em forma", "Preços e alternativas"]}', '"Em forma", "Preços e alternativas", "Lesões e castigos"]}')
rep('"syn": ["preços", "subidas", "descidas", "alternativas", "substitutos"]}',
    '"syn": ["preços", "subidas", "descidas", "alternativas", "substitutos"]}, {"v": "mercado", "s": "lesoes", "a": "Jogadores", "n": "Lesões e castigos", '
    '"syn": ["lesão", "lesões", "lesionados", "regresso", "quando volta", "data de regresso", "amarelos", "cartões", "cartão amarelo", "vermelho", "castigo", "castigos", "suspensão", "suspensos", "disponibilidade"]}')
rep("mercado: ['pesquisa']};", "mercado: ['pesquisa', 'lesoes']};")

# ---------------------------------------------------------------- 6. tutorial e versão
rep("  var APP_VERSION = 'V57';", "  var APP_VERSION = 'V58';")
rep("      {id: 'precos', ix: 'mercado/precos', since: 'V24',",
    "      {id: 'lesoes58', ix: 'mercado/lesoes', since: 'V58', sel: '#av58-list, #av58-who', t: 'Lesões e castigos', d: () => `Quando volta cada lesionado (ex.: ${tutSafe(() => { const p = FULL_POOL.filter(q => q.status === 'i' && av58(q) && av58(q).ret).sort((a, b) => (b.own || 0) - (a.own || 0))[0]; return shortName(p.name) + ': ' + av58RetTxt(p); }, 'Regresso provável: J13 (55%)')}) e quem está à beira de um castigo por amarelos. Filtra por \"Só o meu plantel\" ou \"Só os rivais\". São probabilidades, não certezas — e os pontos esperados de toda a app já contam com elas.`},\n"
    "      {id: 'precos', ix: 'mercado/precos', since: 'V24',")
rep("      {id: 'dados57', ix: 'semana/registo', since: 'V57',",
    "      {id: 'avisos58', ix: 'semana/resumo', since: 'V58', opt: true, sel: '#alerts', t: 'Regressos e castigos nos avisos', d: () => 'Os avisos mostram a jornada provável de regresso dos teus lesionados (e de quem tens no plano), se compensa aguentar com o banco ou vender, e quem está a 1 amarelo de um jogo de castigo. Na ficha de cada jogador há a mesma informação: \"Regresso provável\" e \"Amarelos\".'},\n"
    "      {id: 'dados57', ix: 'semana/registo', since: 'V57',")

# ---------------------------------------------------------------- 7. estilos (claro e escuro pelos tokens)
rep("  .pc-tag.doubt { background: var(--warn-weak); color: var(--warn); }\n",
    "  .pc-tag.doubt { background: var(--warn-weak); color: var(--warn); }\n"
    "  .pc-tag.ret { background: var(--good-weak); color: var(--good); }\n"
    "  .pc-tag.yc { background: #F7E27A; color: #4A3A00; }\n"
    "  .av58-strip { display: inline-flex; gap: 3px; flex-wrap: wrap; }\n"
    "  .av58-c { display: inline-flex; flex-direction: column; align-items: center; min-width: 34px; padding: 2px 3px; border-radius: 5px; font-size: 11px; line-height: 1.25; font-variant-numeric: tabular-nums; }\n"
    "  .av58-c b { font-size: 9.5px; font-weight: 700; opacity: .8; }\n"
    "  .av58-c.hi { background: var(--good-weak); color: var(--good); }\n"
    "  .av58-c.mid { background: var(--warn-weak); color: var(--warn); }\n"
    "  .av58-c.lo { background: var(--bad-weak); color: var(--bad); }\n"
    "  .av58-ficha { margin: 10px 0 4px; }\n"
    "  .av58-ficha h3 { margin-bottom: 4px; }\n"
    "  .av58-row { margin: 4px 0 8px; }\n"
    "  .av58-row .note { margin: 2px 0 4px; }\n"
    "  .av58-verdict { margin: 4px 0 8px; padding: 6px 8px; border-radius: 6px; font-size: 13px; background: var(--surface-2); }\n"
    "  .av58-verdict.sell { background: var(--bad-weak); }\n"
    "  .av58-verdict.hold { background: var(--good-weak); }\n"
    "  .av58-filters { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 6px; }\n"
    "  .av58-note ul { margin: 4px 0; padding-left: 18px; }\n")

H.write_text(s, encoding='utf-8', newline='\n')
print('V58 aplicada ao index.html')
