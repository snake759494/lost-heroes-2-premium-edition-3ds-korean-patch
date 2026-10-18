# 히어로 전기(SFC) 한글 ROM — 데이터 전용 빌드(3DS 내장 에뮬레이터는 ROM 코드 수정을 무시하므로 코드 패치 없음)
#  python -X utf8 tools/hsbuild2.py [출력]
#  한글 음절 = 8x16 칸 2개(hsfont 조합형). 칸 → 원래 엔진의 글자 코드(1바이트 또는 EF xx), 글자표 01:85C1/01:8981과
#  폰트 압축 블록(VRAM 타일 0x000~0x1FF)을 새로 써 넣음. 대사는 그룹 단위로 한 뱅크에 재배치(롱 점프 없음).
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(__file__))
import hstext, hsfont, hslz, hsscript as HS
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG = os.path.join(W, 'hs', 'orig.sfc')
def off(a): return ((a >> 16) & 0x7F) * 0x8000 + (a & 0x7FFF)

ONE = {' ': 0x01, '(': 0xA3, ')': 0xA4, '「': 0xA5, '」': 0xA6, '!': 0xA7, '?': 0xA8, '、': 0xAA,
       ',': 0xAA, '.': 0xAB, '・': 0xAC, '~': 0xAD, '♥': 0xAF, 'ー': 0xB1, '-': 0xB1, '▶': 0xB2, '/': 0xB3,
       '=': 0xB4, 'α': 0xBA, 'ν': 0xBC, 'm': 0xBE,
       'k': 0xBF, 'Ⅱ': 0xC1, 'Ⅲ': 0xC2, ':': 0xCD}
for i in range(10): ONE[str(i)] = 0xC3 + i
FREEABLE = []   # (기호 코드를 칸으로 돌리면 3DS판이 멈춤 — 사용 안 함)   # 번역에서 안 쓰는 기호(。…▼←→○×∞βⅠ) → 한글 칸으로
KEEP = (set([0x01]) | set(range(0xA3, 0xCE)) | set(range(0xF0, 0xF0 + 26))) - set(FREEABLE)     # 그대로 두는 코드(기호·숫자·영문)
TOP, BOT = 0x85C1, 0x8981          # 글자표(ROM 오프셋, 01:85C1 / 01:8981)
NTAB = 0x1E0                       # 표 항목 수(코드 0~0xEF + EF 확장 0xF0~0x1DF)
FONTPTR = {0x60030: 0, 0x60033: 0, 0x60036: 1, 0x60039: 1}   # 폰트 블록 포인터(0C:8304 → 타일 0~FF, 0C:8896 → 100~1FF)
FONT_DST = 0x3D8000

def tables(rom):
    return [struct.unpack_from('<H', rom, TOP + 2 * c)[0] & 0x3FF for c in range(NTAB)], \
           [struct.unpack_from('<H', rom, BOT + 2 * c)[0] & 0x3FF for c in range(NTAB)]

def pool_tiles(rom):
    """기호·숫자·영문이 쓰지 않는, 가나·한자 전용 타일(창 테두리 등 다른 그림은 건드리지 않음)"""
    top, bot = tables(rom); used = {}
    for c in range(NTAB):
        for t in (top[c], bot[c]): used.setdefault(t, set()).add(c)
    return sorted(t for t, cs in used.items() if t < 0x200 and not (cs & KEEP) and t not in (0x000, 0x100))   # 0/100: 빈 칸 채움

class Enc:
    """음절 → 바이트. cellcode: 칸(위,아래 그림) → 코드(0x02~0xEE 1바이트, 0x100+ 은 EF xx)"""
    def __init__(s, cellcode): s.cc = cellcode; s.glyphs = []
    def text(s, ch):
        if ch not in s.ok: return bytes([0xA8])           # (LOOSE 시험용) 미지원 음절은 '?'
        t = hsfont.tiles_of(ch); (lt, lb), (rt, rb) = hsfont.layout(ch); out = bytearray()
        for cell in ((t[lt], t[lb]), (t[rt], t[rb])):
            if cell not in s.cc: out.append(0xA8); continue
            c = s.cc[cell]
            out += bytes([c]) if c < 0xEF else bytes([0xEF, c - 0xF0])
        return bytes(out)

def build(outp):
    rom = bytearray(open(ORIG, 'rb').read()); rom += b'\xFF' * (0x200000 - len(rom))
    allowed = set(open(os.path.join(W, 'hs', 'allowed.txt'), encoding='utf-8').read())
    # 1) 번역문에 쓰인 음절 빈도 → 칸 빈도
    syl = collections.Counter()
    for gi in hstext.MODES:
        for k in hstext.load_tr(gi).values():
            for c in k:
                if 0xAC00 <= ord(c) <= 0xD7A3:
                    if c not in allowed:
                        assert os.environ.get('LOOSE'), '지원 안 되는 음절 %s (g%03d)' % (c, gi); continue
                    syl[c] += 1
    cellf = collections.Counter(); tilebm = {}
    for c, n in syl.items():
        t = hsfont.tiles_of(c); (lt, lb), (rt, rb) = hsfont.layout(c)
        for cell in ((t[lt], t[lb]), (t[rt], t[rb])): cellf[cell] += n
    # 2) 코드 배정: 많이 쓰는 칸부터 1바이트
    one = [c for c in range(0x02, 0xEF) if c not in KEEP and not (0xCE <= c <= 0xCF or 0xE8 <= c <= 0xEE)]   # 원래 안 쓰던 코드 제외(3DS판 멈춤)
    ext = [0xF0 + x for x in range(26, NTAB - 0xF0)]
    codes = one + ext; cells = [c for c, _ in cellf.most_common()]
    assert len(cells) <= len(codes), ('칸이 너무 많음', len(cells), len(codes))
    cellcode = dict(zip(cells, codes))
    # 3) 타일 배정: 서로 다른 8x8 그림 → 풀 타일
    pool = pool_tiles(bytes(rom)); blank = tuple(tuple([0] * 8) for _ in range(8))
    bms = []
    for cell in cells:
        for bm in cell:
            if bm not in bms: bms.append(bm)
    assert len(bms) <= len(pool), ('타일 부족', len(bms), len(pool))
    tileof = dict(zip(bms, pool))
    # 4) 글자표: 한글 칸 코드는 새 타일, 안 쓰는 가나 코드는 빈칸(공백 타일)
    top, bot = tables(bytes(rom)); sp = (top[1], bot[1])
    for c in range(0x02, NTAB):
        if c in KEEP or c == 0xEF: continue
        struct.pack_into('<H', rom, TOP + 2 * c, sp[0]); struct.pack_into('<H', rom, BOT + 2 * c, sp[1])
    for cell, c in cellcode.items():
        struct.pack_into('<H', rom, TOP + 2 * c, tileof[cell[0]]); struct.pack_into('<H', rom, BOT + 2 * c, tileof[cell[1]])
    # 5) 폰트 블록 다시 쓰기 (배경 1, 글자 3 — 원래 가나와 같은 색)
    blocks = []
    for src in (0x60304, 0x60896):
        d, _ = hslz.decompress(bytes(rom), src); blocks.append(bytearray(d))
    def put(tile, bm):
        b = blocks[tile >> 8]; o = (tile & 0xFF) * 16
        for y in range(8):
            lo = hi = 0
            for x in range(8):
                v = 3 if bm[y][x] else 1; lo |= (v & 1) << (7 - x); hi |= (v >> 1) << (7 - x)
            b[o + 2 * y] = lo; b[o + 2 * y + 1] = hi
    for bm, t in tileof.items(): put(t, bm)
    comma = tuple(tuple(1 if ch == '3' else 0 for ch in row) for row in
                  (['11111111'] * 13 + ['13311111', '11311111', '13111111'])[8:])
    put(bot[0xAA], comma)                              # '、' → 쉼표 모양
    dst = FONT_DST; ptr = []
    for b in blocks:
        cdata = hslz.store(bytes(b)) if os.environ.get("STORE", "1") == "1" else hslz.compress(bytes(b)); rom[off(dst):off(dst) + len(cdata)] = cdata; ptr.append(dst); dst += len(cdata)
        assert (dst & 0xFFFF) < 0x10000 and dst >> 16 == FONT_DST >> 16
    for po, k in FONTPTR.items(): rom[po:po + 3] = struct.pack('<I', ptr[k])[:3]
    # 6) 타이틀 로고(스프라이트) 한글화: 같은 자리(0F:8706)에 원래 크기 이하로 다시 압축 — 주소가 코드 즉시값이라 옮길 수 없음
    import hslogo
    d, end = hslz.decompress(bytes(rom), hslogo.SRC); d = bytearray(d); room = 0x7B7BE - hslogo.SRC
    hslogo.put_canvas(d, hslogo.LOGO, hslogo.make_logo(hslogo.canvas(d, hslogo.LOGO)))
    hslogo.put_canvas(d, hslogo.SUB, hslogo.make_sub(128, 16))
    cache = os.path.join(W, 'hs', 'logo_lz.bin'); key = __import__('hashlib').sha1(bytes(d)).hexdigest()
    if os.path.exists(cache) and open(cache + '.key').read() == key: cl = open(cache, 'rb').read()
    else: cl = hslz.compress_opt(bytes(d)); open(cache, 'wb').write(cl); open(cache + '.key', 'w').write(key)
    assert len(cl) <= room, ('로고 압축이 자리를 넘음', len(cl), room)
    rom[hslogo.SRC:hslogo.SRC + len(cl)] = cl
    # 7) 대사 재배치(롱 점프 없이)
    enc = Enc(cellcode); enc.ok = set(syl); hstext.enc_one.update(ONE)
    hstext.build(rom, enc, dataonly=True, warn=lambda s: None)
    open(outp, 'wb').write(rom)
    print('음절', len(syl), '칸', len(cells), '(1바이트 %d)' % min(len(cells), len(one)), '타일', len(bms), '/', len(pool))

if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(W, 'hs', 'test2.sfc'))
