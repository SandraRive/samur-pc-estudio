import json,re,os
D=json.load(open('data.json')); R=json.load(open('ref.json'))
M={'users':'users','shield':'shield-check','hand':'hand-helping','phone':'phone-call','message':'message-square-heart','chat':'messages-square','route':'route','link':'link-2','heart-hand':'heart-handshake','code':'hash','truck':'truck','alert':'triangle-alert','brain':'brain','lungs':'wind','flask':'flask-conical','heart':'heart','stomach':'stethoscope','drop':'droplet','kidney':'bean','neuro':'brain-circuit','baby':'baby','child':'smile','bolt':'zap','mind':'brain-cog','bone':'bone','pulse':'activity','eye':'eye','tools':'wrench','wave':'audio-waveform','soap':'sparkles','tube':'pipette','bandage':'bandage','syringe':'syringe','cross':'briefcase-medical','clipboard':'clipboard-list','headset':'headset','siren':'siren'}
for a in D['tree']:
    a['icon']=M.get(a['icon'],a['icon'])
    for g in a['groups']: g['icon']=M.get(g['icon'],g['icon'])
D['tree'][-1]['icon']='syringe'
need=set(M.values())|set('search check circle-check ban package info list-checks target git-merge shield-alert book-open gamepad-2 trophy flame shuffle arrow-left arrow-right x chevron-right file-text clock timer star radio ambulance hospital sun moon book-a library thermometer octagon-alert lightbulb house badge-check circle-x rotate-ccw medal crosshair layers heart-pulse pill brain list-ordered map-pin vest bookmark sparkle'.split())
icons={}
for n in need:
    f=f'node_modules/lucide-static/icons/{n}.svg'
    if not os.path.exists(f): continue
    s=open(f).read(); inner=re.search(r'<svg[^>]*>\s*(.*)</svg>',s,re.S).group(1)
    icons[n]=re.sub(r'\s+',' ',inner).strip()
t=open('template.html').read()
t=t.replace('/*DATA*/',json.dumps(D,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
t=t.replace('/*REF*/',json.dumps(R,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
t=t.replace('/*ICONS*/',json.dumps(icons,separators=(',',':')))
open('samur-manual.html','w').write(t)
print(len(t))
