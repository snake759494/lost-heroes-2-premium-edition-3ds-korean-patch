import sys,os,time
sys.path.insert(0,os.path.dirname(__file__))
from emu import *
B=os.path.join(os.path.dirname(__file__),'..')
import subprocess
import myproc
pids=myproc.mypids()
W=[w for pid in pids for w in wins(pid)]
for w in W:
    if not title(w).startswith('Azahar'): u.PostMessageW(w,0x10,0,0)
time.sleep(0.3)
import numpy as _n
C=[w for pid in pids for w in wins(pid) if title(w).startswith('Azahar')]
h=C[0]
for s in sys.argv[2:]:
    if s.startswith('w'): time.sleep(float(s[1:]));continue
    k,_,n=s.partition('*')
    for i in range(int(n or 1)): key(h,k);time.sleep(0.35)
import glob,shutil
from ctrlkey import ctrl_key
SD=os.path.join(B,'azahar','shots');old=set(glob.glob(SD+'/*.png'))
ctrl_key(h,ord('P'))
new=set()
for i in range(40):
    time.sleep(0.25);new=set(glob.glob(SD+'/*.png'))-old
    if new: break
if new:
    f=list(new)[0];time.sleep(0.4);shutil.move(f,sys.argv[1])
else: print('no shot')
