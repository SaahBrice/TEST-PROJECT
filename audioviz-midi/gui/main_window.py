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
from playback import PlaybackController, PlaybackState
from visualization import PianoRollRenderer
from gui.control_panel import ControlPanel
from visualization import PygameWidget
from gui.processing_thread import ProcessingThread
from gui.file_drop_widget import FileDropWidget
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QIcon, QKeySequence
from utils.logger import get_logger
from utils.config import ConfigManager
from export import MIDIExporter, JSONExporter
from utils import ErrorHandler
from utils import get_performance_monitor



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
        self.pygame_widget = None  # Pygame visualization widget
        self.playback_controller = PlaybackController() 
        self.midi_exporter = MIDIExporter(config)
        self.json_exporter = JSONExporter(config)
        # Connect playback signals
        self.playback_controller.state_changed.connect(self._on_playback_state_changed)
        self.playback_controller.time_updated.connect(self._on_playback_time_updated)
        self.playback_controller.playback_finished.connect(self._on_playback_finished)
        
        # Performance monitoring
        self.perf_monitor = get_performance_monitor()
        self.perf_monitor.log_memory_usage("Application start")
        
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
        
        # Set up keyboard shortcuts
        self._setup_keyboard_shortcuts()

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
        
        # Keyboard Shortcuts action - ADD THIS
        shortcuts_action = QAction('&Keyboard Shortcuts...', self)
        shortcuts_action.setShortcut('F1')
        shortcuts_action.setStatusTip('View keyboard shortcuts')
        shortcuts_action.triggered.connect(self._on_keyboard_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        help_menu.addSeparator()
        
        # About action
        about_action = QAction('&About...', self)
        about_action.setStatusTip('About AudioViz MIDI')
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
        
        logger.debug("Menu bar created")
    
    def _check_workflow_state(self) -> dict:
        """
        Check current workflow state for UI guidance.
        
        Returns:
            Dictionary with workflow state information
        """
        return {
            'has_file': self.current_file is not None,
            'has_transcription': self.midi_data is not None,
            'is_processing': self.is_processing,
            'can_transcribe': self.current_file is not None and not self.is_processing,
            'can_play': self.midi_data is not None,
            'can_export': self.midi_data is not None
        }



    def _setup_keyboard_shortcuts(self):
        """Set up additional keyboard shortcuts beyond menu items."""
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        
        # Spacebar for Play/Pause toggle
        self.play_pause_shortcut = QShortcut(QKeySequence(Qt.Key_Space), self)
        self.play_pause_shortcut.activated.connect(self._toggle_play_pause)
        
        # Escape to stop playback
        self.stop_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.stop_shortcut.activated.connect(self._on_stop)
        
        # Arrow keys for seeking
        self.seek_forward_shortcut = QShortcut(QKeySequence(Qt.Key_Right), self)
        self.seek_forward_shortcut.activated.connect(self._seek_forward)
        
        self.seek_backward_shortcut = QShortcut(QKeySequence(Qt.Key_Left), self)
        self.seek_backward_shortcut.activated.connect(self._seek_backward)
        
        # Ctrl+T for transcribe
        self.transcribe_shortcut = QShortcut(QKeySequence('Ctrl+T'), self)
        self.transcribe_shortcut.activated.connect(self._on_transcribe)
        
        # Ctrl+E for quick export (MIDI)
        self.quick_export_shortcut = QShortcut(QKeySequence('Ctrl+E'), self)
        self.quick_export_shortcut.activated.connect(self._on_export_midi)
        
        logger.info("Keyboard shortcuts configured")

    def _toggle_play_pause(self):
        """Toggle between play and pause (Spacebar)."""
        from playback import PlaybackState
        
        if not self.midi_data:
            return
        
        state = self.playback_controller.get_state()
        
        if state == PlaybackState.PLAYING:
            self._on_pause()
        elif state in [PlaybackState.STOPPED, PlaybackState.PAUSED]:
            self._on_play()
    
    def _seek_forward(self):
        """Seek forward 5 seconds (Right Arrow)."""
        if not self.midi_data:
            return
        
        current_time = self.playback_controller.get_current_time()
        stats = self.midi_data.get_statistics()
        duration = stats['duration']
        
        # Move forward 5 seconds
        new_time = min(current_time + 5.0, duration)
        position = new_time / duration if duration > 0 else 0
        
        self.playback_controller.seek(position)
        logger.debug(f"Seek forward to {new_time:.1f}s")
    
    def _seek_backward(self):
        """Seek backward 5 seconds (Left Arrow)."""
        if not self.midi_data:
            return
        
        current_time = self.playback_controller.get_current_time()
        stats = self.midi_data.get_statistics()
        duration = stats['duration']
        
        # Move backward 5 seconds
        new_time = max(current_time - 5.0, 0.0)
        position = new_time / duration if duration > 0 else 0
        
        self.playback_controller.seek(position)
        logger.debug(f"Seek backward to {new_time:.1f}s")



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
        
        toolbar.addSeparator()

        # Help button
        help_action = QAction('Help', self)
        help_action.setStatusTip('Show workflow help')
        help_action.triggered.connect(self._show_workflow_help)
        toolbar.addAction(help_action)

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
        
        try:
            # Validate file using AudioLoader
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
                    ErrorHandler.show_warning(self, 'Large File', message)
            else:
                # File is invalid
                logger.error(f"Invalid file: {message}")
                ErrorHandler.show_warning(self, 'Invalid File', 
                    f'Cannot load file:\n\n{message}')
                self.file_drop_widget.reset()
                
        except Exception as e:
            ErrorHandler.handle_file_error(self, e, file_path)
            self.file_drop_widget.reset()




    def _on_transcribe(self):
        """Handle Transcribe action."""
        if not self.current_file:
            logger.warning("No file loaded to transcribe")
            return
        
        # Validate state
        if not self._validate_can_transcribe():
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
        
        # Get statistics ONCE at the beginning
        stats = midi_data.get_statistics()
        
        # Enable control panel and set duration
        self.control_panel.set_enabled(True)
        self.control_panel.set_duration(stats['duration'])
        
        # Update UI state
        self.is_processing = False
        self.show_progress(False)
        
        # Enable export actions
        self.export_midi_action.setEnabled(True)
        self.export_json_action.setEnabled(True)
        self.export_action.setEnabled(True)
        
        # CREATE AND SET UP PIANO ROLL RENDERER
        renderer = PianoRollRenderer(self.pygame_widget.screen, self.config)
        renderer.set_midi_data(midi_data)
        self.pygame_widget.set_renderer(renderer)
        self.pygame_widget.set_midi_data(midi_data)
        
        # LOAD AUDIO FOR PLAYBACK
        try:
            self.playback_controller.load_audio(self.current_file, stats['duration'])
            logger.info("Audio loaded for playback")
        except Exception as e:
            logger.error(f"Failed to load audio for playback: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                'Playback Warning',
                f'Audio loaded but playback may not work:\n{e}'
            )
        
        # Switch to Pygame visualization
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
        
        if not self.midi_data or not self.current_file:
            logger.warning("No MIDI data or audio file available for playback")
            return
        
        # Start playback
        self.playback_controller.play()
    
    def _on_pause(self):
        """Handle pause button from control panel."""
        logger.info("Pause requested from control panel")
        self.playback_controller.pause()
    
    def _on_stop(self):
        """Handle stop button from control panel."""
        logger.info("Stop requested from control panel")
        self.playback_controller.stop()
    
    def _on_seek(self, position: float):
        """
        Handle seek request from control panel.
        
        Args:
            position: Position from 0.0 to 1.0
        """
        logger.info(f"Seek requested to position: {position:.3f}")
        self.playback_controller.seek(position)
    
    def _on_speed_changed(self, speed: float):
        """
        Handle speed change from control panel.
        
        Args:
            speed: Speed multiplier
        """
        logger.info(f"Speed changed to {speed}x")
        self.playback_controller.set_speed(speed)
        self.set_status(f"Note: Speed control not fully implemented in MVP")

    def _on_playback_state_changed(self, state):
        """
        Handle playback state changes.
        
        Args:
            state: New PlaybackState
        """
        from playback import PlaybackState
        
        if state == PlaybackState.PLAYING:
            self.control_panel.set_playing(True)
            self.set_status("Playing...")
        elif state == PlaybackState.PAUSED:
            self.control_panel.set_playing(False)
            self.set_status("Paused")
        elif state == PlaybackState.STOPPED:
            self.control_panel.set_playing(False)
            self.set_status("Stopped")
    
    def _on_playback_time_updated(self, time: float):
        """
        Handle playback time updates.
        
        Args:
            time: Current time in seconds
        """
        # Update control panel
        self.control_panel.set_playback_position(time)
        
        # Update visualization
        if self.pygame_widget:
            self.pygame_widget.set_playback_time(time)
    
    def _on_playback_finished(self):
        """Handle playback completion."""
        logger.info("Playback finished")
        self.set_status("Playback complete")



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
        
        # Show error with helpful suggestions
        suggestions = []
        
        if "memory" in error_message.lower():
            suggestions.append("• Close other applications to free up memory")
            suggestions.append("• Try a shorter audio clip")
        elif "audio" in error_message.lower() or "load" in error_message.lower():
            suggestions.append("• Check that the audio file is not corrupted")
            suggestions.append("• Try converting to WAV format")
        elif "pitch" in error_message.lower() or "frequency" in error_message.lower():
            suggestions.append("• Ensure audio contains clear musical notes")
            suggestions.append("• Try audio with less background noise")
        else:
            suggestions.append("• Check the log files for detailed error information")
            suggestions.append("• Try a different audio file")
        
        message = f"Transcription failed:\n\n{error_message}\n"
        
        if suggestions:
            message += "\nSuggestions:\n" + "\n".join(suggestions)
        
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(self, 'Processing Error', message)




    def _on_export_midi(self):
        """Handle Export MIDI action."""
        if not self.midi_data:
            ErrorHandler.show_warning(self, 'No Data', 
                'Please transcribe audio first before exporting.')
            return
        
        logger.info("Export MIDI triggered")
        
        try:
            # Get default filename
            default_name = self.midi_exporter.get_default_filename(self.current_file)
            default_dir = self.config.get('export', 'default_directory', 'exports')
            
            # Create exports directory if it doesn't exist
            import os
            if not os.path.exists(default_dir):
                try:
                    os.makedirs(default_dir)
                except Exception as e:
                    logger.warning(f"Could not create exports directory: {e}")
                    default_dir = os.path.expanduser('~')  # Fall back to home directory
            
            default_path = os.path.join(default_dir, default_name)
            
            # Show save dialog
            from PyQt5.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                'Export MIDI File',
                default_path,
                'MIDI Files (*.mid);;All Files (*.*)'
            )
            
            if file_path:
                # Ensure .mid extension
                if not file_path.lower().endswith('.mid'):
                    file_path += '.mid'
                
                # Check if file exists and confirm overwrite
                if os.path.exists(file_path):
                    from PyQt5.QtWidgets import QMessageBox
                    reply = QMessageBox.question(
                        self,
                        'Confirm Overwrite',
                        f'File already exists:\n{file_path}\n\nOverwrite?',
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return
                
                # Export
                success = self.midi_exporter.export(self.midi_data, file_path)
                
                if success:
                    logger.info(f"MIDI exported to: {file_path}")
                    self.set_status(f"MIDI exported: {os.path.basename(file_path)}")
                    
                    ErrorHandler.show_info(
                        self,
                        'Export Successful',
                        f'MIDI file saved successfully!\n\n{file_path}'
                    )
                else:
                    raise Exception("Export failed - check logs for details")
                    
        except Exception as e:
            ErrorHandler.handle_export_error(self, e, 'MIDI', 
                file_path if 'file_path' in locals() else 'unknown')

    
    def _on_export_json(self):
        """Handle Export JSON action."""
        if not self.midi_data:
            ErrorHandler.show_warning(self, 'No Data', 
                'Please transcribe audio first before exporting.')
            return
        
        logger.info("Export JSON triggered")
        
        try:
            # Get default filename
            default_name = self.json_exporter.get_default_filename(self.current_file)
            default_dir = self.config.get('export', 'default_directory', 'exports')
            
            # Create exports directory if it doesn't exist
            import os
            if not os.path.exists(default_dir):
                try:
                    os.makedirs(default_dir)
                except Exception as e:
                    logger.warning(f"Could not create exports directory: {e}")
                    default_dir = os.path.expanduser('~')
            
            default_path = os.path.join(default_dir, default_name)
            
            # Show save dialog
            from PyQt5.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                'Export JSON File',
                default_path,
                'JSON Files (*.json);;All Files (*.*)'
            )
            
            if file_path:
                # Ensure .json extension
                if not file_path.lower().endswith('.json'):
                    file_path += '.json'
                
                # Check if file exists and confirm overwrite
                if os.path.exists(file_path):
                    from PyQt5.QtWidgets import QMessageBox
                    reply = QMessageBox.question(
                        self,
                        'Confirm Overwrite',
                        f'File already exists:\n{file_path}\n\nOverwrite?',
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return
                
                # Export
                success = self.json_exporter.export(
                    self.midi_data, 
                    file_path,
                    source_file=self.current_file
                )
                
                if success:
                    logger.info(f"JSON exported to: {file_path}")
                    self.set_status(f"JSON exported: {os.path.basename(file_path)}")
                    
                    ErrorHandler.show_info(
                        self,
                        'Export Successful',
                        f'JSON file saved successfully!\n\n{file_path}'
                    )
                else:
                    raise Exception("Export failed - check logs for details")
                    
        except Exception as e:
            ErrorHandler.handle_export_error(self, e, 'JSON', 
                file_path if 'file_path' in locals() else 'unknown')

    def _validate_can_transcribe(self) -> bool:
        """
        Validate that transcription can proceed.
        
        Returns:
            True if ready to transcribe
        """
        if not self.current_file:
            ErrorHandler.show_warning(self, 'No File', 
                'Please load an audio file first.')
            return False
        
        if self.is_processing:
            ErrorHandler.show_warning(self, 'Already Processing', 
                'Please wait for current transcription to complete.')
            return False
        
        # Check file still exists
        import os
        if not os.path.exists(self.current_file):
            ErrorHandler.show_warning(self, 'File Not Found', 
                f'The audio file no longer exists:\n{self.current_file}\n\n'
                'Please load the file again.')
            self.current_file = None
            self.file_drop_widget.reset()
            return False
        
        return True

    
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
    
    def _on_keyboard_shortcuts(self):
        """Show keyboard shortcuts dialog."""
        shortcuts_text = """
        <h3>Keyboard Shortcuts</h3>
        <table cellpadding="5">
        <tr><td><b>Ctrl+O</b></td><td>Open Audio File</td></tr>
        <tr><td><b>Ctrl+T</b></td><td>Transcribe Audio</td></tr>
        <tr><td><b>Ctrl+M</b></td><td>Export MIDI</td></tr>
        <tr><td><b>Ctrl+J</b></td><td>Export JSON</td></tr>
        <tr><td><b>Ctrl+E</b></td><td>Quick Export (MIDI)</td></tr>
        <tr><td><b>Ctrl+Q</b></td><td>Quit Application</td></tr>
        <tr><td><b>Ctrl+0</b></td><td>Reset Window Size</td></tr>
        <tr><td><b>F11</b></td><td>Toggle Fullscreen</td></tr>
        <tr><td colspan="2"><hr></td></tr>
        <tr><td><b>Space</b></td><td>Play / Pause</td></tr>
        <tr><td><b>Escape</b></td><td>Stop Playback</td></tr>
        <tr><td><b>Left Arrow</b></td><td>Seek Backward 5s</td></tr>
        <tr><td><b>Right Arrow</b></td><td>Seek Forward 5s</td></tr>
        </table>
        """
        
        QMessageBox.information(
            self,
            'Keyboard Shortcuts',
            shortcuts_text
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
            QTimer.singleShot(timeout, lambda: self._set_ready_status())
        logger.debug(f"Status: {message}")
    
    def _set_ready_status(self):
        """Set status to ready with workflow hint."""
        state = self._check_workflow_state()
        
        if state['is_processing']:
            return  # Don't override processing status
        elif not state['has_file']:
            self.status_label.setText('Ready - Open an audio file to begin')
        elif not state['has_transcription']:
            self.status_label.setText('Ready - Click Transcribe to analyze audio')
        elif state['has_transcription']:
            self.status_label.setText('Ready - Use playback controls or export')
        else:
            self.status_label.setText('Ready')

    
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
    
    def _show_workflow_help(self):
        """Show contextual help based on current workflow state."""
        state = self._check_workflow_state()
        
        if not state['has_file']:
            message = (
                "To get started:\n\n"
                "1. Click 'Open Audio' or drag & drop an audio file\n"
                "2. Supported formats: WAV, MP3, FLAC, OGG\n\n"
                "Tip: Press Ctrl+O to open file dialog"
            )
        elif not state['has_transcription']:
            message = (
                "Next steps:\n\n"
                "1. Click 'Transcribe' to analyze the audio\n"
                "2. Wait for processing to complete\n"
                "3. The piano roll will display your notes\n\n"
                "Tip: Press Ctrl+T to start transcription"
            )
        else:
            message = (
                "You can now:\n\n"
                "• Press Space to play/pause\n"
                "• Use arrow keys to seek through audio\n"
                "• Export MIDI file (Ctrl+M)\n"
                "• Export JSON data (Ctrl+J)\n\n"
                "Tip: Press F1 to see all keyboard shortcuts"
            )
        
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, 'Quick Help', message)



    def closeEvent(self, event):
        """Handle window close event."""
        # Log performance summary
        self.perf_monitor.log_summary()
        
        # Clean up playback
        if self.playback_controller:
            self.playback_controller.cleanup()
        
        # Clean up Pygame
        if self.pygame_widget:
            self.pygame_widget.cleanup()
        
        # Save window size to config
        self.config.set('ui', 'window_width', self.width())
        self.config.set('ui', 'window_height', self.height())
        self.config.save_config()
        
        logger.info("Main window closing")
        event.accept()



