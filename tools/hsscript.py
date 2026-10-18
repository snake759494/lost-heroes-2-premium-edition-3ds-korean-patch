# 히어로 전기 대사 바이트코드 해석: 그룹표(01:8000) → 메시지표 → 메시지(분기 추적)
import struct, sys
ROM = None
def off(b, a): return (b & 0x7F) * 0x8000 + (a - 0x8000)
LEN = {0xF0: 2, 0xF1: 1, 0xF2: 1, 0xF3: 2, 0xF4: 3, 0xF5: 3, 0xF6: 5, 0xF7: 3, 0xF9: 4, 0xFA: 2, 0xFB: 1,
       0xFC: 2, 0xFD: 2, 0xFE: 1, 0xFF: 1, 0xEF: 2}

def groups(r):
    return [struct.unpack_from('<I', r, 0x8000 + 3 * i)[0] & 0xFFFFFF for i in range(256)]

def table(r, ga):
    """메시지표 항목 수 추정: 표 끝(2n)이 가장 작은 대상 주소에 닿을 때까지"""
    b, a = ga >> 16, ga & 0xFFFF; ents = []; lo = 0x10000
    while a + 2 * len(ents) < lo and len(ents) < 2000:
        v = struct.unpack_from('<H', r, off(b, a + 2 * len(ents)))[0]
        if v == 0 and len(ents) < 4: ents.append(0); continue      # 빈 항목
        if v < 0x8000 or v < a: break
        ents.append(v); lo = min(lo, v)
    while ents and ents[-1] == 0: ents.pop()
    return ents

def walk(r, b, start, seen, calls, f8n=None):
    """메시지를 따라가며 [시작,끝) 구간들 반환. 분기 대상도 추적"""
    todo = [start]; spans = []
    while todo:
        a = todo.pop()
        if a in seen: continue
        s = a
        while True:
            seen.add(a)
            c = r[off(b, a)]
            if c < 0xF0 and c != 0xEF:
                a += 1
            elif c == 0xF8:
                tbl = a + 2; n = 0; lo = 0x10000
                while tbl + 2 * n < lo and n < 64:
                    v = struct.unpack_from('<H', r, off(b, tbl + 2 * n))[0]
                    if v < tbl: break
                    lo = min(lo, v); todo.append(v); n += 1
                a = tbl + 2 * n; spans.append((s, a, 'f8')); s = a; break
            else:
                ln = LEN[c]
                if c == 0xF4: calls.add(struct.unpack_from('<H', r, off(b, a + 1))[0])
                if c in (0xF6, 0xF7, 0xF9):
                    t = struct.unpack_from('<H', r, off(b, a + ln - 2))[0]; todo.append(t)
                a += ln
                if c in (0xF7, 0xFF): break
            if a in seen and a != s: break
        if a > s: spans.append((s, a, ''))
    return spans

if __name__ == '__main__':
    r = open(sys.argv[1], 'rb').read(); G = groups(r)
    uniq = sorted(set(G)); tot = 0
    for ga in uniq:
        ents = table(r, ga); b = ga >> 16
        seen = set(); calls = set(); sz = 0
        for e in ents:
            for s, t, _ in walk(r, b, e, seen, calls): pass
        sz = len(seen)
        print('%06X grp=%s n=%d bytes=%d' % (ga, [i for i, g in enumerate(G) if g == ga][:6], len(ents), sz))
        tot += sz
    print('total', tot)

HIRA = ' あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんがぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽぁぃぅぇぉっゃゅょ'
KATA = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンヴガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポァィゥェォッャュョ'
SYM = '()「」!?。、.・~…♥▼ー▶/=←→○×∞αβν?mkⅠⅡⅢ0123456789:'
KAN = '仮面星人号国市東西南北年月日山世改軍家光回転反竜'
def ch(c):
    if c == 1: return ' '
    if 2 <= c <= 0x51: return HIRA[c - 1]
    if 0x52 <= c <= 0xA2: return KATA[c - 0x52] if c - 0x52 < len(KATA) else '?'
    if 0xA3 <= c <= 0xCD: return SYM[c - 0xA3]
    if 0xD0 <= c <= 0xE7: return KAN[c - 0xD0]
    return '<%02X>' % c
def dec(r, b, a, maxn=400):
    o = []; n = 0
    while n < maxn:
        c = r[off(b, a)]
        if c < 0xF0 and c != 0xEF: o.append(ch(c)); a += 1
        elif c == 0xEF: o.append('<EF%02X>' % r[off(b, a) + 1]); a += 2
        elif c == 0xF1: o.append('\n'); a += 1
        elif c == 0xF8: o.append('<F8>'); break
        else:
            ln = LEN[c]; o.append('{' + r[off(b, a):off(b, a) + ln].hex() + '}'); a += ln
            if c in (0xF7, 0xFF): break
        n += 1
    return ''.join(o)

MLEN = {0xF0: 2, 0xF1: 1, 0xF2: 3, 0xF3: 5, 0xF4: 2, 0xF5: 3, 0xF6: 3, 0xF7: 4, 0xF8: 3, 0xF9: 4, 0xFA: 4,
        0xFB: 3, 0xFC: 2, 0xFD: 1, 0xFE: 2, 0xFF: 1, 0xEF: 2}
def mwalk(r, b, a, lim=2000):
    """메뉴 엔진 문자열: FF까지 선형. 반환 [(주소, 길이)]"""
    out = []
    for _ in range(lim):
        c = r[off(b, a)]; ln = MLEN.get(c, 1); out.append((a, ln)); a += ln
        if c == 0xFF: return out
    return None
