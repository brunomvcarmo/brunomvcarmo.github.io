import sys, pathlib
from playwright.sync_api import sync_playwright

here = pathlib.Path(sys.argv[1]).resolve()
import tempfile; out = pathlib.Path(tempfile.gettempdir()) / "port103-shots"
out.mkdir(exist_ok=True)
SKEL = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><style>:root{color-scheme:light}body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style></head><body>'
import tempfile; page_html = pathlib.Path(tempfile.gettempdir()) / "_p103_wrapped.html"
src_txt = here.read_text(encoding="utf-8")
if src_txt.lstrip().lower().startswith("<!doctype"): page_html = here
else: page_html.write_text(SKEL + here.read_text(encoding="utf-8") + "</body></html>", encoding="utf-8")

errors = []
def check(page, label):
    ov = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    # elements wider than viewport
    wide = page.evaluate("""() => { const w = innerWidth; return [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.right > w + 1 || r.left < -1) && getComputedStyle(e).position !== 'absolute' && !e.closest('.back'); }).slice(0,5).map(e => e.tagName + '.' + e.className + '#' + e.id + ' ' + Math.round(e.getBoundingClientRect().right)); }""")
    # text overflowing card faces
    clip = page.evaluate("""() => [...document.querySelectorAll('.face')].map(f => f.scrollHeight - f.clientHeight)""")
    btm = page.evaluate("Math.round(document.getElementById('actions').getBoundingClientRect().bottom)"); print("   actions bottom:", btm, "of", page.viewport_size["height"])
    print(f"[{label}] horiz overflow={ov} wide={wide} faceOverflow={clip}")
    if ov > 0 or wide: errors.append(label + ': horizontal overflow')
    if any(c > 2 for c in clip): errors.append(label + f': card text clipped {clip}')

with sync_playwright() as p:
    b = p.chromium.launch()
    for scheme in ["light", "dark"]:
        ctx = b.new_context(viewport={"width": 375, "height": 740}, device_scale_factor=2, is_mobile=True, has_touch=True, color_scheme=scheme)
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("JS error: " + str(e)))
        pg.on("console", lambda m: m.type == "error" and errors.append("console: " + m.text))
        pg.goto(page_html.as_uri())
        pg.wait_for_timeout(1200)
        # Learn mode
        pg.click('[data-view="learn"]')
        pg.wait_for_timeout(300)
        check(pg, scheme + " learn")
        pg.screenshot(path=str(out / f"{scheme}-1-learn.png"))
        first = pg.text_content("#fWord")
        pg.tap("#card"); pg.wait_for_timeout(250)
        second = pg.text_content("#fWord")
        print("tap card advances:", first, "->", second)
        if first == second: errors.append("learn: tap did not advance")
        pg.click('[data-act="prev"]'); pg.wait_for_timeout(200)
        if pg.text_content("#fWord") != first: errors.append("learn: previous did not go back")
        if scheme == "light":
            # swipe left via touch events
            pg.evaluate("""() => { const c = document.getElementById('card'); const t = (x) => new Touch({identifier:1, target:c, clientX:x, clientY:200});
              c.dispatchEvent(new TouchEvent('touchstart', {touches:[t(300)], changedTouches:[t(300)], bubbles:true}));
              for (const x of [270, 220, 170, 120]) c.dispatchEvent(new TouchEvent('touchmove', {touches:[t(x)], changedTouches:[t(x)], bubbles:true}));
              c.dispatchEvent(new TouchEvent('touchend', {touches:[], changedTouches:[t(120)], bubbles:true})); }""")
            pg.wait_for_timeout(200)
            print("swipe advances:", pg.text_content("#stRound"))
            if pg.text_content("#fWord") == first: errors.append("learn: swipe did not advance")
            # long phrase in learn mode: jump to the restaurant phrases topic only
            pg.click("#topics summary"); pg.wait_for_timeout(200)
            pg.screenshot(path=str(out / "light-2-topics.png"), full_page=True)
            check(pg, "topics open")
            for g in ["casa", "comida", "compras", "viagens"]:
                pg.click(f'[data-grp="{g}"]'); pg.wait_for_timeout(100)
            print("summary text:", pg.text_content("#topicsTitle"))
            pg.click('.grp-more[data-g="comida"] summary'); pg.click('[data-cat="frasesrest"]'); pg.wait_for_timeout(200)
            print("summary text:", pg.text_content("#topicsTitle"))
            pg.screenshot(path=str(out / "light-2b-topics-partial.png"), full_page=True)
            pg.click("#doneBtn"); pg.wait_for_timeout(300)
            for _ in range(13): pg.click('[data-act="next"]')
            pg.wait_for_timeout(200)
            check(pg, "learn long phrase")
            pg.screenshot(path=str(out / "light-3-longphrase.png"))
            pg.click("#topics summary"); pg.click('[data-grp="casa"]'); pg.click('[data-grp="comida"]'); pg.click("#doneBtn")
            print("summary text:", pg.text_content("#topicsTitle"))
        # Flip mode
        pg.click('[data-view="flip"]'); pg.wait_for_timeout(300)
        check(pg, scheme + " flip front")
        pg.screenshot(path=str(out / f"{scheme}-4-flip-front.png"))
        pg.tap("#card"); pg.wait_for_timeout(600)
        check(pg, scheme + " flip back")
        pg.screenshot(path=str(out / f"{scheme}-5-flip-back.png"))
        before = pg.text_content("#stRound")
        pg.click('[data-act="yes"]'); pg.wait_for_timeout(300)
        print("after 'know':", before, "->", pg.text_content("#stRound"))
        if scheme == "light":
            # Type mode
            pg.click("#topics summary"); pg.click('[data-dir="en-pt"]'); pg.click("#doneBtn"); pg.click('[data-view="type"]'); pg.wait_for_timeout(300)
            pg.screenshot(path=str(out / "light-6-type.png"))
            pg.fill("#answer", "xyz"); pg.click("#checkBtn"); pg.wait_for_timeout(600)
            check(pg, "type wrong")
            pg.screenshot(path=str(out / "light-7-type-wrong.png"))
            pg.click('[data-act="next-bad"]'); pg.wait_for_timeout(300)
            # list tab
            pg.click('[data-view="list"]'); pg.wait_for_timeout(300)
            pg.fill("#search", "cozinha"); pg.wait_for_timeout(200)
            check(pg, "list")
            pg.screenshot(path=str(out / "light-8-list.png"))
            # finish a round of 10
            pg.click('[data-view="flip"]'); pg.click("#topics summary"); pg.select_option("#roundSize", "10"); pg.click("#doneBtn")
            for _ in range(10):
                pg.tap("#card"); pg.wait_for_timeout(50); pg.click('[data-act="yes"]')
            pg.wait_for_timeout(300)
            check(pg, "summary")
            pg.screenshot(path=str(out / "light-9-summary.png"))
        ctx.close()
    b.close()
print("ERRORS", len(errors))
for e in errors: print(" -", e)
