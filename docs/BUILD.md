# 빌드 방법

번역 대본·원문·그림 편집 명세는 저장소에 없으므로, 아래는 자신이 가진 원본과 번역 파일로 다시 빌드하는 절차입니다.

## 준비물
- 원본 `Lost Heroes 2 (Premium Edition) (Japan).3ds` (MD5 `e73ca7ff1b0475fdab84fd7b4b95dd3a`)
- Python 3.12+ : `pip install pillow numpy opencv-python-headless`
- .NET 6 SDK: `tools/lz11c`(LZ11 압축기, 필수), `tools/ocr`(Windows 일본어 OCR, 그림 글자 검출용)
- 글꼴 `NanumSquareNeo-*.ttf`, `SeoulHangangM.ttf`

## 폴더 구성
```
<작업 폴더>/                    원본 .3ds, 글꼴
  <이 저장소>/
    tools/
    ext/                        추출물 (1단계)
    lz11c/bin/lz11c.exe         dotnet build -c Release -o lz11c/bin tools/lz11c
    gmap.txt                    본문 폰트 글리프→문자 표 (2단계)
    gstaff.txt                  스태프롤 폰트 글리프→문자 표
    strings.json                원문 목록, packs.json 팩 목록
    tr/in/*.json, tr/out/*.json 번역 묶음 {번호: 한국어}
    tex/index.json, tex/uniq.json, tex/allhash.json, tex/edits/*.json, tex/ko/*.png  그림 글자
```

## 순서
1. 추출: `python tools/ctr.py "<원본>.3ds" ext`, `python tools/codeblz.py ext/exefs/.code code.bin`
2. 글리프 표: 폰트 텍스처를 PNG로 풀고 `python tools/glyphmatch.py <Font14.png> g14.txt` (스태프롤은 `glyphmatch_staff.py`) → 가나·영숫자 영역을 순서대로 보정해 `gmap.txt`
3. 원문 목록: `python tools/export.py` → `strings.json`. 묶음으로 나눠 번역하고 `python tools/check.py tr/in/<묶음>.json tr/out/<묶음>.json` 로 검사(토큰·금지 문자·줄 수·줄 폭)
4. 그림 글자: 팩 속 CTPK 텍스처를 PNG로 풀어 `tools/ocr`로 일본어 검출 → `tex/edits/<id>.json` 명세 작성 → `python tools/imgedit.py <id>` (좌표 확인은 `tools/grid.py`). `python tools/texhash.py`로 같은 그림의 모든 사본 표 생성
5. 빌드: (히어로 전기) `python -X utf8 tools/hsbuild2.py hs/herosenki_ko.bin` 후 `python tools/mkpatch.py <출력>.3ds`
6. 업데이트: 복호화된 v1.1.0 업데이트 CIA의 RomFS를 `upd/` 로 추출한 뒤 `python tools/mkupdate.py <원본 업데이트.cia> <한글 업데이트.cia>` (본편과 같은 글리프 표 사용)
7. 실기용: 환경 변수 `LFS_OUT=<폴더>` 를 주고 5·6단계를 실행하면 LayeredFS 폴더가 함께 만들어집니다. 배포용 생성기는 `tools/lfstool` (`dotnet publish -c Release`)
8. 차분: `xdelta3 -e -0 -S none -A -s 원본.3ds 한글.3ds 패치.xdelta` (압축 옵션 없이)
