"""Tests the Practice area at phone size: every answer key, wrong/right feedback, repeats, shops board, prepositions."""
import sys, pathlib, tempfile
from playwright.sync_api import sync_playwright
here = pathlib.Path(sys.argv[1]).resolve()
tmp = pathlib.Path(tempfile.gettempdir()); shots = tmp / "port103-shots"; shots.mkdir(exist_ok=True)
src = here.read_text(encoding="utf-8")
if not src.lstrip().lower().startswith("<!doctype"):
    w = tmp / "_p103_wrapped.html"
    w.write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>:root{color-scheme:light}body{margin:0}[hidden]{display:none!important}</style></head><body>' + src + '</body></html>', encoding="utf-8")
    here = w
fails = []
def ok(c, m):
    print(("  ok   " if c else "  FAIL ") + m)
    if not c: fails.append(m)
def overflow(pg, label):
    ov = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    ok(ov <= 0, f"{label}: no sideways scrolling ({ov})")
def answer(pg, text):
    pg.fill("#pIn", text); pg.click("#pForm button[type=submit]"); pg.wait_for_timeout(80)
def fbclass(pg): return pg.get_attribute(".p-fb", "class")
with sync_playwright() as p:
    b = p.chromium.launch()
    for scheme in ["light", "dark"]:
        ctx = b.new_context(viewport={"width": 375, "height": 740}, device_scale_factor=2, is_mobile=True, has_touch=True, color_scheme=scheme)
        pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(here.as_uri()); pg.wait_for_timeout(700)
        pg.click('[data-view="practice"]'); pg.wait_for_timeout(200)
        pg.screenshot(path=str(shots / f"pr-{scheme}-0-home.png"))
        if scheme == "dark":
            pg.click('[data-p="prep"]'); pg.wait_for_timeout(200)
            pg.screenshot(path=str(shots / "pr-dark-prep.png")); overflow(pg, "dark prep")
            ok(not errs, "dark: no JS errors " + str(errs)); ctx.close(); continue
        print("Answer keys (every question accepts its own answer)")
        bad = pg.evaluate("""() => {
          const out = [];
          GITEMS.forEach(it => { if (ACT.grammar.check(it, it.a[0]).ok !== true) out.push('grammar ' + it.id); });
          GITEMS.filter(it => it.t === 'verbs').forEach(it => { if (ACT.grammar.check(it, it.pron.split(' / ')[0] + ' ' + it.a[0]).ok !== true) out.push('verb+pronoun ' + it.id); });
          HITEMS.forEach(it => it.rooms.forEach(r => { if (ACT.house.check(it, ROOMS[r].pt).ok !== true) out.push('house ' + it.pt + ' ' + r); if (ACT.house.check(it, (ROOMS[r].pt.startsWith('a ') ? 'na ' : 'no ') + ROOMS[r].pt.slice(2)).ok !== true) out.push('house na/no ' + it.pt); }));
          DITEMS.forEach(it => {
            it.a.forEach(x => { const r = it.full ? ACT.prep.check(it, it.subj + ' ' + it.verb + ' ' + x + '.') : ACT.prep.check(it, x); if (r.ok !== true) out.push('prep ' + it.id + ' ' + x); });
            if (!phraseBase(it.a[0])) out.push('prep base ' + it.id);
            const h = ACT.prep.hint(it); if ((h.match(/chip mini/g) || []).length !== 4) out.push('hint ' + it.id);
          });
          SCENES.forEach(sc => { if (/NaN|undefined/.test(sceneSvg(sc, []))) out.push('svg ' + sc.id); });
          return out; }""")
        ok(not bad, "all answer keys accepted, hints have 4 choices, pictures draw: " + (", ".join(bad[:8]) if bad else "ok"))
        counts = pg.evaluate("[GITEMS.length, HITEMS.length, SITEMS.length, DITEMS.length]")
        print("   questions: grammar %d, house %d, shops %d, prepositions %d" % tuple(counts))

        print("A. Grammar drills")
        pg.click('[data-p="grammar"]'); pg.wait_for_timeout(200)
        ok(pg.is_visible("#pIn") and not pg.is_visible(".p-fb"), "question shown, answer hidden until you try")
        html = pg.inner_html(".p-card"); first = pg.evaluate("PQ.queue[0]")
        ok(first["a"][0] not in pg.inner_text(".p-card").split(), "the card does not show the answer")
        pg.click('#pForm button[type=submit]'); pg.wait_for_timeout(100)
        ok(not pg.is_visible(".p-fb"), "an empty answer is not accepted")
        answer(pg, "xyz")
        ok("bad" in fbclass(pg) and "Correct:" in pg.inner_text(".p-fb"), "wrong answer → explanation + correct answer")
        pg.screenshot(path=str(shots / "pr-light-1-grammar-wrong.png")); overflow(pg, "grammar feedback")
        pg.click('[data-p="next"]'); pg.wait_for_timeout(100)
        ok(pg.evaluate("PQ.queue.some(x => x.id === '%s')" % first["id"]), "wrong question goes back in the queue")
        n = 0
        while pg.evaluate("PQ.queue.length") and n < 60:
            a = pg.evaluate("PQ.queue[0].a[0]"); answer(pg, a)
            if "ok" not in fbclass(pg): fails.append("grammar right answer rejected: " + a)
            pg.keyboard.press("Enter"); pg.wait_for_timeout(60); n += 1
        ok(pg.is_visible(".summary") and "1" in pg.inner_text(".summary"), "round ends with a summary listing what to review")
        pg.screenshot(path=str(shots / "pr-light-2-grammar-done.png"))
        pg.click('[data-gt="serestar"]'); pg.wait_for_timeout(100)
        ok(pg.evaluate("PQ.queue.every(x => x.t === 'serestar')"), "topic chip: only ser/estar questions")
        q = pg.evaluate("PQ.queue[0]"); acc = q["a"][0]
        if acc in ("está", "estão", "estás", "é", "são"):
            import unicodedata
            plainv = "".join(c for c in unicodedata.normalize("NFD", acc) if unicodedata.category(c) != "Mn")
            answer(pg, plainv); ok("warn" in fbclass(pg) and "accent" in pg.inner_text(".p-fb"), f"'{plainv}' instead of '{acc}' → 'check the accent'")
            pg.click('[data-p="next"]')

        print("B. Where in the house?")
        pg.click('[data-p="home"]'); pg.click('[data-p="house"]'); pg.wait_for_timeout(150)
        it = pg.evaluate("PQ.queue[0]")
        answer(pg, "na garagem" if "garagem" not in it["rooms"] else "na cozinha")
        ok("bad" in fbclass(pg) and it["en"] in pg.inner_text(".p-fb"), "wrong room → correct room + English translation")
        pg.click('[data-p="next"]')
        answer(pg, "blah"); ok("recognise" in pg.inner_text(".p-fb"), "unknown room name is explained"); pg.click('[data-p="next"]')
        it = pg.evaluate("PQ.queue[0]")
        pg.click('.p-help [data-fill="%s"]' % pg.evaluate("ROOMS['%s'].pt" % it["rooms"][0])); pg.click("#pForm button[type=submit]"); pg.wait_for_timeout(80)
        ok("ok" in fbclass(pg), "tapping a room name fills the answer and it is accepted")
        pg.screenshot(path=str(shots / "pr-light-3-house.png")); overflow(pg, "house")
        multi = pg.evaluate("HITEMS.filter(x => x.rooms.length > 1).length")
        ok(multi > 30, f"{multi} objects accept more than one room")

        print("C. Which shop?")
        pg.click('[data-p="home"]'); pg.click('[data-p="shops"]'); pg.wait_for_timeout(150)
        items = pg.evaluate("SH.items.map(x => ({id: x.id, shops: x.shops}))")
        ok(len(items) == 24, "24 items to sort")
        ok(pg.evaluate("Object.keys(SHOPS).every(k => SH.items.some(it => it.shops[0] === k))"), "every shop has items in the round")
        ok(pg.is_disabled('[data-p="shcheck"]'), "cannot check before sorting everything")
        pg.screenshot(path=str(shots / "pr-light-4-shops.png")); overflow(pg, "shops")
        wrong_id = items[0]["id"]
        for i, itx in enumerate(items):
            pg.click('.pool [data-item="%s"]' % itx["id"]); pg.wait_for_timeout(40)
            if i == 0: pg.screenshot(path=str(shots / "pr-light-5-sheet.png"))
            target = "correios" if (i == 0 and "correios" not in itx["shops"]) else ("padaria" if i == 0 else itx["shops"][0])
            pg.click('#sheet [data-pick="%s"]' % target); pg.wait_for_timeout(30)
        ok(not pg.is_disabled('[data-p="shcheck"]'), "check button turns on when all items are sorted")
        pg.click('[data-p="shcheck"]'); pg.wait_for_timeout(150)
        txt = pg.inner_text(".summary")
        ok("23 of 24" in txt and "You chose" in txt, "one wrong item is corrected with the right shop")
        pg.screenshot(path=str(shots / "pr-light-6-shops-checked.png"), full_page=True)
        pg.click('[data-p="shnew"]'); pg.wait_for_timeout(100)
        ok(pg.evaluate("SH.items.some(x => x.id === '%s')" % wrong_id), "next round brings back the item I got wrong")

        print("D. Where is it? (prepositions)")
        pg.click('[data-p="home"]'); pg.click('[data-p="prep"]'); pg.wait_for_timeout(150)
        pg.screenshot(path=str(shots / "pr-light-7-prep.png")); overflow(pg, "prepositions")
        ok(pg.is_visible(".scene-svg"), "the room picture is shown")
        it = pg.evaluate("PQ.queue[0]")
        u = pg.evaluate("(() => { const it = PQ.queue[0]; const s = splitPrep(it.a[0]); return s.base === 'entre' ? null : s.base + ' ' + it.art; })()")
        if u:
            answer(pg, u); ok("contract" in pg.inner_text(".p-fb"), f"'{u}' → asks to contract it")
            pg.click('[data-p="next"]')
        it = pg.evaluate("PQ.queue[0]")
        ok(not pg.is_visible(".p-help"), "no multiple choice unless I ask")
        pg.click('[data-p="hint"]'); pg.wait_for_timeout(80)
        ok(pg.locator(".p-help .chip").count() == 4, "hint shows 4 choices")
        n = 0
        while pg.evaluate("PQ.queue.length") and n < 40:
            it = pg.evaluate("PQ.queue[0]")
            if it.get("full"):
                answer(pg, it["a"][0]); ok("bad" in fbclass(pg) and "complete sentence" in pg.inner_text(".p-fb"), "sentence without verb → asks for a complete sentence")
                pg.screenshot(path=str(shots / "pr-light-8-prep-full.png"))
                pg.click('[data-p="next"]'); it = pg.evaluate("PQ.queue[0]")
                answer(pg, it["subj"] + " " + it["verb"] + " " + it["a"][-1] + ".")
            else:
                answer(pg, it["a"][0])
            if "ok" not in fbclass(pg): fails.append("prep right answer rejected " + it["id"])
            pg.click('[data-p="next"]'); n += 1
        ok(pg.is_visible(".summary"), "room finished → summary with 'Next room'")
        pg.click('[data-p="again"]'); pg.wait_for_timeout(100)
        ok(pg.evaluate("PQ.queue[0].scene") != it["scene"], "Next room moves to another room")
        for sc in ["quarto", "cozinha", "banho", "estar", "jantar"]:
            pg.click('[data-room="%s"]' % sc); pg.wait_for_timeout(80)
            pg.locator(".scene-svg").screenshot(path=str(shots / f"pr-scene-{sc}.png"))
        pg.click('[data-view="flip"]'); pg.wait_for_timeout(200)
        ok(pg.is_visible("#card"), "back to flashcards from the menu")
        ok(not errs, "no JS errors " + str(errs))
        ctx.close()
    b.close()
print("FAILS", len(fails))
for f in fails[:20]: print(" -", f)
