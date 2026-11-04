"""Testa o tutorial (V49): percorre o tutorial completo no computador (1280) e no telemóvel (390), com o Bruno e com
o Marco, nos modos completo e simples; confirma que cada destaque existe e está visível, que no telemóvel a caixa
não tapa o destaque e que o foco do teclado fica na caixa. Testa também as boas-vindas (1.ª visita, novidades,
continuar onde parei), a visita rápida, ⚙ "Ver o tutorial", o Procurar ("ajuda") e o Esc.
Uso (a partir da raiz): py -X utf8 _build/scripts/test_tutorial.py"""
import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright

URL = (Path(__file__).resolve().parents[2] / 'index.html').as_uri()
STATE = '''() => {
  const box = document.getElementById('tut-box'); if (!box) return null;
  const st = TUT.list[TUT.i], el = TUT.el, b = box.getBoundingClientRect();
  const r = el ? el.getBoundingClientRect() : null;
  return {i: TUT.i, n: TUT.list.length, id: st && st.id, sel: st && st.sel, hasEl: !!el,
          vis: !!(r && r.height > 0 && r.bottom > 0 && r.top < innerHeight),
          // o destaque (a moldura) não pode ficar por baixo da caixa no telemóvel
          overlap: (() => { const sp = document.getElementById('tut-spot'); if (!sp || sp.hidden || innerWidth >= 960) return false; const q = sp.getBoundingClientRect(); return Math.min(q.bottom, b.bottom) - Math.max(q.top, b.top) > 2; })(),
          focus: box.contains(document.activeElement), prog: box.querySelector('.tut-prog').innerText};
}'''


async def run_full(pg, label, errs):
    await pg.evaluate("tutStart('full')"); await pg.wait_for_timeout(700)
    seen, guard = [], 0
    while guard < 80:
        guard += 1
        s = await pg.evaluate(STATE)
        if not s:
            break
        seen.append(s['id'])
        if s['sel'] and not s['hasEl']: errs.append(f'{label}: passo {s["id"]} sem destaque')
        if s['sel'] and s['hasEl'] and not s['vis']: errs.append(f'{label}: passo {s["id"]} com destaque fora do ecrã')
        if s['overlap']: errs.append(f'{label}: passo {s["id"]} — a caixa tapa o destaque')
        if not s['focus']: errs.append(f'{label}: passo {s["id"]} — o foco não está na caixa')
        await pg.click('#tut-box [data-t="next"]'); await pg.wait_for_timeout(200)
        # espera que o passo seguinte esteja mostrado (alguns esperam por cálculos)
        for _ in range(40):
            if await pg.evaluate("!document.getElementById('tut-box') || TUT.shown === TUT.i"): break
            await pg.wait_for_timeout(100)
        await pg.wait_for_timeout(320)  # a moldura anima 0,18 s entre passos
    miss = await pg.evaluate("TUT.miss")
    if miss: errs.append(f'{label}: destaques que faltaram {miss}')
    return seen


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        total_err = 0
        for w, h in [(1280, 900), (390, 844)]:
            for mode in ('completo', 'simples'):
                for mgr in ('bruno', 'marco'):
                    pg = await b.new_page(viewport={'width': w, 'height': h})
                    await pg.add_init_script("try{localStorage.setItem('fpl-tour-done','\"off\"');localStorage.setItem('fpl-mode'," + json.dumps(json.dumps(mode)) + ")}catch(e){}")
                    errs = []
                    pg.on('pageerror', lambda e: errs.append('PAGEERR ' + str(e)))
                    pg.on('console', lambda m: errs.append('CONSOLE ' + m.text) if m.type in ('error', 'warning') and not ('Failed to load resource' in m.text or 'fonts.g' in m.text) else None)
                    await pg.goto(URL); await pg.wait_for_timeout(1200)
                    if await pg.is_visible('#tut-wel'): errs.append('boas-vindas apareceram com "off"')
                    await pg.click(f'.mswitch-btn[data-manager="{mgr}"]'); await pg.wait_for_timeout(200)
                    label = f'{w} {mode} {mgr}'
                    seen = await run_full(pg, label, errs)
                    if mode == 'simples' and 'simples-fim' not in seen: errs.append(f'{label}: falta o aviso final do modo simples')
                    print(f'{label}: {len(seen)} passos · ERRORS {len(errs)}')
                    [print('   ', e) for e in errs[:12]]
                    total_err += len(errs)
                    await pg.close()
            # boas-vindas e entradas
            pg = await b.new_page(viewport={'width': w, 'height': h})
            errs = []
            pg.on('pageerror', lambda e: errs.append('PAGEERR ' + str(e)))
            await pg.goto(URL); await pg.wait_for_timeout(1600)
            btns = await pg.eval_on_selector_all('#tut-wel [data-w]', 'els => els.map(e => e.dataset.w)')
            if btns[-3:] != ['full', 'quick', 'none']: errs.append(f'1.ª visita: botões {btns}')
            await pg.click('#tut-wel [data-w="quick"]'); await pg.wait_for_timeout(400)
            q = 0
            while await pg.query_selector('#tut-box') and q < 10:
                q += 1; await pg.click('#tut-box [data-t="next"]'); await pg.wait_for_timeout(300)
            if q != 5: errs.append(f'visita rápida com {q} passos (queria 5)')
            # continuar onde parei
            await pg.evaluate("tutStart('full')"); await pg.wait_for_timeout(400)
            for _ in range(3):
                await pg.click('#tut-box [data-t="next"]'); await pg.wait_for_timeout(300)
            await pg.keyboard.press('Escape'); await pg.wait_for_timeout(200)
            if await pg.query_selector('#tut-box'): errs.append('Esc não fecha')
            await pg.click('#set-btn'); await pg.wait_for_timeout(100); await pg.click('#set-tour'); await pg.wait_for_timeout(300)
            res = await pg.eval_on_selector_all('#tut-wel [data-w]', 'els => els.map(e => e.innerText)')
            if not any('Continuar onde parei' in t for t in res): errs.append(f'⚙ tutorial sem "Continuar": {res}')
            await pg.keyboard.press('Escape'); await pg.wait_for_timeout(150)
            # Procurar "ajuda"
            if w < 960: await pg.click('#srch-btn')
            await pg.fill('#srch-q', 'ajuda'); await pg.wait_for_timeout(150); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(300)
            if not await pg.is_visible('#tut-wel'): errs.append('Procurar "ajuda" não abre o tutorial')
            await pg.keyboard.press('Escape')
            # novidades: quem viu o guia antigo (true) ou a V47 recebe "Ver o que há de novo"; quem viu a V49 recebe as da V54 (duplas e brancas); quem viu a V54 não recebe nada
            for val, want in (('true', True), ('"V47"', True), ('"V49"', True), ('"V54"', False)):
                pg2 = await b.new_page(viewport={'width': w, 'height': h})
                await pg2.add_init_script("try{localStorage.setItem('fpl-tour-done'," + json.dumps(val) + ")}catch(e){}")
                await pg2.goto(URL); await pg2.wait_for_timeout(1600)
                has = bool(await pg2.query_selector('#tut-wel [data-w="new"]'))
                if has != want: errs.append(f'novidades com {val}: {has} (queria {want})')
                if has:
                    await pg2.click('#tut-wel [data-w="new"]'); await pg2.wait_for_timeout(400)
                    n = await pg2.evaluate("TUT.list.length")
                    if not n: errs.append(f'novidades com {val}: lista vazia')
                await pg2.close()
            # o índice do Procurar e o tutorial não ficam desencontrados (o Avançado tem um passo próprio)
            gaps = await pg.evaluate("APP_INDEX.filter(x => x.v && x.v !== 'avancado' && !tutAll().some(st => st.ix === x.v + '/' + x.s)).map(x => x.v + '/' + x.s)")
            if gaps: errs.append(f'separadores sem passo no tutorial: {gaps}')
            print(f'{w} boas-vindas/entradas · ERRORS {len(errs)}'); [print('   ', e) for e in errs[:12]]
            total_err += len(errs)
            await pg.close()
        print('TOTAL ERRORS', total_err)
        await b.close()

asyncio.run(main())
