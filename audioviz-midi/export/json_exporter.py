# export/json_exporter.py
"""
JSON Exporter Module for AudioViz MIDI.
Exports MIDI data to JSON format with detailed note information.
"""

import json
import os
from typing import Optional
from midi import MIDIData
from utils.logger import get_logger
from utils.config import ConfigManager

logger = get_logger(__name__)


class JSONExporter:
    """
    Exports MIDI data to JSON format.
    
    Creates human-readable JSON files with complete note information
    including timing, pitch, frequency, note names, and velocities.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """
        Initialize the JSON exporter.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config or ConfigManager()
        
        # Load export settings
        self.include_metadata = self.config.get('export', 'include_metadata', True)
        
        logger.info("JSONExporter initialized")
    
    def export(self, midi_data: MIDIData, output_path: str,
               source_file: Optional[str] = None) -> bool:
        """
        Export MIDI data to JSON file.
        
        Args:
            midi_data: MIDIData object containing notes
            output_path: Output file path (.json)
            source_file: Optional source audio filename for metadata
        
        Returns:
            True if export successful, False otherwise
        """
        try:
            logger.info(f"Exporting JSON to: {output_path}")
            
            if not midi_data or len(midi_data) == 0:
                logger.error("No MIDI data to export")
                return False
            
            # Build JSON structure
            data = {
                "format": "AudioViz MIDI JSON Export",
                "version": "1.0"
            }
            
            # Add metadata if enabled
            if self.include_metadata:
                data["metadata"] = self._build_metadata(midi_data, source_file)
            
            # Add notes
            data["notes"] = midi_data.to_dict_list()
            
            # Write JSON file with pretty formatting
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Verify file was created
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                logger.info(f"JSON file exported successfully: {file_size} bytes")
                return True
            else:
                logger.error("JSON file was not created")
                return False
            
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}", exc_info=True)
            return False
    
    def _build_metadata(self, midi_data: MIDIData, source_file: Optional[str]) -> dict:
        """
        Build metadata dictionary.
        
        Args:
            midi_data: Source MIDI data
            source_file: Source audio filename
        
        Returns:
            Metadata dictionary
        """
        stats = midi_data.get_statistics()
        
        metadata = {
            "total_notes": stats['total_notes'],
            "duration_seconds": round(stats['duration'], 3),
            "pitch_range": {
                "min": stats['pitch_range'][0],
                "max": stats['pitch_range'][1]
            },
            "average_note_duration": round(stats['avg_note_duration'], 3),
            "average_velocity": round(stats['avg_velocity'], 1)
        }
        
        if source_file:
            metadata["source_file"] = os.path.basename(source_file)
        
        # Add timestamp
        from datetime import datetime
        metadata["export_date"] = datetime.now().isoformat()
        
        return metadata
    
    def validate_output_path(self, path: str) -> tuple[bool, str]:
        """
        Validate output file path.
        
        Args:
            path: Proposed output path
        
        Returns:
            Tuple of (is_valid, message)
        """
        # Check extension
        if not path.lower().endswith('.json'):
            return False, "File must have .json extension"
        
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
            Suggested JSON filename
        """
        # Get base name without extension
        base_name = os.path.splitext(os.path.basename(source_audio))[0]
        
        # Add _notes suffix and .json extension
        return f"{base_name}_notes.json"
