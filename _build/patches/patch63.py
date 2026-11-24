"""V63 (24 nov 2026): Guia do Laboratório — um tutorial próprio, passo a passo, que faz as coisas a sério numa
experiência de exemplo («Exemplo do guia», copiada do plantel): trocar com um comando, ver uma troca recusada e porquê,
trancar, ver os números, comparar lado a lado e seguir como equipa fantasma. No fim pergunta se o exemplo fica.
- TUT_CH ganha o capítulo 'labguia' (passos com labTut: true, que só aparecem no modo 'lab': tutStart('lab')).
- tutShow corre o st.pre() de cada passo (uma vez por guia); tutEnd apaga o exemplo, a não ser que se escolha «Guardar».
- Entradas: botão «Guia passo a passo» no topo do Laboratório, botão nas boas-vindas do tutorial, Procurar
  («guia do laboratório») e um passo novo no tutorial geral (Jogadores) que aponta para o botão.
- Nada disto mexe na equipa verdadeira: o Laboratório nunca escreve no SQUAD_STATE (sexta lição).
Uso (a partir da raiz): py -X utf8 _build/patches/patch63.py   (Linux: python3)"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
H = ROOT / 'index.html'
LABJS = ROOT / '_build' / 'patches' / 'lab62.js'
s = H.read_text(encoding='utf-8')
lj = LABJS.read_text(encoding='utf-8')


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)


def rep2(a, b):
    """No index.html e na cópia de partida do Laboratório (lab62.js)."""
    global s, lj
    rep(a, b)
    assert lj.count(a) == 1, ('lab62.js', a[:90], lj.count(a))
    lj = lj.replace(a, b)


CSS = r'''
  /* ===================== V63: Guia do Laboratório ===================== */
  .lab-guide { flex: none; white-space: nowrap; }
  .tut-lab { display: inline-flex; flex-wrap: wrap; gap: 6px; margin: 8px 0 4px; }
  .tut-lab .btn { min-height: 32px; }
'''
rep('</style>', CSS + '</style>')

# 1. botão no topo do Laboratório e o clique
rep2("      <div class=\"card-head\"><div><h2>Laboratório</h2><div class=\"card-sub\">Experimenta equipas sem mexer na tua equipa verdadeira e vê, jornada a jornada, se as ideias resultam. ${curMgr() === 'marco' ? 'Xarola Team' : 'Brunorussia FC'}.</div></div></div>",
     "      <div class=\"card-head\"><div><h2>Laboratório</h2><div class=\"card-sub\">Experimenta equipas sem mexer na tua equipa verdadeira e vê, jornada a jornada, se as ideias resultam. ${curMgr() === 'marco' ? 'Xarola Team' : 'Brunorussia FC'}.</div></div><button type=\"button\" class=\"btn small lab-guide\" id=\"lab-guide-btn\" data-lab=\"guia\">Guia passo a passo</button></div>")
rep2("    const a = b.dataset.lab, id = +b.dataset.id || 0, S = labS(), U = LAB.ui; let x = labCur();\n",
     "    const a = b.dataset.lab, id = +b.dataset.id || 0, S = labS(), U = LAB.ui; let x = labCur();\n"
     "    if (a === 'guia') { if (typeof tutStart === 'function') tutStart('lab'); return; }   // V63: Guia do Laboratório\n")

# 2. capítulo do guia (só no modo 'lab') e um passo no tutorial geral que aponta para o botão
STEPS = r'''    {id: 'labguia', t: 'Guia do Laboratório', steps: [
      {id: 'lg-o-que', labTut: true, ix: 'mercado/lab', since: 'V63', wait: 450, sel: '#lab-cmd', pre: () => { labTutDemo(); }, t: 'O Laboratório',
        d: () => `Aqui experimentas equipas <b>sem mexer na tua equipa verdadeira</b>: nada do que fazes no Laboratório conta como transferência nem muda o plantel da app. Para aprenderes, criei uma experiência de exemplo, «${nwEsc(labTutName())}», a partir do teu plantel. Nos próximos passos faço coisas a sério nela e, no fim, decides se fica ou se a apago.`},
      {id: 'lg-lista', labTut: true, ix: 'mercado/lab', since: 'V63', sel: '#lab-list', pre: () => { labTutDemo(); }, t: 'As tuas experiências',
        d: () => 'Cada experiência mostra o nome, a jornada em que foi criada, o orçamento, o capitão e o vice, o onze, a ordem do banco e a tua nota. Para criar outra, escolhe em «Nova experiência» de onde parte — de raiz, do teu plantel, da Equipa ideal, da Equipa simulada ou do plantel de um rival — e carrega em «Criar». Também há «Guardar como experiência» na Equipa ideal e no Comparar equipas. Toca numa experiência para a abrir.'},
      {id: 'lg-equipa', labTut: true, ix: 'mercado/lab', since: 'V63', sel: '#lab-edit', pre: () => { labTutDemo(); }, t: 'Mexer na equipa à mão',
        d: () => 'O campo mostra a experiência aberta. <b>Toca num jogador</b> e aparecem os botões: trocar (abre a pesquisa, com filtros de posição, clube, preço e «só os que cabem»), trancar 🔒, capitão, vice, mudar de lugar (onze ↔ banco), tirar e ficha. Em cima escolhes o <b>orçamento</b> (valor de mercado, o teu orçamento real ou um número) e se o capitão e o banco são <b>automáticos</b> (pela simulação das substituições) ou <b>à mão</b>. Também lhe podes mudar o nome e escrever uma nota.'},
      {id: 'lg-cmd', labTut: true, ix: 'mercado/lab', since: 'V63', sel: '#lab-cmd', pre: async () => { labTutDemo(); await labTutCmd('troca', labTutTrade()); }, t: 'Os comandos',
        d: () => { const r = labTutOut('troca'); return `Também podes escrever o que queres. Escrevi por ti <b>«${nwEsc(r.frase)}»</b> e carreguei em «Fazer»: ${r.ok ? 'a resposta, a verde, diz o que mudou, quanto custa e quanto sobra.' : 'a app não fez a troca e a resposta diz porquê.'}${r.sug ? ' É a troca que a app te sugere para esta jornada — mas aqui é só uma experiência: no site não mudou nada.' : ''} Os exemplos por baixo da caixa escrevem-se sozinhos se lhes tocares; «ajuda» mostra tudo o que a app percebe.`; }},
      {id: 'lg-regras', labTut: true, ix: 'mercado/lab', since: 'V63', sel: '#lab-cmd', pre: async () => { labTutDemo(); await labTutCmd('regra', labTutBad()); }, t: 'As regras da FPL',
        d: () => { const r = labTutOut('regra'), why = (r.txt || '').replace(/^Não troquei [^:]*:\s*/, '').replace(/\.$/, ''); return `Agora tentei <b>«${nwEsc(r.frase)}»</b>, que não pode ser${r.ok ? '' : `: a resposta, a vermelho, diz porquê («${nwEsc(why)}») e a equipa ficou como estava`}. As regras valem sempre: 2 guarda-redes, 5 defesas, 5 médios e 3 avançados; no máximo 3 do mesmo clube; e tudo dentro do orçamento. Se uma experiência sair das regras, aparece um aviso amarelo com o motivo.`; }},
      {id: 'lg-tranca', labTut: true, ix: 'mercado/lab', since: 'V63', sel: '#lab-edit', pre: async () => { labTutDemo(); await labTutCmd('tranca', `tranca ${labTutTop()}`); }, t: 'Trancar e completar com os melhores',
        d: () => `Escrevi «${nwEsc(labTutOut('tranca').frase)}»: o cadeado 🔒 marca quem fica de certeza. «<b>Completar com os melhores</b>» usa o otimizador da Equipa ideal para escolher o resto dentro do orçamento, sem tocar nos trancados. É a forma rápida de testar ideias: escreve, por exemplo, <b>«cria uma equipa com 3 do Arsenal e o Haaland»</b> e a app tranca-os e completa a equipa sozinha. Aqui não carreguei em «Completar» para não mudar o exemplo todo.`},
      {id: 'lg-mostra', labTut: true, ix: 'mercado/lab', since: 'V63', wait: 500, sel: '#lab-eval', pre: () => { labTutDemo(); labDraw(); LABTUT.rep = labReport(LABTUT.id); }, t: 'O que cada experiência mostra',
        d: () => labTutEvalTxt()},
      {id: 'lg-lado', labTut: true, ix: 'mercado/lab', since: 'V63', wait: 500, sel: '#lab-cmp', pre: () => { labTutDemo(); const S = labS(); if (!LABTUT.prevCmp) LABTUT.prevCmp = S.cmp.slice(); labCmpAdd(LABTUT.id); labSave(); labDraw(); }, t: 'Lado a lado',
        d: () => `Marquei «comparar» no exemplo: fica ao lado da tua equipa real, linha a linha (pontos esperados da J${HZ[0]} e das próximas 5, capitão, H2H, diferenciais, lesões, custo), a verde quem ganha cada linha e por quanto. Dá para comparar até 4 experiências de cada vez. Também podes escrever «compara com a minha» ou «compara com o Frederico».`},
      {id: 'lg-fantasma', labTut: true, ix: 'mercado/lab', since: 'V63', wait: 500, sel: '#lab-ghost', pre: async () => { labTutDemo(); await labTutCmd('segue', `segue a partir da J${labTutFrom()}`); LABTUT.rep = labReport(LABTUT.id); }, t: 'Equipas fantasma',
        d: () => labTutGhostTxt()},
      {id: 'lg-guardar', labTut: true, ix: 'mercado/lab', since: 'V63', sel: '#lab-list', pre: () => { labTutDemo(); }, t: 'Guardar e levar para outro dispositivo',
        d: () => 'As tuas experiências ficam guardadas <b>neste browser</b>, separadas para o Bruno e para o Marco. Para as levares para o telemóvel: «<b>Exportar</b>» dá um código; copia-o e, no outro dispositivo, cola-o em «<b>Importar</b>». O Claude Code também cria experiências (pede, por exemplo: «cria no Laboratório uma equipa com 3 do Arsenal e o Haaland e diz-me como fica contra a do Frederico»): essas aparecem em todos os dispositivos, marcadas «Claude Code», e copias-as para as tuas para mexer nelas.'},
      {id: 'lg-fim', labTut: true, ix: 'mercado/lab', since: 'V63', sel: null, t: 'Pronto!',
        d: () => labTutEndTxt()},
    ]},
'''
i = s.index('const TUT_CH = ['); j = s.index('\n  ];', i)
s = s[:j] + '\n' + STEPS.rstrip('\n') + s[j:]
rep("      {id: 'forma', ix: 'mercado/forma', since: 'V23', sel: '#hot-players-body', t: 'Em forma',",
    "      {id: 'labguia63', ix: 'mercado/lab', since: 'V63', sel: '#lab-guide-btn', t: 'Guia do Laboratório', d: () => 'Novo: um guia passo a passo só do Laboratório. Cria uma experiência de exemplo e mostra-te, a fazer, como trocar, trancar, ver os números, comparar e seguir uma equipa fantasma. Abre-o neste botão, nas boas-vindas do tutorial ou no Procurar («guia do laboratório»).'},\n"
    "      {id: 'forma', ix: 'mercado/forma', since: 'V23', sel: '#hot-players-body', t: 'Em forma',")

# 3. motor do tutorial: modo 'lab', st.pre e limpeza no fim
rep("    let L = tutAll();\n    if (mode === 'quick')",
    "    let L = tutAll();\n"
    "    if (mode === 'lab') return L.filter(x => x.labTut);   // V63: o guia do Laboratório é um percurso próprio\n"
    "    L = L.filter(x => !x.labTut);\n"
    "    if (mode === 'quick')")
rep("    await tutSleep(st.wait || 180);\n    const el = tutTarget(st);",
    "    if (st.pre) { await tutSleep(60); try { await st.pre(); } catch (e) { console.error(e); } }   // V63: o guia faz coisas a sério\n"
    "    await tutSleep(st.wait || 180);\n    const el = tutTarget(st);")
rep("  function tutEnd(done) {\n    TUT.active = false;",
    "  function tutEnd(done) {\n    if (LABTUT) { try { labTutEnd(); } catch (e) { console.error(e); } }   // V63: o exemplo do guia sai, a não ser que se guarde\n"
    "    TUT.active = false;")
rep("    TUT.mode = mode; TUT.list = tutSteps(mode); TUT.miss = []; TUT.active = true;",
    "    if (LABTUT) { try { labTutEnd(); } catch (e) { console.error(e); } }\n"
    "    TUT.mode = mode; TUT.list = tutSteps(mode); TUT.miss = []; TUT.active = true;")
# boas-vindas e Procurar
rep("        <button type=\"button\" class=\"btn${nNew || posOk ? '' : ' primary'}\" data-w=\"full\">Tutorial completo <span class=\"note\">≈5 min</span></button>",
    "        <button type=\"button\" class=\"btn\" data-w=\"lab\">Guia do Laboratório <span class=\"note\">≈3 min</span></button>\n"
    "        <button type=\"button\" class=\"btn${nNew || posOk ? '' : ' primary'}\" data-w=\"full\">Tutorial completo <span class=\"note\">≈5 min</span></button>")
rep("  APP_INDEX.push({v: '', s: '', a: 'Ajuda', n: 'Tutorial', act: 'tour', syn: ['tutorial', 'ajuda', 'guia', 'visita guiada', 'novidades', 'o que há de novo']});",
    "  APP_INDEX.push({v: '', s: '', a: 'Ajuda', n: 'Tutorial', act: 'tour', syn: ['tutorial', 'ajuda', 'guia', 'visita guiada', 'novidades', 'o que há de novo']});\n"
    "  APP_INDEX.push({v: '', s: '', a: 'Ajuda', n: 'Guia do Laboratório', act: 'labtour', syn: ['guia do laboratório', 'guia do laboratorio', 'tutorial do laboratório', 'como usar o laboratório', 'aprender o laboratório', 'ajuda do laboratório']});")
rep("go: () => x.act === 'tour' ? tutWelcome(true) : (",
    "go: () => x.act === 'tour' ? tutWelcome(true) : x.act === 'labtour' ? tutStart('lab') : (")

# 4. funções do guia
JS = r'''
  // ---------- V63: Guia do Laboratório (tutStart('lab')) ----------
  // Faz as coisas a sério numa experiência de exemplo («Exemplo do guia», copiada do plantel). Cada comando corre uma
  // só vez por guia (LABTUT.done), para «Anterior» não o repetir. No fim o exemplo é apagado, a não ser que se guarde.
  var LABTUT = null;
  function labTutX() { return LABTUT ? (labS(LABTUT.mgr).list.find(x => x.id === LABTUT.id) || null) : null; }
  function labTutName() { const x = labTutX(); return x ? x.name : 'Exemplo do guia'; }
  function labTutDemo() {
    if (LABTUT && curMgr() !== LABTUT.mgr) { try { refreshForManager(LABTUT.mgr); } catch (e) {} }
    let x = labTutX();
    if (!x) {
      const S = labS(), prev = S.sel;
      x = labFromSquad(); x.name = ''; x.name = labName('Exemplo do guia'); x.note = 'Criada pelo guia do Laboratório.';
      LABTUT = {mgr: curMgr(), id: x.id, prev, keep: false, done: {}, out: {}, prevCmp: null, rep: null};
    }
    labS(LABTUT.mgr).sel = LABTUT.id; labSave();
    try { labDraw(); } catch (e) { console.error(e); }
    return x;
  }
  function labTutOut(k) { return (LABTUT && LABTUT.out[k]) || {frase: '', ok: false, txt: ''}; }
  // escreve a frase na caixa de comandos e carrega em «Fazer», como o utilizador faria
  async function labTutCmd(key, frase) {
    if (!LABTUT || LABTUT.done[key]) return labTutOut(key);
    LABTUT.done[key] = true;
    const inp = document.getElementById('lab-cmd-in'), f = document.getElementById('lab-cmdf');
    if (!inp || !f) return labTutOut(key);
    inp.value = frase;
    if (f.requestSubmit) f.requestSubmit(); else f.dispatchEvent(new Event('submit', {cancelable: true, bubbles: true}));
    let o = null;
    for (let k = 0; k < 50; k++) { await tutSleep(60); o = document.getElementById('lab-cmd-out'); if (o && !o.hidden && o.textContent !== 'A fazer…') break; }
    LABTUT.out[key] = {frase, ok: !!(o && o.classList.contains('ok')), txt: o ? o.innerText.trim() : '', sug: !!LABTUT.sug && key === 'troca'};
    return LABTUT.out[key];
  }
  // a troca a experimentar: a sugerida da semana, se der; senão o 1.º exemplo da caixa de comandos
  function labTutTrade() {
    const x = labTutX(); if (!x) return 'ajuda';
    const mv = ((SUGGESTED_MOVES[LABTUT.mgr] || {}).transfers || []).find(m => x.ids.includes(m.out) && !x.ids.includes(m.in) && FULL_POOL_BY_ID[m.in] && FULL_POOL_BY_ID[m.out]);
    LABTUT.sug = !!mv;
    return mv ? `troca ${shortName(FULL_POOL_BY_ID[mv.out].name)} por ${shortName(FULL_POOL_BY_ID[mv.in].name)}` : labExamples()[0];
  }
  // uma troca que as regras não deixam: um defesa por um avançado (já há 3 avançados)
  function labTutBad() {
    const x = labTutX(); if (!x) return 'ajuda';
    const ps = labPs(x), d = ps.filter(p => p.cls === 'def').sort((a, b) => a.price - b.price)[0];
    const f = FULL_POOL.filter(p => p.cls === 'fwd' && !x.ids.includes(p.id) && labFindPlayer(shortName(p.name)) === p).sort((a, b) => b.price - a.price)[0];
    return d && f ? `troca ${shortName(d.name)} por ${shortName(f.name)}` : 'troca um defesa por um avançado';
  }
  function labTutTop() { const x = labTutX(); const p = x ? labPs(x).filter(q => q.cls !== 'gk').sort((a, b) => epAt(b, 0) - epAt(a, 0))[0] : null; return p ? shortName(p.name) : 'Haaland'; }
  function labTutFrom() { return Math.max(1, GW_META.last - 3); }
  function labTutEvalTxt() {
    const r = LABTUT && LABTUT.rep;
    if (!r || r.ep1 == null) return 'Aqui aparecem os pontos esperados da próxima jornada e das próximas 5, a probabilidade de o capitão fazer 10 ou mais, a diferença para a tua equipa real, o H2H, os diferenciais e as ameaças, e as lesões e castigos previstos.';
    return `Para «${nwEsc(r.name)}»: <b>≈${f1(r.ep1)} pts esperados na J${HZ[0]}</b> e ≈${f1(r.ep5)} nas J${HZ[0]}-J${HZ[HZ.length - 1]}; o capitão (${nwEsc(r.cap)}) tem ${r.p10}% de fazer 10 ou mais.`
      + (r.real ? ` A tua equipa real: ≈${f1(r.real.ep1)} e ≈${f1(r.real.ep5)} (${sgn(r.ep1 - r.real.ep1)} e ${sgn(r.ep5 - r.real.ep5)}).` : '')
      + (r.h2h ? ` Contra o teu adversário do H2H (${nwEsc(r.h2h.opp)}) ganharias ${r.h2h.win}% das vezes${r.h2h.realWin != null ? ` (${r.h2h.realWin}% com a equipa real)` : ''}.` : '')
      + ` Mostra ainda os <b>diferenciais</b> (teus e de poucos rivais), as <b>ameaças</b> (de muitos rivais e não teus) e as <b>lesões e castigos</b> previstos, com o custo em pontos.`;
  }
  function labTutGhostTxt() {
    const o = labTutOut('segue'), g = LABTUT && LABTUT.rep && LABTUT.rep.ghost;
    const nums = g && g.gws && g.gws.length ? ` Como se tivesses esta equipa, parada, desde a J${g.from}: <b>${g.pts} pts</b> nas J${g.from}-J${g.gws[g.gws.length - 1][0]}, contra ${g.real} da tua equipa real.` : '';
    return `Escrevi «${nwEsc(o.frase)}»: a app soma os <b>pontos reais</b> que esta equipa faria em cada jornada, com as regras da FPL (substituições automáticas pela ordem do banco; capitão a dobrar, ou o vice se ele não jogar).${nums} Três modos: <b>congelada</b>, <b>segue o conselho da app</b> (a troca e o capitão aconselhados antes de cada deadline) ou <b>segue um plano meu</b> (marcas as trocas por jornada). Para testar uma ideia daqui para a frente, liga «Seguir a partir da J${GW_META.next}»: os pontos aparecem à medida que as jornadas são jogadas.`;
  }
  function labTutEndTxt() {
    const x = labTutX();
    return `Resumo: <b>cria</b> na lista, <b>mexe</b> no campo ou com comandos, <b>vê</b> os números, <b>compara</b> lado a lado e <b>segue</b> como fantasma.`
      + (x ? ` O que faço ao exemplo «${nwEsc(x.name)}»?<br><span class="tut-lab"><button type="button" class="btn small primary" data-labtut="keep">Guardar</button><button type="button" class="btn small" data-labtut="del">Apagar</button></span><br><span class="note">Se carregares em «Terminar» sem escolher, apago-o (fica «Recuperar» na lista).</span>` : '')
      + ` Voltas a este guia pelo botão «Guia passo a passo», no topo do Laboratório.`;
  }
  function labTutEnd() {
    const T = LABTUT; if (!T) return; LABTUT = null;
    const S = labS(T.mgr), x = S.list.find(e => e.id === T.id);
    if (x && !T.keep) {
      S.list = S.list.filter(e => e.id !== T.id); LAB.trash = x;
      S.cmp = (T.prevCmp || S.cmp).filter(id => id !== T.id && (S.list.some(e => e.id === id) || LAB.repo.some(e => e.id === id)));
      S.sel = T.prev && S.list.some(e => e.id === T.prev) ? T.prev : ((S.list[0] || {}).id || null);
    }
    labSave();
    try { LAB.ui.msg = null; const o = document.getElementById('lab-cmd-out'); if (o) o.hidden = true; const i = document.getElementById('lab-cmd-in'); if (i) i.value = ''; if (curMgr() === T.mgr) labDraw(); } catch (e) { console.error(e); }
  }
  document.addEventListener('click', ev => {
    const b = ev.target.closest('[data-labtut]'); if (!b || !LABTUT) return;
    LABTUT.keep = b.dataset.labtut === 'keep'; tutEnd(true);
  });
'''
rep("  // o guia antigo passa a abrir as boas-vindas (⚙ \"Ver o tutorial\" chama startTour)\n",
    JS + "  // o guia antigo passa a abrir as boas-vindas (⚙ \"Ver o tutorial\" chama startTour)\n")

rep("  var APP_VERSION = 'V62';", "  var APP_VERSION = 'V63';")
H.write_text(s, encoding='utf-8', newline='\n')
LABJS.write_text(lj, encoding='utf-8', newline='\n')
print('V63 aplicado')
