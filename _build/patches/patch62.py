"""V62 (11 nov 2026): Laboratório — Jogadores › Laboratório.
- Experiências (equipas que não mexem na equipa verdadeira): criar de raiz, do plantel, da Equipa ideal, da Equipa
  simulada ou do plantel de um rival; trocar, trancar, completar com os melhores, orçamento (valor de mercado ou
  orçamento real), capitão e banco automáticos ou à mão; regras da FPL sempre, com o motivo quando algo não cabe.
- O que cada uma mostra: pontos esperados (próxima e próximas 5), 10+ do capitão, diferença para o plantel real,
  probabilidade de ganhar o H2H, diferenciais e ameaças (EO), lesões e castigos, custo; "lado a lado" até 4 + real.
- Equipas fantasma: pontos reais jornada a jornada (history/points-J<n>.json), congelada / conselho da app / plano meu.
- Comandos em linguagem simples (sem IA), Exportar/Importar, e lab/experiments.json (experiências do Claude Code).
- "Guardar como experiência" na Equipa ideal, na Equipa simulada e no Comparar equipas.
O código e os estilos estão em _build/patches/lab62.js e lab62.css (cópias de partida; se mudares o Laboratório, muda-o
no index.html). Uso (a partir da raiz, uma só vez): py -X utf8 _build/patches/patch62.py   (Linux: python3)"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
H = HERE.parents[1] / 'index.html'
s = H.read_text(encoding='utf-8')
assert "data-sub=\"lab\"" not in s, 'o V62 já está aplicado'


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)


# 1. estilos
rep('</style>', (HERE / 'lab62.css').read_text(encoding='utf-8') + '</style>')

# 2. separador e a sua vista (a seguir à Equipa simulada)
rep('        <button class="subtab" type="button" data-sub="simulada">Equipa simulada</button>\n',
    '        <button class="subtab" type="button" data-sub="simulada">Equipa simulada</button>\n'
    '        <button class="subtab" type="button" data-sub="lab">Laboratório</button>\n')
rep('      <div class="subview" data-sub="forma" hidden>\n',
    '      <div class="subview" data-sub="lab" hidden>\n'
    '        <div class="stack" id="lab-root">\n'
    '          <section class="card" id="lab-cmd"></section>\n'
    '          <section class="card" id="lab-list"></section>\n'
    '          <div class="sec-div">A equipa</div>\n'
    '          <section class="card" id="lab-edit"></section>\n'
    '          <section class="card" id="lab-pick" hidden></section>\n'
    '          <div class="sec-div">O que mostra</div>\n'
    '          <div class="stack" id="lab-eval"><section class="card"><p class="note">A calcular…</p></section></div>\n'
    '          <div class="sec-div">Lado a lado</div>\n'
    '          <section class="card" id="lab-cmp"></section>\n'
    '          <div class="sec-div">Equipas fantasma</div>\n'
    '          <section class="card" id="lab-ghost"></section>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div class="subview" data-sub="forma" hidden>\n')

# 3. índice das áreas e Procurar
rep('"Equipa simulada", "Em forma"', '"Equipa simulada", "Laboratório", "Em forma"')
rep('{"v": "mercado", "s": "forma", "a": "Jogadores", "n": "Em forma"',
    '{"v": "mercado", "s": "lab", "a": "Jogadores", "n": "Laboratório", "syn": ["laboratório", "laboratorio", "lab", "experiência", "experiencia", "experiências", "experiencias", '
    '"testar equipa", "testar equipas", "testar", "experimentar", "e se", "fantasma", "equipa fantasma", "comandos", "exportar", "importar", "guardar como experiência"]}, '
    '{"v": "mercado", "s": "lab", "a": "Jogadores", "n": "Equipas fantasma", "h": "lab-ghost", "syn": ["fantasmas", "equipas fantasma", "seguir equipa", "pontos reais", "acumulado"]}, '
    '{"v": "mercado", "s": "forma", "a": "Jogadores", "n": "Em forma"')

# 4. o código do Laboratório (antes da navegação, depois de tudo o que ele usa)
NAV = '  // ===== Navegação: menu lateral (áreas) + sub-abas (temas dentro de cada área) =====\n'
rep(NAV, (HERE / 'lab62.js').read_text(encoding='utf-8').lstrip('\n') + NAV)

# 5. redesenhar quando muda o gestor ou chegam dados novos
rep("    try { if (typeof NW_READY !== 'undefined' && NW_READY) { lazyRender('semana/noticias', renderNews); nwLine(); } } catch (e) {}   // V61 (só depois do arranque)\n",
    "    try { if (typeof NW_READY !== 'undefined' && NW_READY) { lazyRender('semana/noticias', renderNews); nwLine(); } } catch (e) {}   // V61 (só depois do arranque)\n"
    "    try { if (typeof LAB_READY !== 'undefined' && LAB_READY) labReset(); } catch (e) {}   // V62\n")
rep("    try { dis59Refresh(); } catch (e) { console.error(e); }\n  }\n  async function loadLive() {",
    "    try { dis59Refresh(); } catch (e) { console.error(e); }\n"
    "    try { if (typeof LAB_READY !== 'undefined' && LAB_READY) labReset(); } catch (e) { console.error(e); }\n  }\n  async function loadLive() {")

# 6. "Guardar como experiência": Equipa ideal, Equipa simulada e Comparar equipas
rep('<button type="button" class="btn" id="idl-to-sim"${stale ? \' disabled\' : \'\'}>Copiar para a equipa simulada</button>',
    '<button type="button" class="btn" id="idl-to-sim"${stale ? \' disabled\' : \'\'}>Copiar para a equipa simulada</button>'
    '<button type="button" class="btn" id="idl-to-lab"${stale ? \' disabled\' : \'\'}>Guardar como experiência</button>')
rep("    const ts = el.querySelector('#idl-to-sim');\n",
    "    const tl = el.querySelector('#idl-to-lab');\n"
    "    if (tl && r) tl.addEventListener('click', () => { try { labSaveFrom('ideal'); } catch (e) { console.error(e); } });\n"
    "    const ts = el.querySelector('#idl-to-sim');\n")
rep('<button type="button" class="btn" id="fsim-copy">Copiar o meu plantel</button>',
    '<button type="button" class="btn" id="fsim-copy">Copiar o meu plantel</button><button type="button" class="btn" id="fsim-lab"${ps.length ? \'\' : \' disabled\'}>Guardar como experiência</button>')
rep("    root.querySelector('#fsim-clear').addEventListener('click',",
    "    root.querySelector('#fsim-lab').addEventListener('click', () => { try { labSaveFrom('simulada'); } catch (e) { console.error(e); } });\n"
    "    root.querySelector('#fsim-clear').addEventListener('click',")
rep("        ${h2hE ? `<button type=\"button\" data-q=\"${me}|${h2hE}\">vs o adversário H2H da J${GW_META.next} (${cmpName(h2hE)})</button>` : ''}\n      </div>`;",
    "        ${h2hE ? `<button type=\"button\" data-q=\"${me}|${h2hE}\">vs o adversário H2H da J${GW_META.next} (${cmpName(h2hE)})</button>` : ''}\n"
    "        <button type=\"button\" data-labsave=\"${CMP.a}\">Guardar como experiência: ${cmpName(CMP.a)}</button>${CMP.b !== CMP.a ? `<button type=\"button\" data-labsave=\"${CMP.b}\">Guardar como experiência: ${cmpName(CMP.b)}</button>` : ''}\n      </div>`;")
rep("    pick.querySelectorAll('[data-q]').forEach(b => b.addEventListener('click', () => { const [x, y] = b.dataset.q.split('|').map(Number); CMP.a = x; CMP.b = y; renderCompare(); }));",
    "    pick.querySelectorAll('[data-q]').forEach(b => b.addEventListener('click', () => { const [x, y] = b.dataset.q.split('|').map(Number); CMP.a = x; CMP.b = y; renderCompare(); }));\n"
    "    pick.querySelectorAll('[data-labsave]').forEach(b => b.addEventListener('click', () => { try { labSaveFrom('rival', +b.dataset.labsave); } catch (e) { console.error(e); } }));   // V62")

# 7. tutorial e versão
rep("      {id: 'forma', ix: 'mercado/forma', since: 'V23',",
    "      {id: 'lab62', ix: 'mercado/lab', since: 'V62', wait: 700, sel: '#lab-list', t: 'Laboratório', d: () => `Experimenta equipas sem mexer na tua equipa verdadeira. Cria uma de raiz, a partir do teu plantel, da Equipa ideal, da Equipa simulada ou do plantel de um rival (e há um botão \"Guardar como experiência\" na Equipa ideal e no Comparar equipas). Cada uma guarda os 15, o capitão, o vice, a ordem do banco, o orçamento e uma nota tua. Agora tens ${tutSafe(() => labList().length, 0)}. \"Exportar\" e \"Importar\" passam-nas para outro dispositivo com um código.`},\n"
    "      {id: 'labcmd62', ix: 'mercado/lab', since: 'V62', sel: '#lab-cmd', t: 'Comandos em linguagem simples', d: () => 'Escreve o que queres fazer: \"troca Saka por Cherki\", \"tranca Haaland e Groß\", \"orçamento 101\", \"capitão Haaland\", \"melhor equipa para a J' + tutSafe(() => HZ[1], 12) + '\", \"copia a equipa do Frederico\", \"compara com a minha\". Se a app não perceber, mostra exemplos do que sabe fazer.'},\n"
    "      {id: 'labeq62', ix: 'mercado/lab', since: 'V62', sel: '#lab-edit', t: 'Mexer depressa na equipa', d: () => 'Toca num jogador para o trocar, trancar, fazer capitão ou vice, ou mudar de lugar no onze e no banco. \"Completar com os melhores\" usa o otimizador da Equipa ideal e mantém os trancados. O orçamento pode ser o valor de mercado ou o teu orçamento real. As regras da FPL valem sempre (2-5-5-3, máximo 3 por clube, orçamento): quando algo não cabe, a app diz porquê.'},\n"
    "      {id: 'labeval62', ix: 'mercado/lab', since: 'V62', sel: '#lab-eval', t: 'O que cada experiência mostra', d: () => `Os pontos esperados da J${HZ[0]} e das próximas 5, a probabilidade de o capitão fazer 10 ou mais, a diferença para a tua equipa real, a probabilidade de ganhares ao teu próximo adversário do H2H (${tutSafe(() => GW_META.h2h[curMgr()].next, 'o adversário')}), os diferenciais e as ameaças na liga, as lesões e os castigos previstos e o custo.`},\n"
    "      {id: 'labcmp62', ix: 'mercado/lab', since: 'V62', sel: '#lab-cmp', t: 'Lado a lado', d: () => 'Marca \"comparar\" em até 4 experiências: aparecem lado a lado com a tua equipa real, a verde quem ganha cada linha e por quanto.'},\n"
    "      {id: 'labghost62', ix: 'mercado/lab', since: 'V62', sel: '#lab-ghost', t: 'Equipas fantasma', d: () => 'Liga \"Seguir a partir da J…\" e a app soma os pontos reais que essa equipa faria em cada jornada, com as regras da FPL (substituições automáticas, capitão e vice). Três modos: congelada, segue o conselho da app, ou segue um plano de trocas teu. O gráfico compara o acumulado com a tua equipa real.'},\n"
    "      {id: 'forma', ix: 'mercado/forma', since: 'V23',")
rep("  var APP_VERSION = 'V61';", "  var APP_VERSION = 'V62';")

H.write_text(s, encoding='utf-8', newline='\n')
print('V62 aplicado')
