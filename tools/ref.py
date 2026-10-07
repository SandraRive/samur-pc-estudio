import re,json,subprocess
t=subprocess.run(['pdftotext','-layout','-f','57','-l','65','m.pdf','-'],capture_output=True,text=True).stdout
t=t.replace('ﬁ','fi').replace('ﬂ','fl')
ls=[l.rstrip() for l in t.split('\n') if l.strip() and 'Home - Manual' not in l and not re.match(r'\s*Page \d+',l)]
def idx(s,start=0):
    return next(i for i in range(start,len(ls)) if ls[i].strip()==s)
# indicativos
sec=None; ind={'Particulares':[],'Generales':[],'Según base o función':[],'Bases':[],'Ajenos':[]}
a=idx('PARTICULARES'); b=idx('CLAVES')
cur=None
for l in ls[a:b]:
    s=l.strip()
    if s=='PARTICULARES': sec='Particulares'; continue
    if s=='GENERALES': sec='Generales'; continue
    if s.startswith('Según la base'): sec='Según base o función'; continue
    if s.startswith('Los indicativos de las bases'): sec='Bases'; continue
    if s=='Indicativos ajenos': sec='Ajenos'; continue
    if s in('Extraordinarios',) : sec=None; continue
    if not sec: continue
    m=re.match(r'^•\s*(.+?)(?::| - )\s*(.+)$',s)
    if m:
        cur=[m.group(1).strip(),m.group(2).strip()]; ind[sec].append(cur)
    elif cur and not s.startswith('•') and len(l)-len(l.lstrip())>3: cur[1]+=' '+s
    else: cur=None
# claves
a=idx('CLAVES'); b=idx('CÓDIGOS DE INCIDENTES')
claves=[];cur=None
for l in ls[a:b]:
    s=l.strip()
    m=re.match(r'^•\s*(clave [\w\.]+|Estatus \d+|CQ)\s*:\s*(.+)$',s,re.I)
    if m:
        k=m.group(1); k=re.sub(r'^clave ','',k,flags=re.I)
        cur=[k.upper() if k.lower()=='victor' else k,m.group(2).strip()]; claves.append(cur)
    elif cur and not s.startswith('•'): cur[1]+=' '+s
    else: cur=None
# codigos
a=idx('CÓDIGOS DE INCIDENTES'); b=idx('CÓDIGOS ESPECÍFICOS')
groups=[];cur=None
for l in ls[a:b]:
    s=l.strip()
    g=re.match(r'^(\d+)\.\s+([A-ZÁÉÍÓÚÑ ,y/]+)$',s)
    m=re.match(r'^(\d+(?:\.\d+)*)\s{3,}(.+)$',s)
    if g and not m:
        groups.append({'n':g.group(1),'name':g.group(2).strip().capitalize(),'c':[]}); cur=None; continue
    if m and groups:
        cur=[m.group(1),m.group(2).strip()]; groups[-1]['c'].append(cur)
    elif cur and len(l)-len(l.lstrip())>30 and not s.startswith('•'):
        cur[1]+=' '+s
# especificos
a=idx('CÓDIGOS ESPECÍFICOS'); b=next(i for i in range(a,len(ls)) if ls[i].strip().startswith('Ver anexo'))
esp=[];cur=None
for l in ls[a+1:b]:
    s=l.strip()
    m=re.match(r'^•\s*(Código [^-]+?)\s+-\s+(.+)$',s)
    if m: cur=[m.group(1),m.group(2)]; esp.append(cur)
    elif cur: cur[1]+=' '+s
json.dump({'ind':ind,'claves':claves,'codigos':groups,'esp':esp},open('ref.json','w'),ensure_ascii=False)
print({k:len(v) for k,v in ind.items()},len(claves),[(g['n'],g['name'],len(g['c'])) for g in groups],len(esp))
print(claves[:5],claves[-3:])
