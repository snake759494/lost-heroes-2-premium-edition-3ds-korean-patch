# 히어로 전기 대사 추출/재배치
#  python tools/hstext.py extract   → tr/hs/gNNN.txt (블록별 일본어 + 번역칸, 이미 있으면 건너뜀)
#  build(rom, enc) → 번역 블록을 새 위치에 다시 쓰고 그룹표 갱신 (hsbuild에서 호출)
# 블록 = 흐름 제어(F6/F7/F8/F9/FF)나 분기 대상에서 끊긴 텍스트 조각. 표기: | = F1 줄바꿈, {xx..} = 원시 바이트
# 모드: d = 대사 엔진(자동 줄바꿈), n = 대사 엔진 문자열(이름·아이템, 줄바꿈 없음), m = 메뉴 엔진(분기 없음, 줄바꿈 없음)
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(__file__))
import hsscript as H
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TR = os.path.join(W, 'tr', 'hs')
MODES = {}
for g in [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 32, 33, 34, 35, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 78, 100]:
    MODES[g] = 'd'
for g in [16, 82, 83, 84, 85, 86, 101]: MODES[g] = 'n'
MODES[99] = 'm'
FLOW = (0xF6, 0xF7, 0xF8, 0xF9, 0xFF)
off = H.off

# 표시용 역변환: 원래 코드 ↔ 문자 (유일한 것만)
CH2C = {}; C2CH = {}
for c in range(1, 0xE8):
    ch = 'r' if c == 0xBD else H.ch(c)
    if len(ch) == 1 and ch not in CH2C and ch not in '{}|<>': CH2C[ch] = c; C2CH[c] = ch

def bad(r, b, s): return any(r[off(b, x)] in (0, 0xCE, 0xCF) or 0xE8 <= r[off(b, x)] <= 0xEE for x in s)

def insns(r, b, a, mode='d'):
    """a에서 명령 하나: (길이, 대상 목록)"""
    c = r[off(b, a)]
    if mode == 'm': return H.MLEN.get(c, 1), []
    if c < 0xF0 and c != 0xEF: return 1, []
    if c == 0xF8:
        tbl = a + 2; n = 0; lo = 0x10000; ts = []
        while tbl + 2 * n < lo and n < 64:
            v = struct.unpack_from('<H', r, off(b, tbl + 2 * n))[0]
            if v < tbl: break
            lo = min(lo, v); ts.append(v); n += 1
        return 2 + 2 * n, ts
    ln = H.LEN[c]
    if c in (0xF6, 0xF7, 0xF9): return ln, [struct.unpack_from('<H', r, off(b, a + ln - 2))[0]]
    return ln, []

def flows(mode): return (0xFF,) if mode == 'm' else FLOW

def analyze(r, gi):
    """그룹 gi: 유효 항목, 명령 시작 주소들, 블록 시작 집합"""
    mode = MODES[gi]; ga = H.groups(r)[gi]; b = ga >> 16; ents = H.table(r, ga); ok = []
    for a in ents:
        if a == 0: ok.append(False); continue
        if mode == 'm':
            w = H.mwalk(r, b, a); ok.append(w is not None and not bad(r, b, [x for x, _ in w] if False else []))
        else:
            s = set(); H.walk(r, b, a, s, set()); ok.append(not bad(r, b, s))
    I = {}; starts = set(e for e, k in zip(ents, ok) if k); todo = list(starts); FL = flows(mode)
    while todo:
        a = todo.pop()
        while a not in I:
            ln, ts = insns(r, b, a, mode); I[a] = (ln, ts)
            for t in ts:
                starts.add(t); todo.append(t)
            c = r[off(b, a)]; a += ln
            if c in (0xF6, 0xF9) and mode != 'm': starts.add(a)
            if c in (0xF7, 0xFF, 0xF8) and (mode != 'm' or c == 0xFF): break
    return b, ents, ok, I, starts

def blocks(r, b, I, starts, mode):
    """[(시작, [명령주소...])] — 원래 주소 순"""
    out = []; cur = None; prev_end = None; FL = flows(mode)
    for a in sorted(I):
        if cur is None or a in starts or a != prev_end:
            cur = (a, []); out.append(cur)
        cur[1].append(a); prev_end = a + I[a][0]
        if r[off(b, a)] in FL: prev_end = None
    return out

def show(r, b, a, ln, mode):
    c = r[off(b, a)]
    if c == 0xEF:
        x = r[off(b, a) + 1]
        if x < 26: return chr(65 + x)
    if c == 0xF1: return '|'
    if c in C2CH and (mode != 'm' or c < 0xF0): return C2CH[c]
    return '{' + r[off(b, a):off(b, a) + ln].hex() + '}'

def showblk(r, b, body, I, mode):
    if mode != 'm': return ''.join(show(r, b, a, I[a][0], mode) for a in body)
    big = True; o = []
    for a in body:
        c = r[off(b, a)]
        if c in (0xFE, 0xF6): big = (r[off(b, a) + 1] & 0xC0) == 0x40
        if not big and c < 0xF0 and c != 0xEF: o.append('{%02x}' % c)
        else: o.append(show(r, b, a, I[a][0], mode))
    return ''.join(o)

def extract():
    os.makedirs(TR, exist_ok=True); r = open(os.path.join(W, 'hs', 'orig.sfc'), 'rb').read(); G = H.groups(r); done = set()
    for gi, mode in MODES.items():
        if G[gi] in done: continue
        done.add(G[gi]); b, ents, ok, I, starts = analyze(r, gi); L = []; FL = flows(mode)
        for s, ins in blocks(r, b, I, starts, mode):
            body = ins[:-1] if r[off(b, ins[-1])] in FL else ins
            t = showblk(r, b, body, I, mode)
            if not any(2 <= r[off(b, a)] <= 0xE7 for a in body): continue  # 글자 없는 블록 생략
            L.append('@%04X\n%s\n>\n' % (s, t))
        p = os.path.join(TR, 'g%03d.txt' % gi)
        if os.path.exists(p): print('skip existing', p); continue
        open(p, 'w', encoding='utf-8').write('# group %d  %06X  mode %s\n' % (gi, G[gi], mode) + '\n'.join(L))
        print(gi, mode, len(L))

def load_tr(gi):
    """번역 읽기: gNNN.txt의 > 줄, 그다음 ko/gNNN*.txt(@주소 / >번역)가 덮어씀"""
    import glob
    if os.environ.get('NOTR'): return {}
    p = os.path.join(TR, 'g%03d.txt' % gi); d = {}
    files = ([p] if os.path.exists(p) else []) + sorted(glob.glob(os.path.join(TR, 'ko', 'g%03d*.txt' % gi)))
    for f in files: d.update(_read_tr(f))
    return d

def _read_tr(p):
    d = {}; cur = None; ja = None
    for line in open(p, encoding='utf-8').read().split('\n'):
        if line.startswith('@'): cur = int(line[1:5], 16); ja = None
        elif cur is not None and line.startswith('>'):
            k = line[1:].rstrip('\r')
            if k.strip(): d[cur] = k
        elif cur is not None and ja is None: ja = line
    return d

POOL = [0x08, 0x09, 0x0A, 0x0B, 0x28, 0x29] + list(range(0x35, 0x3D)) + [0x3E, 0x3F]   # 3D: 폰트 블록·검수 스텁
RESERVE = 0x800   # 뱅크 08 앞부분: 한글 훅 코드 자리
CE = 0xCE   # 새 제어코드: CE lo hi bank = 롱 점프

def tokens(t):
    """번역문 → [(종류, 값)] : ('c',문자) ('b',bytes)"""
    out = []; i = 0
    while i < len(t):
        c = t[i]
        if c == '{':
            j = t.index('}', i); out.append(('b', bytes.fromhex(t[i+1:j]))); i = j + 1; continue
        out.append(('c', c)); i += 1
    return out

WIDTH = 27; LINES = 3
def cw(k, v):
    if k == 'b': return 6 if v[0] == 0xF4 else 0
    return 2 if 0xAC00 <= ord(v) <= 0xD7A3 else 1
def width(t):
    """가장 긴 줄의 칸 수"""
    best = 0; col = 0
    for k, v in tokens(t):
        if k == 'c' and v == '|' or k == 'b' and v[0] == 0xF2: col = 0; continue
        col += cw(k, v); best = max(best, col)
    return best
def wrap(t):
    """자동 줄바꿈: 폭 WIDTH 칸 넘으면 공백에서 끊고, 창에 LINES줄 넘으면 F2"""
    parts = t.split('|')                      # 공백으로 정렬한 줄(서명 등)이 넘치면 앞 공백을 줄임
    for i, p in enumerate(parts):
        n = len(p) - len(p.lstrip(' '))
        if n >= 3 and width(p) > WIDTH: parts[i] = ' ' * max(0, n - (width(p) - WIDTH)) + p.lstrip(' ')
    t = '|'.join(parts); auto = '{f3' in t
    tk = tokens(t); out = []; line = []; col = 0; nl = 0
    def newline():
        nonlocal nl, col
        nl += 1; col = 0
        if nl >= LINES:
            if auto: out.append(('b', bytes([0xF3, 0xE0]))); out.append(('b', bytes([0xF3, 0xE0])))   # 자동 진행 장면: 읽을 시간
            out.append(('b', bytes([0xF2]))); nl = 0
        else: out.append(('c', '|'))
    for k, v in tk:
        if k == 'c' and v == '|': out.extend(line); line = []; newline(); continue
        if k == 'b' and v[0] == 0xF2: out.extend(line); line = []; out.append((k, v)); nl = 0; col = 0; continue
        line.append((k, v)); col += cw(k, v)
        if k == 'c' and v == ' ': out.extend(line); line = []
        elif col > WIDTH:
            if out and out[-1] == ('c', ' ') and len(line) < col: out.pop()
            lw = sum(cw(*x) for x in line)
            if lw >= col: out.extend(line[:-1]); line = line[-1:]   # 공백 없는 긴 줄: 강제 분할
            newline(); col = sum(cw(*x) for x in line)
    out.extend(line); return out

def enc_text(t, enc, mode='d'):
    out = bytearray()
    for k, v in (wrap(t) if mode == 'd' else tokens(t)):
        if k == 'b': out += v
        elif v == '|': out.append(0xF1)
        elif 'A' <= v <= 'Z': out += bytes([0xEF, ord(v) - 65])
        elif 0xAC00 <= ord(v) <= 0xD7A3: out += enc.text(v)
        elif v in enc_one: out.append(enc_one[v])
        elif v in CH2C: out.append(CH2C[v])
        else: raise ValueError('인코딩 불가 문자 %r in %r' % (v, t))
    return bytes(out)
enc_one = {}   # hsbuild가 1바이트 기호표를 채움

def build(rom, enc, log=print, warn=print, dataonly=False):
    """rom(bytearray, 2MB)에 번역 대사 재배치. 반환: 사용 통계"""
    r = bytes(rom); G = H.groups(r); done = {}
    units = []   # 그룹별 (gi목록, 표항목, 유효, 블록들)
    for gi, mode in MODES.items():
        if G[gi] in done: continue
        same = [i for i, g in enumerate(G) if g == G[gi]]; done[G[gi]] = 1
        b, ents, ok, I, starts = analyze(r, gi); tr = load_tr(gi); bl = []; FL = flows(mode)
        for s, ins in blocks(r, b, I, starts, mode):
            last = ins[-1]; c = r[off(b, last)]
            body_ins = ins[:-1] if c in FL else ins
            orig = b''.join(r[off(b, a):off(b, a) + I[a][0]] for a in body_ins)
            if s in tr:
                body = enc_text(tr[s], enc, mode)
                if mode != 'd':
                    ja = showblk(r, b, body_ins, I, mode)
                    if width(tr[s]) > width(ja): warn('폭 초과 g%03d @%04X: %d > %d  %s' % (gi, s, width(tr[s]), width(ja), tr[s]))
            else: body = orig
            flow = None
            if c in FL:
                ln, ts = I[last]; raw = r[off(b, last):off(b, last) + ln]; flow = (c, raw, ts)
            end = (last + I[last][0]) if (c not in FL or c in (0xF6, 0xF9)) else None   # 이어지는 주소
            bl.append({'s': s, 'body': body, 'flow': flow, 'next': end})
        units.append((same, ents, ok, bl))
    if dataonly: split_big(units, G)
    # 1패스: 뱅크 배정 (그룹 전체가 한 뱅크에 들어가면 쪼개지 않음)
    free = {bk: (0x8000 + RESERVE if bk == POOL[0] else 0x8000) for bk in POOL}; pi = 0; place = {}
    def size(x):
        n = len(x['body']) + (len(x['flow'][1]) if x['flow'] else 0)
        return n if dataonly else n + 4 + 4 * (len(x['flow'][2]) if x['flow'] else 0)
    for ui, (same, ents, ok, bl) in enumerate(units):
        need_t = (2 if dataonly else 6) * len(ents) + 1; tot = need_t + sum(size(x) for x in bl)
        if dataonly:                                   # 롱 점프 없음: 그룹 전체가 한 뱅크에
            if tot > 0x7000: print('큰 그룹 g%03d %d' % (same[0], tot))
            if os.environ.get('LISTSIZES'): continue
            assert tot <= 0x8000, '그룹이 한 뱅크를 넘음: g%03d %d바이트' % (same[0], tot)
            if free[POOL[pi]] + tot > 0x10000: pi += 1
            assert free[POOL[pi]] + tot <= 0x10000
        if tot <= 0x8000 and free[POOL[pi]] + tot > 0x10000: pi += 1
        while free[POOL[pi]] + need_t > 0x10000: pi += 1
        tb = POOL[pi]; free[tb] += need_t; place[(ui, 'tbl')] = tb
        for x in bl:
            while free[POOL[pi]] + size(x) > 0x10000: pi += 1
            place[(ui, x['s'])] = POOL[pi]; free[POOL[pi]] += size(x)
        if dataonly and len({place[(ui, x['s'])] for x in bl} | {tb}) > 1: print('배치 갈라짐 g%03d' % same[0], tb, tot, {place[(ui, x['s'])] for x in bl})
    # 2패스: 주소 결정. 뱅크별로 [표/블록...][스텁...]
    for bk in POOL:
        rom[off(bk, 0x8000):off(bk, 0x8000) + 0x8000] = b'\xFF' * 0x8000
    cur = {}; addr = {}; lay = {bk: [] for bk in POOL}
    for ui, (same, ents, ok, bl) in enumerate(units):
        lay[place[(ui, 'tbl')]].append(('tbl', ui))
        for x in bl: lay[place[(ui, x['s'])]].append(('blk', ui, x))
    stubs = {bk: {} for bk in POOL}
    for bk in POOL:
        p = 0x8000 + RESERVE if bk == POOL[0] else 0x8000
        for j, it in enumerate(lay[bk]):
            if it[0] == 'tbl':
                ents = units[it[1]][1]; addr[(it[1], 'tbl')] = (bk, p); p += 2 * len(ents) + 1   # +1: FF(빈 항목용)
            else:
                nx = lay[bk][j + 1] if j + 1 < len(lay[bk]) else None
                ui, x = it[1], it[2]
                x['adj'] = bool(nx and nx[0] == 'blk' and nx[1] == ui and nx[2]['s'] == x['next'])
                addr[(ui, x['s'])] = (bk, p)
                p += len(x['body']) + (len(x['flow'][1]) if x['flow'] else 0)
                if x['next'] is not None and not x['adj']: p += 4
        cur[bk] = p
    def long_of(ui, s):
        bk, a = addr[(ui, s)]; return (bk << 16) | a
    def target(ui, bk, s):
        """bk 뱅크 안에서 쓸 16비트 주소(다른 뱅크면 스텁)"""
        L = long_of(ui, s)
        if L >> 16 == bk: return L & 0xFFFF
        st = stubs[bk]
        if L not in st:
            st[L] = cur[bk]; cur[bk] += 4; assert cur[bk] <= 0x10000, 'bank full %02X' % bk
        return st[L]
    for bk in POOL:
        for it in lay[bk]:
            if it[0] == 'tbl':
                ui = it[1]; same, ents, ok, bl = units[ui]; tbk, ta = addr[(ui, 'tbl')]
                ffa = ta + 2 * len(ents); rom[off(tbk, ffa)] = 0xFF
                for i, (e, k) in enumerate(zip(ents, ok)):
                    v = target(ui, tbk, e) if k else (0 if e == 0 else ffa)
                    struct.pack_into('<H', rom, off(tbk, ta + 2 * i), v)
                for gi in same: rom[0x8000 + 3 * gi:0x8003 + 3 * gi] = struct.pack('<I', (tbk << 16) | ta)[:3]
            else:
                ui, x = it[1], it[2]; bk2, p = addr[(ui, x['s'])]; o = bytearray(x['body'])
                if x['flow']:
                    c, raw, ts = x['flow']; raw = bytearray(raw)
                    if c == 0xF8:
                        for i, t in enumerate(ts): struct.pack_into('<H', raw, 2 + 2 * i, target(ui, bk2, t))
                    elif c in (0xF6, 0xF7, 0xF9) and ts:
                        struct.pack_into('<H', raw, len(raw) - 2, target(ui, bk2, ts[0]))
                    o += raw
                if x['next'] is not None and not x['adj']:
                    o += bytes([CE]) + struct.pack('<I', long_of(ui, x['next']))[:3]
                rom[off(bk2, p):off(bk2, p) + len(o)] = o
    if dataonly:
        assert not any(stubs.values()), '데이터 전용인데 뱅크 간 스텁 발생'
        assert all(x['adj'] for u in units for x in u[3] if x['next'] is not None), '데이터 전용인데 롱 점프 필요'
    for bk in POOL:
        for L, a in stubs[bk].items(): rom[off(bk, a):off(bk, a) + 4] = bytes([CE]) + struct.pack('<I', L)[:3]
    # 검증: 표 항목·분기 대상·이어지는 흐름이 새 위치로 정확히 가는지
    def resolve(bk, a16):
        o = off(bk, a16)
        if not dataonly and rom[o] == CE: v = struct.unpack_from('<I', rom, o + 1)[0] & 0xFFFFFF; return v
        return (bk << 16) | a16
    nerr = 0
    for ui, (same, ents, ok, bl) in enumerate(units):
        tbk, ta = addr[(ui, 'tbl')]
        for i, (e, k) in enumerate(zip(ents, ok)):
            if k and resolve(tbk, struct.unpack_from('<H', rom, off(tbk, ta + 2 * i))[0]) != long_of(ui, e): nerr += 1
        for x in bl:
            bk2, p = addr[(ui, x['s'])]; q = p + len(x['body'])
            if x['flow']:
                c, raw, ts = x['flow']
                if c == 0xF8: fields = [q + 2 + 2 * i for i in range(len(ts))]
                elif c in (0xF6, 0xF7, 0xF9) and ts: fields = [q + len(raw) - 2]
                else: fields = []
                for fa, t in zip(fields, ts):
                    if resolve(bk2, struct.unpack_from('<H', rom, off(bk2, fa))[0]) != long_of(ui, t): nerr += 1
                q += len(raw)
            if x['next'] is not None:
                got = ((bk2 << 16) | q) if x['adj'] else resolve(bk2, q)
                if got != long_of(ui, x['next']): nerr += 1
    assert nerr == 0, '재배치 검증 실패 %d건' % nerr
    used = {bk: cur[bk] - 0x8000 for bk in POOL if cur[bk] > 0x8000}
    log('text banks: ' + ' '.join('%02X:%d' % kv for kv in used.items()))
    return used

if __name__ == '__main__':
    if sys.argv[1] == 'extract': extract()

HOST = 82     # 보조 그룹: 표 길이가 확정된 g082 뒤에 항목을 덧붙임(원래 게임은 그 번호를 쓰지 않음)
LIMIT = 0x7F00
def _usize(ents, bl): return 2 * len(ents) + 1 + sum(len(x['body']) + (len(x['flow'][1]) if x['flow'] else 0) for x in bl)
def split_big(units, G):
    """롱 점프 없이 한 뱅크를 넘는 그룹: 분기로 이어진 블록 묶음을 HOST 그룹으로 옮기고, 원래 항목은 [F4 idx HOST][FF] 스텁으로"""
    hu = [u for u in units if HOST in u[0]][0]
    for ui, (same, ents, ok, bl) in enumerate(units):
        if _usize(ents, bl) <= LIMIT: continue
        idx = {x['s']: k for k, x in enumerate(bl)}; par = list(range(len(bl)))
        def find(a):
            while par[a] != a: par[a] = par[par[a]]; a = par[a]
            return a
        for k, x in enumerate(bl):
            links = ([x['next']] if x['next'] is not None else []) + (list(x['flow'][2]) if x['flow'] else [])
            for t in links:
                if t in idx: par[find(k)] = find(idx[t])
        comp = {}
        for k in range(len(bl)): comp.setdefault(find(k), []).append(k)
        comps = sorted(comp.values(), key=lambda c: -sum(len(bl[k]['body']) for k in c))
        moved = set()
        for c in comps:
            if _usize(ents, [x for k, x in enumerate(bl) if k not in moved]) + 4 * len(ents) // 50 <= LIMIT - 0x200: break
            moved |= set(c)
        hs, hents, hok, hbl = hu
        mk = lambda s: ('m', same[0], s)
        for k in sorted(moved):
            x = dict(bl[k]); x['s'] = mk(x['s'])
            if x['next'] is not None: x['next'] = mk(x['next'])
            if x['flow']: x['flow'] = (x['flow'][0], x['flow'][1], [mk(t) for t in x['flow'][2]])
            hbl.append(x)
        mstarts = {bl[k]['s'] for k in moved}; newbl = [x for k, x in enumerate(bl) if k not in moved]
        for i, (e, o) in enumerate(zip(ents, ok)):
            if o and e in mstarts:
                hents.append(mk(e)); hok.append(True); hi = len(hents) - 1
                assert hi < 0xFF
                newbl.append({'s': ('stub', i), 'body': bytes([0xF4, hi, HOST]), 'flow': (0xFF, b'\xff', []), 'next': None})
                ents[i] = ('stub', i)
        bl[:] = newbl
        print('분할 g%03d: 블록 %d개를 g%03d로 (%d → %d바이트)' % (same[0], len(moved), HOST, 0, _usize(ents, bl)))
