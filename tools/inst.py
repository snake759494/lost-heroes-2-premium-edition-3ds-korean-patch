# usage: python tools/inst.py <cia>  : 포터블 Azahar로 CIA 설치(백그라운드)
import subprocess,time,sys,os,shutil
sys.path.insert(0,os.path.dirname(__file__))
from emu import *
src=sys.argv[1];dst=os.path.join(os.path.dirname(EXE),'_inst.cia');shutil.copy(src,dst)
si=subprocess.STARTUPINFO();si.dwFlags=1;si.wShowWindow=4;fg=u.GetForegroundWindow()
p=subprocess.Popen([EXE,'-i',dst],startupinfo=si,creationflags=0x8|0x200)
r=None
for i in range(40):
    time.sleep(1);t=[title(h) for h in wins(p.pid)]
    if 'Success' in t or 'Failure' in t: r=t;break
    for h in wins(p.pid): u.SetWindowPos(h,1,0,0,0,0,0x13)
    if fg: u.SetForegroundWindow(fg)
subprocess.run(['taskkill','/PID',str(p.pid),'/F'],capture_output=True);time.sleep(1);os.remove(dst);print(r)
