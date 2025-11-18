# test_onset_detector.py
"""
Test script for Onset Detector Module.
Tests onset detection with various audio patterns.
"""

from audio import AudioLoader, OnsetDetector
from utils import setup_logging
import numpy as np
import soundfile as sf

def main():
    # Initialize logging
    logger = setup_logging()
    logger.info("Testing Onset Detector Module...")
    
    # Create instances
    loader = AudioLoader()
    detector = OnsetDetector()
    
    # Test 1: Create test audio with distinct note onsets
    print("\n--- Test 1: Creating test audio with 5 note onsets ---")
    test_audio, expected_onsets = create_test_audio_with_onsets()
    sf.write('test_onsets.wav', test_audio, 22050)
    logger.info(f"Test audio created with expected onsets at: {expected_onsets}")
    
    # Test 2: Load the audio
    print("\n--- Test 2: Loading audio file ---")
    audio_data, sample_rate = loader.load_audio('test_onsets.wav')
    duration = len(audio_data) / sample_rate
    logger.info(f"Audio loaded: {duration:.2f}s duration")
    
    # Test 3: Detect onsets
    print("\n--- Test 3: Detecting onsets ---")
    onset_times, onset_strength = detector.detect_onsets(audio_data, sample_rate)
    
    logger.info(f"Detected {len(onset_times)} onsets")
    logger.info(f"Onset times: {onset_times}")
    
    # Test 4: Compare with expected onsets
    print("\n--- Test 4: Comparing with expected onsets ---")
    for i, expected in enumerate(expected_onsets):
        if i < len(onset_times):
            detected = onset_times[i]
            error = abs(detected - expected)
            status = "✓" if error < 0.1 else "✗"
            logger.info(f"{status} Expected: {expected:.2f}s, Detected: {detected:.2f}s, Error: {error:.3f}s")
        else:
            logger.warning(f"✗ Expected onset at {expected:.2f}s not detected")
    
    # Test 5: Get detection statistics
    print("\n--- Test 5: Getting detection statistics ---")
    stats = detector.get_detection_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            logger.info(f"{key}: {value:.3f}")
        else:
            logger.info(f"{key}: {value}")
    
    # Test 6: Get onset intervals
    print("\n--- Test 6: Getting onset intervals ---")
    intervals = detector.get_onset_intervals(duration)
    logger.info(f"Generated {len(intervals)} intervals:")
    for i, (start, end) in enumerate(intervals[:5]):  # Show first 5
        logger.info(f"  Interval {i+1}: {start:.3f}s - {end:.3f}s (duration: {end-start:.3f}s)")
    
    # Test 7: Visualize onsets
    print("\n--- Test 7: Visualizing onsets ---")
    visualization = detector.visualize_onsets(onset_times, duration)
    print("\nOnset Timeline:")
    print(visualization)
    
    # Test 8: Test with real-world audio (if exists)
    print("\n--- Test 8: Testing with previous test file ---")
    try:
        audio_data2, sample_rate2 = loader.load_audio('test_pitch_440hz.wav')
        onset_times2, _ = detector.detect_onsets(audio_data2, sample_rate2)
        logger.info(f"Detected {len(onset_times2)} onsets in 440Hz test file")
        logger.info(f"Onset times: {onset_times2}")
    except FileNotFoundError:
        logger.info("Previous test file not found, skipping this test")
    
    print("\n✓ All tests completed! Check results above.")

def create_test_audio_with_onsets(sample_rate=22050):
    """
    Create test audio with distinct note onsets.
    Creates 5 notes with silence between them.
    
    Returns:
        Tuple of (audio_array, expected_onset_times)
    """
    duration_per_note = 0.3  # seconds
    silence_duration = 0.2   # seconds
    num_notes = 5
    
    # Frequencies for each note (C4, D4, E4, F4, G4)
    frequencies = [261.63, 293.66, 329.63, 349.23, 392.00]
    
    expected_onsets = []
    segments = []
    current_time = 0.0
    
    for i, freq in enumerate(frequencies):
        # Note onset time
        expected_onsets.append(current_time)
        
        # Create note audio
        t = np.linspace(0, duration_per_note, int(sample_rate * duration_per_note))
        
        # Add envelope to make onset more distinct
        envelope = np.exp(-3 * t / duration_per_note)  # Exponential decay
        note = 0.5 * envelope * np.sin(2 * np.pi * freq * t)
        
        segments.append(note)
        current_time += duration_per_note
        
        # Add silence between notes (except after last note)
        if i < num_notes - 1:
            silence = np.zeros(int(sample_rate * silence_duration))
            segments.append(silence)
            current_time += silence_duration
    
    # Concatenate all segments
    audio = np.concatenate(segments).astype(np.float32)
    
    return audio, expected_onsets

if __name__ == '__main__':
    main()
