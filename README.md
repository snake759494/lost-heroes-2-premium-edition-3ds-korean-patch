# 로스트 히어로즈 2 프리미엄 에디션 (3DS) 비공식 한글패치

닌텐도 3DS 일본판 **ロストヒーローズ2 プレミアムエディション** 비공식 한국어 패치입니다. 이 저장소에는 제작 도구와 기술 문서만 있고, 패치 파일(xdelta)은 [Releases](../../releases)에서 받을 수 있습니다. 게임 원본·일본어 원문·번역 대본은 포함하지 않습니다.

## 적용 방법
1. 아래 해시와 일치하는 **원본 `.3ds`**(복호화된 카트리지 덤프, 1GB)를 준비합니다. CIA나 암호화된 덤프에는 적용할 수 없습니다.
   - PowerShell: `Get-FileHash -Algorithm MD5 -LiteralPath '.\Lost Heroes 2 (Premium Edition) (Japan).3ds'`
2. xdeltaUI 같은 도구로 원본에 xdelta를 적용합니다. 원본 판본에 맞는 것을 고르세요(결과물은 같음).
   - `LostHeroes2PE_3DS_KO_v1.0.xdelta`: NoCrypto 표시가 **켜진** 복호화 덤프용(GodMode9 등, 일반적인 경우)
   - `LostHeroes2PE_3DS_KO_v1.0_CryptoFlag.xdelta`: 복호화는 되었지만 NoCrypto 표시가 **꺼진** 덤프용
   - 「target window checksum mismatch」 오류가 나면 다른 쪽을 적용하세요.
   - 명령줄: `xdelta3 -d -s "Lost Heroes 2 (Premium Edition) (Japan).3ds" LostHeroes2PE_3DS_KO_v1.0.xdelta "Lost Heroes 2 (Premium Edition) (Korean).3ds"`
3. 만들어진 `.3ds`를 Azahar 등 3DS 에뮬레이터에서 실행합니다.

| 항목 | 값 |
| --- | --- |
| 원본 3DS 크기 | 1,073,741,824 바이트 |
| 원본 3DS MD5 | `e73ca7ff1b0475fdab84fd7b4b95dd3a` |
| 원본 3DS SHA-256 | `28c6d18321477ded7712fcd3197dff292a5a052ecf868a90be2a133c9792e771` |
| xdelta SHA-256 | `96c04e2a0c9f4782f18b303e861895cc1884a702252283e30a61e35fa9aeae91` |
| (NoCrypto 꺼진 판본) 원본 3DS MD5 | `f04d2f36f395ef807473c39a57061b26` |
| (NoCrypto 꺼진 판본) 원본 3DS SHA-256 | `6cb7b52fdc7d87a672ee59f8be4598ae25f0a83f2dea2ae0956e4472196f8e08` |
| (NoCrypto 꺼진 판본) xdelta SHA-256 | `714504d24b4b446267d845b0c258622fb20ddb81581e7082cbff0290a1ed7b28` |
| 결과 3DS 크기 | 872,046,592 바이트 |
| 결과 3DS MD5 | `13dc109e8761bcca0e6f62800f2f90e0` |
| 결과 3DS SHA-256 | `5e8f2ac6148ba510b03a91f551480835d286cf96b66de2b1450a65518dfc3036` |

## 주의
- 결과 파일은 복호화 상태(NoCrypto)입니다. **에뮬레이터(Azahar) 기준으로 검증**했으며, 실기(커스텀 펌웨어)에서의 동작은 확인하지 않았습니다.
- 결과 파일은 원본의 빈 공간(패딩)을 잘라내 원본보다 작습니다.
- Azahar에서 화면이 검게 멈추면 설정의 "디스크 셰이더 캐시 사용"을 꺼 보세요.

## 한글화 내용
- 게임 텍스트 고유 문장 27,333개 전부: 메인·서브 이벤트 대사, 거점 대화, 퀘스트, 스킬·아이템·포스·칩 이름과 설명, 전투 메시지, 메뉴·시스템 메시지, 튜토리얼
- 엔딩 스태프롤(전용 명조 폰트 재작성, 인명은 한국어 음역)
- 그림 글자 273장(같은 그림의 사본 포함): 타이틀 로고·메뉴·저작권 표기, 불법복제 경고 화면, 거점·캠프·공통 메뉴 UI, 전투 UI·결과 화면, 튜토리얼 캡션, 오프닝 연출 문장, 큐브 로고·지역명·미니맵 범례, DLC·세이브 화면, 카지노 미니게임, 히어로 이름판
- 게임 자체 폰트 2종(14px·12px 칸)에 한글 1,246자(나눔스퀘어네오 Bold), 스태프롤 폰트에 222자(서울한강체 M)
- 고유명사: 가면라이더·울트라맨·건담 시리즈는 한국 방영·발매 명칭을 아는 경우 그것을, 게임 오리지널 명칭은 음역·의역했습니다.

## 그대로 둔 것
- 게임 중 나오지 않는 디버그·테스트용 데이터
- 튜토리얼 그림 구석의 4~6px 크기 버튼 안내처럼 읽을 수 없을 만큼 작은 글자
- 일부 6~9px 그림 글자(능력치 약칭, 미니맵 범례)는 한글로 바꿨지만 작아서 뭉개져 보일 수 있습니다.

## 검증 범위
Azahar에서 부팅, 타이틀 화면, 오프닝 이벤트 대사(이름표 포함), 첫 전투 진입 직전까지 확인했습니다. 전체 플레이 검증은 하지 않았습니다. 문제를 발견하면 Issues에 알려 주세요.

## 문서
- [CHANGELOG.md](CHANGELOG.md) — 변경 기록
- [docs/TECHNICAL.md](docs/TECHNICAL.md) — 파일 형식과 한글화 방법
- [docs/BUILD.md](docs/BUILD.md) — 직접 빌드하는 방법
- [docs/FONT_CREDITS.md](docs/FONT_CREDITS.md) — 글꼴
- [RIGHTS.md](RIGHTS.md) — 권리 및 외부 자료
