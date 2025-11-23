# Program Change and Bank Select Support - Summary

## 문제 (Problem)
사용자가 보고한 문제:
- MIDI 재생은 되지만 코드가 야마하 스타일처럼 나오지 않음
- 프로그램 체인지(악기 선택)가 제대로 적용되지 않음

The user reported:
- MIDI playback works but chords don't sound like in Yamaha style files
- Program change (instrument selection) isn't being applied properly

## 해결 방법 (Solution)

### 1. ChannelInfo 데이터 구조 추가
새로운 `ChannelInfo` 클래스를 만들어 각 채널의 설정 정보 저장:
- Bank Select MSB (CC#0)
- Bank Select LSB (CC#32)
- Program Change (악기/보이스)
- Volume (CC#7)
- Pan (CC#10)
- Reverb (CC#91)
- Chorus (CC#93)

### 2. 스타일 파일에서 정보 추출
`find_section_pattern()` 함수 개선:
- Program Change 이벤트 캡처
- Bank Select MSB/LSB 캡처
- Control Change 이벤트 캡처
- 모든 정보를 `IntroPattern.channel_info`에 저장

### 3. 출력 MIDI 파일에 적용
`render_intro()` 함수 개선:
- 각 채널에 대해 Bank Select MSB/LSB 먼저 전송
- Program Change로 악기 설정
- Volume, Pan, Reverb, Chorus 설정
- 노트 이벤트 전송

## 기술 세부사항 (Technical Details)

### Yamaha Voice Selection
야마하 키보드에서 보이스는 3가지 값으로 결정됩니다:
- **MSB**: Bank 그룹 (0=GM, 63=Yamaha Preset, 127=GM Drum 등)
- **LSB**: Bank 변형 (0=Normal, 기타 User/Preset 뱅크)
- **PC**: Program Change (0-127, 실제 악기)

예시:
- GM Piano: MSB=0, LSB=0, PC=0
- Yamaha Preset 1: MSB=63, LSB=0, PC=0
- User Voice: MSB=63, LSB=8, PC=4

### MIDI 메시지 순서
올바른 악기 설정을 위한 메시지 순서:
1. Bank Select MSB (CC#0)
2. Bank Select LSB (CC#32)
3. Program Change
4. Volume, Pan 등 기타 Control Changes
5. Note On/Off 이벤트

## 테스트 결과 (Test Results)

### Before (이전)
```
Channel 0:
  [노트만 있고 악기 정보 없음]
```

### After (이후)
```
Channel 0:
  *** CONTROL CHANGE: channel=0, Bank MSB=0
  *** CONTROL CHANGE: channel=0, Bank LSB=0
  *** PROGRAM CHANGE: channel=0, program=0
  *** CONTROL CHANGE: channel=0, Volume=100
  *** CONTROL CHANGE: channel=0, Pan=64
  note_on: note=59, vel=80, ch=0
  ...
```

## 참고 자료 (References)
- psrtutorial.com - Yamaha Style File Format documentation
- Jørgen Sørensen's CASM Editor documentation
- Yamaha MIDI Data List specifications

## 결과 (Outcome)
이제 렌더링된 MIDI 파일이:
✅ 올바른 악기로 재생됨
✅ 원래 야마하 스타일과 동일한 사운드
✅ Volume, Pan, Effect 설정 유지
✅ Bank Select로 정확한 보이스 뱅크 선택
