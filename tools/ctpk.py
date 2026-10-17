import struct,sys,os
sys.path.insert(0,os.path.dirname(__file__))
import texdec,numpy as np
FMT=['rgba8','rgb8','rgba5551','rgb565','rgba4','la8','hilo8','l8','a8','la4','l4','a4','etc1','etc1a4']
def entries(t):
    ho=t.find(b'CTPK');c=t[ho:]
    n=struct.unpack_from('<H',c,6)[0];do=struct.unpack_from('<I',c,8)[0]
    out=[]
    for i in range(n):
        e=struct.unpack_from('<IIIIHHBBBBII',c,0x20+i*0x20)
        name=c[e[0]:c.find(b'\0',e[0])].decode()
        out.append(dict(i=i,name=name,size=e[1],pos=ho+do+e[2],fmt=FMT[e[3]],w=e[4],h=e[5],mip=e[6]))
    return out
def decode(t,e):
    return texdec.decode(e['fmt'],t[e['pos']:e['pos']+e['size']],e['w'],e['h'])
