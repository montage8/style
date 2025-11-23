# NTT Framework Status / NTT 프레임워크 상태

## English

### What's Been Completed

The **NTT (Note Transposition Table) framework** is now fully implemented in the codebase:

#### 1. Data Structures
- ✅ Extended chord type support from 11 to 18 types
- ✅ Added `CHORD_TYPE_NAMES` mapping for all chord types
- ✅ Cntt data structure already parsed and stored in ChordSegment

#### 2. Core Functions
```python
parse_ntt_table(cntt_data: bytes, ntt_index: int) -> Optional[List[List[int]]]
# Parses NTT table from Cntt chunk data
# Currently returns None - awaiting byte format analysis

apply_ntt_transformation(note, source_root, target_root, 
                         source_chord_type, target_chord_type, 
                         ntt_table) -> int
# Applies NTT-based transformation to a note
# Uses chord-specific note mapping from NTT table
# Falls back to interval transposition if table unavailable

get_ntt_table_for_ctab(chord_segment, ctab) -> Optional[List[List[int]]]
# Retrieves NTT table for a specific Ctab from ChordSegment
# Returns None if NTT index invalid or Cntt unavailable
```

#### 3. Integration
- ✅ `apply_casm_transposition()`: Tries NTT first, falls back to NTR
- ✅ `transpose_pattern_with_casm()`: Passes NTT table to transposition
- ✅ `intro_renderer.py`: Gets NTT table from ChordSegment and uses it

#### 4. Fallback Behavior
- ✅ When no NTT table: Uses NTR-only transposition
- ✅ When NTT parsing fails: Graceful fallback to interval transposition
- ✅ System never crashes due to missing NTT data

### What's Pending

#### NTT Byte Format Analysis and Parsing

**The Challenge**:
The `parse_ntt_table()` function currently returns `None` because:
- Cntt byte format varies significantly between Yamaha keyboard models
- Different style file versions use different table formats
- No single universal byte structure documented

**What's Needed**:
1. **Collect sample .sty files** from various Yamaha models:
   - PSR series (PSR-S670, PSR-S970, etc.)
   - Tyros series
   - Genos
   - CVP series

2. **Analyze Cntt byte structure**:
   - Identify table dimensions (12 notes × ? chord types)
   - Determine byte value meaning (absolute note? semitone offset?)
   - Find octave encoding
   - Detect version markers

3. **Implement parsing logic**:
   - Parse bytes into 2D array structure
   - Handle different format versions
   - Validate table data

4. **Test and verify**:
   - Compare output with Yamaha keyboard
   - Test with various chord types
   - Verify against OMB or similar players

### Expected NTT Table Structure

Based on documentation, the expected format is:

```
NTT Table:
  12 source notes (C, C#, D, D#, E, F, F#, G, G#, A, A#, B)
  ×
  34 chord types (or subset)
  
Example (simplified):
  Source Note | Major | Minor | 7th | Dim | Aug | ...
  C          |   0   |   0   |  0  |  0  |  0  | ...
  C#         |   1   |   0   |  1  |  0  |  1  | ...
  D          |   2   |   2   |  2  |  1  |  2  | ...
  ...

Values represent: semitone offset from target root
```

### How to Continue

#### Option 1: Manual Analysis (Most Reliable)
1. Get actual .sty file
2. Locate Cntt chunk (find "Cntt" in binary)
3. Dump hex bytes
4. Compare with known patterns
5. Reverse engineer byte structure

#### Option 2: Reference Implementation
1. Study OMB or other style player source code
2. Find NTT parsing routines
3. Adapt to Python

#### Option 3: Incremental Approach
1. Start with simplest case (bypass table = identity mapping)
2. Implement for one keyboard model
3. Expand to other models as patterns emerge

### Current Test Results

```bash
$ python3 intro_renderer.py --style demo_style.mid --section "Intro A" --chord G --quality major --out test.mid
✓ Style loaded: 3 tracks, 0 chord segments
✓ Section found
✓ Chord parsed: Chord(G major)
✓ MIDI file saved successfully!
```

Note: demo_style.mid has no CASM data, so it uses simple interval transposition (fallback mode).

---

## 한국어

### 완료된 작업

**NTT (Note Transposition Table) 프레임워크**가 코드베이스에 완전히 구현되었습니다:

#### 1. 데이터 구조
- ✅ 코드 타입 지원 11개에서 18개로 확장
- ✅ 모든 코드 타입에 대한 `CHORD_TYPE_NAMES` 매핑 추가
- ✅ Cntt 데이터 구조 이미 파싱되어 ChordSegment에 저장됨

#### 2. 핵심 함수들
```python
parse_ntt_table(cntt_data: bytes, ntt_index: int) -> Optional[List[List[int]]]
# Cntt 청크 데이터에서 NTT 테이블 파싱
# 현재 None 반환 - 바이트 형식 분석 대기 중

apply_ntt_transformation(note, source_root, target_root, 
                         source_chord_type, target_chord_type, 
                         ntt_table) -> int
# 노트에 NTT 기반 변환 적용
# NTT 테이블의 코드별 노트 매핑 사용
# 테이블 없으면 인터벌 변환으로 폴백

get_ntt_table_for_ctab(chord_segment, ctab) -> Optional[List[List[int]]]
# ChordSegment에서 특정 Ctab의 NTT 테이블 가져오기
# NTT 인덱스 무효하거나 Cntt 없으면 None 반환
```

#### 3. 통합
- ✅ `apply_casm_transposition()`: NTT 먼저 시도, NTR로 폴백
- ✅ `transpose_pattern_with_casm()`: NTT 테이블을 변환에 전달
- ✅ `intro_renderer.py`: ChordSegment에서 NTT 테이블 가져와서 사용

#### 4. 폴백 동작
- ✅ NTT 테이블 없을 때: NTR 전용 변환 사용
- ✅ NTT 파싱 실패 시: 인터벌 변환으로 우아하게 폴백
- ✅ NTT 데이터 없어도 시스템 절대 크래시 안 함

### 대기 중인 작업

#### NTT 바이트 형식 분석 및 파싱

**문제점**:
`parse_ntt_table()` 함수가 현재 None을 반환하는 이유:
- Cntt 바이트 형식이 야마하 키보드 모델마다 크게 다름
- 스타일 파일 버전마다 다른 테이블 형식 사용
- 단일 범용 바이트 구조 문서화 없음

**필요한 작업**:
1. **다양한 야마하 모델의 .sty 파일 수집**:
   - PSR 시리즈 (PSR-S670, PSR-S970 등)
   - Tyros 시리즈
   - Genos
   - CVP 시리즈

2. **Cntt 바이트 구조 분석**:
   - 테이블 차원 확인 (12 노트 × ? 코드 타입)
   - 바이트 값 의미 파악 (절대 노트? 반음 오프셋?)
   - 옥타브 인코딩 찾기
   - 버전 마커 감지

3. **파싱 로직 구현**:
   - 바이트를 2D 배열 구조로 파싱
   - 다양한 형식 버전 처리
   - 테이블 데이터 검증

4. **테스트 및 검증**:
   - 야마하 키보드 출력과 비교
   - 다양한 코드 타입으로 테스트
   - OMB 등 다른 플레이어와 검증

### 예상 NTT 테이블 구조

문서에 따르면 예상 형식:

```
NTT 테이블:
  12개 소스 노트 (C, C#, D, D#, E, F, F#, G, G#, A, A#, B)
  ×
  34개 코드 타입 (또는 부분집합)
  
예시 (단순화):
  소스 노트 | Major | Minor | 7th | Dim | Aug | ...
  C        |   0   |   0   |  0  |  0  |  0  | ...
  C#       |   1   |   0   |  1  |  0  |  1  | ...
  D        |   2   |   2   |  2  |  1  |  2  | ...
  ...

값 의미: 타겟 루트에서의 반음 오프셋
```

### 진행 방법

#### 방법 1: 수동 분석 (가장 신뢰성 높음)
1. 실제 .sty 파일 구하기
2. Cntt 청크 위치 찾기 (바이너리에서 "Cntt" 검색)
3. 헥스 바이트 덤프
4. 알려진 패턴과 비교
5. 바이트 구조 역공학

#### 방법 2: 참조 구현
1. OMB 또는 다른 스타일 플레이어 소스 코드 연구
2. NTT 파싱 루틴 찾기
3. Python으로 적응

#### 방법 3: 점진적 접근
1. 가장 간단한 경우부터 시작 (bypass 테이블 = 항등 매핑)
2. 한 키보드 모델에 대해 구현
3. 패턴 발견되면 다른 모델로 확장

### 현재 테스트 결과

```bash
$ python3 intro_renderer.py --style demo_style.mid --section "Intro A" --chord G --quality major --out test.mid
✓ Style loaded: 3 tracks, 0 chord segments
✓ Section found
✓ Chord parsed: Chord(G major)
✓ MIDI file saved successfully!
```

참고: demo_style.mid는 CASM 데이터가 없어서 단순 인터벌 변환 사용 (폴백 모드).
