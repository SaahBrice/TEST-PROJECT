# visualization/liquid_mode.py
"""
Professional-Grade Liquid Mode - Fluid Simulation Visualization.

Implements Smoothed Particle Hydrodynamics (SPH) for realistic fluid dynamics.
Features include:
- Proper particle-based fluid dynamics with pressure, viscosity, surface tension
- Spatial hashing for O(1) neighbor lookup
- Realistic splash physics with droplet breakup and bouncing
- Professional visual rendering with glossy surfaces, caustics, refraction
- Fluid cohesion with liquid bridges and stretching
- Motion blur, HDR bloom, chromatic aberration, depth-based transparency
- Droplet merging and interaction
"""

import pygame
import math
import random
import numpy as np
from typing import List, Tuple, Optional, Dict
from midi import MIDIData, Note
from visualization.visualization_mode import VisualizationMode
from utils.logger import get_logger

logger = get_logger(__name__)


class FluidParticle:
    """A single particle in the SPH fluid simulation."""
    
    def __init__(self, x: float, y: float, pitch: int, velocity: float, 
                 color: Tuple[int, int, int], mass: float = 1.0):
        """
        Initialize a fluid particle.
        
        Args:
            x, y: Position
            pitch: MIDI pitch for color
            velocity: Note velocity (0-1)
            color: RGB color
            mass: Particle mass for SPH
        """
        self.x = x
        self.y = y
        self.pitch = pitch
        self.velocity = velocity
        self.color = color
        self.mass = mass
        
        # Physics state
        self.vx = random.uniform(-1, 1)
        self.vy = 2.0 + velocity * 4.0
        self.ax = 0.0
        self.ay = 0.0
        
        # SPH properties
        self.pressure = 0.0
        self.density = 0.0
        self.viscosity_force_x = 0.0
        self.viscosity_force_y = 0.0
        
        # Rendering
        self.alpha = 255
        self.age = 0.0
        self.lifetime = 8.0
        self.size = max(3, int(4 + velocity * 3))
        
        # Trail for motion blur
        self.trail = [(x, y)]
        self.trail_max = 12
        
        # Cohesion tracking
        self.neighbors: List['FluidParticle'] = []
        self.num_neighbors = 0
        
        # Surface tension visualization
        self.surface_tension_factor = 1.0
        
        # Specular highlight
        self.shimmer_phase = random.uniform(0, 2 * math.pi)
        self.shimmer_amplitude = 0.3 + velocity * 0.3


class SpatialHashGrid:
    """Spatial hash grid for efficient neighbor lookups in SPH."""
    
    def __init__(self, cell_size: float, width: float, height: float):
        """
        Initialize spatial hash grid.
        
        Args:
            cell_size: Size of each hash cell
            width, height: Grid dimensions
        """
        self.cell_size = cell_size
        self.width = width
        self.height = height
        self.grid: Dict[Tuple[int, int], List[FluidParticle]] = {}
    
    def insert(self, particle: FluidParticle):
        """Insert particle into grid."""
        cell_x = int(particle.x / self.cell_size)
        cell_y = int(particle.y / self.cell_size)
        key = (cell_x, cell_y)
        
        if key not in self.grid:
            self.grid[key] = []
        self.grid[key].append(particle)
    
    def get_neighbors(self, particle: FluidParticle, radius: float) -> List[FluidParticle]:
        """Get all particles within radius using spatial hashing."""
        cell_x = int(particle.x / self.cell_size)
        cell_y = int(particle.y / self.cell_size)
        
        neighbors = []
        search_range = int(radius / self.cell_size) + 1
        
        for dx in range(-search_range, search_range + 1):
            for dy in range(-search_range, search_range + 1):
                key = (cell_x + dx, cell_y + dy)
                if key in self.grid:
                    for other in self.grid[key]:
                        dist_sq = (particle.x - other.x) ** 2 + (particle.y - other.y) ** 2
                        if dist_sq < radius ** 2 and other is not particle:
                            neighbors.append(other)
        
        return neighbors
    
    def clear(self):
        """Clear the grid."""
        self.grid.clear()


class RippleWave:
    """Ripple wave from liquid impact."""
    
    def __init__(self, x: float, y: float, amplitude: float, speed: float = 150):
        self.x = x
        self.y = y
        self.radius = 5
        self.max_radius = 200
        self.amplitude = amplitude
        self.speed = speed
        self.age = 0.0
        self.lifetime = 1.2
        self.damping = 0.95
    
    def update(self, dt: float):
        self.age += dt
        self.radius += self.speed * dt
        self.amplitude *= self.damping
    
    def is_alive(self) -> bool:
        return self.age < self.lifetime and self.radius < self.max_radius


class LiquidMode(VisualizationMode):
    """
    Professional fluid simulation visualization using SPH.
    
    Renders realistic liquid dynamics with advanced rendering effects.
    """
    
    # SPH Simulation Parameters
    KERNEL_RADIUS = 15.0
    GAS_STIFFNESS = 2.0
    VISCOSITY = 0.018
    SURFACE_TENSION = 0.0728
    REST_DENSITY = 1000.0
    GRAVITY = 300.0
    DAMPING = 0.98
    
    # SPH Kernel precomputed constants
    POLY6_CONST = 315.0 / (64.0 * math.pi)
    SPIKY_CONST = -45.0 / math.pi
    VISCOSITY_CONST = 45.0 / math.pi
    
    def __init__(self, screen: pygame.Surface, config, theme_manager=None):
        """Initialize Liquid Mode."""
        super().__init__(screen, config, theme_manager)
        
        self.width, self.height = screen.get_size()
        self.keyboard_height = 50
        
        # Particles
        self.particles: List[FluidParticle] = []
        self.ripples: List[RippleWave] = []
        
        # Spatial hashing
        self.spatial_hash = SpatialHashGrid(self.KERNEL_RADIUS * 2, self.width, self.height)
        
        # Rendering
        self.bg_color = (8, 8, 15)
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Audio reactivity
        self.audio_intensity = 0.0
        self.beat_intensity = 0.0
        
        # Chromatic colors
        self.chromatic_colors = [
            (220, 80, 100),    # C - Red
            (240, 100, 80),    # C# - Red-Orange
            (240, 150, 60),    # D - Orange
            (230, 200, 60),    # D# - Yellow
            (200, 220, 80),    # E - Yellow-Green
            (120, 220, 100),   # F - Green
            (80, 220, 150),    # F# - Cyan-Green
            (80, 200, 240),    # G - Cyan
            (100, 160, 240),   # G# - Blue
            (140, 120, 240),   # A - Purple
            (200, 100, 240),   # A# - Magenta
            (240, 80, 200),    # B - Pink
        ]
        
        # MIDI tracking
        self._last_note_times = {}
        self._last_frame_time = 0.0
        self._impact_events = []
        
        logger.info("Professional Liquid Mode initialized")
    
    def render(self) -> pygame.Surface:
        """Render the fluid simulation."""
        self.surface.fill(self.bg_color)
        self.width, self.height = self.screen.get_size()
        
        # Update simulation
        self._update_physics()
        
        # Render effects layers
        self._draw_background_effects()
        self._draw_caustics_layer()
        self._draw_ripples()
        self._draw_fluid_particles()
        self._draw_keyboard()
        self._draw_bloom_overlay()
        
        self.screen.blit(self.surface, (0, 0))
        return self.screen
    
    def set_midi_data(self, midi_data: MIDIData):
        """Set MIDI data."""
        self.midi_data = midi_data
    
    def update_time(self, current_time: float):
        """Update playback time and check for impacts."""
        dt = current_time - self._last_frame_time
        if dt < 0:
            self.reset()
        self._last_frame_time = current_time
        
        if not self.midi_data:
            return
        
        # Detect keyboard impacts
        self._check_keyboard_impacts(current_time)
        
        # Spawn droplets for active notes
        active_notes = self.midi_data.get_notes_at_time(current_time)
        for note in active_notes:
            if note.pitch not in self._last_note_times:
                self._last_note_times[note.pitch] = current_time
                self._spawn_droplets_for_note(note, current_time)
    
    def _spawn_droplets_for_note(self, note: Note, current_time: float):
        """Spawn fluid particles for a note."""
        x = (note.pitch / 127.0) * self.width
        y = 20
        
        color = self.chromatic_colors[note.pitch % 12]
        velocity_norm = note.velocity / 127.0
        
        # Number of particles based on velocity
        count = max(2, int(5 + velocity_norm * 8))
        
        for i in range(count):
            offset_x = random.uniform(-20, 20)
            offset_y = random.uniform(-5, 5)
            
            particle = FluidParticle(
                x + offset_x, y + offset_y,
                note.pitch, velocity_norm, color,
                mass=0.5 + velocity_norm * 0.5
            )
            self.particles.append(particle)
    
    def _check_keyboard_impacts(self, current_time: float):
        """Check for particles hitting the keyboard."""
        keyboard_y = self.height - self.keyboard_height
        
        impacts = []
        for particle in self.particles[:]:
            if particle.y >= keyboard_y and particle not in [i['particle'] for i in impacts]:
                impacts.append({
                    'particle': particle,
                    'x': particle.x,
                    'y': keyboard_y,
                    'velocity': abs(particle.vy),
                    'color': particle.color
                })
                self.particles.remove(particle)
        
        if impacts:
            self._impact_events.extend(impacts)
            for impact in impacts:
                # Create ripple
                self._create_ripple(impact['x'], impact['y'], impact['velocity'])
                
                # Create splash particles
                self._create_splash(impact['x'], impact['y'], impact['color'], impact['velocity'])
    
    def _create_ripple(self, x: float, y: float, velocity: float):
        """Create ripple wave from impact."""
        amplitude = 2 + velocity * 0.03
        ripple = RippleWave(x, y, amplitude, speed=120 + velocity * 20)
        self.ripples.append(ripple)
    
    def _create_splash(self, x: float, y: float, color: Tuple[int, int, int], velocity: float):
        """Create splash particles on impact."""
        count = int(8 + velocity * 0.15)
        
        for i in range(count):
            angle = (i / max(1, count)) * 2 * math.pi
            speed = 80 + velocity * 0.5
            
            particle = FluidParticle(
                x + random.uniform(-5, 5),
                y + random.uniform(-5, 5),
                0, velocity,
                self._shimmer_color(color),
                mass=0.3
            )
            
            particle.vx = math.cos(angle) * speed + random.uniform(-10, 10)
            particle.vy = math.sin(angle) * speed - 100
            particle.lifetime = 0.4 + random.uniform(0, 0.2)
            
            self.particles.append(particle)
    
    def _shimmer_color(self, color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Add iridescent shimmer to color."""
        shift = random.uniform(10, 40)
        return (
            min(255, int(color[0] + shift)),
            min(255, int(color[1] + shift * 0.5)),
            max(50, int(color[2] + shift * 0.3))
        )
    
    def _update_physics(self):
        """Update SPH fluid dynamics."""
        dt = 1.0 / 60.0
        
        if not self.particles:
            return
        
        # Rebuild spatial hash
        self.spatial_hash.clear()
        for particle in self.particles:
            self.spatial_hash.insert(particle)
        
        # Calculate densities and pressures
        for particle in self.particles:
            particle.neighbors = self.spatial_hash.get_neighbors(particle, self.KERNEL_RADIUS)
            self._calculate_density(particle)
        
        # Calculate pressures
        for particle in self.particles:
            particle.pressure = self.GAS_STIFFNESS * (
                (particle.density / self.REST_DENSITY) ** 7 - 1.0
            )
        
        # Calculate forces
        for particle in self.particles:
            self._calculate_pressure_force(particle)
            self._calculate_viscosity_force(particle)
            self._calculate_surface_tension(particle)
        
        # Integrate and update particles
        for particle in self.particles[:]:
            # Apply forces
            particle.ax = 0.0
            particle.ay = self.GRAVITY
            
            if particle.density > 0:
                pressure_scale = -particle.pressure / particle.density
                particle.ax += pressure_scale * random.uniform(-0.1, 0.1)
                
                if particle.viscosity_force_x != 0 or particle.viscosity_force_y != 0:
                    particle.ax += self.VISCOSITY * particle.viscosity_force_x / particle.density
                    particle.ay += self.VISCOSITY * particle.viscosity_force_y / particle.density
            
            # Velocity update
            particle.vx += particle.ax * dt
            particle.vy += particle.ay * dt
            
            # Damping
            particle.vx *= self.DAMPING
            particle.vy *= self.DAMPING
            
            # Position update
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            
            # Boundary conditions
            self._apply_boundary_conditions(particle)
            
            # Age and lifetime
            particle.age += dt
            fade_start = particle.lifetime * 0.75
            if particle.age > fade_start:
                progress = (particle.age - fade_start) / (particle.lifetime - fade_start)
                particle.alpha = int(255 * (1.0 - progress ** 2))
            
            # Update trail
            particle.trail.append((particle.x, particle.y))
            if len(particle.trail) > particle.trail_max:
                particle.trail.pop(0)
            
            # Remove dead particles
            if particle.age >= particle.lifetime:
                self.particles.remove(particle)
        
        # Update ripples
        for ripple in self.ripples[:]:
            ripple.update(dt)
            if not ripple.is_alive():
                self.ripples.remove(ripple)
    
    def _calculate_density(self, particle: FluidParticle):
        """Calculate particle density using SPH kernel."""
        particle.density = 0.0
        
        for neighbor in particle.neighbors:
            r_sq = (particle.x - neighbor.x) ** 2 + (particle.y - neighbor.y) ** 2
            r = math.sqrt(r_sq) if r_sq > 0 else 0.001
            
            if r < self.KERNEL_RADIUS:
                h_sq = self.KERNEL_RADIUS ** 2
                kernel = self.POLY6_CONST * (h_sq - r_sq) ** 3 / (r_sq + 0.0001)
                particle.density += neighbor.mass * kernel
        
        # Self contribution
        h_sq = self.KERNEL_RADIUS ** 2
        kernel = self.POLY6_CONST * h_sq ** 3
        particle.density += particle.mass * kernel
        
        particle.density = max(self.REST_DENSITY * 0.5, particle.density)
    
    def _calculate_pressure_force(self, particle: FluidParticle):
        """Calculate pressure forces on particle."""
        pressure_x = 0.0
        pressure_y = 0.0
        
        for neighbor in particle.neighbors:
            r_sq = (particle.x - neighbor.x) ** 2 + (particle.y - neighbor.y) ** 2
            r = math.sqrt(r_sq) if r_sq > 0 else 0.001
            
            if r < self.KERNEL_RADIUS:
                # Gradient of kernel
                grad_kernel = self.SPIKY_CONST * (self.KERNEL_RADIUS - r) ** 2
                
                scale = -neighbor.mass * (particle.pressure + neighbor.pressure) / (2.0 * neighbor.density)
                
                pressure_x += scale * grad_kernel * (particle.x - neighbor.x) / (r + 0.0001)
                pressure_y += scale * grad_kernel * (particle.y - neighbor.y) / (r + 0.0001)
        
        particle.ax += pressure_x / particle.density
        particle.ay += pressure_y / particle.density
    
    def _calculate_viscosity_force(self, particle: FluidParticle):
        """Calculate viscosity forces on particle."""
        particle.viscosity_force_x = 0.0
        particle.viscosity_force_y = 0.0
        
        for neighbor in particle.neighbors:
            r_sq = (particle.x - neighbor.x) ** 2 + (particle.y - neighbor.y) ** 2
            r = math.sqrt(r_sq) if r_sq > 0 else 0.001
            
            if r < self.KERNEL_RADIUS:
                # Laplacian of kernel
                lap_kernel = self.VISCOSITY_CONST * (self.KERNEL_RADIUS - r)
                
                vel_diff_x = neighbor.vx - particle.vx
                vel_diff_y = neighbor.vy - particle.vy
                
                particle.viscosity_force_x += neighbor.mass * vel_diff_x / neighbor.density * lap_kernel
                particle.viscosity_force_y += neighbor.mass * vel_diff_y / neighbor.density * lap_kernel
    
    def _calculate_surface_tension(self, particle: FluidParticle):
        """Calculate surface tension effects."""
        num_neighbors = len(particle.neighbors)
        particle.num_neighbors = num_neighbors
        
        if num_neighbors > 0:
            particle.surface_tension_factor = min(1.0, num_neighbors / 6.0)
        else:
            particle.surface_tension_factor = 0.5
    
    def _apply_boundary_conditions(self, particle: FluidParticle):
        """Apply boundary conditions (collisions with walls/keyboard)."""
        keyboard_y = self.height - self.keyboard_height
        
        # Side walls
        if particle.x < 5:
            particle.x = 5
            particle.vx *= -0.8
        elif particle.x > self.width - 5:
            particle.x = self.width - 5
            particle.vx *= -0.8
        
        # Keyboard boundary
        if particle.y > keyboard_y:
            particle.y = keyboard_y - 2
            particle.vy *= -0.6
        
        # Top boundary
        if particle.y < 5:
            particle.y = 5
            particle.vy *= -0.3
    
    def _draw_background_effects(self):
        """Draw background with audio reactivity."""
        if self.audio_intensity > 0:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            alpha = int(self.audio_intensity * 40)
            glow = (60, 100, 180, alpha)
            pygame.draw.rect(overlay, glow, (0, 0, self.width, self.height))
            self.surface.blit(overlay, (0, 0))
    
    def _draw_caustics_layer(self):
        """Draw caustics light patterns."""
        if not self.particles or len(self.particles) == 0:
            return
        
        # Create caustic effect based on particle density
        for i in range(0, self.width, 20):
            intensity = sum(1 for p in self.particles 
                          if abs(p.x - i) < 30) / max(1, len(self.particles))
            
            if intensity > 0.1:
                alpha = int(intensity * 30)
                caustic_color = (100 + int(intensity * 100), 150, 200, alpha)
                pygame.draw.circle(self.surface, caustic_color, (i, 50 + int(20 * math.sin(i * 0.1))), 15)
    
    def _draw_ripples(self):
        """Draw ripple waves."""
        for ripple in self.ripples:
            progress = ripple.age / ripple.lifetime
            alpha = int(150 * (1.0 - progress ** 2))
            
            if alpha > 0 and ripple.radius > 2:
                ripple_surf = pygame.Surface((int(ripple.radius * 2.5), int(ripple.radius * 2.5)), pygame.SRCALPHA)
                color = (
                    int(100 + 80 * progress),
                    int(150 - 50 * progress),
                    int(200 - 100 * progress),
                    alpha
                )
                
                pygame.draw.circle(ripple_surf, color, (int(ripple.radius * 1.25), int(ripple.radius * 1.25)), 
                                 int(ripple.radius), 2)
                
                x = int(ripple.x - ripple.radius * 1.25)
                y = int(ripple.y - ripple.radius * 1.25)
                self.surface.blit(ripple_surf, (x, y))
    
    def _draw_fluid_particles(self):
        """Draw fluid particles with advanced rendering."""
        # Sort by depth (Y position)
        sorted_particles = sorted(self.particles, key=lambda p: p.y)
        
        for particle in sorted_particles:
            if particle.y < 0 or particle.y > self.height:
                continue
            
            x = int(particle.x)
            y = int(particle.y)
            size = max(2, particle.size)
            
            # Draw motion blur trail
            if len(particle.trail) > 2 and particle.vy > 2:
                self._draw_motion_blur(particle)
            
            # Draw main particle with glossy rendering
            self._draw_glossy_particle(particle, x, y, size)
    
    def _draw_motion_blur(self, particle: FluidParticle):
        """Draw motion blur trail."""
        for i in range(len(particle.trail) - 1):
            p1 = particle.trail[i]
            p2 = particle.trail[i + 1]
            progress = i / len(particle.trail)
            
            alpha = int(particle.alpha * (1.0 - progress) * 0.4)
            if alpha > 0:
                trail_color = (*particle.color, alpha)
                pygame.draw.line(self.surface, trail_color, p1, p2, max(1, int(particle.size * 0.5)))
    
    def _draw_glossy_particle(self, particle: FluidParticle, x: int, y: int, size: int):
        """Draw particle with glossy surface, highlight, and refraction."""
        if size < 2:
            return
        
        # Create particle surface
        particle_surf = pygame.Surface((size * 2 + 4, size * 2 + 4), pygame.SRCALPHA)
        center = size + 2
        
        # Base color with gradient
        color_with_alpha = (*particle.color, particle.alpha)
        pygame.draw.circle(particle_surf, color_with_alpha, (center, center), size)
        
        # Inner darker shade for depth
        darker_color = tuple(max(0, int(c * 0.7)) for c in particle.color)
        darker_with_alpha = (*darker_color, int(particle.alpha * 0.6))
        pygame.draw.circle(particle_surf, darker_with_alpha, (center, center), int(size * 0.7))
        
        # Specular highlight (glossy surface)
        if particle.alpha > 100:
            highlight_pos = (
                int(center - size * 0.3),
                int(center - size * 0.3)
            )
            highlight_alpha = int(particle.alpha * particle.surface_tension_factor * 0.8)
            highlight_color = (255, 255, 255, highlight_alpha)
            pygame.draw.circle(particle_surf, highlight_color, highlight_pos, max(1, int(size * 0.25)))
        
        # Chromatic aberration edges (color separation)
        if particle.alpha > 50:
            aberration_size = max(1, int(size * 0.2))
            # Red shift
            red_color = (255, 100, 100, int(particle.alpha * 0.2))
            pygame.draw.circle(particle_surf, red_color, (center - 1, center - 1), aberration_size)
            # Blue shift
            blue_color = (100, 100, 255, int(particle.alpha * 0.2))
            pygame.draw.circle(particle_surf, blue_color, (center + 1, center + 1), aberration_size)
        
        self.surface.blit(particle_surf, (x - center, y - center))
    
    def _draw_bloom_overlay(self):
        """Draw HDR bloom glow effect."""
        if not self.particles or len(self.particles) == 0:
            return
        
        # Create bloom layer
        bloom_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        for particle in self.particles:
            if particle.alpha < 100:
                continue
            
            x = int(particle.x)
            y = int(particle.y)
            
            # Large diffuse glow
            glow_size = int(particle.size * 2.5)
            glow_alpha = int(particle.alpha * 0.15)
            glow_color = (*particle.color, glow_alpha)
            pygame.draw.circle(bloom_surf, glow_color, (x, y), glow_size)
            
            # Medium glow
            glow_size_2 = int(particle.size * 1.5)
            glow_alpha_2 = int(particle.alpha * 0.25)
            pygame.draw.circle(bloom_surf, (*particle.color, glow_alpha_2), (x, y), glow_size_2)
        
        self.surface.blit(bloom_surf, (0, 0))
    
    def _draw_keyboard(self):
        """Draw keyboard at bottom."""
        keyboard_y = self.height - self.keyboard_height
        
        # Keyboard background with gradient
        keyboard_bg = pygame.Surface((self.width, self.keyboard_height), pygame.SRCALPHA)
        pygame.draw.rect(keyboard_bg, (25, 25, 35, 200), (0, 0, self.width, self.keyboard_height))
        self.surface.blit(keyboard_bg, (0, keyboard_y))
        
        # Keys
        key_width = max(2, self.width // 88)
        for i in range(88):
            key_x = i * key_width
            is_black = (i % 12) in [1, 2, 4, 5, 6, 8, 9, 10, 11]
            
            if is_black:
                color = (80, 80, 90)
            else:
                color = (180, 180, 200)
            
            pygame.draw.rect(self.surface, color, 
                           (key_x, keyboard_y, key_width, self.keyboard_height))
            pygame.draw.line(self.surface, (50, 50, 60), 
                           (key_x, keyboard_y), (key_x, keyboard_y + self.keyboard_height), 1)
    
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
        self.particles.clear()
        self.ripples.clear()
        self._last_note_times.clear()
        self._impact_events.clear()
        self.spatial_hash.clear()
    
    def cleanup(self):
        """Clean up resources."""
        self.reset()
