import asyncio, sys, os
from playwright.async_api import async_playwright
from pathlib import Path as _P
URL = (_P(__file__).resolve().parents[2] / 'index.html').as_uri()
SHOTS = str(_P(__file__).resolve().parents[1] / 'shots')
_P(SHOTS).mkdir(parents=True, exist_ok=True)   # num clone novo a pasta ainda não existe
os.makedirs(SHOTS, exist_ok=True)
CHECK = '''() => {
  const vis = el => !!(el && el.offsetParent !== null);
  const v = [...document.querySelectorAll('.view')].filter(x => !x.hidden);
  const subs = v.length ? [...v[0].querySelectorAll(':scope > .subview')].filter(x => !x.hidden) : [];
  // empty visible containers that JS should have filled
  const empties = [...document.querySelectorAll('.view:not([hidden]) [id]')].filter(el =>
     vis(el) && /^(DIV|TBODY|OL|UL)$/.test(el.tagName) && el.children.length === 0 && el.textContent.trim() === ''
     && !['crumbs','onze-detail'].includes(el.id)).map(el => el.id);
  return {views: v.length, subs: subs.length, empties,
          overflow: document.documentElement.scrollWidth > window.innerWidth + 1,
          crumbs: document.getElementById('crumbs').innerText};
}'''

TOUR_OFF = "try{localStorage.setItem('fpl-tour-done','\"off\"')}catch(e){}"

async def goto_view(pg, v):
    # V47: no computador o menu lateral; no telemóvel os 5 botões, e o Avançado pelo link do rodapé
    if await pg.is_visible('.mnav'):
        if await pg.query_selector(f'.mnav-btn[data-v="{v}"]'):
            await pg.click(f'.mnav-btn[data-v="{v}"]')
        else:
            await pg.click(f'.page-foot [data-goto="{v}"]')
        return
    await pg.click(f'.nav-item[data-view="{v}"]')

OLD = ['pontos', 'decisoes-capitao', 'decisoes-simulador', 'liga-orcamentos', 'liga-capitaes', 'planeador-registo', 'historico-modelo',
       'plantel-orcamento', 'equipas-europa-eq', 'jogadores-ideal', 'rivais', 'onzes', 'aovivo-liga', 'regras-fontes']
SEARCH = [('braçadeira', 'Capitão'), ('dinheiro', 'Orçamentos e chips'), ('wildcard', 'Chips'), ('equipa perfeita', 'Equipa ideal'),
          ('melhor equipa', 'Equipa ideal'), ('budget', 'Orçamentos e chips'), ('haala', 'Erling Haaland'), ('bengalinha', 'Pedro Bengalinha'),
          ('dupla', 'Duplas e brancas (J20-J38)'), ('bgw', 'Duplas e brancas (J20-J38)'), ('chips segunda metade', 'Duplas e brancas (J20-J38)')]

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for mode in ('completo', 'simples'):
          for w,h in [(1280,900),(390,844)]:
            pg = await b.new_page(viewport={'width':w,'height':h})
            await pg.add_init_script(TOUR_OFF + f"try{{localStorage.setItem('fpl-mode', JSON.stringify('{mode}'))}}catch(e){{}}")
            errs = []
            pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
            pg.on('console', lambda m: errs.append('CONSOLE '+m.type+' '+m.text) if m.type in ('error','warning') and not ('Failed to load resource' in m.text or 'fonts.g' in m.text) else None)   # falhas de rede (fontes da Google, sem internet) não são erros da app
            await pg.goto(URL); await pg.wait_for_timeout(800)
            n = 0
            for mgr in ['bruno','marco']:
                await pg.click(f'.mswitch-btn[data-manager="{mgr}"]'); await pg.wait_for_timeout(150)
                # só as áreas e separadores visíveis no modo (no simples o resto está escondido)
                views = await pg.eval_on_selector_all('.nav-item[data-view]','els=>els.filter(e=>!e.hidden).map(e=>e.dataset.view)')
                for v in views:
                    await goto_view(pg, v); await pg.wait_for_timeout(80)
                    subs = await pg.eval_on_selector_all(f'.view[data-view="{v}"] > .subtabs .subtab','els=>els.filter(e=>!e.hidden).map(e=>e.dataset.sub)')
                    for s in (subs or ['']):
                        if s:
                            await pg.click(f'.view[data-view="{v}"] > .subtabs .subtab[data-sub="{s}"]'); await pg.wait_for_timeout(80)
                        r = await pg.evaluate(CHECK)
                        n += 1
                        if r['views'] != 1 or (subs and r['subs'] != 1): errs.append(f'VIS {mode} {w} {mgr} {v}/{s} {r}')
                        if r['overflow']: errs.append(f'OVERFLOW {mode} {w} {mgr} {v}/{s}')
                        if r['empties']: errs.append(f'EMPTY {mode} {w} {mgr} {v}/{s} {r["empties"]}')
                        if mode == 'completo' and (w == 1280 or mgr == 'bruno'):
                            await pg.screenshot(path=f'{SHOTS}/{w}-{mgr}-{v}-{s or "main"}.png', full_page=(w == 1280))
            extra = []
            if mode == 'completo':
                # onzes picker
                await goto_view(pg, 'jogos'); await pg.click('.view[data-view="jogos"] > .subtabs .subtab[data-sub="onzes"]'); await pg.click('.match-btn[data-match="4"]'); await pg.wait_for_timeout(100)
                extra.append('onze: ' + await pg.evaluate("document.querySelector('#onze-detail h2').innerText"))
                # atalhos: guardar o Capitão; aparece no Resumo; o Marco não o vê
                await pg.click('.mswitch-btn[data-manager="bruno"]'); await pg.wait_for_timeout(200)
                await pg.evaluate("showView('semana','capitao')"); await pg.wait_for_timeout(150)
                await pg.click('.view[data-view="semana"] > .fav-sub'); await pg.wait_for_timeout(100)
                await pg.evaluate("showView('semana','resumo')"); await pg.wait_for_timeout(150)
                fav = await pg.evaluate("document.getElementById('fav-card').innerText")
                if 'Capitão' not in fav: errs.append('FAV não aparece: ' + fav[:80])
                if 'Usaste recentemente' not in fav: errs.append('RECENTES não aparecem')
                await pg.click('.mswitch-btn[data-manager="marco"]'); await pg.wait_for_timeout(200)
                favm = await pg.evaluate("document.querySelector('#fav-card .fav-chips').innerText")
                if 'Capitão' in favm: errs.append('FAV não está separado por gestor')
                await pg.click('.mswitch-btn[data-manager="bruno"]'); await pg.wait_for_timeout(200)
                if w < 960 and not await pg.is_visible('#mfav .fav-chip'): errs.append('FAV sem etiqueta no telemóvel')
                # ligações entre ferramentas
                async def act(go, sel, want):
                    await pg.evaluate(go); await pg.wait_for_timeout(250)
                    await pg.click(sel); await pg.wait_for_timeout(500)
                    c = await pg.evaluate("document.getElementById('crumbs').innerText")
                    if want not in c: errs.append(f'LINK {sel} -> {c}')
                    return c
                extra.append(await act("showView('mercado','pesquisa')", '#pl-body [data-act="cmp"]', 'Comparador'))
                extra.append(await act("showView('mercado','pesquisa')", '#pl-body [data-act="plan"]', 'Transferências'))
                if not await pg.query_selector('#plan-root .plan-add'): errs.append('LINK plano sem formulário')
                extra.append(await act("showView('competicao','vigiar')", '#riv-root [data-act="rcmp"]', 'Comparar'))
                extra.append(await act("showView('competicao','vigiar')", '#riv-root [data-act="rwin"]', 'Equipa para ganhar'))
                al = await pg.evaluate("(() => { showView('semana','resumo'); return [...document.querySelectorAll('#alerts [data-act]')].map(b => b.dataset.act); })()")
                if 'subs' in al: extra.append(await act("showView('semana','resumo')", '#alerts [data-act="subs"]', 'Pesquisa'))
                if await pg.query_selector('#todo [data-act="chips"]'): extra.append(await act("showView('semana','resumo')", '#todo [data-act="chips"]', 'Chips'))
                # Definições: mudar para o modo simples e voltar
                await pg.click('#set-btn'); await pg.wait_for_timeout(100)
                await pg.click('#set-pop .seg[data-k="mode"] .seg-btn[data-v="simples"]'); await pg.wait_for_timeout(150)
                hid = await pg.evaluate("[...document.querySelectorAll('.nav-item[data-view]')].filter(b=>b.hidden).length")
                if hid != 3: errs.append(f'MODO simples esconde {hid} áreas (queria 3)')
                await pg.click('#set-pop .seg[data-k="mode"] .seg-btn[data-v="completo"]'); await pg.wait_for_timeout(150)
                await pg.keyboard.press('Escape')
                # deep link e endereços antigos
                await pg.goto(URL + '#liga-capitaes'); await pg.wait_for_timeout(500)
                extra.append('deep: ' + await pg.evaluate("document.getElementById('crumbs').innerText"))
                for t in OLD:
                    await pg.goto(URL + '#' + t); await pg.wait_for_timeout(250)
                    c = await pg.evaluate("document.getElementById('crumbs').innerText")
                    if 'Resumo' in c: errs.append(f'ALIAS {t} -> {c}')
            else:
                # modo simples: a pesquisa encontra o que está escondido, abre e avisa
                if w < 960: await pg.click('#srch-btn')
                await pg.fill('#srch-q', 'simulador'); await pg.wait_for_timeout(120); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(300)
                c = await pg.evaluate("document.getElementById('crumbs').innerText")
                note = await pg.evaluate("(document.getElementById('mode-note')||{}).hidden === false ? document.getElementById('mode-note').innerText : ''")
                if 'Simulador' not in c or 'modo completo' not in note: errs.append(f'SIMPLES pesquisa: {c} / {note[:60]}')
                extra.append(f'{c} · aviso: {note[:40]}')
                await pg.evaluate("showView('semana','resumo')"); await pg.wait_for_timeout(150)
                if await pg.evaluate("!document.getElementById('mode-note').hidden"): errs.append('SIMPLES aviso fica no Resumo')
            # pesquisa: sinónimos, jogadores e gestores; "/" abre no computador
            for term, want in SEARCH:
                if w < 960: await pg.click('#srch-btn')
                await pg.fill('#srch-q', term); await pg.wait_for_timeout(120)
                first = await pg.evaluate("(document.querySelector('#srch-res .srch-it span')||{}).innerText")
                if first != want: errs.append(f'SEARCH {mode} {w} {term!r} -> {first!r} (queria {want!r})')
                await pg.keyboard.press('Escape')
            if w < 960: await pg.click('#srch-btn')
            await pg.fill('#srch-q', 'braçadeira'); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(200)
            enter = await pg.evaluate("document.getElementById('crumbs').innerText")
            if 'Capitão' not in enter: errs.append('SEARCH Enter -> ' + enter)
            if w >= 960:
                await pg.click('body'); await pg.keyboard.press('/'); await pg.wait_for_timeout(80)
                if not await pg.evaluate("document.activeElement && document.activeElement.id === 'srch-q'"): errs.append('SEARCH "/" não abre')
                await pg.keyboard.press('Escape')
            print(mode, w, 'states checked:', n, '|', ' | '.join(extra))
            print('ERRORS', len(errs)); [print('  ', e) for e in errs[:40]]
            await pg.close()
        await b.close()
asyncio.run(main())
