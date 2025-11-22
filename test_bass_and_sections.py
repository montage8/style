"""
Test bass note transformation and section filtering
"""

from chord_engine import parse_chord, transform_bass_notes, transform_notes_for_chord

def test_bass_transformation():
    """Test that bass notes are transformed to root only"""
    print("=== Testing Bass Note Transformation ===")
    
    # Original bass pattern in C (notes: C3, G2, C3, E3)
    bass_notes = [
        (0, 48, 80, 480),      # C3
        (480, 43, 75, 480),    # G2
        (960, 48, 80, 480),    # C3
        (1440, 52, 75, 480),   # E3
    ]
    
    # Transform to G chord
    g_chord = parse_chord("G", "major")
    transformed = transform_bass_notes(bass_notes, g_chord)
    
    print(f"Original bass notes (C): {[n[1] for n in bass_notes]}")
    print(f"Transformed bass notes (G): {[n[1] for n in transformed]}")
    
    # All notes should now be G (MIDI 43 or 31, depending on octave)
    unique_pitches = set(n[1] for n in transformed)
    print(f"Unique pitches in transformed bass: {unique_pitches}")
    
    # Should have only one unique pitch (the root)
    if len(unique_pitches) == 1:
        print("✓ Bass transformation correct - all notes are root")
    else:
        print("✗ Bass transformation failed - multiple pitches found")
    
    print()

def test_regular_voice_leading():
    """Test that non-bass channels still use voice leading"""
    print("=== Testing Regular Voice Leading ===")
    
    # Chord pattern in C (C, E, G)
    chord_notes = [
        (0, 60, 80, 480),   # C4
        (480, 64, 75, 480), # E4
        (960, 67, 70, 480), # G4
    ]
    
    # Transform to G chord
    g_chord = parse_chord("G", "major")
    transformed, _ = transform_notes_for_chord(chord_notes, {}, g_chord)
    
    print(f"Original chord notes (C major): {[n[1] for n in chord_notes]}")
    print(f"Transformed chord notes (G major): {[n[1] for n in transformed]}")
    
    # Should have different pitches (voice leading)
    unique_pitches = set(n[1] for n in transformed)
    if len(unique_pitches) > 1:
        print("✓ Voice leading applied - multiple chord tones used")
    else:
        print("✗ Voice leading failed - only one pitch")
    
    print()

if __name__ == '__main__':
    test_bass_transformation()
    test_regular_voice_leading()
    print("=" * 60)
    print("✓ Tests complete")
    print("=" * 60)
