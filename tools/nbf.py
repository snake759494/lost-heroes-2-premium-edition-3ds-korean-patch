import struct
def parse(d):
    assert d[:4]==b'2NBF'
    n,ho,x=struct.unpack_from('<III',d,4)
    ents=[]
    for i in range(n):
        p=0x10+i*0x8c
        name=d[p:p+0x80].split(b'\0')[0].decode()
        a,b,c=struct.unpack_from('<III',d,p+0x80)
        ents.append([name,d[ho+a:ho+a+c],b])
    return ents,d[:ho]
def build(ents,hdr):
    h=bytearray(hdr);cur=0;body=bytearray()
    for i,(name,data,b) in enumerate(ents):
        p=0x10+i*0x8c
        struct.pack_into('<III',h,p+0x80,len(body),b,len(data))
        body+=data;body+=b'\0'*((-len(body))%16)
    return bytes(h)+bytes(body)
