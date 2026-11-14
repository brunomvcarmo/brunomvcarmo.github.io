"""Testa o Laboratório (V62): Jogadores › Laboratório no computador (1280) e no telemóvel (390), com o Bruno e o Marco.
Confirma: comandos em linguagem simples, regras da FPL com o motivo, que nada mexe no plantel verdadeiro (sexta lição),
contas das equipas fantasma (substituições automáticas, capitão/vice) — incluindo contra os pontos oficiais dos 20
gestores na última jornada, quando os plantéis da app são dessa jornada —, exportar/importar, experiências do
repositório (só de leitura), Procurar, "Guardar como experiência", tema escuro e nada fixo no ecrã.
Uso (a partir da raiz): py -X utf8 _build/scripts/test_lab.py   (Linux: python3)"""
import asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright

URL = (Path(__file__).resolve().parents[2] / 'index.html').as_uri()
REPO = {'experiments': {'experiments': [{'id': 'ctest1', 'mgr': 'bruno', 'name': 'Do repositório', 'gw': 1, 'budget': 100, 'ids': [], 'src': 'claude'}]}, 'advice': {}, 'history': {}}
TOUR_OFF = "try{localStorage.setItem('fpl-tour-done','\"off\"')}catch(e){}"
STRIP = lambda h: re.sub(r'<[^>]+>', '', h or '')


async def cmd(pg, c):
    return await pg.evaluate("(c) => { const r = labCmd(c); labDraw(); return r; }", c)


async def main():
    total = 0
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for w, h in [(1280, 900), (390, 844)]:
            pg = await b.new_page(viewport={'width': w, 'height': h})
            await pg.add_init_script(TOUR_OFF + "window.__LAB_DATA = " + json.dumps(REPO) + ";")
            errs = []
            pg.on('pageerror', lambda e: errs.append('PAGEERR ' + str(e)))
            pg.on('console', lambda m: errs.append('CONSOLE ' + m.type + ' ' + m.text) if m.type in ('error', 'warning') and not ('Failed to load resource' in m.text or 'fonts.g' in m.text) else None)
            await pg.goto(URL); await pg.wait_for_timeout(1000)
            n = 0
            for mgr in ('bruno', 'marco'):
                await pg.click(f'.mswitch-btn[data-manager="{mgr}"]'); await pg.wait_for_timeout(200)
                before = await pg.evaluate("JSON.stringify([SQUAD_STATE, STORE.log, STORE.plan, SUGGESTED_MOVES])")
                await pg.evaluate("showView('mercado','lab')"); await pg.wait_for_timeout(900)
                L = f'{w} {mgr}'
                st = await pg.evaluate("""() => ({list: labS().list.length, secs: ['lab-cmd','lab-list','lab-edit','lab-eval','lab-cmp','lab-ghost'].filter(k => { const e = document.getElementById(k); return !e || !e.innerText.trim(); }),
                    over: document.documentElement.scrollWidth > innerWidth + 1, fixed: [...document.querySelectorAll('#lab-root *')].filter(e => getComputedStyle(e).position === 'fixed').length,
                    kpis: document.querySelectorAll('#lab-eval .kpi').length, toks: document.querySelectorAll('#lab-edit [data-lab="tok"]').length})""")
                if st['list'] < 1: errs.append(f'{L}: sem a experiência de partida')
                if st['secs']: errs.append(f'{L}: secções vazias {st["secs"]}')
                if st['over']: errs.append(f'{L}: a página passa a largura do ecrã')
                if st['fixed']: errs.append(f'{L}: {st["fixed"]} elementos fixos no ecrã')
                if st['kpis'] != 5 or st['toks'] != 15: errs.append(f'{L}: {st["kpis"]} números-chave (queria 5) e {st["toks"]} jogadores no campo (queria 15)')
                # comandos do pedido, com jogadores que existem neste plantel
                ex = await pg.evaluate("""() => { const x = labCur(), ps = labPs(x), mid = ps.filter(p => p.cls === 'mid').sort((a, b) => a.price - b.price)[0];
                    const alt = FULL_POOL.filter(p => p.cls === 'mid' && !ps.includes(p) && p.status === 'a' && p.price <= mid.price && ps.filter(q => q.team === p.team && q !== mid).length < 3).sort((a, b) => sum5(b) - sum5(a))[0];
                    const E = Object.keys(LEAGUE_SQUADS).map(Number).find(e => e !== CMP_ENTRY[curMgr()]);
                    return {out: mid.name, inn: alt.name, cap: ps.filter(p => p.cls === 'fwd').sort((a, b) => epAt(b, 0) - epAt(a, 0))[0].name, gw: HZ[Math.min(1, HZ.length - 1)], riv: LEAGUE_SQUADS[E].m, b: Math.ceil(x.budget)}; }""")
                for c in [f'troca {ex["out"]} por {ex["inn"]}', f'tranca {ex["cap"]} e {ex["inn"]}', f'orçamento {ex["b"]}', f'capitão {ex["cap"]}', f'melhor equipa para a J{ex["gw"]}',
                          f'copia a equipa do {ex["riv"]}', 'compara com a minha', 'segue a partir da J1', 'nova experiência Teste', 'completa com os melhores', 'duplica', 'apaga', 'desfaz']:
                    r = await cmd(pg, c); n += 1
                    if not r['ok']: errs.append(f'{L}: comando «{c}» falhou: {STRIP(r["msg"])[:140]}')
                r = await cmd(pg, 'faz-me um café')
                if r['ok'] or 'data-lab="ex"' not in r['msg']: errs.append(f'{L}: uma frase desconhecida devia mostrar exemplos')
                # regras: 4.º jogador do mesmo clube e orçamento, com o motivo
                rules = await pg.evaluate("""() => { const x = labNew({name: 'Regras', budget: 100}), club = FULL_POOL.filter(p => p.team === 1 && p.status === 'a').sort((a, b) => a.price - b.price);
                    const pick = []; ['def', 'mid', 'fwd', 'gk'].forEach(c => { const p = club.find(q => q.cls === c && !pick.includes(q)); if (p && pick.length < 3) pick.push(p); });
                    pick.forEach(p => labAdd(x, p)); const four = club.find(p => !pick.includes(p) && labPs(x).filter(q => q.cls === p.cls).length < LAB_NEED[p.cls]);
                    const a = labAdd(x, four); x.budget = +(labCost(labPs(x)) + 1).toFixed(1); const dear = FULL_POOL.filter(p => p.team !== 1).sort((p, q) => q.price - p.price)[0]; const c = labAdd(x, dear);
                    const pr = labProblems(x); const g = labGhostOn(x, GW_META.next, 'frozen'); labS().list = labS().list.filter(e => e !== x); labS().sel = null; labSave(); return {a, c, pr, g, n: x.ids.length}; }""")
                if 'máximo 3 por clube' not in rules['a']: errs.append(f'{L}: o 4.º jogador do clube entrou ({rules["a"]!r})')
                if 'orçamento' not in rules['c']: errs.append(f'{L}: jogador caro demais sem motivo ({rules["c"]!r})')
                if rules['n'] != 3 or not rules['pr'] or not rules['g']: errs.append(f'{L}: regras {rules}')
                # nada mexeu no plantel verdadeiro
                after = await pg.evaluate("JSON.stringify([SQUAD_STATE, STORE.log, STORE.plan, SUGGESTED_MOVES])")
                if after != before: errs.append(f'{L}: o Laboratório mexeu no plantel verdadeiro, no registo ou no plano')
                # fantasmas: desenhadas, com gráfico e tabela
                gh = await pg.evaluate("""() => { const x = labList().find(e => e.ghost); if (!x) return null; labS().sel = x.id; labDraw(); const r = labGhostRun(x);
                    return {played: r.played.length, total: r.total, svg: !!document.querySelector('#lab-ghost svg'), rows: document.querySelectorAll('#lab-ghost table tbody tr').length, over: document.documentElement.scrollWidth > innerWidth + 1}; }""")
                if not gh or not gh['played'] or not gh['svg'] or gh['rows'] != gh['played'] + 1 or gh['over']: errs.append(f'{L}: equipas fantasma {gh}')
                # exportar / importar
                io = await pg.evaluate("""() => { const S = labS(), n = S.list.length, code = labExportCode(); S.list = []; const r = labImportCode(code); const bad = labImportCode('abc'); return {n, back: labS().list.length, ok: r.ok, bad: bad.ok}; }""")
                if not io['ok'] or io['n'] != io['back'] or io['bad']: errs.append(f'{L}: exportar/importar {io}')
            # separado por gestor; experiência do repositório só no Bruno e só de leitura
            sep = await pg.evaluate("""() => { const S = labStore(); return {b: S.bruno.list.map(x => x.id), m: S.marco.list.map(x => x.id)}; }""")
            if set(sep['b']) & set(sep['m']) or not sep['b'] or not sep['m']: errs.append(f'{w}: experiências não estão separadas por gestor')
            await pg.click('.mswitch-btn[data-manager="bruno"]'); await pg.wait_for_timeout(300)
            await pg.evaluate("showView('mercado','lab')"); await pg.wait_for_timeout(500)
            repo = await pg.evaluate("""() => { const x = labList().find(e => e.repo); if (!x) return null; labS().sel = x.id; labDraw(); const r = labCmdOne('apaga');
                return {txt: document.getElementById('lab-list').innerText.includes('Claude Code'), ro: document.getElementById('lab-name').disabled, del: r.ok, still: !!labList().find(e => e.repo)}; }""")
            if not repo or not repo['txt'] or not repo['ro'] or repo['del'] or not repo['still']: errs.append(f'{w}: experiência do repositório {repo}')
            await pg.click('.mswitch-btn[data-manager="marco"]'); await pg.wait_for_timeout(300)
            if await pg.evaluate("labList().some(e => e.repo)"): errs.append(f'{w}: a experiência do Bruno no repositório aparece ao Marco')
            await pg.click('.mswitch-btn[data-manager="bruno"]'); await pg.wait_for_timeout(300)
            # contas da FPL: capitão sem jogar → vice a dobrar; GR pelo GR; suplentes pela ordem se a formação continuar válida
            sc = await pg.evaluate("""() => { const sq = squadOf('bruno').filter(Boolean), L = labLineup({ids: sq.map(p => p.id), auto: true});
                const T = {xi: L.xi.map(p => p.id), bench: L.bench.map(p => p.id), cap: L.cap.id, vice: L.vice.id}, gk = L.xi.find(p => p.cls === 'gk').id, gk2 = L.bench.find(p => p.cls === 'gk').id, ob = L.bench.filter(p => p.cls !== 'gk').map(p => p.id);
                const H = (zero, fin) => ({final: fin !== false, get: id => zero.includes(id) ? [0, 0] : id === gk2 ? [7, 90] : ob.includes(id) ? [3 + ob.indexOf(id), 90] : [2, 90]});
                const a = labScore(T, H([])), b = labScore(T, H([T.cap])), c = labScore(T, H([gk])), d = labScore(T, H([T.cap, T.vice])), e = labScore(T, H([T.cap], false));
                const defs = L.xi.filter(p => p.cls === 'def'), nd = defs.length, firstOk = FULL_POOL_BY_ID[ob[0]].cls === 'def' || nd > 3;
                const f = labScore(T, H([defs[0].id]));
                return {a: a.total, b: [b.total, b.capUsed === T.vice, b.subs.length, b.subs.length ? 20 + 3 + ob.indexOf(b.subs[0][0]) + 2 : 22], c: [c.total, c.subs.length], d: [d.total, d.capUsed], e: [e.total, e.subs.length], f: [f.total, f.subs.length ? f.subs[0][0] : null, firstOk, ob]}; }""")
            if sc['a'] != 24: errs.append(f'{w}: onze completo devia dar 24 ({sc["a"]})')
            if sc['b'][0] != sc['b'][3] or not sc['b'][1] or sc['b'][2] != 1: errs.append(f'{w}: capitão sem jogar {sc["b"]} (queria o vice a dobrar e 1 substituição)')
            if sc['c'] != [29, 1]: errs.append(f'{w}: GR sem jogar {sc["c"]} (queria 29 com o GR suplente)')
            if sc['d'][1] is not None: errs.append(f'{w}: capitão e vice sem jogar: ninguém dobra ({sc["d"]})')
            if sc['e'] != [20, 0]: errs.append(f'{w}: jornada por fechar não tem substituições ({sc["e"]})')
            if sc['f'][2] and sc['f'][1] != sc['f'][3][0]: errs.append(f'{w}: o 1.º do banco devia entrar primeiro ({sc["f"]})')
            # contra os pontos oficiais dos 20 gestores na última jornada (só quando os plantéis da app são dessa jornada)
            off = await pg.evaluate("""() => { const g = GW_META.last, H = labPtsGw(g); if (!H || !H.final || (GW_META.squadsGw || g) !== g || (window.__LIVE && window.__LIVE.picks_event !== g)) return null;
                const bad = []; let n = 0; Object.keys(LEAGUE_SQUADS).forEach(e => { const L = LEAGUE_SQUADS[e], chip = L['chip' + g]; if (chip === '3xc' || chip === 'bboost' || L.pend) return;
                  const c = FULL_POOL_BY_NAME[L.c], v = FULL_POOL_BY_NAME[L.vc]; if (!c) return; n++;
                  const s = labScore({xi: L.s, bench: L.b, cap: c.id, vice: v ? v.id : c.id}, H); if (s.total !== L.p6) bad.push([L.tn, s.total, L.p6]); });
                return {n, bad}; }""")
            if off and off['bad']: errs.append(f'{w}: pontos das equipas diferentes dos oficiais: {off["bad"][:4]}')
            # Procurar e "Guardar como experiência"
            for term in ('laboratório', 'experiência', 'testar equipa', 'fantasma'):
                if w < 960: await pg.click('#srch-btn')
                await pg.fill('#srch-q', term); await pg.wait_for_timeout(120)
                first = await pg.evaluate("(document.querySelector('#srch-res .srch-it span')||{}).innerText")
                if first != 'Laboratório': errs.append(f'{w}: Procurar {term!r} -> {first!r}')
                await pg.keyboard.press('Escape')
            n0 = await pg.evaluate("labS().list.length")
            await pg.evaluate("showView('competicao','comparar')"); await pg.wait_for_timeout(300)
            await pg.click('#cmp-pick [data-labsave]'); await pg.wait_for_timeout(700)
            c1 = await pg.evaluate("document.getElementById('crumbs').innerText")
            await pg.evaluate("showView('mercado','ideal')")
            await pg.wait_for_selector('#idl-to-lab:not([disabled])', timeout=20000)
            await pg.click('#idl-to-lab'); await pg.wait_for_timeout(700)
            c2 = await pg.evaluate("document.getElementById('crumbs').innerText")
            n1 = await pg.evaluate("labS().list.length")
            if 'Laboratório' not in c1 or 'Laboratório' not in c2 or n1 != n0 + 2: errs.append(f'{w}: Guardar como experiência: {c1} / {c2} / {n0}->{n1}')
            # tema escuro: os cartões do Laboratório não ficam brancos
            dark = await pg.evaluate("""() => { document.documentElement.setAttribute('data-theme', 'dark'); const lum = s => { const m = s.match(/\\d+/g).map(Number); return (m[0] + m[1] + m[2]) / 3; };
                const r = ['#lab-list', '.lab-it', '#lab-cmd-in', '#lab-name', '.lab-act, .lab-hint'].map(q => { const e = document.querySelector(q); return e ? [q, lum(getComputedStyle(e).backgroundColor), getComputedStyle(e).backgroundColor] : null; }).filter(Boolean);
                document.documentElement.removeAttribute('data-theme'); return r.filter(x => x[1] > 160 && !/, 0\\)$/.test(x[2])); }""")
            if dark: errs.append(f'{w}: no tema escuro ficam claros: {dark}')
            await pg.screenshot(path=str(Path(__file__).resolve().parents[1] / 'shots' / f'{w}-lab.png'), full_page=(w == 1280))
            print(f'{w}: {n} comandos' + (f' · {off["n"]} equipas conferidas com os pontos oficiais da J' + str(await pg.evaluate('GW_META.last')) if off else ' · (plantéis de outra jornada: sem conferência oficial)'))
            print('ERRORS', len(errs)); [print('  ', e[:300]) for e in errs[:30]]
            total += len(errs)
            await pg.close()
        await b.close()

asyncio.run(main())
