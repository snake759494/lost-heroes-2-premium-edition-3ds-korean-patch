# 전체 팩의 모든 CTPK 텍스처 원본 바이트 md5 표 → tex/allhash.json [[pack,tpc,name,md5],...]
import sys,os,glob,json,hashlib
sys.path.insert(0,os.path.dirname(__file__))
from lz11 import comp_dec;import nbf,ctpk
B=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..');res=[]
for f in sorted(glob.glob(B+'/ext/romfs/**/*_pk.cmp',recursive=True)):
    r='ext/romfs/'+os.path.relpath(f,B+'/ext/romfs').replace(chr(92),'/')
    try: ents,_=nbf.parse(comp_dec(open(f,'rb').read()))
    except Exception: continue
    for n,data,b in ents:
        if n.endswith('.tpc') and data[:4]==b'GFPT':
            for e in ctpk.entries(data):
                res.append([r,n,e['name'],hashlib.md5(data[e['pos']:e['pos']+e['size']]).hexdigest()])
json.dump(res,open(B+'/tex/allhash.json','w'));print(len(res))
