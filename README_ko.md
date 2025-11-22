# 야마하 스타일 파일 (SFF1) 파서 및 인트로 렌더러

## 개요

이 프로젝트는 야마하 SFF1 스타일 파일을 파싱하고, 인트로 섹션을 사용자 지정 코드로 변환하여 MIDI 파일로 렌더링하는 Python 기반 도구입니다.

## 구현 완료 사항

### 핵심 모듈

1. **style_parser.py** - 스타일 파일 파서
   - SFF1 파일 읽기 및 파싱
   - CASM (Chord and Section Management) 청크 추출
   - Sdec, Ctab, Cntt 서브청크 파싱
   - 섹션 패턴 추출 (Intro A/B/C, Main 등)

2. **chord_engine.py** - 코드 엔진
   - 코드 파싱 (C, F#, Eb 등)
   - 코드 톤 생성 (장조/단조)
   - 보이스 리딩 알고리즘
   - 음역 제약 (A2~F4)

3. **intro_renderer.py** - CLI 렌더러
   - 인트로 섹션 렌더링
   - 코드 변환 적용
   - MIDI 파일 생성
   - 명령줄 인터페이스

### 지원 기능

- ✅ SFF1 스타일 파일 파싱 (.sty, .prs)
- ✅ 표준 MIDI 파일도 처리 가능
- ✅ **악기/보이스 보존** - Program Change 및 Bank Select 지원
- ✅ **채널 설정 유지** - Volume, Pan, Reverb, Chorus 보존
- ✅ 섹션 자동 감지 (Intro A, Intro B, Main A 등)
- ✅ 장조/단조 코드 변환
- ✅ 보이스 리딩 알고리즘으로 부드러운 화성 진행
- ✅ **대화형 모드** - 단계별 한글/영문 안내
- ✅ 스크린 리더 친화적인 CLI 인터페이스
- ✅ 명령줄 모드로 스크립팅/자동화 지원
- ✅ 모든 출력은 텍스트 기반

## 사용 방법

### 설치

```bash
pip install -r requirements.txt
```

### 대화형 모드 (권장)

인자 없이 프로그램을 실행하면 단계별 안내를 받을 수 있습니다:

```bash
python intro_renderer.py
```

프로그램이 다음 단계를 안내합니다:
1. 스타일 파일 선택
2. 렌더링할 섹션 선택 (Intro A, Intro B 등)
3. 코드 루트 지정 (C, D, E, F, G, A, B, 샵/플랫 포함)
4. 장조/단조 선택
5. 출력 파일 이름 설정

모든 안내 메시지는 한글과 영문으로 표시되어 접근성이 뛰어납니다.

### 명령줄 모드

자동화나 스크립팅을 위해 모든 매개변수를 명령줄 인자로 제공할 수 있습니다:

```bash
python intro_renderer.py --style 스타일파일.sty --section "Intro A" --chord C --quality major --out intro_C.mid
```

### 명령줄 옵션

- `--style`: 스타일 파일 경로 (.sty, .prs)
- `--section`: 섹션 이름 (예: "Intro A", "Intro B", "Intro C")
- `--chord`: 코드 루트 (예: C, F#, Eb, A)
- `--quality`: 코드 품질 - "major" 또는 "minor"
- `--out`: 출력 MIDI 파일 경로

### 사용 예시

```bash
# 대화형 모드 - 초보자에게 가장 쉬움
python intro_renderer.py

# C 메이저로 Intro A 렌더링
python intro_renderer.py --style PubPiano.S549.sty --section "Intro A" --chord C --quality major --out intro_C.mid

# A 마이너로 Intro B 렌더링
python intro_renderer.py --style mystyle.sty --section "Intro B" --chord A --quality minor --out intro_Am.mid

# Eb 메이저로 Intro A 렌더링
python intro_renderer.py --style mystyle.sty --section "Intro A" --chord Eb --quality major --out intro_Eb.mid

# F# 마이너로 Intro C 렌더링
python intro_renderer.py --style mystyle.sty --section "Intro C" --chord "F#" --quality minor --out intro_F#m.mid
```

## 기술 세부사항

### SFF1 파일 포맷

야마하 SFF1 파일은 표준 MIDI 파일(SMF) 기반에 추가 청크가 있습니다:
- **CASM**: 코드 및 섹션 관리 청크
  - **CSEG**: 코드 세그먼트
  - **Sdec**: 섹션 선언 (예: "Intro A", "Main A")
  - **Ctab**: 채널 테이블 (악기 할당)
  - **Cntt**: 노트 트랜스포즈 테이블

### 악기 및 보이스 처리

파서는 이제 야마하 보이스 선택을 정확하게 처리합니다:
- **Program Change**: 악기/보이스 선택 (0-127)
- **Bank Select MSB** (CC#0): 뱅크 그룹 선택 (0=GM, 63=야마하 프리셋 등)
- **Bank Select LSB** (CC#32): 그룹 내 뱅크 변형 선택
- **Control Changes**: Volume (CC#7), Pan (CC#10), Reverb (CC#91), Chorus (CC#93)

이를 통해 렌더링된 MIDI 파일이 올바른 악기와 이펙트로 원래 야마하 스타일처럼 들립니다.

### 보이스 리딩 알고리즘

보이스 리딩 알고리즘은 다음과 같이 작동합니다:
1. 타겟 코드의 코드 톤 식별
2. 각 노트를 가장 가까운 코드 톤에 매핑
3. 이전 보이싱을 고려하여 보이스 이동 최소화
4. 지정된 범위(기본값: A2~F4) 내에서 노트 유지

## 현재 버전의 제한사항

- 메이저/마이너 코드만 지원 (7화음, sus, dim 등 미지원)
- 한 번에 하나의 인트로 섹션만 처리
- 오프라인 MIDI 생성만 가능 (실시간 재생 없음)
- 기본 보이스 리딩 (향후 버전에서 개선 예정)

## 향후 개선 계획

- 확장 코드 지원 (7화음, 9화음, sus, dim, aug)
- 코드 진행 지원 (여러 마디에 걸친 다른 코드)
- Main 섹션, Fill, Ending 지원
- 실시간 MIDI 재생
- 더 정교한 보이스 리딩 알고리즘
- GUI 인터페이스 (선택 사항)

## 접근성

이 도구는 명령줄 인터페이스와 스크린 리더를 통해 완전히 접근 가능하도록 설계되었습니다. 모든 출력은 텍스트 기반이며 시각장애인 사용자에게 적합합니다.

## 테스트

프로젝트에는 다음 테스트 도구가 포함되어 있습니다:

```bash
# 코드 엔진 테스트
python test_chord_engine.py

# 데모 MIDI 파일 생성
python create_demo.py
```

## 설계 철학

이 프로젝트는 OMB(One Man Band) 같은 기존 스타일 플레이어의 한계를 극복하기 위해 만들어졌습니다:

- OMB는 CASM을 부분적으로만 해석하고, 특정 채널에서만 리보이싱이 작동
- CASM 값을 수정하는 방식은 전체 시스템을 망가뜨릴 수 있음
- 해결책: 스타일 파일을 "C키 기준 패턴"으로만 활용하고, 코드 해석과 보이싱은 자체 알고리즘으로 처리

## 보안

CodeQL 보안 스캔을 통과했으며, 알려진 보안 취약점이 없습니다.

## 파일 구조

```
style/
├── README.md                 # 영문 문서
├── README_ko.md              # 한글 문서 (이 파일)
├── requirements.txt          # Python 의존성
├── .gitignore               # Git 무시 파일
├── style_parser.py          # 스타일 파일 파서
├── chord_engine.py          # 코드 엔진
├── intro_renderer.py        # CLI 렌더러
├── test_chord_engine.py     # 테스트 스크립트
└── create_demo.py           # 데모 파일 생성기
```

## 기여

이 프로젝트는 야마하 스타일 파일을 다루는 모든 분들을 위한 것입니다. 개선 사항이나 버그 리포트는 환영합니다.

## 라이선스

LICENSE 파일을 참조하세요.
