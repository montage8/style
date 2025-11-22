"""
Yamaha Style File Format (SFF1) Parser

This module provides functionality to parse Yamaha SFF1 style files,
extracting CASM (Chord and Section Management) information and MIDI patterns.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import struct
import mido


@dataclass
class Ctab:
    """Represents a Ctab (Channel Table) entry in CASM"""
    name: str
    channel: int
    raw_params: bytes
    
    def __repr__(self):
        return f"Ctab(name='{self.name}', channel={self.channel})"


@dataclass
class ChordSegment:
    """Represents a CSEG (Chord Segment) in CASM"""
    sections: List[str]  # List of section names from Sdec
    ctabs: List[Ctab]
    
    def __repr__(self):
        return f"ChordSegment(sections={self.sections}, ctabs={len(self.ctabs)})"


@dataclass
class NoteEvent:
    """Represents a MIDI note event with timing"""
    time: int  # Time in ticks
    pitch: int  # MIDI note number (0-127)
    velocity: int  # Note velocity (0-127)
    duration: int  # Note duration in ticks
    channel: int  # MIDI channel (0-15)


@dataclass
class IntroPattern:
    """Represents a parsed intro/section pattern from the style"""
    ticks_per_beat: int
    length_ticks: int
    tempo: int  # BPM
    time_signature: Tuple[int, int]  # (numerator, denominator)
    notes_by_channel: Dict[int, List[NoteEvent]]  # channel -> list of note events
    
    def __repr__(self):
        channels = list(self.notes_by_channel.keys())
        total_notes = sum(len(notes) for notes in self.notes_by_channel.values())
        return f"IntroPattern(tempo={self.tempo}, channels={channels}, total_notes={total_notes})"


@dataclass
class Style:
    """Represents a complete Yamaha style file"""
    raw_bytes: bytes
    midi_data: mido.MidiFile
    chord_segments: List[ChordSegment]
    
    def __repr__(self):
        return f"Style(tracks={len(self.midi_data.tracks)}, cseg={len(self.chord_segments)})"


def read_style_file(path: str) -> Style:
    """
    Read and parse a Yamaha SFF1 style file.
    
    Args:
        path: Path to the .sty or .prs file
        
    Returns:
        Style object containing parsed data
    """
    with open(path, 'rb') as f:
        raw_bytes = f.read()
    
    # Parse MIDI data
    try:
        midi_data = mido.MidiFile(path)
    except Exception as e:
        raise ValueError(f"Failed to parse MIDI data: {e}")
    
    # Parse CASM chunks
    chord_segments = parse_casm(raw_bytes)
    
    return Style(
        raw_bytes=raw_bytes,
        midi_data=midi_data,
        chord_segments=chord_segments
    )


def parse_casm(style_bytes: bytes) -> List[ChordSegment]:
    """
    Parse CASM (Chord and Section Management) chunk from style file.
    
    Args:
        style_bytes: Raw bytes of the style file
        
    Returns:
        List of ChordSegment objects
    """
    chord_segments = []
    
    # Find CASM chunk
    casm_pos = style_bytes.find(b'CASM')
    if casm_pos == -1:
        return chord_segments
    
    # Read CASM length (4 bytes after CASM marker)
    casm_length = struct.unpack('>I', style_bytes[casm_pos + 4:casm_pos + 8])[0]
    casm_data = style_bytes[casm_pos + 8:casm_pos + 8 + casm_length]
    
    # Parse CSEGs within CASM
    pos = 0
    while pos < len(casm_data) - 4:
        # Look for CSEG marker
        if casm_data[pos:pos + 4] == b'CSEG':
            cseg_length = struct.unpack('>I', casm_data[pos + 4:pos + 8])[0]
            cseg_data = casm_data[pos + 8:pos + 8 + cseg_length]
            
            # Parse this CSEG
            cseg = parse_cseg(cseg_data)
            if cseg:
                chord_segments.append(cseg)
            
            pos += 8 + cseg_length
        else:
            pos += 1
    
    return chord_segments


def parse_cseg(cseg_data: bytes) -> Optional[ChordSegment]:
    """
    Parse a single CSEG (Chord Segment).
    
    Args:
        cseg_data: Raw bytes of the CSEG chunk
        
    Returns:
        ChordSegment object or None
    """
    sections = []
    ctabs = []
    
    pos = 0
    while pos < len(cseg_data) - 4:
        chunk_type = cseg_data[pos:pos + 4]
        
        if chunk_type == b'Sdec':
            # Section declaration - parse section names
            sdec_length = struct.unpack('>I', cseg_data[pos + 4:pos + 8])[0]
            sdec_data = cseg_data[pos + 8:pos + 8 + sdec_length]
            
            # Section names are comma-separated ASCII text
            section_text = sdec_data.decode('ascii', errors='ignore').rstrip('\x00')
            sections = [s.strip() for s in section_text.split(',') if s.strip()]
            
            pos += 8 + sdec_length
            
        elif chunk_type == b'Ctab':
            # Channel table - parse channel assignment
            ctab_length = struct.unpack('>I', cseg_data[pos + 4:pos + 8])[0]
            ctab_data = cseg_data[pos + 8:pos + 8 + ctab_length]
            
            if len(ctab_data) >= 10:
                # First byte appears to be Ctab ID
                # Next 8 bytes are the name (ASCII, space-padded)
                name = ctab_data[1:9].decode('ascii', errors='ignore').rstrip()
                
                # Next byte(s) contain channel assignment
                # Channel is often at position 9 (0-indexed)
                channel = ctab_data[9] if len(ctab_data) > 9 else 0
                
                # Store remaining params
                raw_params = ctab_data[10:] if len(ctab_data) > 10 else b''
                
                ctabs.append(Ctab(
                    name=name,
                    channel=channel,
                    raw_params=raw_params
                ))
            
            pos += 8 + ctab_length
            
        elif chunk_type == b'Cntt':
            # Note transpose table - skip for now
            cntt_length = struct.unpack('>I', cseg_data[pos + 4:pos + 8])[0]
            pos += 8 + cntt_length
            
        else:
            pos += 1
    
    if sections or ctabs:
        return ChordSegment(sections=sections, ctabs=ctabs)
    
    return None


def find_section_pattern(style: Style, section_name: str) -> IntroPattern:
    """
    Find and extract MIDI pattern for a specific section (e.g., "Intro A").
    
    Args:
        style: Parsed Style object
        section_name: Name of the section to find (e.g., "Intro A", "Main A")
        
    Returns:
        IntroPattern containing the MIDI events for that section
    """
    midi = style.midi_data
    ticks_per_beat = midi.ticks_per_beat
    
    # Default values
    tempo = 120  # Default BPM
    time_signature = (4, 4)
    
    # Find tracks that match the section name
    section_tracks = []
    for track_idx, track in enumerate(midi.tracks):
        for msg in track:
            if msg.type == 'track_name' and section_name.lower() in msg.name.lower():
                section_tracks.append(track_idx)
                break
            elif msg.type == 'marker' and section_name.lower() in msg.text.lower():
                section_tracks.append(track_idx)
                break
            elif msg.type == 'text' and section_name.lower() in msg.text.lower():
                section_tracks.append(track_idx)
                break
    
    # If no specific tracks found, use all tracks (except track 0 which is often tempo/meta)
    if not section_tracks:
        section_tracks = list(range(1, len(midi.tracks)))
    
    # Parse note events from relevant tracks
    notes_by_channel: Dict[int, List[NoteEvent]] = {}
    max_time = 0
    
    for track_idx in section_tracks:
        track = midi.tracks[track_idx]
        current_time = 0
        active_notes: Dict[Tuple[int, int], Tuple[int, int]] = {}  # (channel, pitch) -> (start_time, velocity)
        
        for msg in track:
            current_time += msg.time
            
            # Extract tempo
            if msg.type == 'set_tempo':
                tempo = mido.tempo2bpm(msg.tempo)
            
            # Extract time signature
            elif msg.type == 'time_signature':
                time_signature = (msg.numerator, msg.denominator)
            
            # Note on
            elif msg.type == 'note_on' and msg.velocity > 0:
                key = (msg.channel, msg.note)
                active_notes[key] = (current_time, msg.velocity)
            
            # Note off (or note_on with velocity 0)
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                key = (msg.channel, msg.note)
                if key in active_notes:
                    start_time, note_velocity = active_notes.pop(key)
                    duration = current_time - start_time
                    
                    note_event = NoteEvent(
                        time=start_time,
                        pitch=msg.note,
                        velocity=note_velocity,
                        duration=duration,
                        channel=msg.channel
                    )
                    
                    if msg.channel not in notes_by_channel:
                        notes_by_channel[msg.channel] = []
                    notes_by_channel[msg.channel].append(note_event)
                    
                    max_time = max(max_time, current_time)
    
    # If no notes found, try a different approach - parse all tracks
    if not notes_by_channel:
        for track in midi.tracks:
            current_time = 0
            active_notes: Dict[Tuple[int, int], Tuple[int, int]] = {}  # (channel, pitch) -> (start_time, velocity)
            
            for msg in track:
                current_time += msg.time
                
                if msg.type == 'set_tempo':
                    tempo = mido.tempo2bpm(msg.tempo)
                elif msg.type == 'time_signature':
                    time_signature = (msg.numerator, msg.denominator)
                elif msg.type == 'note_on' and msg.velocity > 0:
                    key = (msg.channel, msg.note)
                    active_notes[key] = (current_time, msg.velocity)
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    key = (msg.channel, msg.note)
                    if key in active_notes:
                        start_time, note_velocity = active_notes.pop(key)
                        duration = current_time - start_time
                        
                        note_event = NoteEvent(
                            time=start_time,
                            pitch=msg.note,
                            velocity=note_velocity,
                            duration=duration,
                            channel=msg.channel
                        )
                        
                        if msg.channel not in notes_by_channel:
                            notes_by_channel[msg.channel] = []
                        notes_by_channel[msg.channel].append(note_event)
                        
                        max_time = max(max_time, current_time)
    
    # Determine pattern length (default to 4 bars in 4/4)
    length_ticks = max_time if max_time > 0 else ticks_per_beat * time_signature[0] * 4
    
    return IntroPattern(
        ticks_per_beat=ticks_per_beat,
        length_ticks=length_ticks,
        tempo=int(tempo),
        time_signature=time_signature,
        notes_by_channel=notes_by_channel
    )
