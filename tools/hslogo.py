# 히어로 전기 타이틀 로고(스프라이트) 복원·교체 도구
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(__file__))
import hslz
from PIL import Image
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = 0x78706                              # 0F:8706 → VRAM 0x8000 (OBJ 문자 기준)
LOGO = dict(x0=24, y0=55, cols=13, rows=4, tiles=[0x00,0x02,0x04,0x06,0x08,0x0a,0x0c,0x0e,0x20,0x22,0x24,0x26,0x28,
             0x2a,0x2c,0x2e,0x40,0x42,0x44,0x46,0x48,0x4a,0x4c,0x4e,0x60,0x62, 0x64,0x66,0x68,0x6a,0x6c,0x6e,0x80,0x82,0x84,0x86,0x88,0x8a,0x8c,
             0x8e,0xa0,0xa2,0xa4,0xa6,0xa8,0xaa,0xac,0xae,0xc0,0xc2,0xc4,0xc6])
SUB = dict(cols=8, rows=1, tiles=[0xe0,0xe2,0xe4,0xe6,0xe8,0xea,0xec,0xee])
def tile_get(d, t):
    b = d[t*32:t*32+32]
    return [[((b[2*y]>>(7-x))&1)|(((b[2*y+1]>>(7-x))&1)<<1)|(((b[16+2*y]>>(7-x))&1)<<2)|(((b[17+2*y]>>(7-x))&1)<<3) for x in range(8)] for y in range(8)]
def tile_put(d, t, px):
    o = t*32
    for y in range(8):
        p = [0,0,0,0]
        for x in range(8):
            v = px[y][x]
            for k in range(4): p[k] |= ((v >> k) & 1) << (7 - x)
        d[o+2*y], d[o+2*y+1], d[o+16+2*y], d[o+17+2*y] = p
def canvas(d, spec):
    """스프라이트 격자 → 인덱스 그림(16x16 단위, 순서: 위 행 왼→오)"""
    cols, rows, ts = spec['cols'], spec['rows'], spec['tiles']
    cv = [[0]*(cols*16) for _ in range(rows*16)]
    for k, t in enumerate(ts):
        cx, cy = (k % cols)*16, (k // cols)*16
        for q, (dx, dy) in enumerate(((0,0),(8,0),(0,8),(8,8))):
            px = tile_get(d, t + [0,1,16,17][q])
            for y in range(8):
                for x in range(8): cv[cy+dy+y][cx+dx+x] = px[y][x]
    return cv
def put_canvas(d, spec, cv):
    cols, ts = spec['cols'], spec['tiles']
    for k, t in enumerate(ts):
        cx, cy = (k % cols)*16, (k // cols)*16
        for q, (dx, dy) in enumerate(((0,0),(8,0),(0,8),(8,8))):
            tile_put(d, t + [0,1,16,17][q], [[cv[cy+dy+y][cx+dx+x] for x in range(8)] for y in range(8)])
def palette(cg, n):
    pal = []
    for i in range(16):
        v = struct.unpack_from('<H', cg, 2*(128 + 16*n + i))[0]
        pal.append(((v & 31) * 8, ((v >> 5) & 31) * 8, ((v >> 10) & 31) * 8))
    return pal
def save(cv, pal, path, scale=4):
    im = Image.new('RGB', (len(cv[0]), len(cv)))
    for y, row in enumerate(cv):
        for x, v in enumerate(row): im.putpixel((x, y), pal[v] if v else (40, 160, 230))
    im.resize((im.width*scale, im.height*scale), Image.NEAREST).save(path)

from PIL import ImageDraw, ImageFont
FONTDIR = os.path.dirname(W)
def text_mask(text, font, size, w, h, shear=0.0, track=0, xoff=0, yoff=0, thr=128):
    f = ImageFont.truetype(os.path.join(FONTDIR, font), size)
    big = Image.new('L', (w * 4, h * 4), 0); dr = ImageDraw.Draw(big)
    x = 0
    for ch in text:
        dr.text((x, 0), ch, font=f, fill=255); x += f.getbbox(ch)[2] + track if ch != ' ' else size // 3
    bb = big.getbbox(); big = big.crop(bb)
    if shear:
        big = big.transform((int(big.width + abs(shear) * big.height), big.height), Image.AFFINE, (1, shear, -shear * big.height if shear > 0 else 0, 0, 1, 0), Image.BICUBIC)
    big = big.resize((w - 2 * xoff, h - 2 * yoff), Image.LANCZOS)
    m = [[0] * w for _ in range(h)]
    for y in range(big.height):
        for x2 in range(big.width):
            if big.getpixel((x2, y)) >= thr: m[y + yoff][x2 + xoff] = 1
    return m
def dilate(m, r):
    h, w = len(m), len(m[0]); out = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if m[y][x]:
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        if dx * dx + dy * dy <= r * r + r and 0 <= y + dy < h and 0 <= x + dx < w: out[y + dy][x + dx] = 1
    return out
def make_logo(orig, text='히어로 전기', font='SeoulHangangEB.ttf'):
    h, w = len(orig), len(orig[0])
    blue = [v for row in orig for v in row if 9 <= v <= 14]; pink = [v for row in orig for v in row if 2 <= v <= 7]
    # 원본 질감 패치(글자·판 안쪽 픽셀만 모은 순환 표본)
    bt = [[orig[y][x] for x in range(w)] for y in range(h)]
    L_ = dilate(text_mask(text, font, 64, w, h, shear=-0.22, track=6, xoff=9, yoff=9, thr=140), 1)
    P = dilate(L_, 4); O = dilate(P, 1)
    def pick(y, x, lo, hi, fallback):
        for r in range(0, 12):
            for dy in range(-r, r + 1):
                for dx in (-r, r) if abs(dy) != r else range(-r, r + 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < h and 0 <= xx < w and lo <= orig[yy][xx] <= hi: return orig[yy][xx]
        return fallback
    cv = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if L_[y][x]:
                v = pick(y, x, 10, 13, 11)
                if y > 0 and not L_[y - 1][x] or x > 0 and not L_[y][x - 1]: v = 9          # 왼쪽 위 밝은 가장자리
                elif y + 1 < h and not L_[y + 1][x] or x + 1 < w and not L_[y][x + 1]: v = 14   # 오른쪽 아래 어두운 가장자리
                cv[y][x] = v
            elif P[y][x]:
                o = orig[y][x]; v = o if o in (3, 4) else 3       # 매끄러운 분홍(원본 무늬 그대로, 없으면 기본색)
                if y > 0 and not P[y - 1][x]: v = 2
                elif y + 1 < h and not P[y + 1][x] or x + 1 < w and not P[y][x + 1]: v = 7
                cv[y][x] = v
            elif O[y][x]: cv[y][x] = 15
    # 판 아래·오른쪽 그림자(원본처럼 남색 1픽셀 더)
    for y in range(h - 1, 0, -1):
        for x in range(w - 1, 0, -1):
            if cv[y][x] == 0 and cv[y - 1][x - 1] not in (0, 1) and cv[y-1][x-1] != 15: cv[y][x] = 15
    return cv
def make_sub(w, h, text='프로젝트 올림푸스', font='NanumSquareNeo-cBd.ttf'):
    M = text_mask(text, font, 44, w, h, shear=-0.12, track=6, xoff=4, yoff=2, thr=150)
    cv = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if M[y][x]:
                cv[y][x] = 2 if (y == 0 or not M[y - 1][x]) else (4 if (y + 1 >= h or not M[y + 1][x]) else 3)
    for y in range(h):
        for x in range(w):
            if cv[y][x] == 0:
                if y > 0 and x > 0 and M[y - 1][x - 1]: cv[y][x] = 7
                elif (y > 1 and x > 0 and M[y - 2][x - 1]) or (y > 0 and x > 1 and M[y - 1][x - 2]): cv[y][x] = 6
    return cv
