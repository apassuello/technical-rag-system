"""
Initialization Performance Profiler
===================================

Profiles the Epic 2 demo initialization process to identify bottlenecks
and optimize for <5s target.
"""

import time
import logging
from contextlib import contextmanager
from typing import Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class InitializationStep:
    """Represents a timed initialization step"""
    name: str
    start_time: float
    duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_ms(self) -> float:
        return self.duration * 1000


class InitializationProfiler:
    """Profiles initialization steps for performance optimization"""
    
    def __init__(self):
        self.steps: List[InitializationStep] = []
        self.start_time: float = 0
        self.total_duration: float = 0
        
    def start_profiling(self):
        """Start the initialization profiling"""
        self.start_time = time.time()
        self.steps.clear()
        logger.info("Starting initialization profiling")
    
    def finish_profiling(self):
        """Finish profiling and calculate total time"""
        self.total_duration = time.time() - self.start_time
        logger.info(f"Initialization profiling completed in {self.total_duration:.2f}s")
        
    @contextmanager
    def profile_step(self, step_name: str, metadata: Dict[str, Any] = None):
        """Context manager to profile an initialization step"""
        start_time = time.time()
        logger.info(f"Starting step: {step_name}")
        
        try:
            yield
        finally:
            duration = time.time() - start_time
            step = InitializationStep(
                name=step_name,
                start_time=start_time,
                duration=duration,
                metadata=metadata or {}
            )
            self.steps.append(step)
            logger.info(f"Completed step: {step_name} in {duration:.2f}s")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of initialization performance"""
        return {
            "total_time_s": self.total_duration,
            "target_time_s": 5.0,
            "over_target_s": max(0, self.total_duration - 5.0),
            "steps": [
                {
                    "name": step.name,
                    "duration_s": step.duration,
                    "duration_ms": step.duration_ms,
                    "percentage": (step.duration / self.total_duration) * 100 if self.total_duration > 0 else 0,
                    "metadata": step.metadata
                }
                for step in self.steps
            ]
        }
    
    def print_report(self):
        """Print a detailed profiling report"""
        print("\n" + "="*80)
        print("INITIALIZATION PERFORMANCE REPORT")
        print("="*80)
        print(f"Total Time: {self.total_duration:.2f}s (target: 5.0s)")
        
        if self.total_duration <= 5.0:
            print("✅ Target achieved!")
        else:
            print(f"❌ Need to optimize by {self.total_duration - 5.0:.2f}s")
        
        print("\nStep Breakdown:")
        print("-" * 80)
        print(f"{'Step':<35} {'Time':<10} {'%':<8} {'Details'}")
        print("-" * 80)
        
        for step in sorted(self.steps, key=lambda s: s.duration, reverse=True):
            percentage = (step.duration / self.total_duration) * 100 if self.total_duration > 0 else 0
            details = ", ".join(f"{k}={v}" for k, v in step.metadata.items())
            print(f"{step.name:<35} {step.duration:.2f}s{'':<4} {percentage:.1f}%{'':<3} {details}")
        
        print("-" * 80)
        print(f"{'TOTAL':<35} {self.total_duration:.2f}s{'':<4} {'100.0%':<8}")
        print("="*80)
        
        # Optimization recommendations
        print("\nOPTIMIZATION RECOMMENDATIONS:")
        print("-" * 80)
        
        slowest_steps = sorted(self.steps, key=lambda s: s.duration, reverse=True)[:3]
        for i, step in enumerate(slowest_steps, 1):
            print(f"{i}. Optimize '{step.name}' ({step.duration:.2f}s)")
        
        print("\n")


# Global profiler instance
profiler = InitializationProfiler()