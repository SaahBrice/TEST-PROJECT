# visualization/theme_manager.py
"""
Theme Manager for AudioViz MIDI.
Manages color themes and visual styles for the piano roll visualization.
"""

from typing import Dict, Tuple, List
from utils.logger import get_logger

logger = get_logger(__name__)


class Theme:
    """
    Represents a visual theme for the piano roll.
    
    Contains all color definitions and visual parameters for a theme.
    """
    
    def __init__(self, name: str, display_name: str, description: str):
        """
        Initialize a theme.
        
        Args:
            name: Internal theme name (e.g., 'studio_dark')
            display_name: User-friendly name (e.g., 'Studio Dark')
            description: Theme description
        """
        self.name = name
        self.display_name = display_name
        self.description = description
        
        # Colors (will be set by subclasses)
        self.background_color: Tuple[int, int, int] = (30, 30, 40)
        self.grid_color: Tuple[int, int, int] = (60, 60, 70)
        self.playhead_color: Tuple[int, int, int] = (255, 100, 100)
        
        # Keyboard colors
        self.keyboard_white_key: Tuple[int, int, int] = (200, 200, 210)
        self.keyboard_black_key: Tuple[int, int, int] = (40, 40, 50)
        self.keyboard_border: Tuple[int, int, int] = (60, 60, 70)
        self.keyboard_text: Tuple[int, int, int] = (150, 150, 160)
        
        # Note colors (chromatic by default)
        self.note_colors: List[Tuple[int, int, int]] = [
            (255, 100, 100),  # C - Red
            (255, 150, 100),  # C# - Orange-Red
            (255, 200, 100),  # D - Orange
            (255, 255, 100),  # D# - Yellow
            (200, 255, 100),  # E - Yellow-Green
            (100, 255, 100),  # F - Green
            (100, 255, 200),  # F# - Cyan-Green
            (100, 200, 255),  # G - Light Blue
            (100, 100, 255),  # G# - Blue
            (150, 100, 255),  # A - Purple-Blue
            (200, 100, 255),  # A# - Purple
            (255, 100, 200),  # B - Pink
        ]
        
        # Brightness multipliers
        self.active_note_brightness: float = 1.3
        self.inactive_note_brightness: float = 0.85


class StudioDarkTheme(Theme):
    """Professional dark theme - clean and elegant for dark backgrounds."""
    
    def __init__(self):
        super().__init__(
            name='studio_dark',
            display_name='Studio Dark',
            description='Professional dark theme - clean and elegant'
        )
        
        # Darker, more refined background
        self.background_color = (26, 26, 36)  # Very dark blue-gray
        self.grid_color = (42, 42, 52)  # Subtle grid
        self.playhead_color = (255, 71, 87)  # Brighter red
        
        # Keyboard
        self.keyboard_white_key = (210, 210, 220)  # Bright white keys
        self.keyboard_black_key = (35, 35, 45)  # Very dark black keys
        self.keyboard_border = (50, 50, 60)
        self.keyboard_text = (160, 160, 170)
        
        # Slightly more saturated note colors for dark background
        self.note_colors = [
            (255, 110, 110),  # C - Bright Red
            (255, 160, 110),  # C# - Coral
            (255, 210, 110),  # D - Orange
            (255, 255, 120),  # D# - Bright Yellow
            (210, 255, 120),  # E - Lime
            (120, 255, 120),  # F - Green
            (120, 255, 210),  # F# - Aqua
            (120, 210, 255),  # G - Sky Blue
            (120, 120, 255),  # G# - Blue
            (160, 120, 255),  # A - Violet
            (210, 120, 255),  # A# - Purple
            (255, 120, 210),  # B - Pink
        ]
        
        self.active_note_brightness = 1.35
        self.inactive_note_brightness = 0.8


class StudioLightTheme(Theme):
    """Professional light theme - for bright, clean presentations."""
    
    def __init__(self):
        super().__init__(
            name='studio_light',
            display_name='Studio Light',
            description='Professional light theme - bright and clean'
        )
        
        # Light, clean background
        self.background_color = (245, 245, 250)  # Very light gray-blue
        self.grid_color = (220, 220, 230)  # Light grid lines
        self.playhead_color = (220, 20, 60)  # Deep red (Crimson)
        
        # Keyboard
        self.keyboard_white_key = (255, 255, 255)  # Pure white
        self.keyboard_black_key = (40, 40, 45)  # Dark keys
        self.keyboard_border = (180, 180, 190)
        self.keyboard_text = (80, 80, 90)  # Dark text on light
        
        # Darker, more saturated colors for light background
        self.note_colors = [
            (220, 50, 50),    # C - Deep Red
            (230, 100, 50),   # C# - Orange-Red
            (240, 150, 50),   # D - Orange
            (240, 200, 50),   # D# - Gold
            (180, 220, 50),   # E - Yellow-Green
            (80, 200, 80),    # F - Green
            (80, 200, 170),   # F# - Teal
            (80, 160, 220),   # G - Sky Blue
            (80, 80, 220),    # G# - Blue
            (130, 80, 220),   # A - Purple-Blue
            (180, 80, 220),   # A# - Purple
            (220, 80, 180),   # B - Magenta
        ]
        
        self.active_note_brightness = 1.2
        self.inactive_note_brightness = 0.7


class NeonFlashyTheme(Theme):
    """High-energy neon theme - vibrant and eye-catching."""
    
    def __init__(self):
        super().__init__(
            name='neon_flashy',
            display_name='Neon Flashy',
            description='High-energy neon theme - vibrant and eye-catching'
        )
        
        # Very dark background to make neon pop
        self.background_color = (10, 10, 15)  # Almost black
        self.grid_color = (30, 30, 40)  # Minimal grid
        self.playhead_color = (255, 0, 255)  # Magenta
        
        # Keyboard
        self.keyboard_white_key = (240, 240, 255)  # Bright white
        self.keyboard_black_key = (20, 20, 30)  # Very dark
        self.keyboard_border = (100, 100, 150)  # Neon-ish border
        self.keyboard_text = (200, 200, 255)  # Bright text
        
        # Electric, vibrant neon colors
        self.note_colors = [
            (255, 0, 100),    # C - Hot Pink
            (255, 100, 0),    # C# - Electric Orange
            (255, 200, 0),    # D - Bright Gold
            (200, 255, 0),    # D# - Electric Lime
            (0, 255, 100),    # E - Neon Green
            (0, 255, 200),    # F - Cyan
            (0, 200, 255),    # F# - Electric Blue
            (0, 100, 255),    # G - Bright Blue
            (100, 0, 255),    # G# - Electric Purple
            (200, 0, 255),    # A - Neon Purple
            (255, 0, 200),    # A# - Neon Magenta
            (255, 0, 150),    # B - Hot Pink-Purple
        ]
        
        self.active_note_brightness = 1.5  # Very bright when playing
        self.inactive_note_brightness = 0.7


class ThemeManager:
    """
    Manages themes for the visualization.
    
    Handles theme loading, switching, and color retrieval.
    """
    
    def __init__(self):
        """Initialize the theme manager."""
        # Register all available themes
        self.themes: Dict[str, Theme] = {
            'studio_dark': StudioDarkTheme(),
            'studio_light': StudioLightTheme(),
            'neon_flashy': NeonFlashyTheme(),
        }
        
        # Current theme
        self.current_theme: Theme = self.themes['studio_dark']
        
        logger.info(f"ThemeManager initialized with {len(self.themes)} themes")
    
    def get_theme(self, theme_name: str) -> Theme:
        """
        Get a theme by name.
        
        Args:
            theme_name: Name of theme to retrieve
        
        Returns:
            Theme object, or default if not found
        """
        if theme_name in self.themes:
            return self.themes[theme_name]
        else:
            logger.warning(f"Theme '{theme_name}' not found, using studio_dark")
            return self.themes['studio_dark']
    
    def set_theme(self, theme_name: str):
        """
        Set the current theme.
        
        Args:
            theme_name: Name of theme to activate
        """
        if theme_name in self.themes:
            self.current_theme = self.themes[theme_name]
            logger.info(f"Theme changed to: {self.current_theme.display_name}")
        else:
            logger.error(f"Theme '{theme_name}' not found")
    
    def get_current_theme(self) -> Theme:
        """
        Get the currently active theme.
        
        Returns:
            Current Theme object
        """
        return self.current_theme
    
    def get_available_themes(self) -> List[Dict[str, str]]:
        """
        Get list of available themes.
        
        Returns:
            List of theme info dictionaries
        """
        return [
            {
                'name': theme.name,
                'display_name': theme.display_name,
                'description': theme.description
            }
            for theme in self.themes.values()
        ]
