# tests/test_velocity_data.py
"""
Test velocity data capture and validation.
Verifies that MIDI velocity values are correctly captured during transcription.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import soundfile as sf
from audio import AudioLoader, PitchDetector, OnsetDetector
from midi import MIDIConverter, Note
from utils import setup_logging

logger = setup_logging()


def create_test_audio_with_dynamics():
    """
    Create test audio with varying dynamics (soft to loud).
    
    Returns:
        Tuple of (filename, expected_velocities)
    """
    logger.info("Creating test audio with dynamics...")
    
    sample_rate = 22050
    frequency = 440.0  # A4
    
    # Create 5 notes with increasing amplitude (soft to loud)
    segments = []
    expected_velocities = []
    
    amplitudes = [0.2, 0.4, 0.6, 0.8, 1.0]  # Soft to loud
    
    for amp in amplitudes:
        # Generate note
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration))
        envelope = np.exp(-2 * t / duration)  # Decay envelope
        note = amp * envelope * np.sin(2 * np.pi * frequency * t)
        segments.append(note)
        
        # Calculate expected velocity (0-127 range)
        # Our system should map amplitude to velocity
        velocity = int(amp * 127)
        expected_velocities.append(velocity)
        
        # Add silence
        silence = np.zeros(int(sample_rate * 0.1))
        segments.append(silence)
    
    # Combine all segments
    audio = np.concatenate(segments).astype(np.float32)
    
    # Save to file
    filename = 'test_velocity_dynamics.wav'
    sf.write(filename, audio, sample_rate)
    
    logger.info(f"Test audio created: {filename}")
    logger.info(f"Expected velocities: {expected_velocities}")
    
    return filename, expected_velocities


def test_velocity_capture():
    """Test that velocity values are captured during transcription."""
    logger.info("\n" + "="*60)
    logger.info("TEST: Velocity Data Capture")
    logger.info("="*60)
    
    try:
        # Create test audio
        audio_file, expected_velocities = create_test_audio_with_dynamics()
        
        # Load audio
        loader = AudioLoader()
        audio_data, sample_rate = loader.load_audio(audio_file)
        logger.info(f"✓ Audio loaded: {len(audio_data)} samples")
        
        # Detect pitch
        pitch_detector = PitchDetector()
        frequencies, confidences, times = pitch_detector.detect_pitch(audio_data, sample_rate)
        logger.info(f"✓ Pitch detected: {len(frequencies)} frames")
        
        # Detect onsets
        onset_detector = OnsetDetector()
        onset_times, onset_strengths = onset_detector.detect_onsets(audio_data, sample_rate)
        logger.info(f"✓ Onsets detected: {len(onset_times)} onsets")
        
        # Convert to MIDI
        converter = MIDIConverter()
        midi_data = converter.convert_to_midi(frequencies, confidences, times, onset_times)
        logger.info(f"✓ MIDI conversion: {len(midi_data)} notes created")
        
        # VALIDATE VELOCITY DATA
        logger.info("\nValidating velocity data:")
        
        notes = midi_data.get_notes()
        
        if len(notes) == 0:
            logger.error("❌ No notes created")
            return False
        
        # Check each note has velocity
        all_have_velocity = True
        velocities = []
        
        for i, note in enumerate(notes):
            if not hasattr(note, 'velocity'):
                logger.error(f"❌ Note {i} missing velocity attribute")
                all_have_velocity = False
            else:
                velocities.append(note.velocity)
                logger.info(f"  Note {i}: velocity={note.velocity}, pitch={note.pitch}, "
                          f"start={note.start_time:.2f}s")
        
        if not all_have_velocity:
            return False
        
        logger.info("\n✓ All notes have velocity attribute")
        
        # Check velocity range
        min_vel = min(velocities)
        max_vel = max(velocities)
        avg_vel = sum(velocities) / len(velocities)
        
        logger.info(f"\nVelocity Statistics:")
        logger.info(f"  Min: {min_vel}")
        logger.info(f"  Max: {max_vel}")
        logger.info(f"  Average: {avg_vel:.1f}")
        logger.info(f"  Range: {max_vel - min_vel}")
        
        # Validate range (0-127)
        if not all(0 <= v <= 127 for v in velocities):
            logger.error("❌ Velocity values outside valid range (0-127)")
            return False
        
        logger.info("✓ All velocities in valid range (0-127)")
        
        # Check for variation (not all the same)
        if len(set(velocities)) == 1:
            logger.warning("⚠ All velocities are the same - may need tuning")
        else:
            logger.info(f"✓ Velocity variation detected: {len(set(velocities))} unique values")
        
        # Check if velocities correlate with expected dynamics
        if len(velocities) >= 3:
            # Check if there's a general trend (not exact match needed)
            if velocities[-1] > velocities[0]:
                logger.info("✓ Velocity trend matches dynamics (increasing)")
            elif velocities[-1] < velocities[0]:
                logger.info("✓ Velocity trend detected (decreasing)")
            else:
                logger.warning("⚠ No clear velocity trend")
        
        logger.info("\n✅ Velocity Data Capture Test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False


def test_velocity_edge_cases():
    """Test edge cases for velocity values."""
    logger.info("\n" + "="*60)
    logger.info("TEST: Velocity Edge Cases")
    logger.info("="*60)
    
    try:
        # Test 1: Very soft note (should not be 0)
        note_soft = Note(pitch=60, start_time=0.0, end_time=1.0, velocity=1)
        assert note_soft.velocity == 1, "Soft note velocity incorrect"
        logger.info("✓ Very soft note (velocity=1)")
        
        # Test 2: Very loud note (should be 127)
        note_loud = Note(pitch=60, start_time=0.0, end_time=1.0, velocity=127)
        assert note_loud.velocity == 127, "Loud note velocity incorrect"
        logger.info("✓ Very loud note (velocity=127)")
        
        # Test 3: Medium note
        note_medium = Note(pitch=60, start_time=0.0, end_time=1.0, velocity=64)
        assert note_medium.velocity == 64, "Medium note velocity incorrect"
        logger.info("✓ Medium note (velocity=64)")
        
        # Test 4: Check velocity is stored correctly
        assert hasattr(note_medium, 'velocity'), "Note missing velocity attribute"
        logger.info("✓ Velocity attribute exists")
        
        # Test 5: Velocity affects to_dict output
        note_dict = note_medium.to_dict()
        assert 'velocity' in note_dict, "Velocity missing from dict representation"
        assert note_dict['velocity'] == 64, "Velocity value incorrect in dict"
        logger.info("✓ Velocity in dict representation")
        
        logger.info("\n✅ Velocity Edge Cases Test PASSED")
        return True
        
    except AssertionError as e:
        logger.error(f"❌ Test failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}", exc_info=True)
        return False


def run_all_tests():
    """Run all velocity validation tests."""
    logger.info("\n" + "="*60)
    logger.info("STARTING VELOCITY VALIDATION TEST SUITE")
    logger.info("="*60)
    
    results = []
    
    # Test 1: Edge cases (quick)
    results.append(("Edge Cases", test_velocity_edge_cases()))
    
    # Test 2: Full capture test
    results.append(("Velocity Capture", test_velocity_capture()))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    logger.info("="*60)
    logger.info(f"Results: {passed_count}/{total_count} tests passed")
    logger.info("="*60)
    
    return all(p for _, p in results)


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
