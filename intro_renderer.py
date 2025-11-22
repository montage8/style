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
from chord_engine import parse_chord, transform_notes_for_chord


def render_intro(
    style_path: str,
    section_name: str,
    chord_symbol: str,
    quality: str,
    out_path: str
) -> None:
    """
    Render an intro section from a style file to a MIDI file.
    
    Args:
        style_path: Path to the .sty or .prs style file
        section_name: Section to render (e.g., "Intro A", "Intro B")
        chord_symbol: Root note of target chord (e.g., "C", "F#", "Eb")
        quality: Chord quality ("major" or "minor")
        out_path: Output MIDI file path
    """
    print(f"Loading style file: {style_path}")
    
    # Load and parse style file
    try:
        style = read_style_file(style_path)
        print(f"✓ Style loaded: {len(style.midi_data.tracks)} tracks, "
              f"{len(style.chord_segments)} chord segments")
    except Exception as e:
        print(f"✗ Error loading style file: {e}")
        sys.exit(1)
    
    # Find the requested section
    print(f"Finding section: {section_name}")
    try:
        pattern = find_section_pattern(style, section_name)
        print(f"✓ Section found: {pattern}")
    except Exception as e:
        print(f"✗ Error finding section: {e}")
        sys.exit(1)
    
    # Parse target chord
    print(f"Parsing chord: {chord_symbol} {quality}")
    try:
        target_chord = parse_chord(chord_symbol, quality)
        print(f"✓ Chord parsed: {target_chord}")
    except Exception as e:
        print(f"✗ Error parsing chord: {e}")
        sys.exit(1)
    
    # Create output MIDI file
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
        
        # Transform notes to target chord
        # Convert NoteEvent objects to tuples
        note_tuples = [(n.time, n.pitch, n.velocity, n.duration) for n in notes]
        
        # For first measure, no previous voicing
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
    print(f"Saving MIDI file: {out_path}")
    midi_file.save(out_path)
    print(f"✓ MIDI file saved successfully!")
    print(f"  Tempo: {pattern.tempo} BPM")
    print(f"  Time signature: {pattern.time_signature[0]}/{pattern.time_signature[1]}")
    print(f"  Channels: {list(pattern.notes_by_channel.keys())}")
    print(f"  Total events: {total_notes}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Render intro sections from Yamaha SFF1 style files to MIDI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Render Intro A in C major
  python intro_renderer.py --style mystyle.sty --section "Intro A" --chord C --quality major --out intro_C.mid
  
  # Render Intro B in A minor
  python intro_renderer.py --style mystyle.sty --section "Intro B" --chord A --quality minor --out intro_Am.mid
  
  # Render Intro A in Eb major
  python intro_renderer.py --style mystyle.sty --section "Intro A" --chord Eb --quality major --out intro_Eb.mid
        """
    )
    
    parser.add_argument('--style', required=True,
                       help='Path to Yamaha style file (.sty, .prs)')
    
    parser.add_argument('--section', required=True,
                       help='Section name to render (e.g., "Intro A", "Intro B", "Intro C")')
    
    parser.add_argument('--chord', required=True,
                       help='Chord root (e.g., C, F#, Eb, A)')
    
    parser.add_argument('--quality', required=True,
                       choices=['major', 'minor'],
                       help='Chord quality (major or minor)')
    
    parser.add_argument('--out', required=True,
                       help='Output MIDI file path')
    
    args = parser.parse_args()
    
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
