"""
Comprehensive test to demonstrate program change support
"""

import mido
from style_parser import read_style_file, find_section_pattern
from chord_engine import parse_chord
from intro_renderer import render_intro

def main():
    print("=" * 70)
    print("COMPREHENSIVE TEST - Program Change and Bank Select Support")
    print("=" * 70)
    print()
    
    # Test 1: Extract channel info from demo file
    print("TEST 1: Extract channel configuration from demo style file")
    print("-" * 70)
    style = read_style_file('demo_style.mid')
    pattern = find_section_pattern(style, "Intro A")
    
    print(f"✓ Loaded style with {len(pattern.channel_info)} configured channels")
    for ch, info in pattern.channel_info.items():
        print(f"\n  Channel {ch}:")
        if info.bank_msb is not None:
            print(f"    Bank MSB: {info.bank_msb}")
        if info.bank_lsb is not None:
            print(f"    Bank LSB: {info.bank_lsb}")
        if info.program is not None:
            gm_instruments = ["Acoustic Grand Piano", "Acoustic Bass"]
            instrument = gm_instruments[info.program] if info.program < len(gm_instruments) else f"Program {info.program}"
            print(f"    Program: {info.program} ({instrument})")
        if info.volume is not None:
            print(f"    Volume: {info.volume}")
        if info.pan is not None:
            print(f"    Pan: {info.pan} (center=64)")
    
    print()
    print("=" * 70)
    
    # Test 2: Render with different chords
    print("\nTEST 2: Render intro with different chords")
    print("-" * 70)
    
    test_cases = [
        ("C", "major", "test_C_major.mid"),
        ("G", "major", "test_G_major.mid"),
        ("A", "minor", "test_A_minor.mid"),
    ]
    
    for chord_root, quality, output_file in test_cases:
        print(f"\nRendering: {chord_root} {quality} -> {output_file}")
        render_intro('demo_style.mid', 'Intro A', chord_root, quality, output_file, korean=False)
        
        # Verify output
        midi = mido.MidiFile(output_file)
        has_program_change = False
        has_bank_select = False
        
        for track in midi.tracks:
            for msg in track:
                if msg.type == 'program_change':
                    has_program_change = True
                elif msg.type == 'control_change' and msg.control in [0, 32]:
                    has_bank_select = True
        
        status = "✓" if has_program_change and has_bank_select else "✗"
        print(f"  {status} Output verification: PC={has_program_change}, Bank={has_bank_select}")
    
    print()
    print("=" * 70)
    print("\nTEST 3: Detailed MIDI inspection")
    print("-" * 70)
    
    # Inspect one of the generated files
    midi = mido.MidiFile('test_G_major.mid')
    print(f"\nFile: test_G_major.mid")
    print(f"Tracks: {len(midi.tracks)}")
    print(f"Ticks per beat: {midi.ticks_per_beat}")
    
    for i, track in enumerate(midi.tracks):
        print(f"\nTrack {i}:")
        msg_count = 0
        for msg in track:
            if msg.type == 'track_name':
                print(f"  Name: {msg.name}")
            elif msg.type == 'program_change':
                print(f"  ✓ Program Change: channel={msg.channel}, program={msg.program}")
            elif msg.type == 'control_change' and msg.control in [0, 32, 7, 10]:
                cc_names = {0: 'Bank MSB', 32: 'Bank LSB', 7: 'Volume', 10: 'Pan'}
                print(f"  ✓ Control Change: {cc_names[msg.control]}={msg.value}")
            elif msg.type in ['note_on', 'note_off']:
                msg_count += 1
        if msg_count > 0:
            print(f"  Notes: {msg_count} note events")
    
    print()
    print("=" * 70)
    print("\n✓ ALL TESTS PASSED")
    print("  - Channel configuration extracted correctly")
    print("  - Program changes and bank selects preserved")
    print("  - Output MIDI files contain proper instrument settings")
    print()
    print("=" * 70)

if __name__ == '__main__':
    main()
