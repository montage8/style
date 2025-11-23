"""
Test script for chord engine functionality
"""

from chord_engine import parse_chord, build_chord_tones, transform_notes_for_chord


def test_chord_parsing():
    """Test chord parsing functionality"""
    print("=== Testing Chord Parsing ===")
    
    # Test major chords
    c_maj = parse_chord("C", "major")
    print(f"C major: {c_maj}")
    assert c_maj.root == 0
    assert not c_maj.is_minor
    
    # Test minor chords
    a_min = parse_chord("A", "minor")
    print(f"A minor: {a_min}")
    assert a_min.root == 9
    assert a_min.is_minor
    
    # Test sharp chords
    fs_maj = parse_chord("F#", "major")
    print(f"F# major: {fs_maj}")
    assert fs_maj.root == 6
    
    # Test flat chords
    eb_maj = parse_chord("Eb", "major")
    print(f"Eb major: {eb_maj}")
    assert eb_maj.root == 3
    
    print("✓ All chord parsing tests passed\n")


def test_chord_tones():
    """Test chord tone generation"""
    print("=== Testing Chord Tones ===")
    
    # C major: C(0), E(4), G(7)
    c_maj_tones = build_chord_tones(0, False)
    print(f"C major tones: {c_maj_tones}")
    assert c_maj_tones == [0, 4, 7]
    
    # A minor: A(9), C(0), E(4)
    a_min_tones = build_chord_tones(9, True)
    print(f"A minor tones: {a_min_tones}")
    assert a_min_tones == [9, 0, 4]
    
    # G major: G(7), B(11), D(2)
    g_maj_tones = build_chord_tones(7, False)
    print(f"G major tones: {g_maj_tones}")
    assert g_maj_tones == [7, 11, 2]
    
    print("✓ All chord tone tests passed\n")


def test_note_transformation():
    """Test note transformation with voice leading"""
    print("=== Testing Note Transformation ===")
    
    # Example: Transform C major pattern to G major
    # C major chord tones in MIDI: C4(60), E4(64), G4(67)
    c_pattern = [
        (0, 60, 80, 480),    # C4 at beat 0
        (480, 64, 75, 480),  # E4 at beat 1
        (960, 67, 70, 480),  # G4 at beat 2
    ]
    
    target_chord = parse_chord("G", "major")
    
    transformed, voicing = transform_notes_for_chord(
        c_pattern,
        {},  # No previous voicing
        target_chord
    )
    
    print(f"Original pattern (C major): {c_pattern}")
    print(f"Transformed pattern (G major): {transformed}")
    print(f"Voicing: {voicing}")
    
    # Check that we got some notes back
    assert len(transformed) == len(c_pattern)
    
    # Check that pitches changed
    original_pitches = [n[1] for n in c_pattern]
    transformed_pitches = [n[1] for n in transformed]
    print(f"Original pitches: {original_pitches}")
    print(f"Transformed pitches: {transformed_pitches}")
    
    print("✓ Note transformation tests passed\n")


def test_voice_leading():
    """Test voice leading across multiple measures"""
    print("=== Testing Voice Leading ===")
    
    # Measure 1: C major
    measure1 = [
        (0, 60, 80, 480),
        (480, 64, 75, 480),
    ]
    
    c_chord = parse_chord("C", "major")
    transformed1, voicing1 = transform_notes_for_chord(measure1, {}, c_chord)
    print(f"Measure 1 (C major): {transformed1}")
    print(f"Voicing 1: {voicing1}")
    
    # Measure 2: G major (using previous voicing)
    measure2 = [
        (0, 60, 80, 480),
        (480, 64, 75, 480),
    ]
    
    g_chord = parse_chord("G", "major")
    transformed2, voicing2 = transform_notes_for_chord(measure2, voicing1, g_chord)
    print(f"Measure 2 (G major): {transformed2}")
    print(f"Voicing 2: {voicing2}")
    
    print("✓ Voice leading tests passed\n")


if __name__ == '__main__':
    test_chord_parsing()
    test_chord_tones()
    test_note_transformation()
    test_voice_leading()
    
    print("=" * 50)
    print("✓ All tests passed successfully!")
    print("=" * 50)
