# midi/midi_converter.py
"""
MIDI Converter Module for AudioViz MIDI.
Converts audio analysis results (pitch + onset data) into MIDI notes.
Combines frequency detection and onset timing to create Note objects.
"""

import numpy as np
from typing import List, Optional, Tuple
from midi.note import Note
from midi.midi_data import MIDIData
from utils.logger import get_logger
from utils.config import ConfigManager

logger = get_logger(__name__)


class MIDIConverter:
    """
    Converts audio analysis results into MIDI note data.
    
    Takes pitch detection output (frequencies, confidences, times) and
    onset detection output (onset times) to create structured Note objects
    with accurate timing and pitch information.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """
        Initialize the MIDI Converter.
        
        Args:
            config: Configuration manager instance. If None, uses default settings.
        """
        self.config = config or ConfigManager()
        
        # Load MIDI conversion settings from config
        self.default_velocity = self.config.get('midi', 'default_velocity', 80)
        self.min_note_duration = self.config.get('pitch_detection', 'min_note_duration', 0.05)
        self.confidence_threshold = self.config.get('pitch_detection', 'threshold', 0.1)
        
        logger.info("MIDIConverter initialized")
        logger.debug(f"Default velocity: {self.default_velocity}")
        logger.debug(f"Minimum note duration: {self.min_note_duration}s")
        logger.debug(f"Confidence threshold: {self.confidence_threshold}")
    
    def convert_to_midi(self,
                       frequencies: np.ndarray,
                       confidences: np.ndarray,
                       times: np.ndarray,
                       onset_times: Optional[np.ndarray] = None) -> MIDIData:
        """
        Convert pitch detection results to MIDI notes.
        
        Args:
            frequencies: Array of detected frequencies in Hz (0 = no pitch)
            confidences: Array of confidence scores (0.0 to 1.0)
            times: Array of time stamps in seconds for each frame
            onset_times: Optional array of detected onset times in seconds
        
        Returns:
            MIDIData object containing detected notes
        """
        logger.info("Converting audio analysis to MIDI notes...")
        logger.debug(f"Processing {len(frequencies)} frequency frames")
        
        if onset_times is not None:
            logger.debug(f"Using {len(onset_times)} detected onsets")
            notes = self._convert_with_onsets(frequencies, confidences, times, onset_times)
        else:
            logger.debug("No onsets provided, using continuous pitch tracking")
            notes = self._convert_continuous(frequencies, confidences, times)
        
        midi_data = MIDIData(notes)
        
        logger.info(f"Conversion complete: {len(midi_data)} notes created")
        stats = midi_data.get_statistics()
        if len(midi_data) > 0:
            logger.debug(f"Pitch range: {stats['pitch_range']}")
            logger.debug(f"Duration: {stats['duration']:.2f}s")
        
        return midi_data
    
    def _convert_with_onsets(self,
                            frequencies: np.ndarray,
                            confidences: np.ndarray,
                            times: np.ndarray,
                            onset_times: np.ndarray) -> List[Note]:
        """
        Convert using onset-based segmentation (preferred method).
        Each onset marks the start of a new note.
        
        Args:
            frequencies: Frequency array
            confidences: Confidence array
            times: Time array
            onset_times: Onset time array
        
        Returns:
            List of Note objects
        """
        notes = []
        
        # Process each onset to create a note
        for i, onset_start in enumerate(onset_times):
            # Determine note end time (next onset or end of audio)
            if i < len(onset_times) - 1:
                onset_end = onset_times[i + 1]
            else:
                onset_end = times[-1]
            
            # Find frequency frames within this onset interval
            mask = (times >= onset_start) & (times < onset_end)
            segment_freqs = frequencies[mask]
            segment_confs = confidences[mask]
            
            # Skip if no valid frequencies in this segment
            if len(segment_freqs) == 0:
                logger.debug(f"Skipping onset at {onset_start:.3f}s - no frequency data")
                continue
            
            # Filter out zero/invalid frequencies
            valid_mask = segment_freqs > 0
            if not np.any(valid_mask):
                logger.debug(f"Skipping onset at {onset_start:.3f}s - no valid pitch detected")
                continue
            
            valid_freqs = segment_freqs[valid_mask]
            valid_confs = segment_confs[valid_mask]
            
            # Calculate average frequency weighted by confidence
            if len(valid_freqs) > 0:
                # Use confidence-weighted average for more accurate pitch
                if valid_confs.sum() > 0:
                    avg_frequency = np.average(valid_freqs, weights=valid_confs)
                else:
                    avg_frequency = np.median(valid_freqs)
                
                avg_confidence = valid_confs.mean()
            else:
                continue
            
            # Skip if confidence too low
            if avg_confidence < self.confidence_threshold:
                logger.debug(f"Skipping onset at {onset_start:.3f}s - low confidence ({avg_confidence:.3f})")
                continue
            
            # Convert frequency to MIDI pitch
            pitch = Note.frequency_to_pitch(avg_frequency)
            
            # Calculate note duration
            duration = onset_end - onset_start
            
            # Skip if duration too short
            if duration < self.min_note_duration:
                logger.debug(f"Skipping onset at {onset_start:.3f}s - duration too short ({duration:.3f}s)")
                continue
            
            # Calculate velocity based on confidence
            velocity = self._calculate_velocity(avg_confidence)
            
            # Create note
            try:
                note = Note(
                    pitch=pitch,
                    start_time=onset_start,
                    end_time=onset_end,
                    velocity=velocity
                )
                notes.append(note)
                logger.debug(f"Created note: {note.note_name} at {onset_start:.3f}s, duration {duration:.3f}s")
            except ValueError as e:
                logger.warning(f"Failed to create note at {onset_start:.3f}s: {e}")
                continue
        
        return notes
    
    def _convert_continuous(self,
                           frequencies: np.ndarray,
                           confidences: np.ndarray,
                           times: np.ndarray) -> List[Note]:
        """
        Convert using continuous pitch tracking without onsets.
        Creates notes by detecting pitch changes and sustained regions.
        
        Args:
            frequencies: Frequency array
            confidences: Confidence array
            times: Time array
        
        Returns:
            List of Note objects
        """
        notes = []
        
        # Track current note being built
        current_pitch = None
        current_start = None
        current_freqs = []
        current_confs = []
        
        for i, (freq, conf, time) in enumerate(zip(frequencies, confidences, times)):
            # Skip invalid frequencies or low confidence
            if freq <= 0 or conf < self.confidence_threshold:
                # End current note if exists
                if current_pitch is not None:
                    note = self._finalize_note(current_pitch, current_start, time,
                                              current_freqs, current_confs)
                    if note:
                        notes.append(note)
                    
                    # Reset
                    current_pitch = None
                    current_start = None
                    current_freqs = []
                    current_confs = []
                continue
            
            # Convert frequency to pitch
            pitch = Note.frequency_to_pitch(freq)
            
            # Check if pitch changed (new note starts)
            if current_pitch is None:
                # Start new note
                current_pitch = pitch
                current_start = time
                current_freqs = [freq]
                current_confs = [conf]
            elif pitch == current_pitch:
                # Continue current note
                current_freqs.append(freq)
                current_confs.append(conf)
            else:
                # Pitch changed - finalize current note and start new one
                note = self._finalize_note(current_pitch, current_start, time,
                                          current_freqs, current_confs)
                if note:
                    notes.append(note)
                
                # Start new note
                current_pitch = pitch
                current_start = time
                current_freqs = [freq]
                current_confs = [conf]
        
        # Finalize last note if exists
        if current_pitch is not None:
            note = self._finalize_note(current_pitch, current_start, times[-1],
                                      current_freqs, current_confs)
            if note:
                notes.append(note)
        
        return notes
    
    def _finalize_note(self,
                      pitch: int,
                      start_time: float,
                      end_time: float,
                      frequencies: List[float],
                      confidences: List[float]) -> Optional[Note]:
        """
        Finalize a note with validation and quality checks.
        
        Args:
            pitch: MIDI pitch number
            start_time: Note start time
            end_time: Note end time
            frequencies: List of frequencies in this note
            confidences: List of confidences in this note
        
        Returns:
            Note object or None if invalid
        """
        duration = end_time - start_time
        
        # Check minimum duration
        if duration < self.min_note_duration:
            return None
        
        # Calculate average confidence
        avg_confidence = np.mean(confidences) if confidences else 0.0
        
        # Calculate velocity
        velocity = self._calculate_velocity(avg_confidence)
        
        try:
            note = Note(
                pitch=pitch,
                start_time=start_time,
                end_time=end_time,
                velocity=velocity
            )
            return note
        except ValueError:
            return None
    
    def _calculate_velocity(self, confidence: float) -> int:
        """
        Calculate MIDI velocity from confidence score.
        
        Args:
            confidence: Confidence score (0.0 to 1.0)
        
        Returns:
            MIDI velocity (0-127)
        """
        # Map confidence to velocity range
        # Use default as baseline, scale by confidence
        min_velocity = 40   # Minimum velocity for audible notes
        max_velocity = 127  # Maximum MIDI velocity
        
        # Linear mapping with confidence
        velocity = int(min_velocity + (max_velocity - min_velocity) * confidence)
        
        # Clamp to valid range
        velocity = max(Note.MIN_VELOCITY, min(Note.MAX_VELOCITY, velocity))
        
        return velocity
    
    def set_default_velocity(self, velocity: int):
        """
        Set default MIDI velocity for notes.
        
        Args:
            velocity: MIDI velocity (0-127)
        
        Raises:
            ValueError: If velocity is out of range
        """
        if not 0 <= velocity <= 127:
            raise ValueError(f"Velocity must be 0-127, got {velocity}")
        
        self.default_velocity = velocity
        logger.info(f"Default velocity set to {velocity}")
    
    def set_min_note_duration(self, duration: float):
        """
        Set minimum note duration threshold.
        
        Args:
            duration: Minimum duration in seconds
        
        Raises:
            ValueError: If duration is negative
        """
        if duration < 0:
            raise ValueError("Duration must be non-negative")
        
        self.min_note_duration = duration
        logger.info(f"Minimum note duration set to {duration}s")
    
    def set_confidence_threshold(self, threshold: float):
        """
        Set confidence threshold for note detection.
        
        Args:
            threshold: Confidence threshold (0.0 to 1.0)
        
        Raises:
            ValueError: If threshold is out of range
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be 0.0-1.0, got {threshold}")
        
        self.confidence_threshold = threshold
        logger.info(f"Confidence threshold set to {threshold}")
