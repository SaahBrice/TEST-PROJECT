# gui/processing_thread.py
"""
Processing Thread for AudioViz MIDI.
Handles audio transcription in a background thread to keep UI responsive.
"""

from PyQt5.QtCore import QThread, pyqtSignal
from audio import AudioLoader, PitchDetector, OnsetDetector
from midi import MIDIConverter, NoteQuantizer
from utils.logger import get_logger

logger = get_logger(__name__)


class ProcessingThread(QThread):
    """
    Background thread for audio-to-MIDI transcription.
    
    Signals:
        progress_updated: Emitted with progress percentage (0-100) and status message
        processing_complete: Emitted with MIDIData object when complete
        processing_error: Emitted with error message if processing fails
    """
    
    # Signals
    progress_updated = pyqtSignal(int, str)  # (percentage, message)
    processing_complete = pyqtSignal(object)  # (midi_data)
    processing_error = pyqtSignal(str)  # (error_message)
    
    def __init__(self, file_path: str):
        """
        Initialize processing thread.
        
        Args:
            file_path: Path to audio file to process
        """
        super().__init__()
        self.file_path = file_path
        self.is_cancelled = False
        
        logger.debug(f"ProcessingThread created for: {file_path}")
    
    def run(self):
        """Execute the processing pipeline in background thread."""
        try:
            logger.info("=" * 60)
            logger.info("Starting Audio-to-MIDI Transcription")
            logger.info("=" * 60)
            
            # Step 1: Load audio (0-20%)
            self.progress_updated.emit(0, "Loading audio file...")
            logger.info("Step 1: Loading audio...")
            
            loader = AudioLoader()
            audio_data, sample_rate = loader.load_audio(self.file_path)
            
            if self.is_cancelled:
                return
            
            audio_info = loader.get_audio_info()
            logger.info(f"Audio loaded: {audio_info['duration']:.2f}s, {sample_rate} Hz")
            self.progress_updated.emit(20, f"Audio loaded: {audio_info['duration']:.1f}s")
            
            # Step 2: Detect pitch (20-50%)
            self.progress_updated.emit(20, "Detecting pitch...")
            logger.info("Step 2: Detecting pitch...")
            
            pitch_detector = PitchDetector()
            frequencies, confidences, times = pitch_detector.detect_pitch(
                audio_data, sample_rate
            )
            
            if self.is_cancelled:
                return
            
            pitch_stats = pitch_detector.get_detection_stats()
            logger.info(f"Pitch detection: {pitch_stats['frames_with_pitch']} frames detected")
            self.progress_updated.emit(50, "Pitch detected")
            
            # Step 3: Detect onsets (50-65%)
            self.progress_updated.emit(50, "Detecting note onsets...")
            logger.info("Step 3: Detecting onsets...")
            
            onset_detector = OnsetDetector()
            onset_times, _ = onset_detector.detect_onsets(audio_data, sample_rate)
            
            if self.is_cancelled:
                return
            
            onset_stats = onset_detector.get_detection_stats()
            logger.info(f"Onset detection: {onset_stats['total_onsets']} onsets found")
            self.progress_updated.emit(65, f"Found {len(onset_times)} notes")
            
            # Step 4: Convert to MIDI (65-80%)
            self.progress_updated.emit(65, "Converting to MIDI...")
            logger.info("Step 4: Converting to MIDI...")
            
            midi_converter = MIDIConverter()
            midi_data = midi_converter.convert_to_midi(
                frequencies, confidences, times, onset_times
            )
            
            if self.is_cancelled:
                return
            
            logger.info(f"MIDI conversion: {len(midi_data)} notes created")
            self.progress_updated.emit(80, f"Created {len(midi_data)} MIDI notes")
            
            # Step 5: Quantize/clean notes (80-95%)
            self.progress_updated.emit(80, "Improving note quality...")
            logger.info("Step 5: Quantizing notes...")
            
            quantizer = NoteQuantizer()
            midi_data_quantized = quantizer.quantize(midi_data)
            
            if self.is_cancelled:
                return
            
            logger.info(f"Quantization: {len(midi_data_quantized)} notes (filtered from {len(midi_data)})")
            self.progress_updated.emit(95, "Finalizing...")
            
            # Step 6: Complete (95-100%)
            stats = midi_data_quantized.get_statistics()
            logger.info("=" * 60)
            logger.info("Transcription Complete!")
            logger.info(f"Total notes: {stats['total_notes']}")
            logger.info(f"Duration: {stats['duration']:.2f}s")
            logger.info(f"Pitch range: {stats['pitch_range']}")
            logger.info("=" * 60)
            
            self.progress_updated.emit(100, "Complete!")
            
            # Emit completion signal
            self.processing_complete.emit(midi_data_quantized)
            
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}", exc_info=True)
            self.processing_error.emit(str(e))
    
    def cancel(self):
        """Cancel the processing operation."""
        self.is_cancelled = True
        logger.info("Processing cancelled by user")
