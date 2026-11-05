"""Rotina diária automática (V56): decide o que fazer, guarda as recomendações antes/depois, marca a atualização
na app e escreve o registo. O trabalho de juízo (pesquisa, leitura, textos) é feito pelo Claude seguindo a secção
"Rotina diária" do CLAUDE.md; este script trata das partes mecânicas.

Uso (a partir da raiz):  Linux: python3 _build/rotina.py <comando>   ·   Windows: py -X utf8 _build/rotina.py <comando>
  decidir [--qualquer-hora]   imprime JSON {"tipo": "completa" | "ultima_hora" | "nada" | "fora_de_hora", "motivo": …}
                              (a rotina acorda às 08:00 e 09:00 UTC; só trabalha quando em Lisboa são 9h)
  recs antes|depois           guarda as recomendações da app (troca, capitão, vice, chip) em _build/rotina/recs-<x>.json
  marcar <tipo> [--motivo-bruno "…"] [--motivo-marco "…"]
                              compara antes/depois, escreve _build/rotina/auto.json e a const AUTO_UPDATE no index.html
                              (linha "Última atualização automática" e aviso "Mudou desde ontem" no Resumo)
  registar <tipo> "<o que mudou>" <publicou: sim|não|erro> ["<erro>"]
                              acrescenta uma linha a _build/rotina-log.md"""
import json, re, sys, time, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / '_build' / 'rotina'
LOG = ROOT / '_build' / 'rotina-log.md'
H = ROOT / 'index.html'


def lisboa(d):
    """Hora de Lisboa sem tzdata: UTC+1 entre o último domingo de março e o último de outubro (01:00 UTC)."""
    def last_sun(m):
        x = datetime(d.year, m, 31, 1, tzinfo=timezone.utc); return x - timedelta(days=(x.weekday() + 1) % 7)
    return d + timedelta(hours=1 if last_sun(3) <= d < last_sun(10) else 0)


def fpl(path):
    url = f'https://fantasy.premierleague.com/api/{path}{"&" if "?" in path else "?"}t={int(time.time() * 1000)}'
    for k in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (fpl-app)'}), timeout=60) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception:
            if k == 3: raise
            time.sleep(5 * (k + 1))


def meta():
    s = H.read_text(encoding='utf-8')
    return json.loads(re.search(r'const GW_META = (\{.*?\});\n', s).group(1))


def decidir():
    now = datetime.now(timezone.utc)
    if '--qualquer-hora' not in sys.argv and lisboa(now).hour != 9:
        return dict(tipo='fora_de_hora', motivo=f'em Lisboa são {lisboa(now):%H:%M}; a rotina só trabalha às 9h')
    M = meta()
    try:
        boot = fpl('bootstrap-static/')
    except Exception:
        # sem acesso à API da FPL (rede do ambiente): usar as jornadas do live.json, que a GitHub Action atualiza
        LV = json.loads((ROOT / 'live.json').read_text(encoding='utf-8'))
        evs = [dict(id=e['id'], finished=e['finished'], deadline_time=e['deadline']) for e in LV['events']]
        for e in evs: e['is_next'] = False
        fut = [e for e in evs if datetime.strptime(e['deadline_time'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc) > now]
        if fut: min(fut, key=lambda e: e['id'])['is_next'] = True
        boot = dict(events=evs, fonte='live.json')
    fin = [e['id'] for e in boot['events'] if e['finished']]
    last_done = max(fin) if fin else 0
    if last_done > M['last']:
        return dict(tipo='completa', motivo=f'a J{last_done} fechou na FPL e a app ainda está na J{M["last"]}', last=last_done)
    nxt = next((e for e in boot['events'] if e['is_next']), None)
    if nxt:
        dl = datetime.strptime(nxt['deadline_time'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
        h = (dl - now).total_seconds() / 3600
        if 0 < h <= 30:
            return dict(tipo='ultima_hora', motivo=f'deadline da J{nxt["id"]} daqui a {h:.0f} h ({['seg','ter','qua','qui','sex','sáb','dom'][lisboa(dl).weekday()]} {lisboa(dl):%d/%m %H:%M} em Lisboa)', next=nxt['id'], horas=round(h, 1))
        return dict(tipo='nada', motivo=f'nenhuma jornada nova fechada e o deadline da J{nxt["id"]} é daqui a {h:.0f} h', next=nxt['id'], horas=round(h, 1))
    return dict(tipo='nada', motivo='sem próxima jornada (fim da época)')


def recs(qual):
    """Recomendações que a app mostra agora (lidas da própria app com o Playwright)."""
    from playwright.sync_api import sync_playwright
    DIR.mkdir(parents=True, exist_ok=True)
    js = """(() => { const out = {gw: GW_META.next, date: new Date().toISOString()};
      ['bruno', 'marco'].forEach(m => {
        const mv = (SUGGESTED_MOVES[m] || {transfers: []}).transfers;
        const r = pickXi(applyMoves(squadOf(m).filter(Boolean), mv), 0);
        const P = id => FULL_POOL_BY_ID[id] || {};
        const cp = (typeof chipPlanFor === 'function' ? chipPlanFor(m) : CHIP_PLAN)[GW_META.next] || {};
        out[m] = {transfers: mv.map(x => ({out: x.out, in: x.in, outN: P(x.out).name, inN: P(x.in).name})),
          cap: r.cap.name, capId: r.cap.id, capEp: +epAt(r.cap, 0).toFixed(1), vice: r.vice.name,
          chip: cp.chip && !cp.used ? cp.chip : null,
          status: Object.fromEntries([...mv.flatMap(x => [x.out, x.in]), r.cap.id].map(id => [id, [P(id).name, P(id).status, P(id).chance, +epAt(P(id), 0).toFixed(1)]]))};
      });
      return out; })()"""
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page()
        pg.add_init_script("localStorage.setItem('fpl-tour-done', JSON.stringify('off'))")
        pg.goto(H.resolve().as_uri()); pg.wait_for_timeout(2500)
        out = pg.evaluate(js); b.close()
    (DIR / f'recs-{qual}.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8', newline='\n')
    print(json.dumps({m: {k: out[m][k] for k in ('transfers', 'cap', 'vice', 'chip')} for m in ('bruno', 'marco')}, ensure_ascii=False))


CHIP = {'wc': 'Wildcard', 'fh': 'Free Hit', 'bb': 'Bench Boost', 'tc': 'Triple Captain', None: 'nenhuma'}
ST = {'a': 'disponível', 'd': 'dúvida', 'i': 'lesionado', 's': 'castigado', 'u': 'indisponível', 'n': 'indisponível'}


def diff(A, B, m, motivo=None):
    """Frases "Mudou desde ontem" de um gestor, com o motivo calculado a partir do estado e dos pontos esperados."""
    a, b = A[m], B[m]; out = []
    def why(old_id, new_id):
        o = b['status'].get(str(old_id)) or a['status'].get(str(old_id)); n = b['status'].get(str(new_id))
        if o and o[1] != 'a': return f'o {o[0]} passou a {ST.get(o[1], o[1])}{f" ({o[2]}%)" if o[2] is not None else ""}'
        if o and n: return f'pontos esperados: {n[0]} ≈{n[3]} contra {o[0]} ≈{o[3]}'
        return 'dados novos (lesões, onzes prováveis, odds)'
    ta = [(t['outN'], t['inN']) for t in a['transfers']]; tb = [(t['outN'], t['inN']) for t in b['transfers']]
    if ta != tb:
        txt = (' + '.join(f'{x} → {y}' for x, y in tb) or 'nenhuma troca')
        prev = (' + '.join(f'{x} → {y}' for x, y in ta) or 'nenhuma troca')
        w = motivo or (why(a['transfers'][0]['in'], b['transfers'][0]['in']) if a['transfers'] and b['transfers'] else 'dados novos (lesões, onzes prováveis, odds)')
        out.append(f'troca sugerida: {txt} (era {prev}) — {w}.')
    if a['cap'] != b['cap']:
        out.append(f'capitão: {b["cap"]} (era {a["cap"]}) — {motivo or why(a["capId"], b["capId"])}.')
    if a['chip'] != b['chip']:
        out.append(f'chip: {CHIP[b["chip"]]} (era {CHIP[a["chip"]]}){" — " + motivo if motivo else ""}.')
    return out


def marcar(tipo):
    DIR.mkdir(parents=True, exist_ok=True)
    arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
    A = json.loads((DIR / 'recs-antes.json').read_text(encoding='utf-8')) if (DIR / 'recs-antes.json').exists() else None
    B = json.loads((DIR / 'recs-depois.json').read_text(encoding='utf-8')) if (DIR / 'recs-depois.json').exists() else None
    ch = {}
    if A and B and A.get('gw') == B.get('gw'):   # só se compara a mesma jornada (numa jornada nova tudo muda)
        for m in ('bruno', 'marco'):
            d = diff(A, B, m, arg('--motivo-' + m))
            if d: ch[m] = d
    auto = dict(date=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), tipo=tipo, gw=(B or {}).get('gw'), changes=ch)
    (DIR / 'auto.json').write_text(json.dumps(auto, ensure_ascii=False, indent=1), encoding='utf-8', newline='\n')
    s = H.read_text(encoding='utf-8')
    line = 'const AUTO_UPDATE = ' + json.dumps(auto, ensure_ascii=False, separators=(',', ':')) + ';\n'
    m = re.search(r'const AUTO_UPDATE = .*?;\n', s)
    if m: s = s[:m.start()] + line + s[m.end():]
    else:
        i = s.index('const GW_META = '); s = s[:i] + line + s[i:]
    H.write_text(s, encoding='utf-8', newline='\n')
    print(json.dumps(auto, ensure_ascii=False))


def registar(tipo, oque, pub, erro=''):
    now = lisboa(datetime.now(timezone.utc))
    if not LOG.exists():
        LOG.write_text('# Registo da rotina diária\n\nUma linha por execução (hora de Lisboa). Tipos: completa, última hora, nada.\n\n'
                       '| Data | Tipo | O que mudou | Publicou |\n|---|---|---|---|\n', encoding='utf-8', newline='\n')
    pub_txt = {'sim': 'sim', 'não': 'não', 'nao': 'não', 'erro': f'não (erro: {erro})'}.get(pub, pub)
    with open(LOG, 'a', encoding='utf-8', newline='\n') as f:
        f.write(f'| {now:%Y-%m-%d %H:%M} | {tipo} | {oque.replace("|", "/")} | {pub_txt.replace("|", "/")} |\n')
    print(f'registado: {now:%Y-%m-%d %H:%M} {tipo}')


if __name__ == '__main__':
    c = sys.argv[1] if len(sys.argv) > 1 else ''
    if c == 'decidir': print(json.dumps(decidir(), ensure_ascii=False))
    elif c == 'recs': recs(sys.argv[2])
    elif c == 'marcar': marcar(sys.argv[2])
    elif c == 'registar': registar(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] if len(sys.argv) > 5 else '')
    else: print(__doc__); sys.exit(1)
