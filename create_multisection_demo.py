"""
Create a comprehensive demo style file with multiple sections and bass channel
"""

import mido


def create_comprehensive_demo():
    """Create a demo style file with Intro A, Intro B, and Main A sections, plus bass"""
    
    midi = mido.MidiFile(ticks_per_beat=480)
    
    # Track 0: Tempo and metadata
    track0 = mido.MidiTrack()
    midi.tracks.append(track0)
    track0.append(mido.MetaMessage('track_name', name='Tempo Track', time=0))
    track0.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(120), time=0))
    track0.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    
    # Track 1: Intro A - Piano (channel 0)
    track1 = mido.MidiTrack()
    midi.tracks.append(track1)
    track1.append(mido.MetaMessage('track_name', name='Intro A', time=0))
    track1.append(mido.MetaMessage('marker', text='Intro A', time=0))
    
    # Program Change for Acoustic Grand Piano
    track1.append(mido.Message('control_change', channel=0, control=0, value=0, time=0))
    track1.append(mido.Message('control_change', channel=0, control=32, value=0, time=0))
    track1.append(mido.Message('program_change', channel=0, program=0, time=0))
    
    # C major arpeggio pattern
    intro_a_notes = [(0, 60), (480, 64), (960, 67), (1440, 60)]
    current_time = 0
    for abs_time, pitch in intro_a_notes:
        delta = abs_time - current_time
        track1.append(mido.Message('note_on', note=pitch, velocity=80, channel=0, time=delta))
        track1.append(mido.Message('note_off', note=pitch, velocity=0, channel=0, time=240))
        current_time = abs_time + 240
    
    track1.append(mido.MetaMessage('end_of_track', time=0))
    
    # Track 2: Intro B - Piano (channel 0)
    track2 = mido.MidiTrack()
    midi.tracks.append(track2)
    track2.append(mido.MetaMessage('track_name', name='Intro B', time=0))
    track2.append(mido.MetaMessage('marker', text='Intro B', time=0))
    
    # Program Change
    track2.append(mido.Message('control_change', channel=0, control=0, value=0, time=0))
    track2.append(mido.Message('control_change', channel=0, control=32, value=0, time=0))
    track2.append(mido.Message('program_change', channel=0, program=0, time=0))
    
    # Different pattern for Intro B
    intro_b_notes = [(0, 67), (480, 64), (960, 60), (1440, 64)]
    current_time = 0
    for abs_time, pitch in intro_b_notes:
        delta = abs_time - current_time
        track2.append(mido.Message('note_on', note=pitch, velocity=80, channel=0, time=delta))
        track2.append(mido.Message('note_off', note=pitch, velocity=0, channel=0, time=240))
        current_time = abs_time + 240
    
    track2.append(mido.MetaMessage('end_of_track', time=0))
    
    # Track 3: Intro A Bass (channel 1)
    track3 = mido.MidiTrack()
    midi.tracks.append(track3)
    track3.append(mido.MetaMessage('track_name', name='Intro A - Bass', time=0))
    
    # Program Change for Acoustic Bass
    track3.append(mido.Message('control_change', channel=1, control=0, value=0, time=0))
    track3.append(mido.Message('control_change', channel=1, control=32, value=0, time=0))
    track3.append(mido.Message('program_change', channel=1, program=32, time=0))
    
    # Bass pattern - various notes that should all become root
    bass_notes = [(0, 48), (960, 43), (1440, 52), (1680, 48)]  # C3, G2, E3, C3
    current_time = 0
    for abs_time, pitch in bass_notes:
        delta = abs_time - current_time
        track3.append(mido.Message('note_on', note=pitch, velocity=70, channel=1, time=delta))
        track3.append(mido.Message('note_off', note=pitch, velocity=0, channel=1, time=240))
        current_time = abs_time + 240
    
    track3.append(mido.MetaMessage('end_of_track', time=0))
    
    # Track 4: Main A - Piano (channel 0)
    track4 = mido.MidiTrack()
    midi.tracks.append(track4)
    track4.append(mido.MetaMessage('track_name', name='Main A', time=0))
    track4.append(mido.MetaMessage('marker', text='Main A', time=0))
    
    # Program Change
    track4.append(mido.Message('control_change', channel=0, control=0, value=0, time=0))
    track4.append(mido.Message('control_change', channel=0, control=32, value=0, time=0))
    track4.append(mido.Message('program_change', channel=0, program=0, time=0))
    
    # Main A pattern (should NOT appear when requesting Intro A)
    main_a_notes = [(0, 72), (480, 76), (960, 79)]
    current_time = 0
    for abs_time, pitch in main_a_notes:
        delta = abs_time - current_time
        track4.append(mido.Message('note_on', note=pitch, velocity=80, channel=0, time=delta))
        track4.append(mido.Message('note_off', note=pitch, velocity=0, channel=0, time=240))
        current_time = abs_time + 240
    
    track4.append(mido.MetaMessage('end_of_track', time=0))
    
    # Add end of track to tempo track
    track0.append(mido.MetaMessage('end_of_track', time=1920))
    
    # Create a CASM-like structure in a separate track for channel info
    # This would normally be in CASM chunk, but we'll simulate with track names
    track5 = mido.MidiTrack()
    midi.tracks.append(track5)
    track5.append(mido.MetaMessage('track_name', name='Channel Info', time=0))
    track5.append(mido.MetaMessage('text', text='Channel 1: Bass', time=0))
    track5.append(mido.MetaMessage('end_of_track', time=0))
    
    # Save the file
    midi.save('demo_multisection.mid')
    print(f"✓ Created comprehensive demo style file: demo_multisection.mid")
    print(f"  Tracks: {len(midi.tracks)}")
    print(f"  Sections: Intro A, Intro B, Main A")
    print(f"  Channels: 0 (Piano), 1 (Bass)")


if __name__ == '__main__':
    create_comprehensive_demo()
