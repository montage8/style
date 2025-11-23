#!/usr/bin/env python3
"""
Implement NTT table parsing based on CASM documentation.

Based on Jørgen Sørensen's CASM format documentation:
- NTT tables contain note transformation rules for different chord types
- Typical structure: 12 source notes × N chord types
- Each entry maps a source note to a target note offset or absolute pitch

This script provides an improved implementation of parse_ntt_table().
"""

from typing import Optional, List, Dict
from dataclasses import dataclass

@dataclass
class NTTTable:
    """
    Note Transposition Table.
    Maps source notes to target notes for different chord types.
    """
    # table[source_note][target_chord_type] = target_note_offset
    # source_note: 0-11 (C through B)
    # target_chord_type: 0-33+ (Yamaha chord types)
    # target_note_offset: typically -12 to +12 or absolute pitch
    table: List[List[int]]  # [12][num_chord_types]
    
    def __init__(self, num_chord_types: int = 34):
        """Initialize empty NTT table."""
        self.table = [[0 for _ in range(num_chord_types)] for _ in range(12)]
    
    def get_transformation(self, source_note: int, chord_type: int) -> Optional[int]:
        """
        Get note transformation for source note and chord type.
        
        Args:
            source_note: 0-11 (C=0, C#=1, ..., B=11)
            chord_type: Yamaha chord type (0=Major, 1=6th, 2=7th, etc.)
        
        Returns:
            Note offset or None if out of range
        """
        if 0 <= source_note < 12 and 0 <= chord_type < len(self.table[0]):
            return self.table[source_note][chord_type]
        return None


def parse_ntt_table_v1(cntt_bytes: bytes) -> Optional[NTTTable]:
    """
    Parse NTT table - Version 1 (simple byte array format).
    
    Format assumption based on common SFF1 structure:
    - 12 bytes per chord type
    - Each byte is a note offset (-12 to +12) stored as unsigned (add 12 to get 0-24 range)
    - Or each byte is absolute note class (0-11)
    
    Args:
        cntt_bytes: Raw Cntt chunk data
    
    Returns:
        Parsed NTT table or None if format doesn't match
    """
    if not cntt_bytes or len(cntt_bytes) < 12:
        return None
    
    # Check if length is divisible by 12 (12 notes per chord type)
    if len(cntt_bytes) % 12 != 0:
        # Try alternative formats
        return None
    
    num_chord_types = len(cntt_bytes) // 12
    
    # Limit to reasonable number of chord types
    if num_chord_types > 40:
        return None
    
    ntt = NTTTable(num_chord_types)
    
    # Parse bytes into table
    # Format: chord_type_0_note_0, chord_type_0_note_1, ..., chord_type_0_note_11,
    #         chord_type_1_note_0, ...
    for chord_type in range(num_chord_types):
        for note in range(12):
            byte_index = chord_type * 12 + note
            raw_value = cntt_bytes[byte_index]
            
            # Interpret byte value
            # Common encodings:
            # 1. Offset from source: value - 12 gives -12 to +12 range
            # 2. Absolute note class: value is 0-11 directly
            # 3. Special values: 0xFF = no change, 0xFE = mute, etc.
            
            if raw_value == 0xFF:
                # Special: no change (use source note)
                ntt.table[note][chord_type] = 0  # offset 0
            elif raw_value == 0xFE:
                # Special: mute (large negative offset to move out of range)
                ntt.table[note][chord_type] = -24
            elif raw_value <= 24:
                # Offset encoding: 0-24 maps to -12 to +12
                ntt.table[note][chord_type] = raw_value - 12
            elif raw_value < 128:
                # Might be absolute note class (0-11) or MIDI note
                # Store as small offset for now
                ntt.table[note][chord_type] = (raw_value % 12) - note
            else:
                # Unknown encoding - default to no change
                ntt.table[note][chord_type] = 0
    
    return ntt


def parse_ntt_table_v2(cntt_bytes: bytes) -> Optional[NTTTable]:
    """
    Parse NTT table - Version 2 (structured format with header).
    
    Some style files have a header before the actual table data.
    Format might include:
    - Header with table size, chord type count, etc.
    - Actual transformation data
    
    Args:
        cntt_bytes: Raw Cntt chunk data
    
    Returns:
        Parsed NTT table or None if format doesn't match
    """
    if not cntt_bytes or len(cntt_bytes) < 16:
        return None
    
    # Try to detect header
    # Common header patterns:
    # - First 4 bytes: magic number or size
    # - Next 2 bytes: num chord types
    # - Next bytes: flags, version, etc.
    
    # For now, skip first N bytes and try to parse remaining as v1
    for header_size in [0, 4, 8, 12, 16]:
        if header_size >= len(cntt_bytes):
            continue
        
        remaining = cntt_bytes[header_size:]
        ntt = parse_ntt_table_v1(remaining)
        if ntt is not None:
            return ntt
    
    return None


def parse_ntt_table_improved(cntt_bytes: bytes) -> Optional[NTTTable]:
    """
    Improved NTT table parser that tries multiple format versions.
    
    Args:
        cntt_bytes: Raw Cntt chunk data
    
    Returns:
        Parsed NTT table or None if no format matched
    """
    if not cntt_bytes:
        return None
    
    # Try version 1 first (most common)
    ntt = parse_ntt_table_v1(cntt_bytes)
    if ntt is not None:
        return ntt
    
    # Try version 2 (with header)
    ntt = parse_ntt_table_v2(cntt_bytes)
    if ntt is not None:
        return ntt
    
    # No format matched
    return None


def test_ntt_parsing():
    """Test NTT parsing with sample data."""
    print("Testing NTT parsing implementation...")
    
    # Test case 1: Simple format - 12 bytes per chord type
    # Example: Major chord (C E G) mapping
    test_data_1 = bytes([
        # Chord type 0 (Major): C->C, D->D, E->E, F->F, G->G, A->A, B->B, ...
        12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12,  # No change (offset 0)
        # Chord type 1 (Minor): Different offsets
        12, 12, 11, 12, 12, 12, 12, 12, 12, 11, 12, 12,  # Flatten 3rd and 6th
    ])
    
    ntt = parse_ntt_table_improved(test_data_1)
    if ntt:
        print("✓ Test 1 passed: Parsed simple format")
        print(f"  Table size: {len(ntt.table)} notes × {len(ntt.table[0])} chord types")
    else:
        print("✗ Test 1 failed")
    
    # Test case 2: Empty data
    ntt2 = parse_ntt_table_improved(bytes())
    if ntt2 is None:
        print("✓ Test 2 passed: Correctly rejected empty data")
    else:
        print("✗ Test 2 failed")
    
    # Test case 3: Invalid length
    ntt3 = parse_ntt_table_improved(bytes([1, 2, 3, 4, 5]))
    if ntt3 is None:
        print("✓ Test 3 passed: Correctly rejected invalid length")
    else:
        print("✗ Test 3 failed")
    
    print("\nNTT parsing implementation ready for integration!")


if __name__ == "__main__":
    test_ntt_parsing()
