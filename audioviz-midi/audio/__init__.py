# audio/__init__.py
"""
Audio processing modules for AudioViz MIDI.
Handles audio loading, pitch detection, and onset detection.
"""

from .audio_loader import AudioLoader
from .pitch_detector import PitchDetector
from .onset_detector import OnsetDetector

__all__ = ['AudioLoader', 'PitchDetector', 'OnsetDetector']
