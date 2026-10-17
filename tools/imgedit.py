# 텍스처 한글화 명세 적용기
# usage: python tools/imgedit.py <id> [<id>...]   (tex/edits/<id>.json -> tex/ko/<id>.png + tex/preview/<id>.png)
# 명세: {"ops":[ ... ]} 순서대로 적용. 좌표는 원본 텍스처 픽셀 [x0,y0,x1,y1] (x1,y1 미포함)
#  {"erase":[box]}                       투명화(알파 0)
#  {"fill":[box],"color":[r,g,b,a]}      단색 채우기
#  {"inpaint":[box],"mask":"bright|all"} 배경 복원(OpenCV), 알파 유지
#  {"copy":[sx0,sy0,sx1,sy1],"to":[dx,dy]} 원본 영역 복사
#  {"text":"한글","box":[box],"font":"NanumSquareNeo-eHv.ttf","size":0(자동),
#   "color":[r,g,b] | "auto", "grad":[[r,g,b],[r,g,b]], "stroke":0, "stroke_color":[r,g,b] | "auto",
#   "align":"center|left|right","valign":"center|top|bottom","scale_x":1.0,"spacing":0,"glow":0,"glow_color":[r,g,b]}
import sys,os,json
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont,ImageFilter
B=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
FD=os.path.join(B,'..')
SS=4
def font(name,px): return ImageFont.truetype(os.path.join(FD,name),px)
def auto_colors(orig,box):
    x0,y0,x1,y1=box;r=orig[y0:y1,x0:x1].reshape(-1,4).astype(int)
    r=r[r[:,3]>160]
    if len(r)<4: return (255,255,255),(0,0,0)
    L=r[:,:3].mean(1);o=np.argsort(L)
    hi=r[o[-max(1,len(o)//5):],:3].mean(0);lo=r[o[:max(1,len(o)//5)],:3].mean(0)
    return tuple(int(v) for v in hi),tuple(int(v) for v in lo)
def render_text(img,orig,op):
    x0,y0,x1,y1=op['box'];bw,bh=x1-x0,y1-y0
    txt=op['text'];fn=op.get('font','NanumSquareNeo-eHv.ttf');sx=op.get('scale_x',1.0)
    st=op.get('stroke',0);sp=op.get('spacing',0);glow=op.get('glow',0)
    hi,lo=auto_colors(orig,op['box'])
    col=hi if op.get('color','auto')=='auto' else tuple(op['color'][:3])
    scol=lo if op.get('stroke_color','auto')=='auto' else tuple(op['stroke_color'][:3])
    lines=txt.split('\n')
    size=op.get('size',0)
    def measure(px):
        f=font(fn,px*SS);ws=[];asc,desc=f.getmetrics()
        for l in lines:
            w=sum(f.getlength(c) for c in l)+sp*SS*max(0,len(l)-1)
            ws.append(w*sx)
        lh=px*SS*op.get('line_h',1.15)
        return f,ws,lh,(len(lines)-1)*lh+px*SS
    if not size:
        size=max(4,bh//len(lines))
        while size>4:
            f,ws,lh,th=measure(size)
            if max(ws)+2*st*SS<=bw*SS and th+2*st*SS<=bh*SS*1.05: break
            size-=1
    f,ws,lh,th=measure(size)
    W,H=bw*SS,bh*SS
    layer=Image.new('L',(W,H),0);sl=Image.new('L',(W,H),0)
    al=op.get('align','center');va=op.get('valign','center')
    ty=(H-th)/2 if va=='center' else (st*SS if va=='top' else H-th-st*SS)
    ty+=op.get('dy',0)*SS
    for li,l in enumerate(lines):
        w=ws[li];tx=(W-w)/2 if al=='center' else (st*SS if al=='left' else W-w-st*SS)
        tx+=op.get('dx',0)*SS
        # 글자별로 그려 가로 압축/자간 적용
        cx=tx
        for c in l:
            cw=f.getlength(c)
            g=Image.new('L',(int(cw)+8*SS,int(size*SS*1.6)),0);d=ImageDraw.Draw(g)
            d.text((4*SS,0),c,font=f,fill=255)
            if sx!=1.0: g=g.resize((max(1,int(g.width*sx)),g.height),Image.LANCZOS)
            pos=(int(cx-4*SS*sx),int(ty+li*lh-size*SS*0.12))
            layer.paste(255,pos,g)
            cx+=cw*sx+sp*SS
    if st: sl=layer.filter(ImageFilter.MaxFilter(2*st*SS+1))
    mask=np.array(layer.resize((bw,bh),Image.LANCZOS)).astype(np.float32)/255
    smask=np.array(sl.resize((bw,bh),Image.LANCZOS)).astype(np.float32)/255 if st else np.zeros_like(mask)
    if glow:
        gm=np.array(layer.filter(ImageFilter.GaussianBlur(glow*SS)).resize((bw,bh),Image.LANCZOS)).astype(np.float32)/255
        gm=np.clip(gm*2.5,0,1);gc=np.array(op.get('glow_color',scol),np.float32)
    region=img[y0:y1,x0:x1].astype(np.float32)
    def over(region,m,c):
        c=np.array(c,np.float32)
        a=region[...,3:4]/255;m=m[...,None]
        rgb=region[...,:3]*a*(1-m)+c*m;na=a+m*(1-a)
        region[...,:3]=np.where(na>0,rgb/np.maximum(na,1e-6),0);region[...,3:4]=na*255
        return region
    if glow: region=over(region,gm,gc)
    if st: region=over(region,smask,scol)
    if 'grad' in op:
        g0,g1=[np.array(c,np.float32) for c in op['grad']]
        t=np.linspace(0,1,bh)[:,None,None];gr=g0*(1-t)+g1*t
        a=region[...,3:4]/255;m=mask[...,None]
        rgb=region[...,:3]*a*(1-m)+gr*m;na=a+m*(1-a)
        region[...,:3]=np.where(na>0,rgb/np.maximum(na,1e-6),0);region[...,3:4]=na*255
    else: region=over(region,mask,col)
    img[y0:y1,x0:x1]=np.clip(region,0,255).astype(np.uint8)
def apply(tid):
    spec=json.load(open(os.path.join(B,'tex','edits','%s.json'%tid),encoding='utf-8'))
    idx=json.load(open(os.path.join(B,'tex','index.json')))
    src=idx[int(tid)][6]
    orig=np.array(Image.open(os.path.join(B,src)).convert('RGBA'));img=orig.copy()
    for op in spec['ops']:
        if 'erase' in op: x0,y0,x1,y1=op['erase'];img[y0:y1,x0:x1,3]=0
        elif 'fill' in op: x0,y0,x1,y1=op['fill'];img[y0:y1,x0:x1]=op['color'] if len(op['color'])==4 else op['color']+[255]
        elif 'copy' in op:
            sx0,sy0,sx1,sy1=op['copy'];dx,dy=op['to'];img[dy:dy+sy1-sy0,dx:dx+sx1-sx0]=orig[sy0:sy1,sx0:sx1]
        elif 'inpaint' in op:
            x0,y0,x1,y1=op['inpaint'];m=np.zeros(img.shape[:2],np.uint8)
            sub=img[y0:y1,x0:x1,:3].astype(int)
            if op.get('mask','all')=='bright':
                L=sub.mean(2);m[y0:y1,x0:x1]=(L>op.get('thr',150)).astype(np.uint8)*255
                m=cv2.dilate(m,np.ones((3,3),np.uint8))
            else: m[y0:y1,x0:x1]=255
            rgb=cv2.inpaint(np.ascontiguousarray(img[...,:3]),m,3,cv2.INPAINT_TELEA);img[...,:3]=rgb
        elif 'text' in op: render_text(img,orig,op)
    os.makedirs(os.path.join(B,'tex','ko'),exist_ok=True);os.makedirs(os.path.join(B,'tex','preview'),exist_ok=True)
    Image.fromarray(img).save(os.path.join(B,'tex','ko','%s.png'%tid))
    # 미리보기: 원본 | 수정본, 회색 배경 위, 2배
    def flat(a):
        bg=Image.new('RGBA',(a.shape[1],a.shape[0]),(70,70,70,255));bg.alpha_composite(Image.fromarray(a));return bg.convert('RGB')
    h,w=img.shape[:2];sc=2 if max(w,h)<=256 else 1
    pv=Image.new('RGB',(w*2*sc+8,h*sc),(255,0,255))
    pv.paste(flat(orig).resize((w*sc,h*sc),Image.NEAREST),(0,0));pv.paste(flat(img).resize((w*sc,h*sc),Image.NEAREST),(w*sc+8,0))
    pv.save(os.path.join(B,'tex','preview','%s.png'%tid))
if __name__=='__main__':
    for t in sys.argv[1:]: apply(t);print('ok',t)
