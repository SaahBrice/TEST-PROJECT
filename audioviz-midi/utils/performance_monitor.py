# utils/performance_monitor.py
"""
Performance Monitor for AudioViz MIDI.
Tracks memory usage, processing times, and performance metrics.
"""

import time
import psutil
import os
from typing import Optional, Dict
from utils.logger import get_logger

logger = get_logger(__name__)


class PerformanceMonitor:
    """
    Monitors application performance and resource usage.
    
    Tracks processing times, memory usage, and provides optimization insights.
    """
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.process = psutil.Process(os.getpid())
        self.start_times = {}
        self.metrics = {}
        
        logger.info("PerformanceMonitor initialized")
    
    def start_timer(self, operation: str):
        """
        Start timing an operation.
        
        Args:
            operation: Name of operation to time
        """
        self.start_times[operation] = time.time()
        logger.debug(f"Timer started: {operation}")
    
    def stop_timer(self, operation: str) -> float:
        """
        Stop timing an operation and log the duration.
        
        Args:
            operation: Name of operation
        
        Returns:
            Duration in seconds
        """
        if operation not in self.start_times:
            logger.warning(f"Timer not found: {operation}")
            return 0.0
        
        duration = time.time() - self.start_times[operation]
        
        # Store metric
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration)
        
        # Log
        logger.info(f"⏱️  {operation}: {duration:.3f}s")
        
        # Remove start time
        del self.start_times[operation]
        
        return duration
    
    def get_memory_usage(self) -> Dict[str, float]:
        """
        Get current memory usage.
        
        Returns:
            Dictionary with memory usage in MB
        """
        memory_info = self.process.memory_info()
        
        usage = {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
        }
        
        return usage
    
    def log_memory_usage(self, label: str = "Current"):
        """
        Log current memory usage.
        
        Args:
            label: Label for the log entry
        """
        usage = self.get_memory_usage()
        logger.info(f"💾 {label} Memory: {usage['rss_mb']:.1f} MB (RSS), "
                   f"{usage['vms_mb']:.1f} MB (VMS)")
        
        # Warn if high memory usage
        if usage['rss_mb'] > 500:
            logger.warning(f"High memory usage: {usage['rss_mb']:.1f} MB")
    
    def get_cpu_usage(self) -> float:
        """
        Get current CPU usage percentage.
        
        Returns:
            CPU usage percentage
        """
        return self.process.cpu_percent(interval=0.1)
    
    def log_cpu_usage(self):
        """Log current CPU usage."""
        cpu = self.get_cpu_usage()
        logger.info(f"🔥 CPU Usage: {cpu:.1f}%")
    
    def get_operation_stats(self, operation: str) -> Optional[Dict]:
        """
        Get statistics for an operation.
        
        Args:
            operation: Operation name
        
        Returns:
            Dictionary with statistics or None
        """
        if operation not in self.metrics or not self.metrics[operation]:
            return None
        
        times = self.metrics[operation]
        
        return {
            'count': len(times),
            'total': sum(times),
            'average': sum(times) / len(times),
            'min': min(times),
            'max': max(times)
        }
    
    def log_summary(self):
        """Log a summary of all performance metrics."""
        logger.info("=" * 60)
        logger.info("Performance Summary")
        logger.info("=" * 60)
        
        # Memory
        self.log_memory_usage("Final")
        
        # CPU
        self.log_cpu_usage()
        
        # Operations
        if self.metrics:
            logger.info("\nOperation Timings:")
            for operation, times in self.metrics.items():
                stats = self.get_operation_stats(operation)
                logger.info(f"  {operation}:")
                logger.info(f"    Count: {stats['count']}")
                logger.info(f"    Average: {stats['average']:.3f}s")
                logger.info(f"    Min: {stats['min']:.3f}s")
                logger.info(f"    Max: {stats['max']:.3f}s")
        
        logger.info("=" * 60)
    
    def check_performance_targets(self) -> Dict[str, bool]:
        """
        Check if performance targets are met.
        
        Returns:
            Dictionary of target checks
        """
        targets = {}
        
        # Memory target: < 500 MB
        memory = self.get_memory_usage()
        targets['memory_ok'] = memory['rss_mb'] < 500
        
        # Transcription target: < 45s for 3-minute audio
        transcription_stats = self.get_operation_stats('transcription')
        if transcription_stats:
            # Estimate for 3-minute audio based on actual duration
            targets['transcription_ok'] = transcription_stats['average'] < 45
        
        return targets


# Global performance monitor instance
_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """
    Get global performance monitor instance.
    
    Returns:
        PerformanceMonitor instance
    """
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor
