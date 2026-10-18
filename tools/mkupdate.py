# 한글 업데이트 CIA 빌드: 복호화된 v1.1.0 업데이트 CIA의 RomFS(대사·팩·이름판)를 본편 패치와 같은 글리프 표로 한글화
# usage: python tools/mkupdate.py <원본 업데이트.cia> <출력.cia>
import sys,os,io,json,glob,hashlib,struct
sys.path.insert(0,os.path.dirname(__file__))
import numpy as np
from PIL import Image
import mkpatch,build,nbf,ctpk,texenc,mbb2
from lz11 import comp_dec
B=mkpatch.B
al=lambda x,a:(x+a-1)//a*a

def texmap():
    # 원본 텍스처 바이트 md5 -> 한글 이미지 (본편 편집 + 업데이트 전용 편집)
    AH=json.load(open(B+'/tex/allhash.json'));key={(a,b,c):d for a,b,c,d in AH}
    tidx=json.load(open(B+'/tex/index.json'));m={}
    for ef in glob.glob(B+'/tex/edits/*.json'):
        tid=int(os.path.basename(ef)[:-5]);sp=json.load(open(ef,encoding='utf-8'))
        if sp.get('skip') or not os.path.exists(B+'/tex/ko/%d.png'%tid): continue
        r=tidx[tid];img=np.array(Image.open(B+'/tex/ko/%d.png'%tid).convert('RGBA'))
        if r[0].startswith('UPD:'):
            d=open(B+'/upd/romfs/'+r[1],'rb').read();e=[e for e in ctpk.entries(d) if e['name']==r[2]][0]
            m[hashlib.md5(d[e['pos']:e['pos']+e['size']]).hexdigest()]=img
        else:
            h=key.get(('ext/romfs/'+r[0],r[1],r[2]))
            if h: m[h]=img
    return m

def patch_tpc(d,tm):
    if d[:4]!=b'GFPT': return d,0
    t=bytearray(d);n=0
    for e in ctpk.entries(d):
        img=tm.get(hashlib.md5(d[e['pos']:e['pos']+e['size']]).hexdigest())
        if img is None: continue
        b=texenc.encode(e['fmt'],img);assert len(b)==e['size']
        t[e['pos']:e['pos']+e['size']]=b;n+=1
    return bytes(t),n

def main(src,out):
    tr=mkpatch.load_tr();fixed,newmap=mkpatch.make_map(tr);cmap=dict(fixed);cmap.update(newmap)
    tm=texmap()
    root=B+'/upd/romfs/';repl={};raws={};stat=[0,0]
    for f in sorted(glob.glob(root+'**/*',recursive=True)):
        if os.path.isdir(f): continue
        rel=os.path.relpath(f,root).replace(chr(92),'/');d=open(f,'rb').read()
        if rel.endswith('.mbb'):
            nb=mkpatch.trmbb(d,tr,cmap)
            if nb!=d: repl[rel]=nb;stat[0]+=1
        elif rel.endswith('.tpc'):
            nb,n=patch_tpc(d,tm)
            if n: repl[rel]=nb;stat[1]+=n
        elif rel.endswith('_pk.cmp'):
            ents,hdr=nbf.parse(comp_dec(d));ch=0
            for e in ents:
                if e[0].endswith('.mbb'):
                    nb=mkpatch.trmbb(e[1],tr,cmap)
                    if nb!=e[1]: e[1]=nb;ch+=1;stat[0]+=1
                elif e[0].endswith('.tpc'):
                    nb,n=patch_tpc(e[1],tm)
                    if n: e[1]=nb;ch+=1;stat[1]+=n
            if ch: raws[rel]=nbf.build(ents,hdr)
    repl.update(mkpatch.batch_comp(raws))
    print('mbb',stat[0],'textures',stat[1],'files',len(repl))
    if os.environ.get('LFS_OUT'):  # 업데이트가 바꾸는 파일도 한글판으로 덮어씀(업데이트 설치 여부와 무관하게 동작)
        for k,v in repl.items():
            p=os.path.join(os.environ['LFS_OUT'],k);os.makedirs(os.path.dirname(p),exist_ok=True);open(p,'wb').write(v)
    # --- NCCH 재조립 ---
    f=open(src,'rb');cia=bytearray(f.read())
    hs,typ,ver,cs,ts,tm_,ms,cz=struct.unpack_from('<IHHIIIIQ',cia,0)
    o_tmd=al(al(al(hs,64)+cs,64)+ts,64);o_c=al(o_tmd+tm_,64);o_meta=al(o_c+cz,64)
    nc=o_c;h=bytearray(cia[nc:nc+0x200]);g=lambda o:struct.unpack_from('<I',h,o)[0]*0x200
    rfo=g(0x1b0)
    tmp=io.BytesIO()
    class W:  # build_romfs가 쓰는 파일 인터페이스
        def write(self,b): tmp.write(b)
    f.seek(0);build.build_romfs(f,nc+rfo,repl,W())
    romfs=tmp.getvalue();rlen=len(romfs)
    pre=bytearray(cia[nc:nc+rfo])
    # 업데이트 실행 코드: 히어로 전기 래퍼 문자열(시스템 폰트) 영어화 후 비압축으로 교체
    import codeblz,codestr
    exo=struct.unpack_from('<I',pre,0x1a0)[0]*0x200;eh=pre[exo:exo+0x200]
    for k in range(10):
        nm,o,sz=struct.unpack_from('<8sII',eh,k*16)
        if nm.rstrip(bytes(1))==b'.code': code=bytes(pre[exo+0x200+o:exo+0x200+o+sz])
    if pre[0x20d]&1: code=codeblz.decompress(code)
    newcode,n16,n8=codestr.patch(code);print('code strings',n16,n8)
    if os.environ.get('LFS_OUT'): open(os.path.join(os.environ['LFS_OUT'],'..','code.bin'),'wb').write(newcode)
    pre,rfo=build.rebuild_exefs(pre,newcode)
    struct.pack_into('<I',pre,0x1b0,rfo//0x200)
    struct.pack_into('<I',pre,0x1b4,al(rlen,0x200)//0x200)
    pre[0x1e0:0x200]=hashlib.sha256(romfs[:0x200]).digest()
    total=al(rfo+rlen,0x200);struct.pack_into('<I',pre,0x104,total//0x200)
    ncch=bytes(pre)+romfs+b'\0'*(total-rfo-rlen)
    # --- CIA 재조립: 콘텐츠 교체, TMD 크기·해시 갱신 ---
    tmd=bytearray(cia[o_tmd:o_tmd+tm_]);H=0x140
    cnt=struct.unpack_from('>H',tmd,H+0x9E)[0];CR=H+0xC4+64*0x24
    struct.pack_into('>Q',tmd,CR+8,len(ncch));tmd[CR+0x10:CR+0x30]=hashlib.sha256(ncch).digest()
    tmd[H+0xC4+4:H+0xC4+0x24]=hashlib.sha256(bytes(tmd[CR:CR+0x30*cnt])).digest()
    tmd[H+0xA4:H+0xC4]=hashlib.sha256(bytes(tmd[H+0xC4:H+0xC4+64*0x24])).digest()
    meta=bytes(cia[o_meta:o_meta+ms]) if ms else b''
    hdr=bytearray(cia[:o_tmd]);struct.pack_into('<Q',hdr,0x18,len(ncch))
    outb=bytes(hdr)+bytes(tmd);outb+=b'\0'*(al(len(outb),64)-len(outb))+ncch
    outb+=b'\0'*(al(len(outb),64)-len(outb))+meta
    open(out,'wb').write(outb);print('built',out,len(outb))

if __name__=='__main__': main(sys.argv[1],sys.argv[2])
