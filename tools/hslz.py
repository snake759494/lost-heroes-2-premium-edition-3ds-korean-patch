# 히어로 전기(SFC) 그래픽 LZ 해제/압축 — 루틴 01:9C57~9CF3 해석 결과
# 비트열: 플래그 바이트 MSB부터. 1=리터럴 1바이트
#  0,0: 짧은 복사 — 2비트 n(길이 n+2), 다음 바이트 b: 거리 = b-256 (−1~−256)
#  0,1: 긴 복사 — 2바이트 b0 b1: v=(b0<<8)|b1, 거리 = (v>>3)-8192, n=v&7 → 길이 n+2; n==0이면 다음 바이트 c: c==0 종료, 아니면 길이 c+1
class Bits:
    def __init__(s, d, p): s.d = d; s.p = p; s.cnt = 0; s.cur = 0
    def bit(s):
        if s.cnt == 0:
            s.cur = s.d[s.p]; s.p += 1; s.cnt = 8
        s.cnt -= 1; b = (s.cur >> 7) & 1; s.cur = (s.cur << 1) & 0xFF; return b
    def byte(s):
        v = s.d[s.p]; s.p += 1; return v

def decompress(d, p):
    r = Bits(d, p); out = bytearray()
    while True:
        if r.bit():
            out.append(r.byte()); continue
        if not r.bit():
            n = (r.bit() << 1) | r.bit(); ln = n + 2
            dist = r.byte() - 256
        else:
            b0 = r.byte(); b1 = r.byte(); v = (b0 << 8) | b1
            dist = (v >> 3) - 8192; n = v & 7
            if n: ln = n + 2
            else:
                c = r.byte()
                if c == 0: break
                ln = c + 1
        s = len(out) + dist
        for i in range(ln): out.append(out[s + i])
    return bytes(out), r.p

def compress(data):
    """탐욕적 LZ 압축(위 형식). 반환: bytes"""
    out = bytearray(); flags = []; pend = []
    # 비트·바이트를 원래 순서대로 섞어 쓰기 위해, 플래그 바이트 자리를 예약하며 기록
    res = bytearray(); fpos = None; fcnt = 8; fval = 0
    def putbit(b):
        nonlocal fpos, fcnt, fval
        if fcnt == 8:
            if fpos is not None: res[fpos] = fval
            fpos = len(res); res.append(0); fcnt = 0; fval = 0
        fval |= (b & 1) << (7 - fcnt); fcnt += 1
    def flush():
        if fpos is not None: res[fpos] = fval
    n = len(data); i = 0
    import collections
    table = collections.defaultdict(list)
    while i < n:
        best = 0; bdist = 0
        if i + 2 <= n:
            key = data[i:i+2]
            for j in reversed(table.get(key, [])[-64:]):
                if i - j > 8192: break
                l = 0
                while i + l < n and l < 256 and data[j + l] == data[i + l]: l += 1
                if l > best: best = l; bdist = i - j
                if best >= 256: break
        if best >= 2 and not (best == 2 and bdist > 256):
            if best <= 5 and bdist <= 256:
                putbit(0); putbit(0); ln = best - 2; putbit(ln >> 1); putbit(ln & 1); res.append(256 - bdist)
            else:
                if best > 256: best = 256
                d13 = 8192 - bdist
                if best <= 9:
                    v = (d13 << 3) | (best - 2)
                    putbit(0); putbit(1); res += bytes([v >> 8, v & 0xFF])
                else:
                    v = (d13 << 3)
                    putbit(0); putbit(1); res += bytes([v >> 8, v & 0xFF, best - 1])
            for k in range(best):
                if i + k + 2 <= n: table[data[i+k:i+k+2]].append(i + k)
            i += best
        else:
            putbit(1); res.append(data[i])
            if i + 2 <= n: table[data[i:i+2]].append(i)
            i += 1
    putbit(0); putbit(1); res += bytes([0, 0, 0])  # 종료: 긴 복사 n=0, c=0
    flush()
    return bytes(res)

def store(data):
    """복사 없이 리터럴만 쓰는 가장 단순한 스트림(해제기 호환성 최우선)"""
    res = bytearray(); i = 0; n = len(data)
    while i < n:
        chunk = data[i:i + 8]
        flag = 0
        for k in range(len(chunk)): flag |= 0x80 >> k
        if len(chunk) == 8:
            res.append(flag); res += chunk
        else:
            # 남은 리터럴 + 종료(0,1 + 00 00 00)
            bits = [1] * len(chunk) + [0, 1]
            fval = 0
            for k, b in enumerate(bits[:8]): fval |= b << (7 - k)
            res.append(fval); res += chunk; res += bytes([0, 0, 0])
            if len(bits) > 8: raise ValueError
            return bytes(res)
        i += 8
    res.append(0x40); res += bytes([0, 0, 0])   # 0,1 → 종료
    return bytes(res)

def compress_opt(data, window=8192, maxcand=512):
    """최소 비트 수 파싱(동적계획). 비용: 리터럴 9, 짧은복사(2~5, 거리≤256) 12, 긴복사(3~9) 18, 긴복사+길이(2~256) 26비트"""
    import collections
    n = len(data); INF = 1 << 60
    cost = [INF] * (n + 1); cost[n] = 0; choice = [None] * (n + 1)
    pos = collections.defaultdict(list)
    for i in range(n - 1): pos[data[i:i + 2]].append(i)
    import bisect
    for i in range(n - 1, -1, -1):
        best = cost[i + 1] + 9; ch = ('L',)
        if i + 2 <= n:
            lst = pos.get(data[i:i + 2], []); k = bisect.bisect_left(lst, i)
            cand = lst[max(0, k - maxcand):k]
            for j in reversed(cand):
                d = i - j
                if d > window: break
                l = 2
                while i + l < n and l < 256 and data[j + l] == data[i + l]: l += 1
                for L in range(2, l + 1):
                    if d <= 256 and L <= 5: c = 12
                    elif 3 <= L <= 9: c = 18
                    else: c = 26
                    if cost[i + L] + c < best: best = cost[i + L] + c; ch = ('C', d, L)
        cost[i] = best; choice[i] = ch
    # 기록
    res = bytearray(); st = {'fpos': None, 'fcnt': 8, 'fval': 0}
    def putbit(b):
        if st['fcnt'] == 8:
            if st['fpos'] is not None: res[st['fpos']] = st['fval']
            st['fpos'] = len(res); res.append(0); st['fcnt'] = 0; st['fval'] = 0
        st['fval'] |= (b & 1) << (7 - st['fcnt']); st['fcnt'] += 1
    i = 0
    while i < n:
        ch = choice[i]
        if ch[0] == 'L': putbit(1); res.append(data[i]); i += 1; continue
        _, d, L = ch
        if d <= 256 and L <= 5:
            putbit(0); putbit(0); putbit((L - 2) >> 1); putbit((L - 2) & 1); res.append(256 - d)
        else:
            d13 = 8192 - d
            if 3 <= L <= 9: v = (d13 << 3) | (L - 2); putbit(0); putbit(1); res += bytes([v >> 8, v & 0xFF])
            else: v = d13 << 3; putbit(0); putbit(1); res += bytes([v >> 8, v & 0xFF, L - 1])
        i += L
    putbit(0); putbit(1); res += bytes([0, 0, 0])
    if st['fpos'] is not None: res[st['fpos']] = st['fval']
    return bytes(res)
