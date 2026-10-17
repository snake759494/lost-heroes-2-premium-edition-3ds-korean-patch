using System;using System.IO;using System.Linq;using System.Text;using System.Threading.Tasks;
using Windows.Globalization;using Windows.Graphics.Imaging;using Windows.Media.Ocr;using Windows.Storage;
// usage: ocr <list.txt> <out.tsv> [scale]
class P{static async Task Main(string[] a){
 var eng=OcrEngine.TryCreateFromLanguage(new Language("ja"));int scale=a.Length>2?int.Parse(a[2]):2;
 var sb=new StringBuilder();
 foreach(var f in File.ReadAllLines(a[0])){
  try{var file=await StorageFile.GetFileFromPathAsync(Path.GetFullPath(f));
   using var st=await file.OpenAsync(FileAccessMode.Read);var dec=await BitmapDecoder.CreateAsync(st);
   uint w=dec.PixelWidth*(uint)scale,h=dec.PixelHeight*(uint)scale;
   if(w>OcrEngine.MaxImageDimension||h>OcrEngine.MaxImageDimension){w=dec.PixelWidth;h=dec.PixelHeight;}
   var tr=new BitmapTransform{ScaledWidth=w,ScaledHeight=h,InterpolationMode=BitmapInterpolationMode.Linear};
   var bmp=await dec.GetSoftwareBitmapAsync(BitmapPixelFormat.Bgra8,BitmapAlphaMode.Premultiplied,tr,ExifOrientationMode.IgnoreExifOrientation,ColorManagementMode.DoNotColorManage);
   var res=await eng.RecognizeAsync(bmp);
   sb.Append(f).Append('\t').Append(string.Join(" | ",res.Lines.Select(l=>l.Text))).Append('\n');
  }catch(Exception e){sb.Append(f).Append("\tERR ").Append(e.Message).Append('\n');}
 }
 File.WriteAllText(a[1],sb.ToString(),new UTF8Encoding(false));}}
