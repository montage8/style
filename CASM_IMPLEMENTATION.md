# CASM 해석기 구현 - Implementation Status

## 완료된 작업 (Completed)

### 1. CASM 파싱 (CASM Parsing)
✅ **Ctab 구조 완전 파싱**:
- NTR (Note Transposition Rule): 0=Root Trans, 1=Root Fixed, 2=Guitar, 3=Bypass
- NTT (Note Transposition Table): 테이블 인덱스
- Bass NTT: 베이스 전용 NTT 설정
- Source Root: 원본 루트 음 (0=C, 1=C#, ...)
- Source Chord: 원본 코드 타입 (0=Major, 2=Minor, ...)
- High Key, Note Low/High: 음역 제한
- Retrigger Rule: 리트리거 규칙

✅ **Cntt 구조 파싱**:
- Note Transposition Table 데이터 추출
- ChordSegment에 포함

### 2. CASM 해석기 (CASM Interpreter)
✅ **casm_interpreter.py 모듈 생성**:
- `apply_ntr_root_trans()`: Root Transpose 모드 - 인터벌 기반 변환
- `apply_ntr_root_fixed()`: Root Fixed 모드 - 음역 내에서 변환
- `apply_casm_transposition()`: Ctab 규칙 적용
- `transpose_pattern_with_casm()`: 패턴 전체 변환
- `get_ctab_for_channel()`: 채널별 Ctab 찾기

✅ **코드 타입 지원**:
- Major, Minor, Major7, Minor7, Dominant 7
- Diminished, Diminished 7, Augmented
- Sus4, Major6, Minor7b5

### 3. 렌더러 업데이트 (Renderer Update)
✅ **intro_renderer.py 수정**:
- CASM 해석기 사용
- Ctab 데이터 있으면 CASM 규칙 적용
- Ctab 없으면 단순 인터벌 변환 (폴백)
- 커스텀 voice leading 대신 CASM 사용

## 작동 방식 (How It Works)

### 현재 구조:
```
사용자 입력: G Major
  ↓
CASM 해석기:
  1. 섹션별 Ctab 찾기
  2. 각 채널의 NTR 모드 확인
  3. Source Root (C) → Target Root (G)
  4. NTR 규칙에 따라 노트 변환
  5. 음역 제한 적용
```

### 예시:
```python
# Bass 채널: NTR=Root Fixed
원본 (C): [48, 43, 52, 48]  # C3, G2, E3, C3
변환 (G): [55, 55, 55, 55]  # G3만 (Root Fixed는 루트만)

# Chord 채널: NTR=Root Trans
원본 (C): [60, 64, 67]  # C4, E4, G4
변환 (G): [67, 71, 74]  # G4, B4, D5 (7 semitone 이동)
```

## 남은 작업 (Remaining Work)

### 1. NTT 테이블 해석 (High Priority)
❌ **Cntt 데이터 해석**:
- Cntt 바이트 구조 파싱
- 코드 타입별 노트 매핑 테이블
- 12개 노트 × 34개 코드 타입 매핑
- NTT 인덱스로 적절한 테이블 선택

### 2. Guitar 모드 (Medium Priority)
❌ **NTR=Guitar 구현**:
- 기타 특유의 보이싱 규칙
- 개방현 시뮬레이션

### 3. On-Bass 코드 (Medium Priority)
❌ **Slash 코드 지원**:
- Dm7/G 같은 코드
- Bass NTT ON/OFF 플래그 사용

### 4. 확장 코드 타입 (Low Priority)
❌ **34+ 야마하 코드 타입**:
- 현재: 11개 기본 코드
- 필요: dim7, 9th, 11th, 13th, altered 등

### 5. 실제 스타일 파일 테스트
❌ **실제 .sty 파일로 검증**:
- CASM 데이터 있는 파일
- 다양한 NTR/NTT 조합
- 복잡한 코드 진행

## 기술적 세부사항 (Technical Details)

### Ctab 바이트 맵:
```
Byte 0:    Ctab ID
Byte 1-8:  Name (ASCII, space-padded)
Byte 9:    Source Channel (0-15)
Byte 10:   NTR (Note Transposition Rule)
Byte 11:   NTT (Note Transposition Table index)
Byte 12:   Bass NTT
Byte 13:   Source Root (0=C, 1=C#, ...)
Byte 14:   Source Chord (0=Maj, 2=Min, ...)
Byte 15:   High Key limit
Byte 16:   Note Low limit
Byte 17:   Note High limit
Byte 18:   Retrigger Rule
Byte 19+:  Additional params (Cntt refs, etc.)
```

### NTR 모드:
- **0 (Root Trans)**: 멜로디 채널용 - 인터벌 유지하며 이동
- **1 (Root Fixed)**: 코드/베이스용 - 음역 내에서 유지
- **2 (Guitar)**: 기타용 - 특수 보이싱
- **3 (Bypass)**: 변환 없음 - 드럼 등

## 다음 단계 (Next Steps)

1. **우선순위 1**: NTT 테이블 해석 구현
   - Cntt 바이트 구조 분석
   - 코드별 노트 매핑 추출
   - 변환 로직에 적용

2. **우선순위 2**: 실제 스타일 파일로 테스트
   - .sty 파일 업로드
   - CASM 데이터 덤프 확인
   - 결과 검증

3. **우선순위 3**: Guitar 모드 및 On-Bass 코드 지원

## 참고 자료 (References)

- Jørgen Sørensen's CASM Format: http://www.jososoft.dk/yamaha/articles/casm_1.htm
- Style CASM Section: http://www.jososoft.dk/yamaha/articles/style2_2.htm
- PSR Tutorial: https://psrtutorial.com/
- StyleFiles PDF: https://wierzba.hier-im-netz.de/stylefiles_v101.pdf

## 현재 상태 (Current Status)

✅ 기본 CASM 해석 작동 중
✅ NTR Root Trans / Root Fixed 구현됨
✅ 채널별 Ctab 매칭 작동
✅ 폴백 모드 (CASM 없을 때)
❌ NTT 테이블 해석 미구현
❌ Guitar 모드 미구현
❌ 복잡한 코드 타입 미지원

**요약**: CASM 파싱과 기본 NTR 모드는 완료. NTT 테이블 해석이 다음 핵심 작업.
