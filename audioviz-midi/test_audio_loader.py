# test_audio_loader.py
"""
Test script for Audio Loader Module.
Tests audio loading, preprocessing, and validation functionality.
"""

from audio import AudioLoader
from utils import setup_logging
import numpy as np

def main():
    # Initialize logging
    logger = setup_logging()
    logger.info("Testing Audio Loader Module...")
    
    # Create audio loader instance
    loader = AudioLoader()
    
    # Display supported formats
    formats = AudioLoader.get_supported_formats()
    logger.info(f"Supported formats: {', '.join(formats)}")
    
    # Test 1: Generate and save a simple test audio file
    print("\n--- Test 1: Creating test audio file ---")
    test_audio = create_test_audio()
    save_test_audio(test_audio)
    logger.info("Test audio file created: test_audio.wav")
    
    # Test 2: Validate the test file
    print("\n--- Test 2: Validating audio file ---")
    is_valid, message = loader.validate_file('test_audio.wav')
    logger.info(f"Validation result: {is_valid}")
    logger.info(f"Validation message: {message}")
    
    # Test 3: Load the audio file
    print("\n--- Test 3: Loading audio file ---")
    try:
        audio_data, sample_rate = loader.load_audio('test_audio.wav')
        logger.info(f"Audio loaded successfully!")
        logger.info(f"Sample rate: {sample_rate} Hz")
        logger.info(f"Audio shape: {audio_data.shape}")
        logger.info(f"Duration: {len(audio_data) / sample_rate:.2f} seconds")
        
        # Test 4: Get audio info
        print("\n--- Test 4: Getting audio info ---")
        info = loader.get_audio_info()
        for key, value in info.items():
            logger.info(f"{key}: {value}")
        
        print("\n✓ All tests passed! Audio Loader is working correctly.")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print("\n✗ Test failed. Check logs for details.")

def create_test_audio():
    """Create a simple test audio signal (1 second, 440 Hz sine wave)."""
    import numpy as np
    
    sample_rate = 22050
    duration = 1.0  # seconds
    frequency = 440.0  # A4 note
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = 0.5 * np.sin(2 * np.pi * frequency * t)
    
    return audio.astype(np.float32)

def save_test_audio(audio_data):
    """Save test audio to WAV file."""
    import soundfile as sf
    
    sf.write('test_audio.wav', audio_data, 22050)

if __name__ == '__main__':
    main()
