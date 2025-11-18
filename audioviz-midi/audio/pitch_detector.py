# audio/pitch_detector.py
"""
Pitch Detector Module for AudioViz MIDI.
Extracts pitch information from audio signals using librosa.
Implements multiple detection algorithms for flexibility and accuracy.
"""

import librosa
import numpy as np
from typing import Tuple, Optional
from utils.logger import get_logger
from utils.config import ConfigManager

logger = get_logger(__name__)


class PitchDetector:
    """
    Detects pitch (frequency) information from audio signals.
    
    Supports multiple detection algorithms:
    - piptrack: Fast, good for real-time or quick processing
    - pyin: More accurate, better for offline analysis
    
    Outputs frequency arrays with confidence scores for downstream MIDI conversion.
    """
    
    # Supported pitch detection algorithms
    ALGORITHMS = ['piptrack', 'pyin']
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """
        Initialize the Pitch Detector.
        
        Args:
            config: Configuration manager instance. If None, uses default settings.
        """
        self.config = config or ConfigManager()
        
        # Load pitch detection settings from config
        self.algorithm = self.config.get('pitch_detection', 'algorithm', 'piptrack')
        self.fmin = self.config.get('pitch_detection', 'fmin', 65.0)  # C2
        self.fmax = self.config.get('pitch_detection', 'fmax', 2093.0)  # C7
        self.threshold = self.config.get('pitch_detection', 'threshold', 0.1)
        
        # Validate algorithm selection
        if self.algorithm not in self.ALGORITHMS:
            logger.warning(f"Invalid algorithm '{self.algorithm}', using 'piptrack'")
            self.algorithm = 'piptrack'
        
        logger.info(f"PitchDetector initialized with algorithm: {self.algorithm}")
        logger.debug(f"Frequency range: {self.fmin} Hz - {self.fmax} Hz")
        logger.debug(f"Confidence threshold: {self.threshold}")
        
        # Store last detection results
        self.frequencies = None
        self.confidences = None
        self.times = None
    
    def detect_pitch(self, 
                    audio_data: np.ndarray, 
                    sample_rate: int,
                    hop_length: int = 512) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Detect pitch from audio signal.
        
        Args:
            audio_data: Audio signal as numpy array (mono)
            sample_rate: Sample rate in Hz (typically 22050)
            hop_length: Number of samples between analysis frames (default: 512)
        
        Returns:
            Tuple of (frequencies, confidences, times)
            - frequencies: Array of detected frequencies in Hz (0 = no pitch detected)
            - confidences: Array of confidence scores (0.0 to 1.0)
            - times: Array of time stamps in seconds for each frame
        """
        logger.info(f"Starting pitch detection using {self.algorithm} algorithm...")
        logger.debug(f"Audio length: {len(audio_data)} samples")
        logger.debug(f"Hop length: {hop_length} samples")
        
        try:
            if self.algorithm == 'piptrack':
                frequencies, confidences, times = self._detect_piptrack(
                    audio_data, sample_rate, hop_length
                )
            elif self.algorithm == 'pyin':
                frequencies, confidences, times = self._detect_pyin(
                    audio_data, sample_rate, hop_length
                )
            else:
                raise ValueError(f"Unsupported algorithm: {self.algorithm}")
            
            # Store results
            self.frequencies = frequencies
            self.confidences = confidences
            self.times = times
            
            # Log statistics
            valid_pitches = frequencies[frequencies > 0]
            logger.info(f"Pitch detection complete")
            logger.debug(f"Total frames analyzed: {len(frequencies)}")
            logger.debug(f"Frames with pitch detected: {len(valid_pitches)}")
            if len(valid_pitches) > 0:
                logger.debug(f"Frequency range: {valid_pitches.min():.2f} - {valid_pitches.max():.2f} Hz")
                logger.debug(f"Average confidence: {confidences[frequencies > 0].mean():.3f}")
            
            return frequencies, confidences, times
            
        except Exception as e:
            logger.error(f"Pitch detection failed: {str(e)}")
            raise Exception(f"Pitch detection error: {str(e)}")
    
    def _detect_piptrack(self, 
                        audio_data: np.ndarray, 
                        sample_rate: int,
                        hop_length: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Detect pitch using librosa's piptrack algorithm.
        Fast method suitable for real-time processing.
        
        Args:
            audio_data: Audio signal
            sample_rate: Sample rate in Hz
            hop_length: Hop length in samples
        
        Returns:
            Tuple of (frequencies, confidences, times)
        """
        logger.debug("Using piptrack algorithm for pitch detection")
        
        # Compute pitch using piptrack
        pitches, magnitudes = librosa.piptrack(
            y=audio_data,
            sr=sample_rate,
            hop_length=hop_length,
            fmin=self.fmin,
            fmax=self.fmax,
            threshold=self.threshold
        )
        
        # Extract the most prominent pitch for each time frame
        num_frames = pitches.shape[1]
        frequencies = np.zeros(num_frames)
        confidences = np.zeros(num_frames)
        
        for t in range(num_frames):
            # Get the index of the maximum magnitude at this time frame
            index = magnitudes[:, t].argmax()
            
            # Extract frequency and magnitude
            freq = pitches[index, t]
            mag = magnitudes[index, t]
            
            # Only keep frequencies within our range and above threshold
            if self.fmin <= freq <= self.fmax and mag > self.threshold:
                frequencies[t] = freq
                confidences[t] = mag
            else:
                frequencies[t] = 0.0
                confidences[t] = 0.0
        
        # Normalize confidences to [0, 1] range
        if confidences.max() > 0:
            confidences = confidences / confidences.max()
        
        # Calculate time stamps for each frame
        times = librosa.frames_to_time(
            np.arange(num_frames),
            sr=sample_rate,
            hop_length=hop_length
        )
        
        return frequencies, confidences, times
    
    def _detect_pyin(self, 
                    audio_data: np.ndarray, 
                    sample_rate: int,
                    hop_length: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Detect pitch using librosa's pyin algorithm.
        More accurate method better for offline analysis.
        
        Args:
            audio_data: Audio signal
            sample_rate: Sample rate in Hz
            hop_length: Hop length in samples
        
        Returns:
            Tuple of (frequencies, confidences, times)
        """
        logger.debug("Using pyin algorithm for pitch detection")
        
        # Compute pitch using pyin
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y=audio_data,
            sr=sample_rate,
            hop_length=hop_length,
            fmin=self.fmin,
            fmax=self.fmax
        )
        
        # Replace NaN values with 0
        frequencies = np.nan_to_num(f0, nan=0.0)
        
        # Use voiced probabilities as confidence scores
        confidences = voiced_probs
        
        # Calculate time stamps for each frame
        times = librosa.frames_to_time(
            np.arange(len(frequencies)),
            sr=sample_rate,
            hop_length=hop_length
        )
        
        return frequencies, confidences, times
    
    def get_detection_stats(self) -> dict:
        """
        Get statistics about the last pitch detection run.
        
        Returns:
            Dictionary containing detection statistics
        """
        if self.frequencies is None:
            logger.warning("No pitch detection has been performed yet")
            return {}
        
        valid_pitches = self.frequencies[self.frequencies > 0]
        
        stats = {
            'algorithm': self.algorithm,
            'total_frames': len(self.frequencies),
            'frames_with_pitch': len(valid_pitches),
            'pitch_coverage': len(valid_pitches) / len(self.frequencies) if len(self.frequencies) > 0 else 0,
            'frequency_range': (float(valid_pitches.min()), float(valid_pitches.max())) if len(valid_pitches) > 0 else (0, 0),
            'average_confidence': float(self.confidences[self.frequencies > 0].mean()) if len(valid_pitches) > 0 else 0,
            'duration': float(self.times[-1]) if len(self.times) > 0 else 0
        }
        
        return stats
    
    def set_algorithm(self, algorithm: str):
        """
        Change the pitch detection algorithm.
        
        Args:
            algorithm: Algorithm name ('piptrack' or 'pyin')
        
        Raises:
            ValueError: If algorithm is not supported
        """
        if algorithm not in self.ALGORITHMS:
            raise ValueError(f"Unsupported algorithm: {algorithm}. Choose from {self.ALGORITHMS}")
        
        self.algorithm = algorithm
        logger.info(f"Algorithm changed to: {algorithm}")
    
    def set_frequency_range(self, fmin: float, fmax: float):
        """
        Set the frequency range for pitch detection.
        
        Args:
            fmin: Minimum frequency in Hz
            fmax: Maximum frequency in Hz
        
        Raises:
            ValueError: If frequency range is invalid
        """
        if fmin >= fmax:
            raise ValueError("fmin must be less than fmax")
        
        if fmin < 20 or fmax > 20000:
            logger.warning("Frequency range outside typical audio range (20-20000 Hz)")
        
        self.fmin = fmin
        self.fmax = fmax
        logger.info(f"Frequency range updated: {fmin} - {fmax} Hz")
    
    @staticmethod
    def frequency_to_note_name(frequency: float) -> str:
        """
        Convert frequency to musical note name.
        
        Args:
            frequency: Frequency in Hz
        
        Returns:
            Note name (e.g., 'A4', 'C#5') or 'N/A' if frequency is 0
        """
        if frequency <= 0:
            return 'N/A'
        
        # Note names
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Convert frequency to MIDI note number
        midi_note = 69 + 12 * np.log2(frequency / 440.0)
        midi_note_rounded = int(round(midi_note))
        
        # Get note name and octave
        note_index = midi_note_rounded % 12
        octave = (midi_note_rounded // 12) - 1
        
        return f"{note_names[note_index]}{octave}"
