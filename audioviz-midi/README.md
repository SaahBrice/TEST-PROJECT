# AudioViz MIDI

Guitar/Piano Audio → MIDI transcription and visualization desktop app (Python).  
Creates synchronized piano-roll visualizations for screen recording and exports MIDI/JSON for DAWs and editors.

Badges: Platform: Windows / macOS / Linux · Python 3.9+ · Status: MVP

Table of Contents
- Executive Summary
- Features
- Quickstart
- Installation
- Usage
- Architecture & Modules
- File Structure
- Export Formats
- UI & Visualization
- Performance Targets
- Roadmap
- Testing
- Contributing
- License

## Executive Summary
AudioViz MIDI transcribes monophonic guitar and piano audio into MIDI and renders a high-quality, customizable piano-roll visualization suitable for YouTube screen recordings. It runs fully locally (no cloud), supports WAV/MP3/FLAC/OGG and exports standard MIDI and JSON note timelines.

## Key Features
- Audio upload (WAV, MP3, FLAC, OGG) via dialog or drag & drop
- Automatic preprocessing (mono, resample 22050 Hz, normalize)
- Monophonic pitch detection and onset detection (pyin / piptrack selectable)
- Piano-roll visualization with keyboard reference, grid, waveform overlay
- Playback controls: play, pause, stop, seek, speed, loop
- Exports: Standard MIDI (.mid) and pretty-printed JSON (timestamped notes)
- Customizable color schemes, window presets for 1080p/1440p/4K
- Cross-platform: Windows, macOS, Linux

## Quickstart
1. Clone repo:
    git clone https://github.com/<your-org>/audioviz-midi.git
2. Enter project:
    cd audioviz-midi
3. Create venv and install:
    python -m venv .venv
    source .venv/bin/activate   # macOS / Linux
    .venv\Scripts\activate      # Windows
    pip install -r requirements.txt
4. Run:
    python -m audioviz_midi.main

(Adjust main entry if your project uses a different script)

## Installation (Dependencies)
Requires Python 3.9+. Recommended use of virtualenv/venv.

Core libraries:
- PyQt5 (GUI)
- pygame (visualization & playback)
- librosa, numpy, scipy (audio analysis)
- soundfile (audio I/O)
- pydub (format conversions)
- pretty-midi, mido (MIDI handling)
- Pillow (image utilities)

Install:
pip install -r requirements.txt

## Usage Overview
- Open app → Upload or drag audio file
- Wait for preprocessing and transcription
- Inspect piano roll; play/pause/seek
- Choose color scheme, adjust visualization settings
- Export → choose MIDI (.mid) or JSON (.json)

Exported JSON includes source metadata, per-note timestamp (s), MIDI number, note name, duration (s), velocity, and detected frequency.

## System Architecture (concise)
Layered design:
- Presentation: PyQt5 GUI
- Business Logic: app coordinators, state management
- Audio Processing: librosa-based loaders, pitch & onset detectors
- MIDI Management: conversion, quantization, data models
- Visualization: pygame renderers (piano-roll)
- Playback: mixer controller, synchronization

Design patterns: MVC, Observer (playback events), Strategy (swappable analysis algorithms), Factory (renderers).

## Module Summary
- main — app entry, config & logging
- gui/ — MainWindow, ControlPanel, SettingsDialog
- audio/ — loader.py, pitch_detector.py, onset_detector.py
- midi/ — converter.py, midi_model.py, quantizer.py
- visualization/ — manager.py, piano_roll_renderer.py, themes.py
- playback/ — controller.py
- export/ — midi_exporter.py, json_exporter.py
- utils/ — helpers, constants, logging
- tests/ — unit & integration tests

## File Structure (example)
audioviz-midi/
├─ audioviz_midi/
│  ├─ main.py
│  ├─ gui/
│  ├─ audio/
│  ├─ midi/
│  ├─ visualization/
│  ├─ playback/
│  ├─ export/
│  └─ utils/
├─ requirements.txt
├─ README.md
├─ LICENSE
└─ tests/

## Visualization & UI
- Piano-roll with horizontal time axis and vertical pitch axis
- Playhead, piano keyboard reference, beat/measure grid lines
- Color schemes: chromatic, octave, velocity, rainbow, custom pickers
- Resizable window and presets for common recording resolutions
- Target synchronization accuracy: ≤ 20 ms

Visualization optimizations:
- Only render visible notes
- Precompute note geometry on export
- Frame target: 60 FPS (min 30 FPS)

## Exports
MIDI:
- Format 1 compatible with DAWs
- Note On/Off events with velocities, tempo metadata (default 120 BPM if unknown)
- Instrument default: Acoustic Grand Piano (Program 0)

JSON:
- Pretty-printed UTF-8 with metadata and notes array
- Millisecond timestamp precision
- Example note object:
  {
     "time": 12.345,
     "note": "C4",
     "midi": 60,
     "duration": 0.75,
     "velocity": 95,
     "frequency": 261.63
  }

## Performance Targets
- Audio load: ~2s for typical 3min / 5MB
- Pitch detection: ≤ 30s for 3min
- Full pipeline: ≤ 45s typical
- Memory: ≤ 500MB typical
- CPU: < 50% during playback on recommended hardware

## Roadmap
Planned enhancements:
- Phase 2: Polyphonic transcription, real-time microphone input, manual note editing, new visualizers
- Phase 3: Sheet music export, plugin renderer system, batch processing
- Long-term: ML-driven transcription improvements, DAW plugin integrations, mobile companions

## Testing
- Unit tests: audio loader, pitch/onset detectors, MIDI converter
- Integration tests: upload → transcription → export
- Performance benchmarks and cross-platform compatibility tests
Run tests:
pytest tests/

## Contributing
- Fork → create feature branch → open PR
- Follow style, add tests for new behavior
- Update CHANGELOG and docs for breaking changes

## Support & Maintenance
- Issues tracked in GitHub Issues with severity tags
- Semantic versioning for releases
- Documentation and video tutorials to be maintained in docs/ and examples/

## License
MIT License — see LICENSE file.

---

For developer setup notes, sample config, CI, and contribution guidelines, add docs/ and a CODE_OF_CONDUCT.md as needed.
