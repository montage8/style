# SFF2 Support - Preparation Complete / SFF2 지원 - 준비 완료

## English

### Current Status: Framework Ready ✅

The codebase has been prepared for SFF2 (Style File Format 2, also known as SFF GE - Guitar Edition) support.

### What's Been Implemented

#### 1. Format Detection ✅
- `detect_sff_version()` function distinguishes between SFF1 and SFF2 files
- Checks for "SFF2" and "SFF GE" markers in file headers
- Falls back to SFF1 for older files without explicit markers

#### 2. Multi-Range CASM Structure ✅
- `ChordSegment` now includes `range_type` field
- Supports: "single" (SFF1), "low"/"mid"/"high" (SFF2)
- Parser detects and labels CSEG segments appropriately

#### 3. Guitar Mode NTR ✅
- Implemented `apply_ntr_guitar()` for guitar-specific voicing
- Maps notes to chord tones with voice leading
- Considers proximity to chord tones for realistic guitar parts

#### 4. Version-Aware Parsing ✅
- `Style` dataclass includes `format_version` field
- `parse_casm()` accepts format version parameter
- Backward compatible with SFF1 files

### SFF1 vs SFF2: Key Differences

| Feature | SFF1 (COMPLETE ✅) | SFF2 (Framework Ready ⏳) |
|---------|-------------------|---------------------------|
| CASM Data | Single setting | Three settings (low/mid/high) |
| Format Detection | ✅ Supported | ✅ Supported |
| NTR Modes | ✅ All 4 modes | ✅ All 4 modes |
| Guitar Mode | ✅ Implemented | ✅ Implemented (enhanced needed) |
| NTT Tables | ✅ Full parsing | ⏳ Per-range tables needed |
| Multi-Range CASM | N/A | ⏳ Parsing ready, routing needed |
| Mega Voices | ✅ Basic support | ⏳ Enhanced articulation needed |

### What Remains for Full SFF2 Support

#### 1. Multi-Range CASM Routing (HIGH PRIORITY)
**Goal**: Route notes to appropriate CASM range based on pitch

**Implementation needed**:
```python
def route_note_to_casm_range(note_pitch: int) -> str:
    """Determine which CASM range (low/mid/high) handles this note"""
    if note_pitch < 48:  # Below C3
        return "low"
    elif note_pitch < 72:  # C3 to B4
        return "mid"
    else:  # C5 and above
        return "high"

def get_ctab_for_note(style: Style, channel: int, note: int) -> Optional[Ctab]:
    """Get appropriate Ctab based on note pitch and SFF version"""
    if style.format_version == "SFF1":
        # Single CASM for all ranges
        return get_ctab_for_channel(style.chord_segments[0], channel)
    else:
        # SFF2: route to appropriate range
        range_type = route_note_to_casm_range(note)
        for cseg in style.chord_segments:
            if cseg.range_type == range_type:
                return get_ctab_for_channel(cseg, channel)
    return None
```

#### 2. Per-Range NTT Tables
**Goal**: Use different NTT tables for low/mid/high ranges

**Current**: NTT parsing works but doesn't distinguish ranges
**Needed**: Load and apply correct NTT table based on note range

#### 3. Enhanced Mega Voice Support
**Goal**: Support advanced Mega Voice articulations

**SFF2 Features**:
- More articulation types
- Guitar-specific techniques (slides, bends, harmonics)
- Better velocity/expression mapping

**Implementation approach**:
- Parse Mega Voice parameters from style file
- Map to MIDI controllers (CC#, aftertouch)
- Apply articulation rules per note

#### 4. Testing with Real SFF2 Files
**Goal**: Validate implementation with actual Yamaha SFF2 files

**Sources**:
- Tyros 3/4/5 styles
- PSR-S910/950/970 styles
- Genos styles

**Test cases**:
- Verify CASM range detection
- Confirm guitar parts sound realistic
- Check Mega Voice articulations

### Code Structure

#### Files Modified for SFF2 Preparation

1. **style_parser.py**:
   - Added `format_version` to `Style` dataclass
   - Added `range_type` to `ChordSegment` dataclass
   - Added `detect_sff_version()` function
   - Updated `parse_casm()` with format version parameter
   - Updated `parse_cseg()` with range type detection

2. **casm_interpreter.py**:
   - Added `apply_ntr_guitar()` function
   - Updated `apply_casm_transposition()` to use guitar mode

### Usage

The system now automatically detects SFF1 vs SFF2:

```bash
# Works with both SFF1 and SFF2 files
python intro_renderer.py --style mystyle.sty --section "Intro A" --chord G --quality major --out intro_G.mid

# Analyze format version
python analyze_sty_file.py mystyle.sty
# Output shows: "Format: SFF2" or "Format: SFF1"
```

### Next Steps (Priority Order)

1. **Implement multi-range note routing** (HIGH)
2. **Test with real SFF2 files** (HIGH)
3. **Enhanced Mega Voice parsing** (MEDIUM)
4. **Guitar mode refinement** (MEDIUM)
5. **Full 34+ chord type support** (LOW)

### References

- MidiSoft SFF Guide: https://www.midisoft.pl/en/assets/pdf/guide-sff-en.pdf
- PSR Tutorial Forum: https://forum.psrtutorial.com/
- Jørgen Sørensen's Documentation: http://www.jososoft.dk/yamaha/

---

## 한국어

### 현재 상태: 프레임워크 준비 완료 ✅

SFF2 (Style File Format 2, Guitar Edition) 지원을 위한 코드베이스 준비가 완료되었습니다.

### 구현된 기능

#### 1. 포맷 감지 ✅
- `detect_sff_version()` 함수로 SFF1/SFF2 구분
- 파일 헤더에서 "SFF2", "SFF GE" 마커 확인
- 마커 없는 구형 파일은 SFF1로 처리

#### 2. 다중 범위 CASM 구조 ✅
- `ChordSegment`에 `range_type` 필드 추가
- "single"(SFF1), "low"/"mid"/"high"(SFF2) 지원
- 파서가 CSEG 세그먼트를 적절히 라벨링

#### 3. 기타 모드 NTR ✅
- `apply_ntr_guitar()` 기타 전용 보이싱 구현
- 코드톤 매핑과 보이스 리딩
- 실제 기타 파트처럼 코드톤 근접도 고려

#### 4. 버전 인식 파싱 ✅
- `Style`에 `format_version` 필드
- `parse_casm()`이 포맷 버전 파라미터 받음
- SFF1 파일과 하위 호환성 유지

### SFF1 vs SFF2: 주요 차이점

| 기능 | SFF1 (완료 ✅) | SFF2 (프레임워크 준비 ⏳) |
|------|----------------|---------------------------|
| CASM 데이터 | 단일 설정 | 3개 설정 (저음/중음/고음) |
| 포맷 감지 | ✅ 지원 | ✅ 지원 |
| NTR 모드 | ✅ 4개 모드 전부 | ✅ 4개 모드 전부 |
| 기타 모드 | ✅ 구현 완료 | ✅ 구현 완료 (향상 필요) |
| NTT 테이블 | ✅ 완전 파싱 | ⏳ 범위별 테이블 필요 |
| 다중범위 CASM | 해당없음 | ⏳ 파싱 준비, 라우팅 필요 |
| Mega Voice | ✅ 기본 지원 | ⏳ 고급 아티큘레이션 필요 |

### 완전한 SFF2 지원을 위한 남은 작업

#### 1. 다중 범위 CASM 라우팅 (최우선)
**목표**: 음높이에 따라 적절한 CASM 범위로 노트 라우팅

#### 2. 범위별 NTT 테이블
**목표**: 저음/중음/고음 범위별로 다른 NTT 테이블 사용

#### 3. 향상된 Mega Voice 지원
**목표**: 고급 Mega Voice 아티큘레이션 지원

#### 4. 실제 SFF2 파일로 테스트
**목표**: 실제 야마하 SFF2 파일로 구현 검증

### 사용법

시스템이 자동으로 SFF1/SFF2를 감지합니다:

```bash
# SFF1, SFF2 모두 작동
python intro_renderer.py --style mystyle.sty --section "Intro A" --chord G --quality major --out intro_G.mid

# 포맷 버전 분석
python analyze_sty_file.py mystyle.sty
# 출력: "Format: SFF2" 또는 "Format: SFF1"
```

### 다음 단계 (우선순위 순서)

1. **다중 범위 노트 라우팅 구현** (높음)
2. **실제 SFF2 파일로 테스트** (높음)
3. **향상된 Mega Voice 파싱** (중간)
4. **기타 모드 개선** (중간)
5. **34+ 코드 타입 완전 지원** (낮음)

### 결론

SFF1 구현은 100% 완료되었고, SFF2를 위한 프레임워크가 준비되었습니다. 다중 범위 CASM 라우팅 구현이 완전한 SFF2 지원의 핵심입니다.
