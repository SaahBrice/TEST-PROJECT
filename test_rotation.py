#!/usr/bin/env python3
"""
Advanced visualization test with all visual enhancements and effects.
"""

import sys
import os
import math

# Add audioviz-midi to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'audioviz-midi'))

import pygame
from midi import MIDIData, Note
from visualization.piano_roll_renderer import PianoRollRenderer
from utils.config import ConfigManager

def test_advanced_effects():
    """Test the piano roll renderer with all advanced visual effects."""
    # Initialize Pygame
    pygame.init()
    
    # Create a surface
    width, height = 1200, 800
    surface = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Advanced Music Visualizer")
    
    # Create config
    config = ConfigManager()
    
    # Create renderer with all effects enabled
    renderer = PianoRollRenderer(surface, config)
    
    # Enable all visual effects
    renderer.enable_3d_perspective = True
    renderer.enable_ghosted_notes = True
    renderer.enable_motion_blur = True
    renderer.enable_audio_reactive_bg = True
    renderer.enable_waveform = True
    renderer.enable_particles = True
    renderer.enable_keyboard_animation = True
    renderer.enable_bloom = True
    renderer.enable_chord_labels = True
    renderer.enable_beat_effects = True
    
    # Create test MIDI data with chord progressions
    midi_data = MIDIData()
    
    # Build a musical progression with chords and melodies
    progression = [
        # C major chord + melody
        {'time': 0.0, 'notes': [(36, 0.4), (48, 0.4), (60, 0.4), (64, 0.8), (67, 1.2)]},
        # A minor chord + melody
        {'time': 1.5, 'notes': [(36, 0.4), (45, 0.4), (57, 0.4), (60, 0.8), (65, 1.2)]},
        # F major chord + melody
        {'time': 3.0, 'notes': [(36, 0.4), (41, 0.4), (53, 0.4), (65, 0.8), (69, 1.2)]},
        # G major chord + melody
        {'time': 4.5, 'notes': [(36, 0.4), (43, 0.4), (55, 0.4), (67, 0.8), (71, 1.2)]},
    ]
    
    for section in progression:
        base_time = section['time']
        for pitch, duration in section['notes']:
            note = Note(
                pitch=pitch,
                start_time=base_time,
                end_time=base_time + duration,
                velocity=80 + (pitch % 12) * 2
            )
            midi_data.add_note(note)
    
    # Add fast runs for dynamic rhythm
    for run_start in [6.0, 7.0]:
        for i in range(8):
            note = Note(
                pitch=48 + (i * 2) % 24,
                start_time=run_start + (i * 0.1),
                end_time=run_start + (i * 0.1) + 0.12,
                velocity=100
            )
            midi_data.add_note(note)
    
    renderer.set_midi_data(midi_data)
    
    # Test rendering
    clock = pygame.time.Clock()
    running = True
    current_time = 0.0
    
    print("=" * 70)
    print("ADVANCED MUSIC VISUALIZER - FULL EFFECTS TEST")
    print("=" * 70)
    print()
    print("ACTIVE VISUAL EFFECTS:")
    print()
    print("1. PARTICLE SYSTEM")
    print("   [+] Colorful particles burst when notes hit the playhead")
    print("   [+] Particles fade out smoothly over time")
    print()
    print("2. KEYBOARD ANIMATION")
    print("   [+] Piano keys press down smoothly when notes play")
    print("   [+] Keys release with smooth animation")
    print("   [+] Depth shadows show key depression")
    print()
    print("3. BLOOM/GLOW EFFECT")
    print("   [+] Bright radiant glow around active notes")
    print("   [+] Multiple layers create bloom effect")
    print()
    print("4. CHORD DETECTION & LABELING")
    print("   [+] Automatically detects chord progressions")
    print("   [+] Displays chord names (C major, Am, F, G)")
    print("   [+] Shows for 1.5 seconds with smooth fade")
    print()
    print("5. BEAT EFFECTS")
    print("   [+] Subtle camera shake on beats")
    print("   [+] Zoom pulse synchronized with rhythm")
    print("   [+] Dynamic feel without clutter")
    print()
    print("PREVIOUS FEATURES (Still Active):")
    print("   [+] 3D Perspective scaling")
    print("   [+] Ghosted upcoming notes")
    print("   [+] Motion blur trails")
    print("   [+] Audio-reactive background")
    print("   [+] Waveform visualization")
    print()
    print("-" * 70)
    print("Controls:")
    print("  SPACE - Reset to beginning")
    print("  UP/DOWN - Adjust audio intensity")
    print("  LEFT/RIGHT - Adjust beat intensity")
    print("  ESC - Close")
    print("-" * 70)
    print()
    
    audio_intensity = 0.5
    beat_intensity = 0.5
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    current_time = 0.0
                if event.key == pygame.K_UP:
                    audio_intensity = min(1.0, audio_intensity + 0.1)
                if event.key == pygame.K_DOWN:
                    audio_intensity = max(0.0, audio_intensity - 0.1)
                if event.key == pygame.K_RIGHT:
                    beat_intensity = min(1.0, beat_intensity + 0.1)
                if event.key == pygame.K_LEFT:
                    beat_intensity = max(0.0, beat_intensity - 0.1)
        
        # Update time
        current_time += clock.tick(60) / 1000.0
        
        # Simulate audio with pulsing pattern
        simulated_audio = 0.5 + 0.3 * math.sin(current_time * 2)
        
        # Simulate beats every 1 second with varying intensity
        beat_phase = (current_time % 1.0)
        simulated_beat = 1.0 if beat_phase < 0.1 else (0.3 if beat_phase < 0.5 else 0.1)
        
        # Set effects
        renderer.set_playback_time(current_time)
        renderer.set_audio_intensity(simulated_audio * audio_intensity)
        renderer.set_beat_intensity(simulated_beat * beat_intensity)
        renderer.render()
        
        # Display info
        fps = clock.get_fps()
        pygame.display.set_caption(
            f"Advanced Visualizer | Time: {current_time:.1f}s | "
            f"Audio: {simulated_audio:.2f} | Beat: {simulated_beat:.2f} | "
            f"FPS: {fps:.0f}"
        )
        pygame.display.flip()
    
    pygame.quit()
    print("\n" + "=" * 70)
    print("Test completed successfully!")
    print("All advanced visual effects are now available in your application!")
    print("=" * 70)

if __name__ == '__main__':
    test_advanced_effects()
