# midi/note.py
"""
MIDI Data Model for AudioViz MIDI.
Defines core data structures for representing musical notes in MIDI format.
"""

import numpy as np
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class Note:
    """
    Represents a single musical note with MIDI attributes.
    
    Attributes:
        pitch: MIDI note number (0-127), where 60 = Middle C (C4)
        start_time: Note onset time in seconds
        end_time: Note offset time in seconds
        velocity: MIDI velocity (0-127), representing note intensity/volume
    """
    
    # MIDI note number range
    MIN_PITCH = 0
    MAX_PITCH = 127
    
    # MIDI velocity range
    MIN_VELOCITY = 0
    MAX_VELOCITY = 127
    
    # Note names for pitch classes (C=0, C#=1, etc.)
    NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    def __init__(self, 
                 pitch: int, 
                 start_time: float, 
                 end_time: float, 
                 velocity: int = 80):
        """
        Initialize a Note object.
        
        Args:
            pitch: MIDI note number (0-127)
            start_time: Note start time in seconds
            end_time: Note end time in seconds
            velocity: MIDI velocity (0-127), default 80 for medium-loud
        
        Raises:
            ValueError: If parameters are out of valid ranges
        """
        # Validate pitch
        if not self.MIN_PITCH <= pitch <= self.MAX_PITCH:
            raise ValueError(f"Pitch must be between {self.MIN_PITCH} and {self.MAX_PITCH}, got {pitch}")
        
        # Validate velocity
        if not self.MIN_VELOCITY <= velocity <= self.MAX_VELOCITY:
            raise ValueError(f"Velocity must be between {self.MIN_VELOCITY} and {self.MAX_VELOCITY}, got {velocity}")
        
        # Validate timing
        if start_time < 0:
            raise ValueError(f"Start time must be non-negative, got {start_time}")
        
        if end_time <= start_time:
            raise ValueError(f"End time ({end_time}) must be greater than start time ({start_time})")
        
        self.pitch = int(pitch)
        self.start_time = float(start_time)
        self.end_time = float(end_time)
        self.velocity = int(velocity)
    
    @property
    def duration(self) -> float:
        """
        Get note duration in seconds.
        
        Returns:
            Duration in seconds
        """
        return self.end_time - self.start_time
    
    @property
    def frequency(self) -> float:
        """
        Get frequency in Hz corresponding to this MIDI note.
        Uses standard A4 = 440 Hz tuning.
        
        Returns:
            Frequency in Hz
        """
        # MIDI note to frequency: f = 440 * 2^((n-69)/12)
        return 440.0 * (2.0 ** ((self.pitch - 69) / 12.0))
    
    @property
    def note_name(self) -> str:
        """
        Get musical note name (e.g., 'C4', 'A#5').
        
        Returns:
            Note name string
        """
        pitch_class = self.pitch % 12
        octave = (self.pitch // 12) - 1
        return f"{self.NOTE_NAMES[pitch_class]}{octave}"
    
    def overlaps(self, other: 'Note') -> bool:
        """
        Check if this note overlaps in time with another note.
        
        Args:
            other: Another Note object
        
        Returns:
            True if notes overlap in time
        """
        return not (self.end_time <= other.start_time or self.start_time >= other.end_time)
    
    def is_active_at(self, time: float) -> bool:
        """
        Check if this note is active at a given time.
        
        Args:
            time: Time in seconds
        
        Returns:
            True if note is playing at the given time
        """
        return self.start_time <= time < self.end_time
    
    def to_dict(self) -> dict:
        """
        Convert note to dictionary representation for serialization.
        
        Returns:
            Dictionary with note attributes
        """
        return {
            'pitch': self.pitch,
            'note_name': self.note_name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'velocity': self.velocity,
            'frequency': self.frequency
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Note':
        """
        Create Note from dictionary representation.
        
        Args:
            data: Dictionary containing note attributes
        
        Returns:
            Note object
        """
        return cls(
            pitch=data['pitch'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            velocity=data.get('velocity', 80)
        )
    
    @staticmethod
    def frequency_to_pitch(frequency: float) -> int:
        """
        Convert frequency in Hz to nearest MIDI pitch number.
        
        Args:
            frequency: Frequency in Hz
        
        Returns:
            MIDI pitch number (0-127)
        """
        if frequency <= 0:
            return 0
        
        # Calculate MIDI note: n = 69 + 12 * log2(f/440)
        pitch = 69 + 12 * np.log2(frequency / 440.0)
        pitch_rounded = int(round(pitch))
        
        # Clamp to valid MIDI range
        return max(Note.MIN_PITCH, min(Note.MAX_PITCH, pitch_rounded))
    
    @staticmethod
    def pitch_to_frequency(pitch: int) -> float:
        """
        Convert MIDI pitch number to frequency in Hz.
        
        Args:
            pitch: MIDI pitch number (0-127)
        
        Returns:
            Frequency in Hz
        """
        # f = 440 * 2^((n-69)/12)
        return 440.0 * (2.0 ** ((pitch - 69) / 12.0))
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"Note(pitch={self.pitch}, note={self.note_name}, "
                f"start={self.start_time:.3f}s, duration={self.duration:.3f}s, "
                f"velocity={self.velocity})")
    
    def __eq__(self, other) -> bool:
        """Check equality based on all attributes."""
        if not isinstance(other, Note):
            return False
        return (self.pitch == other.pitch and
                abs(self.start_time - other.start_time) < 0.001 and
                abs(self.end_time - other.end_time) < 0.001 and
                self.velocity == other.velocity)
    
    def __lt__(self, other: 'Note') -> bool:
        """Compare notes by start time for sorting."""
        return self.start_time < other.start_time
