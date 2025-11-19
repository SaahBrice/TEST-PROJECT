# AudioViz MIDI - User Guide

Complete guide to using AudioViz MIDI for audio-to-MIDI conversion and visualization.

## Table of Contents
1. [Getting Started](#getting-started)
2. [User Interface Overview](#user-interface-overview)
3. [Workflow Guide](#workflow-guide)
4. [Advanced Features](#advanced-features)
5. [Tips & Best Practices](#tips--best-practices)
6. [FAQ](#faq)

---

## Getting Started

### First Launch

When you first run AudioViz MIDI, you'll see:
- Menu bar at the top
- Toolbar with quick action buttons
- Central drop area for audio files
- Control panel at the bottom (disabled initially)
- Status bar showing "Ready - Open an audio file to begin"

### Recommended Audio Files

**Best Results:**
- Solo guitar or piano recordings
- Clear, isolated instrument
- Minimal background noise
- Good recording quality (44.1kHz or higher)
- Moderate tempo (60-120 BPM works best)

**Supported Formats:**
- WAV (recommended)
- MP3
- FLAC
- OGG

---

## User Interface Overview

### Menu Bar

**File Menu**
- Open Audio (`Ctrl+O`) - Load audio file
- Export MIDI (`Ctrl+M`) - Save as MIDI file
- Export JSON (`Ctrl+J`) - Save as JSON data
- Exit (`Ctrl+Q`) - Close application

**Edit Menu**
- Settings - Configure application (coming soon)

**View Menu**
- Fullscreen (`F11`) - Toggle fullscreen
- Window size presets (1080p, 1440p, 4K)
- Reset to Default Size (`Ctrl+0`)

**Help Menu**
- Keyboard Shortcuts (`F1`) - View all shortcuts
- About - Application information

### Toolbar

Quick access buttons:
- **Open Audio** - Load file dialog
- **Transcribe** - Start processing
- **Export** - Save MIDI file
- **Help** - Contextual tips

### Visualization Area

Before transcription:
- Drag & drop zone for audio files
- Shows file status after loading

After transcription:
- Piano keyboard on left side
- Horizontal note bars (color-coded by pitch)
- Grid lines for timing and pitch reference
- Red playhead indicator
- Smooth scrolling animation

### Control Panel

**Timeline Slider**
- Shows current time / total duration
- Drag to seek to specific position
- Updates in real-time during playback

**Transport Buttons**
- ▶️ **Play** - Start playback
- ⏸ **Pause** - Pause at current position
- ⏹ **Stop** - Stop and return to start

**Speed Control**
- Dropdown to select playback speed
- Options: 0.5x, 0.75x, 1.0x, 1.25x, 1.5x, 2.0x
- *Note: Speed control limited in current version*

---

## Workflow Guide

### Step-by-Step: Audio to MIDI

#### 1. Load Audio File

**Method A: Drag & Drop**
1. Open file explorer
2. Navigate to your audio file
3. Drag file onto application window
4. Drop when border highlights blue
5. File validates and loads automatically

**Method B: File Dialog**
1. Click "Open Audio" button (or `Ctrl+O`)
2. Browse to your audio file
3. Select file and click "Open"
4. File loads and displays in green state

**What Happens:**
- File format validated
- File size checked (warns if >100MB)
- Green confirmation shows filename
- "Transcribe" button becomes enabled

#### 2. Transcribe Audio

1. Click "Transcribe" button (or `Ctrl+T`)
2. Watch progress bar advance through stages:
   - Loading audio file... (0-20%)
   - Detecting pitch... (20-50%)
   - Detecting note onsets... (50-65%)
   - Converting to MIDI... (65-80%)
   - Improving note quality... (80-95%)
   - Finalizing... (95-100%)

3. Wait for completion dialog
   - Shows number of notes detected
   - Shows duration
   - Confirms you can now export

**Processing Time:**
- 1 minute audio ≈ 8 seconds
- 3 minute audio ≈ 22 seconds
- 5 minute audio ≈ 35 seconds

**During Processing:**
- Window remains responsive
- You can see progress updates
- Cannot start new transcription
- Can still move/resize window

#### 3. Review Results

**Piano Roll Display:**
- Notes appear as colored horizontal bars
- Vertical position = pitch (higher = higher pitch)
- Horizontal length = duration
- Color = pitch class (C=red, D=orange, E=yellow, etc.)
- Piano keyboard on left shows note names

**Playback Controls:**
- All controls now enabled
- Timeline shows total duration
- Ready to play back audio with visualization

#### 4. Playback & Review

**Play Audio:**
1. Press `Space` or click ▶️ Play
2. Watch notes scroll across screen
3. Active notes glow brighter
4. Timeline updates in real-time

**Navigation:**
- `Left Arrow` - Jump back 5 seconds
- `Right Arrow` - Jump forward 5 seconds
- Click timeline to jump to position
- Drag timeline while paused for precise positioning

**Control Playback:**
- `Space` - Toggle play/pause
- `Escape` - Stop and return to start
- Speed dropdown - Adjust playback rate (partially functional)

#### 5. Export Results

**Export MIDI File:**
1. Click "Export MIDI" or press `Ctrl+M`
2. Choose save location
3. Edit filename if desired (defaults to `[original]_midi.mid`)
4. Click "Save"
5. Confirmation dialog appears

**Export JSON File:**
1. Click "Export JSON" or press `Ctrl+J`
2. Choose save location
3. Edit filename if desired (defaults to `[original]_notes.json`)
4. Click "Save"
5. Confirmation dialog appears

**Export Locations:**
- Default: `exports/` folder in application directory
- Can save to any location with write permissions
- Warns if file already exists (asks to overwrite)

---

## Advanced Features

### Keyboard Shortcuts

**Master the workflow with shortcuts:**

Complete list press `F1` in application.

**Pro Tips:**
- `Space` is your friend - quickest play/pause
- Arrow keys for quick navigation
- `Ctrl+T` starts transcription instantly
- `Ctrl+E` for quick MIDI export

### Configuration Options

Edit `config.json` for advanced control:

**Audio Settings:**
"audio": {
"sample_rate": 22050, // Lower = faster, higher = more accurate
"hop_length": 512, // Frame size for analysis
"normalize": true // Auto-normalize volume
}


**Pitch Detection:**
"pitch_detection": {
"algorithm": "piptrack", // or "pyin" for better accuracy
"fmin": 65.0, // Lowest frequency (C2)
"fmax": 2093.0, // Highest frequency (C7)
"threshold": 0.1 // Lower = more sensitive
}


**Visualization:**
"visualization": {
"color_scheme": "chromatic", // or "octave", "velocity"
"fps": 60, // Frame rate (30-60)
"show_grid": true,
"show_keyboard": true
}


---

## Tips & Best Practices

### For Best Results

**Recording Quality:**
- Use high sample rate (44.1kHz+)
- Record in quiet environment
- Single, clear instrument
- Moderate volume levels
- Avoid distortion

**Audio Preparation:**
- Convert to WAV if possible
- Trim silence from start/end
- Normalize volume
- Remove background noise
- Keep under 5 minutes for faster processing

**Troubleshooting Poor Results:**
- Increase `threshold` in config (0.15-0.20)
- Try `"algorithm": "pyin"` for more accuracy
- Ensure audio is clear and isolated
- Check that instrument is in pitch range

### Workflow Optimization

**Speed Up Processing:**
- Process shorter clips
- Close other applications
- Use WAV files (faster to load)
- Lower `sample_rate` to 16000 (if quality ok)

**Better Visualization:**
- Use fullscreen (`F11`) for recording
- Adjust window to desired resolution first
- Set `fps` to match video frame rate
- Use `color_scheme` that fits your style

---

## FAQ

### Q: How accurate is the transcription?
**A:** Accuracy depends on audio quality:
- Clean, solo recordings: 85-95% accuracy
- Complex arrangements: 60-80% accuracy
- Poor quality audio: 40-60% accuracy

### Q: Can it handle multiple instruments?
**A:** Current version (0.1.0) is optimized for single instruments. Polyphonic support planned for v0.2.

### Q: What's the difference between MIDI and JSON export?
**A:**
- **MIDI (.mid)**: Standard format, use in DAWs, music software
- **JSON (.json)**: Human-readable, includes metadata, for data analysis

### Q: Can I edit the MIDI after transcription?
**A:** Not within AudioViz MIDI currently. Export MIDI and edit in a DAW like FL Studio, Ableton, or Logic Pro.

### Q: Why does processing take so long?
**A:** Audio analysis is computationally intensive. Longer files and higher quality settings increase processing time.

### Q: Can I use this commercially?
**A:** Yes, AudioViz MIDI is MIT licensed. Free for personal and commercial use.

### Q: My audio won't load, what do I do?
**A:** Check:
1. File format is supported (WAV, MP3, FLAC, OGG)
2. File isn't corrupted (try playing in media player)
3. File has correct permissions
4. Try converting to WAV format

### Q: The visualization is laggy, how to fix?
**A:** Try:
1. Lower `fps` to 30 in config
2. Close other applications
3. Use smaller window size
4. Process shorter audio clips

### Q: Can I record live input?
**A:** Not in v0.1.0. Real-time recording planned for v0.2.

---

## Need More Help?

- Check `logs/` folder for detailed error information
- Run tests: `python tests/test_smoke.py`
- Report issues on GitHub
- Email support: your.email@example.com



## For Developers

- Module documentation in code docstrings
- Run `pydoc` to generate API docs
- See test files for usage examples

**Happy transcribing! 🎵**