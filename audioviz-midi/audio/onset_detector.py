# audio/onset_detector.py
"""
Onset Detector Module for AudioViz MIDI.
Identifies note start times (onsets) within audio signals.
Analyzes amplitude envelopes and spectral changes to detect when notes begin.
"""

import librosa
import numpy as np
from typing import List, Tuple, Optional
from utils.logger import get_logger
from utils.config import ConfigManager

logger = get_logger(__name__)


class OnsetDetector:
    """
    Detects note onset times (when notes start) in audio signals.
    
    Uses librosa's onset detection algorithms to identify moments when
    new notes begin by analyzing amplitude changes and spectral flux.
    Essential for determining note boundaries in MIDI conversion.
    """
    
    # Supported onset detection methods
    METHODS = ['energy', 'rms', 'complex', 'phase', 'hfc', 'flux']
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """
        Initialize the Onset Detector.
        
        Args:
            config: Configuration manager instance. If None, uses default settings.
        """
        self.config = config or ConfigManager()
        
        # Load configuration settings (using defaults if not in config)
        self.hop_length = self.config.get('audio', 'hop_length', 512)
        self.min_note_duration = self.config.get('pitch_detection', 'min_note_duration', 0.05)
        
        # Onset detection parameters
        self.method = 'energy'  # Default method
        self.backtrack = True   # Backtrack to find precise onset time
        
        # Store last detection results
        self.onset_times = None
        self.onset_frames = None
        self.onset_strength = None
        
        logger.info("OnsetDetector initialized")
        logger.debug(f"Hop length: {self.hop_length} samples")
        logger.debug(f"Minimum note duration: {self.min_note_duration} seconds")
    
    def detect_onsets(self, 
                     audio_data: np.ndarray, 
                     sample_rate: int,
                     method: str = 'energy') -> Tuple[np.ndarray, np.ndarray]:
        """
        Detect note onset times in audio signal.
        
        Args:
            audio_data: Audio signal as numpy array (mono)
            sample_rate: Sample rate in Hz (typically 22050)
            method: Detection method - 'energy', 'rms', 'complex', 'phase', 'hfc', 'flux'
        
        Returns:
            Tuple of (onset_times, onset_strength)
            - onset_times: Array of onset times in seconds
            - onset_strength: Array of onset strength envelope over time
        """
        logger.info(f"Detecting onsets using '{method}' method...")
        logger.debug(f"Audio length: {len(audio_data)} samples ({len(audio_data)/sample_rate:.2f}s)")
        
        # Validate method
        if method not in self.METHODS:
            logger.warning(f"Invalid method '{method}', using 'energy'")
            method = 'energy'
        
        self.method = method
        
        try:
            # Compute onset strength envelope
            # This represents how likely an onset is at each time frame
            onset_env = librosa.onset.onset_strength(
                y=audio_data,
                sr=sample_rate,
                hop_length=self.hop_length,
                aggregate=np.median
            )
            
            logger.debug(f"Onset strength envelope computed: {len(onset_env)} frames")
            
            # Detect onset frames (peaks in the onset strength)
            onset_frames = librosa.onset.onset_detect(
                onset_envelope=onset_env,
                sr=sample_rate,
                hop_length=self.hop_length,
                backtrack=self.backtrack,
                units='frames'
            )
            
            logger.debug(f"Detected {len(onset_frames)} onset frames")
            
            # Convert frames to time in seconds
            onset_times = librosa.frames_to_time(
                onset_frames,
                sr=sample_rate,
                hop_length=self.hop_length
            )
            
            # Filter onsets that are too close together (merge nearby onsets)
            onset_times = self._filter_close_onsets(onset_times)
            
            logger.info(f"Onset detection complete: {len(onset_times)} onsets detected")
            
            # Store results
            self.onset_times = onset_times
            self.onset_frames = onset_frames
            self.onset_strength = onset_env
            
            return onset_times, onset_env
            
        except Exception as e:
            logger.error(f"Onset detection failed: {str(e)}")
            raise Exception(f"Onset detection error: {str(e)}")
    
    def _filter_close_onsets(self, onset_times: np.ndarray) -> np.ndarray:
        """
        Filter out onsets that are too close together.
        Prevents spurious detections from being treated as separate notes.
        
        Args:
            onset_times: Array of onset times in seconds
        
        Returns:
            Filtered array of onset times
        """
        if len(onset_times) <= 1:
            return onset_times
        
        # Keep first onset
        filtered = [onset_times[0]]
        
        # Check each subsequent onset
        for onset in onset_times[1:]:
            # If onset is far enough from previous, keep it
            if onset - filtered[-1] >= self.min_note_duration:
                filtered.append(onset)
            else:
                logger.debug(f"Filtered onset at {onset:.3f}s (too close to previous)")
        
        logger.debug(f"Filtered {len(onset_times) - len(filtered)} close onsets")
        
        return np.array(filtered)
    
    def get_onset_intervals(self, 
                           total_duration: float) -> List[Tuple[float, float]]:
        """
        Get time intervals between consecutive onsets.
        Useful for determining note durations.
        
        Args:
            total_duration: Total duration of audio in seconds
        
        Returns:
            List of tuples (start_time, end_time) for each detected segment
        """
        if self.onset_times is None or len(self.onset_times) == 0:
            logger.warning("No onsets detected yet")
            return []
        
        intervals = []
        
        # Create intervals between consecutive onsets
        for i in range(len(self.onset_times)):
            start = self.onset_times[i]
            
            # End is either the next onset or the total duration
            if i < len(self.onset_times) - 1:
                end = self.onset_times[i + 1]
            else:
                end = total_duration
            
            intervals.append((start, end))
        
        logger.debug(f"Generated {len(intervals)} onset intervals")
        
        return intervals
    
    def get_detection_stats(self) -> dict:
        """
        Get statistics about the last onset detection run.
        
        Returns:
            Dictionary containing detection statistics
        """
        if self.onset_times is None:
            logger.warning("No onset detection has been performed yet")
            return {}
        
        # Calculate statistics
        if len(self.onset_times) > 1:
            intervals = np.diff(self.onset_times)
            avg_interval = float(intervals.mean())
            min_interval = float(intervals.min())
            max_interval = float(intervals.max())
        else:
            avg_interval = 0.0
            min_interval = 0.0
            max_interval = 0.0
        
        stats = {
            'method': self.method,
            'total_onsets': len(self.onset_times),
            'first_onset': float(self.onset_times[0]) if len(self.onset_times) > 0 else 0.0,
            'last_onset': float(self.onset_times[-1]) if len(self.onset_times) > 0 else 0.0,
            'average_interval': avg_interval,
            'min_interval': min_interval,
            'max_interval': max_interval,
            'estimated_tempo': 60.0 / avg_interval if avg_interval > 0 else 0.0
        }
        
        return stats
    
    def visualize_onsets(self, onset_times: np.ndarray, duration: float) -> str:
        """
        Create a simple text visualization of onsets for debugging.
        
        Args:
            onset_times: Array of onset times in seconds
            duration: Total duration in seconds
        
        Returns:
            String representation of onset positions
        """
        # Create a timeline string
        timeline_width = 80
        timeline = ['-'] * timeline_width
        
        # Mark onsets on the timeline
        for onset in onset_times:
            position = int((onset / duration) * (timeline_width - 1))
            if 0 <= position < timeline_width:
                timeline[position] = '|'
        
        timeline_str = ''.join(timeline)
        
        # Add time markers
        time_markers = f"0s{' ' * (timeline_width - 10)}{duration:.1f}s"
        
        return f"{timeline_str}\n{time_markers}"
    
    def set_min_note_duration(self, duration: float):
        """
        Set minimum note duration threshold.
        
        Args:
            duration: Minimum duration in seconds
        
        Raises:
            ValueError: If duration is negative or too large
        """
        if duration < 0:
            raise ValueError("Duration must be non-negative")
        
        if duration > 2.0:
            logger.warning(f"Large minimum duration ({duration}s) may filter valid notes")
        
        self.min_note_duration = duration
        logger.info(f"Minimum note duration set to {duration}s")
    
    def combine_with_pitch(self, 
                          onset_times: np.ndarray,
                          frequencies: np.ndarray,
                          freq_times: np.ndarray) -> List[Tuple[float, float, float]]:
        """
        Combine onset times with pitch information to create note segments.
        
        Args:
            onset_times: Array of onset times in seconds
            frequencies: Array of detected frequencies in Hz
            freq_times: Array of time stamps for frequency detections
        
        Returns:
            List of tuples (onset_time, frequency, confidence)
            representing detected notes with their pitches
        """
        logger.debug("Combining onsets with pitch information...")
        
        notes = []
        
        for onset in onset_times:
            # Find the frequency closest to this onset time
            idx = np.argmin(np.abs(freq_times - onset))
            frequency = frequencies[idx]
            
            # Only include if a valid pitch was detected
            if frequency > 0:
                notes.append((float(onset), float(frequency), 1.0))
        
        logger.debug(f"Created {len(notes)} note segments from onsets")
        
        return notes
