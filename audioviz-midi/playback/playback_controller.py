# playback/playback_controller.py
"""
Playback Controller for AudioViz MIDI.
Manages audio playback state and synchronization with visualization.
"""

import pygame
import time
from enum import Enum
from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from utils.logger import get_logger

logger = get_logger(__name__)


class PlaybackState(Enum):
    """Playback state enumeration."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class PlaybackController(QObject):
    """
    Controls audio playback and manages synchronization.
    
    Signals:
        state_changed: Emitted when playback state changes
        time_updated: Emitted with current time position
        playback_finished: Emitted when playback completes
    """
    
    # Signals
    state_changed = pyqtSignal(object)  # PlaybackState
    time_updated = pyqtSignal(float)  # current_time in seconds
    playback_finished = pyqtSignal()
    
    def __init__(self):
        """Initialize the playback controller."""
        super().__init__()
        
        # Initialize pygame mixer
        self._init_mixer()
        
        # Playback state
        self.state = PlaybackState.STOPPED
        self.audio_file = None
        self.duration = 0.0
        self.current_time = 0.0
        self.playback_speed = 1.0
        self.volume = 0.8
        
        # Timing
        self.start_time = 0.0  # Time when playback started
        self.pause_time = 0.0  # Position when paused
        
        # MIDI data for keyboard-hit sync (optional)
        self.midi_data = None
        self.midi_keyboard_offset = 0.0  # Time offset to reach keyboard
        
        # Update timer for position tracking
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_position)
        self.update_timer.setInterval(16)  # ~60 FPS updates
        
        logger.info("PlaybackController initialized")
    
    def _init_mixer(self):
        """Initialize pygame mixer for audio playback."""
        try:
            # Initialize mixer with specific settings for better quality
            pygame.mixer.init(
                frequency=22050,  # Sample rate
                size=-16,  # 16-bit signed
                channels=2,  # Stereo
                buffer=512  # Buffer size
            )
            logger.info("Pygame mixer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize mixer: {e}")
    
    def load_audio(self, audio_file: str, duration: float):
        """
        Load audio file for playback.
        
        Args:
            audio_file: Path to audio file
            duration: Duration in seconds
        """
        try:
            logger.info(f"Loading audio file: {audio_file}")
            
            # Stop any current playback
            self.stop()
            
            # Load audio file
            pygame.mixer.music.load(audio_file)
            
            # Set volume
            pygame.mixer.music.set_volume(self.volume)
            
            # Store file info
            self.audio_file = audio_file
            self.duration = duration
            self.current_time = 0.0
            
            logger.info(f"Audio loaded: duration={duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to load audio: {e}")
            raise Exception(f"Failed to load audio: {e}")
    
    def set_midi_data(self, midi_data, keyboard_offset: float = 0.0):
        """
        Set MIDI data for keyboard-synchronized playback.
        
        When MIDI data is set, audio playback will be delayed so that
        sounds trigger when notes visually hit the piano keyboard.
        
        Args:
            midi_data: MIDIData object containing note information
            keyboard_offset: Time offset (in seconds) to reach keyboard
                           (calculated from note start time)
        """
        self.midi_data = midi_data
        self.midi_keyboard_offset = keyboard_offset
        logger.info(f"MIDI data set with keyboard offset: {keyboard_offset:.3f}s")
    
    def play(self):
        """Start or resume playback."""
        if not self.audio_file:
            logger.warning("No audio file loaded")
            return
        
        if self.state == PlaybackState.PLAYING:
            logger.warning("Already playing")
            return
        
        logger.info("Starting playback")
        
        if self.state == PlaybackState.PAUSED:
            # Resume from pause
            pygame.mixer.music.unpause()
            self.start_time = time.time() - self.pause_time
        else:
            # Start from current position
            start_position = self.current_time
            
            # Apply MIDI keyboard offset if set
            # This delays audio playback so sound triggers when notes hit the keyboard
            actual_start_position = max(0.0, start_position - self.midi_keyboard_offset)
            
            # Note: pygame.mixer.music doesn't support start position directly
            # So we play from beginning and fast-forward if needed
            pygame.mixer.music.play(start=actual_start_position)
            self.start_time = time.time() - actual_start_position
        
        # Update state
        self._set_state(PlaybackState.PLAYING)
        
        # Start position updates
        self.update_timer.start()
    
    def pause(self):
        """Pause playback."""
        if self.state != PlaybackState.PLAYING:
            logger.warning("Not currently playing")
            return
        
        logger.info("Pausing playback")
        
        # Pause audio
        pygame.mixer.music.pause()
        
        # Save pause position
        self.pause_time = self.current_time
        
        # Update state
        self._set_state(PlaybackState.PAUSED)
        
        # Stop position updates
        self.update_timer.stop()
    
    def stop(self):
        """Stop playback and reset to beginning."""
        if self.state == PlaybackState.STOPPED:
            return
        
        logger.info("Stopping playback")
        
        # Stop audio
        pygame.mixer.music.stop()
        
        # Reset position
        self.current_time = 0.0
        self.pause_time = 0.0
        
        # Update state
        self._set_state(PlaybackState.STOPPED)
        
        # Stop position updates
        self.update_timer.stop()
        
        # Emit time update for reset
        self.time_updated.emit(0.0)
    
    def seek(self, position: float):
        """
        Seek to specific position.
        
        Args:
            position: Position from 0.0 to 1.0
        """
        if not self.audio_file:
            logger.warning("No audio file loaded")
            return
        
        # Calculate time
        seek_time = position * self.duration
        seek_time = max(0.0, min(seek_time, self.duration))
        
        logger.info(f"Seeking to {seek_time:.2f}s ({position:.1%})")
        
        # Store current state
        was_playing = (self.state == PlaybackState.PLAYING)
        
        # Stop current playback
        if self.state != PlaybackState.STOPPED:
            pygame.mixer.music.stop()
        
        # Update position
        self.current_time = seek_time
        self.pause_time = seek_time
        
        # Restart if was playing
        if was_playing:
            # Apply keyboard offset for delayed audio
            actual_seek_time = max(0.0, seek_time - self.midi_keyboard_offset)
            pygame.mixer.music.play(start=actual_seek_time)
            self.start_time = time.time() - actual_seek_time
            self._set_state(PlaybackState.PLAYING)
        else:
            self._set_state(PlaybackState.STOPPED)
        
        # Emit time update
        self.time_updated.emit(seek_time)
    
    def set_speed(self, speed: float):
        """
        Set playback speed.
        
        Note: pygame.mixer doesn't support speed change during playback,
        so this is a placeholder for future implementation.
        
        Args:
            speed: Speed multiplier (0.5 to 2.0)
        """
        logger.info(f"Speed change requested: {speed}x (not yet implemented)")
        self.playback_speed = speed
        
        # Note: Full speed control requires additional audio processing
        # For MVP, we acknowledge the limitation
        logger.warning("Playback speed adjustment not available in pygame.mixer")
    
    def set_volume(self, volume: float):
        """
        Set playback volume.
        
        Args:
            volume: Volume from 0.0 to 1.0
        """
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)
        logger.debug(f"Volume set to {self.volume:.2f}")
    
    def _update_position(self):
        """Update current playback position (called by timer)."""
        if self.state != PlaybackState.PLAYING:
            return
        
        # Calculate current position based on elapsed time
        elapsed = time.time() - self.start_time
        self.current_time = elapsed
        
        # Check if playback finished
        if self.current_time >= self.duration:
            logger.info("Playback finished")
            self.stop()
            self.playback_finished.emit()
            return
        
        # Check if audio actually stopped (pygame quirk)
        if not pygame.mixer.music.get_busy():
            logger.info("Audio stopped playing")
            self.stop()
            self.playback_finished.emit()
            return
        
        # Emit time update
        self.time_updated.emit(self.current_time)
    
    def _set_state(self, new_state: PlaybackState):
        """
        Update playback state and emit signal.
        
        Args:
            new_state: New playback state
        """
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            logger.debug(f"State changed: {old_state.value} -> {new_state.value}")
            self.state_changed.emit(new_state)
    
    def get_state(self) -> PlaybackState:
        """
        Get current playback state.
        
        Returns:
            Current PlaybackState
        """
        return self.state
    
    def get_current_time(self) -> float:
        """
        Get current playback position.
        
        Returns:
            Current time in seconds
        """
        return self.current_time
    
    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up playback controller")
        self.stop()
        self.update_timer.stop()
        pygame.mixer.quit()
