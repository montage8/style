"""
Test script to verify program changes are working correctly
"""

import mido
from style_parser import read_style_file, find_section_pattern

def test_program_change_extraction():
    """Test that we can extract program changes from style file"""
    print("=== Testing Program Change Extraction ===")
    print()
    
    # Read demo style file
    style = read_style_file('demo_style.mid')
    print(f"✓ Loaded style: {len(style.midi_data.tracks)} tracks")
    
    # Find Intro A pattern
    pattern = find_section_pattern(style, "Intro A")
    print(f"✓ Found pattern: {pattern}")
    print()
    
    # Check channel info
    print("Channel Information:")
    for channel, info in pattern.channel_info.items():
        print(f"  Channel {channel}:")
        if info.bank_msb is not None:
            print(f"    Bank MSB: {info.bank_msb}")
        if info.bank_lsb is not None:
            print(f"    Bank LSB: {info.bank_lsb}")
        if info.program is not None:
            print(f"    Program: {info.program}")
        if info.volume is not None:
            print(f"    Volume: {info.volume}")
        if info.pan is not None:
            print(f"    Pan: {info.pan}")
    print()
    
    # Verify we have program changes
    has_program_changes = any(info.program is not None for info in pattern.channel_info.values())
    has_bank_select = any(info.bank_msb is not None or info.bank_lsb is not None 
                          for info in pattern.channel_info.values())
    
    if has_program_changes:
        print("✓ Program changes extracted successfully")
    else:
        print("✗ No program changes found")
    
    if has_bank_select:
        print("✓ Bank select messages extracted successfully")
    else:
        print("✗ No bank select messages found")
    
    print()
    print("=== Test Complete ===")

if __name__ == '__main__':
    test_program_change_extraction()
