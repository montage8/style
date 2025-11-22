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
NTR_GUITAR = 2  # Guitar mode
NTR_BYPASS = 3  # No transposition


# Chord types (simplified - full table has 34+ types in Yamaha)
CHORD_MAJOR = 0
CHORD_MAJOR7 = 1
CHORD_MINOR = 2
CHORD_MINOR7 = 3
CHORD_SEVENTH = 4
CHORD_MINOR7B5 = 5
CHORD_DIM = 6
CHORD_DIM7 = 7
CHORD_AUG = 8
CHORD_SUS4 = 9
CHORD_MAJOR6 = 10


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


def get_chord_tones(root: int, chord_type: int) -> List[int]:
    """
    Get the chord tones for a given root and chord type.
    
    Args:
        root: Root note (0=C, 1=C#, etc.)
        chord_type: Chord type constant
        
    Returns:
        List of semitone offsets from root for chord tones
    """
    # Simplified chord tone tables
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
    }
    
    return chord_tables.get(chord_type, [0, 4, 7])  # Default to major


def apply_casm_transposition(
    note: int,
    ctab: Ctab,
    source_root: int,
    target_root: int,
    target_chord_type: int = CHORD_MAJOR
) -> int:
    """
    Apply CASM transposition rules to a single note.
    
    Args:
        note: Original MIDI note number
        ctab: Ctab entry containing NTR/NTT settings
        source_root: Source root from style file (usually C=0)
        target_root: Target root from user input
        target_chord_type: Target chord type
        
    Returns:
        Transposed MIDI note number
    """
    # Use source_root and source_chord from Ctab if available
    src_root = ctab.source_root if ctab.source_root is not None else source_root
    
    # Apply NTR mode
    if ctab.ntr == NTR_ROOT_TRANS:
        # Root Transpose mode - simple interval transposition
        return apply_ntr_root_trans(note, src_root, target_root)
        
    elif ctab.ntr == NTR_ROOT_FIXED:
        # Root Fixed mode - keep in range
        return apply_ntr_root_fixed(note, src_root, target_root, 
                                     ctab.note_low, ctab.note_high)
        
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
    target_chord_type: int = CHORD_MAJOR
) -> List[Tuple[int, int, int, int]]:
    """
    Transpose a pattern using CASM rules from a Ctab entry.
    
    Args:
        notes: List of (time, pitch, velocity, duration) tuples
        ctab: Ctab entry with NTR/NTT settings
        target_root: Target root note (0=C, 1=C#, etc.)
        target_chord_type: Target chord type
        
    Returns:
        List of transposed notes
    """
    source_root = ctab.source_root
    
    transformed_notes = []
    for time, pitch, velocity, duration in notes:
        # Apply CASM transposition
        new_pitch = apply_casm_transposition(
            pitch, ctab, source_root, target_root, target_chord_type
        )
        
        transformed_notes.append((time, new_pitch, velocity, duration))
    
    return transformed_notes


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
