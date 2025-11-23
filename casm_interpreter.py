"""
CASM Interpreter for Yamaha Style Files

This module interprets CASM (Chord Arrangement Section Management) rules
from Yamaha style files to transpose and transform MIDI notes according
to NTR (Note Transposition Rule) and NTT (Note Transposition Table) settings.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from style_parser import Ctab, Cntt, ChordSegment


# NTR (Note Transposition Rule) modes
NTR_ROOT_TRANS = 0  # Root Transpose - melodic transposition
NTR_ROOT_FIXED = 1  # Root Fixed - keeps notes in range
NTR_GUITAR = 2  # Guitar mode - guitar-specific voicing
NTR_BYPASS = 3  # No transposition


# Chord types (Yamaha has 34+ types, implementing most common ones)
CHORD_MAJOR = 0
CHORD_MAJOR7 = 1
CHORD_MINOR = 2
CHORD_MINOR7 = 3
CHORD_SEVENTH = 4  # Dominant 7th
CHORD_MINOR7B5 = 5  # Half-diminished
CHORD_DIM = 6
CHORD_DIM7 = 7
CHORD_AUG = 8
CHORD_SUS4 = 9
CHORD_MAJOR6 = 10
CHORD_MINOR6 = 11
CHORD_SUS2 = 12
CHORD_MAJOR9 = 13
CHORD_MINOR9 = 14
CHORD_SEVENTH9 = 15
CHORD_ADD9 = 16
CHORD_MAJOR7_9 = 17

# Chord type name mapping
CHORD_TYPE_NAMES = {
    CHORD_MAJOR: "Major",
    CHORD_MAJOR7: "Major7",
    CHORD_MINOR: "Minor",
    CHORD_MINOR7: "Minor7",
    CHORD_SEVENTH: "7th",
    CHORD_MINOR7B5: "m7b5",
    CHORD_DIM: "Dim",
    CHORD_DIM7: "Dim7",
    CHORD_AUG: "Aug",
    CHORD_SUS4: "Sus4",
    CHORD_MAJOR6: "Major6",
    CHORD_MINOR6: "Minor6",
    CHORD_SUS2: "Sus2",
    CHORD_MAJOR9: "Major9",
    CHORD_MINOR9: "Minor9",
    CHORD_SEVENTH9: "7th9",
    CHORD_ADD9: "Add9",
    CHORD_MAJOR7_9: "Major7/9",
}


def apply_ntr_root_trans(note: int, source_root: int, target_root: int) -> int:
    """
    Apply Root Transpose NTR mode.
    Transposes the note by the interval between source and target roots.
    
    Args:
        note: Original MIDI note number
        source_root: Source root note (0=C, 1=C#, etc.)
        target_root: Target root note
        
    Returns:
        Transposed MIDI note number
    """
    interval = target_root - source_root
    return note + interval


def apply_ntr_root_fixed(note: int, source_root: int, target_root: int, 
                          note_low: int = 0, note_high: int = 127) -> int:
    """
    Apply Root Fixed NTR mode.
    Tries to keep the note in the same range while changing the root.
    
    Args:
        note: Original MIDI note number
        source_root: Source root note (0=C, 1=C#, etc.)
        target_root: Target root note
        note_low: Minimum note limit
        note_high: Maximum note limit
        
    Returns:
        Transposed MIDI note number
    """
    # Get the note class (0-11) relative to source root
    note_class = (note - source_root) % 12
    
    # Find the octave
    octave = note // 12
    
    # Calculate new note with target root
    new_note = octave * 12 + target_root + note_class
    
    # Keep within range
    while new_note < note_low and new_note < 127:
        new_note += 12
    while new_note > note_high and new_note > 0:
        new_note -= 12
    
    return max(0, min(127, new_note))


def apply_ntr_guitar(note: int, source_root: int, target_root: int, target_chord_tones: List[int]) -> int:
    """
    Apply Guitar NTR mode.
    Guitar-specific voicing that considers chord tones and voice leading.
    Maps notes to chord tones when appropriate for realistic guitar parts.
    
    Args:
        note: Original MIDI note number
        source_root: Source root note (0=C, 1=C#, etc.)
        target_root: Target root note
        target_chord_tones: List of chord tone offsets for target chord
        
    Returns:
        Transformed note with guitar-style voicing
    """
    # Calculate base interval
    interval = (target_root - source_root) % 12
    
    # Get note class of the original note
    original_note_class = note % 12
    original_octave = note // 12
    
    # Check if original note is close to a chord tone in the source
    # (within 2 semitones suggests it was meant to be a chord tone or passing tone)
    src_chord_tones = get_chord_tones(source_root, CHORD_MAJOR)  # Assume source is major
    is_near_chord_tone = any(abs((original_note_class - (source_root + tone) % 12 + 6) % 12 - 6) <= 2 
                             for tone in src_chord_tones)
    
    if is_near_chord_tone:
        # Map to closest chord tone in target chord
        target_tones_abs = [(target_root + tone) % 12 for tone in target_chord_tones]
        
        # Find closest chord tone
        new_note_class = min(
            target_tones_abs,
            key=lambda t: min(abs(t - original_note_class), 
                            abs(t - original_note_class + 12), 
                            abs(t - original_note_class - 12))
        )
        
        # Reconstruct pitch preserving octave as much as possible
        new_pitch = original_octave * 12 + new_note_class
        
        # Adjust octave if too far from original (keep within 6 semitones if possible)
        if abs(new_pitch - note) > 6:
            if new_pitch > note:
                new_pitch -= 12
            else:
                new_pitch += 12
        
        return max(0, min(127, new_pitch))
    else:
        # Non-chord tone: simple transpose by interval
        new_pitch = note + interval
        return max(0, min(127, new_pitch))


def get_chord_tones(root: int, chord_type: int) -> List[int]:
    """
    Get the chord tones for a given root and chord type.
    
    Args:
        root: Root note (0=C, 1=C#, etc.)
        chord_type: Chord type constant
        
    Returns:
        List of semitone offsets from root for chord tones
    """
    # Chord tone tables - semitone offsets from root
    chord_tables = {
        CHORD_MAJOR: [0, 4, 7],  # Root, Major 3rd, Perfect 5th
        CHORD_MAJOR7: [0, 4, 7, 11],  # + Major 7th
        CHORD_MINOR: [0, 3, 7],  # Root, Minor 3rd, Perfect 5th
        CHORD_MINOR7: [0, 3, 7, 10],  # + Minor 7th
        CHORD_SEVENTH: [0, 4, 7, 10],  # Dominant 7th
        CHORD_MINOR7B5: [0, 3, 6, 10],  # Half-diminished
        CHORD_DIM: [0, 3, 6],  # Diminished
        CHORD_DIM7: [0, 3, 6, 9],  # Diminished 7th
        CHORD_AUG: [0, 4, 8],  # Augmented
        CHORD_SUS4: [0, 5, 7],  # Suspended 4th
        CHORD_MAJOR6: [0, 4, 7, 9],  # Major 6th
        CHORD_MINOR6: [0, 3, 7, 9],  # Minor 6th
        CHORD_SUS2: [0, 2, 7],  # Suspended 2nd
        CHORD_MAJOR9: [0, 4, 7, 11, 14],  # Major 9th
        CHORD_MINOR9: [0, 3, 7, 10, 14],  # Minor 9th
        CHORD_SEVENTH9: [0, 4, 7, 10, 14],  # Dominant 9th
        CHORD_ADD9: [0, 4, 7, 14],  # Add 9
        CHORD_MAJOR7_9: [0, 4, 7, 11, 14],  # Major 7/9
    }
    
    return chord_tables.get(chord_type, [0, 4, 7])  # Default to major


def apply_casm_transposition(
    note: int,
    ctab: Ctab,
    source_root: int,
    target_root: int,
    target_chord_type: int = CHORD_MAJOR,
    ntt_table: Optional[List[List[int]]] = None
) -> int:
    """
    Apply CASM transposition rules to a single note.
    
    Args:
        note: Original MIDI note number
        ctab: Ctab entry containing NTR/NTT settings
        source_root: Source root from style file (usually C=0)
        target_root: Target root from user input
        target_chord_type: Target chord type
        ntt_table: Optional NTT table for chord-specific transformations
        
    Returns:
        Transposed MIDI note number
    """
    # Use source_root and source_chord from Ctab if available
    src_root = ctab.source_root if ctab.source_root is not None else source_root
    src_chord = ctab.source_chord if ctab.source_chord is not None else CHORD_MAJOR
    
    # If NTT table is available and NTT index is set, try NTT first
    if ntt_table is not None and ctab.ntt is not None and ctab.ntt != 127:
        # NTT-based transformation (more sophisticated)
        return apply_ntt_transformation(
            note, src_root, target_root,
            src_chord, target_chord_type, ntt_table
        )
    
    # Otherwise, apply NTR mode
    if ctab.ntr == NTR_ROOT_TRANS:
        # Root Transpose mode - simple interval transposition
        return apply_ntr_root_trans(note, src_root, target_root)
        
    elif ctab.ntr == NTR_ROOT_FIXED:
        # Root Fixed mode - keep in range
        return apply_ntr_root_fixed(note, src_root, target_root, 
                                     ctab.note_low, ctab.note_high)
        
    elif ctab.ntr == NTR_GUITAR:
        # Guitar mode - guitar-specific voicing
        target_chord_tones = get_chord_tones(target_root, target_chord_type)
        return apply_ntr_guitar(note, src_root, target_root, target_chord_tones)
        
    elif ctab.ntr == NTR_BYPASS:
        # Bypass - no transposition
        return note
        
    else:
        # Default to Root Transpose
        return apply_ntr_root_trans(note, src_root, target_root)


def transpose_pattern_with_casm(
    notes: List[Tuple[int, int, int, int]],  # (time, pitch, velocity, duration)
    ctab: Ctab,
    target_root: int,
    target_chord_type: int = CHORD_MAJOR,
    ntt_table: Optional[List[List[int]]] = None
) -> List[Tuple[int, int, int, int]]:
    """
    Transpose a pattern using CASM rules from a Ctab entry.
    
    Args:
        notes: List of (time, pitch, velocity, duration) tuples
        ctab: Ctab entry with NTR/NTT settings
        target_root: Target root note (0=C, 1=C#, etc.)
        target_chord_type: Target chord type
        ntt_table: Optional NTT table for chord-specific transformations
        
    Returns:
        List of transposed notes
    """
    source_root = ctab.source_root
    
    transformed_notes = []
    for time, pitch, velocity, duration in notes:
        # Apply CASM transposition (with NTT if available)
        new_pitch = apply_casm_transposition(
            pitch, ctab, source_root, target_root, target_chord_type, ntt_table
        )
        
        transformed_notes.append((time, new_pitch, velocity, duration))
    
    return transformed_notes


def get_ntt_table_for_ctab(
    chord_segment: ChordSegment,
    ctab: Ctab
) -> Optional[List[List[int]]]:
    """
    Get the NTT table for a Ctab from the ChordSegment's Cntt list.
    
    Args:
        chord_segment: ChordSegment containing Cntt entries
        ctab: Ctab entry with NTT index
        
    Returns:
        Parsed NTT table or None if not available
    """
    if ctab.ntt is None or ctab.ntt == 127:  # 127 = no NTT
        return None
    
    if not chord_segment.cntts or ctab.ntt >= len(chord_segment.cntts):
        return None
    
    # Get the Cntt entry
    cntt = chord_segment.cntts[ctab.ntt]
    
    # Parse the NTT table from Cntt data
    return parse_ntt_table(cntt.table_data, ctab.ntt)


def get_ctab_for_channel(chord_segment: ChordSegment, channel: int) -> Optional[Ctab]:
    """
    Get the Ctab entry for a specific MIDI channel.
    
    Args:
        chord_segment: ChordSegment containing Ctab entries
        channel: MIDI channel number (0-15)
        
    Returns:
        Ctab entry for the channel, or None if not found
    """
    for ctab in chord_segment.ctabs:
        if ctab.channel == channel:
            return ctab
    return None


def parse_ntt_table(cntt_data: bytes, ntt_index: int = 0) -> Optional[List[List[int]]]:
    """
    Parse NTT (Note Transposition Table) from Cntt data.
    
    NTT table format (from Yamaha documentation):
    - 12 source notes (C, C#, D, D#, E, F, F#, G, G#, A, A#, B)
    - For each note: mapping for each of 34 chord types
    - Each mapping: target note (semitone offset or absolute)
    
    This implementation handles the most common SFF1 format.
    
    Args:
        cntt_data: Raw bytes from Cntt chunk
        ntt_index: Index of the NTT table to use (from Ctab)
        
    Returns:
        2D array [12 notes][34 chord types] or None if cannot parse
    """
    if not cntt_data or len(cntt_data) < 12:
        return None
    
    # Try Format 1: Simple byte array (12 bytes per chord type)
    # This is the most common format in SFF1 files
    # Structure: chord_type_0_note_0, chord_type_0_note_1, ..., chord_type_0_note_11,
    #            chord_type_1_note_0, chord_type_1_note_1, ..., chord_type_1_note_11, ...
    
    if len(cntt_data) % 12 == 0:
        num_chord_types = len(cntt_data) // 12
        
        # Limit to reasonable number of chord types (Yamaha has up to 34+)
        if num_chord_types > 40:
            # Try with header - skip first N bytes
            for header_size in [4, 8, 12, 16]:
                if header_size < len(cntt_data):
                    remaining = cntt_data[header_size:]
                    if len(remaining) % 12 == 0 and len(remaining) // 12 <= 40:
                        cntt_data = remaining
                        num_chord_types = len(cntt_data) // 12
                        break
            else:
                # Still too large, cannot parse
                return None
        
        # Parse bytes into table structure: table[note][chord_type]
        table = [[0 for _ in range(num_chord_types)] for _ in range(12)]
        
        for chord_type in range(num_chord_types):
            for note in range(12):  # C through B
                byte_index = chord_type * 12 + note
                raw_value = cntt_data[byte_index]
                
                # Interpret byte value based on Yamaha encoding:
                # - 0xFF: No change (keep source note)
                # - 0xFE: Mute note
                # - 0-24: Offset encoding (subtract 12 for -12 to +12 range)
                # - Other: Try to interpret as absolute note class
                
                if raw_value == 0xFF:
                    # Special: no change
                    table[note][chord_type] = 0
                elif raw_value == 0xFE:
                    # Special: mute (move far out of range)
                    table[note][chord_type] = -24
                elif raw_value <= 24:
                    # Standard offset encoding: 0-24 → -12 to +12
                    table[note][chord_type] = raw_value - 12
                elif raw_value < 128:
                    # Possible absolute note class or MIDI note
                    # Convert to offset from source note
                    table[note][chord_type] = (raw_value % 12) - note
                else:
                    # Unknown - default to no change
                    table[note][chord_type] = 0
        
        return table
    
    # If format doesn't match, return None
    # System will fall back to NTR-only transposition
    return None


def apply_ntt_transformation(
    note: int,
    source_root: int,
    target_root: int,
    source_chord_type: int,
    target_chord_type: int,
    ntt_table: Optional[List[List[int]]] = None
) -> int:
    """
    Apply NTT (Note Transposition Table) transformation to a note.
    
    This is more sophisticated than NTR as it considers:
    - The source note's relationship to the source chord
    - The target chord type
    - Note mapping tables specific to chord changes
    
    Args:
        note: Original MIDI note number
        source_root: Source root note (0=C, 1=C#, etc.)
        target_root: Target root note
        source_chord_type: Source chord type
        target_chord_type: Target chord type
        ntt_table: Parsed NTT table (12 notes × chord types)
        
    Returns:
        Transformed MIDI note number
    """
    if ntt_table is None:
        # Fallback to simple interval transposition
        interval = target_root - source_root
        return note + interval
    
    # Get note class relative to source root
    note_class = (note % 12 - source_root) % 12
    octave = note // 12
    
    # Look up transformation in NTT table
    try:
        # ntt_table[note_class][target_chord_type] gives target note class
        target_note_class = ntt_table[note_class][target_chord_type]
        
        # Reconstruct note with target root
        new_note = octave * 12 + target_root + target_note_class
        
        return max(0, min(127, new_note))
        
    except (IndexError, TypeError):
        # Fallback to simple transposition
        interval = target_root - source_root
        return note + interval
