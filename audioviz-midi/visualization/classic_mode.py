# visualization/classic_mode.py
"""
Classic Visualization Mode - The original waterfall piano roll.
Features rotated 90° layout with notes flowing downward, enhanced with
particles, bloom, keyboard animation, and audio-reactive effects.
"""

from visualization.piano_roll_renderer import PianoRollRenderer
from visualization.visualization_mode import VisualizationMode
import pygame


class ClassicMode(VisualizationMode):
    """
    Classic Mode uses the original PianoRollRenderer implementation.
    This maintains all existing visual features and functionality.
    """
    
    def __init__(self, screen: pygame.Surface, config, theme_manager=None):
        """
        Initialize Classic Mode.
        
        Args:
            screen: Pygame surface to render to
            config: Configuration manager
            theme_manager: Theme manager for styling
        """
        super().__init__(screen, config, theme_manager)
        
        # Use existing PianoRollRenderer as the implementation
        self.renderer = PianoRollRenderer(screen, config)
        if theme_manager:
            self.renderer.set_theme(theme_manager.current_theme)
    
    def render(self) -> pygame.Surface:
        """Render the classic waterfall visualization."""
        self.renderer.render()
        return self.screen
    
    def set_midi_data(self, midi_data):
        """Set MIDI data."""
        self.midi_data = midi_data
        self.renderer.set_midi_data(midi_data)
    
    def update_time(self, current_time: float):
        """Update playback time."""
        self.current_time = current_time
        self.renderer.set_playback_time(current_time)
    
    def set_audio_intensity(self, intensity: float):
        """Set audio intensity for reactive effects."""
        self.renderer.set_audio_intensity(intensity)
    
    def set_beat_intensity(self, intensity: float):
        """Set beat intensity for beat-sync effects."""
        self.renderer.set_beat_intensity(intensity)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame events (not used in classic mode)."""
        return False
    
    def get_name(self) -> str:
        """Get mode name."""
        return "Classic Mode"
    
    def reset(self):
        """Reset to initial state."""
        self.current_time = 0.0
        self.renderer.set_playback_time(0.0)
    
    def cleanup(self):
        """Clean up resources."""
        if hasattr(self.renderer, 'cleanup'):
            self.renderer.cleanup()
