# usage: python tools/place_base.py <.3ds> <sdmc 루트>  : 본편 NCCH(파티션0)를 설치 경로에 배치(히어로 전기의 자기 재실행용)
import sys,os,struct
rom,sd=sys.argv[1],sys.argv[2]
f=open(rom,'rb');f.seek(0x120);p=struct.unpack('<16I',f.read(64))
o,s=p[0]*0x200,p[1]*0x200
d=os.path.join(sd,'Nintendo 3DS','0'*32,'0'*32,'title','00040000','00146c00','content');os.makedirs(d,exist_ok=True)
f.seek(o);out=open(os.path.join(d,'00000000.app'),'wb')
while s>0:
    b=f.read(min(s,1<<24));out.write(b);s-=len(b)
out.close();print('placed',os.path.join(d,'00000000.app'))
