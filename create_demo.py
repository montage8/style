"""
Create a simple demo MIDI file to test the intro_renderer without needing an actual style file
"""

import mido


def create_demo_style_file(output_path: str):
    """Create a simple demo style file for testing"""
    
    # Create a MIDI file
    midi = mido.MidiFile(ticks_per_beat=480)
    
    # Track 0: Tempo and metadata
    track0 = mido.MidiTrack()
    midi.tracks.append(track0)
    
    track0.append(mido.MetaMessage('track_name', name='Tempo Track', time=0))
    track0.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(120), time=0))
    track0.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    
    # Track 1: Intro A - Simple C major chord pattern with piano voice
    track1 = mido.MidiTrack()
    midi.tracks.append(track1)
    
    track1.append(mido.MetaMessage('track_name', name='Intro A', time=0))
    track1.append(mido.MetaMessage('marker', text='Intro A', time=0))
    
    # Add Bank Select and Program Change for Acoustic Grand Piano
    # MSB=0 (GM bank), LSB=0, Program=0 (Acoustic Grand Piano)
    track1.append(mido.Message('control_change', channel=0, control=0, value=0, time=0))  # Bank MSB
    track1.append(mido.Message('control_change', channel=0, control=32, value=0, time=0))  # Bank LSB
    track1.append(mido.Message('program_change', channel=0, program=0, time=0))  # Acoustic Grand Piano
    track1.append(mido.Message('control_change', channel=0, control=7, value=100, time=0))  # Volume
    track1.append(mido.Message('control_change', channel=0, control=10, value=64, time=0))  # Pan center
    
    # Simple pattern: C-E-G arpeggio (C major chord)
    # Channel 0, C4(60), E4(64), G4(67)
    notes = [
        (0, 60),      # C4 at beat 0
        (480, 64),    # E4 at beat 1
        (960, 67),    # G4 at beat 2
        (1440, 60),   # C4 at beat 3
    ]
    
    current_time = 0
    for abs_time, pitch in notes:
        delta = abs_time - current_time
        track1.append(mido.Message('note_on', note=pitch, velocity=80, channel=0, time=delta))
        track1.append(mido.Message('note_off', note=pitch, velocity=0, channel=0, time=240))  # 1/8 note duration
        current_time = abs_time + 240
    
    track1.append(mido.MetaMessage('end_of_track', time=0))
    
    # Track 2: Another pattern on channel 1 (bass line with acoustic bass)
    track2 = mido.MidiTrack()
    midi.tracks.append(track2)
    
    track2.append(mido.MetaMessage('track_name', name='Bass', time=0))
    
    # Add Bank Select and Program Change for Acoustic Bass
    # MSB=0 (GM bank), LSB=0, Program=32 (Acoustic Bass)
    track2.append(mido.Message('control_change', channel=1, control=0, value=0, time=0))  # Bank MSB
    track2.append(mido.Message('control_change', channel=1, control=32, value=0, time=0))  # Bank LSB
    track2.append(mido.Message('program_change', channel=1, program=32, time=0))  # Acoustic Bass
    track2.append(mido.Message('control_change', channel=1, control=7, value=90, time=0))  # Volume
    
    # Bass notes: C3(48), G2(43)
    bass_notes = [
        (0, 48),      # C3 at beat 0
        (960, 43),    # G2 at beat 2
    ]
    
    current_time = 0
    for abs_time, pitch in bass_notes:
        delta = abs_time - current_time
        track2.append(mido.Message('note_on', note=pitch, velocity=70, channel=1, time=delta))
        track2.append(mido.Message('note_off', note=pitch, velocity=0, channel=1, time=480))  # 1/4 note duration
        current_time = abs_time + 480
    
    track2.append(mido.MetaMessage('end_of_track', time=0))
    
    # Add end of track to tempo track
    track0.append(mido.MetaMessage('end_of_track', time=1920))  # 4 beats * 480 ticks
    
    # Save the file
    midi.save(output_path)
    print(f"✓ Created demo style file: {output_path}")
    print(f"  Tracks: {len(midi.tracks)}")
    print(f"  Ticks per beat: {midi.ticks_per_beat}")


if __name__ == '__main__':
    create_demo_style_file('demo_style.mid')
    
    print("\nYou can now test the intro_renderer with this demo file:")
    print("python intro_renderer.py --style demo_style.mid --section 'Intro A' --chord G --quality major --out intro_G.mid")
