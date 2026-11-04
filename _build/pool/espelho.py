"""Espelho da API da FPL + calendário oficial, para uma sessão nova (nuvem ou computador).
1. Descarrega para _build/mirror/ os CSV do FPL-Elo-Insights (playerstats, players, teams e matches_gwN.csv de
   N = 1 até à última jornada fechada — nunca o da jornada seguinte).
2. Grava o calendário oficial (api/fixtures/) em _build/data/fixtures.json (jornadas 1-38).
3. Confere a última jornada fechada do espelho contra a API oficial (event/N/live: pontos e minutos por jogador).
Uso (a partir da raiz):  Windows: py -X utf8 _build/pool/espelho.py   ·   Linux: python3 _build/pool/espelho.py
Opções: --sem-validar (salta o passo 3)."""
import csv, io, json, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIR = ROOT / '_build' / 'mirror'
DATA = ROOT / '_build' / 'data'
BASE = 'https://raw.githubusercontent.com/olbauday/FPL-Elo-Insights/main/data/2026-2027'
UA = {'User-Agent': 'Mozilla/5.0 (fpl-app)', 'Accept': '*/*'}


def get(url, tries=4):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read()
        except Exception as e:
            if k == tries - 1: raise RuntimeError(f'falhou {url}: {e}')
            time.sleep(3 + 4 * k)


def fpl(path):   # parâmetro extra contra as cópias antigas em cache (nona lição)
    return json.loads(get(f'https://fantasy.premierleague.com/api/{path}{"&" if "?" in path else "?"}t={int(time.time() * 1000)}'))


def main():
    MIR.mkdir(parents=True, exist_ok=True); DATA.mkdir(parents=True, exist_ok=True)
    boot = fpl('bootstrap-static/')
    fx = fpl('fixtures/')
    done = {g for g in range(1, 39) if [f for f in fx if f['event'] == g] and all(f['finished_provisional'] for f in fx if f['event'] == g)}
    last = max(done) if done else 0
    print(f'última jornada com os jogos todos acabados: J{last}')
    for name in ('playerstats', 'players', 'teams'):
        b = get(f'{BASE}/{name}.csv'); (MIR / f'{name}.csv').write_bytes(b)
        print(f'  {name}.csv {len(b) // 1024} KB')
    for g in range(1, last + 1):
        (MIR / f'matches_gw{g}.csv').write_bytes(get(f'{BASE}/By%20Gameweek/GW{g}/matches.csv'))
    for p in MIR.glob('matches_gw*.csv'):   # nunca guardar o da jornada seguinte (ainda sem jogos)
        if int(p.stem.replace('matches_gw', '')) > last: p.unlink()
    print(f'  matches_gw1..{last}.csv')
    out = {}
    for f in fx:
        g = f['event']
        if g: out.setdefault(str(g), []).append(dict(id=f['id'], event=g, kickoff=f['kickoff_time'], h=f['team_h'], a=f['team_a'], hs=f['team_h_score'],
                                                      **{'as': f['team_a_score']}, finished=f['finished_provisional'], dh=f['team_h_difficulty'], da=f['team_a_difficulty']))
    (DATA / 'fixtures.json').write_text(json.dumps(out), encoding='utf-8', newline='\n')
    print(f'  data/fixtures.json: {sum(len(v) for v in out.values())} jogos; sem jornada (adiados): {[f["id"] for f in fx if f["event"] is None]}')
    if '--sem-validar' in sys.argv or not last: return
    off = {e['id']: e['stats'] for e in fpl(f'event/{last}/live/')['elements']}
    rows = list(csv.DictReader(open(MIR / 'playerstats.csv', encoding='utf-8')))
    prev = {int(r['id']): r for r in rows if r['gw'] == str(last - 1)}
    cur = {int(r['id']): r for r in rows if r['gw'] == str(last)}
    if not cur:
        print(f'AVISO: o espelho ainda não tem a J{last} (atualiza 2×/dia): tenta mais tarde'); sys.exit(2)
    bad = []
    for i, r in cur.items():
        o = off.get(i)
        if not o: continue
        m = int(float(r['minutes'])) - (int(float(prev[i]['minutes'])) if i in prev else 0)
        if int(r['event_points']) != o['total_points'] or m != o['minutes']: bad.append((i, r['web_name'], r['event_points'], o['total_points']))
    print(f'validação J{last}: {len(cur)} jogadores comparados com a API oficial, {len(bad)} diferentes {bad[:8]}')
    if bad: sys.exit(3)


if __name__ == '__main__':
    main()
