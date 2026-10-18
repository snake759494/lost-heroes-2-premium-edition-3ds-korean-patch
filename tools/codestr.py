# 히어로 전기(내장 레트로 게임) 래퍼 UI 문자열 패치 — 실행 코드(.code) 안 UTF-16/UTF-8 문자열을 제자리 교체
# 이 문구들은 3DS 시스템 공용 폰트로 그려지는데, 일본판 본체 시스템 폰트에는 한글이 없어
# 실기에서도 표시되도록 영어로 옮긴다. 원래 자리(종료 문자 + 뒤의 0 패딩) 안에서만 바꾼다.
import struct

U16 = [  # (일본어, 영어)
    ('タッチでTOPメニューへ', 'Touch:TOP menu'),
    ('を押すとHOMEメニューに戻ります。', ': Back to HOME Menu'),
    ('データを書き込んでいます。', 'Writing data.'),
    ('電源を切ったりカードに', 'Do not turn'),
    ('触らないでください。', 'power off.'),
    ('ヒーロー戦記のセーブデータが', 'Hero Senki data'),
    ('壊れています。', 'is bad.'),
    ('壊れたデータを削除します。', 'Deleting data'),
    ('次に進む', 'Next'),
    ('本製品の全てのセーブデータが', 'All save data'),
    ('想定外の処理が行われました。', 'Error occurred.'),
    ('プログラムが異常です。', 'Bad program'),
    ('ゲームをリセットしますか？', 'Reset game?'),
    ('保存していないデータは失われます。', 'Unsaved data lost.'),
    ('リセット', 'Reset'),
    ('いいえ', 'No'),
    ('はい', 'OK'),
    ('画面設定', 'Video'),
    ('ノーマル', 'Basic'),
    ('ドットバイドット', 'Pixel 1:1'),
    ('フル', 'Full'),
    ('戻る', '<-'),
    ('初期設定', 'Init'),
    ('ロストヒーローズ２に戻ります。', 'Return to game.'),
    ('ロストヒーローズ２', 'Main Game'),
]
U8 = [('ロストヒーローズ2', 'Main Game'), ('リセット', 'Reset'), ('ゲーム再開', 'Resume'), ('画面設定', 'Video')]

def _cap16(d, s, n):
    """s: 시작, n: 원문 글자 수 -> 쓸 수 있는 글자 수(종료 문자 1칸 제외)"""
    e = s + 2 * n
    if d[e:e+2] != b'\0\0':
        return None  # 종료되지 않는 조각(접두 등)은 길이 그대로만 허용
    z = 0
    while d[e + 2*z:e + 2*z + 2] == b'\0\0': z += 1
    return n + z - 1

def patch(code):
    d = bytearray(code); n16 = n8 = 0
    anchor = d.find('タッチでTOPメニューへ'.encode('utf-16le'))
    assert anchor > 0, 'anchor not found'
    lo, hi = anchor - 0x400, anchor + 0xA00  # 히어로 전기 래퍼 문자열 표 영역
    done = set()
    for jp, en in U16:
        pat = jp.encode('utf-16le'); i = lo
        while True:
            i = d.find(pat, i, hi)
            if i < 0: break
            if i % 2 or i in done: i += 2; continue
            cap = _cap16(d, i, len(jp))
            lim = len(jp) if cap is None else cap
            assert len(en) <= lim, (jp, en, lim)
            b = en.encode('utf-16le'); span = max(2*len(jp), len(b) + (2 if cap is not None else 0))
            if cap is None:  # 종료 없는 조각: 같은 길이로 공백 채움
                b = (en + ' ' * (len(jp) - len(en))).encode('utf-16le'); d[i:i+len(b)] = b
            else:
                d[i:i+span] = b + b'\x00' * (span - len(b))
            done.update(range(i, i + span)); n16 += 1; i += span
    for jp, en in U8:
        pat = jp.encode('utf-8') + b'\0'; i = 0
        while True:
            i = d.find(pat, i)
            if i < 0: break
            if i > 0 and d[i-1] != 0: i += 1; continue  # 다른 문자열의 꼬리는 제외
            b = en.encode('utf-8'); assert len(b) < len(pat)
            d[i:i + len(pat)] = b + b'\0' * (len(pat) - len(b)); n8 += 1; i += len(pat)
    return bytes(d), n16, n8
