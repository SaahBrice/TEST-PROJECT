# midi/note_quantizer.py
"""
Note Quantizer Module for AudioViz MIDI.
Post-processes MIDI notes to improve quality and accuracy.
Filters spurious detections, removes short notes, and fills gaps.
"""

import numpy as np
from typing import List, Optional
from midi.note import Note
from midi.midi_data import MIDIData
from utils.logger import get_logger
from utils.config import ConfigManager

logger = get_logger(__name__)


class NoteQuantizer:
    """
    Improves MIDI note quality through post-processing.
    
    Applies various filtering and correction techniques:
    - Removes notes that are too short (likely spurious)
    - Merges adjacent notes with same pitch
    - Fills small gaps between consecutive notes
    - Filters out notes with very low velocity
    - Removes overlapping notes (keeps stronger one)
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """
        Initialize the Note Quantizer.
        
        Args:
            config: Configuration manager instance. If None, uses default settings.
        """
        self.config = config or ConfigManager()
        
        # Load quantization settings from config
        self.min_note_duration = self.config.get('pitch_detection', 'min_note_duration', 0.05)
        self.remove_short_notes = self.config.get('midi', 'remove_short_notes', True)
        self.fill_gaps = self.config.get('midi', 'fill_gaps', True)
        
        # Additional quantization parameters
        self.max_gap_to_fill = 0.1  # Maximum gap duration to fill (seconds)
        self.min_velocity = 30  # Minimum velocity to keep
        self.merge_threshold = 0.05  # Merge notes closer than this (seconds)
        
        logger.info("NoteQuantizer initialized")
        logger.debug(f"Remove short notes: {self.remove_short_notes}")
        logger.debug(f"Fill gaps: {self.fill_gaps}")
    
    def quantize(self, midi_data: MIDIData) -> MIDIData:
        """
        Apply all quantization steps to improve note quality.
        
        Args:
            midi_data: Input MIDI data
        
        Returns:
            New MIDIData object with quantized notes
        """
        logger.info("Starting note quantization...")
        notes = midi_data.get_notes()
        original_count = len(notes)
        
        if original_count == 0:
            logger.warning("No notes to quantize")
            return MIDIData()
        
        # Step 1: Remove short notes
        if self.remove_short_notes:
            notes = self._remove_short_notes(notes)
            logger.debug(f"After removing short notes: {len(notes)} notes")
        
        # Step 2: Remove low velocity notes
        notes = self._remove_low_velocity_notes(notes)
        logger.debug(f"After removing low velocity: {len(notes)} notes")
        
        # Step 3: Sort by start time
        notes.sort(key=lambda n: n.start_time)
        
        # Step 4: Merge adjacent notes with same pitch
        notes = self._merge_adjacent_notes(notes)
        logger.debug(f"After merging adjacent: {len(notes)} notes")
        
        # Step 5: Fill gaps between consecutive notes
        if self.fill_gaps:
            notes = self._fill_gaps(notes)
            logger.debug(f"After filling gaps: {len(notes)} notes")
        
        # Step 6: Remove overlapping notes
        notes = self._remove_overlaps(notes)
        logger.debug(f"After removing overlaps: {len(notes)} notes")
        
        # Create new MIDIData with quantized notes
        quantized = MIDIData(notes)
        
        logger.info(f"Quantization complete: {original_count} -> {len(quantized)} notes")
        
        return quantized
    
    def _remove_short_notes(self, notes: List[Note]) -> List[Note]:
        """
        Remove notes shorter than minimum duration.
        
        Args:
            notes: List of notes
        
        Returns:
            Filtered list of notes
        """
        filtered = []
        removed_count = 0
        
        for note in notes:
            if note.duration >= self.min_note_duration:
                filtered.append(note)
            else:
                removed_count += 1
                logger.debug(f"Removed short note: {note.note_name} (duration: {note.duration:.3f}s)")
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} short notes")
        
        return filtered
    
    def _remove_low_velocity_notes(self, notes: List[Note]) -> List[Note]:
        """
        Remove notes with velocity below threshold.
        
        Args:
            notes: List of notes
        
        Returns:
            Filtered list of notes
        """
        filtered = []
        removed_count = 0
        
        for note in notes:
            if note.velocity >= self.min_velocity:
                filtered.append(note)
            else:
                removed_count += 1
                logger.debug(f"Removed low velocity note: {note.note_name} (velocity: {note.velocity})")
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} low velocity notes")
        
        return filtered
    
    def _merge_adjacent_notes(self, notes: List[Note]) -> List[Note]:
        """
        Merge consecutive notes with same pitch that are very close together.
        
        Args:
            notes: List of notes (must be sorted by start time)
        
        Returns:
            List with merged notes
        """
        if len(notes) <= 1:
            return notes
        
        merged = []
        current = notes[0]
        merge_count = 0
        
        for i in range(1, len(notes)):
            next_note = notes[i]
            
            # Check if notes have same pitch and are close together
            gap = next_note.start_time - current.end_time
            
            if (current.pitch == next_note.pitch and 
                0 <= gap <= self.merge_threshold):
                # Merge notes by extending current to end of next
                current = Note(
                    pitch=current.pitch,
                    start_time=current.start_time,
                    end_time=next_note.end_time,
                    velocity=max(current.velocity, next_note.velocity)
                )
                merge_count += 1
                logger.debug(f"Merged {next_note.note_name} notes (gap: {gap:.3f}s)")
            else:
                # Different pitch or gap too large - save current and move to next
                merged.append(current)
                current = next_note
        
        # Add the last note
        merged.append(current)
        
        if merge_count > 0:
            logger.info(f"Merged {merge_count} adjacent note pairs")
        
        return merged
    
    def _fill_gaps(self, notes: List[Note]) -> List[Note]:
        """
        Fill small gaps between consecutive notes by extending note durations.
        
        Args:
            notes: List of notes (must be sorted by start time)
        
        Returns:
            List with gap-filled notes
        """
        if len(notes) <= 1:
            return notes
        
        filled = []
        fill_count = 0
        
        for i in range(len(notes) - 1):
            current = notes[i]
            next_note = notes[i + 1]
            
            # Calculate gap
            gap = next_note.start_time - current.end_time
            
            # If gap is small and positive, extend current note
            if 0 < gap <= self.max_gap_to_fill:
                # Extend current note to meet next note
                filled_note = Note(
                    pitch=current.pitch,
                    start_time=current.start_time,
                    end_time=next_note.start_time,  # Extend to next note start
                    velocity=current.velocity
                )
                filled.append(filled_note)
                fill_count += 1
                logger.debug(f"Filled {gap:.3f}s gap after {current.note_name}")
            else:
                # Gap too large or negative (overlap) - keep original
                filled.append(current)
        
        # Add the last note
        filled.append(notes[-1])
        
        if fill_count > 0:
            logger.info(f"Filled {fill_count} gaps")
        
        return filled
    
    def _remove_overlaps(self, notes: List[Note]) -> List[Note]:
        """
        Remove or trim overlapping notes, keeping the one with higher velocity.
        
        Args:
            notes: List of notes (must be sorted by start time)
        
        Returns:
            List without overlapping notes
        """
        if len(notes) <= 1:
            return notes
        
        cleaned = []
        removed_count = 0
        
        for i in range(len(notes)):
            current = notes[i]
            has_overlap = False
            
            # Check if this note overlaps with any already added notes
            for existing in cleaned:
                if current.overlaps(existing):
                    has_overlap = True
                    
                    # Keep the note with higher velocity
                    if current.velocity > existing.velocity:
                        # Replace existing with current
                        cleaned.remove(existing)
                        cleaned.append(current)
                        logger.debug(f"Replaced {existing.note_name} with {current.note_name} (higher velocity)")
                    else:
                        # Keep existing, discard current
                        removed_count += 1
                        logger.debug(f"Removed overlapping {current.note_name} (lower velocity)")
                    break
            
            if not has_overlap:
                cleaned.append(current)
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} overlapping notes")
        
        # Sort by start time
        cleaned.sort(key=lambda n: n.start_time)
        
        return cleaned
    
    def set_min_duration(self, duration: float):
        """
        Set minimum note duration threshold.
        
        Args:
            duration: Minimum duration in seconds
        """
        if duration < 0:
            raise ValueError("Duration must be non-negative")
        
        self.min_note_duration = duration
        logger.info(f"Minimum note duration set to {duration}s")
    
    def set_gap_fill_threshold(self, threshold: float):
        """
        Set maximum gap size to fill.
        
        Args:
            threshold: Maximum gap in seconds
        """
        if threshold < 0:
            raise ValueError("Threshold must be non-negative")
        
        self.max_gap_to_fill = threshold
        logger.info(f"Gap fill threshold set to {threshold}s")
    
    def set_merge_threshold(self, threshold: float):
        """
        Set maximum gap for merging adjacent same-pitch notes.
        
        Args:
            threshold: Maximum gap in seconds
        """
        if threshold < 0:
            raise ValueError("Threshold must be non-negative")
        
        self.merge_threshold = threshold
        logger.info(f"Merge threshold set to {threshold}s")
    
    def enable_short_note_removal(self, enable: bool):
        """Enable or disable short note removal."""
        self.remove_short_notes = enable
        logger.info(f"Short note removal: {'enabled' if enable else 'disabled'}")
    
    def enable_gap_filling(self, enable: bool):
        """Enable or disable gap filling."""
        self.fill_gaps = enable
        logger.info(f"Gap filling: {'enabled' if enable else 'disabled'}")
