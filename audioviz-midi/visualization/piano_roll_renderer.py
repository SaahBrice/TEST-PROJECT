# visualization/piano_roll_renderer.py
"""
Piano Roll Renderer for AudioViz MIDI.
Renders MIDI notes as horizontal rectangles in a scrolling piano roll visualization.
"""

import pygame
import math
from typing import Optional, Tuple
from midi import MIDIData, Note
from utils.logger import get_logger
from utils.config import ConfigManager
from visualization.theme_manager import ThemeManager, Theme


logger = get_logger(__name__)


class PianoRollRenderer:
    """
    Renders MIDI data as a piano roll visualization.
    
    Displays notes as horizontal colored rectangles positioned by time and pitch,
    with a piano keyboard reference on the left and grid lines for reference.
    """
    
    # Note names for keyboard display
    NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    # Color schemes
    CHROMATIC_COLORS = [
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
    
    def __init__(self, surface: pygame.Surface, config: Optional[ConfigManager] = None):
        """
        Initialize the piano roll renderer.
        
        Args:
            surface: Pygame surface to render on
            config: Configuration manager instance
        """
        self.surface = surface
        self.config = config or ConfigManager()
        
        # Load configuration
        self.color_scheme = self.config.get('visualization', 'color_scheme', 'chromatic')
        self.show_grid = self.config.get('visualization', 'show_grid', True)
        self.show_measure_lines = self.config.get('visualization', 'show_measure_lines', True)
        self.measure_interval = self.config.get('visualization', 'measure_interval', 4)

        self.show_keyboard = self.config.get('visualization', 'show_keyboard', True)

        # Theme system
        self.theme_manager = ThemeManager()
        theme_name = self.config.get('visualization', 'theme', 'studio_dark')
        self.theme_manager.set_theme(theme_name)
        self.current_theme = self.theme_manager.get_current_theme()

        # Colors from theme (instead of config)
        self.bg_color = self.current_theme.background_color
        self.grid_color = self.current_theme.grid_color
        self.playhead_color = self.current_theme.playhead_color

        logger.info(f"Theme loaded: {self.current_theme.display_name}")

        
        # Rendering parameters
        self.keyboard_width = 70  # Width of piano keyboard on left
        self.note_height = self.config.get('visualization', 'note_height', 12)  # Load from config
        self.pixels_per_second = 200  # Horizontal scaling factor
        
        
        # Pitch range (will be updated based on MIDI data)
        self.min_pitch = 36  # C2
        self.max_pitch = 96  # C7
        
        # Current state
        self.midi_data = None
        self.current_time = 0.0
        self.duration = 0.0
        
        # Font for text rendering
        pygame.font.init()
        self.font = pygame.font.Font(None, 18)
        self.small_font = pygame.font.Font(None, 14)
        
        logger.info("PianoRollRenderer initialized")
    
    def set_midi_data(self, midi_data: MIDIData):
        """
        Set MIDI data to visualize.
        
        Args:
            midi_data: MIDIData object containing notes
        """
        self.midi_data = midi_data
        
        if midi_data and len(midi_data) > 0:
            # Update pitch range based on actual data
            stats = midi_data.get_statistics()
            self.min_pitch = max(21, stats['pitch_range'][0] - 3)  # Add padding
            self.max_pitch = min(108, stats['pitch_range'][1] + 3)
            self.duration = stats['duration']
            
            logger.info(f"MIDI data set: {len(midi_data)} notes, "
                       f"pitch range {self.min_pitch}-{self.max_pitch}")
        else:
            logger.warning("Empty MIDI data set")
    
    def set_playback_time(self, time: float):
        """
        Set current playback time.
        
        Args:
            time: Current time in seconds
        """
        self.current_time = time
    
    def render(self):
        """Render the complete piano roll visualization."""
        if not self.midi_data:
            self._render_no_data()
            return
        
        # Clear background
        self.surface.fill(self.bg_color)
        
        # Get surface dimensions
        width, height = self.surface.get_size()
        
        # Calculate visible area (excluding keyboard)
        vis_x = self.keyboard_width if self.show_keyboard else 0
        vis_width = width - vis_x
        vis_height = height
        
        # Draw grid if enabled
        if self.show_grid:
            self._draw_grid(vis_x, vis_width, vis_height)
        
        # Draw piano keyboard if enabled
        if self.show_keyboard:
            self._draw_keyboard(vis_height)
        
        # Draw notes
        self._draw_notes(vis_x, vis_width, vis_height)
        
        # Draw playhead
        self._draw_playhead(vis_x, vis_width, vis_height)
    
    def _render_no_data(self):
        """Render message when no MIDI data is available."""
        self.surface.fill(self.bg_color)
        
        # Draw message
        text = self.font.render('No MIDI data to display', True, (100, 100, 100))
        text_rect = text.get_rect(center=(self.surface.get_width() // 2,
                                          self.surface.get_height() // 2))
        self.surface.blit(text, text_rect)
    
    def _draw_grid(self, x_offset: int, width: int, height: int):
        """
        Draw enhanced grid lines for timing and pitch reference.
        
        Implements two-tier grid system:
        - Primary grid: Octave lines (C notes) - thicker and brighter
        - Secondary grid: Semitone lines - thinner and subtle
        - Vertical grid: Time markers with dashed lines
        
        Args:
            x_offset: X offset for grid start
            width: Grid width
            height: Grid height
        """
        # HORIZONTAL LINES (Pitch Grid)
        num_pitches = self.max_pitch - self.min_pitch + 1
        
        for i in range(num_pitches + 1):
            pitch = self.min_pitch + i
            y = self._pitch_to_y(pitch, height)
            
            # PRIMARY GRID: C notes (octave markers) - thicker and brighter
            if pitch % 12 == 0:
                thickness = 2
                # Make octave lines 20% brighter than base grid color
                brightness_boost = 1.2
                color = tuple(min(int(c * brightness_boost), 255) for c in self.grid_color)
                pygame.draw.line(self.surface, color,
                               (x_offset, y), (x_offset + width, y), thickness)
            
            # SECONDARY GRID: All other notes - subtle
            else:
                thickness = 1
                color = self.grid_color
                pygame.draw.line(self.surface, color,
                               (x_offset, y), (x_offset + width, y), thickness)
        
        # VERTICAL LINES (Time Grid)
        if self.duration > 0:
            self._draw_vertical_grid(x_offset, width, height)
    
    def _draw_vertical_grid(self, x_offset: int, width: int, height: int):
        """
        Draw vertical time grid with dashed lines.
        
        Args:
            x_offset: X offset for grid start
            width: Grid width
            height: Grid height
        """
        # Calculate visible time range
        visible_duration = width / self.pixels_per_second
        start_time = max(0, self.current_time - visible_duration / 3)
        end_time = start_time + visible_duration
        
        # Draw dashed line every second
        for t in range(int(start_time), int(end_time) + 1):
            x = self._time_to_x(t, x_offset, width)
            
            if x_offset <= x <= x_offset + width:
                # Draw dashed line instead of solid
                dash_length = 6
                gap_length = 4
                total_length = dash_length + gap_length
                
                # Draw dashes from top to bottom
                y = 0
                while y < height:
                    # Draw dash segment
                    dash_end = min(y + dash_length, height)
                    pygame.draw.line(self.surface, self.grid_color,
                                   (x, y), (x, dash_end), 1)
                    y += total_length
        
        # Optional: Draw measure markers (every 4 seconds as example)
        # This creates stronger vertical lines at regular intervals
        # Draw measure markers if enabled
        if not self.show_measure_lines:
            return
            
        measure_interval = self.measure_interval  # From config

        for t in range(int(start_time), int(end_time) + 1):
            if t % measure_interval == 0 and t > 0:
                x = self._time_to_x(t, x_offset, width)
                
                if x_offset <= x <= x_offset + width:
                    # Thicker solid line for measures
                    brightness_boost = 1.15
                    color = tuple(min(int(c * brightness_boost), 255) for c in self.grid_color)
                    pygame.draw.line(self.surface, color,
                                   (x, 0), (x, height), 2)

    
    def _draw_keyboard(self, height: int):
        """
        Draw piano keyboard reference on the left side.
        
        Args:
            height: Available height for keyboard
        """
        num_pitches = self.max_pitch - self.min_pitch + 1
        
        for i in range(num_pitches):
            pitch = self.min_pitch + i
            y = self._pitch_to_y(pitch, height)
            key_height = self.note_height
            
            # Determine if this is a black key
            note_class = pitch % 12
            is_black_key = note_class in [1, 3, 6, 8, 10]  # C#, D#, F#, G#, A#
            
            # Draw key 
            if is_black_key:
                key_color = self.current_theme.keyboard_black_key
                key_width = self.keyboard_width - 18  # Narrower for black keys
            else:
                key_color = self.current_theme.keyboard_white_key
                key_width = self.keyboard_width - 8  # Slightly wider white keys

            
            pygame.draw.rect(self.surface, key_color,
                           (2, y, key_width, key_height))
            
            # Draw key border using theme color
            pygame.draw.rect(self.surface, self.current_theme.keyboard_border,
                        (2, y, key_width, key_height), 1)

            
            # Draw note name for C notes
            if note_class == 0:  # C notes
                octave = (pitch // 12) - 1
                note_name = f'C{octave}'
                text = self.small_font.render(note_name, True, self.current_theme.keyboard_text)
                # Center text horizontally in key
                text_x = 8
                text_y = y + (key_height - text.get_height()) // 2
                self.surface.blit(text, (text_x, text_y))

    
    def _draw_notes(self, x_offset: int, width: int, height: int):
        """
        Draw MIDI notes as horizontal rectangles.
        
        Args:
            x_offset: X offset for drawing area
            width: Drawing area width
            height: Drawing area height
        """
        if not self.midi_data:
            return
        
        # Calculate visible time range
        visible_duration = width / self.pixels_per_second
        start_time = max(0, self.current_time - visible_duration / 3)
        end_time = start_time + visible_duration
        
        # OPTIMIZATION: Only get notes in visible time range
        visible_notes = self.midi_data.get_notes_in_range(start_time, end_time)
        
        # OPTIMIZATION: Skip drawing if too many notes (performance fallback)
        if len(visible_notes) > 1000:
            # Draw simplified version for many notes
            logger.warning(f"Many notes visible ({len(visible_notes)}), using simplified rendering")
            for note in visible_notes[::2]:  # Draw every other note
                self._draw_note(note, x_offset, width, height)
        else:
            # Draw each note normally
            for note in visible_notes:
                self._draw_note(note, x_offset, width, height)

    
    def _draw_note(self, note: Note, x_offset: int, width: int, height: int):
        """
        Draw a single note rectangle with enhanced visual quality.
        
        Args:
            note: Note object to draw
            x_offset: X offset for drawing area
            width: Drawing area width
            height: Drawing area height
        """
        # Calculate note position and size
        note_x = self._time_to_x(note.start_time, x_offset, width)
        note_y = self._pitch_to_y(note.pitch, height)
        note_width = int(note.duration * self.pixels_per_second)
        note_height = self.note_height
        
        # Skip if note is outside visible area
        if note_x + note_width < x_offset or note_x > x_offset + width:
            return
        
        # Get note color based on scheme
        color = self._get_note_color(note)
        
        # Create note rectangle
        note_rect = pygame.Rect(note_x, note_y, note_width, note_height)
        
        # ENHANCEMENT 1: Draw shadow (for depth)
        shadow_offset = 2  # pixels
        shadow_alpha = 76  # 30% opacity (0.3 * 255)
        shadow_color = (0, 0, 0, shadow_alpha)  # Black with alpha
        shadow_rect = note_rect.copy()
        shadow_rect.x += shadow_offset
        shadow_rect.y += shadow_offset
        
        # Create temporary surface for shadow with alpha
        shadow_surface = pygame.Surface((note_width + shadow_offset, 
                                         note_height + shadow_offset), 
                                        pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, shadow_color, 
                        (shadow_offset, shadow_offset, note_width, note_height),
                        border_radius=3)
        self.surface.blit(shadow_surface, (note_x, note_y))
        
        # ENHANCEMENT 2: Draw main note body with rounded corners
        pygame.draw.rect(self.surface, color, note_rect, border_radius=3)
        
        # ENHANCEMENT 3: Draw thicker border (2px instead of 1px)
        border_color = tuple(max(0, c - 40) for c in color)
        pygame.draw.rect(self.surface, border_color, note_rect, 2, border_radius=3)
        
        # ENHANCEMENT 4: Add inner highlight for depth (optional)
        # Creates a subtle "3D" effect
        if note_height > 8:  # Only for taller notes
            highlight_color = tuple(min(255, c + 30) for c in color)
            highlight_rect = pygame.Rect(note_x + 2, note_y + 1, 
                                         note_width - 4, 1)
            pygame.draw.rect(self.surface, highlight_color, highlight_rect)
        
        # Highlight if note is currently playing
        if note.is_active_at(self.current_time):
            # Brighter glow for active notes
            glow_color = tuple(min(255, c + 80) for c in color)
            glow_rect = note_rect.inflate(4, 4)
            pygame.draw.rect(self.surface, glow_color, glow_rect, 2, border_radius=4)

    
    def _draw_playhead(self, x_offset: int, width: int, height: int):
        """
        Draw the moving playhead indicator.
        
        Args:
            x_offset: X offset for drawing area
            width: Drawing area width
            height: Drawing area height
        """
        # Playhead at 1/3 from left edge (allows seeing upcoming notes)
        playhead_x = x_offset + width // 3
        
        # Draw vertical line
        pygame.draw.line(self.surface, self.playhead_color,
                        (playhead_x, 0), (playhead_x, height), 4)
        
        # Draw small triangle at top
        triangle_points = [
            (playhead_x, 0),
            (playhead_x - 8, 15),
            (playhead_x + 8, 15)
        ]
        pygame.draw.polygon(self.surface, self.playhead_color, triangle_points)
    
    def _get_note_color(self, note: Note) -> Tuple[int, int, int]:
        """
        Get color for a note based on current color scheme.
        
        Args:
            note: Note object
        
        Returns:
            RGB color tuple
        """
        if self.color_scheme == 'chromatic':
            # Color by pitch class using theme colors
            pitch_class = note.pitch % 12
            return self.current_theme.note_colors[pitch_class]

        
        elif self.color_scheme == 'octave':
            # Color by octave
            octave = (note.pitch // 12) % 8
            hue = octave / 8.0
            return self._hsv_to_rgb(hue, 0.8, 0.9)
        
        elif self.color_scheme == 'velocity':
            # Color by velocity (brightness)
            intensity = note.velocity / 127.0
            base_hue = 0.6  # Blue
            return self._hsv_to_rgb(base_hue, 0.7, intensity)
        
        else:  # Default to chromatic
            pitch_class = note.pitch % 12
            return self.CHROMATIC_COLORS[pitch_class]
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """
        Convert HSV color to RGB.
        
        Args:
            h: Hue (0.0 to 1.0)
            s: Saturation (0.0 to 1.0)
            v: Value (0.0 to 1.0)
        
        Returns:
            RGB color tuple
        """
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))
    
    def _pitch_to_y(self, pitch: int, height: int) -> int:
        """
        Convert MIDI pitch to Y coordinate with spacing between rows.
        
        Args:
            pitch: MIDI pitch number
            height: Available height
        
        Returns:
            Y coordinate in pixels
        """
        num_pitches = self.max_pitch - self.min_pitch + 1
        pitch_index = self.max_pitch - pitch  # Invert (higher pitch = lower Y)
        
        # Calculate base position
        note_spacing = 1  # 1px gap between notes
        total_note_height = self.note_height + note_spacing
        
        # Position with spacing included
        y_position = int((pitch_index / num_pitches) * height)
        
        return y_position

    
    def _time_to_x(self, time: float, x_offset: int, width: int) -> int:
        """
        Convert time to X coordinate (scrolling with playhead).
        
        Args:
            time: Time in seconds
            x_offset: X offset for drawing area
            width: Drawing area width
        
        Returns:
            X coordinate in pixels
        """
        # Playhead is at 1/3 from left
        playhead_x = x_offset + width // 3
        
        # Calculate offset from current time
        time_offset = time - self.current_time
        pixel_offset = int(time_offset * self.pixels_per_second)
        
        return playhead_x + pixel_offset

    def set_theme(self, theme_name: str):
        """
        Switch to a different theme.
        
        Args:
            theme_name: Name of theme to activate
        """
        self.theme_manager.set_theme(theme_name)
        self.current_theme = self.theme_manager.get_current_theme()
        
        # Update colors from new theme
        self.bg_color = self.current_theme.background_color
        self.grid_color = self.current_theme.grid_color
        self.playhead_color = self.current_theme.playhead_color
        
        logger.info(f"Theme switched to: {self.current_theme.display_name}")
