# 자동 진행(F3 대기 포함) 블록 중 번역 후 창 수가 원문보다 늘어난 것 찾기
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
import hstext as T
def windows_ja(t):
    n = 1; lines = 1
    for k, v in T.tokens(t):
        if k == 'c' and v == '|':
            lines += 1
            if lines > 3: n += 1; lines = 1
        if k == 'b' and v[0] == 0xF2: n += 1; lines = 1
    return n
def windows_ko(t):
    return 1 + sum(1 for k, v in T.wrap(t) if k == 'b' and v[0] == 0xF2)
for gi, mode in T.MODES.items():
    if mode != 'd': continue
    ja = {}; cur = None
    for line in open(os.path.join(T.TR, 'g%03d.txt' % gi), encoding='utf-8').read().split('\n'):
        if line.startswith('@'): cur = int(line[1:5], 16)
        elif cur is not None and not line.startswith('>') and cur not in ja: ja[cur] = line
    tr = T.load_tr(gi)
    for a, k in tr.items():
        if '{f3' not in ja.get(a, ''): continue
        if windows_ko(k) > windows_ja(ja[a]):
            print('g%03d @%04X 창 %d→%d\n  JA %s\n  KO %s' % (gi, a, windows_ja(ja[a]), windows_ko(k), ja[a], k))
