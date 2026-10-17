# 한글 패치 빌드: 번역 적용(mbb) + 한글 폰트(Font14/Font10) + ROM 재조립
import sys,os,json,glob,re,struct
sys.path.insert(0,os.path.dirname(__file__))
import numpy as np
import mbb2,export,tex,gfpt,hfont,build
from lz11 import comp_dec,comp_enc
B=os.path.join(os.path.dirname(__file__),'..')
ROM=os.environ.get('LH2_ROM',os.path.join(B,'..','Lost Heroes 2 (Premium Edition) (Japan).3ds'))
G=export.G

def load_tr():
    old=json.load(open(B+'/strings_old.json',encoding='utf-8'))
    new=json.load(open(B+'/strings.json',encoding='utf-8'))
    tr={}
    for f in sorted(glob.glob(B+'/tr/out/c[0-9][0-9][0-9].json')):
        try: dd=json.load(open(f,encoding='utf-8'))
        except Exception: print('skip',f);continue
        for k,v in dd.items():
            i=int(k)
            if i>=200000: continue
            jp=old[i]['jp'] if i<100000 else new[i-100000]['jp']
            tr[jp]=v
    UNIFY=[('카풀','카프루'),('카프르','카프루'),('안크','앙크'),('스파크 돌즈','스파크 돌스'),('마레브란데스','말레브란데스'),
           ('풍도','후토'),('소매 부대','소데츠키'),('DG세포','DG 세포'),('이매진','이마진')]
    for k in tr:
        v=tr[k]
        for a,b in UNIFY: v=v.replace(a,b)
        tr[k]=v
    fx=B+'/tr/fix.json'
    if os.path.exists(fx): tr.update(json.load(open(fx,encoding='utf-8')))
    return tr

KEEP=list(range(0,64))+list(range(233,363))
FREE=list(range(363,2646))+list(range(64,233))
TOK=re.compile(r'\{([0-9a-fg]+)(?:\*(\d+))?\}')

def batch_comp(raws):
    import subprocess,shutil
    T=os.path.abspath(B+'/tmp_lz');os.makedirs(T,exist_ok=True);L=[];keys=list(raws)
    for i,k in enumerate(keys):
        open(T+'/%d.raw'%i,'wb').write(raws[k]);L.append(T+'/%d.raw'%i+chr(9)+T+'/%d.cmp'%i)
    open(T+'/list.txt','w',encoding='utf-8').write(chr(10).join(L))
    subprocess.run([os.path.abspath(B+'/lz11c/bin/lz11c.exe'),T+'/list.txt'],check=True)
    out={k:open(T+'/%d.cmp'%i,'rb').read() for i,k in enumerate(keys)}
    shutil.rmtree(T);return out

def trmbb(b,tr,cmap):
    t=mbb2.parse(b)
    for tb in t:
        x=mbb2.strings(tb)
        for i,s in enumerate(x):
            if s and not isinstance(s,tuple) and not all(v==1 for v in s):
                j=export.tok(s)
                if j in tr: x[i]=encode(tr[j],cmap)
    return mbb2.build(t)

NL=chr(10)
def staff_patch():
    # 엔딩 스태프롤: 전용 폰트(FontStaff 15x16, 17열) 재구성 + StaffRoll*.mbb 인코딩
    GS=open(B+'/gstaff.txt',encoding='utf-8').read()
    ci=json.load(open(B+'/tr/in/c064.json',encoding='utf-8'));co=json.load(open(B+'/tr/out/c064.json',encoding='utf-8'))
    st={e['jp']:co[str(e['i'])] for e in ci}
    def dec(a):
        o=''
        for v in a:
            if v==0x8001: o+=NL
            elif v>=0x8000: o+='{%x}'%v
            elif v==1: o+='　'
            else: o+=GS[v-1] if GS[v-1]!='\0' else '{g%d}'%v
        return o
    chars=sorted({c for v in st.values() for c in TOK.sub('',v)}-{NL,'*',' ','　'})
    slots=[i for i in range(2,17*32) if i not in (1,15)]
    assert len(chars)<=len(slots),len(chars)
    smap={c:slots[k] for k,c in enumerate(chars)};smap['*']=1;smap[' ']=15;smap['　']=15
    def enc(t):
        out=[];p=0
        for m in TOK.finditer(t):
            for c in t[p:m.start()]: out.append(0x8001 if c==NL else smap[c]+1)
            g=m.group(1);out.append(int(g[1:]) if g[0]=='g' else int(g,16));p=m.end()
        for c in t[p:]: out.append(0x8001 if c==NL else smap[c]+1)
        return out
    res={}
    for f in sorted(glob.glob(B+'/ext/romfs/Table/StaffRoll/*.mbb')):
        tabs=mbb2.parse(open(f,'rb').read())
        for tb in tabs:
            x=mbb2.strings(tb)
            for i,a in enumerate(x):
                if a and not isinstance(a,tuple):
                    j=dec(a)
                    if j in st: x[i]=enc(st[j])
        res['Table/StaffRoll/'+os.path.basename(f)]=mbb2.build(tabs)
    d=bytearray(comp_dec(open(B+'/ext/romfs/Font/FontStaff.cmp','rb').read()));T=gfpt.textures(d)[0]
    im=tex.untile4(bytes(d[T['pos']:T['pos']+T['size']]),256,512).copy()
    keep={0,1,15};f=hfont.fontfor('SeoulHangangM.ttf',14)
    for s_ in range(17*32):
        if s_ in keep: continue
        r,c=s_//17,s_%17;im[r*16:(r+1)*16,c*15:(c+1)*15]=0
    for ch_,s_ in smap.items():
        if s_ in keep: continue
        r,c=s_//17,s_%17
        g=hfont.glyph(ch_,f,(0,1,13,14),(15,16));im[r*16:(r+1)*16,c*15:(c+1)*15]=(np.round(g/17.0)*17).astype(np.uint8)
    d[T['pos']:T['pos']+T['size']]=tex.tile4(im)
    res['Font/FontStaff.cmp']=bytes(d)
    print('staff chars',len(chars))
    return res

def make_map(tr):
    fixed={}
    for s in KEEP:
        if G[s]!='\0' and G[s] not in fixed: fixed[G[s]]=s
    fixed.pop('　',None)
    fixed['!']=233
    chars=set()
    for v in tr.values(): chars|=set(TOK.sub('',v))
    chars.discard('\n')
    chars.add(' ')
    need=sorted(c for c in chars if c not in fixed)
    assert len(need)<=len(FREE),(len(need),len(FREE))
    newmap={c:FREE[i] for i,c in enumerate(need)}
    return fixed,newmap

def encode(s,cmap):
    out=[];p=0
    for m in TOK.finditer(s):
        for c in s[p:m.start()]: out.append(0x8001 if c=='\n' else cmap[' ' if c=='　' else c]+1)
        t=m.group(1)
        if t[0]=='g': out.append(int(t[1:]))
        else:
            out.append(int(t,16));out+= [1]*int(m.group(2) or 0)
        p=m.end()
    for c in s[p:]: out.append(0x8001 if c=='\n' else cmap[' ' if c=='　' else c]+1)
    return out

def patch_font(name,newmap,cw,ch,ncol,fontfile,size,box):
    raw=comp_dec(open(B+'/ext/romfs/Font/%s.cmp'%name,'rb').read())
    d=bytearray(raw);T=gfpt.textures(d)
    per=ncol*(512//ch)
    ims=[tex.untile4(bytes(d[t['pos']:t['pos']+t['size']]),t['w'],t['h']).copy() for t in T]
    f=hfont.fontfor(fontfile,size)
    cap=per*len(T)
    for s in FREE:
        if s>=cap: continue
        t,r,c=s//per,(s%per)//ncol,s%ncol
        ims[t][r*ch:(r+1)*ch,c*cw:(c+1)*cw]=0
    for c,s in newmap.items():
        if s>=cap: continue
        t,r,cc=s//per,(s%per)//ncol,s%ncol
        g=hfont.glyph(c,f,box,(cw,ch))
        ims[t][r*ch:(r+1)*ch,cc*cw:(cc+1)*cw]=(np.round(g/17.0)*17).astype(np.uint8)
    for t,im in zip(T,ims):
        d[t['pos']:t['pos']+t['size']]=tex.tile4(im)
    return bytes(d),ims

def main(out):
    tr=load_tr()
    fixed,newmap=make_map(tr)
    cmap=dict(fixed);cmap.update(newmap)
    print('translations',len(tr),'new glyphs',len(newmap))
    repl={};miss=set()
    root=B+'/ext/romfs/'
    for f in sorted(glob.glob(root+'Table/**/*.mbb',recursive=True)):
        rel=f[len(root):].replace(chr(92),'/')
        if 'StaffRoll' in rel or 'TestData' in rel or rel.endswith('Enemy/SystemMessage.mbb'): continue
        d=open(f,'rb').read();tabs=mbb2.parse(d);ch=False
        for tb in tabs:
            x=mbb2.strings(tb)
            for i,s in enumerate(x):
                if not s or isinstance(s,tuple) or all(v==1 for v in s): continue
                jp=export.tok(s)
                if jp in tr: x[i]=encode(tr[jp],cmap);ch=True
                else: miss.add(jp)
        if ch: repl[rel]=mbb2.build(tabs)
    print('untranslated',len(miss))
    json.dump(sorted(miss),open(B+'/untranslated.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
    f14,ims14=patch_font('Font14',newmap,14,16,18,'NanumSquareNeo-cBd.ttf',14,(0,1,12,13))
    f10,ims10=patch_font('Font10',newmap,12,12,21,'NanumSquareNeo-cBd.ttf',10,(0,1,10,10))
    raws={'Font/Font14.cmp':f14,'Font/Font10.cmp':f10}
    raws.update(staff_patch())
    inner={k:v for k,v in repl.items() if k.endswith('.mbb')}
    inner['Font/Font14.tpc']=f14;inner['Font/Font10.tpc']=f10
    import nbf
    packs=json.load(open(B+'/packs.json'))
    # 이미지 교체: tex/edits/<id>.json(skip 아님) + tex/ko/<id>.png → 같은 해시 그룹 전체
    import ctpk,texenc
    from PIL import Image as _I
    tidx=json.load(open(B+'/tex/index.json'));groups=json.load(open(B+'/tex/uniq.json'))
    gmap={g[0]:g for g in groups};texp={}
    AH=json.load(open(B+'/tex/allhash.json'));hkey={(a,b,c):d for a,b,c,d in AH};byhash={}
    for a,b,c,d in AH: byhash.setdefault(d,[]).append((a,b,c))
    for ef in glob.glob(B+'/tex/edits/*.json'):
        tid=int(os.path.basename(ef)[:-5]);sp=json.load(open(ef,encoding='utf-8'))
        if sp.get('skip') or not os.path.exists(B+'/tex/ko/%d.png'%tid): continue
        img=np.array(_I.open(B+'/tex/ko/%d.png'%tid).convert('RGBA'))
        r=tidx[tid];h=hkey.get(('ext/romfs/'+r[0],r[1],r[2]))
        for (pk_,tp_,nm_) in byhash.get(h,[('ext/romfs/'+r[0],r[1],r[2])]):
            texp.setdefault(pk_,{})[(tp_,nm_)]=img
    print('texture edits',sum(len(v) for v in texp.values()))
    packs=list(dict.fromkeys(list(packs)+list(texp)))
    if os.environ.get('PACKS'): packs=[p for p in packs if any(x in p for x in os.environ['PACKS'].split(','))]
    for pf in packs:
        rel=pf[len('ext/romfs/'):]
        d=comp_dec(open(B+'/'+pf,'rb').read());ents,hdr=nbf.parse(d);ch=0
        for e in ents:
            k=e[0].replace(chr(92),'/')
            if k in inner: e[1]=inner[k];ch+=1
            elif k.endswith('.mbb') and 'StaffRoll' not in k and 'TestData' not in k:
                nb=trmbb(e[1],tr,cmap)
                if nb!=e[1]: e[1]=nb;ch+=1
            if pf in texp and k.endswith('.tpc') and e[1][:4]==b'GFPT':
                t=bytearray(e[1])
                for te in ctpk.entries(e[1]):
                    im=texp[pf].get((e[0],te['name']))
                    if im is None: continue
                    b=texenc.encode(te['fmt'],im);assert len(b)==te['size']
                    t[te['pos']:te['pos']+te['size']]=b;ch+=1
                e[1]=bytes(t)
        if ch: raws[rel]=nbf.build(ents,hdr)
    repl.update(batch_comp(raws))
    print('packs patched',sum(1 for k in repl if k.endswith('_pk.cmp') or k.endswith('.cmp')))
    from PIL import Image
    Image.fromarray(np.hstack(ims14)).save(B+'/font14_ko.png');Image.fromarray(np.hstack(ims10)).save(B+'/font10_ko.png')
    json.dump({c:s for c,s in cmap.items()},open(B+'/charmap.json','w',encoding='utf-8'),ensure_ascii=False)
    build.build(ROM,out,repl)
    print('built',out)
if __name__=='__main__':
    main(sys.argv[1])
