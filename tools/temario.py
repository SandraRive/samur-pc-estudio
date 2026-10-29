"""Busca, para cada pregunta, el párrafo del manual donde está la respuesta.

Lo usa tools/juegos.py. Puntúa cada bloque del manual con las palabras de la
respuesta correcta (peso alto), la explicación y la pregunta, ponderadas por lo
raras que son en el manual (IDF). Las preguntas de un procedimiento buscan solo
en ese procedimiento; las de un bloque, en sus procedimientos; las del examen
oficial, en todo el manual. Si no hay una coincidencia clara no se devuelve
nada (por ejemplo, en preguntas de legislación que no está en el manual).
"""
import math, re, unicodedata
from collections import Counter

STOP = set('''de la el los las un una unos unas y o u a en con por para del al se su sus que es son lo le les
como mas pero si no ni ya muy sin sobre entre hasta desde cuando donde quien cual cuales este esta estos estas
ese esa esos esas aquel otro otra otros otras todo toda todos todas ser estar haber tiene tienen debe deben puede
pueden sera han ha hay fue era sea esto eso cada tras ante bajo segun mismo misma caso casos paciente
pacientes realice realizar valore valorar procedimiento samur manual proteccion civil unidad unidades
correcta correcto incorrecta respuesta respuestas siguientes siguiente indica'''.split())

def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')

def toks(s):
    return {w for w in re.findall(r'[a-z0-9]+(?:[\.,][0-9]+)?', norm(s)) if (len(w) > 2 or w.isdigit()) and w not in STOP}

class Temario:
    def __init__(self, D):
        self.procs = {p['id']: p for p in D['procs']}
        self.by_group = {}
        for p in D['procs']:
            self.by_group.setdefault((p['amb'], p['grp']), []).append(p['id'])
        self.cand = {}   # pid -> list of (texto, encabezado, tokens_nucleo, tokens_ventana)
        df = Counter(); n = 0
        for p in D['procs']:
            raw = []; head = ''
            for b in p['b']:
                x = re.sub(r'\s+', ' ', b.get('x', '')).strip()
                if not x: continue
                if b['t'] == 'pre': raw.append(None); continue   # tablas: el texto sale desordenado
                if b['t'] in ('h', 'lab') and len(x) < 120:
                    head = x.rstrip(':'); raw.append(None); continue
                raw.append((x, head)); n += 1
                for w in toks(x): df[w] += 1
            cands = []
            for i, r in enumerate(raw):
                if r is None: continue
                x, h = r; txt = x; j = i + 1
                while len(txt) < 220 and j < len(raw) and raw[j] is not None:
                    txt += ' ' + raw[j][0]; j += 1
                ht = toks(h)
                cands.append((txt, h, toks(x) | ht, toks(txt) | ht))
            self.cand[p['id']] = cands
        self.idf = Counter({w: math.log((n + 1) / (c + 0.5)) for w, c in df.items()})
        self.maxidf = math.log(n + 1)

    def _w(self, w):
        return self.idf.get(w, self.maxidf)

    def _score(self, tw, qa, qe, qq):
        s = sum(3.0 * self._w(w) for w in qa & tw) + sum(1.2 * self._w(w) for w in qe & tw) + sum(0.8 * self._w(w) for w in qq & tw)
        return s / (1 + 0.15 * math.log(1 + len(tw)))

    def find(self, q, a, e, pids, strict=False):
        qa = toks(a); qe = toks(e) - qa; qq = toks(q) - qa - qe
        need = qa | qe
        if not need: return None
        best = None
        for pid in pids:
            for txt, h, core, win in self.cand.get(pid, []):
                if not (need & win): continue
                sc = self._score(core, qa, qe, qq) + 0.35 * self._score(win, qa, qe, qq)
                if not best or sc > best[0]:
                    best = (sc, pid, h, txt, win)
        if not best: return None
        sc, pid, h, txt, win = best
        cover = sum(self._w(w) for w in need & win) / max(1e-9, sum(self._w(w) for w in need))
        if cover < (0.6 if strict else 0.34) or sc < (9 if strict else 4): return None
        if len(txt) > 520:
            txt = txt[:520].rsplit(' ', 1)[0] + '…'
        return {'p': pid, 'pt': self.procs[pid]['title'], 'h': h, 'x': txt}

    def pids_for(self, s):
        if s.get('p'): return [s['p']]
        return self.by_group.get((s['amb'], s['g']), [])

    def all_pids(self):
        return list(self.procs)
