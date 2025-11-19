# main.py
"""
Main entry point for AudioViz MIDI application.
Initializes the application and displays the main window.
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui import MainWindow
from utils import setup_logging, ConfigManager
from utils import setup_logging, ConfigManager, __version__


def main():
    """Initialize and run the application."""
    # Set up logging
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("AudioViz MIDI Application Starting")
    logger.info(f"AudioViz MIDI v{__version__} Starting")
    logger.info("=" * 60)
    
    # Load configuration
    config = ConfigManager()
    
    # Log configuration version
    config_version = config.get('app', 'version', 'unknown')
    app_name = config.get('app', 'name', 'AudioViz MIDI')
    
    logger.info(f"Application: {app_name}")
    logger.info(f"Config Version: {config_version}")
    
    if config_version != __version__:
        logger.warning(f"Config version mismatch: {config_version} vs {__version__}")



    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("AudioViz MIDI")
    app.setOrganizationName("AudioViz")
    
    # Create and show main window
    main_window = MainWindow(config)
    main_window.show()
    
    logger.info("Main window displayed")
    logger.info("Application ready")
    
    # Run application event loop
    exit_code = app.exec_()
    
    logger.info("Application shutting down")
    logger.info(f"Exit code: {exit_code}")
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
