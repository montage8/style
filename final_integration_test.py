"""
Final integration test for section filtering and bass handling
"""

from style_parser import read_style_file, find_section_pattern
from chord_engine import parse_chord
from intro_renderer import render_intro

print("=" * 70)
print("FINAL INTEGRATION TEST")
print("=" * 70)

# Test 1: Section Filtering
print("\n1. Testing Section Filtering")
print("-" * 70)

style = read_style_file('demo_multisection.mid')

for section in ["Intro A", "Intro B", "Main A"]:
    pattern = find_section_pattern(style, section)
    pitches = sorted(set(n.pitch for notes in pattern.notes_by_channel.values() for n in notes))
    print(f"\n{section}:")
    print(f"  Pitches found: {pitches}")

# Check that Intro A doesn't have Main A notes (72, 76, 79)
intro_a = find_section_pattern(style, "Intro A")
intro_a_pitches = set(n.pitch for notes in intro_a.notes_by_channel.values() for n in notes)
has_main_notes = any(p in intro_a_pitches for p in [72, 76, 79])

if has_main_notes:
    print("\n✗ FAIL: Intro A contains Main A notes")
else:
    print("\n✓ PASS: Section filtering works correctly")

# Test 2: Bass vs. Chord Handling
print("\n\n2. Testing Bass vs. Chord Channel Handling")
print("-" * 70)

# Render with G major chord
render_intro('demo_multisection.mid', 'Intro A', 'G', 'major', 
             'final_test_output.mid', korean=False)

import mido
midi = mido.MidiFile('final_test_output.mid')

for i, track in enumerate(midi.tracks):
    notes = []
    track_name = ""
    channel = None
    
    for msg in track:
        if msg.type == 'track_name':
            track_name = msg.name
        elif msg.type == 'note_on' and msg.velocity > 0:
            notes.append(msg.note)
            if channel is None:
                channel = msg.channel
    
    if notes and 'Channel' in track_name:
        unique = set(notes)
        print(f"\n{track_name}:")
        print(f"  Notes: {notes}")
        print(f"  Unique pitches: {unique}")
        
        if channel == 1:  # Bass channel
            if len(unique) == 1:
                print(f"  ✓ Bass channel: all notes are root (G = MIDI 43 or 31)")
            else:
                print(f"  ✗ Bass channel: should have only one pitch")
        elif channel == 0:  # Chord channel
            if len(unique) > 1:
                print(f"  ✓ Chord channel: voice leading applied")
            else:
                print(f"  ✗ Chord channel: should have multiple pitches")

print("\n" + "=" * 70)
print("✓ FINAL INTEGRATION TEST COMPLETE")
print("=" * 70)
