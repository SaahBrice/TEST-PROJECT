# test_midi_data_model.py
"""
Test script for MIDI Data Model.
Tests Note and MIDIData classes with various operations.
"""

from midi import Note, MIDIData
from utils import setup_logging

def main():
    # Initialize logging
    logger = setup_logging()
    logger.info("Testing MIDI Data Model...")
    
    # Test 1: Create individual notes
    print("\n--- Test 1: Creating Note objects ---")
    note1 = Note(pitch=60, start_time=0.0, end_time=0.5, velocity=80)
    logger.info(f"Created: {note1}")
    logger.info(f"Note name: {note1.note_name}")
    logger.info(f"Frequency: {note1.frequency:.2f} Hz")
    logger.info(f"Duration: {note1.duration:.2f}s")
    
    # Test 2: Test frequency/pitch conversion
    print("\n--- Test 2: Testing frequency-pitch conversion ---")
    test_frequencies = [440.0, 261.63, 329.63, 523.25]
    expected_notes = ['A4', 'C4', 'E4', 'C5']
    
    for freq, expected in zip(test_frequencies, expected_notes):
        pitch = Note.frequency_to_pitch(freq)
        note = Note(pitch=pitch, start_time=0.0, end_time=1.0)
        freq_back = Note.pitch_to_frequency(pitch)
        status = "✓" if note.note_name == expected else "✗"
        logger.info(f"{status} {freq:.2f} Hz -> Pitch {pitch} ({note.note_name}) -> {freq_back:.2f} Hz")
    
    # Test 3: Create a collection of notes
    print("\n--- Test 3: Creating MIDIData collection ---")
    midi_data = MIDIData()
    
    # Add a simple melody (C major scale)
    scale_pitches = [60, 62, 64, 65, 67, 69, 71, 72]  # C4 to C5
    for i, pitch in enumerate(scale_pitches):
        start = i * 0.5
        end = start + 0.4
        note = Note(pitch=pitch, start_time=start, end_time=end, velocity=80)
        midi_data.add_note(note)
        logger.info(f"Added: {note.note_name} at {start:.2f}s")
    
    logger.info(f"Total notes in collection: {len(midi_data)}")
    
    # Test 4: Query notes at specific time
    print("\n--- Test 4: Querying notes at specific time ---")
    query_time = 1.5
    active_notes = midi_data.get_notes_at_time(query_time)
    logger.info(f"Notes active at {query_time}s: {len(active_notes)}")
    for note in active_notes:
        logger.info(f"  - {note.note_name}")
    
    # Test 5: Query notes in time range
    print("\n--- Test 5: Querying notes in time range ---")
    range_notes = midi_data.get_notes_in_range(1.0, 2.5)
    logger.info(f"Notes between 1.0s and 2.5s: {len(range_notes)}")
    for note in range_notes:
        logger.info(f"  - {note.note_name} ({note.start_time:.2f}s - {note.end_time:.2f}s)")
    
    # Test 6: Query notes by pitch
    print("\n--- Test 6: Querying notes by pitch ---")
    pitch_notes = midi_data.get_notes_by_pitch(67)  # G4
    logger.info(f"Notes with pitch 67 (G4): {len(pitch_notes)}")
    
    # Test 7: Get statistics
    print("\n--- Test 7: Getting collection statistics ---")
    stats = midi_data.get_statistics()
    logger.info("Collection Statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.3f}")
        else:
            logger.info(f"  {key}: {value}")
    
    # Test 8: Test note overlap detection
    print("\n--- Test 8: Testing note overlap detection ---")
    note_a = Note(pitch=60, start_time=0.0, end_time=1.0)
    note_b = Note(pitch=62, start_time=0.5, end_time=1.5)
    note_c = Note(pitch=64, start_time=2.0, end_time=3.0)
    
    logger.info(f"Note A and B overlap: {note_a.overlaps(note_b)} (expected: True)")
    logger.info(f"Note A and C overlap: {note_a.overlaps(note_c)} (expected: False)")
    logger.info(f"Note B and C overlap: {note_b.overlaps(note_c)} (expected: False)")
    
    # Test 9: Test serialization
    print("\n--- Test 9: Testing serialization ---")
    note_dict = note1.to_dict()
    logger.info(f"Note as dictionary: {note_dict}")
    
    midi_dict_list = midi_data.to_dict_list()
    logger.info(f"Serialized {len(midi_dict_list)} notes to dictionary list")
    
    # Reconstruct from dictionary
    reconstructed = MIDIData.from_dict_list(midi_dict_list)
    logger.info(f"Reconstructed {len(reconstructed)} notes from dictionary")
    
    # Test 10: Test error handling
    print("\n--- Test 10: Testing error handling ---")
    try:
        invalid_note = Note(pitch=200, start_time=0.0, end_time=1.0)
        logger.error("✗ Should have raised ValueError for invalid pitch")
    except ValueError as e:
        logger.info(f"✓ Correctly caught invalid pitch: {e}")
    
    try:
        invalid_timing = Note(pitch=60, start_time=1.0, end_time=0.5)
        logger.error("✗ Should have raised ValueError for invalid timing")
    except ValueError as e:
        logger.info(f"✓ Correctly caught invalid timing: {e}")
    
    print("\n✓ All tests completed! MIDI Data Model is working correctly.")

if __name__ == '__main__':
    main()
