# 데이터 전용 한글: 지원 음절 선정 (이름·용어집 우선, 나머지 빈도순) → hs/allowed.txt
import sys, os, collections
sys.path.insert(0, os.path.dirname(__file__))
import hsfont as F, hstext as T
CELLS = 408; TILES = 354
def cells(c):
    t = F.tiles_of(c); (lt, lb), (rt, rb) = F.layout(c); return (t[lt], t[lb]), (t[rt], t[rb])   # 그림 기준(글꼴 확정 후 고정)
def main():
    cnt = collections.Counter(); force = collections.Counter()
    for gi in T.MODES:
        for k in T.load_tr(gi).values():
            for c in k:
                if 0xAC00 <= ord(c) <= 0xD7A3:
                    cnt[c] += 1
                    if gi in (16, 82, 83, 85): force[c] += 1
    g = open(os.path.join(T.TR, 'GLOSSARY.md'), encoding='utf-8').read()
    for c in g:
        if 0xAC00 <= ord(c) <= 0xD7A3: force[c] += 1
    blank = tuple(tuple([0] * 8) for _ in range(8))
    cs = set(); ts = {blank}; S = []
    order = sorted(force, key=lambda c: -cnt[c]) + [c for c, _ in cnt.most_common() if c not in force]
    for c in order:
        l, r = cells(c); nc = cs | {l, r}; nt = ts | {l[0], l[1], r[0], r[1]}
        if len(nc) <= CELLS and len(nt) <= TILES: cs, ts = nc, nt; S.append(c)
    A = set(S); tot = sum(cnt.values()); cov = sum(v for c, v in cnt.items() if c in A)
    nb = sum(1 for gi in T.MODES for k in T.load_tr(gi).values() if any(0xAC00 <= ord(c) <= 0xD7A3 and c not in A for c in k))
    print('음절', len(S), '적중 %.2f%%' % (100 * cov / tot), '칸', len(cs), '타일', len(ts), '고칠 블록', nb,
          '빠진 강제음절', ''.join(c for c in force if c not in A))
    open(os.path.join(W, 'hs', 'allowed.txt'), 'w', encoding='utf-8').write(''.join(sorted(S)))
W = F.W
if __name__ == '__main__': main()
