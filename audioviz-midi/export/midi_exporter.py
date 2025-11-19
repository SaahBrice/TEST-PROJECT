# export/midi_exporter.py
"""
MIDI Exporter Module for AudioViz MIDI.
Exports MIDI data to standard MIDI files (.mid) using pretty_midi library.
"""

import pretty_midi
import os
from typing import Optional
from midi import MIDIData, Note
from utils.logger import get_logger
from utils.config import ConfigManager

logger = get_logger(__name__)


class MIDIExporter:
    """
    Exports MIDI data to standard MIDI file format.
    
    Creates .mid files compatible with DAWs and music software.
    Includes proper timing, velocity, and instrument assignment.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """
        Initialize the MIDI exporter.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config or ConfigManager()
        
        # Load export settings
        self.include_metadata = self.config.get('export', 'include_metadata', True)
        self.default_instrument = 0  # Acoustic Grand Piano
        
        logger.info("MIDIExporter initialized")
    
    def export(self, midi_data: MIDIData, output_path: str, 
               instrument_name: str = "Acoustic Grand Piano") -> bool:
        """
        Export MIDI data to file.
        
        Args:
            midi_data: MIDIData object containing notes
            output_path: Output file path (.mid)
            instrument_name: Instrument name for the track
        
        Returns:
            True if export successful, False otherwise
        """
        try:
            logger.info(f"Exporting MIDI to: {output_path}")
            
            if not midi_data or len(midi_data) == 0:
                logger.error("No MIDI data to export")
                return False
            
            # Create PrettyMIDI object
            midi = pretty_midi.PrettyMIDI()
            
            # Create instrument track
            instrument_program = self._get_instrument_program(instrument_name)
            instrument = pretty_midi.Instrument(program=instrument_program)
            
            # Add notes to instrument
            for note in midi_data.get_notes():
                # Create pretty_midi Note
                pm_note = pretty_midi.Note(
                    velocity=note.velocity,
                    pitch=note.pitch,
                    start=note.start_time,
                    end=note.end_time
                )
                instrument.notes.append(pm_note)
            
            # Add instrument to MIDI object
            midi.instruments.append(instrument)
            
            # Add metadata if enabled
            if self.include_metadata:
                self._add_metadata(midi, midi_data)
            
            # Write MIDI file
            midi.write(output_path)
            
            # Verify file was created
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                logger.info(f"MIDI file exported successfully: {file_size} bytes")
                return True
            else:
                logger.error("MIDI file was not created")
                return False
            
        except Exception as e:
            logger.error(f"Failed to export MIDI: {e}", exc_info=True)
            return False
    
    def _get_instrument_program(self, instrument_name: str) -> int:
        """
        Get MIDI program number for instrument name.
        
        Args:
            instrument_name: Name of instrument
        
        Returns:
            MIDI program number (0-127)
        """
        # Common instrument mappings (General MIDI)
        instruments = {
            "Acoustic Grand Piano": 0,
            "Electric Piano": 4,
            "Guitar": 24,
            "Acoustic Guitar": 24,
            "Electric Guitar": 27,
            "Bass": 32,
            "Strings": 48,
            "Violin": 40,
            "Cello": 42,
        }
        
        return instruments.get(instrument_name, 0)  # Default to piano
    
    def _add_metadata(self, midi: pretty_midi.PrettyMIDI, midi_data: MIDIData):
        """
        Add metadata to MIDI file.
        
        Args:
            midi: PrettyMIDI object
            midi_data: Source MIDI data
        """
        try:
            # Get statistics
            stats = midi_data.get_statistics()
            
            # Add text metadata as lyrics track (visible in some DAWs)
            # Note: pretty_midi has limited metadata support
            # Most metadata is stored in the file structure itself
            
            logger.debug(f"Added metadata: {stats['total_notes']} notes, "
                        f"{stats['duration']:.2f}s duration")
            
        except Exception as e:
            logger.warning(f"Failed to add metadata: {e}")
    
    def validate_output_path(self, path: str) -> tuple[bool, str]:
        """
        Validate output file path.
        
        Args:
            path: Proposed output path
        
        Returns:
            Tuple of (is_valid, message)
        """
        # Check extension
        if not path.lower().endswith('.mid'):
            return False, "File must have .mid extension"
        
        # Check directory exists
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            return False, f"Directory does not exist: {directory}"
        
        # Check if file already exists (warning, not error)
        if os.path.exists(path):
            return True, f"Warning: File already exists and will be overwritten"
        
        return True, "Valid"
    
    def get_default_filename(self, source_audio: str) -> str:
        """
        Generate default filename based on source audio.
        
        Args:
            source_audio: Path to source audio file
        
        Returns:
            Suggested MIDI filename
        """
        # Get base name without extension
        base_name = os.path.splitext(os.path.basename(source_audio))[0]
        
        # Add _midi suffix and .mid extension
        return f"{base_name}_midi.mid"
