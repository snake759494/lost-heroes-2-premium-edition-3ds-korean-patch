import struct
def al(x,a=16): return (x+a-1)//a*a
def parse(d):
    assert d[:4]==b'TBB1'
    n,size=struct.unpack_from('<II',d,8)
    offs=struct.unpack_from('<%dI'%n,d,0x10)
    tabs=[]
    for ti,o in enumerate(offs):
        end=offs[ti+1] if ti+1<n else len(d)
        if d[o:o+4]!=b'MTBL': tabs.append(('RAW',d[o:end]));continue
        sz,cnt,x0=struct.unpack_from('<III',d,o+8)
        so=struct.unpack_from('<%dI'%cnt,d,o+0x14)
        strs=[]
        for k,s in enumerate(so):
            if s==0 or s>=sz: strs.append(('NULL',s));continue
            p=o+0x10+s;a=[]
            while True:
                v=struct.unpack_from('<H',d,p)[0];p+=2
                if v==0: break
                a.append(v)
            strs.append(a)
        tabs.append(('MTBL',(x0,strs)))
    return tabs
def strings(t):
    return t[1][1] if t[0]=='MTBL' else []
def build(tabs):
    blobs=[]
    for kind,x in tabs:
        if kind=='RAW': blobs.append(x);continue
        x0,x=x
        cnt=len(x);body=bytearray();offs=[]
        base=al(4+cnt*4)
        for s in x:
            if isinstance(s,tuple): offs.append(s[1]);continue
            offs.append(base+len(body))
            b=struct.pack('<%dH'%len(s),*s)+b'\0\0'
            body+=b+b'\0'*(al(len(b))-len(b))
        t=bytearray(struct.pack('<4sIIII',b'MTBL',0x10,base+len(body),cnt,x0))
        t+=struct.pack('<%dI'%cnt,*offs);t+=b'\0'*(0x10+base-len(t));t+=body
        blobs.append(bytes(t))
    n=len(blobs);h=al(0x10+4*n);offs=[];cur=h
    for b in blobs: offs.append(cur);cur+=al(len(b))
    out=bytearray(struct.pack('<4sIII',b'TBB1',0x10,n,cur))
    out+=struct.pack('<%dI'%n,*offs);out+=b'\0'*(h-len(out))
    for b in blobs: out+=b+b'\0'*(al(len(b))-len(b))
    return bytes(out)
