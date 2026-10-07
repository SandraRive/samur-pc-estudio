import re, json, unicodedata
from tree import TREE, STOPS

raw = open('L.txt').read().split('\x0c')
L = []
for i, pg in enumerate(raw):
    for l in pg.split('\n'):
        s = l.strip()
        if s.startswith('Home - Manual de Procedimientos SAMUR'): continue
        if re.match(r'Page \d+ / 654', s): continue
        l = l.replace('ﬁ', 'fi').replace('ﬂ', 'fl').replace('ﬀ', 'ff').replace('­', '')
        L.append((i + 1, l.rstrip()))

def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]', '', s)

entries = []
for a in TREE:
    for g in a[4]:
        for e in g[2]:
            entries.append(dict(amb=a[0], grp=g[0], key=e[0].replace('ﬁ','fi'), page=e[1],
                                title=(e[2] if len(e) > 2 else e[0]).replace('ﬁ', 'fi')))
for k, p in STOPS:
    entries.append(dict(amb=None, grp=None, key=k, page=p, title=k, stop=True))

order = sorted(range(len(entries)), key=lambda i: (entries[i]['page'], i))
pos = 0
for i in order:
    e = entries[i]; k = norm(e['key'])[:28]
    found = None
    for j in range(pos, len(L)):
        p, l = L[j]
        if p > e['page'] + 1: break
        if p < e['page'] - 1: continue
        st = l.strip()
        if st and st[0] not in '•-' and norm(l).startswith(k) and len(l) - len(l.lstrip()) < 8:
            found = j; break
    if found is None:
        print('NOT FOUND', e['page'], e['key']); e['start'] = None
    else:
        e['start'] = found; pos = found + 1

vadem = next(j for j, (p, l) in enumerate(L) if p >= 595 and l.strip() == 'VADEMÉCUM')
starts = sorted(e['start'] for e in entries if e['start'] is not None)

# ---------- block parser ----------
JUNK = re.compile(r'^(Inicio página|Inicio Vademécum|Inicio Abreviaturas|Manual de Procedimientos SAMUR-Protección Civil · edición.*|Última modificación( el)? \d.*|-)$')

def is_caps(s):
    letters = [c for c in s if c.isalpha()]
    return len(letters) >= 4 and sum(c.isupper() for c in letters) / len(letters) > 0.85

BUL = re.compile(r'^(•|·|▪|◦|o |- |\* )\s*')
NUM = re.compile(r'^(\d{1,2}|[a-z])[\.\)]\s+(?=\S)')

def columnar(l):
    s = l.strip()
    return len(re.findall(r'\S {4,}\S', s)) >= 1 and len(s) > 0

def parse(lines):
    """lines: list of raw strings. returns blocks"""
    # drop junk
    ls = [l for l in lines if not JUNK.match(l.strip())]
    # drop 'Contenido' mini tocs
    out = []; i = 0
    while i < len(ls):
        if ls[i].strip() == 'Contenido':
            i += 1
            while i < len(ls) and (not ls[i].strip() or ls[i].strip().startswith('•')):
                i += 1
            continue
        out.append(ls[i]); i += 1
    ls = out
    # mark table regions
    col = [columnar(l) and not BUL.match(l.strip()) for l in ls]
    intable = [False] * len(ls)
    idx = [i for i, c in enumerate(col) if c]
    # group columnar lines with gaps <=2 nonblank non-col lines
    groups = []
    for i in idx:
        if groups and i - groups[-1][-1] <= 4:
            groups[-1].append(i)
        else:
            groups.append([i])
    for g in groups:
        if len(g) >= 2:
            for k in range(g[0], g[-1] + 1): intable[k] = True
    blocks = []
    para = []
    def flush():
        nonlocal para
        if para:
            t = ''
            for x in para:
                x = x.strip()
                if t.endswith('-') and not t.endswith(' -'): t = t + x
                elif t: t = t + ' ' + x
                else: t = x
            blocks.append({'t': 'p', 'x': t})
            para = []
    i = 0
    cur_item = None  # (block ref, indent)
    while i < len(ls):
        l = ls[i]; s = l.strip()
        if intable[i]:
            flush(); cur_item = None
            tb = []
            while i < len(ls) and intable[i]:
                tb.append(ls[i]); i += 1
            # dedent
            while tb and not tb[-1].strip(): tb.pop()
            ind = min((len(x) - len(x.lstrip()) for x in tb if x.strip()), default=0)
            tb = [x[ind:] for x in tb]
            # collapse multiple blanks
            t2 = []
            for x in tb:
                if not x.strip() and t2 and not t2[-1].strip(): continue
                t2.append(x)
            blocks.append({'t': 'pre', 'x': '\n'.join(t2)})
            continue
        if not s:
            flush(); i += 1
            # blank line ends continuation only if next is not indented continuation
            continue
        ind = len(l) - len(l.lstrip())
        m = BUL.match(s); n = NUM.match(s) if not m else None
        if m or n:
            flush()
            txt = s[m.end():] if m else s[n.end():]
            item = {'t': 'li', 'ind': ind, 'x': txt, 'o': (n.group(1) if n else None)}
            blocks.append(item); cur_item = item
            i += 1
            continue
        # continuation of list item
        if cur_item is not None and ind >= cur_item['ind'] + 2 and (not (is_caps(s) and len(s) < 90) or not re.search(r'[.:;]$', cur_item['x']) or s.startswith('(')):
            x = cur_item['x']
            cur_item['x'] = (x + s) if (x.endswith('-') and not x.endswith(' -')) else (x + ' ' + s)
            i += 1; continue
        cur_item = None
        if is_caps(s) and len(s) < 120 and not para and not s.startswith('('):
            flush(); blocks.append({'t': 'h', 'x': s}); i += 1; continue
        if len(s) < 90 and s.endswith(':') and not para:
            flush(); blocks.append({'t': 'lab', 'x': s}); i += 1; continue
        para.append(l); i += 1
        # paragraph ends when a short line closes a sentence
        if len(l) < 100 and s.endswith(('.', ':')):
            flush()
    flush()
    # convert li indents to levels
    inds = sorted(set(b['ind'] for b in blocks if b['t'] == 'li'))
    merged = []
    for v in inds:
        if merged and v - merged[-1][-1] <= 2: merged[-1].append(v)
        else: merged.append([v])
    lvl = {}
    for k, g in enumerate(merged):
        for v in g: lvl[v] = min(k, 4)
    res = []
    for b in blocks:
        if b['t'] == 'li':
            res.append({'t': 'li', 'l': lvl[b['ind']], 'x': b['x'], **({'o': b['o']} if b['o'] else {})})
        else:
            res.append(b)
    # merge consecutive single-line paragraphs that are clearly part of a sentence
    out = []
    for b in res:
        if out and b['t'] == 'p' and out[-1]['t'] == 'p' and not re.search(r'[\.:;!?)\]]$', out[-1]['x']) and b['x'][:1].islower():
            out[-1]['x'] += ' ' + b['x']
        else:
            out.append(b)
    return out

contents_titles = []
procs = []
for e in entries:
    if e.get('stop') or e['start'] is None: continue
    nxt = [s for s in starts if s > e['start']] + [vadem]
    end = nxt[0]
    seg = [l for p, l in L[e['start']:end]]
    pages = (L[e['start']][0], L[end - 1][0])
    # cut at last 'Inicio página'
    cut = None
    for k in range(len(seg) - 1, -1, -1):
        if seg[k].strip() in ('Inicio página',):
            cut = k; break
    if cut is not None and cut > len(seg) * 0.4:
        seg = seg[:cut]
    # drop title lines (first line + wrapped continuation)
    seg = seg[1:]
    while seg and not seg[0].strip(): seg = seg[1:]
    if seg and len(seg[0]) - len(seg[0].lstrip()) < 2 and len(seg[0].strip()) < 50 and not seg[0].strip().endswith(('.', ':')) and seg[0].strip()[:1].isalpha() and norm(seg[0])[:6] in norm(e['title'] + e['key'] + ' asistencial comunicaciones delta lima fenix uro'):
        seg = seg[1:]
    blocks = parse(seg)
    text = ' '.join(b['x'] for b in blocks)
    procs.append(dict(id=re.sub(r'[^a-z0-9]+', '-', norm(e['title'])[:40]) + str(e['page']), amb=e['amb'], grp=e['grp'],
                      title=e['title'], p=pages, b=blocks, w=len(text.split())))

# ensure unique ids
seen = set()
for p in procs:
    while p['id'] in seen: p['id'] += 'x'
    seen.add(p['id'])

# ---------- vademecum ----------
abre = next(j for j, (p, l) in enumerate(L) if p > 640 and l.strip() == 'Abreviaturas')
colab = next(j for j, (p, l) in enumerate(L) if p > 640 and l.strip() == 'Colaboradores')
V = [l for p, l in L[vadem:abre]]
FIELDS = ['Función', 'Acción', 'Indicaciones', 'Dosis', 'Contraindicaciones', 'Interacciones', 'Efectos secundarios', 'Presentación', 'Precauciones', 'Observaciones', 'Mecanismo de acción', 'Antídoto', 'Conservación']
FRE = re.compile(r'^\s*(' + '|'.join(FIELDS) + r')\s*:\s*', re.I)
# find drug starts: a nonblank line, whose next nonblank line starts with 'Función'
drugs = []
nb = [k for k, l in enumerate(V) if l.strip()]
starts_d = []
def isname(x):
    x2 = x.strip()
    return 2 < len(x2) < 75 and ':' not in x2 and x2[0].isupper() and not x2.startswith(('•','-','Ver anexo','Relación')) and not re.fullmatch(r'[A-Z]', x2) and not JUNK.match(x2) and not x2.endswith(('.', ','))
for a, b in zip(nb, nb[1:]):
    if re.match(r'^\s*(Función|Funcion|Acción|Indicaciones)\s*:', V[b], re.I) and isname(V[a]):
        starts_d.append(a)
# also drugs where name and Función on same structure handled above
for k, a in enumerate(starts_d):
    end = starts_d[k + 1] if k + 1 < len(starts_d) else len(V)
    name = V[a].strip()
    body = V[a + 1:end]
    # split into fields
    fields = []; cur = None; buf = []
    for l in body:
        if JUNK.match(l.strip()): continue
        if re.fullmatch(r'[A-Z]', l.strip()): continue
        if l.strip().startswith(('Ver anexo', 'Relación de nombres comerciales')): continue
        m = FRE.match(l)
        if m:
            if cur: fields.append((cur, buf))
            cur = m.group(1).capitalize(); buf = [' ' * (len(l) - len(l.lstrip())) + l.strip()[m.end() - (len(l) - len(l.lstrip())):]]
        else:
            buf.append(l)
    if cur: fields.append((cur, buf))
    fd = []
    for f, bl in fields:
        blk = parse(bl)
        fd.append({'f': f, 'b': blk})
    drugs.append({'n': name, 'f': fd})

abbr = []
for p, l in L[abre + 1:colab]:
    s = l.rstrip()
    if not s.strip() or JUNK.match(s.strip()) or re.fullmatch(r'[A-Z]', s.strip()): continue
    m = re.match(r'^(\S.{0,40}?)\s{3,}(\S.*)$', s)
    if m: abbr.append([m.group(1).strip(), m.group(2).strip()])
    elif abbr and s.startswith(' ' * 20): abbr[-1][1] += ' ' + s.strip()

data = {'procs': procs, 'drugs': drugs, 'abbr': abbr,
        'tree': [{'id': a[0], 'name': a[1], 'desc': a[2], 'icon': a[3], 'groups': [{'name': g[0], 'icon': g[1]} for g in a[4]]} for a in TREE]}
json.dump(data, open('data.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(procs), 'procs', len(drugs), 'drugs', len(abbr), 'abbr')
print('size', len(json.dumps(data, ensure_ascii=False)))
