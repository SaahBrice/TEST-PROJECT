# visualization/__init__.py
"""
Visualization modules for AudioViz MIDI.
Handles all graphics rendering and visual display.
"""

from .pygame_widget import PygameWidget
from .piano_roll_renderer import PianoRollRenderer

__all__ = ['PygameWidget', 'PianoRollRenderer']
