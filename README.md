# Yamaha Style File (SFF1) Parser and Intro Renderer

A Python-based tool for parsing Yamaha SFF1 style files and rendering intro sections to MIDI with custom chord transformations.

## Features

- Parse Yamaha SFF1 style files (.sty, .prs)
- Extract CASM (Chord and Section Management) information
- **Preserve instrument voices** with Program Change and Bank Select support
- **Maintain channel settings** including Volume, Pan, Reverb, and Chorus
- Render intro sections to MIDI files
- Transform notes to different chords with voice leading
- **Interactive mode** with step-by-step Korean/English prompts
- Command-line interface for scripting and automation

## Installation

1. Clone this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Interactive Mode (Recommended)

Simply run the program without any arguments for a step-by-step interactive experience:

```bash
python intro_renderer.py
```

The program will guide you through:
1. Selecting the style file
2. Choosing the section to render (Intro A, Intro B, etc.)
3. Specifying the chord root (C, D, E, F, G, A, B, with sharps/flats)
4. Selecting major or minor quality
5. Setting the output file name

All prompts are displayed in both Korean and English for accessibility.

### Command-line Mode

For automation or scripting, you can provide all parameters as command-line arguments:

```bash
python intro_renderer.py --style mystyle.sty --section "Intro A" --chord C --quality major --out intro_C.mid
```

### Command-line Options

- `--style`: Path to Yamaha style file (.sty or .prs)
- `--section`: Section name to render (e.g., "Intro A", "Intro B", "Intro C")
- `--chord`: Chord root note (e.g., C, F#, Eb, A)
- `--quality`: Chord quality - either "major" or "minor"
- `--out`: Output MIDI file path

### Examples

```bash
# Interactive mode - easiest for beginners
python intro_renderer.py

# Render Intro A in C major
python intro_renderer.py --style PubPiano.S549.sty --section "Intro A" --chord C --quality major --out intro_C.mid

# Render Intro B in A minor
python intro_renderer.py --style mystyle.sty --section "Intro B" --chord A --quality minor --out intro_Am.mid

# Render Intro A in Eb major
python intro_renderer.py --style mystyle.sty --section "Intro A" --chord Eb --quality major --out intro_Eb.mid

# Render Intro C in F# minor
python intro_renderer.py --style mystyle.sty --section "Intro C" --chord "F#" --quality minor --out intro_F#m.mid
```

## Architecture

The project consists of three main modules:

### style_parser.py

Handles parsing of Yamaha SFF1 style files:
- `read_style_file()`: Reads and parses a style file
- `parse_casm()`: Parses CASM (Chord and Section Management) chunks
- `find_section_pattern()`: Extracts MIDI patterns for specific sections
- **Captures Program Change and Bank Select events** for instrument voices
- **Extracts control changes** (Volume, Pan, Reverb, Chorus) from original style

### chord_engine.py

Manages chord transformations and voice leading:
- `parse_chord()`: Parses chord symbols
- `build_chord_tones()`: Generates chord tones for a given chord
- `transform_notes_for_chord()`: Transforms notes with voice leading

### intro_renderer.py

Main application that ties everything together:
- `render_intro()`: Renders intro sections to MIDI files
- **Applies Program Change, Bank Select, and control changes** to output MIDI
- CLI interface for user interaction

## Technical Details

### SFF1 File Format

Yamaha SFF1 files are based on Standard MIDI File (SMF) format with additional chunks:
- **CASM**: Chord and Section Management chunk containing:
  - **CSEG**: Chord Segments
  - **Sdec**: Section declarations (e.g., "Intro A", "Main A")
  - **Ctab**: Channel tables (instrument assignments)
  - **Cntt**: Note transpose tables

### Instrument and Voice Handling

The parser now properly handles Yamaha-specific voice selection:
- **Program Change**: Selects the instrument/voice (0-127)
- **Bank Select MSB** (CC#0): Selects the bank group (0=GM, 63=Yamaha Preset, etc.)
- **Bank Select LSB** (CC#32): Selects the bank variation within the group
- **Control Changes**: Volume (CC#7), Pan (CC#10), Reverb (CC#91), Chorus (CC#93)

This ensures that rendered MIDI files sound like the original Yamaha styles with correct instruments and effects.

### Voice Leading Algorithm

The voice leading algorithm:
1. Identifies chord tones in the target chord
2. Maps each note to the nearest chord tone
3. Considers previous voicing to minimize voice movement
4. Maintains notes within a specified range (A2 to F4 by default)

## Limitations (Version 1.0)

- Only supports major and minor chords (no 7th, sus, dim, etc.)
- Processes one intro section at a time
- No real-time playback (offline MIDI generation only)
- Basic voice leading (will be enhanced in future versions)

## Future Enhancements

- Support for extended chords (7th, 9th, sus, dim, aug)
- Chord progression support (multiple measures with different chords)
- Main sections, fills, and endings
- Real-time MIDI playback
- More sophisticated voice leading algorithms
- GUI interface (optional)

## Accessibility

This tool is designed to be fully accessible via command-line interface and screen readers. All output is text-based and suitable for visually impaired users.

## License

See LICENSE file for details.
