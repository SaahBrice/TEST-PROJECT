# visualization/liquid_mode.py
"""
Liquid Mode - A breathtaking fluid simulation visualization.

Notes transform into iridescent liquid droplets with metallic shimmer.
When they hit the keyboard, they create mesmerizing ripple waves.
Droplets merge for chords creating beautiful splash effects.
Features physics-based motion, light reflections, and volumetric depth.
"""

import pygame
import math
import random
from typing import List, Tuple, Optional
from midi import MIDIData, Note
from visualization.visualization_mode import VisualizationMode
from utils.logger import get_logger

logger = get_logger(__name__)


class LiquidDroplet:
    """Represents a liquid droplet in the simulation."""
    
    def __init__(self, x: float, y: float, pitch: int, velocity: float, 
                 color: Tuple[int, int, int], size: float = 1.0):
        """
        Initialize a droplet.
        
        Args:
            x: X position
            y: Y position
            pitch: MIDI pitch (for color)
            velocity: Note velocity (affects splash size)
            color: RGB base color
            size: Size multiplier (1.0 = normal)
        """
        self.x = x
        self.y = y
        self.pitch = pitch
        self.velocity = velocity
        self.color = color
        self.size = size
        
        # Physics
        self.vx = random.uniform(-2, 2)  # Random horizontal drift
        self.vy = 4.0 + velocity / 32.0  # Velocity affects fall speed
        self.ax = -self.vx * 0.02  # Air resistance
        self.ay = 0.15  # Gravity
        
        # Liquid properties
        self.surface_tension = 0.8
        self.viscosity = 0.95
        self.age = 0.0
        self.lifetime = 5.0
        self.alpha = 255
        
        # Trail for motion blur
        self.trail = [(self.x, self.y)]
        self.trail_max = 8
        
        # Shimmer animation
        self.shimmer_phase = 0.0
        self.shimmer_speed = random.uniform(2, 4)
    
    def update(self, dt: float):
        """Update droplet physics."""
        # Apply forces
        self.vx += self.ax * dt
        self.vy += self.ay * dt
        
        # Apply viscosity (slow down over time)
        self.vx *= self.viscosity
        self.vy *= self.viscosity
        
        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Age and fade
        self.age += dt
        fade_start = self.lifetime * 0.7
        if self.age > fade_start:
            progress = (self.age - fade_start) / (self.lifetime - fade_start)
            self.alpha = int(255 * (1.0 - progress))
        
        # Update trail (motion blur)
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.trail_max:
            self.trail.pop(0)
        
        # Shimmer animation
        self.shimmer_phase += self.shimmer_speed * dt
    
    def get_current_color(self) -> Tuple[int, int, int]:
        """Get color with shimmer effect."""
        shimmer = math.sin(self.shimmer_phase) * 0.3 + 0.7
        return tuple(int(c * shimmer) for c in self.color)
    
    def is_alive(self) -> bool:
        """Check if droplet is still alive."""
        return self.age < self.lifetime


class RippleWave:
    """Represents a ripple wave from liquid impact."""
    
    def __init__(self, x: float, y: float, initial_radius: float, amplitude: float):
        """
        Initialize a ripple wave.
        
        Args:
            x: Center X position
            y: Center Y position
            initial_radius: Starting ripple radius
            amplitude: Wave height
        """
        self.x = x
        self.y = y
        self.radius = initial_radius
        self.max_radius = 150
        self.amplitude = amplitude
        self.age = 0.0
        self.lifetime = 0.8
        self.speed = 150  # Pixels per second
    
    def update(self, dt: float):
        """Update ripple."""
        self.age += dt
        self.radius += self.speed * dt
    
    def is_alive(self) -> bool:
        """Check if ripple is still active."""
        return self.age < self.lifetime and self.radius < self.max_radius


class LiquidMode(VisualizationMode):
    """
    Liquid Mode - Fluid simulation visualization.
    
    Creates a mesmerizing display where notes become liquid droplets
    with physics, reflections, and beautiful ripple effects.
    """
    
    def __init__(self, screen: pygame.Surface, config, theme_manager=None):
        """
        Initialize Liquid Mode.
        
        Args:
            screen: Pygame surface to render to
            config: Configuration manager
            theme_manager: Theme manager for styling
        """
        super().__init__(screen, config, theme_manager)
        
        self.droplets: List[LiquidDroplet] = []
        self.ripples: List[RippleWave] = []
        self.particles: List[dict] = []
        
        # Screen properties
        self.width, self.height = screen.get_size()
        self.keyboard_height = 50
        
        # Colors and rendering
        self.bg_color = (15, 15, 25)  # Deep space
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Timing
        self.pixels_per_second = 100  # Vertical scroll speed
        self.audio_intensity = 0.0
        self.beat_intensity = 0.0
        
        # MIDI tracking
        self._last_note_times = {}  # Track when notes last fell
        self._recently_impacted = []  # Notes that just hit keyboard
        self._last_frame_time = 0.0
        
        # Chromatic colors for liquid shimmer
        self.chromatic_colors = [
            (220, 80, 80),    # C - Red
            (220, 100, 80),   # C# - Red-Orange
            (220, 140, 60),   # D - Orange
            (220, 180, 60),   # D# - Yellow-Orange
            (200, 200, 60),   # E - Yellow
            (140, 200, 80),   # F - Yellow-Green
            (80, 200, 120),   # F# - Green
            (80, 200, 160),   # G - Cyan-Green
            (80, 180, 220),   # G# - Cyan
            (100, 140, 220),  # A - Blue
            (140, 100, 220),  # A# - Purple
            (200, 80, 200),   # B - Magenta
        ]
        
        logger.info("Liquid Mode initialized")
    
    def render(self) -> pygame.Surface:
        """Render the liquid visualization."""
        # Clear background
        self.surface.fill(self.bg_color)
        self.width, self.height = self.screen.get_size()
        
        # Update and draw all elements
        self._update_physics()
        self._draw_background_glow()
        self._draw_ripples()
        self._draw_droplets()
        self._draw_particles()
        self._draw_keyboard()
        
        # Blit to screen
        self.screen.blit(self.surface, (0, 0))
        return self.screen
    
    def set_midi_data(self, midi_data: MIDIData):
        """Set MIDI data."""
        self.midi_data = midi_data
    
    def update_time(self, current_time: float):
        """Update playback time and generate droplets for falling notes."""
        dt = current_time - self._last_frame_time
        if dt < 0:  # Seek backwards
            self.droplets.clear()
            self.ripples.clear()
            self.particles.clear()
        
        self._last_frame_time = current_time
        
        if not self.midi_data:
            return
        
        # Check for notes hitting keyboard
        self._check_keyboard_impacts(current_time)
        
        # Spawn droplets for active notes
        active_notes = self.midi_data.get_notes_at_time(current_time)
        for note in active_notes:
            # Spawn new droplets if note just started
            if note.pitch not in self._last_note_times:
                self._last_note_times[note.pitch] = current_time
                self._spawn_droplets_for_note(note, current_time)
    
    def _spawn_droplets_for_note(self, note: Note, current_time: float):
        """Spawn liquid droplets for a note."""
        x = self._pitch_to_x(note.pitch)
        y = 30  # Start near top
        
        # Base color from pitch
        base_color = self.chromatic_colors[note.pitch % 12]
        
        # Number of droplets based on velocity
        count = max(1, int(3 * note.velocity / 127))
        
        for i in range(count):
            # Spread droplets horizontally
            offset_x = random.uniform(-15, 15)
            droplet = LiquidDroplet(
                x + offset_x, y,
                note.pitch,
                note.velocity / 127.0,
                base_color,
                size=0.7 + note.velocity / 254.0
            )
            self.droplets.append(droplet)
    
    def _check_keyboard_impacts(self, current_time: float):
        """Check for droplets hitting the keyboard."""
        keyboard_y = self.height - self.keyboard_height
        
        for droplet in self.droplets[:]:
            # Check if droplet reached keyboard
            if droplet.y >= keyboard_y and droplet not in self._recently_impacted:
                self._recently_impacted.append(droplet)
                
                # Create ripple at impact
                self._create_ripple(droplet.x, keyboard_y, droplet.velocity)
                
                # Create splash particles
                self._create_splash_particles(
                    droplet.x, keyboard_y,
                    droplet.color, droplet.velocity
                )
                
                # Remove droplet
                self.droplets.remove(droplet)
    
    def _create_ripple(self, x: float, y: float, velocity: float):
        """Create a ripple wave."""
        amplitude = 3 + velocity * 5
        ripple = RippleWave(x, y, 10, amplitude)
        self.ripples.append(ripple)
    
    def _create_splash_particles(self, x: float, y: float, 
                                 color: Tuple[int, int, int], velocity: float):
        """Create splash particles."""
        count = int(10 + velocity * 15)
        
        for i in range(count):
            angle = (i / count) * 2 * math.pi
            speed = 100 + velocity * 200
            
            particle = {
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed - 50,
                'color': self._shimmer_color(color),
                'age': 0.0,
                'lifetime': 0.5 + random.uniform(0, 0.3),
                'gravity': 200
            }
            self.particles.append(particle)
    
    def _shimmer_color(self, color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Add rainbow shimmer to color."""
        hue_shift = random.uniform(0, 30)
        return tuple(
            min(255, int(c + hue_shift)) if i < 2 else max(0, int(c - hue_shift))
            for i, c in enumerate(color)
        )
    
    def _update_physics(self):
        """Update all physics simulations."""
        dt = 1.0 / 60.0  # 60 FPS
        
        # Update droplets
        for droplet in self.droplets[:]:
            droplet.update(dt)
            if not droplet.is_alive():
                self.droplets.remove(droplet)
        
        # Update ripples
        for ripple in self.ripples[:]:
            ripple.update(dt)
            if not ripple.is_alive():
                self.ripples.remove(ripple)
        
        # Update particles
        for particle in self.particles[:]:
            particle['vx'] *= 0.98  # Air resistance
            particle['vy'] += particle['gravity'] * dt
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['age'] += dt
            
            if particle['age'] >= particle['lifetime']:
                self.particles.remove(particle)
    
    def _draw_background_glow(self):
        """Draw audio-reactive background."""
        if self.audio_intensity > 0:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            alpha = int(self.audio_intensity * 60)
            glow_color = (80, 120, 200, alpha)
            pygame.draw.rect(overlay, glow_color, (0, 0, self.width, self.height))
            self.surface.blit(overlay, (0, 0))
    
    def _draw_ripples(self):
        """Draw ripple waves."""
        for ripple in self.ripples:
            progress = ripple.age / ripple.lifetime
            alpha = int(200 * (1.0 - progress))
            
            # Draw ripple circle
            radius = int(ripple.radius)
            if radius > 0:
                ripple_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                color = (100 + int(55 * progress), 150 - int(30 * progress), 
                        200 - int(50 * progress), alpha)
                pygame.draw.circle(ripple_surf, color, (radius, radius), radius, 3)
                
                # Blit centered
                x = int(ripple.x - radius)
                y = int(ripple.y - radius)
                self.surface.blit(ripple_surf, (x, y))
    
    def _draw_droplets(self):
        """Draw liquid droplets with shimmer and reflection."""
        for droplet in self.droplets:
            # Skip if off-screen
            if droplet.y < -50 or droplet.y > self.height + 50:
                continue
            
            x = int(droplet.x)
            y = int(droplet.y)
            size = int(8 * droplet.size)
            
            if size < 2:
                continue
            
            # Draw trail (motion blur)
            if len(droplet.trail) > 2:
                for i in range(len(droplet.trail) - 1):
                    t1 = droplet.trail[i]
                    t2 = droplet.trail[i + 1]
                    progress = i / len(droplet.trail)
                    trail_alpha = int(droplet.alpha * (1.0 - progress) * 0.5)
                    trail_color = (*droplet.get_current_color(), trail_alpha)
                    
                    # Draw thin line
                    if trail_alpha > 0:
                        trail_surf = pygame.Surface((int(abs(t2[0]-t1[0])+2), 
                                                     int(abs(t2[1]-t1[1])+2)), 
                                                    pygame.SRCALPHA)
                        pygame.draw.line(trail_surf, trail_color, 
                                       (t1[0], t1[1]), (t2[0], t2[1]), 1)
            
            # Draw main droplet
            color_with_alpha = (*droplet.get_current_color(), droplet.alpha)
            droplet_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            
            # Main sphere
            pygame.draw.circle(droplet_surf, color_with_alpha, (size, size), size)
            
            # Highlight (reflection)
            if droplet.alpha > 100:
                highlight_alpha = int(droplet.alpha * 0.6)
                highlight_color = (255, 255, 255, highlight_alpha)
                pygame.draw.circle(droplet_surf, highlight_color, 
                                 (size - size // 3, size - size // 3), size // 4)
            
            self.surface.blit(droplet_surf, (x - size, y - size))
    
    def _draw_particles(self):
        """Draw splash particles."""
        for particle in self.particles:
            progress = particle['age'] / particle['lifetime']
            alpha = int(particle['lifetime'] * 255 * (1.0 - progress))
            
            x = int(particle['x'])
            y = int(particle['y'])
            size = 3
            
            if alpha > 0:
                particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                color = (*particle['color'], alpha)
                pygame.draw.circle(particle_surf, color, (size, size), size)
                self.surface.blit(particle_surf, (x - size, y - size))
    
    def _draw_keyboard(self):
        """Draw keyboard at bottom."""
        keyboard_y = self.height - self.keyboard_height
        
        # Keyboard background
        keyboard_rect = pygame.Rect(0, keyboard_y, self.width, self.keyboard_height)
        pygame.draw.rect(self.surface, (30, 30, 40), keyboard_rect)
        
        # Keys
        key_width = self.width // 88
        for i in range(88):
            key_x = i * key_width
            is_black = (i % 12) in [1, 2, 4, 5, 6, 8, 9, 10, 11]
            color = (100, 100, 120) if is_black else (200, 200, 220)
            pygame.draw.rect(self.surface, color, 
                           (key_x, keyboard_y, key_width, self.keyboard_height))
            pygame.draw.line(self.surface, (50, 50, 60), 
                           (key_x, keyboard_y), (key_x, keyboard_y + self.keyboard_height), 1)
    
    def _pitch_to_x(self, pitch: int) -> float:
        """Convert MIDI pitch to X coordinate."""
        # Map MIDI pitch 0-127 to screen width
        return (pitch / 127.0) * self.width
    
    def set_audio_intensity(self, intensity: float):
        """Set audio intensity."""
        self.audio_intensity = max(0.0, min(1.0, intensity))
    
    def set_beat_intensity(self, intensity: float):
        """Set beat intensity."""
        self.beat_intensity = max(0.0, min(1.0, intensity))
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame events."""
        return False
    
    def get_name(self) -> str:
        """Get mode name."""
        return "Liquid Mode"
    
    def reset(self):
        """Reset to initial state."""
        self.droplets.clear()
        self.ripples.clear()
        self.particles.clear()
        self._last_note_times.clear()
        self._recently_impacted.clear()
    
    def cleanup(self):
        """Clean up resources."""
        self.reset()
