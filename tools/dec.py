import os
G=open(os.path.join(os.path.dirname(__file__),'..','gmap.txt'),encoding='utf-8').read()
def dec(a):
    o=[]
    for v in a:
        if 0<v<=len(G) and G[v-1]!='\0': o.append(G[v-1])
        else: o.append('{%x}'%v)
    return ''.join(o)
