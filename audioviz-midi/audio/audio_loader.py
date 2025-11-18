# audio/audio_loader.py
"""
Audio Loader Module for AudioViz MIDI.
Handles loading and preprocessing of audio files in various formats.
Supports WAV, MP3, FLAC, and OGG formats with automatic preprocessing.
"""

import librosa
import numpy as np
import soundfile as sf
import os
from typing import Tuple, Optional
from utils.logger import get_logger
from utils.config import ConfigManager

logger = get_logger(__name__)


class AudioLoader:
    """
    Loads and preprocesses audio files for pitch detection and MIDI conversion.
    
    Performs automatic preprocessing including:
    - Format validation
    - Stereo to mono conversion
    - Resampling to target sample rate (22050 Hz)
    - Volume normalization
    """
    
    # Supported audio file formats
    SUPPORTED_FORMATS = ['.wav', '.mp3', '.flac', '.ogg']
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """
        Initialize the Audio Loader.
        
        Args:
            config: Configuration manager instance. If None, uses default settings.
        """
        self.config = config or ConfigManager()
        
        # Load audio processing settings from config
        self.target_sample_rate = self.config.get('audio', 'sample_rate', 22050)
        self.normalize = self.config.get('audio', 'normalize', True)
        self.mono_conversion = self.config.get('audio', 'mono_conversion', True)
        
        # Current loaded audio data
        self.audio_data = None
        self.sample_rate = None
        self.duration = None
        self.filename = None
        
        logger.info("AudioLoader initialized")
        logger.debug(f"Target sample rate: {self.target_sample_rate} Hz")
    
    def load_audio(self, filepath: str) -> Tuple[np.ndarray, int]:
        """
        Load and preprocess audio file.
        
        Args:
            filepath: Path to audio file
        
        Returns:
            Tuple of (audio_data, sample_rate)
            - audio_data: Numpy array of audio samples (mono, normalized)
            - sample_rate: Sample rate in Hz (22050 by default)
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
            Exception: For other audio loading errors
        """
        logger.info(f"Loading audio file: {filepath}")
        
        # Validate file exists
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            raise FileNotFoundError(f"Audio file not found: {filepath}")
        
        # Validate file format
        file_extension = os.path.splitext(filepath)[1].lower()
        if file_extension not in self.SUPPORTED_FORMATS:
            logger.error(f"Unsupported format: {file_extension}")
            raise ValueError(
                f"Unsupported audio format: {file_extension}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        try:
            # Load audio using librosa (handles all formats and preprocessing)
            logger.debug("Loading audio with librosa...")
            audio_data, sample_rate = librosa.load(
                filepath,
                sr=self.target_sample_rate,  # Resample to target rate
                mono=self.mono_conversion     # Convert to mono if needed
            )
            
            logger.info(f"Audio loaded successfully")
            logger.debug(f"Original sample rate: {sample_rate} Hz")
            logger.debug(f"Audio shape: {audio_data.shape}")
            logger.debug(f"Audio duration: {len(audio_data) / sample_rate:.2f} seconds")
            
            # Apply preprocessing
            audio_data = self._preprocess(audio_data)
            
            # Store loaded audio information
            self.audio_data = audio_data
            self.sample_rate = sample_rate
            self.duration = len(audio_data) / sample_rate
            self.filename = os.path.basename(filepath)
            
            logger.info(f"Preprocessing complete. Duration: {self.duration:.2f}s")
            
            return audio_data, sample_rate
            
        except Exception as e:
            logger.error(f"Error loading audio file: {str(e)}")
            raise Exception(f"Failed to load audio: {str(e)}")
    
    def _preprocess(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Apply preprocessing steps to audio data.
        
        Args:
            audio_data: Raw audio data array
        
        Returns:
            Preprocessed audio data array
        """
        logger.debug("Applying preprocessing...")
        
        # Normalize volume if enabled
        if self.normalize:
            audio_data = self._normalize_audio(audio_data)
            logger.debug("Audio normalized")
        
        # Additional preprocessing can be added here
        # (e.g., filtering, noise reduction)
        
        return audio_data
    
    def _normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Normalize audio to have maximum absolute value of 1.0.
        
        Args:
            audio_data: Audio data array
        
        Returns:
            Normalized audio data array
        """
        max_val = np.abs(audio_data).max()
        
        if max_val > 0:
            # Normalize to range [-1.0, 1.0]
            normalized = audio_data / max_val
            logger.debug(f"Audio normalized. Max value was: {max_val:.4f}")
            return normalized
        else:
            logger.warning("Audio contains only silence, skipping normalization")
            return audio_data
    
    def get_audio_info(self) -> dict:
        """
        Get information about currently loaded audio.
        
        Returns:
            Dictionary containing audio metadata
        """
        if self.audio_data is None:
            logger.warning("No audio loaded")
            return {}
        
        return {
            'filename': self.filename,
            'duration': self.duration,
            'sample_rate': self.sample_rate,
            'num_samples': len(self.audio_data),
            'max_amplitude': float(np.abs(self.audio_data).max()),
            'mean_amplitude': float(np.abs(self.audio_data).mean())
        }
    
    def validate_file(self, filepath: str) -> Tuple[bool, str]:
        """
        Validate audio file without loading it.
        
        Args:
            filepath: Path to audio file
        
        Returns:
            Tuple of (is_valid, message)
            - is_valid: Boolean indicating if file is valid
            - message: Description of validation result
        """
        # Check if file exists
        if not os.path.exists(filepath):
            return False, f"File not found: {filepath}"
        
        # Check file extension
        file_extension = os.path.splitext(filepath)[1].lower()
        if file_extension not in self.SUPPORTED_FORMATS:
            return False, f"Unsupported format: {file_extension}"
        
        # Check file size (warn if over 100MB)
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        if file_size_mb > 100:
            return True, f"Warning: Large file ({file_size_mb:.1f} MB), processing may be slow"
        
        return True, "File is valid"
    
    @staticmethod
    def get_supported_formats() -> list:
        """
        Get list of supported audio formats.
        
        Returns:
            List of supported file extensions
        """
        return AudioLoader.SUPPORTED_FORMATS.copy()
