"""
Intro Renderer - Renders intro sections from Yamaha style files to MIDI

This module provides the main functionality to render intro sections from
Yamaha SFF1 style files with custom chord transformations.
"""

import argparse
import sys
from pathlib import Path
import mido

from style_parser import read_style_file, find_section_pattern
from chord_engine import parse_chord, transform_notes_for_chord, transform_bass_notes


def render_intro(
    style_path: str,
    section_name: str,
    chord_symbol: str,
    quality: str,
    out_path: str,
    korean: bool = False
) -> None:
    """
    Render an intro section from a style file to a MIDI file.
    
    Args:
        style_path: Path to the .sty or .prs style file
        section_name: Section to render (e.g., "Intro A", "Intro B")
        chord_symbol: Root note of target chord (e.g., "C", "F#", "Eb")
        quality: Chord quality ("major" or "minor")
        out_path: Output MIDI file path
        korean: Whether to use Korean messages
    """
    if korean:
        print(f"스타일 파일 로딩 중: {style_path}")
    else:
        print(f"Loading style file: {style_path}")
    
    # Load and parse style file
    try:
        style = read_style_file(style_path)
        if korean:
            print(f"✓ 스타일 로드 완료: {len(style.midi_data.tracks)}개 트랙, "
                  f"{len(style.chord_segments)}개 코드 세그먼트")
        else:
            print(f"✓ Style loaded: {len(style.midi_data.tracks)} tracks, "
                  f"{len(style.chord_segments)} chord segments")
    except Exception as e:
        if korean:
            print(f"✗ 스타일 파일 로딩 오류: {e}")
        else:
            print(f"✗ Error loading style file: {e}")
        sys.exit(1)
    
    # Find the requested section
    if korean:
        print(f"섹션 찾는 중: {section_name}")
    else:
        print(f"Finding section: {section_name}")
    try:
        pattern = find_section_pattern(style, section_name)
        if korean:
            print(f"✓ 섹션 발견: {pattern}")
        else:
            print(f"✓ Section found: {pattern}")
    except Exception as e:
        if korean:
            print(f"✗ 섹션 찾기 오류: {e}")
        else:
            print(f"✗ Error finding section: {e}")
        sys.exit(1)
    
    # Parse target chord
    if korean:
        print(f"코드 파싱 중: {chord_symbol} {quality}")
    else:
        print(f"Parsing chord: {chord_symbol} {quality}")
    try:
        target_chord = parse_chord(chord_symbol, quality)
        if korean:
            print(f"✓ 코드 파싱 완료: {target_chord}")
        else:
            print(f"✓ Chord parsed: {target_chord}")
    except Exception as e:
        if korean:
            print(f"✗ 코드 파싱 오류: {e}")
        else:
            print(f"✗ Error parsing chord: {e}")
        sys.exit(1)
    
    # Create output MIDI file
    if korean:
        print(f"MIDI 파일 생성 중...")
    else:
        print(f"Creating MIDI file...")
    midi_file = mido.MidiFile(ticks_per_beat=pattern.ticks_per_beat)
    
    # Add tempo track
    tempo_track = mido.MidiTrack()
    midi_file.tracks.append(tempo_track)
    
    # Set tempo
    tempo_track.append(mido.MetaMessage('set_tempo', 
                                        tempo=mido.bpm2tempo(pattern.tempo), 
                                        time=0))
    
    # Set time signature
    tempo_track.append(mido.MetaMessage('time_signature',
                                        numerator=pattern.time_signature[0],
                                        denominator=pattern.time_signature[1],
                                        time=0))
    
    # Add track name
    tempo_track.append(mido.MetaMessage('track_name', 
                                        name=f'{section_name} - {chord_symbol} {quality}',
                                        time=0))
    
    # Process each channel
    total_notes = 0
    for channel, notes in pattern.notes_by_channel.items():
        if not notes:
            continue
        
        # Create a track for this channel
        track = mido.MidiTrack()
        midi_file.tracks.append(track)
        
        # Add track name
        track.append(mido.MetaMessage('track_name', 
                                      name=f'Channel {channel}',
                                      time=0))
        
        # Add channel initialization (Bank Select, Program Change, etc.)
        if channel in pattern.channel_info:
            ch_info = pattern.channel_info[channel]
            
            # Bank Select MSB (CC#0)
            if ch_info.bank_msb is not None:
                track.append(mido.Message('control_change',
                                         channel=channel,
                                         control=0,
                                         value=ch_info.bank_msb,
                                         time=0))
            
            # Bank Select LSB (CC#32)
            if ch_info.bank_lsb is not None:
                track.append(mido.Message('control_change',
                                         channel=channel,
                                         control=32,
                                         value=ch_info.bank_lsb,
                                         time=0))
            
            # Program Change
            if ch_info.program is not None:
                track.append(mido.Message('program_change',
                                         channel=channel,
                                         program=ch_info.program,
                                         time=0))
            
            # Volume (CC#7)
            if ch_info.volume is not None:
                track.append(mido.Message('control_change',
                                         channel=channel,
                                         control=7,
                                         value=ch_info.volume,
                                         time=0))
            
            # Pan (CC#10)
            if ch_info.pan is not None:
                track.append(mido.Message('control_change',
                                         channel=channel,
                                         control=10,
                                         value=ch_info.pan,
                                         time=0))
            
            # Reverb (CC#91)
            if ch_info.reverb is not None:
                track.append(mido.Message('control_change',
                                         channel=channel,
                                         control=91,
                                         value=ch_info.reverb,
                                         time=0))
            
            # Chorus (CC#93)
            if ch_info.chorus is not None:
                track.append(mido.Message('control_change',
                                         channel=channel,
                                         control=93,
                                         value=ch_info.chorus,
                                         time=0))
        
        # Transform notes to target chord
        # Convert NoteEvent objects to tuples
        note_tuples = [(n.time, n.pitch, n.velocity, n.duration) for n in notes]
        
        # Check if this is a bass channel - bass should only play root note
        is_bass = False
        if channel in pattern.channel_info:
            is_bass = pattern.channel_info[channel].is_bass_channel()
        
        if is_bass:
            # Bass channels: only play the root note of the chord
            transformed_notes = transform_bass_notes(note_tuples, target_chord)
            new_voicing = {}
        else:
            # Other channels: apply voice leading transformation
            prev_voicing = {}
            transformed_notes, new_voicing = transform_notes_for_chord(
                note_tuples, prev_voicing, target_chord
            )
        
        # Sort by time and convert to MIDI messages
        transformed_notes.sort(key=lambda n: n[0])
        
        # Track the last event time to calculate delta times
        last_time = 0
        pending_note_offs = []  # (time, pitch, channel)
        
        for time, pitch, velocity, duration in transformed_notes:
            note_off_time = time + duration
            pending_note_offs.append((note_off_time, pitch, channel))
        
        # Merge note on and note off events and sort by time
        all_events = []
        for time, pitch, velocity, duration in transformed_notes:
            all_events.append((time, 'note_on', pitch, velocity, channel))
        
        for off_time, pitch, channel in pending_note_offs:
            all_events.append((off_time, 'note_off', pitch, 64, channel))
        
        all_events.sort(key=lambda e: e[0])
        
        # Add MIDI messages with proper delta times
        for abs_time, msg_type, pitch, velocity, ch in all_events:
            delta = abs_time - last_time
            
            if msg_type == 'note_on':
                track.append(mido.Message('note_on',
                                         note=pitch,
                                         velocity=velocity,
                                         channel=ch,
                                         time=delta))
            else:  # note_off
                track.append(mido.Message('note_off',
                                         note=pitch,
                                         velocity=0,
                                         channel=ch,
                                         time=delta))
            
            last_time = abs_time
            total_notes += 1
        
        # Add end of track
        track.append(mido.MetaMessage('end_of_track', time=0))
    
    # Add end of track to tempo track
    tempo_track.append(mido.MetaMessage('end_of_track', 
                                       time=pattern.length_ticks))
    
    # Save MIDI file
    if korean:
        print(f"MIDI 파일 저장 중: {out_path}")
    else:
        print(f"Saving MIDI file: {out_path}")
    midi_file.save(out_path)
    if korean:
        print(f"✓ MIDI 파일 저장 완료!")
        print(f"  템포: {pattern.tempo} BPM")
        print(f"  박자: {pattern.time_signature[0]}/{pattern.time_signature[1]}")
        print(f"  채널: {list(pattern.notes_by_channel.keys())}")
        print(f"  총 이벤트: {total_notes}")
    else:
        print(f"✓ MIDI file saved successfully!")
        print(f"  Tempo: {pattern.tempo} BPM")
        print(f"  Time signature: {pattern.time_signature[0]}/{pattern.time_signature[1]}")
        print(f"  Channels: {list(pattern.notes_by_channel.keys())}")
        print(f"  Total events: {total_notes}")


def interactive_mode():
    """Interactive mode with step-by-step prompts in Korean and English"""
    print("=" * 60)
    print("야마하 스타일 파일 인트로 렌더러")
    print("Yamaha Style File Intro Renderer")
    print("=" * 60)
    print()
    
    # Step 1: Get style file path
    while True:
        style_path = input("1. 스타일 파일 경로를 입력하세요 (.sty, .prs, .mid)\n   Enter style file path: ").strip()
        if not style_path:
            print("   ✗ 파일 경로를 입력해주세요.\n")
            continue
        if not Path(style_path).exists():
            print(f"   ✗ 파일을 찾을 수 없습니다: {style_path}\n")
            continue
        print(f"   ✓ 파일 확인: {style_path}\n")
        break
    
    # Step 2: Get section name
    print("2. 렌더링할 섹션을 입력하세요")
    print("   예시: Intro A, Intro B, Intro C, Main A, Main B")
    section_name = input("   Enter section name: ").strip()
    if not section_name:
        section_name = "Intro A"
        print(f"   ✓ 기본값 사용: {section_name}\n")
    else:
        print(f"   ✓ 섹션 선택: {section_name}\n")
    
    # Step 3: Get chord root
    print("3. 코드 루트를 입력하세요")
    print("   예시: C, D, E, F, G, A, B, C#, Eb, F#, Bb")
    chord_symbol = input("   Enter chord root: ").strip()
    if not chord_symbol:
        chord_symbol = "C"
        print(f"   ✓ 기본값 사용: {chord_symbol}\n")
    else:
        print(f"   ✓ 코드 루트: {chord_symbol}\n")
    
    # Step 4: Get chord quality
    print("4. 코드 품질을 선택하세요")
    print("   1) major (메이저)")
    print("   2) minor (마이너)")
    while True:
        quality_input = input("   선택 (1 또는 2): ").strip()
        if quality_input == "1" or quality_input.lower() == "major":
            quality = "major"
            print(f"   ✓ 선택: major (메이저)\n")
            break
        elif quality_input == "2" or quality_input.lower() == "minor":
            quality = "minor"
            print(f"   ✓ 선택: minor (마이너)\n")
            break
        elif not quality_input:
            quality = "major"
            print(f"   ✓ 기본값 사용: major (메이저)\n")
            break
        else:
            print("   ✗ 1 또는 2를 입력해주세요.\n")
    
    # Step 5: Get output file path
    print("5. 출력 MIDI 파일 경로를 입력하세요")
    out_path = input("   Enter output file path: ").strip()
    if not out_path:
        out_path = f"intro_{chord_symbol}_{quality}.mid"
        print(f"   ✓ 기본값 사용: {out_path}\n")
    else:
        print(f"   ✓ 출력 파일: {out_path}\n")
    
    # Confirm and render
    print("=" * 60)
    print("렌더링 설정 확인:")
    print(f"  스타일 파일: {style_path}")
    print(f"  섹션: {section_name}")
    print(f"  코드: {chord_symbol} {quality}")
    print(f"  출력 파일: {out_path}")
    print("=" * 60)
    
    confirm = input("\n렌더링을 시작하시겠습니까? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', '']:
        print("렌더링이 취소되었습니다.")
        return
    
    print()
    print("=" * 60)
    print("렌더링 시작...")
    print("=" * 60)
    print()
    
    # Render
    render_intro(style_path, section_name, chord_symbol, quality, out_path, korean=True)
    
    print()
    print("=" * 60)
    print("렌더링 완료!")
    print("=" * 60)


def main():
    """Main CLI entry point"""
    # Check if any arguments were provided
    if len(sys.argv) == 1:
        # No arguments - run interactive mode
        interactive_mode()
        return
    
    parser = argparse.ArgumentParser(
        description='Render intro sections from Yamaha SFF1 style files to MIDI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (no arguments)
  python intro_renderer.py
  
  # Command-line mode
  python intro_renderer.py --style mystyle.sty --section "Intro A" --chord C --quality major --out intro_C.mid
  
  # Render Intro B in A minor
  python intro_renderer.py --style mystyle.sty --section "Intro B" --chord A --quality minor --out intro_Am.mid
  
  # Render Intro A in Eb major
  python intro_renderer.py --style mystyle.sty --section "Intro A" --chord Eb --quality major --out intro_Eb.mid
        """
    )
    
    parser.add_argument('--style', required=False,
                       help='Path to Yamaha style file (.sty, .prs)')
    
    parser.add_argument('--section', required=False,
                       help='Section name to render (e.g., "Intro A", "Intro B", "Intro C")')
    
    parser.add_argument('--chord', required=False,
                       help='Chord root (e.g., C, F#, Eb, A)')
    
    parser.add_argument('--quality', required=False,
                       choices=['major', 'minor'],
                       help='Chord quality (major or minor)')
    
    parser.add_argument('--out', required=False,
                       help='Output MIDI file path')
    
    args = parser.parse_args()
    
    # If any required arguments are missing, show error
    if not all([args.style, args.section, args.chord, args.quality, args.out]):
        parser.error("All arguments (--style, --section, --chord, --quality, --out) are required in command-line mode")
    
    # Validate input file exists
    if not Path(args.style).exists():
        print(f"✗ Error: Style file not found: {args.style}")
        sys.exit(1)
    
    # Render intro
    render_intro(
        style_path=args.style,
        section_name=args.section,
        chord_symbol=args.chord,
        quality=args.quality,
        out_path=args.out
    )


if __name__ == '__main__':
    main()
