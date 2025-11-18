# test_pitch_detector.py
"""
Test script for Pitch Detector Module.
Tests pitch detection with both piptrack and pyin algorithms.
"""

from audio import AudioLoader, PitchDetector
from utils import setup_logging
import numpy as np

def main():
    # Initialize logging
    logger = setup_logging()
    logger.info("Testing Pitch Detector Module...")
    
    # Create instances
    loader = AudioLoader()
    detector = PitchDetector()
    
    # Test 1: Generate and save test audio with known pitch
    print("\n--- Test 1: Creating test audio (A4 = 440 Hz) ---")
    test_audio = create_test_audio_with_pitch(440.0, duration=2.0)
    save_test_audio(test_audio, 'test_pitch_440hz.wav')
    logger.info("Test audio created: test_pitch_440hz.wav (440 Hz for 2 seconds)")
    
    # Test 2: Load the audio
    print("\n--- Test 2: Loading audio file ---")
    audio_data, sample_rate = loader.load_audio('test_pitch_440hz.wav')
    logger.info(f"Audio loaded: {len(audio_data)} samples at {sample_rate} Hz")
    
    # Test 3: Detect pitch with piptrack algorithm
    print("\n--- Test 3: Detecting pitch with piptrack algorithm ---")
    frequencies, confidences, times = detector.detect_pitch(audio_data, sample_rate)
    
    logger.info(f"Detection complete!")
    logger.info(f"Number of frames: {len(frequencies)}")
    
    # Analyze results
    valid_frequencies = frequencies[frequencies > 0]
    if len(valid_frequencies) > 0:
        avg_freq = valid_frequencies.mean()
        logger.info(f"Average detected frequency: {avg_freq:.2f} Hz")
        logger.info(f"Expected frequency: 440.00 Hz")
        logger.info(f"Error: {abs(avg_freq - 440.0):.2f} Hz ({abs(avg_freq - 440.0) / 440.0 * 100:.2f}%)")
        
        # Convert to note name
        note_name = PitchDetector.frequency_to_note_name(avg_freq)
        logger.info(f"Detected note: {note_name} (expected: A4)")
    
    # Test 4: Get detection statistics
    print("\n--- Test 4: Getting detection statistics ---")
    stats = detector.get_detection_stats()
    for key, value in stats.items():
        logger.info(f"{key}: {value}")
    
    # Test 5: Test with different algorithm (pyin)
    print("\n--- Test 5: Testing with pyin algorithm ---")
    detector.set_algorithm('pyin')
    frequencies_pyin, confidences_pyin, times_pyin = detector.detect_pitch(audio_data, sample_rate)
    
    valid_frequencies_pyin = frequencies_pyin[frequencies_pyin > 0]
    if len(valid_frequencies_pyin) > 0:
        avg_freq_pyin = valid_frequencies_pyin.mean()
        logger.info(f"Pyin average frequency: {avg_freq_pyin:.2f} Hz")
        logger.info(f"Error: {abs(avg_freq_pyin - 440.0):.2f} Hz")
    
    # Test 6: Test frequency to note name conversion
    print("\n--- Test 6: Testing frequency to note name conversion ---")
    test_frequencies = [440.0, 261.63, 329.63, 523.25, 0.0]
    expected_notes = ['A4', 'C4', 'E4', 'C5', 'N/A']
    
    for freq, expected in zip(test_frequencies, expected_notes):
        note = PitchDetector.frequency_to_note_name(freq)
        status = "✓" if note == expected else "✗"
        logger.info(f"{status} {freq} Hz -> {note} (expected: {expected})")
    
    print("\n✓ All tests completed! Check results above.")

def create_test_audio_with_pitch(frequency, duration=1.0, sample_rate=22050):
    """
    Create test audio signal with specific frequency.
    
    Args:
        frequency: Desired frequency in Hz
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
    
    Returns:
        Audio signal as numpy array
    """
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = 0.5 * np.sin(2 * np.pi * frequency * t)
    return audio.astype(np.float32)

def save_test_audio(audio_data, filename, sample_rate=22050):
    """Save test audio to WAV file."""
    import soundfile as sf
    sf.write(filename, audio_data, sample_rate)

if __name__ == '__main__':
    main()
