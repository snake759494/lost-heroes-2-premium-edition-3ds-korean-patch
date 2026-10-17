import subprocess,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from emu import EXE
def mypids():
    out=subprocess.run(['powershell','-NoProfile','-Command',"Get-CimInstance Win32_Process -Filter \"Name='azahar.exe' or Name='lime3ds.exe'\" | ForEach-Object { \"$($_.ProcessId)|$($_.ExecutablePath)\" }"],capture_output=True,text=True).stdout
    r=[]
    for l in out.splitlines():
        if '|' in l:
            p,e=l.split('|',1)
            if os.path.normcase(os.path.dirname(e)).rstrip(os.sep)==os.path.normcase(os.path.dirname(os.path.abspath(EXE))).rstrip(os.sep): r.append(int(p))  # 내가 띄운 에뮬레이터만
    return r
def killmine():
    for p in mypids(): subprocess.run(['taskkill','/PID',str(p),'/F'],capture_output=True)
if __name__=='__main__':
    if sys.argv[1:]==['kill']: killmine()
    print(mypids())
