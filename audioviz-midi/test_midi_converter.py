# test_midi_converter.py
"""
Test script for MIDI Converter Module.
Tests conversion from audio analysis to MIDI notes.
"""

from audio import AudioLoader, PitchDetector, OnsetDetector
from midi import MIDIConverter
from utils import setup_logging
import numpy as np
import soundfile as sf

def main():
    # Initialize logging
    logger = setup_logging()
    logger.info("Testing MIDI Converter Module...")
    
    # Create instances
    loader = AudioLoader()
    pitch_detector = PitchDetector()
    onset_detector = OnsetDetector()
    midi_converter = MIDIConverter()
    
    # Test 1: Create test audio with known notes
    print("\n--- Test 1: Creating test audio (C4-D4-E4-F4-G4) ---")
    test_audio, expected_notes = create_musical_scale()
    sf.write('test_scale.wav', test_audio, 22050)
    logger.info(f"Created scale with {len(expected_notes)} notes")
    for note_info in expected_notes:
        logger.info(f"  {note_info['name']} at {note_info['start']:.2f}s")
    
    # Test 2: Load and analyze audio
    print("\n--- Test 2: Loading and analyzing audio ---")
    audio_data, sample_rate = loader.load_audio('test_scale.wav')
    logger.info(f"Audio loaded: {len(audio_data)} samples")
    
    # Test 3: Detect pitch
    print("\n--- Test 3: Detecting pitch ---")
    frequencies, confidences, times = pitch_detector.detect_pitch(audio_data, sample_rate)
    logger.info(f"Pitch detection complete: {len(frequencies)} frames")
    
    pitch_stats = pitch_detector.get_detection_stats()
    logger.info(f"Pitch coverage: {pitch_stats['pitch_coverage']:.1%}")
    logger.info(f"Average confidence: {pitch_stats['average_confidence']:.3f}")
    
    # Test 4: Detect onsets
    print("\n--- Test 4: Detecting onsets ---")
    onset_times, _ = onset_detector.detect_onsets(audio_data, sample_rate)
    logger.info(f"Detected {len(onset_times)} onsets")
    logger.info(f"Onset times: {onset_times}")
    
    # Test 5: Convert to MIDI with onsets
    print("\n--- Test 5: Converting to MIDI (with onsets) ---")
    midi_data = midi_converter.convert_to_midi(
        frequencies, confidences, times, onset_times
    )
    
    logger.info(f"Created {len(midi_data)} MIDI notes")
    
    # Display created notes
    for note in midi_data:
        logger.info(f"  {note}")
    
    # Test 6: Compare with expected notes
    print("\n--- Test 6: Comparing with expected notes ---")
    notes_list = midi_data.get_notes()
    
    for i, expected in enumerate(expected_notes):
        if i < len(notes_list):
            detected = notes_list[i]
            pitch_match = detected.note_name == expected['name']
            time_error = abs(detected.start_time - expected['start'])
            
            status = "✓" if pitch_match and time_error < 0.15 else "✗"
            logger.info(
                f"{status} Expected: {expected['name']} at {expected['start']:.2f}s, "
                f"Detected: {detected.note_name} at {detected.start_time:.2f}s "
                f"(error: {time_error:.3f}s)"
            )
        else:
            logger.warning(f"✗ Expected note {expected['name']} at {expected['start']:.2f}s not detected")
    
    # Test 7: Get MIDI statistics
    print("\n--- Test 7: MIDI statistics ---")
    stats = midi_data.get_statistics()
    logger.info("MIDI Data Statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.3f}")
        else:
            logger.info(f"  {key}: {value}")
    
    # Test 8: Convert without onsets (continuous mode)
    print("\n--- Test 8: Converting without onsets (continuous mode) ---")
    midi_data_continuous = midi_converter.convert_to_midi(
        frequencies, confidences, times, onset_times=None
    )
    
    logger.info(f"Continuous mode created {len(midi_data_continuous)} notes")
    logger.info("Notes in continuous mode:")
    for note in midi_data_continuous:
        logger.info(f"  {note}")
    
    # Test 9: Test with different settings
    print("\n--- Test 9: Testing with adjusted settings ---")
    midi_converter.set_min_note_duration(0.1)
    midi_converter.set_confidence_threshold(0.15)
    
    midi_data_filtered = midi_converter.convert_to_midi(
        frequencies, confidences, times, onset_times
    )
    
    logger.info(f"With stricter settings: {len(midi_data_filtered)} notes")
    logger.info("(Should be fewer due to higher thresholds)")
    
    # Test 10: Query notes by time
    print("\n--- Test 10: Querying notes by time ---")
    query_time = 1.0
    notes_at_time = midi_data.get_notes_at_time(query_time)
    logger.info(f"Notes active at {query_time}s: {len(notes_at_time)}")
    for note in notes_at_time:
        logger.info(f"  {note.note_name}")
    
    print("\n✓ All tests completed! Check results above.")

def create_musical_scale(sample_rate=22050):
    """
    Create audio with a musical scale (C4-D4-E4-F4-G4).
    
    Returns:
        Tuple of (audio_array, expected_notes_info)
    """
    # Note frequencies (C4 through G4)
    notes = [
        {'name': 'C4', 'freq': 261.63, 'start': 0.0},
        {'name': 'D4', 'freq': 293.66, 'start': 0.6},
        {'name': 'E4', 'freq': 329.63, 'start': 1.2},
        {'name': 'F4', 'freq': 349.23, 'start': 1.8},
        {'name': 'G4', 'freq': 392.00, 'start': 2.4}
    ]
    
    note_duration = 0.5  # seconds
    silence_duration = 0.1  # seconds between notes
    
    segments = []
    
    for note_info in notes:
        freq = note_info['freq']
        
        # Create note audio with envelope
        t = np.linspace(0, note_duration, int(sample_rate * note_duration))
        envelope = np.exp(-2 * t / note_duration)  # Decay envelope
        note_audio = 0.5 * envelope * np.sin(2 * np.pi * freq * t)
        
        segments.append(note_audio)
        
        # Add silence
        silence = np.zeros(int(sample_rate * silence_duration))
        segments.append(silence)
    
    # Concatenate all segments
    audio = np.concatenate(segments).astype(np.float32)
    
    return audio, notes

if __name__ == '__main__':
    main()
