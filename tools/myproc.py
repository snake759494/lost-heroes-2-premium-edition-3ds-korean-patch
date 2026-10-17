import subprocess,sys
def mypids():
    out=subprocess.run(['powershell','-NoProfile','-Command',"Get-CimInstance Win32_Process -Filter \"Name='azahar.exe'\" | ForEach-Object { \"$($_.ProcessId)|$($_.ExecutablePath)\" }"],capture_output=True,text=True).stdout
    r=[]
    for l in out.splitlines():
        if '|' in l:
            p,e=l.split('|',1)
            if 'lh2emu' in e.lower() or '_work\azahar' in e.lower(): r.append(int(p))
    return r
def killmine():
    for p in mypids(): subprocess.run(['taskkill','/PID',str(p),'/F'],capture_output=True)
if __name__=='__main__':
    if sys.argv[1:]==['kill']: killmine()
    print(mypids())
