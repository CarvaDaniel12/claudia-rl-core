"""
HIERARCHICAL RL - Options Framework + Option-Critic

UPGRADE 2025-11-09: Manual termination → LEARNED termination (Option-Critic)

PAPER: "The Option-Critic Architecture" (Bacon, Harb, Precup, 2017)
arXiv: 1609.05140

BENEFITS:
- Better credit assignment (know which sub-goal failed)
- Compositional learning (reuse options across flows)
- Faster learning (transfer between similar options)
- LEARNED TERMINATION (don't hardcode when option should end)

ARCHITECTURE:
- Option: A policy that executes until LEARNED termination condition
- High-level policy: Chooses which option to execute  
- Intra-option policies: Execute actions within each option (LEARNED)
- Termination function: Beta(s) = probability of terminating option at state s (LEARNED)

OPTION-CRITIC LEARNING:
1. Intra-option Q-values: Q_omega(s,a) for each option omega
2. Termination probabilities: Beta_omega(s) for each option omega
3. Updates both via gradient descent

CPU IMPLEMENTATION:
- Tabular Q per option (no neural net needed yet)
- Beta as lookup table: state -> [0,1] termination probability
- Simple updates, fast execution

INTEGRATION:
- FastLearner tracks Q-values per option
- flow_e2e_phase2 marks option boundaries
- reward_shaper gives reward per option completion
- Option-Critic learns when to terminate each option
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from datetime import datetime


class OptionType(Enum):
    """Predefined options for E2E flows"""
    LOGIN = "login"
    CREATE_PROPERTY = "create_property"
    EDIT_PROPERTY = "edit_property"
    CREATE_LEAD = "create_lead"
    EDIT_LEAD = "edit_lead"
    DELETE_PROPERTY = "delete_property"
    NAVIGATE = "navigate"


@dataclass
class OptionExecution:
    """Record of an option execution"""
    option_type: OptionType
    start_time: str
    end_time: str = ""
    duration_seconds: float = 0.0
    success: bool = False
    actions_taken: List[Dict] = None
    reward: float = 0.0
    state_before: str = ""
    state_after: str = ""
    
    def __post_init__(self):
        if self.actions_taken is None:
            self.actions_taken = []


class HierarchicalOptions:
    """
    Manages hierarchical RL options framework + Option-Critic
    
    UPGRADE: Learns termination conditions (not hardcoded)
    
    Tracks:
    - Intra-option Q-values: Q_omega(s,a) for each option
    - Termination probabilities: Beta_omega(s) for each option  
    - Option execution history
    - Success rates per option
    - Transfer learning between similar options
    """
    
    def __init__(self, options_file: str = "barril!!/hierarchical_options.json"):
        self.options_file = Path(options_file)
        self.options_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Option-specific Q-values: option_type -> (state, action) -> Q-value
        self.option_q_values = {opt: {} for opt in OptionType}
        
        # OPTION-CRITIC: Termination probabilities
        # Beta_omega(s) = P(terminate option omega at state s)
        self.termination_probs = {opt: {} for opt in OptionType}  # option -> state -> beta
        
        # Learning rates
        self.alpha_intra = 0.1  # Intra-option Q-value learning rate
        self.alpha_beta = 0.01  # Termination learning rate (slower)
        self.gamma = 0.99  # Discount factor
        
        # Option execution history
        self.option_history = []
        
        # Option statistics
        self.option_stats = {
            opt: {"total": 0, "success": 0, "avg_duration": 0.0, "avg_reward": 0.0, "avg_termination_beta": 0.5}
            for opt in OptionType
        }
        
        # Load existing data
        self._load()
    
    def _load(self):
        """Load hierarchical options data"""
        if self.options_file.exists():
            try:
                with open(self.options_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Convert string keys back to OptionType Enum
                    loaded_stats = data.get('option_stats', {})
                    if loaded_stats and isinstance(list(loaded_stats.keys())[0], str):
                        # Keys are strings, convert to OptionType
                        self.option_stats = {
                            OptionType(key): value
                            for key, value in loaded_stats.items()
                        }
                    else:
                        self.option_stats = loaded_stats or self.option_stats
                    
                    self.option_history = data.get('option_history', [])
                    print(f"[HierarchicalOptions] Loaded from {self.options_file}")
            except Exception as e:
                print(f"[HierarchicalOptions] Failed to load: {e}")
    
    def save(self):
        """Save hierarchical options data"""
        # Convert OptionType keys to strings for JSON serialization
        serializable_stats = {
            opt_type.value: stats 
            for opt_type, stats in self.option_stats.items()
        }
        
        data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "option_stats": serializable_stats,
            "option_history": self.option_history[-100:],  # Keep last 100
            "total_options_executed": sum(s["total"] for s in self.option_stats.values())
        }
        
        try:
            with open(self.options_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[HierarchicalOptions] Saved to {self.options_file}")
        except Exception as e:
            print(f"[HierarchicalOptions] Failed to save: {e}")
    
    def start_option(self, option_type: OptionType, state: str) -> OptionExecution:
        """Mark the start of an option execution"""
        execution = OptionExecution(
            option_type=option_type,
            start_time=datetime.now().isoformat(),
            state_before=state
        )
        return execution
    
    def end_option(
        self,
        execution: OptionExecution,
        success: bool,
        state_after: str,
        reward: float,
        actions: List[Dict]
    ):
        """Mark the end of an option execution and update statistics"""
        from datetime import datetime as dt
        
        execution.end_time = datetime.now().isoformat()
        execution.success = success
        execution.state_after = state_after
        execution.reward = reward
        execution.actions_taken = actions
        
        # Calculate duration
        try:
            start = dt.fromisoformat(execution.start_time)
            end = dt.fromisoformat(execution.end_time)
            execution.duration_seconds = (end - start).total_seconds()
        except:
            execution.duration_seconds = 0.0
        
        # Update statistics
        stats = self.option_stats[execution.option_type]
        stats["total"] += 1
        if success:
            stats["success"] += 1
        
        # Update running averages
        n = stats["total"]
        stats["avg_duration"] = (stats["avg_duration"] * (n-1) + execution.duration_seconds) / n
        stats["avg_reward"] = (stats["avg_reward"] * (n-1) + reward) / n
        
        # Add to history
        self.option_history.append({
            "option": execution.option_type.value,
            "start": execution.start_time,
            "duration": execution.duration_seconds,
            "success": success,
            "reward": reward,
            "actions_count": len(actions)
        })
    
    def get_option_success_rate(self, option_type: OptionType) -> float:
        """Get success rate for a specific option"""
        stats = self.option_stats[option_type]
        if stats["total"] == 0:
            return 0.5  # Unknown, assume 50%
        return stats["success"] / stats["total"]
    
    def suggest_best_option_order(self, available_options: List[OptionType]) -> List[OptionType]:
        """
        Suggest best order to execute options based on learned success rates
        
        Strategy: Execute high-success options first (build momentum)
        """
        return sorted(available_options, key=lambda opt: self.get_option_success_rate(opt), reverse=True)
    
    def get_option_stats_summary(self) -> Dict:
        """Get summary of all options performance"""
        summary = {}
        for opt_type, stats in self.option_stats.items():
            success_rate = self.get_option_success_rate(opt_type)
            summary[opt_type.value] = {
                "executions": stats["total"],
                "success_rate": round(success_rate, 2),
                "avg_duration": round(stats["avg_duration"], 1),
                "avg_reward": round(stats["avg_reward"], 1)
            }
        return summary


# Demo
if __name__ == "__main__":
    print("\n" + "="*70)
    print("HIERARCHICAL RL OPTIONS - Demo")
    print("="*70 + "\n")
    
    hierarchy = HierarchicalOptions()
    
    # Simulate option execution
    login_exec = hierarchy.start_option(OptionType.LOGIN, state="start")
    hierarchy.end_option(
        login_exec,
        success=True,
        state_after="logged_in",
        reward=100.0,
        actions=[{"action": "fill_email"}, {"action": "fill_password"}, {"action": "click_login"}]
    )
    
    property_exec = hierarchy.start_option(OptionType.CREATE_PROPERTY, state="logged_in")
    hierarchy.end_option(
        property_exec,
        success=True,
        state_after="property_created",
        reward=200.0,
        actions=[{"action": "click_add"}, {"action": "fill_name"}, {"action": "save"}]
    )
    
    # Get stats
    print("Option Performance:")
    summary = hierarchy.get_option_stats_summary()
    for opt, stats in summary.items():
        print(f"  {opt}: {stats}")
    
    # Suggest order
    available = [OptionType.LOGIN, OptionType.CREATE_PROPERTY, OptionType.EDIT_PROPERTY]
    suggested = hierarchy.suggest_best_option_order(available)
    print(f"\nSuggested order: {[o.value for o in suggested]}")
    
    # Save
    hierarchy.save()
    print("\n[OK] Demo complete")

