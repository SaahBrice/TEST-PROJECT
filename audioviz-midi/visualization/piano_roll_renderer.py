# visualization/piano_roll_renderer.py
"""
Piano Roll Renderer for AudioViz MIDI.
Renders MIDI notes as vertical rectangles in a scrolling piano roll visualization (waterfall style).
"""

import pygame
import math
from typing import Optional, Tuple
from midi import MIDIData, Note
from utils.logger import get_logger
from utils.config import ConfigManager
from visualization.theme_manager import ThemeManager, Theme


logger = get_logger(__name__)


class Particle:
    """Represents a single particle in the particle system."""
    
    def __init__(self, x: float, y: float, vx: float, vy: float, 
                 color: Tuple[int, int, int], lifetime: float = 1.0):
        """
        Initialize a particle.
        
        Args:
            x: X position
            y: Y position
            vx: X velocity
            vy: Y velocity
            color: RGB color tuple
            lifetime: How long particle lives (seconds)
        """
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.age = 0.0
    
    def update(self, dt: float) -> bool:
        """
        Update particle position and age.
        
        Args:
            dt: Delta time in seconds
        
        Returns:
            True if particle is still alive, False if expired
        """
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.age += dt
        
        return self.age < self.lifetime
    
    def get_alpha(self) -> int:
        """Get current alpha value based on age (fades out)."""
        progress = self.age / self.lifetime
        return int((1.0 - progress) * 255)


class Chord:
    """Chord detection and naming utility."""
    
    # Common chord patterns (semitone intervals from root)
    CHORD_PATTERNS = {
        'major': (0, 4, 7),
        'minor': (0, 3, 7),
        'major7': (0, 4, 7, 11),
        'minor7': (0, 3, 7, 10),
        'dom7': (0, 4, 7, 10),
        'maj7': (0, 4, 7, 11),
        'dim': (0, 3, 6),
        'aug': (0, 4, 8),
        'sus2': (0, 2, 7),
        'sus4': (0, 5, 7),
        'add9': (0, 4, 7, 14),
        '7sus4': (0, 5, 7, 10),
    }
    
    NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    @staticmethod
    def detect_chord(pitches: list) -> Optional[str]:
        """
        Detect chord from a list of MIDI pitches.
        
        Args:
            pitches: List of MIDI note numbers
        
        Returns:
            Chord name string or None if no match found
        """
        if len(pitches) < 2:
            return None
        
        # Normalize pitches to single octave
        pitches = sorted(set([p % 12 for p in pitches]))
        
        if len(pitches) < 2:
            return None
        
        # Try to find chord starting from lowest note
        for root_idx, root in enumerate(pitches):
            # Calculate intervals from this root
            intervals = tuple(sorted(set([(p - root) % 12 for p in pitches])))
            
            # Check against known patterns
            for chord_type, pattern in Chord.CHORD_PATTERNS.items():
                if intervals == pattern:
                    root_name = Chord.NOTE_NAMES[root]
                    return f"{root_name} {chord_type}"
        
        return None





class PianoRollRenderer:
    """
    Renders MIDI data as a piano roll visualization.
    
    Displays notes as vertical colored rectangles that flow from top to bottom (waterfall style)
    positioned by time (Y axis) and pitch (X axis), with a piano keyboard reference at the bottom
    and grid lines for reference.
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

        
        # Rendering parameters (rotated 90° clockwise: keyboard at bottom, notes flow vertically)
        self.keyboard_height = 70  # Height of piano keyboard at bottom (was width on left)
        self.note_width = self.config.get('visualization', 'note_height', 12)  # Width per pitch (was note_height)
        self.pixels_per_second = 200  # Vertical scaling factor (was horizontal)
        
        
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
        
        # Visual enhancements configuration
        self.enable_3d_perspective = self.config.get('visualization', 'enable_3d_perspective', True)
        self.enable_ghosted_notes = self.config.get('visualization', 'enable_ghosted_notes', True)
        self.ghosted_lookahead_time = 5.0  # Show 5 seconds ahead in ghosted style
        self.enable_motion_blur = self.config.get('visualization', 'enable_motion_blur', True)
        self.enable_audio_reactive_bg = self.config.get('visualization', 'enable_audio_reactive_bg', True)
        self.enable_waveform = self.config.get('visualization', 'enable_waveform', True)
        
        # Audio reactivity state
        self.audio_intensity = 0.0  # Range 0.0 to 1.0
        self.bg_pulse_alpha = 0.0  # For pulsing background effect
        
        # Trail rendering for motion blur
        self.trail_segments = {}  # Store trail segments per note
        
        # Advanced effects configuration
        self.enable_particles = self.config.get('visualization', 'enable_particles', True)
        self.enable_keyboard_animation = self.config.get('visualization', 'enable_keyboard_animation', True)
        self.enable_bloom = self.config.get('visualization', 'enable_bloom', True)
        self.enable_chord_labels = self.config.get('visualization', 'enable_chord_labels', True)
        self.enable_beat_effects = self.config.get('visualization', 'enable_beat_effects', True)
        
        # Particle system
        self.particles = []  # List of active particles
        
        # Keyboard animation state
        self.key_press_states = {}  # Track which keys are pressed and for how long
        
        # Chord detection state
        self.current_chord = None
        self.chord_display_time = 0.0
        self.chord_display_duration = 1.5  # Show chord name for 1.5 seconds
        
        # Beat effect state
        self.beat_intensity = 0.0  # Current beat intensity (0.0 to 1.0)
        self.camera_offset_x = 0.0  # X offset from camera shake
        self.camera_offset_y = 0.0  # Y offset from camera shake
        self.zoom_scale = 1.0  # Zoom scaling factor
        
        # Track recently activated notes for effects
        self._recently_activated_notes = []  # Notes that just started playing this frame
        self._last_frame_time = 0.0
        
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
    
    def set_audio_intensity(self, intensity: float):
        """
        Set audio intensity for reactive background effects.
        
        Args:
            intensity: Audio intensity (0.0 to 1.0)
        """
        self.audio_intensity = max(0.0, min(1.0, intensity))
        # Update pulsing background alpha
        self.bg_pulse_alpha = self.audio_intensity * 0.3
    
    def set_beat_intensity(self, intensity: float):
        """
        Set beat intensity for rhythm effects (camera shake, zoom pulse).
        
        Args:
            intensity: Beat intensity (0.0 to 1.0)
        """
        self.beat_intensity = max(0.0, min(1.0, intensity))
        
        # Update camera shake
        if self.enable_beat_effects and self.beat_intensity > 0:
            shake_amount = self.beat_intensity * 5
            self.camera_offset_x = (math.sin(self.current_time * 50) * shake_amount)
            self.camera_offset_y = (math.cos(self.current_time * 40) * shake_amount)
            
            # Update zoom pulse
            self.zoom_scale = 1.0 + self.beat_intensity * 0.05
    
    def render(self):
        """Render the complete piano roll visualization."""
        if not self.midi_data:
            self._render_no_data()
            return
        
        # Update particles
        self.particles = [p for p in self.particles if p.update(1.0/60.0)]
        
        # Detect current chords and active notes
        active_notes = self.midi_data.get_notes_at_time(self.current_time)
        
        # Detect notes reaching the keyboard (for keyboard hit effects)
        # Instead of triggering at note.start_time, trigger when note reaches bottom keyboard
        self._recently_activated_notes = []
        
        # Get all notes in the MIDI data to check their keyboard-hit times
        all_notes = self.midi_data.get_notes_in_range(
            self.current_time - 1.0,  # Look back 1 second
            self.current_time + 0.1   # Look ahead 100ms
        )
        
        for note in all_notes:
            # Calculate when this note hits the keyboard
            keyboard_hit_time = self.calculate_note_keyboard_hit_time(note, self.surface.get_height())
            
            # Check if this note is hitting the keyboard NOW (within this frame)
            time_since_last_frame = self.current_time - self._last_frame_time
            if time_since_last_frame < 0.05:  # Within 50ms (one frame at 60fps)
                if abs(keyboard_hit_time - self.current_time) < 0.02:  # Just hit keyboard
                    self._recently_activated_notes.append(note)
                    
                    # Trigger effects AT KEYBOARD POSITION
                    if self.enable_particles:
                        note_x = self._pitch_to_x(note.pitch, self.surface.get_width())
                        # Particles burst AT the keyboard (bottom of screen)
                        keyboard_y = self.surface.get_height() - self.keyboard_height
                        color = self._get_note_color(note)
                        self._create_particle_burst(
                            note_x + self.note_width // 2,
                            keyboard_y - 5,  # Just above keyboard for visibility
                            color,
                            count=15
                        )
        
        self._last_frame_time = self.current_time
        
        # Update keyboard animation states based on KEYBOARD-HIT time
        # Keys should animate when notes reach the keyboard, not when they start
        for note in self._recently_activated_notes:
            # These notes just hit the keyboard, so animate the key
            self.key_press_states[note.pitch] = 0.0  # Start press animation
        
        # Update chord display based on notes hitting keyboard
        if self._recently_activated_notes and len(self._recently_activated_notes) >= 2:
            active_pitches = [n.pitch for n in self._recently_activated_notes]
            new_chord = Chord.detect_chord(active_pitches)
            if new_chord != self.current_chord:
                self.current_chord = new_chord
                self.chord_display_time = 0.0
        else:
            if not self._recently_activated_notes:
                self.current_chord = None
        
        if self.current_chord:
            self.chord_display_time += 1.0/60.0
        
        # Decay other keys
        for pitch in list(self.key_press_states.keys()):
            self.key_press_states[pitch] = self.key_press_states.get(pitch, 0.0) + 1.0/60.0
            if self.key_press_states[pitch] > 0.5:  # Release animation time (faster now)
                del self.key_press_states[pitch]
        
        # Clear background
        self.surface.fill(self.bg_color)
        
        # Get surface dimensions
        width, height = self.surface.get_size()
        
        # Calculate visible area (excluding keyboard at bottom)
        vis_y = 0
        vis_height = height - (self.keyboard_height if self.show_keyboard else 0)
        vis_width = width
        
        # Apply camera effects (shake and zoom)
        if self.enable_beat_effects:
            # Apply zoom by scaling the surface content (we'll clip to the visible area)
            pass  # Zoom handled in coordinate calculations
        
        # Draw audio-reactive background if enabled
        if self.enable_audio_reactive_bg:
            self._draw_reactive_background(vis_width, vis_height)
        
        # Draw waveform if enabled
        if self.enable_waveform:
            self._draw_waveform_layer(vis_width, vis_height)
        
        # Draw grid if enabled
        if self.show_grid:
            self._draw_grid(vis_width, vis_height)
        
        # Draw ghosted upcoming notes if enabled
        if self.enable_ghosted_notes:
            self._draw_ghosted_notes(vis_width, vis_height)
        
        # Draw piano keyboard if enabled (now at bottom)
        if self.show_keyboard:
            self._draw_keyboard(width)
        
        # Draw notes with 3D perspective
        self._draw_notes(vis_width, vis_height, active_notes)
        
        # Draw bloom effect on active notes
        if self.enable_bloom:
            self._draw_bloom_on_notes(vis_width, vis_height, active_notes)
        
        # Draw particles
        if self.enable_particles:
            self._draw_particles()
        
        # Draw chord label
        if self.enable_chord_labels and self.current_chord and self.chord_display_time < self.chord_display_duration:
            self._draw_chord_label(vis_width)
    
    def _render_no_data(self):
        """Render message when no MIDI data is available."""
        self.surface.fill(self.bg_color)
        
        # Draw message
        text = self.font.render('No MIDI data to display', True, (100, 100, 100))
        text_rect = text.get_rect(center=(self.surface.get_width() // 2,
                                          self.surface.get_height() // 2))
        self.surface.blit(text, text_rect)
    
    def _draw_grid(self, width: int, height: int):
        """
        Draw enhanced grid lines for timing and pitch reference.
        
        Rotated layout: 
        - Vertical lines (on screen) are now time markers
        - Horizontal lines (on screen) are now pitch markers
        
        Args:
            width: Grid width
            height: Grid height
        """
        # HORIZONTAL LINES (Pitch Grid)
        num_pitches = self.max_pitch - self.min_pitch + 1
        
        for i in range(num_pitches + 1):
            pitch = self.min_pitch + i
            x = self._pitch_to_x(pitch, width)
            
            # PRIMARY GRID: C notes (octave markers) - thicker and brighter
            if pitch % 12 == 0:
                thickness = 2
                # Make octave lines 20% brighter than base grid color
                brightness_boost = 1.2
                color = tuple(min(int(c * brightness_boost), 255) for c in self.grid_color)
                pygame.draw.line(self.surface, color,
                               (x, 0), (x, height), thickness)
            
            # SECONDARY GRID: All other notes - subtle
            else:
                thickness = 1
                color = self.grid_color
                pygame.draw.line(self.surface, color,
                               (x, 0), (x, height), thickness)
        
        # HORIZONTAL LINES (Time Grid)
        if self.duration > 0:
            self._draw_horizontal_grid(width, height)
    
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

    def _draw_horizontal_grid(self, width: int, height: int):
        """
        Draw horizontal time grid with dashed lines (for rotated layout).
        
        Args:
            width: Grid width
            height: Grid height
        """
        # Calculate visible time range
        visible_duration = height / self.pixels_per_second
        start_time = max(0, self.current_time - visible_duration / 3)
        end_time = start_time + visible_duration
        
        # Draw dashed line every second
        for t in range(int(start_time), int(end_time) + 1):
            y = self._time_to_y(t, height)
            
            if 0 <= y <= height:
                # Draw dashed line instead of solid
                dash_length = 6
                gap_length = 4
                total_length = dash_length + gap_length
                
                # Draw dashes from left to right
                x = 0
                while x < width:
                    # Draw dash segment
                    dash_end = min(x + dash_length, width)
                    pygame.draw.line(self.surface, self.grid_color,
                                   (x, y), (dash_end, y), 1)
                    x += total_length
        
        # Optional: Draw measure markers
        if not self.show_measure_lines:
            return
            
        measure_interval = self.measure_interval

        for t in range(int(start_time), int(end_time) + 1):
            if t % measure_interval == 0 and t > 0:
                y = self._time_to_y(t, height)
                
                if 0 <= y <= height:
                    # Thicker solid line for measures
                    brightness_boost = 1.15
                    color = tuple(min(int(c * brightness_boost), 255) for c in self.grid_color)
                    pygame.draw.line(self.surface, color,
                                   (0, y), (width, y), 2)

    
    def _draw_keyboard(self, height: int):
        """
        Draw piano keyboard reference at the bottom (horizontal layout) with dramatic press animations.
        
        Args:
            height: Available width for keyboard display (width parameter)
        """
        width = height  # Parameter is actually surface width
        num_pitches = self.max_pitch - self.min_pitch + 1
        keyboard_y = self.surface.get_height() - self.keyboard_height
        
        for i in range(num_pitches):
            pitch = self.min_pitch + i
            x = self._pitch_to_x(pitch, width)
            key_width = self.note_width
            
            # Determine if this is a black key
            note_class = pitch % 12
            is_black_key = note_class in [1, 3, 6, 8, 10]  # C#, D#, F#, G#, A#
            
            # Get key animation state (0.0 = pressed, 0.5+ = released)
            press_state = self.key_press_states.get(pitch, 1.0)  # 1.0 = released
            
            # Dramatic animation: fast press and slower release
            if press_state < 0.3:
                # Fully pressed (0-0.3 range)
                press_amount = 0.0
            elif press_state < 0.5:
                # Quick release phase (0.3-0.5 range)
                press_amount = (press_state - 0.3) / 0.2
            else:
                # Fully released
                press_amount = 1.0
            
            # DRAMATIC DEPTH: 0-30 pixels (was 0-8)
            key_depth = int(30 * (1.0 - press_amount))
            animated_keyboard_y = keyboard_y + key_depth
            
            # Get base key colors
            if is_black_key:
                base_key_color = self.current_theme.keyboard_black_key
                key_height = self.keyboard_height - 18 - key_depth
            else:
                base_key_color = self.current_theme.keyboard_white_key
                key_height = self.keyboard_height - 8 - key_depth
            
            # COLOR CHANGE when pressed: brighten significantly
            if press_state < 0.5:
                # Pressed: increase brightness dramatically
                brightness_boost = 1.5
                key_color = tuple(min(255, int(c * brightness_boost)) for c in base_key_color)
            else:
                key_color = base_key_color
            
            pygame.draw.rect(self.surface, key_color,
                           (x, animated_keyboard_y, key_width, key_height))
            
            # DRAMATIC SHADOWS under pressed keys
            if key_depth > 0:
                # Much stronger shadow (alpha 120 instead of 40)
                shadow_alpha = 120
                shadow_height = key_depth
                shadow_color = (0, 0, 0, shadow_alpha)
                shadow_surface = pygame.Surface((key_width, shadow_height), pygame.SRCALPHA)
                pygame.draw.rect(shadow_surface, shadow_color, (0, 0, key_width, shadow_height))
                self.surface.blit(shadow_surface, (x, animated_keyboard_y + key_height))
                
                # Add additional highlight shadow beneath
                inner_shadow = (0, 0, 0, 60)
                inner_surface = pygame.Surface((key_width, int(shadow_height / 2)), pygame.SRCALPHA)
                pygame.draw.rect(inner_surface, inner_shadow, 
                               (0, 0, key_width, int(shadow_height / 2)))
                self.surface.blit(inner_surface, (x, animated_keyboard_y + key_height + int(shadow_height / 2)))
            
            # DRAMATIC BORDER: thicker and more visible
            if press_state < 0.5:
                # Darker border when pressed
                border_color = tuple(max(0, c - 60) for c in key_color)
                border_width = 3
            else:
                border_color = self.current_theme.keyboard_border
                border_width = 2
            
            pygame.draw.rect(self.surface, border_color,
                        (x, animated_keyboard_y, key_width, key_height), border_width)
            
            # Draw note name for C notes
            if note_class == 0:  # C notes
                octave = (pitch // 12) - 1
                note_name = f'C{octave}'
                text = self.small_font.render(note_name, True, self.current_theme.keyboard_text)
                # Center text in key, adjust for key press
                text_x = x + (key_width - text.get_width()) // 2
                text_y = animated_keyboard_y + 8
                self.surface.blit(text, (text_x, text_y))

    
    def _draw_notes(self, width: int, height: int, active_notes: list = None):
        """
        Draw MIDI notes as vertical rectangles (notes flow top to bottom).
        
        Args:
            width: Drawing area width
            height: Drawing area height
            active_notes: List of currently active notes (optional)
        """
        if not self.midi_data:
            return
        
        # Calculate visible time range
        visible_duration = height / self.pixels_per_second
        start_time = max(0, self.current_time - visible_duration / 3)
        end_time = start_time + visible_duration
        
        # OPTIMIZATION: Only get notes in visible time range
        visible_notes = self.midi_data.get_notes_in_range(start_time, end_time)
        
        # OPTIMIZATION: Skip drawing if too many notes (performance fallback)
        if len(visible_notes) > 1000:
            # Draw simplified version for many notes
            logger.warning(f"Many notes visible ({len(visible_notes)}), using simplified rendering")
            for note in visible_notes[::2]:  # Draw every other note
                self._draw_note(note, width, height, active_notes or [])
        else:
            # Draw each note normally
            for note in visible_notes:
                self._draw_note(note, width, height, active_notes or [])

    
    def _draw_note(self, note: Note, width: int, height: int, active_notes: list = None):
        """
        Draw a single note rectangle with enhanced visual quality and 3D perspective.
        
        Args:
            note: Note object to draw
            width: Drawing area width
            height: Drawing area height
            active_notes: List of currently active notes (optional)
        """
        # Calculate note position and size (rotated 90°)
        note_x = self._pitch_to_x(note.pitch, width)
        note_y = self._time_to_y(note.start_time, height)
        note_width = self.note_width
        note_height = int(note.duration * self.pixels_per_second)
        
        # Skip if note is outside visible area
        if note_y + note_height < 0 or note_y > height:
            return
        
        # Get note color based on scheme
        color = self._get_note_color(note)
        
        # Calculate 3D perspective scale
        perspective_scale = self._calculate_perspective_scale(note, height)
        
        # Apply perspective scaling to dimensions
        scaled_note_width = int(note_width * perspective_scale)
        scaled_note_height = int(note_height * perspective_scale)
        
        # Adjust position to keep note centered during scaling
        scaled_note_x = note_x + (note_width - scaled_note_width) // 2
        scaled_note_y = note_y + (note_height - scaled_note_height) // 2
        
        # Draw motion blur trail if enabled
        if self.enable_motion_blur:
            self._draw_motion_blur_trail(note, scaled_note_x, scaled_note_y, 
                                        scaled_note_width, scaled_note_height, color)
        
        # Create note rectangle
        note_rect = pygame.Rect(scaled_note_x, scaled_note_y, scaled_note_width, scaled_note_height)
        
        # ENHANCEMENT 1: Draw shadow (for depth)
        shadow_offset = 2  # pixels
        shadow_alpha = 76  # 30% opacity (0.3 * 255)
        shadow_color = (0, 0, 0, shadow_alpha)  # Black with alpha
        shadow_rect = note_rect.copy()
        shadow_rect.x += shadow_offset
        shadow_rect.y += shadow_offset
        
        # Create temporary surface for shadow with alpha
        shadow_surface = pygame.Surface((scaled_note_width + shadow_offset, 
                                         scaled_note_height + shadow_offset), 
                                        pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, shadow_color, 
                        (shadow_offset, shadow_offset, scaled_note_width, scaled_note_height),
                        border_radius=3)
        self.surface.blit(shadow_surface, (scaled_note_x, scaled_note_y))
        
        # ENHANCEMENT 2: Draw main note body with rounded corners
        pygame.draw.rect(self.surface, color, note_rect, border_radius=3)
        
        # ENHANCEMENT 3: Draw thicker border (2px instead of 1px)
        border_color = tuple(max(0, c - 40) for c in color)
        pygame.draw.rect(self.surface, border_color, note_rect, 2, border_radius=3)
        
        # ENHANCEMENT 4: Add inner highlight for depth (optional)
        # Creates a subtle "3D" effect
        if scaled_note_width > 8:  # Only for wider notes
            highlight_color = tuple(min(255, c + 30) for c in color)
            highlight_rect = pygame.Rect(scaled_note_x + 1, scaled_note_y + 2, 
                                         1, scaled_note_height - 4)
            pygame.draw.rect(self.surface, highlight_color, highlight_rect)
        
        # Highlight if note is currently playing
        if note.is_active_at(self.current_time):
            # Brighter glow for active notes
            glow_color = tuple(min(255, c + 80) for c in color)
            glow_rect = note_rect.inflate(4, 4)
            pygame.draw.rect(self.surface, glow_color, glow_rect, 2, border_radius=4)

    
    def _draw_playhead(self, width: int, height: int):
        """
        Playhead has been removed - all visual effects now happen directly on notes.
        This method is kept for backward compatibility but does nothing.
        """
        pass
    
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
        Convert MIDI pitch to Y coordinate with spacing between rows (deprecated - for backwards compatibility).
        
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
        total_note_height = self.note_width + note_spacing
        
        # Position with spacing included
        y_position = int((pitch_index / num_pitches) * height)
        
        return y_position

    def _pitch_to_x(self, pitch: int, width: int) -> int:
        """
        Convert MIDI pitch to X coordinate (rotated layout).
        
        Args:
            pitch: MIDI pitch number
            width: Available width
        
        Returns:
            X coordinate in pixels
        """
        num_pitches = self.max_pitch - self.min_pitch + 1
        pitch_index = pitch - self.min_pitch  # Lower pitch = lower X
        
        # Calculate position
        x_position = int((pitch_index / num_pitches) * width)
        
        return x_position

    def _time_to_x(self, time: float, x_offset: int, width: int) -> int:
        """
        Convert time to X coordinate (scrolling with playhead) - deprecated for rotated layout.
        
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

    def _time_to_y(self, time: float, height: int) -> int:
        """
        Convert time to Y coordinate (vertical flow for rotated layout).
        Notes flow from top to bottom (like falling rain/waterfall).
        
        Args:
            time: Time in seconds
            height: Drawing area height
        
        Returns:
            Y coordinate in pixels
        """
        # Playhead is at 2/3 from top (notes flow down toward it)
        playhead_y = (2 * height) // 3
        
        # Calculate offset from current time
        # Earlier notes (negative offset) should be HIGHER on screen (smaller Y)
        # Later notes (positive offset) should be LOWER on screen (larger Y)
        # We need to INVERT the pixel_offset so that negative offsets go UP
        time_offset = time - self.current_time
        pixel_offset = int(time_offset * self.pixels_per_second)
        
        # Invert: earlier times (negative offset) move UP the screen
        return playhead_y - pixel_offset
    
    def calculate_note_keyboard_hit_time(self, note: Note, height: int) -> float:
        """
        Calculate when a note visually reaches and hits the piano keyboard at the bottom.
        
        The keyboard is positioned at the bottom of the screen (at y = height - keyboard_height).
        Notes start at their start_time Y position and flow downward.
        
        Args:
            note: The MIDI note to calculate for
            height: Total visualization height (including keyboard)
        
        Returns:
            The time (in seconds) when the note visually reaches the keyboard
        """
        # Keyboard is at the bottom
        keyboard_y = height - self.keyboard_height
        
        # Calculate where the note starts (Y position)
        note_start_y = self._time_to_y(note.start_time, height)
        
        # The note moves downward as time progresses
        # Note that just started is at note_start_y
        # As current_time increases, notes move down the screen
        # The note reaches keyboard when its Y position equals keyboard_y
        
        # Using the _time_to_y formula: y = playhead_y - (time - current_time) * pixels_per_second
        # We want to find when: y = keyboard_y
        # So: keyboard_y = playhead_y - (note_hit_time - current_time) * pixels_per_second
        # Solving for note_hit_time:
        # (note_hit_time - current_time) * pixels_per_second = playhead_y - keyboard_y
        # note_hit_time = current_time + (playhead_y - keyboard_y) / pixels_per_second
        
        playhead_y = (2 * height) // 3
        pixel_distance = playhead_y - keyboard_y  # How many pixels down from playhead to keyboard
        time_to_keyboard = pixel_distance / self.pixels_per_second  # How many seconds to travel
        
        # The note reaches the keyboard at:
        note_keyboard_hit_time = note.start_time + time_to_keyboard
        
        return note_keyboard_hit_time

    def _draw_reactive_background(self, width: int, height: int):
        """
        Draw audio-reactive pulsing background.
        
        Args:
            width: Drawable width
            height: Drawable height
        """
        if self.audio_intensity <= 0:
            return
        
        # Create a pulsing overlay that responds to audio intensity
        overlay_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Color based on theme
        pulse_color = self.playhead_color
        
        # Alpha pulsates with audio intensity
        alpha = int(self.bg_pulse_alpha * 255)
        pulse_color_with_alpha = (*pulse_color[:3], alpha)
        
        # Draw subtle pulse effect
        pygame.draw.rect(overlay_surface, pulse_color_with_alpha, (0, 0, width, height))
        self.surface.blit(overlay_surface, (0, 0))

    def _draw_waveform_layer(self, width: int, height: int):
        """
        Draw audio waveform as a semi-transparent backdrop.
        
        Args:
            width: Drawable width
            height: Drawable height
        """
        # Create vertical waveform visualization
        waveform_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Generate smooth vertical waveform pattern
        waveform_color = (*self.grid_color, 30)  # Semi-transparent grid color
        
        # Draw waveform bars at different pitch frequencies
        num_pitches = self.max_pitch - self.min_pitch + 1
        bar_width = max(1, width // (num_pitches // 4))
        
        for i in range(0, width, bar_width):
            # Vary the bar height for visual interest
            frequency = (i / width) * 2 * math.pi
            bar_height = int(height * 0.15 * (math.sin(frequency) + 1) / 2)
            bar_y = (height - bar_height) // 2
            
            pygame.draw.rect(waveform_surface, waveform_color, (i, bar_y, bar_width, bar_height))
        
        self.surface.blit(waveform_surface, (0, 0))

    def _draw_ghosted_notes(self, width: int, height: int):
        """
        Draw upcoming notes in ghosted/transparent style with gradient fade-in.
        
        Args:
            width: Drawable width
            height: Drawable height
        """
        if not self.midi_data:
            return
        
        # Get notes that are 0.5 to ghosted_lookahead_time seconds in the future
        future_start = self.current_time + 0.5
        future_end = self.current_time + self.ghosted_lookahead_time
        
        future_notes = self.midi_data.get_notes_in_range(future_start, future_end)
        
        for note in future_notes:
            # Calculate transparency based on distance from playhead
            time_to_playhead = note.start_time - self.current_time
            progress = time_to_playhead / self.ghosted_lookahead_time
            
            # Fade from transparent (far) to semi-transparent (near)
            alpha = int((1.0 - progress) * 100)  # 0-100 alpha range
            
            if alpha <= 0:
                continue
            
            # Get note color and apply transparency
            color = self._get_note_color(note)
            
            # Draw ghosted note
            note_x = self._pitch_to_x(note.pitch, width)
            note_y = self._time_to_y(note.start_time, height)
            note_width = self.note_width
            note_height = int(note.duration * self.pixels_per_second)
            
            # Create transparent surface for ghosted note
            ghosted_surface = pygame.Surface((note_width, note_height), pygame.SRCALPHA)
            color_with_alpha = (*color[:3], alpha)
            pygame.draw.rect(ghosted_surface, color_with_alpha, (0, 0, note_width, note_height), border_radius=2)
            
            # Draw border in current color at reduced opacity
            border_alpha = int(alpha * 0.5)
            border_color = tuple(max(0, c - 40) for c in color[:3])
            border_color_with_alpha = (*border_color, border_alpha)
            pygame.draw.rect(ghosted_surface, border_color_with_alpha, (0, 0, note_width, note_height), 1, border_radius=2)
            
            self.surface.blit(ghosted_surface, (note_x, note_y))

    def _calculate_perspective_scale(self, note: Note, height: int) -> float:
        """
        Calculate perspective scaling factor based on distance from playhead.
        Notes closer to playhead are larger (more prominent).
        
        Args:
            note: Note object
            height: Drawable height
        
        Returns:
            Scale factor (0.5 to 1.5)
        """
        if not self.enable_3d_perspective:
            return 1.0
        
        # Calculate distance from playhead
        playhead_y = (2 * height) // 3
        note_y = self._time_to_y(note.start_time, height)
        
        distance = abs(note_y - playhead_y)
        max_distance = height
        
        # Scale inversely with distance: closer = larger
        # Range: 0.5x (far) to 1.5x (at playhead)
        scale = 0.5 + (1.0 - (distance / max_distance)) * 1.0
        
        return scale

    def _draw_motion_blur_trail(self, note: Note, x: int, y: int, width: int, 
                               height: int, color: Tuple[int, int, int]):
        """
        Draw motion blur trail behind a falling note.
        
        Args:
            note: Note object
            x: Note X position
            y: Note Y position
            width: Note width
            height: Note height
            color: Note color
        """
        if not self.enable_motion_blur or height <= 0:
            return
        
        # Draw fading trail behind the note
        trail_length = min(height, 40)  # Trail extends above the note
        num_segments = 5
        
        for i in range(1, num_segments + 1):
            # Each segment gets progressively more transparent
            segment_alpha = int(100 * (1.0 - i / num_segments))
            trail_y = y - (trail_length * i // num_segments)
            
            if trail_y < 0:
                continue
            
            # Create trail segment surface
            trail_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            trail_color = (*color[:3], segment_alpha)
            pygame.draw.rect(trail_surface, trail_color, (0, 0, width, height), border_radius=2)
            
            self.surface.blit(trail_surface, (x, trail_y))

    def _create_particle_burst(self, x: int, y: int, color: Tuple[int, int, int], 
                              count: int = 12):
        """
        Create a burst of particles at the given location.
        
        Args:
            x: X position
            y: Y position
            color: Particle color
            count: Number of particles to create
        """
        for i in range(count):
            angle = (i / count) * 2 * math.pi
            speed = 100 + (i % 3) * 50  # Varying speeds
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            particle = Particle(x, y, vx, vy, color, lifetime=0.8)
            self.particles.append(particle)
    
    def _draw_particles(self):
        """Draw all active particles."""
        for particle in self.particles:
            x = int(particle.x)
            y = int(particle.y)
            
            # Skip if off screen
            if x < 0 or x > self.surface.get_width() or y < 0 or y > self.surface.get_height():
                continue
            
            # Draw particle as small circle with fading alpha
            alpha = particle.get_alpha()
            particle_surface = pygame.Surface((6, 6), pygame.SRCALPHA)
            color_with_alpha = (*particle.color, alpha)
            pygame.draw.circle(particle_surface, color_with_alpha, (3, 3), 3)
            self.surface.blit(particle_surface, (x - 3, y - 3))
    
    def _draw_bloom_on_notes(self, width: int, height: int, active_notes: list):
        """
        Draw glowing bloom effect directly on active notes.
        
        Args:
            width: Drawable width
            height: Drawable height
            active_notes: List of currently playing notes
        """
        for note in active_notes:
            note_x = self._pitch_to_x(note.pitch, width)
            note_y = self._time_to_y(note.start_time, height)
            color = self._get_note_color(note)
            
            # Draw multiple bloom circles with decreasing opacity
            for bloom_size in [40, 30, 20, 10]:
                alpha = int(80 * (1.0 - bloom_size / 40.0))  # Increased alpha for visibility
                bloom_surface = pygame.Surface((bloom_size * 2, bloom_size * 2), pygame.SRCALPHA)
                bloom_color = (*color, alpha)
                pygame.draw.circle(bloom_surface, bloom_color, (bloom_size, bloom_size), bloom_size)
                
                # Center on note
                blit_x = note_x + self.note_width // 2 - bloom_size
                blit_y = note_y - bloom_size
                self.surface.blit(bloom_surface, (blit_x, blit_y))
    
    def _draw_chord_label(self, width: int):
        """
        Draw chord name label at the top of the visualization.
        
        Args:
            width: Drawable width
        """
        if not self.current_chord:
            return
        
        # Calculate fade in/out
        fade_progress = self.chord_display_time / self.chord_display_duration
        if fade_progress < 0.1:
            # Fade in
            alpha = int(255 * (fade_progress / 0.1))
        elif fade_progress > 0.9:
            # Fade out
            alpha = int(255 * (1.0 - (fade_progress - 0.9) / 0.1))
        else:
            alpha = 255
        
        # Render chord name
        chord_font = pygame.font.Font(None, 32)
        chord_text = chord_font.render(self.current_chord, True, self.playhead_color)
        
        # Create surface with alpha
        text_surface = pygame.Surface(chord_text.get_size(), pygame.SRCALPHA)
        chord_text_with_alpha = chord_text.copy()
        chord_text_with_alpha.set_alpha(alpha)
        text_surface.blit(chord_text_with_alpha, (0, 0))
        
        # Center at top of visualization
        text_x = (width - chord_text.get_width()) // 2
        text_y = 20
        self.surface.blit(text_surface, (text_x, text_y))

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
