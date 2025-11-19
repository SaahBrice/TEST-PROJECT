# gui/file_drop_widget.py
"""
File Drop Widget for AudioViz MIDI.
Provides a drag-and-drop area for easy audio file loading.
"""

from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QPalette, QFont
from utils.logger import get_logger

logger = get_logger(__name__)


class FileDropWidget(QLabel):
    """
    Custom widget that accepts drag-and-drop file operations.
    
    Signals:
        file_dropped: Emitted when a valid audio file is dropped
    """
    
    # Signal emitted when file is dropped (passes file path)
    file_dropped = pyqtSignal(str)
    
    # Supported audio file extensions
    SUPPORTED_EXTENSIONS = ['.wav', '.mp3', '.flac', '.ogg']
    
    def __init__(self, parent=None):
        """
        Initialize the file drop widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Set up UI
        self._setup_ui()
        
        # Track drag state
        self.is_dragging = False
        
        logger.debug("FileDropWidget initialized")
    
    def _setup_ui(self):
        """Set up the widget appearance."""
        # Set text
        self.setText(
            '🎵 Drag & Drop Audio File Here\n\n'
            'or click "Open Audio" button\n\n'
            'Supported: WAV, MP3, FLAC, OGG'
        )
        
        # Set alignment
        self.setAlignment(Qt.AlignCenter)
        
        # Set font
        font = QFont()
        font.setPointSize(14)
        self.setFont(font)
        
        # Set minimum size
        self.setMinimumHeight(200)
        
        # Apply default style
        self._apply_default_style()
    
    def _apply_default_style(self):
        """Apply default (non-dragging) style."""
        self.setStyleSheet("""
            QLabel {
                background-color: #1e1e28;
                color: #888;
                border: 3px dashed #444;
                border-radius: 12px;
                padding: 20px;
            }
        """)
    
    def _apply_hover_style(self):
        """Apply style when file is being dragged over."""
        self.setStyleSheet("""
            QLabel {
                background-color: #2a2a38;
                color: #4a9eff;
                border: 3px dashed #4a9eff;
                border-radius: 12px;
                padding: 20px;
            }
        """)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        Handle drag enter event.
        
        Args:
            event: Drag enter event
        """
        # Check if dragged data contains URLs (files)
        if event.mimeData().hasUrls():
            # Get the first file
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                
                # Check if it's a supported audio file
                if self._is_supported_file(file_path):
                    event.acceptProposedAction()
                    self.is_dragging = True
                    self._apply_hover_style()
                    logger.debug(f"Drag entered with valid file: {file_path}")
                else:
                    event.ignore()
                    logger.debug(f"Drag entered with unsupported file: {file_path}")
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """
        Handle drag leave event.
        
        Args:
            event: Drag leave event
        """
        self.is_dragging = False
        self._apply_default_style()
        logger.debug("Drag left widget area")
    
    def dropEvent(self, event: QDropEvent):
        """
        Handle drop event.
        
        Args:
            event: Drop event
        """
        # Get dropped files
        urls = event.mimeData().urls()
        
        if urls:
            # Get first file path
            file_path = urls[0].toLocalFile()
            
            # Validate file
            if self._is_supported_file(file_path):
                logger.info(f"File dropped: {file_path}")
                
                # Emit signal with file path
                self.file_dropped.emit(file_path)
                
                # Accept the event
                event.acceptProposedAction()
                
                # Reset style
                self.is_dragging = False
                self._apply_default_style()
            else:
                logger.warning(f"Dropped file has unsupported format: {file_path}")
                event.ignore()
        else:
            event.ignore()
    
    def _is_supported_file(self, file_path: str) -> bool:
        """
        Check if file has supported extension.
        
        Args:
            file_path: Path to file
        
        Returns:
            True if file extension is supported
        """
        import os
        extension = os.path.splitext(file_path)[1].lower()
        return extension in self.SUPPORTED_EXTENSIONS
    
    def set_file_loaded(self, filename: str):
        """
        Update widget to show file is loaded.
        
        Args:
            filename: Name of loaded file
        """
        self.setText(
            f'✓ Audio File Loaded\n\n'
            f'{filename}\n\n'
            'Click "Transcribe" to process\n'
            'or drop another file to replace'
        )
        
        # Apply loaded style
        self.setStyleSheet("""
            QLabel {
                background-color: #1e2e1e;
                color: #6c6;
                border: 3px solid #4a9eff;
                border-radius: 12px;
                padding: 20px;
            }
        """)
    
    def reset(self):
        """Reset widget to initial state."""
        self.setText(
            '🎵 Drag & Drop Audio File Here\n\n'
            'or click "Open Audio" button\n\n'
            'Supported: WAV, MP3, FLAC, OGG'
        )
        self._apply_default_style()
