# test_note_quantizer.py
"""
Test script for Note Quantizer Module.
Tests note post-processing and quality improvements.
"""

from midi import Note, MIDIData, NoteQuantizer
from utils import setup_logging

def main():
    # Initialize logging
    logger = setup_logging()
    logger.info("Testing Note Quantizer Module...")
    
    # Create quantizer
    quantizer = NoteQuantizer()
    
    # Test 1: Create sample notes with issues
    print("\n--- Test 1: Creating test notes with various issues ---")
    notes = create_problematic_notes()
    
    logger.info(f"Created {len(notes)} test notes:")
    for note in notes:
        logger.info(f"  {note}")
    
    midi_data = MIDIData(notes)
    original_stats = midi_data.get_statistics()
    logger.info(f"Original duration: {original_stats['duration']:.3f}s")
    
    # Test 2: Apply quantization
    print("\n--- Test 2: Applying quantization ---")
    quantized_data = quantizer.quantize(midi_data)
    
    logger.info(f"Quantized: {len(midi_data)} -> {len(quantized_data)} notes")
    logger.info("Quantized notes:")
    for note in quantized_data:
        logger.info(f"  {note}")
    
    # Test 3: Compare statistics
    print("\n--- Test 3: Comparing statistics ---")
    quantized_stats = quantized_data.get_statistics()
    
    logger.info("Before quantization:")
    logger.info(f"  Total notes: {original_stats['total_notes']}")
    logger.info(f"  Avg duration: {original_stats['avg_note_duration']:.3f}s")
    logger.info(f"  Min duration: {original_stats['min_note_duration']:.3f}s")
    
    logger.info("After quantization:")
    logger.info(f"  Total notes: {quantized_stats['total_notes']}")
    if quantized_stats['total_notes'] > 0:
        logger.info(f"  Avg duration: {quantized_stats['avg_note_duration']:.3f}s")
        logger.info(f"  Min duration: {quantized_stats['min_note_duration']:.3f}s")
    
    # Test 4: Test with musical scale from previous test
    print("\n--- Test 4: Testing with real conversion data ---")
    try:
        # Load from previous MIDI converter test
        from audio import AudioLoader, PitchDetector
        from midi import MIDIConverter
        
        loader = AudioLoader()
        pitch_detector = PitchDetector()
        midi_converter = MIDIConverter()
        
        # Load test audio
        audio_data, sample_rate = loader.load_audio('test_scale.wav')
        
        # Detect pitch
        frequencies, confidences, times = pitch_detector.detect_pitch(audio_data, sample_rate)
        
        # Convert to MIDI (continuous mode for better results)
        midi_data_raw = midi_converter.convert_to_midi(
            frequencies, confidences, times, onset_times=None
        )
        
        logger.info(f"Raw conversion: {len(midi_data_raw)} notes")
        
        # Apply quantization
        midi_data_quantized = quantizer.quantize(midi_data_raw)
        
        logger.info(f"After quantization: {len(midi_data_quantized)} notes")
        logger.info("Quantized notes from real audio:")
        for note in midi_data_quantized:
            logger.info(f"  {note}")
        
    except FileNotFoundError:
        logger.info("test_scale.wav not found, skipping real audio test")
    
    # Test 5: Test individual quantization features
    print("\n--- Test 5: Testing individual features ---")
    
    # Test gap filling
    notes_with_gaps = [
        Note(pitch=60, start_time=0.0, end_time=0.5, velocity=80),
        Note(pitch=60, start_time=0.55, end_time=1.0, velocity=80),  # Small gap
    ]
    
    midi_gaps = MIDIData(notes_with_gaps)
    quantized_gaps = quantizer.quantize(midi_gaps)
    
    logger.info(f"Gap filling test: {len(midi_gaps)} -> {len(quantized_gaps)} notes")
    if len(quantized_gaps) > 0:
        logger.info(f"First note duration: {quantized_gaps[0].duration:.3f}s")
        logger.info("(Should be extended to fill the gap)")
    
    # Test 6: Test merge threshold adjustment
    print("\n--- Test 6: Testing with different settings ---")
    quantizer.set_min_duration(0.1)
    quantizer.set_gap_fill_threshold(0.15)
    quantizer.set_merge_threshold(0.1)
    
    quantized_adjusted = quantizer.quantize(midi_data)
    logger.info(f"With adjusted settings: {len(quantized_adjusted)} notes")
    
    # Test 7: Test with settings disabled
    print("\n--- Test 7: Testing with features disabled ---")
    quantizer.enable_short_note_removal(False)
    quantizer.enable_gap_filling(False)
    
    quantized_disabled = quantizer.quantize(midi_data)
    logger.info(f"With features disabled: {len(quantized_disabled)} notes")
    logger.info("(Should be same or more than with features enabled)")
    
    print("\n✓ All tests completed! Check results above.")

def create_problematic_notes():
    """
    Create a set of notes with various quality issues for testing.
    
    Returns:
        List of Note objects with issues
    """
    notes = [
        # Normal note
        Note(pitch=60, start_time=0.0, end_time=0.5, velocity=80),
        
        # Very short note (should be removed)
        Note(pitch=62, start_time=0.6, end_time=0.62, velocity=75),
        
        # Normal note with small gap before next
        Note(pitch=64, start_time=0.7, end_time=1.0, velocity=85),
        
        # Same pitch, small gap (should merge or gap-fill)
        Note(pitch=64, start_time=1.05, end_time=1.3, velocity=82),
        
        # Low velocity note (might be removed)
        Note(pitch=65, start_time=1.4, end_time=1.6, velocity=25),
        
        # Overlapping notes (one should be removed)
        Note(pitch=67, start_time=1.7, end_time=2.0, velocity=90),
        Note(pitch=69, start_time=1.8, end_time=2.1, velocity=70),
        
        # Normal ending note
        Note(pitch=72, start_time=2.2, end_time=2.7, velocity=85),
    ]
    
    return notes

if __name__ == '__main__':
    main()
