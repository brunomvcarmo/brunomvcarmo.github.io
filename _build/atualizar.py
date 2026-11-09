"""Passos mecânicos da atualização semanal da app, pela ordem certa, iguais no Windows e no Linux (nuvem).
Corre cada script com o mesmo Python que corre este (py no Windows, python3 no Linux) e pára no primeiro erro.

Uso (a partir da raiz do repositório):
  Windows: py -X utf8 _build/atualizar.py <fase>      Linux/nuvem: python3 _build/atualizar.py <fase>

Fases:
  dados     fpl_fetch.py (live.json/rivals.json) + espelho.py (espelho, calendário, validação da última jornada)
            + research_week.py (projeções, odds, xgstat, OddAlerts) + lineups_rw.py (onzes) + h2h_week.py (H2H)
            + discorda.py medir (pontos reais das discordâncias guardadas: quem teve razão, a app ou o consenso)
  gerar     gen25.py (bloco de dados, inclui duplas/brancas e as discordâncias app × consenso, guardadas antes do deadline) + swapdata.py (troca no index.html) + weekly_app.py (tabelas)
  testes    test.py + test_tutorial.py + test_aovivo.py (precisam do Playwright: bash _build/setup-cloud.sh)
  semana    dados + gerar + testes (sem parar para as partes à mão — ver abaixo)
  deadline  depois do deadline da próxima jornada: fpl_fetch.py + apply_picks.py (plantéis, capitães e chips reais)

Entre "dados" e "gerar" há trabalho à mão (ver CLAUDE.md, "Atualização semanal"): opiniões dos sites
(_build/research/expert.json + expert_pt.json), a leitura própria (READING em _build/pool/model25.py) e as taças
(_build/research/cups.json). Depois de "gerar": as recomendações e textos da semana (ver _build/patches/patch_j10.py).
Opção: --continuar  (não pára num passo que falhe; mostra tudo no fim)."""
import subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
P = lambda *a: [PY, '-X', 'utf8', *a]
FASES = {
    'dados': [('Dados oficiais da FPL', P('scripts/fpl_fetch.py')),
              ('Espelho da API e calendário', P('_build/pool/espelho.py')),
              ('Pesquisa: projeções, odds, dificuldade', P('_build/pool/research_week.py')),
              ('Onzes prováveis', P('_build/pool/lineups_rw.py')),
              ('Liga H2H', P('_build/pool/h2h_week.py')),
              ('Onde a app discorda: medir quem teve razão', P('_build/pool/discorda.py', 'medir'))],
    'gerar': [('Bloco de dados (gen25)', P('_build/pool/gen25.py')),
              ('Troca no index.html', P('_build/build/swapdata.py', '_build/redesign/data25.js')),
              ('Tabelas da app', P('_build/pool/weekly_app.py'))],
    'testes': [('Testes da app', P('_build/scripts/test.py')),
               ('Testes do tutorial', P('_build/scripts/test_tutorial.py')),
               ('Testes do Ao vivo', P('_build/scripts/test_aovivo.py', '.', '_build/shots'))],
    'deadline': [('Dados oficiais da FPL', P('scripts/fpl_fetch.py')),
                 ('Plantéis reais da jornada', P('_build/pool/apply_picks.py'))],
}
FASES['semana'] = FASES['dados'] + FASES['gerar'] + FASES['testes']
OK_TEST = {'Testes da app': 'ERRORS 0', 'Testes do tutorial': 'TOTAL ERRORS 0', 'Testes do Ao vivo': 'ERRORS 0'}


def main():
    fase = next((a for a in sys.argv[1:] if not a.startswith('--')), None)
    if fase not in FASES:
        print(__doc__); sys.exit(1)
    cont = '--continuar' in sys.argv
    res = []
    for nome, cmd in FASES[fase]:
        t0 = time.time()
        print(f'\n=== {nome}: {" ".join(cmd[1:])}', flush=True)
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
        out = (r.stdout or '') + (r.stderr or '')
        tail = '\n'.join(out.strip().split('\n')[-12:])
        print(tail)
        ok = r.returncode == 0
        if nome in OK_TEST:   # os testes escrevem "ERRORS n" por cada parte: todas têm de dar 0
            errs = [l for l in out.split('\n') if 'ERRORS' in l]
            ok = ok and bool(errs) and all(l.strip().endswith(' 0') for l in errs)
        res.append((nome, ok, round(time.time() - t0)))
        if not ok and not cont:
            break
    print('\n=== Resumo')
    for nome, ok, s in res:
        print(f"  {'OK ' if ok else 'ERRO'}  {nome} ({s} s)")
    sys.exit(0 if all(ok for _, ok, _ in res) and len(res) == len(FASES[fase]) else 1)


if __name__ == '__main__':
    main()
