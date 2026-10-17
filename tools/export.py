import sys,glob,os,json,re,collections
sys.path.insert(0,os.path.dirname(__file__));import mbb2,dec
G=dec.G
def tok(a):
    o=[];i=0
    while i<len(a):
        v=a[i]
        if v==0x8001: o.append('\n');i+=1;continue
        if v>=0x8000:
            j=i+1
            while j<len(a) and a[j]==1: j+=1
            n=j-i-1
            o.append('{%x%s}'%(v,'*%d'%n if n else ''));i=j;continue
        if 0<v<=len(G) and G[v-1]!='\0': o.append(G[v-1])
        else: o.append('{g%d}'%v)
        i+=1
    return ''.join(o)
if __name__=='__main__':
    root='ext/romfs/'
    U=collections.OrderedDict()
    for f in sorted(glob.glob(root+'Table/**/*.mbb',recursive=True)):
        rel=f[len(root):].replace(chr(92),'/')
        if 'StaffRoll' in rel or 'TestData' in rel or rel.endswith('Enemy/SystemMessage.mbb'): continue
        for ti,tb in enumerate(mbb2.parse(open(f,"rb").read())):
            x=mbb2.strings(tb)
            for si,s in enumerate(x):
                if not s or isinstance(s,tuple): continue
                if all(v==1 for v in s): continue
                t=tok(s)
                U.setdefault(t,[]).append('%s:%d:%d'%(rel,ti,si))
    json.dump([{'jp':k,'refs':v} for k,v in U.items()],open('strings.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
    print(len(U))
