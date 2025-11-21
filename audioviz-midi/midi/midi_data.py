# midi/midi_data.py
"""
MIDI Data Collection Management for AudioViz MIDI.
Manages collections of Note objects with query and manipulation methods.
"""

from typing import List, Optional, Tuple
import numpy as np
from midi.note import Note
from utils.logger import get_logger

logger = get_logger(__name__)


class MIDIData:
    """
    Container for managing a collection of MIDI notes.
    
    Provides methods for adding, querying, and manipulating musical note data.
    Maintains notes in chronological order for efficient retrieval.
    """
    
    def __init__(self, notes: Optional[List[Note]] = None):
        """
        Initialize MIDI data collection.
        
        Args:
            notes: Optional initial list of Note objects
        """
        self._notes = []
        
        if notes:
            for note in notes:
                self.add_note(note)
        
        logger.debug(f"MIDIData initialized with {len(self._notes)} notes")
    
    def add_note(self, note: Note):
        """
        Add a note to the collection.
        Notes are maintained in chronological order by start time.
        
        Args:
            note: Note object to add
        """
        if not isinstance(note, Note):
            raise TypeError("Can only add Note objects")
        
        self._notes.append(note)
        # Keep notes sorted by start time for efficient queries
        self._notes.sort()
        
        logger.debug(f"Added {note}")
    
    def add_notes(self, notes: List[Note]):
        """
        Add multiple notes to the collection.
        
        Args:
            notes: List of Note objects to add
        """
        for note in notes:
            self.add_note(note)
        
        logger.info(f"Added {len(notes)} notes to collection")
    
    def get_notes(self) -> List[Note]:
        """
        Get all notes in the collection.
        
        Returns:
            List of all Note objects
        """
        return self._notes.copy()
    
    def get_notes_at_time(self, time: float) -> List[Note]:
        """
        Get all notes active at a specific time.
        
        Args:
            time: Time in seconds
        
        Returns:
            List of Note objects active at the given time
        """
        return [note for note in self._notes if note.is_active_at(time)]
    
    def get_notes_in_range(self, start_time: float, end_time: float) -> List[Note]:
        """
        Get all notes that overlap with a time range.
        
        Args:
            start_time: Range start time in seconds
            end_time: Range end time in seconds
        
        Returns:
            List of Note objects overlapping the time range
        """
        return [note for note in self._notes 
                if not (note.end_time <= start_time or note.start_time >= end_time)]
    
    def get_notes_by_pitch(self, pitch: int) -> List[Note]:
        """
        Get all notes with a specific MIDI pitch.
        
        Args:
            pitch: MIDI pitch number (0-127)
        
        Returns:
            List of Note objects with the specified pitch
        """
        return [note for note in self._notes if note.pitch == pitch]
    
    def get_notes_in_pitch_range(self, min_pitch: int, max_pitch: int) -> List[Note]:
        """
        Get all notes within a pitch range.
        
        Args:
            min_pitch: Minimum MIDI pitch (inclusive)
            max_pitch: Maximum MIDI pitch (inclusive)
        
        Returns:
            List of Note objects within pitch range
        """
        return [note for note in self._notes 
                if min_pitch <= note.pitch <= max_pitch]
    
    def remove_note(self, note: Note) -> bool:
        """
        Remove a specific note from the collection.
        
        Args:
            note: Note object to remove
        
        Returns:
            True if note was found and removed, False otherwise
        """
        try:
            self._notes.remove(note)
            logger.debug(f"Removed {note}")
            return True
        except ValueError:
            logger.warning(f"Note not found in collection: {note}")
            return False
    
    def clear(self):
        """Remove all notes from the collection."""
        count = len(self._notes)
        self._notes.clear()
        logger.info(f"Cleared {count} notes from collection")
    
    def get_duration(self) -> float:
        """
        Get total duration from first note start to last note end.
        
        Returns:
            Total duration in seconds, or 0 if no notes
        """
        if not self._notes:
            return 0.0
        
        return self._notes[-1].end_time - self._notes[0].start_time
    
    def get_pitch_range(self) -> Tuple[int, int]:
        """
        Get the range of pitches in the collection.
        
        Returns:
            Tuple of (min_pitch, max_pitch), or (0, 0) if no notes
        """
        if not self._notes:
            return (0, 0)
        
        pitches = [note.pitch for note in self._notes]
        return (min(pitches), max(pitches))
    
    def get_statistics(self) -> dict:
        """
        Get statistical information about the note collection.
        
        Returns:
            Dictionary with various statistics
        """
        if not self._notes:
            return {
                'total_notes': 0,
                'duration': 0.0,
                'pitch_range': (0, 0),
                'avg_note_duration': 0.0,
                'avg_velocity': 0.0,
                'velocity_range': (0, 0)
            }
        
        durations = [note.duration for note in self._notes]
        velocities = [note.velocity for note in self._notes]
        min_pitch, max_pitch = self.get_pitch_range()
        
        stats = {
            'total_notes': len(self._notes),
            'duration': self.get_duration(),
            'pitch_range': (min_pitch, max_pitch),
            'avg_note_duration': float(np.mean(durations)),
            'min_note_duration': float(np.min(durations)),
            'max_note_duration': float(np.max(durations)),
            'avg_velocity': float(np.mean(velocities)),
            'min_velocity': int(np.min(velocities)),
            'max_velocity': int(np.max(velocities)),
            'velocity_range': (int(np.min(velocities)), int(np.max(velocities))),
            'first_note_time': self._notes[0].start_time,
            'last_note_time': self._notes[-1].end_time
        }
        
        return stats
    
    def to_dict_list(self) -> List[dict]:
        """
        Convert all notes to list of dictionaries for serialization.
        
        Returns:
            List of note dictionaries
        """
        return [note.to_dict() for note in self._notes]
    
    @classmethod
    def from_dict_list(cls, data: List[dict]) -> 'MIDIData':
        """
        Create MIDIData from list of note dictionaries.
        
        Args:
            data: List of note dictionaries
        
        Returns:
            MIDIData object
        """
        notes = [Note.from_dict(note_data) for note_data in data]
        return cls(notes)
    
    def __len__(self) -> int:
        """Get number of notes in collection."""
        return len(self._notes)
    
    def __iter__(self):
        """Iterate over notes in chronological order."""
        return iter(self._notes)
    
    def __getitem__(self, index: int) -> Note:
        """Get note by index."""
        return self._notes[index]
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"MIDIData(notes={len(self._notes)}, duration={self.get_duration():.2f}s)"
