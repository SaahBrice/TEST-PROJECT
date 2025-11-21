# tests/test_velocity_quick.py
"""Quick test to verify velocity data is working."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from midi import Note, MIDIData

def test_velocity():
    """Quick velocity check."""
    print("Testing velocity data...")
    
    # Create test notes with different velocities
    notes = [
        Note(pitch=60, start_time=0.0, end_time=1.0, velocity=30),   # Soft
        Note(pitch=62, start_time=1.0, end_time=2.0, velocity=80),   # Medium
        Note(pitch=64, start_time=2.0, end_time=3.0, velocity=120),  # Loud
    ]
    
    # Check velocities
    for i, note in enumerate(notes):
        print(f"Note {i}: velocity={note.velocity}, pitch={note.pitch}")
        assert hasattr(note, 'velocity'), f"Note {i} missing velocity"
        assert 0 <= note.velocity <= 127, f"Note {i} velocity out of range"
    
    # Check MIDIData statistics
    midi_data = MIDIData(notes)
    stats = midi_data.get_statistics()
    
    print(f"\nStatistics:")
    print(f"  Total notes: {stats['total_notes']}")
    print(f"  Avg velocity: {stats['avg_velocity']:.1f}")
    print(f"  Velocity range: {stats['velocity_range']}")
    
    assert 'avg_velocity' in stats, "Missing avg_velocity in stats"
    assert 'velocity_range' in stats, "Missing velocity_range in stats"
    
    print("\n✅ Velocity data working correctly!")
    return True

if __name__ == '__main__':
    test_velocity()
