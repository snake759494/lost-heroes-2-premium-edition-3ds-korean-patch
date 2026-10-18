// 로스트 히어로즈 2 PE 한글패치 - 3DS 실기(Luma3DS LayeredFS)용 폴더 생성기
// 같은 폴더에 원본 .3ds, 한글 .3ds(xdelta 적용 결과), (선택) 한글 업데이트 .cia 를 두고 실행하면
// luma/titles/0004000000146C00/romfs/ 에 바뀐 파일만 만듭니다.
using System;using System.IO;using System.Linq;using System.Collections.Generic;using System.Security.Cryptography;using System.Text;
class RomFS{
  public Dictionary<string,(long off,long size)> Files=new();FileStream fs;public long Ncch;
  public RomFS(FileStream f,long romfsOff){fs=f;
    var iv=Read(romfsOff,0x60);if(Encoding.ASCII.GetString(iv,0,4)!="IVFC")throw new Exception("RomFS(IVFC)를 찾지 못했습니다");
    uint mh=BitConverter.ToUInt32(iv,8);long l3=romfsOff+((0x60+mh+0xFFF)&~0xFFFL);
    var h=Read(l3,0x28);uint dmo=U(h,12),fmo=U(h,28),fms=U(h,32),fdo=U(h,36);uint dms=U(h,16);
    var dm=Read(l3+dmo,(int)dms);var fm=Read(l3+fmo,(int)fms);
    void Walk(uint o,string path){
      uint sib=U(dm,(int)o+4),child=U(dm,(int)o+8),file=U(dm,(int)o+12),nl=U(dm,(int)o+20);
      string name=Encoding.Unicode.GetString(dm,(int)o+24,(int)nl);string cur=o==0?path:(path==""?name:path+"/"+name);
      uint fo=file;
      while(fo!=0xFFFFFFFF){uint fsib=U(fm,(int)fo+4);long dof=(long)BitConverter.ToUInt64(fm,(int)fo+8),sz=(long)BitConverter.ToUInt64(fm,(int)fo+16);uint fnl=U(fm,(int)fo+28);
        string fn=Encoding.Unicode.GetString(fm,(int)fo+32,(int)fnl);Files[cur==""?fn:cur+"/"+fn]=(l3+fdo+dof,sz);fo=fsib;}
      if(child!=0xFFFFFFFF)Walk(child,cur);if(sib!=0xFFFFFFFF&&o!=0)Walk(sib,path);}
    Walk(0,"");}
  static uint U(byte[] b,int o)=>BitConverter.ToUInt32(b,o);
  public byte[] Read(long o,int n){var b=new byte[n];fs.Position=o;int r=0;while(r<n){int k=fs.Read(b,r,n-r);if(k<=0)throw new EndOfStreamException();r+=k;}return b;}
  public byte[] Get(string k){var (o,s)=Files[k];return Read(o,(int)s);}
  static long NcchRomfs(FileStream f,long ncch){var b=new byte[0x200];f.Position=ncch;f.Read(b,0,0x200);
    if(Encoding.ASCII.GetString(b,0x100,4)!="NCCH")throw new Exception("NCCH 헤더가 없습니다(암호화된 파일이거나 다른 형식)");
    return ncch+(long)BitConverter.ToUInt32(b,0x1B0)*0x200;}
  public byte[] Code(){ // ExeFS .code (비압축일 때만)
    var h=Read(Ncch,0x200);long exo=Ncch+(long)BitConverter.ToUInt32(h,0x1A0)*0x200;var ex=Read(Ncch+0x200,0x10);
    if((ex[0xD]&1)!=0)return null;var eh=Read(exo,0x200);
    for(int i=0;i<10;i++){string n=Encoding.ASCII.GetString(eh,i*16,8).TrimEnd('\0');if(n==".code"){uint o=U(eh,i*16+8),sz=U(eh,i*16+12);return Read(exo+0x200+o,(int)sz);}}
    return null;}
  public static RomFS Open3DS(string p){var f=File.OpenRead(p);var b=new byte[0x200];f.Position=0x100;f.Read(b,0,0x40);
    if(Encoding.ASCII.GetString(b,0,4)!="NCSD")throw new Exception(p+": NCSD(.3ds)가 아닙니다");
    long p0=(long)BitConverter.ToUInt32(b,0x20)*0x200;var r=new RomFS(f,NcchRomfs(f,p0));r.Ncch=p0;return r;}
  public static RomFS OpenCIA(string p){var f=File.OpenRead(p);var h=new byte[0x20];f.Read(h,0,0x20);
    long A(long x)=>(x+63)/64*64;uint hs=U(h,0),cs=U(h,8),ts=U(h,12),tm=U(h,16);
    long oc=A(A(A(A(hs)+cs)+ts)+tm);var r=new RomFS(f,NcchRomfs(f,oc));r.Ncch=oc;return r;}
}
class P{
  static int Main(string[] a){
    Console.OutputEncoding=Encoding.UTF8;
    string dir=a.Length>0?a[0]:AppContext.BaseDirectory;
    try{
      var all=Directory.GetFiles(dir);
      string Pick(Func<string,bool> f,string what){var c=all.Where(f).ToList();if(c.Count==0)return null;Console.WriteLine($"{what}: {Path.GetFileName(c[0])}");return c[0];}
      string orig=Pick(x=>x.EndsWith(".3ds",StringComparison.OrdinalIgnoreCase)&&x.Contains("(Japan)"),"원본 .3ds");
      string ko=Pick(x=>x.EndsWith(".3ds",StringComparison.OrdinalIgnoreCase)&&x.Contains("(Korean)"),"한글 .3ds");
      string upd=Pick(x=>x.EndsWith(".cia",StringComparison.OrdinalIgnoreCase)&&x.Contains("(Korean)"),"한글 업데이트 .cia");
      if(orig==null||ko==null){Console.WriteLine("\n같은 폴더에 원본 '...(Japan).3ds' 와 한글 '...(Korean).3ds' 가 필요합니다.");Pause();return 1;}
      string outRoot=Path.Combine(dir,"luma","titles","0004000000146C00","romfs");
      var A=RomFS.Open3DS(orig);var K=RomFS.Open3DS(ko);int n=0;long bytes=0;
      var sha=SHA256.Create();
      foreach(var k in K.Files.Keys){var kd=K.Get(k);
        if(A.Files.ContainsKey(k)){var (o,s)=A.Files[k];if(s==kd.Length&&sha.ComputeHash(A.Get(k)).SequenceEqual(sha.ComputeHash(kd)))continue;}
        var op=Path.Combine(outRoot,k.Replace('/',Path.DirectorySeparatorChar));Directory.CreateDirectory(Path.GetDirectoryName(op));File.WriteAllBytes(op,kd);n++;bytes+=kd.Length;}
      Console.WriteLine($"본편: 바뀐 파일 {n}개");
      string codeOut=Path.Combine(dir,"luma","titles","0004000000146C00","code.bin");byte[] code=K.Code();
      if(upd!=null){var U=RomFS.OpenCIA(upd);int m=0;var uc=U.Code();if(uc!=null)code=uc;
        foreach(var k in U.Files.Keys){var op=Path.Combine(outRoot,k.Replace('/',Path.DirectorySeparatorChar));Directory.CreateDirectory(Path.GetDirectoryName(op));var d=U.Get(k);File.WriteAllBytes(op,d);m++;bytes+=d.Length;}
        Console.WriteLine($"업데이트: 파일 {m}개");}
      else Console.WriteLine("(한글 업데이트 .cia가 없어 본편만 만들었습니다. 실기에 v1.1.0 업데이트를 설치했다면 한글 업데이트 .cia도 함께 두고 다시 실행하세요.)");
      Console.WriteLine($"\n완료: {Path.Combine(dir,"luma")} ({bytes/1048576.0:F1} MB)\n이 'luma' 폴더를 SD 카드 루트에 복사하세요.");
      Pause();return 0;
    }catch(Exception e){Console.WriteLine("오류: "+e.Message);Pause();return 1;}
  }
  static void Pause(){if(!Console.IsInputRedirected){Console.WriteLine("\n아무 키나 누르면 종료합니다.");try{Console.ReadKey(true);}catch{}}}
}
