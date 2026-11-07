"""Decide se a Action "Atualizar dados FPL" deve ir buscar dados agora (escreve run=true/false em $GITHUB_OUTPUT).
Corre sempre: à mão (Run workflow), às terças e sextas (horário antigo) e quando o live.json tem mais de 72 h.
Perto de um deadline (de 36 h antes até 30 h depois) corre se o live.json tiver mais de 2 h 30 min — assim a
véspera e o dia do deadline têm dados frescos, e os plantéis novos (públicos só depois do deadline) chegam depressa.
O agendamento do GitHub atrasa muitas vezes horas, por isso a Action acorda de 3 em 3 horas e decide aqui."""
import json, os, sys
from datetime import datetime, timezone
from pathlib import Path

now = datetime.now(timezone.utc)
ev = os.environ.get('EVENT', '')
cron = os.environ.get('CRON', '')
P = lambda t: datetime.strptime(t, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
run, why = True, 'à mão'
if ev == 'schedule':
    try:
        d = json.loads(Path(os.environ.get('LIVE_JSON') or Path(__file__).resolve().parents[1] / 'live.json').read_text(encoding='utf-8'))
        age = (now - P(d['generated'])).total_seconds() / 3600
        near = [e['id'] for e in d.get('events', []) if e.get('deadline') and -30 <= (P(e['deadline']) - now).total_seconds() / 3600 <= 36]
    except Exception as x:   # sem live.json legível: ir buscar
        age, near = 999, []
        print('live.json ilegível:', x)
    if cron in ('0 7 * * 2', '0 7 * * 5'): run, why = True, 'terça/sexta'
    elif age > 72: run, why = True, f'live.json com {age:.0f} h'
    elif near and age > 2.5: run, why = True, f'perto do deadline da J{near[0]} (live.json com {age:.1f} h)'
    else: run, why = False, f'nada a fazer (live.json com {age:.1f} h' + (f', deadline da J{near[0]} perto mas os dados são recentes)' if near else ', sem deadline perto)')
print(f'run={str(run).lower()} — {why}')
out = os.environ.get('GITHUB_OUTPUT')
if out:
    with open(out, 'a', encoding='utf-8') as f: f.write(f'run={str(run).lower()}\n')
sys.exit(0)
