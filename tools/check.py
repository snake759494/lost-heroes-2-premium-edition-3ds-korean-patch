# usage: python check.py <in.json> <out.json>
import json,re,sys,os
G=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','gmap.txt'),encoding='utf-8').read()
OK=set(G[:64])|set(G[233:363])|set(' \n')|{'~','…','★','·','『','』'}
OK.discard('\0')
def L(s): return sum(0.5 if ord(c)<0x80 and c!=' ' else 1 for c in re.sub(r'\{[^}]*\}','　',s))
inp=json.load(open(sys.argv[1],encoding='utf-8'));out=json.load(open(sys.argv[2],encoding='utf-8'))
err=0
for e in inp:
    k=str(e['i'])
    if k not in out: print('MISSING',k);err+=1;continue
    ko=out[k]
    tj=re.findall(r'\{[^}]*\}',e['jp']);tk=re.findall(r'\{[^}]*\}',ko)
    if sorted(tj)!=sorted(tk): print('TOKEN',k,tj,tk);err+=1
    bad={c for c in re.sub(r'\{[^}]*\}','',ko) if not ('가'<=c<='힣' or c in OK)}
    if bad: print('CHAR',k,''.join(sorted(bad)),ko);err+=1
    lines=ko.split('\n')
    if len(lines)>e['max_lines']: print('LINES',k,len(lines),'>',e['max_lines'],repr(ko));err+=1
    for l in lines:
        if L(l)>e['max_line']: print('WIDTH',k,L(l),'>',e['max_line'],repr(l));err+=1
print('errors',err,'of',len(inp))
