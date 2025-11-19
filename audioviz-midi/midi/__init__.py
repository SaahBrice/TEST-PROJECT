# midi/__init__.py
"""
MIDI modules for AudioViz MIDI.
Handles MIDI data structures, conversion, and quantization.
"""

from .note import Note
from .midi_data import MIDIData
from .midi_converter import MIDIConverter
from .note_quantizer import NoteQuantizer

__all__ = ['Note', 'MIDIData', 'MIDIConverter', 'NoteQuantizer']
