# usage: python tools/tap.py <x> <y>  : 하단 화면 좌표(0~319,0~239)를 백그라운드 클릭으로 터치
import sys,os,time,ctypes,ctypes.wintypes as W
sys.path.insert(0,os.path.dirname(__file__))
from emu import *
import myproc
x,y=int(sys.argv[1]),int(sys.argv[2])
h=[w for p in myproc.mypids() for w in wins(p) if title(w).startswith(('Azahar','Lime'))][0]
im=capture(h);import numpy as np;a=np.array(im)
r=W.RECT();u.GetWindowRect(h,ctypes.byref(r));cr=W.RECT();u.GetClientRect(h,ctypes.byref(cr))
pt=W.POINT(0,0);u.ClientToScreen(h,ctypes.byref(pt));ox,oy=pt.x-r.left,pt.y-r.top
# 하단 화면 = 창 안 320x240 영역(상단 400x240 아래, 가운데 정렬) 추정
H=im.size[1];body=a[60:H-40];rows=np.nonzero(body.max(axis=(1,2))>20)[0]
top=60+rows.min();cw=im.size[0];sx=(cw-320)//2
gx,gy=sx+x,top+240+y  # 창 기준
cx,cy=gx-ox,gy-oy     # 클라이언트 기준
child=u.ChildWindowFromPoint(h,W.POINT(cx,cy)) or h
pt2=W.POINT(gx+r.left,gy+r.top);u.ScreenToClient(child,ctypes.byref(pt2))
lp=(pt2.y<<16)|(pt2.x&0xffff)
u.PostMessageW(child,0x201,1,lp);time.sleep(0.15);u.PostMessageW(child,0x202,0,lp);print('tap',cx,cy)
