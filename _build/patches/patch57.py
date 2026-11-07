"""V57 (7 nov 2026): plantéis sempre iguais aos da FPL.
- live.json: as transferências que a API já lista para uma jornada a seguir à dos picks ("pendentes") são aplicadas
  por cima dos picks, para os 20 (Bruno e Marco incluídos), com a etiqueta "Transferência feita para a J__"
  e o capitão dessa jornada como "só se sabe depois do deadline". (A API pública só as mostra depois do deadline.)
- "Registar o que fiz": se os dados oficiais já têm a troca, o registo deixa de contar (já era assim) e diz porquê.
- Resumo: aviso se os dados oficiais (live.json) tiverem mais de 48 h.
Uso (a partir da raiz): py -X utf8 _build/patches/patch57.py   (Linux: python3)"""
from pathlib import Path

H = Path(__file__).resolve().parents[2] / 'index.html'
s = H.read_text(encoding='utf-8')


def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:90], s.count(a))
    s = s.replace(a, b)


# 1. live.json → LEAGUE_SQUADS com as transferências pendentes por cima dos picks
rep("      if (x.picks && x.picks.starters) { L.s = x.picks.starters; L.b = x.picks.bench; const c = FULL_POOL_BY_ID[x.picks.captain]; if (c) L.c = c.name; }\n",
    "      if (x.picks && x.picks.starters) { L.s = x.picks.starters.slice(); L.b = x.picks.bench.slice(); L.pgw = x.picks.event; const c = FULL_POOL_BY_ID[x.picks.captain]; if (c) L.c = c.name; }\n"
    "      // V57: transferências já feitas para uma jornada a seguir à dos picks (a API pública só as mostra depois do deadline)\n"
    "      L.pend = null;\n"
    "      const pend = x.picks && x.picks.starters ? (x.transfers || []).filter(t => t.event > x.picks.event).sort((a, b) => String(a.time || '').localeCompare(String(b.time || ''))) : [];\n"
    "      if (pend.length) {\n"
    "        pend.forEach(t => [L.s, L.b].forEach(arr => { const i = arr.indexOf(t.out); if (i >= 0 && !L.s.includes(t.in) && !L.b.includes(t.in)) arr[i] = t.in; }));\n"
    "        L.bank = +(L.bank + pend.reduce((a, t) => a + (t.out_cost - t.in_cost) / 10, 0)).toFixed(1);\n"
    "        L.pend = {gw: Math.max(...pend.map(t => t.event)), list: pend.map(t => ({out: t.out, in: t.in}))};\n"
    "      }\n")
# Bruno e Marco: plantel base = picks oficiais + transferências pendentes
rep("""      const x = d.entries[CMP_ENTRY[mgr]]; if (!x || !x.picks || !(x.picks.event >= GW_META.next)) return;
      const ids = [...x.picks.starters, ...x.picks.bench];""",
    """      const x = d.entries[CMP_ENTRY[mgr]], L = LEAGUE_SQUADS[CMP_ENTRY[mgr]];
      BASE_STATE[mgr].pend = L && L.pend ? L.pend : null;
      if (!x || !x.picks || !L || !(x.picks.event >= GW_META.next || L.pend)) return;
      const ids = [...L.s, ...L.b];""")
rep("      const h = (x.history || []).slice(-1)[0]; if (h) BASE_STATE[mgr].bank = h.bank / 10;\n    });\n    applyLog();",
    "      BASE_STATE[mgr].bank = L.bank;\n"
    "      if (L.pend && L.pend.gw === GW_META.next) BASE_STATE[mgr].ft = Math.max(0, BASE_STATE[mgr].ft - L.pend.list.length);\n"
    "    });\n    applyLog();")
rep("    try { fillRealsFromLive(); renderPredictions('bruno'); renderPredictions('marco'); renderModelEval(); renderAlerts(); renderTodo(); } catch (e) { console.error(e); }\n  }\n",
    "    try { fillRealsFromLive(); renderPredictions('bruno'); renderPredictions('marco'); renderModelEval(); renderAlerts(); renderTodo(); } catch (e) { console.error(e); }\n"
    "    try { v57PendNote(); } catch (e) { console.error(e); }\n  }\n")

# 2. cartão do rival: jornada certa do capitão e transferência pendente
rep("            <span>C na J${GW_META.squadsGw || GW_META.last}: <b>${shortName(d.L.c)}</b> · banco £${d.L.bank.toFixed(1)}M</span></div>",
    "            <span>C na J${d.L.pgw || GW_META.squadsGw || GW_META.last}: <b>${shortName(d.L.c)}</b> · banco £${d.L.bank.toFixed(1)}M</span>"
    "${d.L.pend ? `<span class=\"pend57\"><b>Transferência feita para a J${d.L.pend.gw}:</b> ${d.L.pend.list.map(t => `${shortName((FULL_POOL_BY_ID[t.out] || {name: '?'}).name)} → ${shortName((FULL_POOL_BY_ID[t.in] || {name: '?'}).name)}`).join(', ')} · capitão da J${d.L.pend.gw}: só se sabe depois do deadline</span>` : ''}</div>")
rep("  .riv-meta {", "  .pend57 { color: var(--ink); background: var(--accent-soft, rgba(0,0,0,.05)); border-radius: 6px; padding: 3px 6px; }\n  .riv-meta {")

# 3. Esta semana: nota com a transferência oficial já feita (Bruno/Marco) + explicação no Registar
JS = r'''
  // V57: transferência oficial já feita para a jornada seguinte (live.json) — nota em Esta semana › Transferências e Registar
  function v57PendNote() {
    const p = (BASE_STATE[curMgr()] || {}).pend;
    ['transferencias', 'registo'].forEach(sub => {
      const sv = document.querySelector(`.view[data-view="semana"] > .subview[data-sub="${sub}"]`); if (!sv) return;
      let n = sv.querySelector('.v57-note');
      if (!p) { if (n) n.remove(); return; }
      if (!n) { n = document.createElement('div'); n.className = 'callout info v57-note'; sv.insertBefore(n, sv.firstChild); }
      n.innerHTML = `<span class="icon">i</span><div class="body"><p><b>Transferência feita para a J${p.gw}</b> (dados oficiais da FPL): ${p.list.map(t => `${(FULL_POOL_BY_ID[t.out] || {name: '?'}).name} → ${(FULL_POOL_BY_ID[t.in] || {name: '?'}).name}`).join(', ')}. A app já usa o plantel com esta troca. O capitão da J${p.gw} só se sabe depois do deadline.</p></div>`;
    });
  }
  // V57: aviso no Resumo quando os dados oficiais (live.json) têm mais de 48 h
  function v57StaleAlert(add) {
    const d = window.__LIVE; if (!d || !d.generated) return;
    const h = (Date.now() - new Date(d.generated)) / 3600e3; if (!(h > 48)) return;
    const when = new Date(d.generated).toLocaleString('pt-PT', {timeZone: 'Europe/Lisbon', weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'});
    add(h > 96 ? 3 : 2, 'Dados', `Os dados oficiais da FPL têm ${h >= 72 ? Math.floor(h / 24) + ' dias' : Math.floor(h) + ' h'} (última atualização: ${when}). Plantéis, capitães, preços e lesões podem não estar iguais ao site da FPL. A atualização automática corre sozinha na véspera e no dia de cada deadline; se este aviso não desaparecer, pede ao Claude "atualiza os dados" (ou, no GitHub: Actions › Atualizar dados FPL › Run workflow).`, {});
  }
'''
rep("  // V53: conselhos da semana com números lidos dos dados; correm no fim do arranque (depois da calibração)\n",
    JS + "  // V53: conselhos da semana com números lidos dos dados; correm no fim do arranque (depois da calibração)\n")
rep("    try { autoUpdateAlerts(add, mgr); } catch (e) { console.error(e); }\n",
    "    try { autoUpdateAlerts(add, mgr); } catch (e) { console.error(e); }\n    try { v57StaleAlert(add); } catch (e) { console.error(e); }\n")
rep("     () => { document.getElementById('marco-chips-summary').textContent = v52ChipTxt('marco'); }].forEach(",
    "     () => { document.getElementById('marco-chips-summary').textContent = v52ChipTxt('marco'); }, () => v57PendNote()].forEach(")
rep("<div class=\"card-sub\">Fizeste a troca no site da FPL? Regista-a aqui e toda a app passa a usar o plantel novo (campo, pontos esperados, simulador, comparações).</div>",
    "<div class=\"card-sub\">Fizeste a troca no site da FPL? Regista-a aqui e toda a app passa a usar o plantel novo (campo, pontos esperados, simulador, comparações). A FPL só mostra as transferências da jornada seguinte depois do deadline: até lá, só a app sabe delas por este registo. Quando os dados oficiais as trouxerem, o registo deixa de contar sozinho (nunca conta duas vezes).</div>")
rep("'<span class=\"status-chip alt\">já no plantel base</span>'", "'<span class=\"status-chip alt\">já nos dados oficiais</span>'")
rep("<p class=\"note\">\"Já no plantel base\" quer dizer que a atualização de dados seguinte já trouxe esta troca da API — podes anulá-la sem mudar nada.</p>",
    "<p class=\"note\">\"Já nos dados oficiais\" quer dizer que os dados da FPL já trazem esta troca — o registo deixou de contar (não conta duas vezes) e podes anulá-lo sem mudar nada.</p>")

# 4. tutorial e versão
rep("      {id: 'rotina56', ix: 'semana/resumo',",
    "      {id: 'dados57', ix: 'semana/registo', since: 'V57', opt: true, sel: '#log-root', t: 'Plantéis iguais aos da FPL', d: () => 'Os plantéis (o teu, o do Marco e os dos rivais) vêm dos dados oficiais da FPL, que se atualizam sozinhos na véspera e no dia de cada deadline. A FPL só mostra as transferências da jornada seguinte depois do deadline: até lá, regista aqui o que fizeste. Quando os dados oficiais trazem a troca, aparece \"Transferência feita para a J__\" e o registo deixa de contar (nunca conta duas vezes). Se os dados tiverem mais de 48 h, o Resumo avisa.'},\n"
    "      {id: 'rotina56', ix: 'semana/resumo',")
rep("  var APP_VERSION = 'V56';", "  var APP_VERSION = 'V57';")
H.write_text(s, encoding='utf-8', newline='\n')
print('V57 aplicado')
