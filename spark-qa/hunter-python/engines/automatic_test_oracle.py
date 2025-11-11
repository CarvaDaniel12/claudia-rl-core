"""
AUTOMATIC TEST ORACLE - Learn system invariants, detect violations

PROBLEM: Manual assertions don't catch all bugs
SOLUTION: ML learns "normal" system behavior, flags anomalies

APPROACH:
1. Learn from 200+ successful runs
2. Extract invariants (properties always true)
3. Detect violations in future runs

INVARIANTS TRACKED:
- Property always has UUID after creation
- Lead always has firstName + lastName
- Success response always contains specific fields
- State transitions follow expected patterns
- Duration within expected range (statistical outlier detection)

INTEGRATION:
- Trains from barril!! runs
- Validates each new run
- Flags anomalies for human review
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict
import statistics


class AutomaticTestOracle:
    """
    Learns system invariants from successful runs
    Detects violations (potential bugs) in new runs
    """
    
    def __init__(self, oracle_file: str = "barril!!/test_oracle.json"):
        self.oracle_file = Path(oracle_file)
        self.oracle_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Learned invariants
        self.invariants = {
            "required_fields": {},  # entity -> required field names
            "field_patterns": {},   # field -> pattern (type, range, etc)
            "state_transitions": defaultdict(set),  # from_state -> to_states
            "duration_stats": {},   # action -> {mean, std, min, max}
            "response_schemas": {}  # endpoint -> expected schema
        }
        
        # Training data
        self.training_runs = []
        self.trained = False
        self.min_training_runs = 50  # Need at least 50 successful runs
        
        # Violation tracking
        self.violations_found = []
        
        self._load()
    
    def _load(self):
        """Load learned invariants"""
        if self.oracle_file.exists():
            try:
                with open(self.oracle_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.invariants = data.get('invariants', self.invariants)
                    self.trained = data.get('trained', False)
                    self.training_runs = data.get('training_runs', [])
                    print(f"[Oracle] Loaded - Trained on {len(self.training_runs)} runs")
            except Exception as e:
                print(f"[Oracle] Failed to load: {e}")
    
    def save(self):
        """Save learned invariants"""
        data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "trained": self.trained,
            "training_runs": self.training_runs[-200:],  # Keep last 200
            "invariants": self.invariants,
            "total_violations_found": len(self.violations_found),
            "violations_last_10": self.violations_found[-10:]
        }
        
        try:
            with open(self.oracle_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[Oracle] Saved - {len(self.training_runs)} training runs")
        except Exception as e:
            print(f"[Oracle] Failed to save: {e}")
    
    def add_training_run(self, run_data: Dict):
        """Add a successful run to training data"""
        if not run_data.get('success', False):
            return  # Only learn from successful runs
        
        self.training_runs.append({
            "timestamp": datetime.now().isoformat(),
            "duration": run_data.get('duration', 0),
            "actions": run_data.get('actions', []),
            "trajectory": run_data.get('trajectory', [])
        })
        
        # Auto-train when we have enough data
        if len(self.training_runs) >= self.min_training_runs and not self.trained:
            print(f"[Oracle] {len(self.training_runs)} runs collected - training invariants...")
            self.train()
    
    def train(self):
        """Learn invariants from training runs"""
        if len(self.training_runs) < self.min_training_runs:
            print(f"[Oracle] Need {self.min_training_runs} runs, have {len(self.training_runs)}")
            return
        
        print(f"[Oracle] Training on {len(self.training_runs)} successful runs...")
        
        # Learn required fields
        self._learn_required_fields()
        
        # Learn state transitions
        self._learn_state_transitions()
        
        # Learn duration patterns
        self._learn_duration_patterns()
        
        self.trained = True
        print("[Oracle] Training complete - ready to detect anomalies")
    
    def _learn_required_fields(self):
        """Learn which fields are always present"""
        # Track field presence across runs
        field_counts = defaultdict(lambda: defaultdict(int))
        
        for run in self.training_runs:
            # Example: extract from actions
            for action in run.get('actions', []):
                entity = action.get('entity', 'unknown')
                for field in action.get('fields', []):
                    field_counts[entity][field] += 1
        
        # Fields present in >95% of runs are "required"
        threshold = len(self.training_runs) * 0.95
        
        for entity, fields in field_counts.items():
            required = [field for field, count in fields.items() if count >= threshold]
            if required:
                self.invariants['required_fields'][entity] = required
    
    def _learn_state_transitions(self):
        """Learn valid state transition graph"""
        for run in self.training_runs:
            trajectory = run.get('trajectory', [])
            for i in range(len(trajectory) - 1):
                from_state = trajectory[i].get('url', 'unknown')
                to_state = trajectory[i+1].get('url', 'unknown')
                self.invariants['state_transitions'][from_state].add(to_state)
        
        # Convert sets to lists for JSON serialization
        self.invariants['state_transitions'] = {
            k: list(v) for k, v in self.invariants['state_transitions'].items()
        }
    
    def _learn_duration_patterns(self):
        """Learn expected duration ranges (statistical outlier detection)"""
        action_durations = defaultdict(list)
        
        for run in self.training_runs:
            for action in run.get('actions', []):
                action_name = action.get('action', 'unknown')
                duration = action.get('duration', 0)
                if duration > 0:
                    action_durations[action_name].append(duration)
        
        # Calculate mean, std, min, max for each action
        for action, durations in action_durations.items():
            if len(durations) >= 5:  # Need at least 5 samples
                self.invariants['duration_stats'][action] = {
                    "mean": statistics.mean(durations),
                    "std": statistics.stdev(durations) if len(durations) > 1 else 0,
                    "min": min(durations),
                    "max": max(durations),
                    "samples": len(durations)
                }
    
    def validate_run(self, run_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate a run against learned invariants
        
        Returns:
            (is_valid, violations_list)
        """
        if not self.trained:
            return True, []  # Can't validate if not trained
        
        violations = []
        
        # Check required fields
        violations.extend(self._check_required_fields(run_data))
        
        # Check state transitions
        violations.extend(self._check_state_transitions(run_data))
        
        # Check duration outliers
        violations.extend(self._check_duration_outliers(run_data))
        
        # Track violations
        if violations:
            self.violations_found.append({
                "timestamp": datetime.now().isoformat(),
                "run_id": run_data.get('run_id', 'unknown'),
                "violations": violations
            })
        
        return len(violations) == 0, violations
    
    def _check_required_fields(self, run_data: Dict) -> List[str]:
        """Check if required fields are present"""
        violations = []
        
        for action in run_data.get('actions', []):
            entity = action.get('entity', 'unknown')
            required = self.invariants['required_fields'].get(entity, [])
            
            present_fields = set(action.get('fields', []))
            missing = set(required) - present_fields
            
            if missing:
                violations.append(
                    f"INVARIANT VIOLATION: {entity} missing required fields: {missing}"
                )
        
        return violations
    
    def _check_state_transitions(self, run_data: Dict) -> List[str]:
        """Check if state transitions are valid"""
        violations = []
        trajectory = run_data.get('trajectory', [])
        
        for i in range(len(trajectory) - 1):
            from_state = trajectory[i].get('url', 'unknown')
            to_state = trajectory[i+1].get('url', 'unknown')
            
            valid_next_states = self.invariants['state_transitions'].get(from_state, [])
            
            if valid_next_states and to_state not in valid_next_states:
                violations.append(
                    f"INVARIANT VIOLATION: Unexpected transition {from_state} -> {to_state}"
                )
        
        return violations
    
    def _check_duration_outliers(self, run_data: Dict) -> List[str]:
        """Check for statistical outliers in action durations"""
        violations = []
        
        for action in run_data.get('actions', []):
            action_name = action.get('action', 'unknown')
            duration = action.get('duration', 0)
            
            stats = self.invariants['duration_stats'].get(action_name)
            if not stats:
                continue
            
            mean = stats['mean']
            std = stats['std']
            
            # Flag if >3 standard deviations from mean (99.7% outlier)
            if std > 0 and abs(duration - mean) > 3 * std:
                violations.append(
                    f"PERFORMANCE ANOMALY: {action_name} took {duration:.1f}s (expected {mean:.1f}±{std:.1f}s)"
                )
        
        return violations
    
    def get_stats(self) -> Dict:
        """Get oracle statistics"""
        return {
            "trained": self.trained,
            "training_runs": len(self.training_runs),
            "invariants_learned": {
                "required_fields": len(self.invariants['required_fields']),
                "state_transitions": len(self.invariants['state_transitions']),
                "duration_patterns": len(self.invariants['duration_stats'])
            },
            "violations_found": len(self.violations_found),
            "ready": self.trained and len(self.training_runs) >= self.min_training_runs
        }


# Demo
if __name__ == "__main__":
    print("\n" + "="*70)
    print("AUTOMATIC TEST ORACLE - Demo")
    print("="*70 + "\n")
    
    oracle = AutomaticTestOracle()
    
    # Simulate training runs
    for i in range(60):
        oracle.add_training_run({
            "success": True,
            "duration": 120 + i*2,
            "actions": [
                {"entity": "property", "fields": ["name", "uid", "address"], "duration": 30, "action": "create"},
                {"entity": "lead", "fields": ["firstName", "lastName", "email"], "duration": 25, "action": "create"}
            ],
            "trajectory": [
                {"url": "/login"},
                {"url": "/dashboard"},
                {"url": "/properties"}
            ]
        })
    
    # Validate a normal run
    is_valid, violations = oracle.validate_run({
        "run_id": "test_1",
        "success": True,
        "actions": [
            {"entity": "property", "fields": ["name", "uid", "address"], "duration": 32, "action": "create"}
        ],
        "trajectory": [{"url": "/login"}, {"url": "/dashboard"}]
    })
    print(f"Normal run valid: {is_valid}")
    
    # Validate anomalous run
    is_valid, violations = oracle.validate_run({
        "run_id": "test_2",
        "success": True,
        "actions": [
            {"entity": "property", "fields": ["name"], "duration": 150, "action": "create"}  # Missing uid!
        ],
        "trajectory": [{"url": "/login"}, {"url": "/invalid"}]  # Invalid transition!
    })
    print(f"\nAnomalous run valid: {is_valid}")
    if violations:
        print("Violations detected:")
        for v in violations:
            print(f"  - {v}")
    
    # Stats
    print(f"\nOracle stats: {oracle.get_stats()}")
    
    oracle.save()
    print("\n[OK] Demo complete")

