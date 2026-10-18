# 히어로 전기 데이터 전용 한글: 음절 = 8x16 칸 2개(왼/오), 칸 = 8x8 타일(위/아래). 타일·칸을 최대한 공유하는 조합형.
# layout(c) → (L칸=(위타일키,아래타일키), R칸=(...)); tile_img(키) → 8x8 비트맵(0/1)
import os
from PIL import Image, ImageDraw, ImageFont
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(os.path.dirname(W), 'NanumSquareNeo-bRg.ttf')
CHO = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'
JUNG = 'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'
JONG = ' ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ'
VERT = {0, 1, 2, 3, 4, 5, 6, 7, 20}; HOR = {8, 12, 13, 17, 18}
MIXH = {9: 8, 10: 8, 11: 8, 14: 13, 15: 13, 16: 13, 19: 18}          # 섞인 모음 → 가로 부분
MIXV = {9: 0, 10: 1, 11: 20, 14: 4, 15: 5, 16: 20, 19: 20}           # 섞인 모음 → 세로 부분

def dec(c):
    n = ord(c) - 0xAC00; return n // 588, (n % 588) // 28, n % 28

def layout(c):
    """받침은 오른쪽 아래 타일에만: 받침 있는 세로모음 음절 = 왼칸(초성 세로 전체, 무받침과 공유) + 오른칸(모음 위, 받침 아래)"""
    i, v, f = dec(c)
    if not f:
        if v in VERT: return (('A0', i), ('A1', i)), (('a0', v), ('a1', v))
        if v in HOR: return (('BL', i), ('bL', v)), (('BR', i), ('bR', v))
        return (('C', i), ('cH', MIXH[v])), (('c0', MIXV[v]), ('c1', MIXV[v]))
    if v in VERT: return (('A0', i), ('A1', i)), (('d', v), ('F', f))
    if v in HOR: return (('EL', i, v), ('eL', v)), (('ER', i, v), ('F', f))
    return (('GL', i, v), ('gL', v)), (('G0', MIXV[v]), ('F', f))

_cache = {}
def _vowel(ch, w, h):
    """모음 1픽셀 획: 세로형은 기둥+곁가지, 가로형은 막대+곁가지"""
    px = [[0] * w for _ in range(h)]
    def V(x, y0=0, y1=None):
        for y in range(y0, h if y1 is None else y1): px[y][x] = 1
    def Hh(y, x0=0, x1=None):
        for x in range(x0, w if x1 is None else x1): px[y][x] = 1
    m = h // 2
    if ch in 'ㅏㅑㅓㅕㅣㅐㅒㅔㅖ':
        if ch in 'ㅐㅒㅔㅖ':
            V(w - 1); V(w - 4)
            if ch in 'ㅐㅒ': Hh(m - (1 if ch == 'ㅒ' else 0), w - 6 if False else w - 6 + 2, w - 4) if False else None
        else: V(w - 2 if ch in 'ㅏㅑ' else (w - 1 if ch != 'ㅣ' else w // 2))
        if ch in 'ㅏ': Hh(m, w - 1, w)
        if ch == 'ㅑ': Hh(m - 2, w - 1, w); Hh(m + 1, w - 1, w)
        if ch == 'ㅓ': Hh(m, 0, w - 1)
        if ch == 'ㅕ': Hh(m - 2, 0, w - 1); Hh(m + 1, 0, w - 1)
        if ch == 'ㅐ': Hh(m, w - 3, w - 1)
        if ch == 'ㅒ': Hh(m - 2, w - 3, w - 1); Hh(m + 1, w - 3, w - 1)
        if ch == 'ㅔ': Hh(m, w - 6 if w >= 6 else 0, w - 4)
        if ch == 'ㅖ': Hh(m - 2, max(0, w - 6), w - 4); Hh(m + 1, max(0, w - 6), w - 4)
    else:
        Hh(h - 1 if ch in 'ㅗㅛ' else 0) if ch != 'ㅡ' else Hh(h // 2)
        c = w // 2
        if ch == 'ㅗ': V(c, 0, h - 1)
        if ch == 'ㅛ': V(c - 2, 0, h - 1); V(c + 2, 0, h - 1)
        if ch == 'ㅜ': V(c, 1, h)
        if ch == 'ㅠ': V(c - 2, 1, h); V(c + 2, 1, h)
    return px

def jamo(ch, w, h, bold=0):
    """자모 한 글자를 w x h 상자에: 모음은 직접 그림, 자음은 글꼴을 원래 픽셀 크기로 찍음"""
    k = (ch, w, h)
    if k in _cache: return _cache[k]
    if ch in JUNG: px = _vowel(ch, w, h)
    else:
        best = None
        for sz in range(30, 4, -1):
            f = ImageFont.truetype(FONT, sz); im = Image.new('1', (48, 48), 0); d = ImageDraw.Draw(im); d.fontmode = '1'
            d.text((8, 4), ch, font=f, fill=1); bb = im.getbbox()
            if bb and bb[2] - bb[0] <= w and bb[3] - bb[1] <= h: best = im.crop(bb); break
        px = [[0] * w for _ in range(h)]
        if best:
            ox = (w - best.width) // 2; oy = (h - best.height) // 2
            for y in range(best.height):
                for x in range(best.width):
                    if best.getpixel((x, y)): px[oy + y][ox + x] = 1
    _cache[k] = px; return px

def blit(canvas, px, x0, y0):
    for y, row in enumerate(px):
        for x, v in enumerate(row):
            if v and 0 <= y0 + y < 16 and 0 <= x0 + x < 16: canvas[y0 + y][x0 + x] = 1

def syllable_img(c):
    """음절 전체 16x16 (조합 규칙대로)"""
    i, v, f = dec(c); cv = [[0] * 16 for _ in range(16)]
    if not f:
        if v in VERT:
            blit(cv, jamo(CHO[i], 8, 12), 0, 2); blit(cv, jamo(JUNG[v], 5 if v != 20 else 3, 14), 9 if v != 20 else 10, 1)
        elif v in HOR:
            blit(cv, jamo(CHO[i], 11, 7), 2, 1); blit(cv, jamo(JUNG[v], 15, 5 if v != 18 else 3), 0, 9)
        else:
            blit(cv, jamo(CHO[i], 8, 7), 0, 1); blit(cv, jamo(JUNG[MIXH[v]], 8, 5 if MIXH[v] != 18 else 3), 0, 9)
            vv = MIXV[v]; blit(cv, jamo(JUNG[vv], 5 if vv != 20 else 3, 14), 9 if vv != 20 else 10, 1)
    else:
        if v in VERT:
            blit(cv, jamo(CHO[i], 8, 12), 0, 2); blit(cv, jamo(JUNG[v], 5 if v != 20 else 3, 8), 9 if v != 20 else 10, 0)
        elif v in HOR:
            blit(cv, jamo(CHO[i], 11, 5), 2, 0); blit(cv, jamo(JUNG[v], 15, 3), 0, 5)
            blit(cv, [[1] * 0], 0, 0)
        else:
            blit(cv, jamo(CHO[i], 8, 5), 0, 0); blit(cv, jamo(JUNG[MIXH[v]], 8, 3), 0, 5)
            vv = MIXV[v]; blit(cv, jamo(JUNG[vv], 4 if vv != 20 else 3, 8), 10, 0)
        blit(cv, jamo(JONG[f], 7, 7), 8, 9)
    return cv

def tiles_of(c):
    """음절 → {타일키: 8x8} (같은 키는 항상 같은 그림이 되도록 레이아웃 정의와 일치)"""
    cv = syllable_img(c); (lt, lb), (rt, rb) = layout(c)
    q = lambda x0, y0: tuple(tuple(cv[y][x] for x in range(x0, x0 + 8)) for y in range(y0, y0 + 8))
    return {lt: q(0, 0), lb: q(0, 8), rt: q(8, 0), rb: q(8, 8)}

def preview(text, path, scale=3):
    w = sum(16 if 0xAC00 <= ord(c) <= 0xD7A3 else 8 for c in text)
    im = Image.new('RGB', (w, 16), (0, 24, 96)); x = 0
    for c in text:
        if 0xAC00 <= ord(c) <= 0xD7A3:
            cv = syllable_img(c)
            for y in range(16):
                for xx in range(16):
                    if cv[y][xx]: im.putpixel((x + xx, y), (255, 255, 255))
            x += 16
        else: x += 8
    im.resize((w * scale, 16 * scale), Image.NEAREST).save(path)

if __name__ == '__main__':
    import sys
    preview(sys.argv[1], sys.argv[2])
