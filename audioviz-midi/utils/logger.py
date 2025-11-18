# utils/logger.py
"""
Logging configuration for AudioViz MIDI application.
Provides centralized logging setup with file and console output.
"""

import logging
import os
from datetime import datetime


def setup_logging(log_level=logging.INFO):
    """
    Initialize application-wide logging system.
    
    Args:
        log_level: Minimum logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger instance for the application
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Generate log filename with timestamp
    log_filename = f"logs/audioviz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Create logger
    logger = logging.getLogger('AudioVizMIDI')
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create file handler for logging to file
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    
    # Create console handler for logging to terminal
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)  # Respect user's log level for console
    
    # Create detailed formatter for file logs
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create simpler formatter for console logs
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Assign formatters to handlers
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info("Logging system initialized")
    logger.info(f"Log file: {log_filename}")
    
    return logger


def get_logger(name=None):
    """
    Get logger instance for a specific module.
    
    Args:
        name: Module name (typically __name__)
    
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f'AudioVizMIDI.{name}')
    return logging.getLogger('AudioVizMIDI')
