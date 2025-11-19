# AudioViz MIDI - Test Suite

## Running Tests

### Quick Smoke Test
Tests basic imports and functionality: python tests/test_smoke.py


### Full Integration Test
Tests complete end-to-end workflow: python tests/test_integration.py



### Individual Module Tests
Run specific test files from previous phases: 

python test_audio_loader.py
python test_pitch_detector.py
python test_onset_detector.py
python test_midi_data_model.py
python test_midi_converter.py
python test_note_quantizer.py



## Test Coverage

- ✅ Audio loading (WAV, MP3, FLAC, OGG)
- ✅ Pitch detection (piptrack algorithm)
- ✅ Onset detection
- ✅ MIDI conversion
- ✅ Note quantization
- ✅ MIDI file export
- ✅ JSON export
- ✅ Module imports
- ✅ Data structures

## Expected Results

All tests should pass with `✅ PASS` status.

If tests fail, check:
1. All dependencies installed (`pip install -r requirements.txt`)
2. All modules in correct directories
3. Python version 3.9+
4. Log files in `logs/` directory for detailed errors

