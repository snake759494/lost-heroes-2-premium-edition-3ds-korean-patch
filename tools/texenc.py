import sys,os
sys.path.insert(0,os.path.dirname(__file__))
import numpy as np,texdec
def encode(fmt,img):
    """img: HxWx4 uint8 RGBA -> bytes (3DS tiled)"""
    p=texdec.tile(img).astype(np.int32)
    r,g,b,a=p[:,0],p[:,1],p[:,2],p[:,3]
    if fmt=='rgba8': return np.stack([a,b,g,r],1).astype(np.uint8).tobytes()
    if fmt=='rgb8': return np.stack([b,g,r],1).astype(np.uint8).tobytes()
    q=lambda v,bits:((v*((1<<bits)-1)+127)//255)
    if fmt=='rgba4': v=(q(r,4)<<12)|(q(g,4)<<8)|(q(b,4)<<4)|q(a,4)
    elif fmt=='rgba5551': v=(q(r,5)<<11)|(q(g,5)<<6)|(q(b,5)<<1)|(a>=128)
    elif fmt=='rgb565': v=(q(r,5)<<11)|(q(g,6)<<5)|q(b,5)
    elif fmt=='la8': v=(r<<8)|a
    elif fmt=='a8': return a.astype(np.uint8).tobytes()
    elif fmt=='l8': return r.astype(np.uint8).tobytes()
    elif fmt=='a4':
        x=q(a,4);return (x[0::2]|(x[1::2]<<4)).astype(np.uint8).tobytes()
    elif fmt=='la4': return ((q(r,4)<<4)|q(a,4)).astype(np.uint8).tobytes()
    else: raise ValueError(fmt)
    return v.astype('<u2').tobytes()
