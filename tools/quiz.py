"""Convierte las preguntas de quiz/*.py en data/quiz.json.

Cada fichero de quiz/ define QUIZ = {clave: [(pregunta, correcta, [3 distractores], explicación), ...]}
La clave es el id de un procedimiento (p. ej. 'convulsiones432') o un bloque entero
con el formato 'g:<ámbito>:<nombre del bloque>' (p. ej. 'g:tecnicas:Vasculares').
Uso (desde la raíz del repo):  python3 tools/quiz.py
"""
import glob, json, os, re, sys, unicodedata

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(root, 'data', 'data.json')))
procs = {p['id']: p for p in D['procs']}
groups = {(a['id'], g['name']) for a in D['tree'] for g in a['groups']}

def slug(s):
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')

Q = {}
for f in sorted(glob.glob(os.path.join(root, 'quiz', '*.py'))):
    g = {}
    exec(open(f, encoding='utf-8').read(), g)
    for k, v in g['QUIZ'].items():
        if k in Q: sys.exit(f'Clave repetida {k} en {f}')
        Q[k] = (v, os.path.basename(f))

err = []
sets = []
for k, (items, fn) in Q.items():
    if k.startswith('g:'):
        _, amb, gname = k.split(':', 2)
        if (amb, gname) not in groups: err.append(f'{fn}: bloque desconocido {k}'); continue
        s = dict(id='g-' + amb + '-' + slug(gname), amb=amb, g=gname, p=None, t=gname)
    else:
        if k not in procs: err.append(f'{fn}: procedimiento desconocido {k}'); continue
        p = procs[k]
        s = dict(id=k, amb=p['amb'], g=p['grp'], p=k, t=p['title'])
    qs = []
    for n, it in enumerate(items):
        if len(it) != 4 or len(it[2]) != 3: err.append(f'{fn} {k} #{n+1}: formato incorrecto'); continue
        q, a, d, e = it
        if a in d or len(set(d)) != 3: err.append(f'{fn} {k} #{n+1}: opciones repetidas'); continue
        qs.append([q, a, list(d), e])
    s['q'] = qs
    sets.append(s)

if err:
    print('\n'.join(err)); sys.exit(1)

order = {}
for a in D['tree']:
    for g in a['groups']:
        order[(a['id'], g['name'])] = len(order)
pidx = {p['id']: i for i, p in enumerate(D['procs'])}
sets.sort(key=lambda s: (order[(s['amb'], s['g'])], pidx.get(s['p'], -1)))
json.dump(sets, open(os.path.join(root, 'data', 'quiz.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(sets), 'tests,', sum(len(s['q']) for s in sets), 'preguntas -> data/quiz.json')
