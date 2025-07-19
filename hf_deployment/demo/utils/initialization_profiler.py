"""
Initialization profiler for Epic 2 Demo
=======================================

Simplified profiler for HF deployment
"""

import logging
import time
from contextlib import contextmanager
from typing import Dict, Any

logger = logging.getLogger(__name__)


class InitializationProfiler:
    """Profile initialization steps"""
    
    def __init__(self):
        self.steps = {}
        self.start_time = None
        
    def start_profiling(self):
        """Start profiling"""
        self.start_time = time.time()
        self.steps = {}
        logger.info("Profiling started")
    
    @contextmanager
    def profile_step(self, step_name: str):
        """Profile a step"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.steps[step_name] = duration
            logger.debug(f"Step {step_name} took {duration:.3f}s")
    
    def finish_profiling(self):
        """Finish profiling"""
        if self.start_time:
            total_time = time.time() - self.start_time
            logger.info(f"Total profiling time: {total_time:.3f}s")
    
    def print_report(self):
        """Print profiling report"""
        logger.info("Profiling report:")
        for step, duration in self.steps.items():
            logger.info(f"  {step}: {duration:.3f}s")


# Global profiler instance
profiler = InitializationProfiler()