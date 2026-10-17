using System;using System.IO;using System.Collections.Generic;using System.Threading.Tasks;
// usage: lz11c <list.txt>  each line: in<TAB>out ; output = "COMP"+LZ11
class P{
 static byte[] Comp(byte[] s){
  var o=new MemoryStream();o.Write(new byte[]{(byte)'C',(byte)'O',(byte)'M',(byte)'P'});
  int n=s.Length;
  if(n<0x1000000){o.WriteByte(0x11);o.WriteByte((byte)n);o.WriteByte((byte)(n>>8));o.WriteByte((byte)(n>>16));}
  else{o.WriteByte(0x11);o.WriteByte(0);o.WriteByte(0);o.WriteByte(0);o.Write(BitConverter.GetBytes(n));}
  var head=new int[1<<16];var prev=new int[n];Array.Fill(head,-1);
  int p=0;
  while(p<n){
   long flagPos=o.Position;o.WriteByte(0);int flag=0;
   for(int b=0;b<8&&p<n;b++){
    int bestL=0,bestD=0;
    if(p+3<=n){
     int h=(s[p]<<8^s[p+1]<<4^s[p+2])&0xffff;int c=head[h];int tries=256;
     int maxL=Math.Min(0x10110,n-p);
     while(c>=0&&p-c<=0x1000&&tries-->0){
      if(s[c]==s[p]&&s[c+1]==s[p+1]){int l=0;while(l<maxL&&s[c+l]==s[p+l])l++;
       if(l>bestL){bestL=l;bestD=p-c;if(l==maxL)break;}}
      c=prev[c];}
    }
    int adv;
    if(bestL>=3){
     flag|=0x80>>b;int d=bestD-1;
     if(bestL<=0x10){o.WriteByte((byte)(((bestL-1)<<4)|(d>>8)));o.WriteByte((byte)d);}
     else if(bestL<=0x110){int l=bestL-0x11;o.WriteByte((byte)(l>>4));o.WriteByte((byte)(((l&15)<<4)|(d>>8)));o.WriteByte((byte)d);}
     else{int l=bestL-0x111;o.WriteByte((byte)(0x10|(l>>12)));o.WriteByte((byte)(l>>4));o.WriteByte((byte)(((l&15)<<4)|(d>>8)));o.WriteByte((byte)d);}
     adv=bestL;
    }else{o.WriteByte(s[p]);adv=1;}
    for(int k=0;k<adv;k++){int q=p+k;if(q+3<=n){int h=(s[q]<<8^s[q+1]<<4^s[q+2])&0xffff;prev[q]=head[h];head[h]=q;}}
    p+=adv;
   }
   long e=o.Position;o.Position=flagPos;o.WriteByte((byte)flag);o.Position=e;
  }
  return o.ToArray();
 }
 static void Main(string[] a){
  var lines=File.ReadAllLines(a[0]);
  Parallel.ForEach(lines,l=>{var t=l.Split('\t');File.WriteAllBytes(t[1],Comp(File.ReadAllBytes(t[0])));});
 }
}
