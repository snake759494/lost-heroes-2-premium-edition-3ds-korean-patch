import numpy as np
from PIL import Image,ImageDraw,ImageFont
import os
FD=os.environ.get('LH2_FONT_DIR',os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))+'/'
def glyph(ch,font,box,cell):
    # render ch fitting box=(x0,y0,x1,y1) inclusive inside cell (w,h)
    bw=box[2]-box[0]+1;bh=box[3]-box[1]+1
    im=Image.new('L',(cell[0]*3,cell[1]*3));dr=ImageDraw.Draw(im)
    bb=dr.textbbox((0,0),ch,font=font,anchor='ls')
    # place using font-wide metrics: center horizontally on advance, vertical by ascent of '한'
    ref=dr.textbbox((0,0),'한',font=font,anchor='ls')
    adv=font.getlength(ch) if ch.strip() else 0
    x=box[0]+(bw-(ref[2]-ref[0]))/2-ref[0]
    if not ('\uac00'<=ch<='\ud7a3'): x=box[0]+(bw-(bb[2]-bb[0]))/2-bb[0]
    y=box[1]-ref[1]
    dr.text((x+cell[0],y+cell[1]),ch,fill=255,font=font,anchor='ls')
    a=np.array(im)[cell[1]:cell[1]*2,cell[0]:cell[0]*2]
    return a
def fontfor(name,size): return ImageFont.truetype(FD+name,size)
