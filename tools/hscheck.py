# 번역 검사: python tools/hscheck.py 064 [065 ...]
#  - 모든 블록이 번역됐는지, {..} 제어코드 순서가 일본어와 같은지, 쓸 수 없는 문자가 없는지, (n/m 모드) 폭 초과 여부
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
import hstext as T
ONE = set("仮面星人号国市東西南北年月日山世改軍家光回転反竜") | set(" ()「」!?、.・~♥ー-▶/=αν:,rmk0123456789ⅡⅢ") | set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
LIMIT = {86: 22, 101: 22, 16: 10}   # 설명문 상자 폭
_AP = os.path.join(os.path.dirname(T.TR), '..', 'hs', 'allowed.txt')
ALLOWED = set(open(_AP, encoding='utf-8').read()) if os.path.exists(_AP) else None
def codes(t): return re.findall(r'\{[0-9a-f]+\}', t)
def main():
    bad = 0
    for g in sys.argv[1:]:
        gi = int(g); ja = {}; cur = None
        for line in open(os.path.join(T.TR, 'g%03d.txt' % gi), encoding='utf-8').read().split('\n'):
            if line.startswith('@'): cur = int(line[1:5], 16)
            elif cur is not None and not line.startswith('>') and cur not in ja: ja[cur] = line
        tr = T.load_tr(gi); mode = T.MODES[gi]; maxw = max(T.width(v) for v in ja.values()); miss = [a for a in ja if a not in tr]
        for a, k in tr.items():
            if a not in ja: print('g%03d @%04X: 일본어에 없는 주소' % (gi, a)); bad += 1; continue
            if codes(k) != codes(ja[a]): print('g%03d @%04X: 제어코드 불일치\n  JA %s\n  KO %s' % (gi, a, codes(ja[a]), codes(k))); bad += 1
            plain = re.sub(r'\{[0-9a-f]+\}', '', k).replace('|', '')
            odd = [c for c in plain if not (0xAC00 <= ord(c) <= 0xD7A3 or c in ONE)]
            if ALLOWED is not None:
                na = sorted(set(c for c in plain if 0xAC00 <= ord(c) <= 0xD7A3 and c not in ALLOWED))
                if na: print('g%03d @%04X: 지원 안 되는 음절 %s  | %s' % (gi, a, ''.join(na), k)); bad += 1
            if odd: print('g%03d @%04X: 쓸 수 없는/일본 문자 %s' % (gi, a, ''.join(sorted(set(odd))))); bad += 1
            if mode == 'n':
                lim = LIMIT.get(gi, maxw)
                if gi == 84: lim = 5 if a <= 0xB135 else 28
                if T.width(k) > lim: print('g%03d @%04X: 폭 초과 %d>%d %s' % (gi, a, T.width(k), lim, k))
            elif mode == 'm' and T.width(k) > T.width(ja[a]): print('g%03d @%04X: 폭 초과 %d>%d %s' % (gi, a, T.width(k), T.width(ja[a]), k))
        print('g%03d: 블록 %d, 번역 %d, 누락 %d %s' % (gi, len(ja), len(tr), len(miss), ' '.join('%04X' % a for a in miss[:20])))
    print('문제', bad)
main()
