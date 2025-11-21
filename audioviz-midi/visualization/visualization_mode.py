# visualization/visualization_mode.py
"""
Base class for visualization modes in AudioViz MIDI.
Defines the interface that all visualization modes must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
import pygame
from midi import MIDIData
from utils.config import ConfigManager
from visualization.theme_manager import ThemeManager


class VisualizationMode(ABC):
    """
    Abstract base class for all visualization modes.
    
    Each mode implements the rendering pipeline differently while maintaining
    a consistent interface with the rest of the application.
    """
    
    def __init__(self, screen: pygame.Surface, config: ConfigManager, 
                 theme_manager: Optional[ThemeManager] = None):
        """
        Initialize the visualization mode.
        
        Args:
            screen: Pygame surface to render to
            config: Configuration manager
            theme_manager: Theme manager for consistent styling
        """
        self.screen = screen
        self.config = config
        self.theme_manager = theme_manager
        self.midi_data = None
        self.current_time = 0.0
        self.show_grid = True
        self.show_keyboard = True
        
    @abstractmethod
    def render(self) -> pygame.Surface:
        """
        Render the visualization for the current frame.
        
        Returns:
            The rendered surface (can be the screen or a separate surface)
        """
        pass
    
    @abstractmethod
    def set_midi_data(self, midi_data: MIDIData):
        """
        Set the MIDI data to visualize.
        
        Args:
            midi_data: MIDIData object containing notes to visualize
        """
        pass
    
    @abstractmethod
    def update_time(self, current_time: float):
        """
        Update the current playback time.
        
        Args:
            current_time: Time in seconds
        """
        pass
    
    @abstractmethod
    def set_audio_intensity(self, intensity: float):
        """
        Set the audio intensity level (for reactive effects).
        
        Args:
            intensity: Value from 0.0 to 1.0
        """
        pass
    
    @abstractmethod
    def set_beat_intensity(self, intensity: float):
        """
        Set the beat intensity level (for beat-sync effects).
        
        Args:
            intensity: Value from 0.0 to 1.0
        """
        pass
    
    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame events specific to this visualization mode.
        
        Args:
            event: The pygame event to handle
        
        Returns:
            True if event was handled, False otherwise
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get the display name of this visualization mode.
        
        Returns:
            Name string (e.g., "Classic Mode", "Liquid Mode")
        """
        pass
    
    @abstractmethod
    def reset(self):
        """Reset the visualization to initial state."""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Clean up resources used by this mode."""
        pass
