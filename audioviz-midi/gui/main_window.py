# gui/main_window.py
"""
Main Window Module for AudioViz MIDI.
Creates the primary application window with menu bar, toolbar, 
central visualization area, control panel, and status bar.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QAction, QToolBar, QStatusBar,
    QLabel, QFileDialog, QMessageBox, QProgressBar
)
from gui.control_panel import ControlPanel
from visualization import PygameWidget
from gui.processing_thread import ProcessingThread
from gui.file_drop_widget import FileDropWidget
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QIcon, QKeySequence
from utils.logger import get_logger
from utils.config import ConfigManager

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window for AudioViz MIDI.
    
    Provides the primary user interface with menu bar for file operations,
    toolbar for quick actions, central area for visualization,
    control panel for playback, and status bar for messages.
    """
    
    def __init__(self, config: ConfigManager = None):
        """
        Initialize the main window.
        
        Args:
            config: Configuration manager instance
        """
        super().__init__()
        
        self.config = config or ConfigManager()
        
        # Application state
        self.current_file = None
        self.is_processing = False
        self.processing_thread = None
        self.midi_data = None  # Store transcription result
        self.pygame_widget = None

        # Initialize UI components
        self._init_ui()
        
        logger.info("Main window initialized")
    
    def _init_ui(self):
        """Initialize all UI components."""
        # Set window properties
        self._setup_window()
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create toolbar
        self._create_toolbar()
        
        # Create central widget (will hold visualization)
        self._create_central_widget()
        
        # Create status bar
        self._create_status_bar()
        
        # Apply dark theme
        self._apply_theme()
        
        logger.debug("UI components created")
    
    def _setup_window(self):
        """Configure main window properties."""
        # Set window title
        self.setWindowTitle("AudioViz MIDI - Audio to MIDI Converter")
        
        # Load window size from config
        width = self.config.get('ui', 'window_width', 1280)
        height = self.config.get('ui', 'window_height', 720)
        self.resize(width, height)
        
        # Set minimum size
        self.setMinimumSize(800, 600)
        
        # Center window on screen
        self._center_window()
        
        logger.debug(f"Window size set to {width}x{height}")
    
    def _center_window(self):
        """Center the window on the screen."""
        frame_geometry = self.frameGeometry()
        from PyQt5.QtWidgets import QDesktopWidget
        center_point = QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())
    
    def _create_menu_bar(self):
        """Create the menu bar with File, Edit, View, and Help menus."""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu('&File')
        
        # Open Audio action
        open_action = QAction('&Open Audio...', self)
        open_action.setShortcut(QKeySequence.Open)  # Ctrl+O
        open_action.setStatusTip('Open an audio file for transcription')
        open_action.triggered.connect(self._on_open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Export MIDI action
        export_midi_action = QAction('Export &MIDI...', self)
        export_midi_action.setShortcut('Ctrl+M')
        export_midi_action.setStatusTip('Export as MIDI file')
        export_midi_action.setEnabled(False)  # Disabled until transcription complete
        export_midi_action.triggered.connect(self._on_export_midi)
        file_menu.addAction(export_midi_action)
        self.export_midi_action = export_midi_action
        
        # Export JSON action
        export_json_action = QAction('Export &JSON...', self)
        export_json_action.setShortcut('Ctrl+J')
        export_json_action.setStatusTip('Export as JSON file')
        export_json_action.setEnabled(False)  # Disabled until transcription complete
        export_json_action.triggered.connect(self._on_export_json)
        file_menu.addAction(export_json_action)
        self.export_json_action = export_json_action
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut(QKeySequence.Quit)  # Ctrl+Q
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit Menu
        edit_menu = menubar.addMenu('&Edit')
        
        # Settings action
        settings_action = QAction('&Settings...', self)
        settings_action.setShortcut('Ctrl+,')
        settings_action.setStatusTip('Open settings dialog')
        settings_action.triggered.connect(self._on_settings)
        edit_menu.addAction(settings_action)
        
        # View Menu
        view_menu = menubar.addMenu('&View')
        
        # Fullscreen action
        fullscreen_action = QAction('&Fullscreen', self)
        fullscreen_action.setShortcut('F11')
        fullscreen_action.setStatusTip('Toggle fullscreen mode')
        fullscreen_action.setCheckable(True)
        fullscreen_action.triggered.connect(self._on_toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        self.fullscreen_action = fullscreen_action
        
        view_menu.addSeparator()
        
        # Get screen size for validation
        screen_width, screen_height = self._get_screen_size()
        
        # Window size presets with screen size validation
        size_1080p_action = QAction('1080p (1920x1080)', self)
        size_1080p_action.setStatusTip('Resize window to 1080p')
        size_1080p_action.triggered.connect(lambda: self._set_window_size(1920, 1080))
        # Disable if too large for screen
        if 1920 > screen_width or 1080 > screen_height:
            size_1080p_action.setEnabled(False)
            size_1080p_action.setText('1080p (1920x1080) - Too large for screen')
        view_menu.addAction(size_1080p_action)
        
        size_1440p_action = QAction('1440p (2560x1440)', self)
        size_1440p_action.setStatusTip('Resize window to 1440p')
        size_1440p_action.triggered.connect(lambda: self._set_window_size(2560, 1440))
        # Disable if too large for screen
        if 2560 > screen_width or 1440 > screen_height:
            size_1440p_action.setEnabled(False)
            size_1440p_action.setText('1440p (2560x1440) - Too large for screen')
        view_menu.addAction(size_1440p_action)
        
        size_4k_action = QAction('4K (3840x2160)', self)
        size_4k_action.setStatusTip('Resize window to 4K')
        size_4k_action.triggered.connect(lambda: self._set_window_size(3840, 2160))
        # Disable if too large for screen
        if 3840 > screen_width or 2160 > screen_height:
            size_4k_action.setEnabled(False)
            size_4k_action.setText('4K (3840x2160) - Too large for screen')
        view_menu.addAction(size_4k_action)
        
        # Reset to default size action
        reset_size_action = QAction('Reset to &Default Size', self)
        reset_size_action.setShortcut('Ctrl+0')
        reset_size_action.setStatusTip('Reset window to default size (1280x720)')
        reset_size_action.triggered.connect(self._reset_window_size)
        view_menu.addAction(reset_size_action)
        
        # Help Menu
        help_menu = menubar.addMenu('&Help')
        
        # About action
        about_action = QAction('&About...', self)
        about_action.setStatusTip('About AudioViz MIDI')
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
        
        logger.debug("Menu bar created")
    
    def _create_toolbar(self):
        """Create the toolbar with quick action buttons."""
        toolbar = QToolBar('Main Toolbar')
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Open Audio button
        open_audio_action = QAction('Open Audio', self)
        open_audio_action.setStatusTip('Open an audio file')
        open_audio_action.triggered.connect(self._on_open_file)
        toolbar.addAction(open_audio_action)
        
        toolbar.addSeparator()
        
        # Transcribe button
        transcribe_action = QAction('Transcribe', self)
        transcribe_action.setStatusTip('Start audio transcription')
        transcribe_action.setEnabled(False)  # Disabled until file loaded
        transcribe_action.triggered.connect(self._on_transcribe)
        toolbar.addAction(transcribe_action)
        self.transcribe_action = transcribe_action
        
        toolbar.addSeparator()
        
        # Export button
        export_action = QAction('Export', self)
        export_action.setStatusTip('Export MIDI or JSON')
        export_action.setEnabled(False)  # Disabled until transcription complete
        export_action.triggered.connect(self._on_export_midi)
        toolbar.addAction(export_action)
        self.export_action = export_action
        
        logger.debug("Toolbar created")
    

    def _create_central_widget(self):
        """Create the central widget area."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create container for file drop and pygame visualization
        from PyQt5.QtWidgets import QStackedWidget
        self.visualization_stack = QStackedWidget()
        
        # File drop widget (shown when no file loaded)
        self.file_drop_widget = FileDropWidget()
        self.file_drop_widget.file_dropped.connect(self._on_file_dropped)
        self.visualization_stack.addWidget(self.file_drop_widget)  # Index 0
        
        # Pygame visualization widget (shown during/after transcription)
        self.pygame_widget = PygameWidget()
        self.visualization_stack.addWidget(self.pygame_widget)  # Index 1
        
        # Start with file drop widget
        self.visualization_stack.setCurrentIndex(0)
        
        main_layout.addWidget(self.visualization_stack, stretch=1)
        
        # Control panel with playback controls
        self.control_panel = ControlPanel()
        self.control_panel.setMinimumHeight(100)
        self.control_panel.setMaximumHeight(120)
        
        # Connect control panel signals
        self.control_panel.play_clicked.connect(self._on_play)
        self.control_panel.pause_clicked.connect(self._on_pause)
        self.control_panel.stop_clicked.connect(self._on_stop)
        self.control_panel.seek_requested.connect(self._on_seek)
        self.control_panel.speed_changed.connect(self._on_speed_changed)
        
        main_layout.addWidget(self.control_panel)
        
        logger.debug("Central widget created with Pygame visualization")




    def _create_status_bar(self):
        """Create the status bar."""
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)
        
        # Status label (main message area)
        self.status_label = QLabel('Ready')
        statusbar.addWidget(self.status_label, stretch=1)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        statusbar.addPermanentWidget(self.progress_bar)
        
        # Time display (right side)
        self.time_label = QLabel('00:00 / 00:00')
        self.time_label.setMinimumWidth(100)
        self.time_label.setAlignment(Qt.AlignRight)
        statusbar.addPermanentWidget(self.time_label)
        
        logger.debug("Status bar created")
    
    def _apply_theme(self):
        """Apply dark theme stylesheet."""
        dark_theme = """
        QMainWindow {
            background-color: #1e1e28;
        }
        QMenuBar {
            background-color: #252530;
            color: #e0e0e0;
            border-bottom: 1px solid #3a3a44;
        }
        QMenuBar::item:selected {
            background-color: #3a3a44;
        }
        QMenu {
            background-color: #252530;
            color: #e0e0e0;
            border: 1px solid #3a3a44;
        }
        QMenu::item:selected {
            background-color: #3a3a44;
        }
        QToolBar {
            background-color: #252530;
            border-bottom: 1px solid #3a3a44;
            spacing: 5px;
            padding: 5px;
        }
        QStatusBar {
            background-color: #252530;
            color: #e0e0e0;
            border-top: 1px solid #3a3a44;
        }
        QLabel {
            color: #e0e0e0;
        }
        QProgressBar {
            border: 1px solid #3a3a44;
            border-radius: 3px;
            text-align: center;
            color: #e0e0e0;
            background-color: #1e1e28;
        }
        QProgressBar::chunk {
            background-color: #4a9eff;
            border-radius: 2px;
        }
        """
        self.setStyleSheet(dark_theme)
        logger.debug("Dark theme applied")
    
    # Event Handlers
    
    def _on_open_file(self):
        """Handle Open Audio action."""
        logger.info("Open file dialog triggered")
        
        # Get last directory from config
        last_dir = self.config.get('ui', 'last_directory', '')
        
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Open Audio File',
            last_dir,
            'Audio Files (*.wav *.mp3 *.flac *.ogg);;All Files (*.*)'
        )
        
        if file_path:
            import os
            
            logger.info(f"File selected: {file_path}")
            self.current_file = file_path
            
            # Update status
            filename = os.path.basename(file_path)
            self.set_status(f"Loaded: {filename}")
            
            # Save directory to config
            self.config.set('ui', 'last_directory', os.path.dirname(file_path))
            self.config.save_config()
            
            # Enable transcribe button
            self.transcribe_action.setEnabled(True)
            
            # Update visualization widget to GREEN state
            self.file_drop_widget.set_file_loaded(filename)
            
            logger.info(f"File loaded successfully via menu: {filename}")
    

    def _on_file_dropped(self, file_path: str):
        """
        Handle file dropped on widget.
        
        Args:
            file_path: Path to dropped file
        """
        import os
        
        logger.info(f"File dropped: {file_path}")
        
        # Get filename
        filename = os.path.basename(file_path)
        
        # Validate file using AudioLoader
        try:
            from audio import AudioLoader
            loader = AudioLoader()
            is_valid, message = loader.validate_file(file_path)
            
            if is_valid:
                # File is valid
                self.current_file = file_path
                
                # Update status
                self.set_status(f"Loaded: {filename}")
                
                # Save directory to config
                self.config.set('ui', 'last_directory', os.path.dirname(file_path))
                self.config.save_config()
                
                # Enable transcribe button
                self.transcribe_action.setEnabled(True)
                
                # Update visualization widget to GREEN state
                self.file_drop_widget.set_file_loaded(filename)
                
                logger.info(f"File loaded successfully via drag-and-drop: {filename}")
                
                # Show success message if it's a warning (large file)
                if 'Warning' in message:
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(self, 'Large File', message)
            else:
                # File is invalid
                logger.error(f"Invalid file: {message}")
                
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self,
                    'Invalid File',
                    f'Cannot load file:\n\n{message}'
                )
                
                # Reset widget
                self.file_drop_widget.reset()
                
        except Exception as e:
            logger.error(f"Error loading dropped file: {str(e)}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                'Error',
                f'Error loading file:\n\n{str(e)}'
            )
            self.file_drop_widget.reset()



    def _on_transcribe(self):
        """Handle Transcribe action."""
        if not self.current_file:
            logger.warning("No file loaded to transcribe")
            return
        
        if self.is_processing:
            logger.warning("Already processing")
            return
        
        logger.info("=" * 60)
        logger.info("Starting transcription process...")
        logger.info("=" * 60)
        
        # Update UI state
        self.is_processing = True
        self.transcribe_action.setEnabled(False)
        self.export_midi_action.setEnabled(False)
        self.export_json_action.setEnabled(False)
        self.export_action.setEnabled(False)
        
        # Show progress bar
        self.show_progress(True)
        self.set_progress(0)
        self.set_status("Processing...")
        
        # Show processing state on file drop widget
        import os
        self.file_drop_widget.setText(
            f'Processing Audio...\n\n{os.path.basename(self.current_file)}\n\n'
            'Please wait...'
        )
        self.file_drop_widget.setStyleSheet("""
            QLabel {
                background-color: #2a2a38;
                color: #4a9eff;
                border: 3px solid #4a9eff;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        # Create and start processing thread
        self.processing_thread = ProcessingThread(self.current_file)
        self.processing_thread.progress_updated.connect(self._on_progress_updated)
        self.processing_thread.processing_complete.connect(self._on_processing_complete)
        self.processing_thread.processing_error.connect(self._on_processing_error)
        self.processing_thread.start()
        
        logger.info("Background processing thread started")


    def _on_progress_updated(self, percentage: int, message: str):
        """
        Handle progress updates from processing thread.
        
        Args:
            percentage: Progress percentage (0-100)
            message: Status message
        """
        self.set_progress(percentage)
        self.set_status(message)
        logger.debug(f"Progress: {percentage}% - {message}")
    

    def _on_processing_complete(self, midi_data):
        """
        Handle successful completion of processing.
        
        Args:
            midi_data: MIDIData object with transcription results
        """
        logger.info("Processing completed successfully!")
        
        # Store MIDI data
        self.midi_data = midi_data
        
        # Enable control panel and set duration
        stats = midi_data.get_statistics()
        self.control_panel.set_enabled(True)
        self.control_panel.set_duration(stats['duration'])
        
        # Update UI state
        self.is_processing = False
        self.show_progress(False)
        
        # Enable export actions
        self.export_midi_action.setEnabled(True)
        self.export_json_action.setEnabled(True)
        self.export_action.setEnabled(True)
        
        # Switch to Pygame visualization (THIS IS THE NEW PART)
        self.visualization_stack.setCurrentIndex(1)
        
        # Update status
        self.set_status(
            f"Transcription complete! {stats['total_notes']} notes, "
            f"{stats['duration']:.1f}s duration"
        )
        
        # Show success message
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            'Transcription Complete',
            f'Audio successfully transcribed!\n\n'
            f'Notes detected: {stats["total_notes"]}\n'
            f'Duration: {stats["duration"]:.1f}s\n\n'
            f'You can now export the MIDI file.'
        )
        
        # Enable transcribe button for re-processing
        self.transcribe_action.setEnabled(True)



    def _on_play(self):
        """Handle play button from control panel."""
        logger.info("Play requested from control panel")
        
        if not self.midi_data:
            logger.warning("No MIDI data available for playback")
            return
        
        # Update control panel state
        self.control_panel.set_playing(True)
        
        # Placeholder for actual playback (will implement in Phase 5)
        self.set_status("Playback will be implemented in Phase 5")
        
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            'Coming Soon',
            'Playback functionality will be added in Phase 5!\n\n'
            'For now, the controls are functional and ready.'
        )
    
    def _on_pause(self):
        """Handle pause button from control panel."""
        logger.info("Pause requested from control panel")
        self.control_panel.set_playing(False)
        self.set_status("Paused")
    
    def _on_stop(self):
        """Handle stop button from control panel."""
        logger.info("Stop requested from control panel")
        self.control_panel.set_playing(False)
        self.control_panel.set_playback_position(0.0)
        self.set_status("Stopped")
    
    def _on_seek(self, position: float):
        """
        Handle seek request from control panel.
        
        Args:
            position: Position from 0.0 to 1.0
        """
        logger.info(f"Seek requested to position: {position:.3f}")
        
        if self.midi_data:
            stats = self.midi_data.get_statistics()
            time = position * stats['duration']
            self.set_status(f"Seek to {time:.1f}s")
    
    def _on_speed_changed(self, speed: float):
        """
        Handle speed change from control panel.
        
        Args:
            speed: Speed multiplier
        """
        logger.info(f"Speed changed to {speed}x")
        self.set_status(f"Playback speed: {speed}x")



    def _on_processing_error(self, error_message: str):
        """
        Handle processing errors.
        
        Args:
            error_message: Error description
        """
        logger.error(f"Processing failed: {error_message}")
        
        # Update UI state
        self.is_processing = False
        self.show_progress(False)
        self.transcribe_action.setEnabled(True)
        
        # Update status
        self.set_status("Processing failed")
        
        # Reset visualization widget
        import os
        if self.current_file:
            self.file_drop_widget.set_file_loaded(os.path.basename(self.current_file))
        else:
            self.file_drop_widget.reset()
        
        # Show error message
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(
            self,
            'Processing Error',
            f'Transcription failed:\n\n{error_message}\n\n'
            f'Please check the audio file and try again.'
        )



    def _on_export_midi(self):
        """Handle Export MIDI action."""
        logger.info("Export MIDI triggered")
        self.set_status("Export will be implemented in next steps...")
    
    def _on_export_json(self):
        """Handle Export JSON action."""
        logger.info("Export JSON triggered")
        self.set_status("Export will be implemented in next steps...")
    
    def _on_settings(self):
        """Handle Settings action."""
        logger.info("Settings dialog triggered")
        self.set_status("Settings dialog will be implemented in next steps...")
    
    def _on_toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
            logger.info("Exited fullscreen mode")
        else:
            self.showFullScreen()
            logger.info("Entered fullscreen mode")
    
    def _get_screen_size(self):
        """
        Get available screen size.
        
        Returns:
            Tuple of (width, height) for available screen area
        """
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().availableGeometry()
        return screen.width(), screen.height()
    
    def _set_window_size(self, width: int, height: int):
        """
        Set window to specific size with screen bounds checking.
        
        Args:
            width: Window width in pixels
            height: Window height in pixels
        """
        # Get available screen size
        screen_width, screen_height = self._get_screen_size()
        
        # Check if requested size fits on screen (with some margin)
        margin = 50  # Leave margin for taskbar/decorations
        max_width = screen_width - margin
        max_height = screen_height - margin
        
        if width > max_width or height > max_height:
            # Window too large for screen
            logger.warning(f"Requested size {width}x{height} exceeds screen size {screen_width}x{screen_height}")
            
            # Show warning dialog
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                'Window Size Too Large',
                f'The requested window size ({width}x{height}) is larger than your screen.\n\n'
                f'Your screen size: {screen_width}x{screen_height}\n'
                f'Window will be resized to fit your screen instead.'
            )
            
            # Resize to fit screen (maintaining aspect ratio if possible)
            aspect_ratio = width / height
            if width > max_width:
                width = max_width
                height = int(width / aspect_ratio)
            if height > max_height:
                height = max_height
                width = int(height * aspect_ratio)
            
            self.set_status(f"Window size adjusted to fit screen: {width}x{height}")
        
        # Apply size
        self.resize(width, height)
        self._center_window()
        
        logger.info(f"Window resized to {width}x{height}")
        self.set_status(f"Window size: {width}x{height}", timeout=3000)

    def _reset_window_size(self):
        """Reset window to default size."""
        default_width = 1280
        default_height = 720
        self.resize(default_width, default_height)
        self._center_window()
        logger.info("Window size reset to default")
        self.set_status(f"Window reset to default size: {default_width}x{default_height}", timeout=3000)


    
    def _on_about(self):
        """Show About dialog."""
        QMessageBox.about(
            self,
            'About AudioViz MIDI',
            '<h2>AudioViz MIDI</h2>'
            '<p>Version 0.1.0 (MVP)</p>'
            '<p>Audio to MIDI Converter with Visualization</p>'
            '<p>Built with Python, PyQt5, and librosa</p>'
            '<p>© 2025 AudioViz MIDI Project</p>'
        )
    
    # Public Methods
    
    def set_status(self, message: str, timeout: int = 0):
        """
        Display message in status bar.
        
        Args:
            message: Status message to display
            timeout: Auto-clear timeout in milliseconds (0 = no timeout)
        """
        self.status_label.setText(message)
        if timeout > 0:
            QTimer.singleShot(timeout, lambda: self.status_label.setText('Ready'))
        logger.debug(f"Status: {message}")
    
    def show_progress(self, show: bool = True):
        """
        Show or hide progress bar.
        
        Args:
            show: True to show, False to hide
        """
        self.progress_bar.setVisible(show)
        if not show:
            self.progress_bar.setValue(0)
    
    def set_progress(self, value: int):
        """
        Set progress bar value.
        
        Args:
            value: Progress percentage (0-100)
        """
        self.progress_bar.setValue(value)
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Clean up Pygame
        if self.pygame_widget:
            self.pygame_widget.cleanup()
        
        # Save window size to config
        self.config.set('ui', 'window_width', self.width())
        self.config.set('ui', 'window_height', self.height())
        self.config.save_config()
        
        logger.info("Main window closing")
        event.accept()

