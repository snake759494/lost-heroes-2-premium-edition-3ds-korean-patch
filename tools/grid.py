# usage: python tools/grid.py <id> [scale] [x0 y0 x1 y1]  -> tex/grid/<id>.png  (16px 격자, 좌표 라벨)
import sys,os,json
from PIL import Image,ImageDraw
B=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
tid=sys.argv[1];idx=json.load(open(B+'/tex/index.json'))
im=Image.open(B+'/'+idx[int(tid)][6]).convert('RGBA')
if len(sys.argv)>6: im=im.crop(tuple(map(int,sys.argv[3:7])));ox,oy=map(int,sys.argv[3:5])
else: ox=oy=0
sc=int(sys.argv[2]) if len(sys.argv)>2 else max(1,min(4,1024//max(im.size)))
bg=Image.new('RGBA',im.size,(60,60,60,255));bg.alpha_composite(im)
g=bg.convert('RGB').resize((im.width*sc,im.height*sc),Image.NEAREST);d=ImageDraw.Draw(g)
for x in range(0,im.width,16):
    d.line([(x*sc,0),(x*sc,g.height)],fill=(255,0,255) if (x+ox)%64==0 else (120,0,120))
    if (x+ox)%32==0: d.text((x*sc+1,1),str(x+ox),fill=(255,255,0))
for y in range(0,im.height,16):
    d.line([(0,y*sc),(g.width,y*sc)],fill=(255,0,255) if (y+oy)%64==0 else (120,0,120))
    if (y+oy)%32==0: d.text((1,y*sc+1),str(y+oy),fill=(0,255,255))
os.makedirs(B+'/tex/grid',exist_ok=True);g.save(B+'/tex/grid/%s.png'%tid);print(g.size)
