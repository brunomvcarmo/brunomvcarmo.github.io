  // ===================================================================
  // V43 (15 out 2026) — Cartão de jogador: um só componente para todas as listas de jogadores.
  // playerCard(p, opts) devolve o HTML; opts:
  //   full     versão completa (camisola grande, fita com jornadas, forma com números, notícia, posse na liga)
  //   gi       jornada do horizonte para os pontos esperados (0 = próxima)
  //   cap/vice etiqueta C/V        mine  "no plantel" (por defeito: se está no plantel do gestor ativo)
  //   note     linha de texto por baixo do clube (HTML)    extra  coluna à direita (HTML, ex.: ganho de uma troca)
  //   tags     etiquetas extra (HTML)
  // Tocar no cartão abre a ficha do jogador (o clique em [data-pid] já está tratado na app).
  // ===================================================================
  const PC_STATUS = {d: ['doubt', 'dúvida'], i: ['inj', 'lesionado'], s: ['inj', 'suspenso'], u: ['inj', 'indisponível'], n: ['inj', 'indisponível']};
  function pcEO(id) { try { return leagueEO(id); } catch (e) { return null; } }   // LEAGUE_SQUADS pode ainda não existir
  function pcMine(id) { try { return mineIds().has(id); } catch (e) { return false; } }
  function pcFixCell(p, k, full) {
    const gw = HZ[k], fx = fixturesFor(p.team, gw);
    if (!fx.length) return `<span class="pc-fxc blank" title="J${gw}: sem jogo">${full ? `<i>J${gw}</i>` : ''}—</span>`;
    const dx = fx.reduce((s, f) => s + f.d, 0) / fx.length, d = Math.max(1, Math.min(5, Math.round(dx)));
    const opp = fx.map(f => SHORT(f.opp)).join('+'), ha = fx.map(f => f.home ? 'C' : 'F').join('+');
    const title = `J${gw}: ${fx.map(f => `${TEAMS[f.opp]} (${f.home ? 'casa' : 'fora'})`).join(' e ')}, dificuldade ${dx.toFixed(1)}`;
    return `<span class="pc-fxc" style="background:${SEQ[d]};color:${SEQ_TEXT[d]}" title="${title}">${full ? `<i>J${gw}</i>` : ''}${fx.length > 1 ? `${fx.length}×` : opp}<small>${fx.length > 1 ? opp : ha}</small></span>`;
  }
  function pcTags(p, o, eo) {
    const T = [];
    if (o.cap) T.push('<span class="pc-tag cap" title="Capitão">C</span>');
    if (o.vice) T.push('<span class="pc-tag vice" title="Vice-capitão">V</span>');
    const st = PC_STATUS[p.status];
    if (st) T.push(`<span class="pc-tag ${st[0]}" title="${(p.news || '').replace(/"/g, '&quot;')}">${st[1]}${p.status === 'd' && p.chance != null ? ' ' + p.chance + '%' : ''}</span>`);
    if (o.mine) T.push('<span class="pc-tag mine">no plantel</span>');
    if (eo && eo.eo < 0.15 && epAt(p, o.gi) >= 2) T.push(`<span class="pc-tag diff" title="Só ${Math.round(eo.eo * 100)}% da liga o tem a jogar (titular + capitão)">diferencial</span>`);
    if (o.tags) T.push(o.tags);
    return T.join('');
  }
  function playerCard(p, opts) {
    if (!p) return '';
    const o = Object.assign({gi: 0}, opts || {});
    if (o.mine == null) o.mine = pcMine(p.id);
    const gi = o.gi, ep = epAt(p, gi), eo = pcEO(p.id), full = !!o.full;
    const out = ['i', 's', 'u', 'n'].includes(p.status) || ep < 0.5;
    const pts = (p.ptsGw || []).slice(-6);
    const priceCh = p.cch ? ` <span class="${p.cch > 0 ? 'up' : 'down'}" title="Variação nesta jornada">${p.cch > 0 ? '+' : '−'}${Math.abs(p.cch / 10).toFixed(1)}</span>` : '';
    const meta = `<span>${full ? TEAMS[p.team] : SHORT(p.team)}</span><span>·</span><span>${POS_SHORT[p.cls]}</span><span>·</span><span class="pc-price">£${p.price.toFixed(1)}M</span>${priceCh}${priceTag(p)}`;
    const tags = pcTags(p, o, eo);
    const p10 = pAtLeast(p, gi, 10);
    const epBlock = `<div class="pc-ep"><div class="lbl">Pts esp. J${HZ[gi]}</div><div class="v">${f1(ep)}</div><div class="h" title="Probabilidade de 10 ou mais pontos na J${HZ[gi]}">10+ <b>${pctR(p10)}</b></div></div>`;
    const fx = `<div class="pc-fx">${HZ.map((_, k) => pcFixCell(p, k, full)).join('')}</div>`;
    const label = `${p.name}, ${TEAMS[p.team]}, ${POS_SHORT[p.cls]}, £${p.price.toFixed(1)}M, ${f1(ep)} pontos esperados na J${HZ[gi]}${o.cap ? ', capitão' : o.vice ? ', vice-capitão' : ''}${PC_STATUS[p.status] ? ', ' + PC_STATUS[p.status][1] : ''}`;
    const cls = `pcard${full ? ' full' : ''}${o.mine ? ' is-mine' : ''}${out ? ' is-out' : ''}`;
    if (!full) {
      return `<article class="${cls}" data-pid="${p.id}" tabindex="0" role="button" aria-label="${label}"><div class="pc-in${o.extra ? ' has-extra' : ''}">
        <div class="pc-shirt">${shirtSvg(p.team, p.cls)}</div>
        <div class="pc-id"><div class="pc-name"><span class="pc-nm">${shortName(p.name)}</span>${tags}</div><div class="pc-meta">${meta}</div>${o.note ? `<div class="pc-note">${o.note}</div>` : ''}</div>
        ${fx}
        <div class="pc-form"><span class="lbl">Forma</span>${sparkline(pts, {w: 60, h: 20})}</div>
        ${epBlock}${o.extra ? `<div class="pc-extra">${o.extra}</div>` : ''}
      </div></article>`;
    }
    const [lo, hi] = range80(p, gi), sum = HZ.reduce((s, _, k) => s + epAt(p, k), 0);
    const first = GW_META.last - pts.length + 1;
    return `<article class="${cls}" aria-label="${label}"><div class="pc-in">
        <div class="pc-shirt">${shirtSvg(p.team, p.cls)}</div>
        <div class="pc-id"><div class="pc-name"><span class="pc-nm" data-pid="${p.id}">${p.name}</span></div><div class="pc-meta">${meta}</div>${o.note ? `<div class="pc-note">${o.note}</div>` : ''}</div>
        <div class="pc-ep"><div class="lbl">Pts esp. J${HZ[gi]}</div><div class="v">${f1(ep)}</div><div class="h">10+ pts <b>${pctR(p10)}</b></div><div class="h">J${HZ[0]}-J${HZ[HZ.length - 1]}: ${f1(sum)}</div></div>
        <div class="pc-tags">${tags}</div>
        <div class="pc-fxw"><div class="pc-sec">Próximos ${HZ.length} jogos</div>${fx}</div>
        <div class="pc-form"><div class="pc-sec">Forma · pontos J${first}-J${GW_META.last}</div><div class="row">${sparkline(pts, {w: 168, h: 38})}<span class="pts">${pts.join(' · ')}</span></div></div>
        <div class="pc-info">
          ${PC_STATUS[p.status] ? `<div class="news${p.status === 'd' ? ' d' : ''}">${PC_STATUS[p.status][1]}${p.chance != null ? ` (${p.chance}% de jogar)` : ''}${p.news ? ` — ${p.news}` : ''}</div>` : ''}
          <div>Quando joga, 8 em cada 10 vezes faz entre <b>${lo}</b> e <b>${hi}</b> pontos · ≤2 pts ${pctR(pAtMost(p, gi, 2))}</div>
          <div>Posse: ${f1(p.own || 0)}% na FPL${eo ? ` · ${Math.round(eo.own * 100)}% na liga (${Math.round(eo.start * 100)}% titular, ${Math.round(eo.cap * 100)}% capitão) — ${eoReading(p.id)}` : ''}</div>
          ${o.extra ? `<div>${o.extra}</div>` : ''}
          <div><button type="button" class="btn ghost small" data-pid="${p.id}">Abrir a ficha completa</button></div>
        </div>
      </div></article>`;
  }
  const playerCards = (list, optsOf) => `<div class="pc-list">${list.filter(Boolean).map((p, i) => playerCard(p, typeof optsOf === 'function' ? optsOf(p, i) : optsOf)).join('')}</div>`;
  // Enter/espaço num cartão compacto abre a ficha (como o clique)
  document.addEventListener('keydown', e => {
    if ((e.key === 'Enter' || e.key === ' ') && e.target.classList && e.target.classList.contains('pcard') && !e.target.classList.contains('full')) { e.preventDefault(); e.target.click(); }
  });
