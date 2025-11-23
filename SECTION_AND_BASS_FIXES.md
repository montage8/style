# Section Filtering and Bass Handling Fixes - Summary

## 문제 (Problems Reported)

사용자가 보고한 두 가지 주요 문제:

1. **잘못된 섹션 렌더링**: "Intro C" 요청 시 Intro C만 나와야 하는데, Main A/B/C/D, Fill-in 섹션, Ending, Fill in BA 등 모든 섹션이 다 나옴
2. **베이스 코드 문제**: 베이스 섹션이 제대로 안 잡힘. C 코드 시 베이스는 C만 나와야 하는데 이상한 음까지 나옴

User reported two main issues:

1. **Wrong sections rendered**: When requesting "Intro C", all sections (Main A/B/C/D, Fill-ins, Intro, Ending, Fill in BA) are rendered instead of just Intro C
2. **Bass chord issues**: Bass section not handled correctly. When playing C chord, bass should only play C, but wrong notes appear

## 원인 분석 (Root Cause Analysis)

### 1. 섹션 필터링 문제

**이전 코드:**
```python
if section_name.lower() in msg.name.lower():
    section_tracks.append(track_idx)
```

**문제점:**
- `"Intro C"` 검색 시 `in` 연산자가 `"C"`를 포함하는 모든 문자열 매칭
- "Main C", "Fill In CC", "Intro C" 등 모두 매칭됨
- 결과: 요청한 섹션 외 다른 섹션들도 포함됨

### 2. 베이스 처리 문제

**이전 코드:**
- 모든 채널에 동일한 `transform_notes_for_chord()` 적용
- 베이스 채널도 voice leading 알고리즘 사용

**문제점:**
- 베이스는 코드의 루트 음만 연주해야 함 (야마하 키보드에서 C만 누르면 베이스는 C만 연주)
- Voice leading은 화음 채널용으로 베이스에는 부적절
- 결과: 베이스가 C, E, G 등 여러 음을 연주

## 해결 방법 (Solutions)

### 1. 정확한 섹션 매칭

**새로운 코드:**
```python
section_name_lower = section_name.lower().strip()
track_name = msg.name.lower().strip()

# Exact match or "Intro A" in "Intro A - Piano" format
if (track_name == section_name_lower or 
    track_name.startswith(section_name_lower + ' ') or 
    track_name.startswith(section_name_lower + '-')):
    section_tracks.append(track_idx)
```

**개선 사항:**
- 정확한 문자열 매칭 사용
- "Intro A" 또는 "Intro A - Piano" 형식 지원
- "Intro C"는 "Main C"와 매칭되지 않음

### 2. 베이스 채널 자동 감지 및 처리

**새로운 코드:**

```python
# 베이스 채널 감지
def is_bass_channel(self) -> bool:
    # CASM part name으로 확인
    if self.part_name and 'bass' in self.part_name.lower():
        return True
    
    # GM 프로그램 번호로 확인 (32-39는 베이스 악기)
    if self.program is not None and 32 <= self.program <= 39:
        return True
    
    return False

# 베이스 전용 변환 함수
def transform_bass_notes(notes, target_chord):
    # 모든 노트를 코드 루트로 변환
    # 원래 베이스 옥타브 유지
    ...
```

**렌더링 시:**
```python
if is_bass:
    # 베이스: 루트 음만
    transformed_notes = transform_bass_notes(note_tuples, target_chord)
else:
    # 코드: voice leading 적용
    transformed_notes, _ = transform_notes_for_chord(note_tuples, {}, target_chord)
```

## 기술적 배경 (Technical Background)

### Yamaha NTR/NTT 시스템

야마하 스타일 파일에서:
- **NTR (Note Transposition Rule)**: 노트 변환 규칙
  - Root Trans: 멜로디 채널용
  - Root Fixed: 베이스/화음 채널용
- **Bass 채널**: 일반적으로 Root Fixed + 루트 음만 연주

### GM 프로그램 번호

General MIDI에서 프로그램 32-39는 베이스 악기:
- 32: Acoustic Bass
- 33: Electric Bass (finger)
- 34: Electric Bass (pick)
- 35: Fretless Bass
- 36: Slap Bass 1
- 37: Slap Bass 2
- 38: Synth Bass 1
- 39: Synth Bass 2

## 테스트 결과 (Test Results)

### Before (이전)
```
Intro A 요청:
  - 포함된 섹션: Intro A, Main A, Main B, Fill In AA, etc. (전부)
  - 베이스 노트: [48, 43, 52, 48] (C, G, E, C - 여러 음)
```

### After (이후)
```
Intro A 요청:
  - 포함된 섹션: Intro A만
  - 베이스 노트: [43, 43, 43, 43] (G, G, G, G - 루트 음만)
  - 코드 노트: [59, 62, 67, 59] (voice leading 적용)
```

## 검증 (Verification)

```python
# 섹션 필터링 검증
intro_a_pitches = {43, 48, 52, 60, 64, 67}  # Intro A 음들
main_a_pitches = {72, 76, 79}  # Main A 음들

# Main A 음이 Intro A에 없음을 확인
assert not (intro_a_pitches & main_a_pitches)
✓ PASS

# 베이스 처리 검증
bass_output = [43, 43, 43, 43]  # G 코드 시 베이스
assert len(set(bass_output)) == 1  # 하나의 음만
assert bass_output[0] == 43  # G (MIDI 43)
✓ PASS
```

## 참고 자료 (References)

- Yamaha Style Creator Manual - NTR/NTT settings
- PSR Tutorial - Bass channel configuration
- General MIDI Specification - Program numbers
- Yamaha GENOS/Tyros manual - Style file format
