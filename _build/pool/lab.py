"""Laboratório (V62): criar, avaliar e guardar experiências no repositório, e guardar as fotografias do conselho da app.

As experiências criadas aqui ficam em lab/experiments.json e aparecem em TODOS os dispositivos (a app lê esse ficheiro
no site); as que o utilizador cria na app ficam só no browser dele. Este script não faz contas próprias: abre a app
(index.html) com o Playwright e usa os comandos e os números da própria app — por isso bate sempre certo com o que o
utilizador vê em Jogadores › Laboratório.

Uso (a partir da raiz):  Linux: python3 _build/pool/lab.py <comando>   ·   Windows: py -X utf8 _build/pool/lab.py <comando>

  listar                         as experiências do repositório (id, gestor, nome, jogadores, fantasma)
  avaliar [bruno|marco] [nome]   números de cada experiência: pontos esperados, capitão, H2H, diferença para o plantel
                                 real, diferenciais, ameaças, lesões e, se for fantasma, os pontos reais jornada a jornada
  cmd <bruno|marco> "<frase>" ["<frase>" …] [--guardar]
                                 escreve as frases na caixa de comandos do Laboratório, pela ordem dada, e mostra as
                                 respostas da app; com --guardar, o resultado fica em lab/experiments.json
                                 (as frases são as mesmas que o utilizador pode escrever: ver "ajuda")
  apagar <id ou nome>            tira uma experiência do repositório
  conselho                       guarda em lab/advice.json a troca, o onze, o capitão e o vice que a app aconselha
                                 para a próxima jornada (só antes do deadline; a última antes do deadline é a que conta).
                                 Corre sozinho no fim de "atualizar.py testes".
  reconstruir                    refaz as fotografias das jornadas passadas a partir das versões do index.html no git

Exemplo ("cria no Laboratório uma equipa com 3 do Arsenal e o Haaland e diz-me como fica contra a do Frederico"):
  python3 _build/pool/lab.py cmd bruno "cria uma equipa com 3 do Arsenal e o Haaland" "compara com o Frederico" --guardar
Depois: git add lab && git commit && git push (o site atualiza em 1-2 minutos)."""
import json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
H = ROOT / 'index.html'
LAB = ROOT / 'lab'
EXP = LAB / 'experiments.json'
ADV = LAB / 'advice.json'
HIST = ROOT / 'history'
NOTA = ('Experiências do Laboratório criadas pelo Claude Code (aparecem em todos os dispositivos, só de leitura na app). '
        'Escrito por _build/pool/lab.py — ver a secção "Laboratório" do CLAUDE.md. mgr = bruno | marco.')


def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def load(p, dflt):
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return dflt


def save(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')


def experiments():
    d = load(EXP, {})
    d.setdefault('nota', NOTA); d.setdefault('experiments', [])
    return d


def history():
    out = {}
    for f in sorted(HIST.glob('points-J*.json')):
        d = load(f, None)
        if d and d.get('points'):
            out[str(d['event'])] = d
    return out


def strip(html):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html or '')).strip()


class App:
    """A app aberta num browser sem janela, com as experiências do repositório como se fossem do browser (editáveis)."""
    def __init__(self, mgr='bruno', html=None, plain=False):
        from playwright.sync_api import sync_playwright
        self.mgr = mgr
        self.pw = sync_playwright().start()
        self.b = self.pw.chromium.launch()
        self.pg = self.b.new_page(viewport={'width': 1280, 'height': 900})
        self.errs = []
        self.pg.on('pageerror', lambda e: self.errs.append(str(e)))
        init = "try{localStorage.setItem('fpl-tour-done', JSON.stringify('off')); localStorage.setItem('fpl-mgr', %s);}catch(e){}" % json.dumps(mgr)
        if not plain:
            mine = [x for x in experiments()['experiments'] if x.get('mgr', mgr) == mgr]
            store = {m: {'list': mine if m == mgr else [], 'sel': None, 'cmp': [], 'seeded': True} for m in ('bruno', 'marco')}
            data = {'experiments': {'experiments': []}, 'advice': load(ADV, {}), 'history': history()}
            init += "window.__LAB_TOOL = true; window.__LAB_DATA = %s; try{localStorage.setItem('fpl-lab', JSON.stringify(%s));}catch(e){}" % (
                json.dumps(data, ensure_ascii=False), json.dumps(store, ensure_ascii=False))
        self.pg.add_init_script(init)
        self.pg.goto((html or H).resolve().as_uri())
        self.pg.wait_for_timeout(2500)
        if not plain:
            self.pg.evaluate("showView('mercado', 'lab')")
            self.pg.wait_for_timeout(600)

    def js(self, code, arg=None):
        return self.pg.evaluate(code, arg) if arg is not None else self.pg.evaluate(code)

    def close(self):
        self.b.close(); self.pw.stop()


def show(r):
    """Relatório de uma experiência em linhas simples."""
    if not r:
        return
    print(f"\n«{r['name']}» [{r['id']}] — criada na J{r['gw']}, orçamento £{r['budget']:.1f}M, {r['n']}/15 jogadores")
    if r.get('note'): print(f"  Nota: {r['note']}")
    if r.get('problems'): print('  NÃO CUMPRE AS REGRAS: ' + '; '.join(r['problems']))
    if 'ep1' not in r:
        return
    print(f"  Onze ({r['form']}): {', '.join(r['xi'])}")
    print(f"  Banco: {' → '.join(r['bench'])} · capitão {r['cap']} · vice {r['vice']}" + (f" · trancados: {', '.join(r['locked'])}" if r.get('locked') else ''))
    real = r.get('real')
    print(f"  Pontos esperados: próxima jornada {r['ep1']}" + (f" (plantel real {real['ep1']})" if real else '') + f"; próximas 5: {r['ep5']}" + (f" (plantel real {real['ep5']})" if real else ''))
    print(f"  Capitão com 10+ pts: {r['p10']}% · custo £{r['cost']:.1f}M (sobra £{r['left']:.1f}M)" + (f" · {real['dif']} jogadores diferentes do plantel real" if real else ''))
    h = r.get('h2h')
    if h: print(f"  H2H contra {h['opp']} ({h['team']}): ganha {h['win']}%, empata {h['draw']}%, perde {h['lose']}%" + (f" (o plantel real ganha {h['realWin']}%)" if h.get('realWin') is not None else ''))
    if r.get('diffs'): print('  Diferenciais: ' + ', '.join(r['diffs']))
    if r.get('threats'): print('  Ameaças (não as tem): ' + ', '.join(r['threats']))
    print('  Lesões e castigos: ' + ('; '.join(r['avail']) + f" (≈{r['miss']} jogos falhados nas próximas 5)" if r.get('avail') else 'nenhum à vista'))
    g = r.get('ghost')
    if g:
        modo = {'frozen': 'congelada', 'advice': 'segue o conselho da app', 'plan': 'segue um plano'}.get(g['mode'], g['mode'])
        print(f"  Fantasma desde a J{g['from']} ({modo}): {g['pts']} pts reais em {len(g['gws'])} jornadas; a equipa verdadeira fez {g['real']} ({g['pts'] - g['real']:+d})"
              + (' · ' + ', '.join(f'J{a} {b}' for a, b in g['gws']) if g['gws'] else ''))


def cmd_listar():
    L = experiments()['experiments']
    if not L:
        print('lab/experiments.json não tem experiências.'); return
    for x in L:
        g = x.get('ghost')
        print(f"{x['id']:<16} {x.get('mgr', '?'):<6} J{x.get('gw', '?'):<3} {len(x.get('ids', []))}/15  £{float(x.get('budget', 0)):.1f}M  {x.get('name')}" + (f"  [fantasma J{g['from']} {g['mode']}]" if g else ''))


def cmd_avaliar(args):
    mgrs = [a for a in args if a in ('bruno', 'marco')] or ['bruno', 'marco']
    nome = ' '.join(a for a in args if a not in ('bruno', 'marco')).lower()
    for mgr in mgrs:
        mine = [x for x in experiments()['experiments'] if x.get('mgr', mgr) == mgr and (not nome or nome in x.get('name', '').lower() or nome == x['id'])]
        if not mine:
            continue
        app = App(mgr)
        print(f"\n===== {mgr} — próxima jornada J{app.js('GW_META.next')} =====")
        for x in mine:
            show(app.js('(id) => labReport(id)', x['id']))
        app.close()


def cmd_cmd(args):
    guardar = '--guardar' in args
    args = [a for a in args if a != '--guardar']
    if len(args) < 2 or args[0] not in ('bruno', 'marco'):
        print('uso: lab.py cmd <bruno|marco> "<frase>" ["<frase>" …] [--guardar]'); sys.exit(1)
    mgr, frases = args[0], args[1:]
    app = App(mgr)
    ok = True
    for f in frases:
        r = app.js('(c) => labCmd(c)', f)
        ok = ok and r['ok']
        print(f"> {f}\n  {'✓' if r['ok'] else '✗'} {strip(r['msg'])}")
    show(app.js('labReport()'))
    lista = app.js("labS().list")
    if app.errs:
        print('\nERROS da app:', app.errs[:5])
    app.close()
    if not guardar:
        print('\n(não guardei nada: junta --guardar para ficar em lab/experiments.json)'); return
    D = experiments()
    outros = [x for x in D['experiments'] if x.get('mgr', mgr) != mgr]
    for x in lista:
        x['mgr'] = mgr
        x.pop('repo', None)
        if x.get('src') in (None, 'raiz', 'plantel', 'ideal', 'simulada'): x['by'] = 'claude'
    D['experiments'] = outros + lista
    D['updated'] = now()
    save(EXP, D)
    print(f"\nGuardado: lab/experiments.json tem agora {len(D['experiments'])} experiências ({len(lista)} do {mgr}). Falta git add lab && commit && push.")
    if not ok:
        print('Atenção: pelo menos uma frase não foi feita (ver ✗ acima).')


def cmd_apagar(args):
    q = ' '.join(args).lower()
    D = experiments()
    keep = [x for x in D['experiments'] if not (x['id'].lower() == q or x.get('name', '').lower() == q)]
    if len(keep) == len(D['experiments']):
        print(f'não encontrei «{q}» (ver: lab.py listar)'); sys.exit(1)
    print(f"apaguei {len(D['experiments']) - len(keep)} experiência(s)")
    D['experiments'] = keep; D['updated'] = now(); save(EXP, D)


ADVICE_JS = """() => { const out = {gw: GW_META.next, deadline: GW_META.deadline};
  ['bruno', 'marco'].forEach(m => { const a = labLiveAdvice(m); if (a) { delete a.live; out[m] = a; } });
  return out; }"""
# versões antigas da app (sem o Laboratório): o mesmo, só com o que elas já tinham
ADVICE_OLD_JS = """() => { const out = {gw: GW_META.next, deadline: GW_META.deadline};
  ['bruno', 'marco'].forEach(m => { try {
    const mv = ((SUGGESTED_MOVES[m] || {}).transfers || []).filter(x => x.out && x.in);
    const P = id => (FULL_POOL_BY_ID[id] || {}).price || 0;
    const sq = squadOf(m).filter(Boolean), r = pickXi(applyMoves(sq, mv), 0);
    out[m] = {transfers: mv.map(x => ({out: x.out, in: x.in, po: P(x.out), pi: P(x.in)})), xi: r.xi.map(p => p.id),
      bench: [...r.benchGk, ...r.benchOut].map(p => p.id), cap: r.cap.id, vice: r.vice.id, squad: sq.map(p => p.id)};
  } catch (e) { out[m + '_erro'] = String(e); } });
  return out; }"""


def put_advice(a, src):
    D = load(ADV, {})
    D.setdefault('nota', 'Fotografias do conselho da app antes de cada deadline (troca, onze, banco, capitão e vice aconselhados). '
                         'Escrito por _build/pool/lab.py conselho; as equipas fantasma "segue o conselho da app" usam-nas.')
    D.setdefault('gws', {})
    g = str(a['gw'])
    D['gws'][g] = {'at': now(), 'deadline': a.get('deadline'), 'src': src, **{m: a[m] for m in ('bruno', 'marco') if m in a}}
    D['gws'] = dict(sorted(D['gws'].items(), key=lambda kv: int(kv[0])))
    D['updated'] = now()
    save(ADV, D)


def cmd_conselho():
    app = App('bruno', plain=True)
    a = app.js(ADVICE_JS)
    app.close()
    dl = a.get('deadline')
    if dl and datetime.strptime(dl, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        print(f"conselho: o deadline da J{a['gw']} já passou — fica a fotografia que já lá estava"); return
    put_advice(a, 'app')
    for m in ('bruno', 'marco'):
        if m in a:
            print(f"conselho J{a['gw']} {m}: {len(a[m]['transfers'])} troca(s) {a[m]['transfers']}, capitão {a[m]['cap']}, vice {a[m]['vice']}")


def cmd_reconstruir():
    """Para cada jornada com deadline já passado: a última versão do index.html no git antes desse deadline."""
    live = load(ROOT / 'live.json', {})
    tmp = ROOT / '_build' / 'shots'; tmp.mkdir(parents=True, exist_ok=True)
    have = load(ADV, {}).get('gws', {})
    for e in live.get('events', []):
        g, dl = e['id'], e.get('deadline')
        if not dl or datetime.strptime(dl, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
            continue
        if str(g) in have and have[str(g)].get('src') == 'app':
            continue   # uma fotografia tirada na altura vale mais do que uma reconstruída
        sha = subprocess.run(['git', 'log', '-1', f'--before={dl}', '--format=%H', '--', 'index.html'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        if not sha:
            continue
        html = subprocess.run(['git', 'show', f'{sha}:index.html'], cwd=ROOT, capture_output=True).stdout
        f = tmp / f'conselho-J{g}.html'; f.write_bytes(html)
        app = None
        try:
            app = App('bruno', html=f, plain=True)
            a = app.js(ADVICE_OLD_JS)
        except Exception as err:
            print(f'J{g}: a versão {sha[:7]} não tem o conselho num formato que se leia ({str(err).splitlines()[0][:70]})'); continue
        finally:
            if app: app.close()
            f.unlink(missing_ok=True)
        if a.get('gw') != g:
            print(f"J{g}: a versão {sha[:7]} de antes do deadline ainda era da J{a.get('gw')} — sem fotografia"); continue
        a['deadline'] = dl
        put_advice(a, f'reconstruída do commit {sha[:7]}')
        print(f"J{g} ({sha[:7]}): " + ' · '.join(f"{m}: {len(a[m]['transfers'])} troca(s), capitão {a[m]['cap']}" for m in ('bruno', 'marco') if m in a))


if __name__ == '__main__':
    c = sys.argv[1] if len(sys.argv) > 1 else ''
    a = sys.argv[2:]
    if c == 'listar': cmd_listar()
    elif c == 'avaliar': cmd_avaliar(a)
    elif c == 'cmd': cmd_cmd(a)
    elif c == 'apagar': cmd_apagar(a)
    elif c == 'conselho': cmd_conselho()
    elif c == 'reconstruir': cmd_reconstruir()
    else: print(__doc__); sys.exit(1)
