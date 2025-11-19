# tests/test_smoke.py
"""
Smoke tests for AudioViz MIDI.
Quick tests to verify basic functionality.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import setup_logging

logger = setup_logging()


def test_imports():
    """Test that all modules can be imported."""
    logger.info("Testing module imports...")
    
    try:
        from audio import AudioLoader, PitchDetector, OnsetDetector
        logger.info("✓ Audio modules imported")
        
        from midi import Note, MIDIData, MIDIConverter, NoteQuantizer
        logger.info("✓ MIDI modules imported")
        
        from export import MIDIExporter, JSONExporter
        logger.info("✓ Export modules imported")
        
        from visualization import PygameWidget, PianoRollRenderer
        logger.info("✓ Visualization modules imported")
        
        from playback import PlaybackController, PlaybackState
        logger.info("✓ Playback modules imported")
        
        from gui import MainWindow, FileDropWidget, ControlPanel
        logger.info("✓ GUI modules imported")
        
        from utils import ConfigManager, ErrorHandler, get_performance_monitor
        logger.info("✓ Utility modules imported")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        return False


def test_basic_functionality():
    """Test basic object creation."""
    logger.info("\nTesting basic functionality...")
    
    try:
        from audio import AudioLoader
        from midi import Note, MIDIData
        from utils import ConfigManager
        
        # Test config
        config = ConfigManager()
        logger.info("✓ Config manager created")
        
        # Test audio loader
        loader = AudioLoader()
        logger.info("✓ Audio loader created")
        
        # Test note creation
        note = Note(pitch=60, start_time=0.0, end_time=1.0, velocity=80)
        assert note.note_name == 'C4', "Wrong note name"
        assert note.frequency > 260 and note.frequency < 263, "Wrong frequency"
        logger.info("✓ Note creation working")
        
        # Test MIDI data
        midi_data = MIDIData([note])
        assert len(midi_data) == 1, "Wrong note count"
        logger.info("✓ MIDI data structure working")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Basic functionality failed: {e}")
        return False


def test_file_structure():
    """Test that all required files exist."""
    logger.info("\nTesting file structure...")
    
    required_files = [
        'main.py',
        'requirements.txt',
        'config.json',
        'audio/__init__.py',
        'midi/__init__.py',
        'visualization/__init__.py',
        'playback/__init__.py',
        'export/__init__.py',
        'gui/__init__.py',
        'utils/__init__.py',
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            logger.info(f"✓ {file_path}")
        else:
            logger.error(f"✗ {file_path} - MISSING")
            all_exist = False
    
    return all_exist


def run_smoke_tests():
    """Run all smoke tests."""
    logger.info("="*60)
    logger.info("RUNNING SMOKE TESTS")
    logger.info("="*60)
    
    results = []
    
    # Test imports
    logger.info("\n--- Test 1: Module Imports ---")
    results.append(test_imports())
    
    # Test basic functionality
    logger.info("\n--- Test 2: Basic Functionality ---")
    results.append(test_basic_functionality())
    
    # Test file structure
    logger.info("\n--- Test 3: File Structure ---")
    results.append(test_file_structure())
    
    # Summary
    logger.info("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    logger.info(f"Smoke Tests: {passed}/{total} passed")
    logger.info("="*60)
    
    return all(results)


if __name__ == '__main__':
    success = run_smoke_tests()
    sys.exit(0 if success else 1)
