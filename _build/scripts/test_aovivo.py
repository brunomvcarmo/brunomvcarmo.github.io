"""Testa a área Ao vivo com o aovivo.json real da J6 servido por http (?live=1).
Uso: py -X utf8 test_aovivo.py <raiz do repositório> <pasta das capturas>"""
import asyncio, json, subprocess, sys, time, copy
from pathlib import Path
from playwright.async_api import async_playwright

ROOT, SHOTS = Path(sys.argv[1]), Path(sys.argv[2])
SHOTS.mkdir(parents=True, exist_ok=True)
PORT = 8765
BASE = f'http://localhost:{PORT}/'
REAL = json.loads((ROOT / 'aovivo.json').read_text(encoding='utf-8'))


def undo_autosubs(d):
    d = copy.deepcopy(d)
    for x in d['entries'].values():
        pos = {p[0]: p for p in x['picks']}
        for i, o in x['auto']:      # repõe o onze escolhido: quem entrou volta ao banco
            pos[i][1], pos[o][1] = pos[o][1], pos[i][1]
        x['picks'].sort(key=lambda p: p[1])
    return d


def live_sim(d):
    """Jornada a meio: os 3 últimos jogos a decorrer (60'), os 3 anteriores por começar, sem bónus confirmado."""
    d = copy.deepcopy(d)
    fx = d['fixtures']
    playing, pending = fx[-3:], fx[-6:-3]
    for f in playing:
        f.update(min=60, d=False, f=False, b=False)
    for f in pending:
        f.update(s=False, d=False, f=False, b=False, hs=None, **{'as': None}, min=0)
    tp = {t for f in playing for t in (f['h'], f['a'])}
    tn = {t for f in pending for t in (f['h'], f['a'])}
    for a in d['el'].values():
        if a[4] in tp:
            a[7] = 2; a[2] = 1 if a[3] > 25 else 0
        elif a[4] in tn:
            a[7] = 1; a[0] = 0; a[1] = 0; a[2] = 0
    d['finished'] = d['checked'] = False
    return d


CHECK = '''() => ({
  overflow: document.documentElement.scrollWidth > window.innerWidth + 1,
  empties: ['av-equipa','av-h2h','av-liga'].filter(i => !document.getElementById(i).textContent.trim()),
  meta: document.getElementById('av-nav-meta').innerText,
})'''


async def run(pw, variant, data, widths=((1280, 900), (390, 844))):
    out = []
    b = await pw.chromium.launch()
    for w, h in widths:
        pg = await b.new_page(viewport={'width': w, 'height': h})
        await pg.add_init_script("try{localStorage.setItem('fpl-tour-done','\"off\"')}catch(e){}")
        errs = []
        pg.on('pageerror', lambda e: errs.append('PAGEERR ' + str(e)))
        pg.on('console', lambda m: errs.append('CONSOLE ' + m.text) if m.type in ('error', 'warning') and 'fonts' not in m.text else None)
        body = json.dumps(data)
        await pg.route('**/aovivo.json*', lambda r: r.fulfill(status=200, content_type='application/json', body=body))
        await pg.goto(BASE + '?live=1#aovivo-equipa'); await pg.wait_for_timeout(1500)
        res = await pg.evaluate('''() => {
          const E = Object.keys(AV.d.entries).map(Number);
          return {mism: E.map(e => [AV.d.entries[e].name, avTeam(e).gross, AV.d.entries[e].api, avTeam(e).subs.map(([b,o]) => b.name+'<'+o.name)]).filter(x => x[1] !== x[2]),
                  bruno: (() => { const t = avTeam(5191766); return [t.gross, t.net, t.subs.map(([b,o]) => b.name+' por '+o.name), t.active && t.active.name, t.playing, t.toPlay]; })(),
                  marco: (() => { const t = avTeam(1973102); return [t.gross, t.net, t.subs.map(([b,o]) => b.name+' por '+o.name), t.active && t.active.name, t.playing, t.toPlay]; })(),
                  top3: avLeague().slice(0,3).map(r => [r.totalR, r.x.player, r.t.net, r.total])}; }''')
        for mgr in ('bruno', 'marco'):
            await pg.click(f'.mswitch-btn[data-manager="{mgr}"]'); await pg.wait_for_timeout(150)
            for sub in ('equipa', 'h2h', 'liga'):
                await pg.evaluate(f"showView('aovivo','{sub}')"); await pg.wait_for_timeout(150)
                c = await pg.evaluate(CHECK)
                if c['overflow']: errs.append(f'OVERFLOW {w} {mgr} {sub}')
                if c['empties']: errs.append(f'EMPTY {w} {mgr} {sub} {c["empties"]}')
                if mgr == 'bruno' or sub == 'equipa':
                    await pg.screenshot(path=str(SHOTS / f'av-{variant}-{w}-{mgr}-{sub}.png'), full_page=True)
        out.append((w, res, c['meta'], errs))
        await pg.close()
    await b.close()
    return out


async def main():
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'], cwd=ROOT,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    try:
        async with async_playwright() as pw:
            for name, data in (('real', REAL), ('semauto', undo_autosubs(REAL)), ('meio', live_sim(REAL))):
                for w, res, meta, errs in await run(pw, name, data):
                    print(f'== {name} {w}: mismatches={len(res["mism"])} meta={meta!r}')
                    for m in res['mism'][:6]: print('   diff', m)
                    if w == 1280:
                        print('   bruno', res['bruno']); print('   marco', res['marco']); print('   top3', res['top3'])
                    print('   ERRORS', len(errs)); [print('     ', e) for e in errs[:10]]
    finally:
        srv.terminate()

asyncio.run(main())
