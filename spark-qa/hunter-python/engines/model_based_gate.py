"""
MODEL-BASED RL - Shallow next-state predictor

CONCEPT: Predict what happens before acting
- Model: (current_state, action) → predicted_next_state
- Gate: Skip actions that lead to dead-ends/loops
- Lookahead: 1-2 steps (not full planning - too expensive)

APPROACH (CPU-friendly):
- Simple regressor: (state_features, action) → delta_features
- Features: URL, DOM summary, element counts
- No neural net needed - linear regression or decision tree

BENEFITS:
- Avoid obviously futile actions
- Faster learning (fewer wasted explorations)
- Dead-end avoidance

INTEGRATION:
- SelectorHelper asks: "Will this action lead somewhere useful?"
- Model-Based predicts outcome
- If predicted = dead-end/loop → skip action
- Updates model from observed (s, a, s') transitions

CPU ONLY: Scikit-learn regressors, fast inference (<1ms)
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from collections import defaultdict


class ModelBasedGate:
    """
    Shallow next-state predictor for action gating
    Learns (s,a) → s' dynamics
    """
    
    def __init__(self, model_file: str = "barril!!/model_based_gate.json"):
        self.model_file = Path(model_file)
        self.model_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Transition history: (state, action) -> [observed_next_states]
        self.transitions = defaultdict(list)  # key -> [delta_features]
        
        # Simple model: mean delta per (state, action) pair
        self.mean_deltas = {}  # (state_hash, action) -> mean_delta_features
        
        # Dead-end detection
        self.dead_ends = set()  # States that lead nowhere
        self.loop_states = set()  # States that cause loops
        
        # Stats
        self.total_predictions = 0
        self.total_updates = 0
        self.actions_gated = 0
        
        self._load()
    
    def _load(self):
        """Load model data"""
        if self.model_file.exists():
            try:
                with open(self.model_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.dead_ends = set(data.get('dead_ends', []))
                    self.loop_states = set(data.get('loop_states', []))
                    print(f"[ModelBased] Loaded - {len(self.dead_ends)} dead-ends, {len(self.loop_states)} loop states")
            except Exception as e:
                print(f"[ModelBased] Failed to load: {e}")
    
    def save(self):
        """Save model data"""
        data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "total_predictions": self.total_predictions,
            "total_updates": self.total_updates,
            "actions_gated": self.actions_gated,
            "dead_ends": list(self.dead_ends),
            "loop_states": list(self.loop_states),
            "transition_count": len(self.transitions)
        }
        
        try:
            with open(self.model_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[ModelBased] Saved - {self.actions_gated} actions gated")
        except Exception as e:
            print(f"[ModelBased] Failed to save: {e}")
    
    def add_transition(self, state: str, action: str, next_state: str):
        """
        Record observed transition (s, a, s')
        Updates model
        """
        state_hash = hash(state) % 10000
        key = (state_hash, action)
        
        # Compute delta (simple: different URL = 1, same = 0)
        delta = 1.0 if next_state != state else 0.0
        
        self.transitions[key].append(delta)
        
        # Update mean delta
        self.mean_deltas[key] = np.mean(self.transitions[key])
        
        # Detect dead-ends (action never changes state)
        if len(self.transitions[key]) >= 5:
            avg_delta = np.mean(self.transitions[key])
            if avg_delta < 0.1:  # Rarely changes state
                self.dead_ends.add((state, action))
        
        self.total_updates += 1
    
    def predict_next_state_useful(self, state: str, action: str) -> Tuple[bool, str]:
        """
        Predict if action will lead to useful state
        
        Returns:
            (is_useful, reason)
        """
        self.total_predictions += 1
        
        # Check if dead-end
        if (state, action) in self.dead_ends:
            self.actions_gated += 1
            return False, "dead_end"
        
        # Check if loop state
        state_hash = hash(state) % 10000
        if state_hash in self.loop_states:
            self.actions_gated += 1
            return False, "loop_state"
        
        # Check model prediction
        key = (state_hash, action)
        if key in self.mean_deltas:
            predicted_delta = self.mean_deltas[key]
            
            # If predicted delta very low -> probably not useful
            if predicted_delta < 0.2:
                self.actions_gated += 1
                return False, "low_utility"
        
        # Unknown or seems useful
        return True, "ok"
    
    def mark_loop_state(self, state: str):
        """Mark state as causing loops"""
        state_hash = hash(state) % 10000
        self.loop_states.add(state_hash)
    
    def get_stats(self) -> Dict:
        """Get model statistics"""
        gate_ratio = self.actions_gated / max(self.total_predictions, 1)
        
        return {
            "predictions": self.total_predictions,
            "updates": self.total_updates,
            "actions_gated": self.actions_gated,
            "gate_ratio": round(gate_ratio, 3),
            "dead_ends_known": len(self.dead_ends),
            "loop_states_known": len(self.loop_states)
        }


# Demo
if __name__ == "__main__":
    print("\n" + "="*70)
    print("MODEL-BASED GATE - Demo")
    print("="*70 + "\n")
    
    model = ModelBasedGate()
    
    # Simulate transitions
    # Action 1: Always changes state (useful)
    for i in range(10):
        model.add_transition("/login", "click_login", "/dashboard")
    
    # Action 2: Never changes state (dead-end)
    for i in range(10):
        model.add_transition("/properties", "click_disabled_button", "/properties")
    
    # Predictions
    print("Predictions:")
    useful, reason = model.predict_next_state_useful("/login", "click_login")
    print(f"  click_login: useful={useful}, reason={reason}")
    
    useful, reason = model.predict_next_state_useful("/properties", "click_disabled_button")
    print(f"  click_disabled_button: useful={useful}, reason={reason}")
    
    # Stats
    print(f"\nStats: {model.get_stats()}")
    
    model.save()
    print("\n[OK] Demo complete")

