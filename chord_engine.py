"""
Chord Engine for Voice Leading and Revoicing

This module handles chord parsing, chord tone calculation, and voice leading
algorithms for transforming MIDI notes to different chords.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional


# Note name to semitone mapping (C = 0)
NOTE_NAMES = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
    'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
}

# Voice range constraints (MIDI note numbers)
NOTE_MIN = 45  # A2
NOTE_MAX = 77  # F4


@dataclass
class Chord:
    """Represents a musical chord"""
    root: int  # Root note as semitone (0-11, where C=0)
    is_minor: bool
    quality: str  # "major" or "minor" for now
    
    def __repr__(self):
        root_name = [k for k, v in NOTE_NAMES.items() if v == self.root][0]
        return f"Chord({root_name} {self.quality})"


def parse_chord(symbol: str, quality: str) -> Chord:
    """
    Parse a chord symbol and quality into a Chord object.
    
    Args:
        symbol: Chord root (e.g., "C", "F#", "Eb")
        quality: Chord quality ("major" or "minor")
        
    Returns:
        Chord object
        
    Examples:
        >>> parse_chord("C", "major")
        Chord(C major)
        >>> parse_chord("A", "minor")
        Chord(A minor)
    """
    symbol = symbol.strip()
    
    if symbol not in NOTE_NAMES:
        raise ValueError(f"Unknown chord symbol: {symbol}")
    
    root = NOTE_NAMES[symbol]
    is_minor = quality.lower() == "minor"
    
    return Chord(root=root, is_minor=is_minor, quality=quality.lower())


def build_chord_tones(root: int, is_minor: bool) -> List[int]:
    """
    Build chord tones (as semitones 0-11) for a given chord.
    
    Args:
        root: Root note as semitone (0-11)
        is_minor: True for minor chord, False for major
        
    Returns:
        List of chord tones as semitones (0-11)
        
    Examples:
        >>> build_chord_tones(0, False)  # C major
        [0, 4, 7]  # C, E, G
        >>> build_chord_tones(9, True)  # A minor
        [9, 0, 4]  # A, C, E
    """
    # Major: root, major 3rd (+4), perfect 5th (+7)
    # Minor: root, minor 3rd (+3), perfect 5th (+7)
    third_interval = 3 if is_minor else 4
    fifth_interval = 7
    
    tones = [
        root % 12,
        (root + third_interval) % 12,
        (root + fifth_interval) % 12
    ]
    
    return tones


def find_nearest_chord_tone(pitch: int, chord_tones: List[int], prev_pitch: Optional[int] = None) -> int:
    """
    Find the nearest chord tone for a given pitch, considering voice leading.
    
    Args:
        pitch: Original MIDI pitch
        chord_tones: List of chord tones (as semitones 0-11)
        prev_pitch: Previous pitch for voice leading (optional)
        
    Returns:
        New MIDI pitch that is a chord tone
    """
    pitch_class = pitch % 12
    
    # Find which chord tone is closest to the original pitch class
    min_distance = 12
    best_tone = chord_tones[0]
    
    for tone in chord_tones:
        # Calculate smallest distance (considering wrap-around)
        distance = min(abs(tone - pitch_class), 12 - abs(tone - pitch_class))
        if distance < min_distance:
            min_distance = distance
            best_tone = tone
    
    # Determine octave - try to stay close to original pitch or previous pitch
    reference_pitch = prev_pitch if prev_pitch is not None else pitch
    reference_octave = reference_pitch // 12
    
    # Try different octaves and pick the closest one within range
    candidates = []
    for octave_offset in [-1, 0, 1]:
        candidate = (reference_octave + octave_offset) * 12 + best_tone
        if NOTE_MIN <= candidate <= NOTE_MAX:
            distance = abs(candidate - reference_pitch)
            candidates.append((distance, candidate))
    
    if candidates:
        # Sort by distance and pick the closest
        candidates.sort()
        return candidates[0][1]
    
    # Fallback: just use the best tone in the reference octave, clamped to range
    result = reference_octave * 12 + best_tone
    result = max(NOTE_MIN, min(NOTE_MAX, result))
    return result


def transform_bass_notes(
    notes: List[Tuple[int, int, int, int]],  # (time, pitch, velocity, duration)
    target_chord: Chord
) -> List[Tuple[int, int, int, int]]:
    """
    Transform bass notes to play only the root note of the target chord.
    
    Bass channels should only play the chord root, not apply voice leading.
    This maintains the lowest note at approximately the same octave as the original.
    
    Args:
        notes: List of (time, pitch, velocity, duration) tuples
        target_chord: Target chord to transform notes to
        
    Returns:
        Transformed bass notes (all at chord root)
    """
    if not notes:
        return []
    
    # Find the average octave of the original bass notes
    avg_pitch = sum(n[1] for n in notes) / len(notes)
    target_octave = int(avg_pitch / 12)
    
    # Calculate the root note in the target octave
    root_pitch = target_octave * 12 + target_chord.root
    
    # Make sure it's in a reasonable bass range (E1 to C3)
    # E1 = 28, C3 = 48
    if root_pitch < 28:
        root_pitch += 12
    elif root_pitch > 48:
        root_pitch -= 12
    
    # Transform all notes to the root pitch
    transformed_notes = []
    for time, pitch, velocity, duration in notes:
        transformed_notes.append((time, root_pitch, velocity, duration))
    
    return transformed_notes


def transform_notes_for_chord(
    notes: List[Tuple[int, int, int, int]],  # (time, pitch, velocity, duration)
    prev_voicing: Dict[int, int],  # time -> pitch mapping from previous measure
    target_chord: Chord
) -> Tuple[List[Tuple[int, int, int, int]], Dict[int, int]]:
    """
    Transform a list of notes to fit a target chord using voice leading.
    
    Args:
        notes: List of (time, pitch, velocity, duration) tuples
        prev_voicing: Dictionary mapping time -> pitch from previous measure
        target_chord: Target chord to transform notes to
        
    Returns:
        Tuple of (transformed_notes, new_voicing)
        - transformed_notes: List of (time, pitch, velocity, duration) tuples
        - new_voicing: Dictionary mapping time -> pitch for next measure
    """
    chord_tones = build_chord_tones(target_chord.root, target_chord.is_minor)
    
    transformed_notes = []
    new_voicing = {}
    
    # Sort notes by time for processing
    sorted_notes = sorted(notes, key=lambda n: n[0])
    
    for time, pitch, velocity, duration in sorted_notes:
        # Get previous pitch at this time position (for voice leading)
        prev_pitch = prev_voicing.get(time)
        
        # Transform to nearest chord tone
        new_pitch = find_nearest_chord_tone(pitch, chord_tones, prev_pitch)
        
        transformed_notes.append((time, new_pitch, velocity, duration))
        new_voicing[time] = new_pitch
    
    return transformed_notes, new_voicing


def transpose_pattern(
    notes: List[Tuple[int, int, int, int]],  # (time, pitch, velocity, duration)
    source_root: int,  # Semitone of source key (usually 0 for C)
    target_root: int   # Semitone of target key
) -> List[Tuple[int, int, int, int]]:
    """
    Simple transpose of all notes by a fixed interval.
    
    This is a simpler alternative to voice-leading revoicing.
    
    Args:
        notes: List of (time, pitch, velocity, duration) tuples
        source_root: Root of the source key (0-11)
        target_root: Root of the target key (0-11)
        
    Returns:
        Transposed notes
    """
    interval = target_root - source_root
    
    transposed = []
    for time, pitch, velocity, duration in notes:
        new_pitch = pitch + interval
        # Clamp to valid MIDI range
        new_pitch = max(0, min(127, new_pitch))
        transposed.append((time, new_pitch, velocity, duration))
    
    return transposed
