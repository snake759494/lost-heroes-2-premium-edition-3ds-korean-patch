import numpy as np,struct,sys
from PIL import Image,ImageDraw,ImageFont
CW,CH=15,16
a=np.array(Image.open(sys.argv[1])).astype(np.float32)/255  # hstack of textures 256x512
ntex=a.shape[1]//256
cells=[]
for t in range(ntex):
    for r in range(512//CH):
        for c in range(256//CW):
            cells.append(a[r*CH:(r+1)*CH,t*256+c*CW:t*256+(c+1)*CW])
cells=np.array(cells);N=len(cells)
d=open('code.bin','rb').read();s=0x360ffa;e=0x364830
t=struct.unpack_from('<%dH'%((e-s)//2),d,s)
cands=sorted(set(chr(x) for x in t if x!=0xffff)|set(chr(i) for i in range(0x21,0x7f)))
fonts=[ImageFont.truetype('C:/Windows/Fonts/'+f,sz) for f in ['yumin.ttf','BIZ-UDMinchoM.ttc','yumindb.ttf'] for sz in (14,15)]
P=8
def render(ch,font):
    im=Image.new('L',(CW+2*P,CH+2*P));dr=ImageDraw.Draw(im)
    bb=dr.textbbox((0,0),ch,font=font)
    if bb[2]<=bb[0]: return None
    return im,bb
def nz(v):
    v=v-v.mean(-1,keepdims=True);n=np.linalg.norm(v,axis=-1,keepdims=True);return v/np.maximum(n,1e-6)
# cell vectors: compare via bbox-normalized images 24x24 + aspect/size features
def norm_img(g):
    ys,xs=np.nonzero(g>0.3)
    if len(ys)==0: return None
    y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
    sub=Image.fromarray((g[y0:y1,x0:x1]*255).astype(np.uint8))
    return np.array(sub.resize((20,20),Image.BILINEAR),np.float32).ravel()/255,(y1-y0,x1-x0,y0)
cv=[];cinfo=[];empty=[]
for i,g in enumerate(cells):
    r=norm_img(g)
    if r is None: empty.append(i);cv.append(np.zeros(400,np.float32));cinfo.append((0,0,0))
    else: cv.append(r[0]);cinfo.append(r[1])
cv=nz(np.array(cv));cinfo=np.array(cinfo,np.float32)
kv=[];kinfo=[];kch=[]
for f in fonts:
    for ch in cands:
        im=Image.new('L',(40,40));dr=ImageDraw.Draw(im);dr.text((8,4),ch,fill=255,font=f)
        g=np.array(im,np.float32)/255
        # scale to ~ cell height: fonts already approx size
        r=norm_img(g)
        if r is None: continue
        kv.append(r[0]);kinfo.append(r[1]);kch.append(ch)
kv=nz(np.array(kv));kinfo=np.array(kinfo,np.float32);kch=np.array(kch)
S=cv@kv.T  # N x K
# penalize size mismatch (h,w)
dh=np.abs(cinfo[:,None,0]-kinfo[None,:,0]);dw=np.abs(cinfo[:,None,1]-kinfo[None,:,1])
S=S-0.03*(dh+dw)
best=S.argmax(1)
out=[]
for i in range(N):
    if i in empty: out.append('\0');continue
    out.append(kch[best[i]])
open(sys.argv[2],'w',encoding='utf-8').write(''.join(out))
sc=S[np.arange(N),best]
np.save(sys.argv[2]+'.score.npy',sc)
