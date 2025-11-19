# utils/error_handler.py
"""
Error Handler for AudioViz MIDI.
Provides centralized error handling and user-friendly error messages.
"""

from PyQt5.QtWidgets import QMessageBox, QWidget
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class ErrorHandler:
    """
    Centralized error handling for the application.
    
    Provides consistent error logging and user-friendly error dialogs.
    """
    
    @staticmethod
    def handle_file_error(parent: Optional[QWidget], error: Exception, filepath: str):
        """
        Handle file-related errors.
        
        Args:
            parent: Parent widget for dialog
            error: Exception that occurred
            filepath: Path to file that caused error
        """
        logger.error(f"File error for {filepath}: {error}", exc_info=True)
        
        error_msg = str(error)
        
        # Provide specific guidance based on error type
        if "not found" in error_msg.lower() or "no such file" in error_msg.lower():
            message = (
                f"File not found:\n{filepath}\n\n"
                "The file may have been moved or deleted."
            )
        elif "permission" in error_msg.lower() or "access" in error_msg.lower():
            message = (
                f"Cannot access file:\n{filepath}\n\n"
                "Check that the file is not open in another application "
                "and that you have permission to access it."
            )
        elif "format" in error_msg.lower() or "invalid" in error_msg.lower():
            message = (
                f"Invalid or unsupported file format:\n{filepath}\n\n"
                "Please use WAV, MP3, FLAC, or OGG audio files."
            )
        else:
            message = (
                f"Error loading file:\n{filepath}\n\n"
                f"Error: {error_msg}"
            )
        
        QMessageBox.critical(parent, 'File Error', message)
    
    @staticmethod
    def handle_processing_error(parent: Optional[QWidget], error: Exception, stage: str):
        """
        Handle audio processing errors.
        
        Args:
            parent: Parent widget for dialog
            error: Exception that occurred
            stage: Processing stage where error occurred
        """
        logger.error(f"Processing error at {stage}: {error}", exc_info=True)
        
        error_msg = str(error)
        
        # Provide helpful suggestions
        suggestions = []
        
        if "memory" in error_msg.lower():
            suggestions.append("• Try closing other applications to free up memory")
            suggestions.append("• The audio file may be too large")
        
        if "audio" in error_msg.lower() or "sample" in error_msg.lower():
            suggestions.append("• The audio file may be corrupted")
            suggestions.append("• Try converting to WAV format first")
        
        if "pitch" in error_msg.lower() or "frequency" in error_msg.lower():
            suggestions.append("• The audio may not contain clear pitched notes")
            suggestions.append("• Try audio with clearer/louder notes")
        
        message = (
            f"Error during {stage}:\n\n"
            f"{error_msg}\n"
        )
        
        if suggestions:
            message += "\nSuggestions:\n" + "\n".join(suggestions)
        
        QMessageBox.critical(parent, 'Processing Error', message)
    
    @staticmethod
    def handle_export_error(parent: Optional[QWidget], error: Exception, 
                          export_type: str, filepath: str):
        """
        Handle export errors.
        
        Args:
            parent: Parent widget for dialog
            error: Exception that occurred
            export_type: Type of export (MIDI, JSON)
            filepath: Target export path
        """
        logger.error(f"Export error ({export_type}) to {filepath}: {error}", exc_info=True)
        
        error_msg = str(error)
        
        if "permission" in error_msg.lower():
            message = (
                f"Cannot write to:\n{filepath}\n\n"
                "Check that:\n"
                "• The directory exists and is writable\n"
                "• The file is not open in another application\n"
                "• You have write permissions"
            )
        elif "disk" in error_msg.lower() or "space" in error_msg.lower():
            message = (
                f"Cannot write to:\n{filepath}\n\n"
                "Your disk may be full or the path is invalid."
            )
        else:
            message = (
                f"Failed to export {export_type}:\n\n"
                f"{error_msg}\n\n"
                f"Target: {filepath}"
            )
        
        QMessageBox.critical(parent, 'Export Error', message)
    
    @staticmethod
    def handle_playback_error(parent: Optional[QWidget], error: Exception):
        """
        Handle playback errors.
        
        Args:
            parent: Parent widget for dialog
            error: Exception that occurred
        """
        logger.error(f"Playback error: {error}", exc_info=True)
        
        message = (
            "Playback error occurred:\n\n"
            f"{str(error)}\n\n"
            "Suggestions:\n"
            "• Check that your audio device is working\n"
            "• Try restarting the application\n"
            "• The audio file may be corrupted"
        )
        
        QMessageBox.warning(parent, 'Playback Error', message)
    
    @staticmethod
    def show_warning(parent: Optional[QWidget], title: str, message: str):
        """
        Show a warning dialog.
        
        Args:
            parent: Parent widget for dialog
            title: Dialog title
            message: Warning message
        """
        logger.warning(f"{title}: {message}")
        QMessageBox.warning(parent, title, message)
    
    @staticmethod
    def show_info(parent: Optional[QWidget], title: str, message: str):
        """
        Show an info dialog.
        
        Args:
            parent: Parent widget for dialog
            title: Dialog title
            message: Info message
        """
        logger.info(f"{title}: {message}")
        QMessageBox.information(parent, title, message)
