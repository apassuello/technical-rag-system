"""
Mock Memory System for Epic 1 Infrastructure Testing.

Provides controllable memory simulation for testing memory monitoring,
cache eviction, and memory pressure scenarios.
"""

import time
import threading
from typing import Dict, Optional, List, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import random


class MemoryPressureLevel(Enum):
    """Memory pressure levels for simulation."""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MockMemoryStats:
    """Mock system memory statistics."""
    
    total_mb: float
    used_mb: float
    available_mb: float
    percent_used: float
    process_mb: float
    
    def __post_init__(self):
        # Validate consistency
        if abs(self.used_mb + self.available_mb - self.total_mb) > 0.1:
            # Auto-correct available memory
            self.available_mb = self.total_mb - self.used_mb
        
        if abs(self.percent_used - (self.used_mb / self.total_mb * 100)) > 0.1:
            # Auto-correct percentage
            self.percent_used = self.used_mb / self.total_mb * 100


@dataclass  
class MockMemoryConfig:
    """Configuration for mock memory system behavior."""
    
    total_memory_mb: float = 16384.0  # 16GB default
    initial_used_mb: float = 8192.0   # 8GB initial usage
    process_initial_mb: float = 512.0 # 512MB initial process usage
    pressure_simulation: bool = True
    pressure_change_rate: float = 10.0  # MB per second
    enable_random_fluctuation: bool = True
    fluctuation_amplitude: float = 100.0  # MB
    cross_platform_simulation: bool = True


class MockMemorySystem:
    """
    Mock system memory that simulates realistic memory behavior.
    
    Features:
    - Configurable memory pressure simulation
    - Process memory tracking
    - Cross-platform behavior simulation
    - Thread-safe operations
    - Realistic memory allocation patterns
    """
    
    def __init__(self, config: MockMemoryConfig = None):
        self.config = config or MockMemoryConfig()
        
        # Current memory state
        self._total_memory_mb = self.config.total_memory_mb
        self._used_memory_mb = self.config.initial_used_mb
        self._process_memory_mb = self.config.process_initial_mb
        
        # Memory allocations tracking
        self._allocations: Dict[str, float] = {}  # allocation_id -> size_mb
        self._allocation_counter = 0
        
        # Pressure simulation
        self._target_pressure_level = MemoryPressureLevel.LOW
        self._pressure_change_direction = 1  # 1 for increasing, -1 for decreasing
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Background simulation
        self._simulation_running = False
        self._simulation_thread = None
        
        # Callbacks for pressure changes
        self._pressure_callbacks: List[Callable[[MemoryPressureLevel], None]] = []
    
    def start_simulation(self) -> None:
        """Start background memory simulation."""
        with self._lock:
            if self._simulation_running:
                return
                
            self._simulation_running = True
            self._simulation_thread = threading.Thread(
                target=self._simulation_loop,
                daemon=True
            )
            self._simulation_thread.start()
    
    def stop_simulation(self) -> None:
        """Stop background memory simulation."""
        with self._lock:
            self._simulation_running = False
            if self._simulation_thread:
                self._simulation_thread.join(timeout=1.0)
    
    def _simulation_loop(self) -> None:
        """Background simulation loop."""
        while self._simulation_running:
            try:
                self._update_simulation()
                time.sleep(0.1)  # Update every 100ms
            except Exception:
                pass  # Ignore simulation errors
    
    def _update_simulation(self) -> None:
        """Update memory simulation state."""
        with self._lock:
            old_pressure = self.get_memory_pressure_level()
            
            # Random fluctuation
            if self.config.enable_random_fluctuation:
                fluctuation = random.uniform(
                    -self.config.fluctuation_amplitude,
                    self.config.fluctuation_amplitude
                )
                self._used_memory_mb += fluctuation * 0.1  # Scale down for frequent updates
            
            # Pressure simulation
            if self.config.pressure_simulation:
                pressure_change = (
                    self.config.pressure_change_rate * 
                    self._pressure_change_direction * 
                    0.1  # Scale for update frequency
                )
                
                new_used = self._used_memory_mb + pressure_change
                
                # Bound within realistic limits
                new_used = max(
                    self.config.total_memory_mb * 0.1,  # Minimum 10% usage
                    min(new_used, self.config.total_memory_mb * 0.95)  # Maximum 95% usage
                )
                
                # Change direction if at limits or randomly
                if (new_used >= self.config.total_memory_mb * 0.9 or 
                    new_used <= self.config.total_memory_mb * 0.2 or
                    random.random() < 0.01):  # 1% chance to change direction
                    self._pressure_change_direction *= -1
                
                self._used_memory_mb = new_used
            
            # Notify pressure callbacks if pressure level changed
            new_pressure = self.get_memory_pressure_level()
            if new_pressure != old_pressure:
                for callback in self._pressure_callbacks:
                    try:
                        callback(new_pressure)
                    except Exception:
                        pass  # Ignore callback errors
    
    def get_memory_stats(self) -> MockMemoryStats:
        """Get current memory statistics."""
        with self._lock:
            available_mb = self._total_memory_mb - self._used_memory_mb
            percent_used = (self._used_memory_mb / self._total_memory_mb) * 100
            
            return MockMemoryStats(
                total_mb=self._total_memory_mb,
                used_mb=self._used_memory_mb,
                available_mb=available_mb,
                percent_used=percent_used,
                process_mb=self._process_memory_mb
            )
    
    def allocate_memory(self, size_mb: float, allocation_id: Optional[str] = None) -> str:
        """
        Simulate memory allocation.
        
        Args:
            size_mb: Size to allocate in MB
            allocation_id: Optional allocation identifier
            
        Returns:
            Allocation ID for tracking
        """
        with self._lock:
            if allocation_id is None:
                self._allocation_counter += 1
                allocation_id = f"alloc_{self._allocation_counter}"
            
            # Check if allocation would exceed available memory
            available = self._total_memory_mb - self._used_memory_mb
            if size_mb > available:
                raise MemoryError(f"Cannot allocate {size_mb}MB, only {available:.1f}MB available")
            
            # Record allocation
            self._allocations[allocation_id] = size_mb
            self._process_memory_mb += size_mb
            self._used_memory_mb += size_mb
            
            return allocation_id
    
    def deallocate_memory(self, allocation_id: str) -> float:
        """
        Simulate memory deallocation.
        
        Args:
            allocation_id: Allocation to free
            
        Returns:
            Size that was freed in MB
        """
        with self._lock:
            if allocation_id not in self._allocations:
                return 0.0
            
            size_mb = self._allocations.pop(allocation_id)
            self._process_memory_mb -= size_mb
            self._used_memory_mb -= size_mb
            
            return size_mb
    
    def get_allocation_size(self, allocation_id: str) -> Optional[float]:
        """Get size of a specific allocation."""
        with self._lock:
            return self._allocations.get(allocation_id)
    
    def get_total_allocations(self) -> float:
        """Get total allocated memory in MB."""
        with self._lock:
            return sum(self._allocations.values())
    
    def get_allocation_count(self) -> int:
        """Get number of active allocations."""
        with self._lock:
            return len(self._allocations)
    
    def get_memory_pressure_level(self) -> MemoryPressureLevel:
        """Get current memory pressure level."""
        stats = self.get_memory_stats()
        usage_ratio = stats.used_mb / stats.total_mb
        
        if usage_ratio < 0.5:
            return MemoryPressureLevel.LOW
        elif usage_ratio < 0.7:
            return MemoryPressureLevel.MEDIUM
        elif usage_ratio < 0.9:
            return MemoryPressureLevel.HIGH
        else:
            return MemoryPressureLevel.CRITICAL
    
    def add_pressure_callback(self, callback: Callable[[MemoryPressureLevel], None]) -> None:
        """Add callback for memory pressure changes."""
        self._pressure_callbacks.append(callback)
    
    def remove_pressure_callback(self, callback: Callable[[MemoryPressureLevel], None]) -> None:
        """Remove pressure callback."""
        if callback in self._pressure_callbacks:
            self._pressure_callbacks.remove(callback)
    
    def set_pressure_level(self, level: MemoryPressureLevel) -> None:
        """Manually set memory pressure level."""
        with self._lock:
            target_ratios = {
                MemoryPressureLevel.LOW: 0.3,
                MemoryPressureLevel.MEDIUM: 0.6,
                MemoryPressureLevel.HIGH: 0.8,
                MemoryPressureLevel.CRITICAL: 0.95
            }
            
            target_ratio = target_ratios[level]
            self._used_memory_mb = self._total_memory_mb * target_ratio
    
    def simulate_memory_leak(self, rate_mb_per_second: float, duration_seconds: float) -> None:
        """Simulate a memory leak for testing."""
        def leak_simulation():
            start_time = time.time()
            while time.time() - start_time < duration_seconds:
                try:
                    self.allocate_memory(rate_mb_per_second)
                    time.sleep(1.0)
                except MemoryError:
                    break  # Stop if out of memory
        
        thread = threading.Thread(target=leak_simulation, daemon=True)
        thread.start()
        return thread
    
    def reset_to_defaults(self) -> None:
        """Reset memory system to default state."""
        with self._lock:
            self._used_memory_mb = self.config.initial_used_mb
            self._process_memory_mb = self.config.process_initial_mb
            self._allocations.clear()
            self._allocation_counter = 0
            self._pressure_change_direction = 1


class MockMemoryMonitor:
    """
    Mock version of MemoryMonitor that uses MockMemorySystem.
    
    Can be used as a drop-in replacement for real MemoryMonitor in tests.
    """
    
    def __init__(self, memory_system: MockMemorySystem = None):
        self.memory_system = memory_system or MockMemorySystem()
        self._monitoring = False
        self._update_interval = 1.0
    
    def start_monitoring(self) -> None:
        """Start memory monitoring."""
        self._monitoring = True
        self.memory_system.start_simulation()
    
    def stop_monitoring(self) -> None:
        """Stop memory monitoring."""
        self._monitoring = False
        self.memory_system.stop_simulation()
    
    def get_current_stats(self):
        """Get current memory statistics in MemoryStats format."""
        mock_stats = self.memory_system.get_memory_stats()
        
        # Convert to the format expected by real MemoryMonitor
        from src.components.query_processors.analyzers.ml_models.memory_monitor import MemoryStats
        
        return MemoryStats(
            total_mb=mock_stats.total_mb,
            used_mb=mock_stats.used_mb,
            available_mb=mock_stats.available_mb,
            percent_used=mock_stats.percent_used,
            epic1_process_mb=mock_stats.process_mb
        )
    
    def get_epic1_memory_usage(self) -> float:
        """Get Epic1 process memory usage."""
        return self.memory_system.get_memory_stats().process_mb
    
    def estimate_model_memory(self, model_name: str, quantized: bool = True) -> float:
        """Estimate model memory usage."""
        # Use the same estimates as real MemoryMonitor
        estimates = {
            'SciBERT': 440 if not quantized else 220,
            'DistilBERT': 260 if not quantized else 130,
            'DeBERTa-v3': 750 if not quantized else 375,
            'Sentence-BERT': 420 if not quantized else 210,
            'T5-small': 240 if not quantized else 120,
        }
        
        base_size = estimates.get(model_name, 300 if not quantized else 150)
        return base_size + 50  # Add overhead
    
    def would_exceed_budget(self, model_name: str, memory_budget_mb: float, quantized: bool = True) -> bool:
        """Check if loading model would exceed budget."""
        current_usage = self.get_epic1_memory_usage()
        estimated_model_size = self.estimate_model_memory(model_name, quantized)
        return (current_usage + estimated_model_size) > memory_budget_mb
    
    def get_memory_pressure_level(self, memory_budget_mb: float) -> str:
        """Get memory pressure level."""
        current_usage = self.get_epic1_memory_usage()
        usage_ratio = current_usage / memory_budget_mb
        
        if usage_ratio < 0.5:
            return 'low'
        elif usage_ratio < 0.7:
            return 'medium'
        elif usage_ratio < 0.9:
            return 'high'
        else:
            return 'critical'
    
    def record_actual_model_memory(self, model_name: str, memory_mb: float) -> None:
        """Record actual model memory usage."""
        # Simulate allocation in mock system
        try:
            self.memory_system.allocate_memory(memory_mb, f"model_{model_name}")
        except MemoryError:
            pass  # Ignore if allocation fails
    
    def get_eviction_candidates(self, target_free_mb: float) -> Dict[str, float]:
        """Get models that could be evicted."""
        # For testing, return some mock candidates
        allocations = {}
        total_freed = 0
        
        for i in range(1, 6):  # Return up to 5 candidates
            candidate_size = random.uniform(100, 500)
            allocations[f"model_{i}"] = candidate_size
            total_freed += candidate_size
            
            if total_freed >= target_free_mb:
                break
        
        return allocations


def create_memory_test_scenarios() -> Dict[str, MockMemorySystem]:
    """
    Create predefined memory scenarios for testing.
    
    Returns:
        Dict of scenario_name -> MockMemorySystem configured for that scenario
    """
    scenarios = {}
    
    # Low memory scenario (16GB total, high usage)
    scenarios['low_memory'] = MockMemorySystem(MockMemoryConfig(
        total_memory_mb=16384,
        initial_used_mb=14000,  # ~86% usage
        pressure_simulation=False
    ))
    
    # High memory scenario (64GB total, low usage)  
    scenarios['high_memory'] = MockMemorySystem(MockMemoryConfig(
        total_memory_mb=65536,
        initial_used_mb=8000,   # ~12% usage
        pressure_simulation=False
    ))
    
    # Memory pressure scenario (dynamic pressure changes)
    scenarios['memory_pressure'] = MockMemorySystem(MockMemoryConfig(
        total_memory_mb=32768,
        initial_used_mb=16000,
        pressure_simulation=True,
        pressure_change_rate=50.0  # Fast changes for testing
    ))
    
    # Stable memory scenario (no fluctuations)
    scenarios['stable_memory'] = MockMemorySystem(MockMemoryConfig(
        total_memory_mb=32768,
        initial_used_mb=10000,
        pressure_simulation=False,
        enable_random_fluctuation=False
    ))
    
    # Memory constrained scenario (small memory, high usage)
    scenarios['constrained_memory'] = MockMemorySystem(MockMemoryConfig(
        total_memory_mb=8192,
        initial_used_mb=7000,   # ~85% usage
        pressure_simulation=False
    ))
    
    return scenarios


def create_cross_platform_memory_configs() -> Dict[str, MockMemoryConfig]:
    """Create memory configurations simulating different platforms."""
    return {
        'linux_server': MockMemoryConfig(
            total_memory_mb=128 * 1024,  # 128GB
            initial_used_mb=32 * 1024,   # 32GB
            process_initial_mb=2048
        ),
        'macos_laptop': MockMemoryConfig(
            total_memory_mb=32 * 1024,   # 32GB
            initial_used_mb=16 * 1024,   # 16GB
            process_initial_mb=1024
        ),
        'windows_workstation': MockMemoryConfig(
            total_memory_mb=64 * 1024,   # 64GB
            initial_used_mb=24 * 1024,   # 24GB
            process_initial_mb=1536
        ),
        'resource_constrained': MockMemoryConfig(
            total_memory_mb=8 * 1024,    # 8GB
            initial_used_mb=6 * 1024,    # 6GB
            process_initial_mb=512
        )
    }