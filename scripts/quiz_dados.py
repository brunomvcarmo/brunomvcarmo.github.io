"""Dados do jogo "Fora da Caixa" (foradacaixa/index.html): estatísticas da época de todos os jogadores da Premier League.
Lê os CSV do espelho da API da FPL (FPL-Elo-Insights): _build/mirror/ se existir, senão descarrega-os.
Escreve foradacaixa/dados.json (compacto). Corre sozinho na GitHub Action fpl-update.yml.
Uso (a partir da raiz):  Linux: python3 scripts/quiz_dados.py   ·   Windows: py -X utf8 scripts/quiz_dados.py
Opção: --descarregar (ignora o _build/mirror/ e vai buscar os CSV frescos)."""
import csv, io, json, sys, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIR = ROOT / '_build' / 'mirror'
OUT = ROOT / 'foradacaixa' / 'dados.json'
BASE = 'https://raw.githubusercontent.com/olbauday/FPL-Elo-Insights/main/data/2026-2027'
UA = {'User-Agent': 'Mozilla/5.0 (fpl-app)', 'Accept': '*/*'}
POS = {'Goalkeeper': 'gk', 'Defender': 'def', 'Midfielder': 'mid', 'Forward': 'fwd'}


def csv_rows(name):
    p = MIR / f'{name}.csv'
    if p.exists() and '--descarregar' not in sys.argv:
        txt = p.read_text(encoding='utf-8')
    else:
        for k in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request(f'{BASE}/{name}.csv', headers=UA), timeout=120) as r:
                    txt = r.read().decode('utf-8'); break
            except Exception as e:
                if k == 3: raise RuntimeError(f'falhou {name}.csv: {e}')
                time.sleep(3 + 4 * k)
    return list(csv.DictReader(io.StringIO(txt)))


def num(x):
    try: return float(x)
    except (TypeError, ValueError): return 0.0


def main():
    teams = {t['code']: t for t in csv_rows('teams')}
    team_id = {code: int(t['id']) for code, t in teams.items()}
    players = {int(p['player_id']): p for p in csv_rows('players')}
    stats = csv_rows('playerstats')
    gws = sorted({int(r['gw']) for r in stats if r.get('gw')})
    last = gws[-1] if gws else 0
    by = {}
    for r in stats:   # valores acumulados da época, uma linha por jornada
        by.setdefault(int(r['id']), {})[int(r['gw'])] = r
    keys = ['goals_scored', 'assists', 'total_points', 'minutes', 'clean_sheets']
    out = []
    for pid, rows in sorted(by.items()):
        p = players.get(pid)
        if not p or p.get('team_code') not in team_id: continue
        cur = rows[max(rows)]
        series = {k: [] for k in keys}
        prev = {k: 0 for k in keys}
        for g in range(1, last + 1):
            r = rows.get(g)
            for k in keys:
                v = int(num(r[k])) if r else prev[k]
                series[k].append(v - prev[k]); prev[k] = v
        out.append([
            pid, cur['web_name'], f"{p['first_name']} {p['second_name']}".strip(), team_id[p['team_code']], POS.get(p['position'], 'mid'),
            round(num(cur['selected_by_percent']), 1), round(num(cur['now_cost']), 1),
            int(num(cur['minutes'])), int(num(cur['starts'])), int(num(cur['total_points'])),
            int(num(cur['goals_scored'])), int(num(cur['assists'])), int(num(cur['clean_sheets'])),
            int(num(cur['yellow_cards'])), int(num(cur['red_cards'])), int(num(cur['saves'])),
            int(num(cur['penalties_saved'])), int(num(cur['penalties_missed'])), int(num(cur['own_goals'])), int(num(cur['bonus'])),
            series['goals_scored'], series['assists'], series['total_points'], series['minutes'],
        ])
    data = {
        'gerado': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ'),
        'jornada': last,
        'equipas': {int(t['id']): [t['name'], t['short_name']] for t in teams.values()},
        'campos': ['id', 'nome', 'completo', 'equipa', 'pos', 'popular', 'preco', 'minutos', 'titular', 'pontos',
                   'golos', 'assist', 'cs', 'amarelos', 'vermelhos', 'defesas', 'penDef', 'penFalh', 'autogolos', 'bonus',
                   'jGolos', 'jAssist', 'jPontos', 'jMinutos'],
        'jogadores': out,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8', newline='\n')
    print(f'foradacaixa/dados.json: {len(out)} jogadores, até à J{last} ({OUT.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main()
