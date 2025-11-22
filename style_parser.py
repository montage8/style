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
class ChannelInfo:
    """Represents channel configuration from style file"""
    channel: int  # MIDI channel (0-15)
    bank_msb: Optional[int] = None  # Bank Select MSB (CC#0)
    bank_lsb: Optional[int] = None  # Bank Select LSB (CC#32)
    program: Optional[int] = None  # Program Change (0-127)
    volume: Optional[int] = None  # Volume (CC#7)
    pan: Optional[int] = None  # Pan (CC#10)
    reverb: Optional[int] = None  # Reverb (CC#91)
    chorus: Optional[int] = None  # Chorus (CC#93)
    part_name: Optional[str] = None  # Part name from Ctab (e.g., "Bass", "Chord")
    
    def is_bass_channel(self) -> bool:
        """Check if this is a bass channel"""
        # Check by part name first
        if self.part_name:
            return 'bass' in self.part_name.lower()
        
        # Fallback: check by GM program number
        # GM programs 32-39 are bass instruments
        if self.program is not None and 32 <= self.program <= 39:
            return True
        
        return False


@dataclass
class Ctab:
    """Represents a Ctab (Channel Table) entry in CASM"""
    name: str
    channel: int
    ntr: int = 0  # Note Transposition Rule (0=Root Trans, 1=Root Fixed, 2=Guitar, etc.)
    ntt: int = 0  # Note Transposition Table index
    bass_ntt: int = 0  # Bass Note Transposition Table
    source_root: int = 0  # Source root note (0=C, 1=C#, etc.)
    source_chord: int = 0  # Source chord type
    high_key: int = 127  # High key limit
    note_low: int = 0  # Note low limit
    note_high: int = 127  # Note high limit
    retrigger_rule: int = 0  # Retrigger rule
    raw_params: bytes = b''  # Raw parameter bytes for debugging
    
    def __repr__(self):
        return f"Ctab(name='{self.name}', ch={self.channel}, NTR={self.ntr}, NTT={self.ntt})"


@dataclass
class Cntt:
    """Represents a Cntt (Chord Note Transposition Table) entry in CASM"""
    table_data: bytes  # Raw table data (note mappings for different chord types)
    
    def __repr__(self):
        return f"Cntt(size={len(self.table_data)})"


@dataclass
class ChordSegment:
    """Represents a CSEG (Chord Segment) in CASM"""
    sections: List[str]  # List of section names from Sdec
    ctabs: List[Ctab]
    cntts: List[Cntt] = None  # Note transposition tables
    range_type: str = "single"  # "single" for SFF1, "low"/"mid"/"high" for SFF2
    
    def __post_init__(self):
        if self.cntts is None:
            self.cntts = []
    
    def __repr__(self):
        return f"ChordSegment(sections={self.sections}, ctabs={len(self.ctabs)}, cntts={len(self.cntts)}, range={self.range_type})"


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
    channel_info: Dict[int, ChannelInfo]  # channel -> channel configuration
    
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
    format_version: str = "SFF1"  # "SFF1" or "SFF2"
    
    def __repr__(self):
        return f"Style({self.format_version}, tracks={len(self.midi_data.tracks)}, cseg={len(self.chord_segments)})"


def detect_sff_version(style_bytes: bytes) -> str:
    """
    Detect whether the style file is SFF1 or SFF2.
    
    Args:
        style_bytes: Raw bytes of the style file
        
    Returns:
        "SFF1" or "SFF2"
    """
    # Check for SFF2 markers
    if b'SFF2' in style_bytes[:1000] or b'SFF GE' in style_bytes[:1000]:
        return "SFF2"
    
    # Check for SFF1 marker
    if b'SFF1' in style_bytes[:1000]:
        return "SFF1"
    
    # Default to SFF1 for older files without explicit markers
    return "SFF1"


def read_style_file(path: str) -> Style:
    """
    Read and parse a Yamaha SFF1/SFF2 style file.
    
    Args:
        path: Path to the .sty or .prs file
        
    Returns:
        Style object containing parsed data
    """
    with open(path, 'rb') as f:
        raw_bytes = f.read()
    
    # Detect format version
    format_version = detect_sff_version(raw_bytes)
    
    # Parse MIDI data
    try:
        midi_data = mido.MidiFile(path)
    except Exception as e:
        raise ValueError(f"Failed to parse MIDI data: {e}")
    
    # Parse CASM chunks
    chord_segments = parse_casm(raw_bytes, format_version)
    
    return Style(
        raw_bytes=raw_bytes,
        midi_data=midi_data,
        chord_segments=chord_segments,
        format_version=format_version
    )


def parse_casm(style_bytes: bytes, format_version: str = "SFF1") -> List[ChordSegment]:
    """
    Parse CASM (Chord and Section Management) chunk from style file.
    
    Args:
        style_bytes: Raw bytes of the style file
        format_version: "SFF1" or "SFF2"
        
    Returns:
        List of ChordSegment objects
    
    Note:
        SFF2 files may have multiple CASM segments for low/mid/high ranges.
        Currently treats all as single-range for compatibility.
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
    cseg_count = 0
    while pos < len(casm_data) - 4:
        # Look for CSEG marker
        if casm_data[pos:pos + 4] == b'CSEG':
            cseg_length = struct.unpack('>I', casm_data[pos + 4:pos + 8])[0]
            cseg_data = casm_data[pos + 8:pos + 8 + cseg_length]
            
            # Determine range type for SFF2 (low/mid/high)
            range_type = "single"
            if format_version == "SFF2":
                # SFF2 has up to 3 CSEGs for low/mid/high ranges
                if cseg_count == 0:
                    range_type = "low"
                elif cseg_count == 1:
                    range_type = "mid"
                elif cseg_count == 2:
                    range_type = "high"
            
            # Parse this CSEG
            cseg = parse_cseg(cseg_data, range_type)
            if cseg:
                chord_segments.append(cseg)
            
            cseg_count += 1
            pos += 8 + cseg_length
        else:
            pos += 1
    
    return chord_segments


def parse_cseg(cseg_data: bytes, range_type: str = "single") -> Optional[ChordSegment]:
    """
    Parse a single CSEG (Chord Segment).
    
    Args:
        cseg_data: Raw bytes of the CSEG chunk
        
    Returns:
        ChordSegment object or None
    """
    sections = []
    ctabs = []
    cntts = []
    
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
            # Channel table - parse channel assignment and CASM parameters
            ctab_length = struct.unpack('>I', cseg_data[pos + 4:pos + 8])[0]
            ctab_data = cseg_data[pos + 8:pos + 8 + ctab_length]
            
            if len(ctab_data) >= 10:
                # Byte 0: Ctab ID
                ctab_id = ctab_data[0]
                
                # Bytes 1-8: Name (ASCII, space-padded)
                name = ctab_data[1:9].decode('ascii', errors='ignore').rstrip()
                
                # Byte 9: Source Channel (MIDI channel 1-16, stored as 0-15)
                source_channel = ctab_data[9] if len(ctab_data) > 9 else 0
                
                # Parse CASM parameters (based on Jørgen Sørensen's documentation)
                # These offsets may vary by SFF version, but this is the common structure
                ntr = ctab_data[10] if len(ctab_data) > 10 else 0  # Note Transposition Rule
                ntt = ctab_data[11] if len(ctab_data) > 11 else 0  # Note Transposition Table
                bass_ntt = ctab_data[12] if len(ctab_data) > 12 else 0  # Bass NTT
                source_root = ctab_data[13] if len(ctab_data) > 13 else 0  # Source root (C=0)
                source_chord = ctab_data[14] if len(ctab_data) > 14 else 0  # Source chord type
                high_key = ctab_data[15] if len(ctab_data) > 15 else 127  # High key limit
                note_low = ctab_data[16] if len(ctab_data) > 16 else 0  # Note low limit
                note_high = ctab_data[17] if len(ctab_data) > 17 else 127  # Note high limit
                retrigger_rule = ctab_data[18] if len(ctab_data) > 18 else 0  # Retrigger rule
                
                # Store remaining bytes for future use (Cntt references, etc.)
                raw_params = ctab_data[19:] if len(ctab_data) > 19 else b''
                
                ctabs.append(Ctab(
                    name=name,
                    channel=source_channel,
                    ntr=ntr,
                    ntt=ntt,
                    bass_ntt=bass_ntt,
                    source_root=source_root,
                    source_chord=source_chord,
                    high_key=high_key,
                    note_low=note_low,
                    note_high=note_high,
                    retrigger_rule=retrigger_rule,
                    raw_params=raw_params
                ))
            
            pos += 8 + ctab_length
            
        elif chunk_type == b'Cntt':
            # Note transpose table - parse the transposition table
            cntt_length = struct.unpack('>I', cseg_data[pos + 4:pos + 8])[0]
            cntt_data = cseg_data[pos + 8:pos + 8 + cntt_length]
            
            # Store the full table data for interpretation
            cntts.append(Cntt(table_data=cntt_data))
            
            pos += 8 + cntt_length
            
        else:
            pos += 1
    
    if sections or ctabs:
        return ChordSegment(sections=sections, ctabs=ctabs, cntts=cntts, range_type=range_type)
    
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
    
    # Find tracks that match the section name EXACTLY
    section_tracks = []
    section_name_lower = section_name.lower().strip()
    
    for track_idx, track in enumerate(midi.tracks):
        for msg in track:
            # Check for exact match in track name, marker, or text
            if msg.type == 'track_name':
                track_name = msg.name.lower().strip()
                # Exact match or "Intro A" in "Intro A - Piano" format
                if track_name == section_name_lower or track_name.startswith(section_name_lower + ' ') or track_name.startswith(section_name_lower + '-'):
                    section_tracks.append(track_idx)
                    break
            elif msg.type == 'marker':
                marker_text = msg.text.lower().strip()
                if marker_text == section_name_lower:
                    section_tracks.append(track_idx)
                    break
            elif msg.type == 'text':
                text_content = msg.text.lower().strip()
                if text_content == section_name_lower:
                    section_tracks.append(track_idx)
                    break
    
    # If no specific tracks found, try to find by checking CASM sections
    if not section_tracks and style.chord_segments:
        # Look for the section in CASM chord segments
        for cseg in style.chord_segments:
            if section_name in cseg.sections:
                # If found in CASM but no matching track, use all tracks
                section_tracks = list(range(1, len(midi.tracks)))
                break
    
    # Last resort: if still no tracks found, use all tracks (except track 0)
    if not section_tracks:
        section_tracks = list(range(1, len(midi.tracks)))
    
    # Parse note events and channel info from relevant tracks
    notes_by_channel: Dict[int, List[NoteEvent]] = {}
    channel_info: Dict[int, ChannelInfo] = {}
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
            
            # Capture program change
            elif msg.type == 'program_change':
                if msg.channel not in channel_info:
                    channel_info[msg.channel] = ChannelInfo(channel=msg.channel)
                channel_info[msg.channel].program = msg.program
            
            # Capture control changes (Bank Select MSB/LSB, Volume, Pan, etc.)
            elif msg.type == 'control_change':
                if msg.channel not in channel_info:
                    channel_info[msg.channel] = ChannelInfo(channel=msg.channel)
                
                if msg.control == 0:  # Bank Select MSB
                    channel_info[msg.channel].bank_msb = msg.value
                elif msg.control == 32:  # Bank Select LSB
                    channel_info[msg.channel].bank_lsb = msg.value
                elif msg.control == 7:  # Volume
                    channel_info[msg.channel].volume = msg.value
                elif msg.control == 10:  # Pan
                    channel_info[msg.channel].pan = msg.value
                elif msg.control == 91:  # Reverb
                    channel_info[msg.channel].reverb = msg.value
                elif msg.control == 93:  # Chorus
                    channel_info[msg.channel].chorus = msg.value
            
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
                # Capture program change
                elif msg.type == 'program_change':
                    if msg.channel not in channel_info:
                        channel_info[msg.channel] = ChannelInfo(channel=msg.channel)
                    channel_info[msg.channel].program = msg.program
                # Capture control changes
                elif msg.type == 'control_change':
                    if msg.channel not in channel_info:
                        channel_info[msg.channel] = ChannelInfo(channel=msg.channel)
                    
                    if msg.control == 0:  # Bank Select MSB
                        channel_info[msg.channel].bank_msb = msg.value
                    elif msg.control == 32:  # Bank Select LSB
                        channel_info[msg.channel].bank_lsb = msg.value
                    elif msg.control == 7:  # Volume
                        channel_info[msg.channel].volume = msg.value
                    elif msg.control == 10:  # Pan
                        channel_info[msg.channel].pan = msg.value
                    elif msg.control == 91:  # Reverb
                        channel_info[msg.channel].reverb = msg.value
                    elif msg.control == 93:  # Chorus
                        channel_info[msg.channel].chorus = msg.value
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
    
    # Populate part names from CASM Ctab data if available
    if style.chord_segments:
        for cseg in style.chord_segments:
            # Check if this CSEG applies to the requested section
            if section_name in cseg.sections:
                for ctab in cseg.ctabs:
                    if ctab.channel in channel_info:
                        channel_info[ctab.channel].part_name = ctab.name
                    elif ctab.channel in notes_by_channel:
                        # Create channel info if we have notes but no info yet
                        channel_info[ctab.channel] = ChannelInfo(
                            channel=ctab.channel,
                            part_name=ctab.name
                        )
    
    # Determine pattern length (default to 4 bars in 4/4)
    length_ticks = max_time if max_time > 0 else ticks_per_beat * time_signature[0] * 4
    
    return IntroPattern(
        ticks_per_beat=ticks_per_beat,
        length_ticks=length_ticks,
        tempo=int(tempo),
        time_signature=time_signature,
        notes_by_channel=notes_by_channel,
        channel_info=channel_info
    )
