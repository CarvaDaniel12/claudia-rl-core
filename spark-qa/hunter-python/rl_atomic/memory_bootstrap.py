"""
MEMORY BOOTSTRAP - Minimal functional implementation
Loads best patterns into memory for next cycle
"""
from dataclasses import dataclass
from typing import Dict, List
from pathlib import Path

@dataclass
class EfficiencyFrontier:
    """Efficiency frontier data"""
    best_time: float = 999.0
    best_reliability: float = 0.0

@dataclass
class WorkingMemory:
    """Working memory data"""
    best_actions: Dict = None
    common_trajectories: List = None
    
    def __post_init__(self):
        if self.best_actions is None:
            self.best_actions = {}
        if self.common_trajectories is None:
            self.common_trajectories = []

@dataclass
class MetaStat:
    """Meta statistics"""
    cycles_completed: int = 0

class MemoryBootstrap:
    """Minimal memory bootstrap for compatibility"""
    
    def __init__(self):
        self.working_memory = WorkingMemory()

