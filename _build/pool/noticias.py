"""Notícias da semana (V61): valida _build/research/noticias.json e escreve a const NEWS no bloco de dados do index.html
(sem refazer o resto dos dados). O gen25.py também escreve a NEWS, por isso um `atualizar.py gerar` não a perde.
Uso (a partir da raiz):  Windows: py -X utf8 _build/pool/noticias.py   ·   Linux: python3 _build/pool/noticias.py"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / '_build' / 'research' / 'noticias.json'
H = ROOT / 'index.html'
TAGS = {'selecoes', 'lesao', 'treinador', 'castigo', 'calendario', 'mercado'}


def carregar():
    """Lê e valida o ficheiro; devolve só o que a app usa."""
    N = json.loads(SRC.read_text(encoding='utf-8')) if SRC.exists() else {'updated': None, 'gw': None, 'items': []}
    out = []
    for i, it in enumerate(N.get('items', [])):
        assert re.fullmatch(r'\d{4}-\d{2}-\d{2}', it.get('d', '')), f'notícia {i}: data inválida ({it.get("d")})'
        assert it.get('tag') in TAGS, f'notícia {i}: tag desconhecida ({it.get("tag")})'
        assert it.get('t') and it.get('x'), f'notícia {i}: falta o título ou o texto'
        assert it.get('src') and re.match(r'https?://', it.get('url', '')), f'notícia {i}: falta a fonte ou o link'
        assert all(isinstance(x, int) for x in it.get('ids', [])), f'notícia {i}: ids têm de ser números da FPL'
        out.append(dict(d=it['d'], tag=it['tag'], imp=int(it.get('imp', 1)), t=it['t'], x=it['x'], ids=it.get('ids', []), src=it['src'], url=it['url']))
    return dict(updated=N.get('updated'), gw=N.get('gw'), items=out)


def linha():
    return 'const NEWS = ' + json.dumps(carregar(), ensure_ascii=False, separators=(',', ':')) + ';'


if __name__ == '__main__':
    s = H.read_text(encoding='utf-8')
    ln = linha() + '\n'
    m = re.search(r'const NEWS = .*?;\n', s)
    if m: s = s[:m.start()] + ln + s[m.end():]
    else:
        i = s.index('const GW_META = '); s = s[:i] + ln + s[i:]
    H.write_text(s, encoding='utf-8', newline='\n')
    N = carregar()
    print(f'NEWS: {len(N["items"])} notícias (J{N["gw"]}, atualizado a {N["updated"]}) escritas no index.html')
    sys.exit(0)
