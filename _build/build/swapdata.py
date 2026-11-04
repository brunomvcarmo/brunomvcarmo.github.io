"""Troca o bloco de dados (1.º <script> do <body>) do index.html da raiz do repositório pelo ficheiro gerado
por gen25.py, e confirma a sintaxe do JavaScript (precisa do Node instalado; se não houver, salta a verificação).
Uso (a partir da raiz do repositório):  py _build/build/swapdata.py _build/redesign/data25.js   (Linux: python3 …)"""
import re, sys, subprocess, tempfile, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
H = ROOT / 'index.html'
new = open(sys.argv[1], encoding='utf-8').read()
s = H.read_text(encoding='utf-8')
m = re.search(r'<script>\n// ======================= DADOS DA JORNADA.*?</script>', s, re.S)
assert m, 'bloco de dados não encontrado'
s = s[:m.start()] + '<script>\n' + new + '</script>' + s[m.end():]
H.write_text(s, encoding='utf-8', newline='\n')   # sempre LF, também no Windows
# versão para o artefacto do claude.ai (sem <!DOCTYPE>, <html>, </head>, <body>…)
keep = [l for l in s.split('\n') if l not in ('<!DOCTYPE html>', '<html lang="pt">', '</head>', '<body>', '</body>', '</html>')]
(ROOT / '_build' / 'redesign').mkdir(parents=True, exist_ok=True)
(ROOT / '_build' / 'redesign' / 'artefacto.html').write_text('\n'.join(keep), encoding='utf-8', newline='\n')
js = '\n'.join(re.findall(r'<script>\n(.*?)</script>', s, re.S))
if shutil.which('node'):
    f = Path(tempfile.gettempdir()) / 'fpl-check.js'; f.write_text(js, encoding='utf-8')
    print(subprocess.run(['node', '--check', str(f)], capture_output=True, text=True).stderr or 'syntax ok')
else:
    print('node não instalado: verificação de sintaxe saltada')
