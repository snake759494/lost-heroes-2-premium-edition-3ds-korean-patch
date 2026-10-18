// 로스트 히어로즈 2 PE 한글패치 — 에뮬레이터용 일괄 패처
// 같은 폴더의 원본 .3ds(+ 복호화된 v1.1.0 업데이트 .cia)에 한글패치를 적용하고,
// 본편을 에뮬레이터에 설치할 수 있는 CIA로 만듭니다(「히어로 전기」는 본편이 설치되어 있어야 동작).
using System;using System.IO;using System.Linq;using System.Diagnostics;using System.Security.Cryptography;using System.Text;using System.Collections.Generic;
class P{
  const string BASE_X="LostHeroes2PE_3DS_KO_base.xdelta", UPD_X="LostHeroes2PE_3DS_KO_update.xdelta";
  static readonly string[] BASE_MD5={"e73ca7ff1b0475fdab84fd7b4b95dd3a","f04d2f36f395ef807473c39a57061b26"};
  const string UPD_MD5="a0f01dad7f2178f7115c65f2324060e6";
  const string KO3DS_SHA="fa159c4ea8832b6187ecf6473bb9eb019b5cc99b43e985fca750acbb6fd51e92";
  const string KOUPD_SHA="ab9153dd144bcdcb68dffabdbf9bb4b31c510e1d7dc05634421981978b02530c";
  static string Hex(byte[] b)=>string.Concat(b.Select(x=>x.ToString("x2")));
  static string FileHash(HashAlgorithm h,string p){using var f=File.OpenRead(p);return Hex(h.ComputeHash(f));}
  static void Say(string s){Console.WriteLine(s);}
  static int Main(string[] a){
    Console.OutputEncoding=Encoding.UTF8;string dir=a.Length>0?a[0]:AppContext.BaseDirectory;
    try{
      string xd=Path.Combine(dir,"xdelta3.exe");
      foreach(var need in new[]{xd,Path.Combine(dir,BASE_X),Path.Combine(dir,UPD_X)})
        if(!File.Exists(need))throw new Exception("패치 파일이 없습니다: "+Path.GetFileName(need)+" (압축을 모두 풀어 같은 폴더에 두세요)");
      string src3ds=null,srcUpd=null;
      Say("원본 파일을 찾는 중...");
      foreach(var f in Directory.GetFiles(dir)){
        string ext=Path.GetExtension(f).ToLower();if(ext!=".3ds"&&ext!=".cia")continue;
        if(Path.GetFileName(f).Contains("(Korean)"))continue;
        long len=new FileInfo(f).Length;
        if(ext==".3ds"&&len==1073741824&&src3ds==null){var m=FileHash(MD5.Create(),f);
          if(BASE_MD5.Contains(m)){src3ds=f;Say(" 본편: "+Path.GetFileName(f));}else Say(" (맞지 않는 .3ds 건너뜀: "+Path.GetFileName(f)+")");}
        if(ext==".cia"&&srcUpd==null){var m=FileHash(MD5.Create(),f);
          if(m==UPD_MD5){srcUpd=f;Say(" 업데이트: "+Path.GetFileName(f));}else Say(" (복호화된 v1.1.0 업데이트가 아니라 건너뜀: "+Path.GetFileName(f)+")");}
      }
      if(src3ds==null)throw new Exception("원본 .3ds를 찾지 못했습니다. 원본 ROM(1,073,741,824 바이트, MD5 "+BASE_MD5[0]+")을 이 폴더에 두세요.");
      string ko3ds=Path.Combine(dir,"Lost Heroes 2 (Premium Edition) (Korean).3ds");
      Say("\n[1/3] 본편에 한글패치 적용 중... (1~2분)");Run(xd,src3ds,Path.Combine(dir,BASE_X),ko3ds);
      if(FileHash(SHA256.Create(),ko3ds)!=KO3DS_SHA)throw new Exception("패치 결과 검증 실패(본편)");
      string koCia=Path.Combine(dir,"Lost Heroes 2 (Premium Edition) (Korean).cia");
      Say("[2/3] 본편 설치용 CIA 만드는 중...");Cia.FromNcsd(ko3ds,koCia);
      if(srcUpd!=null){string koUpd=Path.Combine(dir,"Lost Heroes 2 Premium Edition Update v1.1.0 (Korean).cia");
        Say("[3/3] 업데이트에 한글패치 적용 중...");Run(xd,srcUpd,Path.Combine(dir,UPD_X),koUpd);
        if(FileHash(SHA256.Create(),koUpd)!=KOUPD_SHA)throw new Exception("패치 결과 검증 실패(업데이트)");}
      else Say("[3/3] 복호화된 업데이트 CIA가 없어 건너뜀 (업데이트 없이도 플레이 가능)");
      Say("\n완료! 만들어진 파일:");
      foreach(var f in Directory.GetFiles(dir).Where(x=>Path.GetFileName(x).Contains("(Korean)")))Say("  "+Path.GetFileName(f));
      Say("\n에뮬레이터(Azahar/Lime3DS)의 「File > Install CIA」로 본편 CIA(와 업데이트 CIA)를 설치한 뒤,");
      Say("게임 목록의 설치된 「로스트 히어로즈 2」를 실행하세요. 「히어로 전기」는 Lime3DS 설치판에서만 동작합니다(Azahar 불가).");
      Pause();return 0;
    }catch(Exception e){Say("\n오류: "+e.Message);Pause();return 1;}
  }
  static void Run(string xd,string src,string patch,string dst){
    var psi=new ProcessStartInfo(xd){UseShellExecute=false,CreateNoWindow=true,RedirectStandardError=true};
    foreach(var x in new[]{"-d","-f","-s",src,patch,dst})psi.ArgumentList.Add(x);
    var p=Process.Start(psi);string err=p.StandardError.ReadToEnd();p.WaitForExit();
    if(p.ExitCode!=0)throw new Exception("xdelta 적용 실패: "+err.Trim());}
  static void Pause(){if(!Console.IsInputRedirected){Console.WriteLine("\n아무 키나 누르면 종료합니다.");try{Console.ReadKey(true);}catch{}}}
}
public static class Cia{
  static long Al(long x,long a)=>(x+a-1)/a*a;
  static void BE16(byte[] b,int o,int v){b[o]=(byte)(v>>8);b[o+1]=(byte)v;}
  static void BE32(byte[] b,int o,uint v){for(int i=0;i<4;i++)b[o+i]=(byte)(v>>(24-8*i));}
  static void BE64(byte[] b,int o,ulong v){for(int i=0;i<8;i++)b[o+i]=(byte)(v>>(56-8*i));}
  static void Str(byte[] b,int o,string s){var t=Encoding.ASCII.GetBytes(s);Array.Copy(t,0,b,o,t.Length);}
  // NCSD(.3ds) -> CIA. 서명은 비워 둠(에뮬레이터는 검증하지 않음). 콘텐츠는 복호화(NoCrypto) 상태 그대로.
  public static void FromNcsd(string src,string dst){
    using var f=File.OpenRead(src);var h=new byte[0x100];f.Position=0x100;f.Read(h,0,0x100);
    if(Encoding.ASCII.GetString(h,0,4)!="NCSD")throw new Exception("NCSD가 아닙니다");
    ulong tid=BitConverter.ToUInt64(h,8);var parts=new List<(int idx,long off,long size)>();
    for(int i=0;i<8;i++){uint o=BitConverter.ToUInt32(h,0x20+i*8),s=BitConverter.ToUInt32(h,0x24+i*8);if(s!=0)parts.Add((i,(long)o*0x200,(long)s*0x200));}
    for(int k=0;k<parts.Count;k++){var nb=new byte[0x200];f.Position=parts[k].off;f.Read(nb,0,0x200);
      if(Encoding.ASCII.GetString(nb,0x100,4)!="NCCH")throw new Exception("파티션 "+parts[k].idx+"에 NCCH가 없습니다");
      parts[k]=(parts[k].idx,parts[k].off,(long)BitConverter.ToUInt32(nb,0x104)*0x200);}
    var ex=new byte[0x400];f.Position=parts[0].off+0x200;f.Read(ex,0,0x400);uint save=BitConverter.ToUInt32(ex,0x1C0);
    var hashes=new List<byte[]>();var buf=new byte[1<<22];
    foreach(var p in parts){using var sh=SHA256.Create();f.Position=p.off;long left=p.size;
      while(left>0){int n=f.Read(buf,0,(int)Math.Min(buf.Length,left));sh.TransformBlock(buf,0,n,null,0);left-=n;}
      sh.TransformFinalBlock(buf,0,0);hashes.Add(sh.Hash);}
    byte[] cert=new byte[0xA00];
    byte[] tik=new byte[0x350];BE32(tik,0,0x10004);int T=0x140;Str(tik,T,"Root-CA00000003-XS0000000c");tik[T+0x7C]=1;BE64(tik,T+0x9C,tid);
    byte[] ci={0x00,0x01,0x00,0x14,0x00,0x00,0x00,0xAC,0x00,0x00,0x00,0x14,0x00,0x01,0x00,0x14,0,0,0,0,0,0,0,0x28,0,0,0,1,0,0,0,0x84,0,0,0,0x84,0,3,0,0,0,0,0,0};
    Array.Copy(ci,0,tik,T+0x164,ci.Length);for(int i=0;i<0x20;i++)tik[T+0x164+ci.Length+i]=0xFF;
    int nc=parts.Count;byte[] tmd=new byte[0x140+0xC4+64*0x24+nc*0x30];BE32(tmd,0,0x10004);int H=0x140;
    Str(tmd,H,"Root-CA00000003-CP0000000b");tmd[H+0x40]=1;BE64(tmd,H+0x4C,tid);BE32(tmd,H+0x54,0x40);
    BitConverter.GetBytes(save).CopyTo(tmd,H+0x5A);BE16(tmd,H+0x9C,0);BE16(tmd,H+0x9E,nc);
    int CR=H+0xC4+64*0x24;
    for(int k=0;k<nc;k++){int o=CR+k*0x30;BE32(tmd,o,(uint)k);BE16(tmd,o+4,parts[k].idx);BE16(tmd,o+6,0);BE64(tmd,o+8,(ulong)parts[k].size);Array.Copy(hashes[k],0,tmd,o+0x10,0x20);}
    using(var s=SHA256.Create()){var rec=s.ComputeHash(tmd,CR,nc*0x30);BE16(tmd,H+0xC4,0);BE16(tmd,H+0xC6,nc);Array.Copy(rec,0,tmd,H+0xC8,0x20);
      var info=s.ComputeHash(tmd,H+0xC4,64*0x24);Array.Copy(info,0,tmd,H+0xA4,0x20);}
    long content=0;foreach(var p in parts)content=Al(content,0x40)+p.size;
    var hdr=new byte[0x2020];BitConverter.GetBytes(0x2020u).CopyTo(hdr,0);BitConverter.GetBytes((uint)cert.Length).CopyTo(hdr,8);
    BitConverter.GetBytes((uint)tik.Length).CopyTo(hdr,12);BitConverter.GetBytes((uint)tmd.Length).CopyTo(hdr,16);BitConverter.GetBytes(content).CopyTo(hdr,24);
    foreach(var p in parts)hdr[0x20+p.idx/8]|=(byte)(0x80>>(p.idx%8));
    using var o2=File.Create(dst);
    void Pad(){long n=Al(o2.Position,64)-o2.Position;if(n>0)o2.Write(new byte[n]);}
    o2.Write(hdr);Pad();o2.Write(cert);Pad();o2.Write(tik);Pad();o2.Write(tmd);Pad();
    foreach(var p in parts){Pad();f.Position=p.off;long left=p.size;while(left>0){int n=f.Read(buf,0,(int)Math.Min(buf.Length,left));o2.Write(buf,0,n);left-=n;}}
  }
}
