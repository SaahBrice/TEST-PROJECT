# audio/__init__.py
"""
Audio processing modules for AudioViz MIDI.
Handles audio loading, pitch detection, and onset detection.
"""

from .audio_loader import AudioLoader

__all__ = ['AudioLoader']
