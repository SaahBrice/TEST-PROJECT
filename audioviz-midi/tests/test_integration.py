# tests/test_integration.py
"""
Integration tests for AudioViz MIDI.
Tests the complete end-to-end workflow.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audio import AudioLoader, PitchDetector, OnsetDetector
from midi import MIDIConverter, NoteQuantizer, MIDIData, Note
from export import MIDIExporter, JSONExporter
from utils import setup_logging, ConfigManager
import numpy as np
import soundfile as sf

logger = setup_logging()


def create_test_audio():
    """Create test audio file for testing."""
    logger.info("Creating test audio...")
    
    sample_rate = 22050
    duration = 3.0
    frequencies = [261.63, 293.66, 329.63, 349.23, 392.00]  # C-D-E-F-G
    
    segments = []
    for freq in frequencies:
        t = np.linspace(0, 0.5, int(sample_rate * 0.5))
        envelope = np.exp(-2 * t / 0.5)
        note = 0.5 * envelope * np.sin(2 * np.pi * freq * t)
        segments.append(note)
        
        silence = np.zeros(int(sample_rate * 0.1))
        segments.append(silence)
    
    audio = np.concatenate(segments).astype(np.float32)
    sf.write('test_audio_integration.wav', audio, sample_rate)
    
    logger.info("Test audio created: test_audio_integration.wav")
    return 'test_audio_integration.wav'


def test_audio_loading():
    """Test audio loading functionality."""
    logger.info("\n" + "="*60)
    logger.info("TEST: Audio Loading")
    logger.info("="*60)
    
    try:
        loader = AudioLoader()
        audio_file = create_test_audio()
        
        # Test validation
        is_valid, message = loader.validate_file(audio_file)
        assert is_valid, f"File validation failed: {message}"
        logger.info("✓ File validation passed")
        
        # Test loading
        audio_data, sample_rate = loader.load_audio(audio_file)
        assert audio_data is not None, "Audio data is None"
        assert sample_rate == 22050, f"Wrong sample rate: {sample_rate}"
        assert len(audio_data) > 0, "Audio data is empty"
        logger.info(f"✓ Audio loaded: {len(audio_data)} samples at {sample_rate} Hz")
        
        # Test info
        info = loader.get_audio_info()
        assert info['duration'] > 0, "Duration is zero"
        logger.info(f"✓ Audio info: {info['duration']:.2f}s duration")
        
        logger.info("✅ Audio Loading Test PASSED")
        return True, audio_file, audio_data, sample_rate
        
    except Exception as e:
        logger.error(f"❌ Audio Loading Test FAILED: {e}")
        return False, None, None, None


def test_pitch_detection(audio_data, sample_rate):
    """Test pitch detection functionality."""
    logger.info("\n" + "="*60)
    logger.info("TEST: Pitch Detection")
    logger.info("="*60)
    
    try:
        detector = PitchDetector()
        
        # Test detection
        frequencies, confidences, times = detector.detect_pitch(audio_data, sample_rate)
        assert len(frequencies) > 0, "No frequencies detected"
        assert len(confidences) > 0, "No confidences returned"
        assert len(times) > 0, "No times returned"
        logger.info(f"✓ Pitch detection: {len(frequencies)} frames analyzed")
        
        # Test statistics
        stats = detector.get_detection_stats()
        assert stats['total_frames'] > 0, "No frames processed"
        assert stats['frames_with_pitch'] > 0, "No pitches detected"
        logger.info(f"✓ Statistics: {stats['frames_with_pitch']} frames with pitch")
        logger.info(f"✓ Pitch coverage: {stats['pitch_coverage']:.1%}")
        
        # Test frequency to note conversion
        note_name = PitchDetector.frequency_to_note_name(440.0)
        assert note_name == 'A4', f"Wrong note name: {note_name}"
        logger.info("✓ Frequency conversion working")
        
        logger.info("✅ Pitch Detection Test PASSED")
        return True, frequencies, confidences, times
        
    except Exception as e:
        logger.error(f"❌ Pitch Detection Test FAILED: {e}")
        return False, None, None, None


def test_onset_detection(audio_data, sample_rate):
    """Test onset detection functionality."""
    logger.info("\n" + "="*60)
    logger.info("TEST: Onset Detection")
    logger.info("="*60)
    
    try:
        detector = OnsetDetector()
        
        # Test detection
        onset_times, onset_strength = detector.detect_onsets(audio_data, sample_rate)
        assert len(onset_times) > 0, "No onsets detected"
        logger.info(f"✓ Onset detection: {len(onset_times)} onsets found")
        
        # Test statistics
        stats = detector.get_detection_stats()
        assert stats['total_onsets'] > 0, "No onsets in stats"
        logger.info(f"✓ Statistics: {stats['total_onsets']} onsets")
        
        # Test intervals
        duration = len(audio_data) / sample_rate
        intervals = detector.get_onset_intervals(duration)
        assert len(intervals) > 0, "No intervals created"
        logger.info(f"✓ Intervals: {len(intervals)} note segments")
        
        logger.info("✅ Onset Detection Test PASSED")
        return True, onset_times
        
    except Exception as e:
        logger.error(f"❌ Onset Detection Test FAILED: {e}")
        return False, None


def test_midi_conversion(frequencies, confidences, times, onset_times):
    """Test MIDI conversion functionality."""
    logger.info("\n" + "="*60)
    logger.info("TEST: MIDI Conversion")
    logger.info("="*60)
    
    try:
        converter = MIDIConverter()
        
        # Test conversion with onsets
        midi_data = converter.convert_to_midi(frequencies, confidences, times, onset_times)
        assert midi_data is not None, "MIDI data is None"
        assert len(midi_data) > 0, "No notes created"
        logger.info(f"✓ MIDI conversion: {len(midi_data)} notes created")
        
        # Test statistics
        stats = midi_data.get_statistics()
        assert stats['total_notes'] > 0, "No notes in stats"
        assert stats['duration'] > 0, "Duration is zero"
        logger.info(f"✓ Statistics: {stats['total_notes']} notes, {stats['duration']:.2f}s")
        logger.info(f"✓ Pitch range: {stats['pitch_range']}")
        
        # Test note structure
        notes = midi_data.get_notes()
        first_note = notes[0]
        assert hasattr(first_note, 'pitch'), "Note missing pitch"
        assert hasattr(first_note, 'start_time'), "Note missing start_time"
        assert hasattr(first_note, 'velocity'), "Note missing velocity"
        logger.info("✓ Note structure valid")
        
        logger.info("✅ MIDI Conversion Test PASSED")
        return True, midi_data
        
    except Exception as e:
        logger.error(f"❌ MIDI Conversion Test FAILED: {e}")
        return False, None


def test_quantization(midi_data):
    """Test note quantization functionality."""
    logger.info("\n" + "="*60)
    logger.info("TEST: Note Quantization")
    logger.info("="*60)
    
    try:
        quantizer = NoteQuantizer()
        
        # Test quantization
        quantized = quantizer.quantize(midi_data)
        assert quantized is not None, "Quantized data is None"
        assert len(quantized) > 0, "No notes after quantization"
        logger.info(f"✓ Quantization: {len(midi_data)} -> {len(quantized)} notes")
        
        # Test that notes are still valid
        notes = quantized.get_notes()
        for note in notes:
            assert note.start_time >= 0, "Invalid start time"
            assert note.end_time > note.start_time, "Invalid end time"
            assert 0 <= note.velocity <= 127, "Invalid velocity"
            assert 0 <= note.pitch <= 127, "Invalid pitch"
        logger.info("✓ All quantized notes valid")
        
        logger.info("✅ Quantization Test PASSED")
        return True, quantized
        
    except Exception as e:
        logger.error(f"❌ Quantization Test FAILED: {e}")
        return False, None


def test_midi_export(midi_data):
    """Test MIDI file export."""
    logger.info("\n" + "="*60)
    logger.info("TEST: MIDI Export")
    logger.info("="*60)
    
    try:
        exporter = MIDIExporter()
        
        # Test export
        output_file = 'test_output.mid'
        success = exporter.export(midi_data, output_file)
        assert success, "Export returned False"
        assert os.path.exists(output_file), "Export file not created"
        logger.info(f"✓ MIDI exported: {output_file}")
        
        # Test file size
        file_size = os.path.getsize(output_file)
        assert file_size > 0, "Export file is empty"
        logger.info(f"✓ File size: {file_size} bytes")
        
        # Test validation
        is_valid, msg = exporter.validate_output_path('test.mid')
        assert is_valid, f"Path validation failed: {msg}"
        logger.info("✓ Path validation working")
        
        logger.info("✅ MIDI Export Test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ MIDI Export Test FAILED: {e}")
        return False


def test_json_export(midi_data, source_file):
    """Test JSON file export."""
    logger.info("\n" + "="*60)
    logger.info("TEST: JSON Export")
    logger.info("="*60)
    
    try:
        exporter = JSONExporter()
        
        # Test export
        output_file = 'test_output.json'
        success = exporter.export(midi_data, output_file, source_file)
        assert success, "Export returned False"
        assert os.path.exists(output_file), "Export file not created"
        logger.info(f"✓ JSON exported: {output_file}")
        
        # Test file content
        import json
        with open(output_file, 'r') as f:
            data = json.load(f)
        assert 'notes' in data, "Missing notes in JSON"
        assert 'metadata' in data, "Missing metadata in JSON"
        assert len(data['notes']) > 0, "No notes in JSON"
        logger.info(f"✓ JSON contains {len(data['notes'])} notes")
        
        logger.info("✅ JSON Export Test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ JSON Export Test FAILED: {e}")
        return False


def run_all_tests():
    """Run all integration tests."""
    logger.info("\n" + "="*60)
    logger.info("STARTING INTEGRATION TEST SUITE")
    logger.info("="*60)
    
    results = {}
    
    # Test 1: Audio Loading
    success, audio_file, audio_data, sample_rate = test_audio_loading()
    results['audio_loading'] = success
    if not success:
        logger.error("Cannot continue without audio loading")
        return results
    
    # Test 2: Pitch Detection
    success, frequencies, confidences, times = test_pitch_detection(audio_data, sample_rate)
    results['pitch_detection'] = success
    if not success:
        logger.error("Cannot continue without pitch detection")
        return results
    
    # Test 3: Onset Detection
    success, onset_times = test_onset_detection(audio_data, sample_rate)
    results['onset_detection'] = success
    if not success:
        logger.error("Cannot continue without onset detection")
        return results
    
    # Test 4: MIDI Conversion
    success, midi_data = test_midi_conversion(frequencies, confidences, times, onset_times)
    results['midi_conversion'] = success
    if not success:
        logger.error("Cannot continue without MIDI conversion")
        return results
    
    # Test 5: Quantization
    success, quantized_data = test_quantization(midi_data)
    results['quantization'] = success
    if not success:
        quantized_data = midi_data  # Use unquantized if failed
    
    # Test 6: MIDI Export
    success = test_midi_export(quantized_data)
    results['midi_export'] = success
    
    # Test 7: JSON Export
    success = test_json_export(quantized_data, audio_file)
    results['json_export'] = success
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    logger.info("="*60)
    logger.info(f"Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    logger.info("="*60)
    
    return results


if __name__ == '__main__':
    results = run_all_tests()
    
    # Exit with appropriate code
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)
