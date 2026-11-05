"""V56 (5 nov 2026): rotina diária automática na app — linha "Última atualização automática" por baixo da faixa
verde e aviso "Mudou desde ontem: …" no Resumo (dados em const AUTO_UPDATE, escrita por _build/rotina.py marcar).
Uso (a partir da raiz): py -X utf8 _build/patches/patch56.py   (Linux: python3)"""
from pathlib import Path

H = Path(__file__).resolve().parents[2] / 'index.html'
s = H.read_text(encoding='utf-8')


def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:90], s.count(a))
    s = s.replace(a, b)


rep('<div class="live-banner" id="live-banner" role="status" hidden></div>',
    '<div class="live-banner" id="live-banner" role="status" hidden></div>\n<div class="auto-line" id="auto-line" hidden></div>')
rep('  .live-banner {', '  .auto-line { font-size: 12.5px; color: var(--muted); margin: -8px 0 14px 2px; }\n  .live-banner {')
JS = r'''
  // V56: rotina diária automática (claude.ai/code). AUTO_UPDATE = {date, tipo: 'completa' | 'ultima_hora', gw, changes: {bruno: [...], marco: [...]}}
  function autoUpdateLine() {
    const el = document.getElementById('auto-line'); if (!el) return;
    if (typeof AUTO_UPDATE === 'undefined' || !AUTO_UPDATE.date) { el.hidden = true; return; }
    const d = new Date(AUTO_UPDATE.date);
    const when = d.toLocaleString('pt-PT', {timeZone: 'Europe/Lisbon', weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'});
    el.textContent = `Última atualização automática: ${when} · ${AUTO_UPDATE.tipo === 'completa' ? 'completa' : 'última hora'}`;
    el.hidden = false;
  }
  function autoUpdateAlerts(add, mgr) {
    if (typeof AUTO_UPDATE === 'undefined' || !AUTO_UPDATE.changes) return;
    const age = (Date.now() - new Date(AUTO_UPDATE.date)) / 3600e3;
    if (age > 48 || AUTO_UPDATE.gw !== GW_META.next) return;   // só para a jornada que aí vem e durante 2 dias
    (AUTO_UPDATE.changes[mgr] || []).forEach(t => add(2, 'Mudou desde ontem', `Mudou desde ontem: ${t}`, {goto: 'semana', gotoSub: 'transferencias', isNew: true}));
  }
  try { autoUpdateLine(); } catch (e) { console.error(e); }
'''
rep("  // V53: conselhos da semana com números lidos dos dados; correm no fim do arranque (depois da calibração)\n",
    JS + "  // V53: conselhos da semana com números lidos dos dados; correm no fim do arranque (depois da calibração)\n")
rep("    try { dgwAlerts(add, squad); } catch (e) { console.error(e); }\n",
    "    try { dgwAlerts(add, squad); } catch (e) { console.error(e); }\n    try { autoUpdateAlerts(add, mgr); } catch (e) { console.error(e); }\n")
# tutorial: um passo novo e a versão
rep("      {id: 'faixa', ix: 'semana/resumo', since: 'V30', opt: true, sel: '#live-banner',",
    "      {id: 'rotina56', ix: 'semana/resumo', since: 'V56', opt: true, sel: '#auto-line', t: 'Atualização automática diária', d: () => 'Todos os dias às 9h uma rotina na nuvem vê se há trabalho: depois de cada jornada faz a atualização completa; na véspera do deadline revê lesões, onzes prováveis e preços. Esta linha diz quando foi a última e de que tipo; se a troca, o capitão ou a chip sugeridos mudarem, aparece um aviso \"Mudou desde ontem\" no Resumo.'},\n"
    "      {id: 'faixa', ix: 'semana/resumo', since: 'V30', opt: true, sel: '#live-banner',")
rep("  var APP_VERSION = 'V54';", "  var APP_VERSION = 'V56';")
H.write_text(s, encoding='utf-8', newline='\n')
print('V56 aplicado')
