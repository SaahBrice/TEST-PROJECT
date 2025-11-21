#!/usr/bin/env python3
"""
Quick test to verify the rotated piano roll visualization works.
"""

import sys
import os

# Add audioviz-midi to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'audioviz-midi'))

import pygame
from midi import MIDIData, Note
from visualization.piano_roll_renderer import PianoRollRenderer
from utils.config import ConfigManager

def test_rotation():
    """Test the rotated piano roll renderer."""
    # Initialize Pygame
    pygame.init()
    
    # Create a surface
    width, height = 1200, 800
    surface = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Piano Roll Rotation Test")
    
    # Create config
    config = ConfigManager()
    
    # Create renderer
    renderer = PianoRollRenderer(surface, config)
    
    # Create test MIDI data
    midi_data = MIDIData()
    
    # Add some test notes across the range
    notes = [
        Note(pitch=36, start_time=0.5, end_time=0.8, velocity=100),   # C1
        Note(pitch=48, start_time=1.0, end_time=1.4, velocity=100),   # C2
        Note(pitch=60, start_time=1.5, end_time=2.0, velocity=100),   # C3
        Note(pitch=72, start_time=2.0, end_time=2.3, velocity=100),   # C4
        Note(pitch=84, start_time=2.5, end_time=2.9, velocity=100),   # C5
        Note(pitch=50, start_time=0.8, end_time=1.4, velocity=80),    # D#2
        Note(pitch=62, start_time=1.3, end_time=2.0, velocity=80),    # D3
        Note(pitch=74, start_time=1.8, end_time=2.3, velocity=80),    # D4
    ]
    
    for note in notes:
        midi_data.add_note(note)
    
    renderer.set_midi_data(midi_data)
    
    # Test rendering at different time points
    clock = pygame.time.Clock()
    running = True
    current_time = 0.0
    
    print("Testing rotated piano roll renderer...")
    print(f"Surface: {width}x{height}")
    print(f"Keyboard height: {renderer.keyboard_height}px")
    print(f"Note width: {renderer.note_width}px")
    print(f"MIDI data: {len(midi_data)} notes")
    print()
    print("Keyboard should be at BOTTOM")
    print("Notes should flow from TOP to BOTTOM (waterfall style)")
    print()
    print("Press ESC to close the test window")
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # Space to pause/resume
                if event.key == pygame.K_SPACE:
                    current_time = 0.0
        
        # Update time
        current_time += clock.tick(60) / 1000.0
        
        # Set playback time and render
        renderer.set_playback_time(current_time)
        renderer.render()
        
        # Display FPS
        pygame.display.set_caption(f"Piano Roll Rotation Test - Time: {current_time:.1f}s")
        pygame.display.flip()
    
    pygame.quit()
    print("\nTest completed successfully!")
    print("If you saw:")
    print("  - Keyboard at the BOTTOM")
    print("  - Notes flowing from TOP to BOTTOM (waterfall style)")
    print("  - Horizontal playhead line at 2/3 from top")
    print("  - Notes scrolling downward toward the playhead")
    print("Then the rotation is working correctly!")

if __name__ == '__main__':
    test_rotation()
