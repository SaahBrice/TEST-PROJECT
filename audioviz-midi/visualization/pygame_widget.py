# visualization/pygame_widget.py
"""
Pygame Widget for AudioViz MIDI.
Embeds a Pygame display surface within a PyQt5 widget for visualization rendering.
"""

import pygame
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt
from utils.logger import get_logger

logger = get_logger(__name__)


class PygameWidget(QWidget):
    """
    Custom Qt widget that embeds a Pygame display surface.
    
    Handles initialization of Pygame, surface creation, and frame updates
    while remaining compatible with PyQt5 event loop.
    """
    
    def __init__(self, parent=None, target_fps=60):
        """
        Initialize the Pygame widget.
        
        Args:
            parent: Parent QWidget
            target_fps: Target frames per second for rendering
        """
        super().__init__(parent)
        
        self.target_fps = target_fps
        self.is_initialized = False
        self.screen = None
        self.clock = None
        
        # Set up widget properties
        self.setMinimumSize(800, 400)
        
        # Initialize Pygame
        self._init_pygame()
        
        # Set up frame update timer
        self._setup_timer()
        
        logger.info("PygameWidget initialized")
    
    def _init_pygame(self):
        """Initialize Pygame and create display surface."""
        try:
            # IMPORTANT: Set SDL window ID BEFORE pygame.init()
            os.environ['SDL_WINDOWID'] = str(int(self.winId()))
            
            # For Windows: also set these environment variables
            if os.name == 'nt':  # Windows
                os.environ['SDL_VIDEODRIVER'] = 'windib'
            
            # Initialize Pygame
            if not pygame.get_init():
                pygame.init()
            
            # Initialize display
            if not pygame.display.get_init():
                pygame.display.init()
            
            # CRITICAL: Small delay to let Qt widget fully initialize
            from PyQt5.QtCore import QCoreApplication
            QCoreApplication.processEvents()
            
            # Create display surface with NOFRAME flag
            size = (self.width(), self.height())
            self.screen = pygame.display.set_mode(size, pygame.NOFRAME)
            
            # Create clock for frame timing
            self.clock = pygame.time.Clock()
            
            # Initial clear to black
            self.screen.fill((30, 30, 40))  # Dark background
            pygame.display.flip()
            
            self.is_initialized = True
            logger.info(f"Pygame initialized with surface size: {size}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pygame: {e}")
            self.is_initialized = False



        """Initialize Pygame and create display surface."""
        try:
            # Set SDL to use windowed mode (required for embedding)
            os.environ['SDL_WINDOWID'] = str(int(self.winId()))
            
            # Initialize Pygame
            pygame.init()
            pygame.display.init()
            
            # Create display surface
            size = (self.width(), self.height())
            self.screen = pygame.display.set_mode(size, pygame.HWSURFACE | pygame.DOUBLEBUF)
            
            # Create clock for frame timing
            self.clock = pygame.time.Clock()
            
            # Initial clear to black
            self.screen.fill((30, 30, 40))  # Dark background
            pygame.display.flip()
            
            self.is_initialized = True
            logger.info(f"Pygame initialized with surface size: {size}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pygame: {e}")
            self.is_initialized = False
    
    def _setup_timer(self):
        """Set up Qt timer for frame updates."""
        # Create timer for regular frame updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_frame)
        
        # Calculate interval in milliseconds
        interval_ms = int(1000 / self.target_fps)
        self.update_timer.setInterval(interval_ms)
        
        # Start timer
        self.update_timer.start()
        
        logger.debug(f"Frame update timer started at {self.target_fps} FPS ({interval_ms}ms interval)")
    
    def _update_frame(self):
        """Update frame - called by Qt timer."""
        if not self.is_initialized:
            return
        
        try:
            # Process Pygame events (required for proper integration)
            pygame.event.pump()
            
            # Render frame (will be overridden by subclasses)
            self._render()
            
            # Update display
            pygame.display.flip()
            
            # Maintain frame rate
            self.clock.tick(self.target_fps)
            
        except Exception as e:
            logger.error(f"Error updating frame: {e}")
    
    def _render(self):
        """
        Render the frame (placeholder - override in subclasses).
        Default implementation shows a test pattern.
        """
        # Clear screen with dark background
        self.screen.fill((30, 30, 40))
        
        # Draw test pattern (will be replaced with actual visualization)
        self._draw_test_pattern()
    
    def _draw_test_pattern(self):
        """Draw a simple test pattern to verify Pygame is working."""
        width, height = self.screen.get_size()
        
        # Draw centered text
        try:
            font = pygame.font.Font(None, 48)
            text = font.render('Pygame Visualization', True, (100, 100, 100))
            text_rect = text.get_rect(center=(width // 2, height // 2 - 40))
            self.screen.blit(text, text_rect)
            
            # Draw subtitle
            small_font = pygame.font.Font(None, 24)
            subtitle = small_font.render('Visualization will appear here', True, (80, 80, 80))
            subtitle_rect = subtitle.get_rect(center=(width // 2, height // 2 + 20))
            self.screen.blit(subtitle, subtitle_rect)
            
            # Draw border rectangle
            border_color = (60, 60, 70)
            pygame.draw.rect(self.screen, border_color, (10, 10, width - 20, height - 20), 2)
            
            # Draw grid pattern
            grid_color = (40, 40, 50)
            for x in range(0, width, 50):
                pygame.draw.line(self.screen, grid_color, (x, 0), (x, height), 1)
            for y in range(0, height, 50):
                pygame.draw.line(self.screen, grid_color, (0, y), (width, y), 1)
                
        except Exception as e:
            logger.error(f"Error drawing test pattern: {e}")
    
    def resizeEvent(self, event):
        """
        Handle widget resize events.
        
        Args:
            event: QResizeEvent
        """
        super().resizeEvent(event)
        
        if self.is_initialized:
            # Resize Pygame surface
            new_size = (self.width(), self.height())
            try:
                self.screen = pygame.display.set_mode(new_size, pygame.HWSURFACE | pygame.DOUBLEBUF)
                logger.debug(f"Pygame surface resized to: {new_size}")
            except Exception as e:
                logger.error(f"Error resizing Pygame surface: {e}")
    
    def cleanup(self):
        """Clean up Pygame resources."""
        if self.is_initialized:
            logger.info("Cleaning up Pygame resources")
            self.update_timer.stop()
            pygame.quit()
            self.is_initialized = False
    
    def closeEvent(self, event):
        """Handle widget close event."""
        self.cleanup()
        super().closeEvent(event)
