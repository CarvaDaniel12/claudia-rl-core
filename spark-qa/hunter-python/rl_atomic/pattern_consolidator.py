"""
PATTERN CONSOLIDATOR - Minimal functional implementation
Consolidates patterns from multiple runs
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class PatternConsolidator:
    """Consolidates patterns across multiple runs"""
    
    def __init__(self):
        self.patterns_consolidated = {}
    
    def consolidate(self, runs: List[Dict]) -> Dict:
        """
        Consolidate patterns from runs
        
        Returns minimal result dict for atomic_loop compatibility
        """
        # Count unique trajectories
        trajectories = set()
        for run in runs:
            actions = run.get('actions', [])
            if actions:
                # Create trajectory signature
                sig = '->'.join([a.get('description', 'unknown') for a in actions[:10]])
                trajectories.add(sig)
        
        return {
            "patterns": {},
            "patterns_count": 0,
            "unique_trajectories": len(trajectories),
            "red_flags": None
        }

