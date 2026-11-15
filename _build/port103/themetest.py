import sys, pathlib
from playwright.sync_api import sync_playwright
here = pathlib.Path(sys.argv[1]).resolve()
import tempfile; shots = pathlib.Path(tempfile.gettempdir()) / "port103-shots"; shots.mkdir(exist_ok=True)
src = here.read_text(encoding="utf-8")
if not src.lstrip().lower().startswith("<!doctype"):
    import tempfile; w = pathlib.Path(tempfile.gettempdir()) / "_p103_wrapped.html"
    w.write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>:root{color-scheme:light}body{margin:0}[hidden]{display:none!important}</style></head><body>' + src + '</body></html>', encoding="utf-8")
    here = w
errs = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for scheme in ["light", "dark"]:
        ctx = b.new_context(viewport={"width": 375, "height": 740}, device_scale_factor=2, is_mobile=True, has_touch=True, color_scheme=scheme)
        pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(here.as_uri()); pg.wait_for_timeout(800)
        bg = lambda: pg.evaluate("getComputedStyle(document.body).backgroundColor")
        box = pg.locator("#themeBtn").bounding_box()
        print(scheme, "start bg", bg(), "| button at x=%d..%d y=%d" % (box["x"], box["x"] + box["width"], box["y"]), pg.get_attribute("#themeBtn", "aria-label"))
        pg.click("#themeBtn"); pg.wait_for_timeout(200)
        print("   after click", bg(), pg.get_attribute("#themeBtn", "aria-label"))
        pg.screenshot(path=str(shots / f"theme-{scheme}-toggled.png"))
        pg.reload(); pg.wait_for_timeout(600)
        print("   after reload", bg(), "(remembered)")
        pg.click("#themeBtn"); pg.wait_for_timeout(200)
        print("   second click", bg())
        ctx.close()
    b.close()
print("JS errors:", errs or 0)
