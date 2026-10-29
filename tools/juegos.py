"""Genera dist/juegos.html (Entreno SAMUR-PC: tests, juegos y actividades).

Uso (desde la raíz del repo, después de tools/quiz.py):  python3 tools/juegos.py
Lee data/*.json y src/juegos.html, y usa los iconos de node_modules/lucide-static.
"""
import json, os, re, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda *p: os.path.join(root, *p)
D = json.load(open(J('data', 'data.json'), encoding='utf-8'))
R = json.load(open(J('data', 'ref.json'), encoding='utf-8'))
QZ = json.load(open(J('data', 'quiz.json'), encoding='utf-8'))
EX = json.load(open(J('data', 'examenes.json'), encoding='utf-8'))

def clip(s, n):
    s = re.sub(r'\s+', ' ', s).strip()
    return s if len(s) <= n else s[:n].rsplit(' ', 1)[0] + '…'

drugs = []
for d in D['drugs']:
    f = next((f for f in d['f'] if re.match(r'Funci|Acci', f['f'])), d['f'][0] if d['f'] else None)
    if not f: continue
    txt = ' '.join(b['x'] for b in f['b'])
    if len(txt) > 25: drugs.append([d['n'], clip(txt, 150)])

# Refuerzo: párrafo del temario donde está la respuesta (ver tools/temario.py)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from temario import Temario, toks
T = Temario(D)
refs, rix = [], {}
def ref(r):
    if not r: return -1
    k = (r['pt'], r['h'], r['x'])
    if k not in rix:
        rix[k] = len(refs); refs.append(list(k))
    return rix[k]
sets = []
for s in QZ:
    pids = T.pids_for(s)
    qs = [[q, a, d, e, ref(T.find(q, a, e, pids))] for q, a, d, e in s['q']]
    sets.append({'id': s['id'], 'amb': s['amb'], 'g': s['g'], 't': s['t'], 'q': qs})
# Examen oficial: búsqueda estricta en todo el manual; si la respuesta es genérica
# («a y b», «todas»...) se usan las opciones. Excluidas las coincidencias revisadas como erróneas.
GEN = re.compile(r'^(a y b|ambas|las (dos|anteriores)|todas)', re.I)
EXCL = {'tats2024': {3, 9, 31, 62, 66, 67, 70, 74, 76, 85, 94}}
exams = []
for ex in EX:
    qs = []
    for n, q, o, c in ex['q']:
        r = None
        if n not in EXCL.get(ex['id'], ()):
            a = o[c]
            if GEN.match(a) or len(toks(a)) < 2: a = ' '.join(x for x in o if not GEN.match(x))
            r = T.find(q, a, '', T.all_pids(), strict=True)
        qs.append([n, q, o, c, ref(r)])
    exams.append(dict(ex, q=qs))

tree = [{'id': a['id'], 'name': a['name'], 'groups': [g['name'] for g in a['groups']]} for a in D['tree']]
G = {
    'tree': tree,
    'sets': sets,
    'exams': exams,
    'refs': refs,
    'claves': [c for c in R['claves'] if not c[0].startswith('Estatus')],
    'codigos': [[c[0], c[1], g['name']] for g in R['codigos'] for c in g['c']],
    'esp': R['esp'],
    'ind': [x for k in ('Particulares', 'Generales', 'Según base o función', 'Ajenos') for x in R['ind'][k]],
    'bases': R['ind'].get('Bases', []),
    'abbr': [a for a in D['abbr'] if len(a[0]) > 1],
    'drugs': drugs,
}

tpl = open(J('src', 'juegos.html'), encoding='utf-8').read()
names = set(re.findall(r"ic\('([a-z0-9-]+)'", tpl)) | set(re.findall(r"icon:'([a-z0-9-]+)'", tpl))
icons = {}
for n in sorted(names):
    f = J('node_modules', 'lucide-static', 'icons', n + '.svg')
    if not os.path.exists(f):
        print('falta icono', n); continue
    s = open(f).read()
    icons[n] = re.sub(r'\s+', ' ', re.search(r'<svg[^>]*>\s*(.*)</svg>', s, re.S).group(1)).strip()

out = tpl.replace('/*GDATA*/', json.dumps(G, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'))
out = out.replace('/*ICONS*/', json.dumps(icons, separators=(',', ':')))
os.makedirs(J('dist'), exist_ok=True)
open(J('dist', 'juegos.html'), 'w', encoding='utf-8').write(out)
print('dist/juegos.html', len(out), 'bytes,', len(icons), 'iconos,', len(refs), 'párrafos de refuerzo')
