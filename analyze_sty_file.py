#!/usr/bin/env python3
"""
Utility to analyze Yamaha style files and dump CASM/Cntt structures.
This helps understand the byte format of NTT tables for parsing implementation.

Usage:
    python analyze_sty_file.py <style_file.sty>
"""

import sys
from style_parser import read_style_file

def analyze_style(filepath: str):
    """Analyze a style file and dump CASM structure details."""
    print(f"Analyzing style file: {filepath}")
    print("=" * 80)
    
    try:
        style = read_style_file(filepath)
        print(f"\n✓ File loaded successfully")
        print(f"  Tracks: {len(style.tracks)}")
        print(f"  Chord Segments: {len(style.chord_segments)}")
        
        if not style.chord_segments:
            print("\n⚠ No CASM data found in this file")
            print("  This may be a standard MIDI file or SFF2 format")
            return
        
        # Analyze each chord segment
        for i, cseg in enumerate(style.chord_segments):
            print(f"\n{'=' * 80}")
            print(f"Chord Segment {i + 1}")
            print(f"{'=' * 80}")
            
            print(f"\nSections: {', '.join(cseg.sections)}")
            
            print(f"\nCtabs ({len(cseg.ctabs)}):")
            for ctab in cseg.ctabs:
                print(f"  - {ctab.name:10s} | Ch:{ctab.channel:2d} | NTR:{ctab.ntr:2d} | NTT:{ctab.ntt_index:2d} | "
                      f"Src Root:{ctab.source_root:2d} | Src Chord:{ctab.source_chord:2d}")
                
                # Show raw bytes for detailed analysis
                if len(ctab.raw_params) > 0:
                    print(f"    Raw bytes (first 20): {ctab.raw_params[:20].hex()}")
            
            print(f"\nCntt tables ({len(cseg.cntt_data)}):")
            for j, cntt in enumerate(cseg.cntt_data):
                print(f"  Table {j}: {len(cntt)} bytes")
                if len(cntt) > 0:
                    # Show first few bytes
                    print(f"    First 32 bytes: {cntt[:32].hex()}")
                    print(f"    Structure analysis:")
                    
                    # Try to identify patterns
                    # Typical NTT format might be:
                    # - 12 notes (C through B) 
                    # - Each with transformations for various chord types
                    # - Bytes could be: note offsets, octave shifts, or lookup indices
                    
                    # Assume simple format: 12 bytes per chord type
                    if len(cntt) >= 12:
                        print(f"    Possible 12-note pattern:")
                        for k in range(min(12, len(cntt))):
                            print(f"      Note {k:2d}: 0x{cntt[k]:02x} ({cntt[k]:3d})")
                    
                    # Check if length suggests 12 x N structure
                    if len(cntt) % 12 == 0:
                        num_chord_types = len(cntt) // 12
                        print(f"    Possible structure: 12 notes × {num_chord_types} chord types")
                    
                    # Show full hex dump if small enough
                    if len(cntt) <= 256:
                        print(f"\n    Full hex dump:")
                        for offset in range(0, len(cntt), 16):
                            hex_str = cntt[offset:offset+16].hex(' ')
                            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in cntt[offset:offset+16])
                            print(f"      {offset:04x}: {hex_str:47s} {ascii_str}")
        
        print(f"\n{'=' * 80}")
        print("Analysis complete!")
        print("\nNext steps:")
        print("1. Examine the Cntt byte patterns above")
        print("2. Compare with CASM specification from psrtutorial.com")
        print("3. Implement parse_ntt_table() based on the structure")
        
    except Exception as e:
        print(f"\n✗ Error analyzing file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_sty_file.py <style_file.sty>")
        sys.exit(1)
    
    analyze_style(sys.argv[1])
