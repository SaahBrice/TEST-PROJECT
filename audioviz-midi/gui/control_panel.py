# gui/control_panel.py
"""
Control Panel Widget for AudioViz MIDI.
Provides playback controls including play, pause, stop, timeline slider, and speed control.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
    QSlider, QLabel, QComboBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from utils.logger import get_logger

logger = get_logger(__name__)


class ControlPanel(QWidget):
    """
    Playback control panel with transport buttons and timeline.
    
    Signals:
        play_clicked: Emitted when play button is clicked
        pause_clicked: Emitted when pause button is clicked
        stop_clicked: Emitted when stop button is clicked
        seek_requested: Emitted with position (0.0 to 1.0) when timeline is moved
        speed_changed: Emitted with speed value (0.5, 1.0, 1.5, 2.0)
    """
    
    # Signals
    play_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    seek_requested = pyqtSignal(float)  # Position from 0.0 to 1.0
    speed_changed = pyqtSignal(float)  # Speed multiplier
    
    def __init__(self, parent=None):
        """
        Initialize the control panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # State
        self.is_playing = False
        self.total_duration = 0.0
        self.current_time = 0.0
        self.is_enabled = False
        
        # Setup UI
        self._setup_ui()
        
        # Initially disabled until transcription complete
        self.set_enabled(False)
        
        logger.debug("ControlPanel initialized")
    
    def _setup_ui(self):
        """Set up the control panel UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(8)
        
        # Timeline section
        timeline_layout = QHBoxLayout()
        
        # Current time label
        self.time_label = QLabel('00:00')
        self.time_label.setMinimumWidth(50)
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        timeline_layout.addWidget(self.time_label)
        
        # Timeline slider
        self.timeline_slider = QSlider(Qt.Horizontal)
        self.timeline_slider.setMinimum(0)
        self.timeline_slider.setMaximum(1000)  # Use 1000 steps for smooth seeking
        self.timeline_slider.setValue(0)
        self.timeline_slider.setEnabled(False)
        self.timeline_slider.sliderPressed.connect(self._on_slider_pressed)
        self.timeline_slider.sliderReleased.connect(self._on_slider_released)
        self.timeline_slider.sliderMoved.connect(self._on_slider_moved)
        timeline_layout.addWidget(self.timeline_slider, stretch=1)
        
        # Duration label
        self.duration_label = QLabel('00:00')
        self.duration_label.setMinimumWidth(50)
        self.duration_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        timeline_layout.addWidget(self.duration_label)
        
        main_layout.addLayout(timeline_layout)
        
        # Controls section
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        # Play button
        self.play_button = QPushButton('▶ Play')
        self.play_button.setMinimumWidth(80)
        self.play_button.setMinimumHeight(35)
        self.play_button.clicked.connect(self._on_play_clicked)
        controls_layout.addWidget(self.play_button)
        
        # Pause button
        self.pause_button = QPushButton('⏸ Pause')
        self.pause_button.setMinimumWidth(80)
        self.pause_button.setMinimumHeight(35)
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self._on_pause_clicked)
        controls_layout.addWidget(self.pause_button)
        
        # Stop button
        self.stop_button = QPushButton('⏹ Stop')
        self.stop_button.setMinimumWidth(80)
        self.stop_button.setMinimumHeight(35)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        controls_layout.addWidget(self.stop_button)
        
        # Spacer
        controls_layout.addSpacerItem(
            QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        
        # Speed control
        speed_label = QLabel('Speed:')
        controls_layout.addWidget(speed_label)
        
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(['0.5x', '0.75x', '1.0x', '1.25x', '1.5x', '2.0x'])
        self.speed_combo.setCurrentText('1.0x')
        self.speed_combo.setMinimumWidth(80)
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)
        controls_layout.addWidget(self.speed_combo)
        
        main_layout.addLayout(controls_layout)
        
        # Apply styling
        self._apply_style()
    
    def _apply_style(self):
        """Apply custom styling to control panel."""
        self.setStyleSheet("""
            QWidget {
                background-color: #252530;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #3a3a44;
                color: #e0e0e0;
                border: 1px solid #4a4a54;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a54;
                border: 1px solid #5a5a64;
            }
            QPushButton:pressed {
                background-color: #2a2a34;
            }
            QPushButton:disabled {
                background-color: #2a2a34;
                color: #666;
                border: 1px solid #3a3a44;
            }
            QPushButton#play_active {
                background-color: #4a9eff;
                border: 1px solid #5aaaff;
            }
            QSlider::groove:horizontal {
                border: 1px solid #3a3a44;
                height: 8px;
                background: #1e1e28;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4a9eff;
                border: 1px solid #5aaaff;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #5aaaff;
            }
            QSlider::sub-page:horizontal {
                background: #4a9eff;
                border: 1px solid #3a3a44;
                height: 8px;
                border-radius: 4px;
            }
            QComboBox {
                background-color: #3a3a44;
                color: #e0e0e0;
                border: 1px solid #4a4a54;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox:hover {
                border: 1px solid #5a5a64;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #e0e0e0;
                margin-right: 5px;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 12px;
            }
        """)
    
    # Event Handlers
    
    def _on_play_clicked(self):
        """Handle play button click."""
        logger.info("Play button clicked")
        self.play_clicked.emit()
    
    def _on_pause_clicked(self):
        """Handle pause button click."""
        logger.info("Pause button clicked")
        self.pause_clicked.emit()
    
    def _on_stop_clicked(self):
        """Handle stop button click."""
        logger.info("Stop button clicked")
        self.stop_clicked.emit()
    
    def _on_slider_pressed(self):
        """Handle timeline slider press."""
        logger.debug("Timeline slider pressed")
    
    def _on_slider_released(self):
        """Handle timeline slider release."""
        # Emit seek request with normalized position (0.0 to 1.0)
        position = self.timeline_slider.value() / 1000.0
        logger.info(f"Seek requested to position: {position:.3f}")
        self.seek_requested.emit(position)
    
    def _on_slider_moved(self, value):
        """
        Handle timeline slider movement.
        
        Args:
            value: Slider value (0-1000)
        """
        # Update time label while dragging
        position = value / 1000.0
        time_seconds = position * self.total_duration
        self._update_time_label(time_seconds)
    
    def _on_speed_changed(self, text):
        """
        Handle speed selection change.
        
        Args:
            text: Selected speed text (e.g., "1.0x")
        """
        # Extract numeric value
        speed = float(text.replace('x', ''))
        logger.info(f"Playback speed changed to {speed}x")
        self.speed_changed.emit(speed)
    
    # Public Methods
    
    def set_enabled(self, enabled: bool):
        """
        Enable or disable the control panel.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.is_enabled = enabled
        
        self.play_button.setEnabled(enabled)
        self.timeline_slider.setEnabled(enabled)
        self.speed_combo.setEnabled(enabled)
        
        # Pause and Stop start disabled even when panel is enabled
        if not enabled:
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(False)
        
        logger.debug(f"Control panel {'enabled' if enabled else 'disabled'}")
    
    def set_duration(self, duration: float):
        """
        Set the total duration for timeline.
        
        Args:
            duration: Total duration in seconds
        """
        self.total_duration = duration
        self.duration_label.setText(self._format_time(duration))
        logger.debug(f"Duration set to {duration:.2f}s")
    
    def set_playback_position(self, time: float):
        """
        Update playback position.
        
        Args:
            time: Current time in seconds
        """
        self.current_time = time
        
        # Update time label
        self._update_time_label(time)
        
        # Update slider position (but don't trigger signals)
        if self.total_duration > 0:
            position = time / self.total_duration
            slider_value = int(position * 1000)
            self.timeline_slider.blockSignals(True)
            self.timeline_slider.setValue(slider_value)
            self.timeline_slider.blockSignals(False)
    
    def set_playing(self, playing: bool):
        """
        Update UI for playing/stopped state.
        
        Args:
            playing: True if playing, False if stopped
        """
        self.is_playing = playing
        
        if playing:
            # Playing state
            self.play_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            logger.debug("Playback state: Playing")
        else:
            # Stopped state
            self.play_button.setEnabled(self.is_enabled)
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            logger.debug("Playback state: Stopped")
    
    def reset(self):
        """Reset control panel to initial state."""
        self.set_playback_position(0.0)
        self.set_playing(False)
        self.set_enabled(False)
        self.total_duration = 0.0
        self.time_label.setText('00:00')
        self.duration_label.setText('00:00')
        self.speed_combo.setCurrentText('1.0x')
        logger.debug("Control panel reset")
    
    # Helper Methods
    
    def _update_time_label(self, time: float):
        """
        Update the current time label.
        
        Args:
            time: Current time in seconds
        """
        self.time_label.setText(self._format_time(time))
    
    def _format_time(self, seconds: float) -> str:
        """
        Format time in seconds as MM:SS string.
        
        Args:
            seconds: Time in seconds
        
        Returns:
            Formatted time string
        """
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f'{minutes:02d}:{secs:02d}'
