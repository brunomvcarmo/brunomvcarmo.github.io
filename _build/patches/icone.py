"""Ícone da app para o ecrã principal do telemóvel (V58): desenha-o em HTML e grava PNG com o Playwright.
Uso (a partir da raiz):  py -X utf8 _build/patches/icone.py <desenho>   (Linux: python3) → icons/*.png
                         py -X utf8 _build/patches/icone.py amostra [desenhos…] → _build/shots/icones.png (lado a lado)
Desenhos: ver D (o escolhido em 8 nov 2026 foi fusao-a-3d: FPL, corte diagonal roxo, bola 3D com rastos).
import math, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'icons'
FONT = '<link href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@700;800&display=block" rel="stylesheet">'
BALL = """<svg class="ball" viewBox="-50 -50 100 100"><circle r="47" fill="#fff"/>
<polygon points="0,-17 16.2,-5.3 10,13.8 -10,13.8 -16.2,-5.3" fill="#1C1528"/>
<g stroke="#1C1528" stroke-width="3" fill="none"><path d="M0,-17 L0,-33 M16.2,-5.3 L31.4,-10.2 M10,13.8 L19.4,26.7 M-10,13.8 L-19.4,26.7 M-16.2,-5.3 L-31.4,-10.2"/></g>
<g fill="#1C1528"><path d="M-12,-46 L12,-46 L8,-35 L-8,-35Z"/><path d="M44,-14 L37,7 L30,-1 L34,-12Z"/><path d="M27,38 L9,46 L13,35 L22,30Z"/><path d="M-27,38 L-9,46 L-13,35 L-22,30Z"/><path d="M-44,-14 L-37,7 L-30,-1 L-34,-12Z"/></g>
<circle r="47" fill="none" stroke="#1C1528" stroke-width="2"/></svg>"""
BASE = ".i{width:512px;height:512px;position:relative;overflow:hidden;font-family:'Barlow Semi Condensed',sans-serif}"
D = {
    # 1. o primeiro: bola branca e FPL em fundo roxo
    'bola': (".i{background:radial-gradient(circle at 30% 20%,#7A43A8 0,#5B2C83 45%,#37194F 100%)}"
             ".ball{position:absolute;left:156px;top:70px;width:200px;height:200px}"
             ".t{position:absolute;left:0;right:0;top:268px;text-align:center;color:#fff;font-size:150px;font-weight:700;letter-spacing:4px;line-height:1}"
             ".bar{position:absolute;left:176px;right:176px;top:424px;height:14px;border-radius:7px;background:#00FF87}",
             BALL + '<div class="t">FPL</div><div class="bar"></div>'),
    # 2. escudo de clube com BFC e uma estrela
    'escudo': (".i{background:linear-gradient(135deg,#05F0FF 0%,#00FF87 100%)}"
               ".sh{position:absolute;left:96px;top:66px;width:320px;height:380px}"
               ".t{position:absolute;left:0;right:0;top:196px;text-align:center;color:#fff;font-size:128px;font-weight:800;letter-spacing:2px;line-height:1}"
               ".s{position:absolute;left:0;right:0;top:330px;text-align:center;color:#00FF87;font-size:44px;font-weight:700;letter-spacing:10px}",
               '<svg class="sh" viewBox="0 0 320 380"><path d="M160 6 L310 50 L310 170 C310 270 240 340 160 374 C80 340 10 270 10 170 L10 50 Z" fill="#37194F" stroke="#fff" stroke-width="10"/>'
               '<polygon points="160,62 172,96 208,96 179,117 190,151 160,130 130,151 141,117 112,96 148,96" fill="#00FF87"/></svg>'
               '<div class="t">BFC</div><div class="s">FPL</div>'),
    # 3. relvado visto de cima (riscas e linhas) com FPL
    'relvado': (".i{background:repeating-linear-gradient(90deg,#1E9E4A 0 64px,#23B054 64px 128px)}"
                ".ln{position:absolute;inset:0}"
                ".t{position:absolute;left:0;right:0;top:186px;text-align:center;color:#fff;font-size:150px;font-weight:800;letter-spacing:4px;line-height:1;"
                "text-shadow:0 6px 0 #37194F,0 0 18px rgba(0,0,0,.25)}",
                '<svg class="ln" viewBox="0 0 512 512"><g fill="none" stroke="#fff" stroke-width="10" opacity=".85">'
                '<rect x="34" y="34" width="444" height="444" rx="6"/><line x1="256" y1="34" x2="256" y2="478"/><circle cx="256" cy="256" r="92"/>'
                '<rect x="34" y="166" width="70" height="180"/><rect x="408" y="166" width="70" height="180"/></g>'
                '<circle cx="256" cy="256" r="12" fill="#fff"/></svg><div class="t">FPL</div>'),
    # 4. cores da FPL: degradê ciano-verde, FPL em roxo e bola pequena
    'gradiente': (".i{background:linear-gradient(160deg,#05F0FF 0%,#00FF87 70%)}"
                  ".ball{position:absolute;left:316px;top:300px;width:130px;height:130px;filter:drop-shadow(0 6px 8px rgba(55,25,79,.35))}"
                  ".t{position:absolute;left:52px;top:96px;color:#37194F;font-size:210px;font-weight:800;line-height:.9;letter-spacing:-2px}"
                  ".s{position:absolute;left:60px;top:300px;color:#37194F;font-size:46px;font-weight:700;line-height:1.15}",
                  BALL + '<div class="t">FPL</div><div class="s">Brunorussia<br>FC</div>'),
    # 5. monograma B com a bola como ponto
    'monograma': (".i{background:radial-gradient(circle at 70% 25%,#4A2470 0,#1C1528 75%)}"
                  ".t{position:absolute;left:96px;top:40px;color:#fff;font-size:440px;font-weight:800;line-height:1}"
                  ".ball{position:absolute;left:330px;top:318px;width:118px;height:118px}"
                  ".bar{position:absolute;left:112px;top:446px;width:190px;height:16px;border-radius:8px;background:#00FF87}",
                  '<div class="t">B</div>' + BALL + '<div class="bar"></div>'),
}
# bola com volume (sombra por baixo e brilho), para as variantes do estilo "gradiente"
BALL3 = BALL.replace('<circle r="47" fill="none" stroke="#1C1528" stroke-width="2"/></svg>',
                     '<defs><radialGradient id="sh" cx="35%" cy="30%" r="75%"><stop offset="55%" stop-color="#000" stop-opacity="0"/>'
                     '<stop offset="100%" stop-color="#37194F" stop-opacity=".35"/></radialGradient></defs>'
                     '<circle r="47" fill="url(#sh)"/><ellipse cx="-17" cy="-24" rx="13" ry="7" fill="#fff" opacity=".7" transform="rotate(-35 -17 -24)"/>'
                     '<circle r="47" fill="none" stroke="#1C1528" stroke-width="2"/></svg>')
G = "background:linear-gradient(150deg,#05F0FF 0%,#00FF87 62%,#00E070 100%)"
SHEEN = '<div style="position:absolute;inset:0;background:radial-gradient(circle at 18% 8%,rgba(255,255,255,.55) 0,rgba(255,255,255,0) 45%)"></div>'
D.update({
    # 6. a mesma ideia mais limpa: luz no canto, bola com volume a sair pelo canto
    'g-sombra': (f".i{{{G}}}"
                 ".ball{position:absolute;left:300px;top:292px;width:250px;height:250px;filter:drop-shadow(-6px 10px 14px rgba(55,25,79,.4))}"
                 ".t{position:absolute;left:48px;top:58px;color:#37194F;font-size:230px;font-weight:800;line-height:.86;letter-spacing:-4px}"
                 ".s{position:absolute;left:56px;top:268px;color:#37194F;font-size:40px;font-weight:700;letter-spacing:5px;text-transform:uppercase;line-height:1.2;opacity:.85}",
                 SHEEN + '<div class="t">FPL</div><div class="s">Brunorussia<br>FC</div>' + BALL3),
    # 7. FPL ao centro e faixa roxa em baixo com o nome da equipa
    'g-faixa': (f".i{{{G}}}"
                ".ball{position:absolute;left:206px;top:40px;width:100px;height:100px;filter:drop-shadow(0 6px 8px rgba(55,25,79,.35))}"
                ".t{position:absolute;left:0;right:0;top:142px;text-align:center;color:#37194F;font-size:200px;font-weight:800;line-height:1;letter-spacing:-2px}"
                ".band{position:absolute;left:0;right:0;bottom:0;height:126px;background:#37194F}"
                ".s{position:absolute;left:0;right:0;bottom:36px;text-align:center;color:#00FF87;font-size:46px;font-weight:700;letter-spacing:6px;text-transform:uppercase}",
                SHEEN + BALL3 + '<div class="t">FPL</div><div class="band"></div><div class="s">Brunorussia FC</div>'),
    # 8. bola em movimento (rastos) por cima de FPL
    'g-movimento': (f".i{{{G}}}"
                    ".ball{position:absolute;left:300px;top:58px;width:150px;height:150px;filter:drop-shadow(0 8px 10px rgba(55,25,79,.35))}"
                    ".tr{position:absolute;height:14px;border-radius:7px;background:#37194F}"
                    ".t{position:absolute;left:44px;top:232px;color:#37194F;font-size:220px;font-weight:800;line-height:.86;letter-spacing:-4px}"
                    ".s{position:absolute;left:52px;top:432px;color:#37194F;font-size:34px;font-weight:700;letter-spacing:6px;text-transform:uppercase;opacity:.85}",
                    SHEEN + '<div class="tr" style="left:120px;top:96px;width:150px;opacity:.9"></div><div class="tr" style="left:70px;top:130px;width:200px;opacity:.6"></div>'
                    '<div class="tr" style="left:150px;top:164px;width:120px;opacity:.35"></div>' + BALL3 + '<div class="t">FPL</div><div class="s">Brunorussia FC</div>'),
    # 9. corte na diagonal: em cima as cores da FPL, em baixo roxo com o nome
    'g-diagonal': (f".i{{{G}}}"
                   ".cut{position:absolute;inset:0;background:#37194F;clip-path:polygon(0 74%,100% 50%,100% 100%,0 100%)}"
                   ".ball{position:absolute;left:340px;top:188px;width:130px;height:130px;filter:drop-shadow(0 8px 10px rgba(28,21,40,.45))}"
                   ".t{position:absolute;left:44px;top:50px;color:#37194F;font-size:220px;font-weight:800;line-height:.86;letter-spacing:-4px}"
                   ".s{position:absolute;left:52px;top:408px;color:#fff;font-size:40px;font-weight:700;letter-spacing:5px;text-transform:uppercase;line-height:1.15}"
                   ".s b{color:#00FF87}",
                   SHEEN + '<div class="cut"></div><div class="t">FPL</div>' + BALL3 + '<div class="s">Brunorussia <b>FC</b></div>'),
    # 10. bola gigante em marca-d'água por trás, FPL nítido à frente
    'g-marca': (f".i{{{G}}}"
                ".wm{position:absolute;left:150px;top:-40px;width:520px;height:520px;opacity:.16}"
                ".t{position:absolute;left:0;right:0;top:150px;text-align:center;color:#37194F;font-size:230px;font-weight:800;line-height:.86;letter-spacing:-4px}"
                ".line{position:absolute;left:150px;right:150px;top:366px;height:10px;border-radius:5px;background:#37194F}"
                ".s{position:absolute;left:0;right:0;top:394px;text-align:center;color:#37194F;font-size:38px;font-weight:700;letter-spacing:6px;text-transform:uppercase}",
                BALL.replace('class="ball"', 'class="wm"').replace('fill="#fff"', 'fill="none"').replace('#1C1528', '#37194F') + SHEEN
                + '<div class="t">FPL</div><div class="line"></div><div class="s">Brunorussia FC</div>'),
})


def bola_real(cls='ball', uid='b'):
    """Bola clássica (icosaedro truncado) vista de frente: pentágono ao centro, 5 pentágonos à volta encolhidos
    pela curvatura, costuras dos hexágonos, sombra esférica e brilho. viewBox -50..50."""
    import math
    def pt(cx, cy, ang, d): return cx + d * math.cos(math.radians(ang)), cy + d * math.sin(math.radians(ang))
    def pent(cx, cy, r, point_to, k=1.0):
        # pentágono com um vértice virado para point_to; k < 1 encolhe na direção do raio (efeito de curvatura)
        out = []
        for i in range(5):
            a = math.radians(point_to + 72 * i)
            x, y = r * math.cos(a), r * math.sin(a)
            rad = math.radians(point_to)
            u = x * math.cos(rad) + y * math.sin(rad); v = -x * math.sin(rad) + y * math.cos(rad)
            u *= k
            out.append((cx + u * math.cos(rad) - v * math.sin(rad), cy + u * math.sin(rad) + v * math.cos(rad)))
        return out
    f = lambda P: ' '.join(f'{x:.2f},{y:.2f}' for x, y in P)
    C = pent(0, 0, 15, -90)
    outer = []
    for i in range(5):
        a = -90 + 72 * i
        cx, cy = pt(0, 0, a, 42)
        outer.append(pent(cx, cy, 17, a + 180, 0.62))
    seams = []
    for i in range(5):
        seams.append((C[i], outer[i][0]))                       # vértice do centro → vértice interior do pentágono de fora
        seams.append((outer[i][1], outer[(i + 1) % 5][4]))      # entre pentágonos vizinhos (fecha os hexágonos)
        for j in (2, 3):                                        # para fora, até à borda
            x, y = outer[i][j]; d = math.hypot(x, y)
            seams.append(((x, y), (x / d * 52, y / d * 52)))
    # costuras ligeiramente curvas (para fora), como numa esfera
    def q(a, b):
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        return f'M{a[0]:.2f},{a[1]:.2f} Q{mx * 1.07:.2f},{my * 1.07:.2f} {b[0]:.2f},{b[1]:.2f}'
    seam_d = ' '.join(q(a, b) for a, b in seams)
    return (f'<svg class="{cls}" viewBox="-50 -50 100 100"><defs>'
            f'<radialGradient id="{uid}f" cx="38%" cy="32%" r="70%"><stop offset="0" stop-color="#fff"/><stop offset=".6" stop-color="#F3F1F6"/><stop offset="1" stop-color="#B9B2C6"/></radialGradient>'
            f'<radialGradient id="{uid}p" cx="40%" cy="35%" r="80%"><stop offset="0" stop-color="#3A2D4F"/><stop offset="1" stop-color="#140E1E"/></radialGradient>'
            f'<radialGradient id="{uid}s" cx="38%" cy="32%" r="68%"><stop offset=".55" stop-color="#1C1528" stop-opacity="0"/><stop offset="1" stop-color="#1C1528" stop-opacity=".38"/></radialGradient>'
            f'<clipPath id="{uid}c"><circle r="47"/></clipPath></defs>'
            f'<circle r="47" fill="url(#{uid}f)"/>'
            f'<g clip-path="url(#{uid}c)"><path d="{seam_d}" stroke="#7D748C" stroke-width="1.1" stroke-linecap="round" fill="none"/>'
            f'<polygon points="{f(C)}" fill="url(#{uid}p)" stroke="#140E1E" stroke-width="1" stroke-linejoin="round"/>'
            + ''.join(f'<polygon points="{f(P)}" fill="url(#{uid}p)" stroke="#140E1E" stroke-width="1" stroke-linejoin="round"/>' for P in outer)
            + f'<circle r="47" fill="url(#{uid}s)"/></g>'
            f'<ellipse cx="-16" cy="-25" rx="14" ry="7" fill="#fff" opacity=".75" transform="rotate(-35 -16 -25)"/>'
            f'<circle r="46.5" fill="none" stroke="#1C1528" stroke-width="1.6"/></svg>')


def bola_moderna(estilo='app', cls='ball', uid='m'):
    """Bola moderna original (painéis curvos em hélice, como as bolas de competição recentes — desenho nosso, não o
    oficial de nenhuma prova). estilo 'app': roxo com friso verde; 'estrelas': azul-noite com friso prateado e estrelas."""
    c1, c2, edge = ('#5B2C83', '#2A1240', '#00FF87') if estilo == 'app' else ('#22336E', '#0B1233', '#C9D3E6')
    blade = 'M2,-4 C14,-12 22,-28 17,-52 L31,-50 C35,-28 25,-8 6,1 Z'
    lip = 'M6,1 C25,-8 35,-28 31,-50'
    star = lambda x, y, r: 'M' + ' L'.join(f'{x + (r if i % 2 == 0 else r * .45) * math.cos(math.radians(-90 + 36 * i)):.2f},'
                                           f'{y + (r if i % 2 == 0 else r * .45) * math.sin(math.radians(-90 + 36 * i)):.2f}' for i in range(10)) + 'Z'
    stars = ''.join(f'<path d="{star(-30, -16, 4.5)}" fill="#fff" transform="rotate({r})"/>' for r in (0, 120, 240)) if estilo == 'estrelas' else ''
    seam = 'M0,0 C-8,-16 -8,-34 2,-52'
    return (f'<svg class="{cls}" viewBox="-50 -50 100 100"><defs>'
            f'<radialGradient id="{uid}f" cx="38%" cy="32%" r="70%"><stop offset="0" stop-color="#fff"/><stop offset=".6" stop-color="#F2F0F5"/><stop offset="1" stop-color="#B4ADC2"/></radialGradient>'
            f'<linearGradient id="{uid}p" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>'
            f'<radialGradient id="{uid}s" cx="38%" cy="32%" r="68%"><stop offset=".5" stop-color="#1C1528" stop-opacity="0"/><stop offset="1" stop-color="#1C1528" stop-opacity=".4"/></radialGradient>'
            f'<clipPath id="{uid}c"><circle r="47"/></clipPath></defs>'
            f'<circle r="47" fill="url(#{uid}f)"/><g clip-path="url(#{uid}c)">'
            + ''.join(f'<path d="{seam}" stroke="#A69FB3" stroke-width="1" fill="none" transform="rotate({r})"/>' for r in range(0, 360, 60))
            + ''.join(f'<g transform="rotate({r})"><path d="{blade}" fill="url(#{uid}p)"/><path d="{lip}" stroke="{edge}" stroke-width="2.6" fill="none" stroke-linecap="round"/></g>' for r in (0, 120, 240))
            + stars
            + f'<circle r="47" fill="url(#{uid}s)"/></g>'
            f'<ellipse cx="-17" cy="-26" rx="15" ry="7" fill="#fff" opacity=".7" transform="rotate(-35 -17 -26)"/>'
            f'<circle r="46.5" fill="none" stroke="#1C1528" stroke-width="1.6"/></svg>')



def bola_3d(cls='ball', uid='r', rx=24, ry=-14, rz=8, pent='#1C1528'):
    """Bola clássica verdadeira: icosaedro truncado (12 pentágonos e 20 hexágonos) insuflado para uma esfera,
    rodado em 3D e projetado, com luz em cada painel, costuras, sombra e brilho. viewBox -50..50."""
    phi = (1 + 5 ** .5) / 2
    V = [(0, a, b * phi) for a in (-1, 1) for b in (-1, 1)] + [(a, b * phi, 0) for a in (-1, 1) for b in (-1, 1)] + [(a * phi, 0, b) for a in (-1, 1) for b in (-1, 1)]
    d2 = lambda p, q: sum((x - y) ** 2 for x, y in zip(p, q))
    nb = {i: [j for j in range(12) if j != i and abs(d2(V[i], V[j]) - 4) < 1e-6] for i in range(12)}
    lerp = lambda p, q, t: tuple(x + (y - x) * t for x, y in zip(p, q))
    faces = []
    for i in range(12):                                   # pentágonos: um por vértice do icosaedro
        v = V[i]; n = sum(x * x for x in v) ** .5; z = tuple(x / n for x in v)
        ref = [x - y for x, y in zip(V[nb[i][0]], v)]
        def ang(j):
            w = [x - y for x, y in zip(V[j], v)]
            e1 = ref; e2 = (z[1] * e1[2] - z[2] * e1[1], z[2] * e1[0] - z[0] * e1[2], z[0] * e1[1] - z[1] * e1[0])
            return math.atan2(sum(a * b for a, b in zip(w, e2)), sum(a * b for a, b in zip(w, e1)))
        faces.append(('p', [lerp(v, V[j], 1 / 3) for j in sorted(nb[i], key=ang)]))
    for i in range(12):                                   # hexágonos: um por face do icosaedro
        for j in nb[i]:
            for k in nb[i]:
                if i < j < k and k in nb[j]:
                    a, b, c = V[i], V[j], V[k]
                    faces.append(('h', [lerp(a, b, 1 / 3), lerp(a, b, 2 / 3), lerp(b, c, 1 / 3), lerp(b, c, 2 / 3), lerp(c, a, 1 / 3), lerp(c, a, 2 / 3)]))
    def rot(p):
        x, y, z = p
        for axis, deg in (('x', rx), ('y', ry), ('z', rz)):
            c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
            if axis == 'x': y, z = y * c - z * s_, y * s_ + z * c
            elif axis == 'y': x, z = x * c + z * s_, -x * s_ + z * c
            else: x, y = x * c - y * s_, x * s_ + y * c
        return x, y, z
    unit = lambda p: tuple(x / sum(y * y for y in p) ** .5 for x in p)
    L = unit((-.45, -.55, .7))
    def limb(p):                                          # o que fica atrás encosta à borda (não aparece por dentro)
        x, y, z = p
        if z >= 0: return p
        r = (x * x + y * y) ** .5 or 1
        return x / r, y / r, z
    out = []
    for kind, P in faces:
        pts = []
        for m in range(len(P)):                           # arestas curvas: subdividir e empurrar para a esfera
            for t in range(6):
                pts.append(limb(rot(unit(lerp(P[m], P[(m + 1) % len(P)], t / 6)))))
        cz = sum(p[2] for p in pts) / len(pts)
        if cz < -.25: continue
        n = unit(rot(unit(tuple(sum(p[i] for p in P) / len(P) for i in range(3)))))
        lit = max(0, sum(a * b for a, b in zip(n, L)))
        if kind == 'h':
            g = int(204 + 51 * lit); fill = f'rgb({g},{g},{min(255, g + 6)})'
        else:
            fill = pent; 
        out.append((cz, f'<polygon points="{" ".join(f"{p[0] * 47:.2f},{p[1] * 47:.2f}" for p in pts)}" fill="{fill}"'
                        f'{f" opacity=" + chr(34) + str(round(.82 + .18 * lit, 2)) + chr(34) if kind == "p" else ""} stroke="#6E6680" stroke-width=".7" stroke-linejoin="round"/>'))
    body = ''.join(x for _, x in sorted(out))
    return (f'<svg class="{cls}" viewBox="-50 -50 100 100"><defs>'
            f'<radialGradient id="{uid}s" cx="36%" cy="30%" r="72%"><stop offset=".55" stop-color="#1C1528" stop-opacity="0"/><stop offset="1" stop-color="#1C1528" stop-opacity=".35"/></radialGradient>'
            f'<radialGradient id="{uid}h" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
            f'<clipPath id="{uid}c"><circle r="47"/></clipPath></defs>'
            f'<circle r="47" fill="#fff"/><g clip-path="url(#{uid}c)">{body}<circle r="47" fill="url(#{uid}s)"/></g>'
            f'<ellipse cx="-16" cy="-24" rx="16" ry="9" fill="url(#{uid}h)" transform="rotate(-35 -16 -24)"/>'
            f'<circle r="46.6" fill="none" stroke="#1C1528" stroke-width="1.4"/></svg>')

# fusão do 4 (bola em movimento) com o 5 (corte diagonal); os rastos seguem a inclinação do corte (≈13,5°)
ANG = -13.5


def fusao(trail, name_color, ball_px, ball_xy, fpl_top=46, big_name=False, ball=None):
    bx, by = ball_xy
    trails = ''.join(f'<div class="tr" style="left:{x}px;top:{y}px;width:{w}px;opacity:{o}"></div>' for x, y, w, o in trail)
    return (f".i{{{G}}}"
            ".cut{position:absolute;inset:0;background:linear-gradient(160deg,#4A2470,#2A1240);clip-path:polygon(0 76%,100% 52%,100% 100%,0 100%)}"
            f".tr{{position:absolute;height:13px;border-radius:7px;background:#37194F;transform:rotate({ANG}deg);transform-origin:100% 50%}}"
            f".ball{{position:absolute;left:{bx}px;top:{by}px;width:{ball_px}px;height:{ball_px}px;filter:drop-shadow(-4px 12px 12px rgba(28,21,40,.45))}}"
            f".t{{position:absolute;left:42px;top:{fpl_top}px;color:#37194F;font-size:224px;font-weight:800;line-height:.86;letter-spacing:-5px}}"
            f".s{{position:absolute;left:50px;top:{404 if big_name else 418}px;color:#fff;font-size:{44 if big_name else 38}px;font-weight:700;letter-spacing:5px;text-transform:uppercase;line-height:1.1}}"
            f".s b{{color:{name_color}}}",
            SHEEN + '<div class="cut"></div><div class="t">FPL</div>' + trails + (ball or bola_real()) + '<div class="s">Brunorussia <b>FC</b></div>')


D.update({
    'bola-3d': (".i{background:#f4f1f8}.ball{position:absolute;left:56px;top:56px;width:400px;height:400px;filter:drop-shadow(0 16px 16px rgba(28,21,40,.3))}", bola_3d()),
    'bola-3d-roxa': (".i{background:#f4f1f8}.ball{position:absolute;left:56px;top:56px;width:400px;height:400px;filter:drop-shadow(0 16px 16px rgba(28,21,40,.3))}", bola_3d(pent='#37194F')),
    'bola-app': (".i{background:#f4f1f8}.ball{position:absolute;left:56px;top:56px;width:400px;height:400px;filter:drop-shadow(0 16px 16px rgba(28,21,40,.3))}", bola_moderna('app')),
    'bola-estrelas': (".i{background:#f4f1f8}.ball{position:absolute;left:56px;top:56px;width:400px;height:400px;filter:drop-shadow(0 16px 16px rgba(28,21,40,.3))}", bola_moderna('estrelas')),
    'bola-nova': (".i{background:#f4f1f8}.ball{position:absolute;left:56px;top:56px;width:400px;height:400px;filter:drop-shadow(0 16px 16px rgba(28,21,40,.3))}",
                  bola_real()),
    # A: bola em cima do corte, rastos roxos por cima do corte
    'fusao-a': fusao([(196, 222, 140, .95), (150, 250, 186, .6), (216, 278, 120, .32)], '#00FF87', 170, (316, 168)),
    'fusao-a-3d': fusao([(196, 222, 140, .95), (150, 250, 186, .6), (216, 278, 120, .32)], '#00FF87', 170, (316, 168), ball=bola_3d()),
    'fusao-a-3d-roxa': fusao([(196, 222, 140, .95), (150, 250, 186, .6), (216, 278, 120, .32)], '#00FF87', 170, (316, 168), ball=bola_3d(pent='#37194F')),
    'fusao-a-app': fusao([(196, 222, 140, .95), (150, 250, 186, .6), (216, 278, 120, .32)], '#00FF87', 170, (316, 168), ball=bola_moderna('app')),
    'fusao-a-estrelas': fusao([(196, 222, 140, .95), (150, 250, 186, .6), (216, 278, 120, .32)], '#00FF87', 170, (316, 168), ball=bola_moderna('estrelas')),
    # B: bola maior a sair pela direita, rastos mais longos
    'fusao-b': fusao([(170, 214, 170, .95), (120, 246, 220, .6), (196, 278, 144, .32)], '#00FF87', 206, (326, 140)),
    # C: bola mais pequena e mais alta (ao lado do L), nome maior
    'fusao-c': fusao([(196, 222, 140, .95), (150, 250, 186, .6), (216, 278, 120, .32)], '#05F0FF', 170, (316, 168), big_name=True),
})


def html(k):
    css, body = D[k]
    return f'<!doctype html><html><head><meta charset="utf-8">{FONT}<style>html,body{{margin:0}}{BASE}{css}</style></head><body><div class="i">{body}</div></body></html>'


def amostra(b, ks=None):
    ks = ks or list(D)
    cells = ''.join(f'<div style="text-align:center;font:600 22px sans-serif;color:#1C1528"><div style="width:256px;height:256px;border-radius:56px;overflow:hidden;margin:0 auto 10px">'
                    f'<iframe srcdoc="{html(k).replace(chr(34), "&quot;")}" style="width:512px;height:512px;border:0;transform:scale(.5);transform-origin:0 0"></iframe></div>{n}. {k}</div>'
                    for n, k in enumerate(ks, 1))
    pg = b.new_page(viewport={'width': 1480, 'height': 340})
    pg.set_content(f'<body style="margin:0;padding:24px;background:#f4f1f8;display:flex;flex-wrap:wrap;gap:28px">{cells}</body>'); pg.wait_for_timeout(2500)
    out = ROOT / '_build' / 'shots' / 'icones.png'; out.parent.mkdir(parents=True, exist_ok=True)
    pg.screenshot(path=str(out), full_page=True); print('amostra em', out)


def gravar(b, k):
    OUT.mkdir(exist_ok=True)
    for size, name in ((512, 'icon-512.png'), (192, 'icon-192.png'), (180, 'apple-touch-icon.png'), (32, 'favicon-32.png')):
        pg = b.new_page(viewport={'width': 512, 'height': 512}, device_scale_factor=size / 512)
        pg.set_content(html(k)); pg.wait_for_timeout(1500)
        pg.locator('.i').screenshot(path=str(OUT / name)); pg.close()
    print(f'ícone "{k}" em', OUT)


if __name__ == '__main__':
    k = sys.argv[1] if len(sys.argv) > 1 else ''
    if k != 'amostra' and k not in D: print(__doc__); sys.exit(1)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        amostra(b, sys.argv[2:]) if k == 'amostra' else gravar(b, k)
        b.close()
