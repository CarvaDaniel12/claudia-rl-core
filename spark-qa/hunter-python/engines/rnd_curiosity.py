"""
RND (Random Network Distillation) - CPU-based intrinsic motivation

PAPER: "Exploration by Random Network Distillation" (Burda et al, 2018)
arXiv: 1810.12894

CONCEPT:
- Target network: Random, frozen (never trained)
- Predictor network: Tries to predict target output
- Intrinsic reward = prediction error (MSE)
- Novel states = high error (predictor never saw it)
- Familiar states = low error (predictor learned it)

BENEFITS vs FIXED CURIOSITY:
- No reward hacking (can't game random target)
- Automatic decay (error naturally decreases)
- Scales better (works on millions of states)

CPU IMPLEMENTATION:
- Small MLP (2 hidden layers, 64 units each)
- NumPy only (no PyTorch needed for simple case)
- Fast forward pass (<1ms)

INTEGRATION:
- reward_shaper calls rnd.calculate_intrinsic_reward(state_features)
- Beta annealing: 0.2 → 0.05 over 200 runs
- Intrinsic added to extrinsic: R_total = R_ext + beta * R_int
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class RNDCuriosity:
    """
    Random Network Distillation for intrinsic motivation
    CPU-only implementation using NumPy
    """
    
    def __init__(self, state_dim: int = 32, rnd_file: str = "barril!!/rnd_curiosity.json"):
        self.state_dim = state_dim
        self.rnd_file = Path(rnd_file)
        self.rnd_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Network architecture (simple MLP)
        self.hidden_dim = 64
        self.output_dim = 32
        
        # Target network (FROZEN - random initialization)
        self.target_w1 = np.random.randn(state_dim, self.hidden_dim) * 0.1
        self.target_b1 = np.zeros(self.hidden_dim)
        self.target_w2 = np.random.randn(self.hidden_dim, self.output_dim) * 0.1
        self.target_b2 = np.zeros(self.output_dim)
        
        # Predictor network (TRAINED - learns to match target)
        self.pred_w1 = np.random.randn(state_dim, self.hidden_dim) * 0.1
        self.pred_b1 = np.zeros(self.hidden_dim)
        self.pred_w2 = np.random.randn(self.hidden_dim, self.output_dim) * 0.1
        self.pred_b2 = np.zeros(self.output_dim)
        
        # Training config
        self.learning_rate = 0.001
        self.beta_start = 0.2  # Intrinsic weight at start
        self.beta_end = 0.05  # Intrinsic weight at end
        self.beta_anneal_runs = 200  # Anneal over 200 runs
        
        # Stats
        self.total_updates = 0
        self.avg_intrinsic_reward = 0.0
        self.current_run = 0
        
        self._load()
    
    def _load(self):
        """Load predictor weights (target stays frozen!)"""
        if self.rnd_file.exists():
            try:
                with open(self.rnd_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Only load predictor (target must stay random!)
                    self.pred_w1 = np.array(data.get('pred_w1', self.pred_w1.tolist()))
                    self.pred_b1 = np.array(data.get('pred_b1', self.pred_b1.tolist()))
                    self.pred_w2 = np.array(data.get('pred_w2', self.pred_w2.tolist()))
                    self.pred_b2 = np.array(data.get('pred_b2', self.pred_b2.tolist()))
                    self.current_run = data.get('current_run', 0)
                    print(f"[RND] Loaded predictor - run {self.current_run}")
            except Exception as e:
                print(f"[RND] Failed to load: {e}")
    
    def save(self):
        """Save predictor weights and stats"""
        data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "current_run": self.current_run,
            "total_updates": self.total_updates,
            "avg_intrinsic_reward": float(self.avg_intrinsic_reward),
            "beta_current": float(self.get_current_beta()),
            "pred_w1": self.pred_w1.tolist(),
            "pred_b1": self.pred_b1.tolist(),
            "pred_w2": self.pred_w2.tolist(),
            "pred_b2": self.pred_b2.tolist()
        }
        
        try:
            with open(self.rnd_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"[RND] Saved - run {self.current_run}, beta={self.get_current_beta():.3f}")
        except Exception as e:
            print(f"[RND] Failed to save: {e}")
    
    def _relu(self, x):
        """ReLU activation"""
        return np.maximum(0, x)
    
    def _forward_target(self, state: np.ndarray) -> np.ndarray:
        """Forward pass through target network (frozen)"""
        h1 = self._relu(state @ self.target_w1 + self.target_b1)
        out = h1 @ self.target_w2 + self.target_b2
        return out
    
    def _forward_predictor(self, state: np.ndarray) -> np.ndarray:
        """Forward pass through predictor network"""
        h1 = self._relu(state @ self.pred_w1 + self.pred_b1)
        out = h1 @ self.pred_w2 + self.pred_b2
        return out
    
    def calculate_intrinsic_reward(self, state_features: np.ndarray) -> float:
        """
        Calculate intrinsic reward = prediction error (MSE)
        
        Args:
            state_features: 1D array of state features (size = state_dim)
            
        Returns:
            Intrinsic reward (normalized MSE)
        """
        if state_features.shape[0] != self.state_dim:
            # Pad or truncate to match state_dim
            if state_features.shape[0] < self.state_dim:
                state_features = np.pad(state_features, (0, self.state_dim - state_features.shape[0]))
            else:
                state_features = state_features[:self.state_dim]
        
        # Normalize state features
        state_features = state_features / (np.linalg.norm(state_features) + 1e-8)
        
        # Target output (frozen, random)
        target_out = self._forward_target(state_features)
        
        # Predictor output
        pred_out = self._forward_predictor(state_features)
        
        # Intrinsic reward = MSE (prediction error)
        mse = np.mean((pred_out - target_out) ** 2)
        
        # Normalize to reasonable range (0-10)
        intrinsic_reward = np.clip(mse * 10, 0, 10)
        
        return float(intrinsic_reward)
    
    def update_predictor(self, state_features: np.ndarray):
        """
        Update predictor to minimize prediction error (gradient descent)
        Simple CPU backprop
        """
        if state_features.shape[0] != self.state_dim:
            if state_features.shape[0] < self.state_dim:
                state_features = np.pad(state_features, (0, self.state_dim - state_features.shape[0]))
            else:
                state_features = state_features[:self.state_dim]
        
        state_features = state_features / (np.linalg.norm(state_features) + 1e-8)
        
        # Forward pass
        h1 = self._relu(state_features @ self.pred_w1 + self.pred_b1)
        pred_out = h1 @ self.pred_w2 + self.pred_b2
        
        # Target (frozen)
        target_out = self._forward_target(state_features)
        
        # Loss = MSE
        error = pred_out - target_out
        loss = np.mean(error ** 2)
        
        # Backprop (simple gradient descent)
        # dL/dw2 = h1^T @ error
        # dL/db2 = error
        grad_w2 = np.outer(h1, error) / len(error)
        grad_b2 = error
        
        # Update weights
        self.pred_w2 -= self.learning_rate * grad_w2
        self.pred_b2 -= self.learning_rate * grad_b2
        
        # Update hidden layer (simplified - just w1)
        grad_h1 = error @ self.pred_w2.T
        grad_h1[h1 <= 0] = 0  # ReLU derivative
        grad_w1 = np.outer(state_features, grad_h1)
        
        self.pred_w1 -= self.learning_rate * grad_w1
        
        self.total_updates += 1
        
        # Update running average
        alpha = 0.01
        self.avg_intrinsic_reward = (1 - alpha) * self.avg_intrinsic_reward + alpha * loss
    
    def get_current_beta(self) -> float:
        """
        Get current intrinsic weight (anneals from 0.2 to 0.05)
        
        Returns:
            Beta coefficient for intrinsic reward
        """
        progress = min(1.0, self.current_run / self.beta_anneal_runs)
        beta = self.beta_start + (self.beta_end - self.beta_start) * progress
        return beta
    
    def increment_run(self):
        """Increment run counter (for beta annealing)"""
        self.current_run += 1
    
    def get_stats(self) -> Dict:
        """Get RND statistics"""
        return {
            "current_run": self.current_run,
            "total_updates": self.total_updates,
            "avg_intrinsic_reward": round(self.avg_intrinsic_reward, 3),
            "beta_current": round(self.get_current_beta(), 3),
            "beta_start": self.beta_start,
            "beta_end": self.beta_end
        }


# Demo
if __name__ == "__main__":
    print("\n" + "="*70)
    print("RND CURIOSITY - Demo")
    print("="*70 + "\n")
    
    rnd = RNDCuriosity(state_dim=32)
    
    # Simulate state features
    print("Testing intrinsic rewards:")
    
    # State 1: Novel
    state1 = np.random.randn(32)
    intrinsic1 = rnd.calculate_intrinsic_reward(state1)
    print(f"  Novel state: {intrinsic1:.3f}")
    
    # Train predictor on state1
    for _ in range(10):
        rnd.update_predictor(state1)
    
    # State 1 again: Should be lower (learned)
    intrinsic1_after = rnd.calculate_intrinsic_reward(state1)
    print(f"  Same state after training: {intrinsic1_after:.3f} (should be lower)")
    
    # State 2: Novel (different)
    state2 = np.random.randn(32) * 2
    intrinsic2 = rnd.calculate_intrinsic_reward(state2)
    print(f"  Novel state 2: {intrinsic2:.3f} (should be high)")
    
    # Beta annealing
    print("\nBeta annealing:")
    for run in [0, 50, 100, 150, 200]:
        rnd.current_run = run
        print(f"  Run {run}: beta={rnd.get_current_beta():.3f}")
    
    # Stats
    print(f"\nStats: {rnd.get_stats()}")
    
    rnd.save()
    print("\n[OK] Demo complete")

