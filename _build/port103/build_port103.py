"""Turn the artifact page into a standalone page for GitHub Pages (port103/)."""
import sys, json, pathlib
from playwright.sync_api import sync_playwright

src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
dest = pathlib.Path(sys.argv[2])
dest.mkdir(parents=True, exist_ok=True)

cut = src.index("</style>") + len("</style>")
head_part, body_part = src[:cut], src[cut:]

page = (
    '<!doctype html>\n<html lang="en">\n<head>\n'
    '<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    '<meta name="theme-color" content="#f7f9fd" media="(prefers-color-scheme: light)">\n'
    '<meta name="theme-color" content="#161c2c" media="(prefers-color-scheme: dark)">\n'
    '<meta name="apple-mobile-web-app-capable" content="yes">\n'
    '<meta name="mobile-web-app-capable" content="yes">\n'
    '<meta name="apple-mobile-web-app-title" content="PORT 103">\n'
    '<link rel="manifest" href="manifest.webmanifest">\n'
    '<link rel="icon" type="image/png" href="icon-192.png">\n'
    '<link rel="apple-touch-icon" href="icon-180.png">\n'
    '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
    'body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>\n'
    + head_part + '\n</head>\n<body>\n' + body_part.strip() + '\n</body>\n</html>\n'
)
(dest / "index.html").write_text(page, encoding="utf-8", newline="\n")

manifest = {
    "name": "Flashcards PORT 103",
    "short_name": "PORT 103",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "background_color": "#f7f9fd",
    "theme_color": "#6b8fdb",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}
(dest / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

ICON = """<html><body style="margin:0"><div id="i" style="width:512px;height:512px;background:#6b8fdb;position:relative;overflow:hidden;font-family:'Segoe UI',system-ui,sans-serif">
<div style="position:absolute;inset:0;background:radial-gradient(circle at 50% 50%, rgba(255,255,255,.22) 0 22%, transparent 23%) 0 0/64px 64px"></div>
<div style="position:absolute;left:96px;top:120px;width:300px;height:220px;background:#dfe8f8;border-radius:36px;transform:rotate(-8deg)"></div>
<div style="position:absolute;left:116px;top:150px;width:300px;height:220px;background:#fff;border-radius:36px;box-shadow:0 18px 40px rgba(30,50,100,.25);display:flex;align-items:center;justify-content:center;flex-direction:column">
<div style="font-size:92px;font-weight:800;color:#2f3a55;line-height:1">Olá</div>
<div style="font-size:38px;font-weight:600;color:#7f8aa3;margin-top:10px">hello</div></div></div></body></html>"""
with sync_playwright() as p:
    b = p.chromium.launch()
    for size in (512, 192, 180):
        pg = b.new_page(viewport={"width": 512, "height": 512}, device_scale_factor=size / 512)
        pg.set_content(ICON)
        pg.locator("#i").screenshot(path=str(dest / f"icon-{size}.png"))
        pg.close()
    b.close()
print("built", sorted(x.name for x in dest.iterdir()))
