#!/usr/bin/env python3
"""
REWARD SHAPER - RL Atomic Loop
Implementa seu sistema de 4 tiers + extensões

BASEADO EM: knowledge-machine/reward_orchestrator.py AdaptiveRewardCalculator
CUSTOMIZADO PARA: Seu especificação de rewards

TIERS (Seu sistema):
1. Baseline: Completou golden path = 100 pontos
2. Exploration Penalty: Mesmo path repetido = -10% por repetição
3. Velocity Bonus: Mais rápido = +20-100 pontos
4. Shortcuts: Com atalhos = +75-150 pontos
5. Recovery Patterns: Atalho + self-healing + rápido = +250 pontos (JACKPOT!)

TIERS (Refinamento):
- Refinement Bonus: 3+ runs consistentes com reward alto = +50
- Exploration Bonus: Caminho novo que completou = +100 + novidade

PLAYWRIGHT KNOWLEDGE INTEGRATION:
- Carrega 475+ selectors validados pelo Playwright
- Valida se selectors usados estão no conhecimento do Playwright
- Bonus: Usar selectors testados = +10 pontos por selector
- Penalidade: Usar selector desconhecido = -5 pontos
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict
from datetime import datetime


class RewardShaper:
    """
    Calcula reward com seu sistema de 4 tiers + refinamentos
    Compatível com AdaptiveRewardCalculator existente
    """

    def __init__(self):
        self.phase = 1
        self.total_runs = 0
        self.best_time = None  # Baseline para comparação
        self.run_history = []  # Últimas N runs para detectar padrões
        self.max_history = 100

        # Playwright knowledge integration
        self.playwright_knowledge = self._load_playwright_knowledge()
        self.playwright_selectors = set(self.playwright_knowledge.get('selectors', []))
        self.playwright_test_ids = set(self.playwright_knowledge.get('test_ids', []))
        
        # Visual state learner integration for loop detection
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / 'engines'))
            from visual_state_learner import VisualStateLearner
            self.visual_learner = VisualStateLearner()
        except:
            self.visual_learner = None
        
        # CURIOSITY-DRIVEN EXPLORATION (OLD - being replaced by RND)
        # Tracks visited states to give intrinsic motivation for discovering new ones
        self.visited_states = set()  # State hashes
        self.state_visit_counts = {}  # State -> count
        self.curiosity_bonus_base = 50.0  # Base reward for discovering new state
        
        # RND INTRINSIC MOTIVATION (NEW - replaces fixed curiosity)
        # Random Network Distillation for better exploration
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / 'engines'))
            from rnd_curiosity import RNDCuriosity
            self.rnd = RNDCuriosity(state_dim=32)
            self.use_rnd = True
            print("[RewardShaper] RND curiosity enabled - beta={0:.3f}".format(self.rnd.get_current_beta()))
        except Exception as e:
            print(f"[RewardShaper] RND not available: {e}")
            self.rnd = None
            self.use_rnd = False

    def _load_playwright_knowledge(self) -> Dict:
        """Carrega playwright_knowledge.json do barril"""
        # Tenta em múltiplos paths
        paths = [
            Path("../../barril!!/playwright_knowledge.json"),
            Path("../barril!!/playwright_knowledge.json"),
            Path("barril!!/playwright_knowledge.json"),
        ]

        for path in paths:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8-sig') as f:
                        data = json.load(f)
                        return data
                except Exception:
                    pass

        return {"selectors": [], "test_ids": []}

    def set_phase(self, total_runs: int):
        """Auto-detect learning phase (compatível com AdaptiveRewardCalculator)"""
        self.total_runs = total_runs
        if total_runs < 50:
            self.phase = 1
        elif total_runs < 150:
            self.phase = 2
        else:
            self.phase = 3

    def calculate(self, run_data: dict) -> float:
        """
        Calcula reward total para um run

        Args:
            run_data: {
                'success': bool,
                'duration': float (segundos),
                'trajectory': list (sequence de states/actions),
                'shortcuts_used': list,
                'recovery_strategies_used': list,
                'exploration_paths': int,
                'is_new_path': bool,
                'loops': int,
                'error_type': str or None
            }

        Returns:
            float: Total reward
        """
        base = 0

        # ========== TIER 1: BASELINE ==========
        if not run_data.get('success', False):
            # Falhou - penalidade severa
            return -100.0

        # Completou golden path
        base = 100.0

        # ========== TIER 2: EXPLORATION PENALTY ==========
        # Se repetir mesmo path, penalidade crescente
        same_path_count = self._count_same_path_repetitions(run_data)
        if same_path_count > 1:
            exploration_penalty = -10 * (same_path_count - 1)
            base += exploration_penalty

        # ========== TIER 3: VELOCITY BONUS ==========
        velocity_bonus = self._calculate_velocity_bonus(run_data)
        base += velocity_bonus

        # ========== TIER 4: SHORTCUTS & RECOVERY ==========
        shortcuts_reward = self._calculate_shortcuts_reward(run_data)
        base += shortcuts_reward

        recovery_reward = self._calculate_recovery_reward(run_data)
        base += recovery_reward

        # ========== BONUS: REFINEMENT ==========
        refinement_bonus = self._calculate_refinement_bonus(run_data)
        base += refinement_bonus

        # ========== BONUS: EXPLORATION ==========
        exploration_bonus = self._calculate_exploration_bonus(run_data)
        base += exploration_bonus
        
        # ========== CURIOSITY REWARD ==========
        # RND (preferred) or fallback to fixed curiosity
        if self.use_rnd and self.rnd:
            curiosity_reward = self._calculate_rnd_curiosity(run_data)
        else:
            curiosity_reward = self._calculate_curiosity_reward(run_data)
        base += curiosity_reward

        # ========== LOOP PENALTY ==========
        loops = run_data.get('loops', 0)
        loop_penalty = max(loops - 1, 0) * (-20)
        base += loop_penalty
        
        # ========== VISUAL LOOP DETECTION (NEW) ==========
        # Uses screenshot-based loop detection (VisualStateLearner)
        # Low penalty (-5) since system in closed circuit for now
        if self.visual_learner and run_data.get('screenshots'):
            visual_loop_detected = self._detect_visual_loops(run_data)
            if visual_loop_detected:
                base += -5  # LOW penalty - will increase when system explores more
        
        # ========== PLAYWRIGHT VALIDATION BONUS ==========
        playwright_bonus = self._calculate_playwright_bonus(run_data)
        base += playwright_bonus

        # ========== PHASE-AWARE SCALING ==========
        if self.phase == 2:
            base *= 0.85  # Mais rigoroso
        elif self.phase == 3:
            base *= 0.70  # Muito rigoroso (só aceita top runs)

        return float(base)

    def _count_same_path_repetitions(self, run_data: dict) -> int:
        """Conta quantas vezes o mesmo path foi repetido recentemente"""
        trajectory_hash = self._hash_trajectory(run_data.get('trajectory', []))

        count = 0
        for hist_run in reversed(self.run_history[-10:]):
            if self._hash_trajectory(hist_run.get('trajectory', [])) == trajectory_hash:
                count += 1
            else:
                break

        return count

    def _hash_trajectory(self, trajectory: list) -> str:
        """Hash simples de trajectory para comparação"""
        if not trajectory:
            return ""
        # Simplificado: hash dos 10 primeiros steps
        steps = str([step.get('action') for step in trajectory[:10]])
        return str(hash(steps))

    def _calculate_velocity_bonus(self, run_data: dict) -> float:
        """
        Seu tier 3: Mais rápido = +20-100 pontos

        Baseline esperado: ~45 segundos (golden path completo)
        """
        duration = run_data.get('duration', 45)

        # Atualizar best_time
        if self.best_time is None or duration < self.best_time:
            self.best_time = duration

        if duration < 40:
            return 100.0  # Super rápido! (+20% vs baseline)
        elif duration < 45:
            return 75.0  # Muito rápido
        elif duration < 50:
            return 50.0  # Rápido
        elif duration < 60:
            return 20.0  # Um pouco mais rápido
        else:
            return 0.0  # Baseline, sem bonus

    def _calculate_shortcuts_reward(self, run_data: dict) -> float:
        """
        Seu tier 4a: Atalhos descobertos = +75-150 pontos

        Shortcuts sem recovery = +75
        Shortcuts com sucesso consistente = +150
        """
        shortcuts = run_data.get('shortcuts_used', [])

        if not shortcuts:
            return 0.0

        base_shortcut_reward = len(shortcuts) * 75

        # Se foi bem-sucedido, double reward
        if run_data.get('success', False):
            return base_shortcut_reward * 1.5  # +112.5-150

        return base_shortcut_reward

    def _calculate_recovery_reward(self, run_data: dict) -> float:
        """
        Seu tier 4b: JACKPOT! Recovery patterns = +250 pontos

        Critério: Atalho + Self-healing + Mais rápido
        Recompensa: +250 (máximo!)
        """
        shortcuts = run_data.get('shortcuts_used', [])
        recovery = run_data.get('recovery_strategies_used', [])
        duration = run_data.get('duration', 999)

        # Precisa ter AMBOS: atalho E recovery
        if not shortcuts or not recovery:
            return 0.0

        # E precisa ser rápido
        if duration > 50:
            return 0.0

        # JACKPOT!
        return 250.0

    def _calculate_refinement_bonus(self, run_data: dict) -> float:
        """
        Bonus refinement: 3+ runs consistentes = +50 pontos

        Detecta se reward tá consistente (não flutuando)
        """
        if len(self.run_history) < 3:
            return 0.0

        recent_rewards = [r.get('calculated_reward', 0) for r in self.run_history[-3:]]

        # Se últimas 3 runs tiveram reward similar e alto
        avg_recent = sum(recent_rewards) / len(recent_rewards)
        if avg_recent > 150:  # Runs boas
            variance = sum((r - avg_recent) ** 2 for r in recent_rewards) / len(recent_rewards)
            if variance < 1000:  # Consistente
                return 50.0

        return 0.0

    def _calculate_exploration_bonus(self, run_data: dict) -> float:
        """
        Bonus exploration: Caminho novo que completou = +100

        is_new_path = True = +100
        """
        if run_data.get('is_new_path', False):
            return 100.0

        return 0.0

    def _calculate_playwright_bonus(self, run_data: dict) -> float:
        """
        Bonus Playwright validation:
        - Selector testado pelo Playwright = +10 pontos
        - Test ID validado = +5 pontos
        - Selector desconhecido = -5 pontos (não está em playwright_knowledge.json)

        Args:
            run_data pode ter:
            - 'selectors_used': list de CSS/XPath selectors usados
            - 'test_ids_used': list de test IDs usados
        """
        bonus = 0

        # Valida selectors
        selectors_used = run_data.get('selectors_used', [])
        for selector in selectors_used:
            if selector in self.playwright_selectors:
                bonus += 10  # Selector validado pelo Playwright
            else:
                bonus -= 5   # Selector novo/desconhecido

        # Valida test IDs
        test_ids_used = run_data.get('test_ids_used', [])
        for test_id in test_ids_used:
            if test_id in self.playwright_test_ids:
                bonus += 5   # Test ID validado
            else:
                bonus -= 2   # Test ID desconhecido

        return float(bonus)

    def save_run(self, run_data: dict, reward: float):
        """Salva run no histórico para cálculos futuros"""
        run_data['calculated_reward'] = reward
        run_data['timestamp'] = datetime.now().isoformat()

        self.run_history.append(run_data)

        # Limita tamanho
        if len(self.run_history) > self.max_history:
            self.run_history = self.run_history[-self.max_history:]

    def export_metrics(self) -> dict:
        """Export métricas pro próximo ciclo"""
        if not self.run_history:
            return {}

        rewards = [r.get('calculated_reward', 0) for r in self.run_history]

        return {
            'total_runs': len(self.run_history),
            'avg_reward': sum(rewards) / len(rewards),
            'max_reward': max(rewards),
            'min_reward': min(rewards),
            'best_time': self.best_time,
            'phase': self.phase
        }


    def _calculate_rnd_curiosity(self, run_data: dict) -> float:
        """
        RND (Random Network Distillation) intrinsic motivation
        Replaces fixed curiosity with learned prediction error
        
        Advantages:
        - No reward hacking (can't game random target)
        - Automatic decay (familiar states = low error)
        - Beta annealing (0.2 -> 0.05 over 200 runs)
        """
        trajectory = run_data.get('trajectory', [])
        if not trajectory:
            return 0.0
        
        # Build state features from trajectory
        # Simple encoding: [url_hash, action_count, duration, success_flag, ...]
        state_features = self._encode_state_for_rnd(run_data)
        
        # Calculate intrinsic reward
        intrinsic_raw = self.rnd.calculate_intrinsic_reward(state_features)
        
        # Apply beta annealing
        beta = self.rnd.get_current_beta()
        intrinsic_reward = beta * intrinsic_raw
        
        # Update RND predictor (learns to predict target)
        self.rnd.update_predictor(state_features)
        
        # Increment run counter for beta annealing
        self.rnd.increment_run()
        
        return intrinsic_reward
    
    def _encode_state_for_rnd(self, run_data: dict) -> np.ndarray:
        """
        Encode run state into feature vector for RND
        
        Returns 32-dim feature vector
        """
        features = []
        
        # URL hash (normalized)
        trajectory = run_data.get('trajectory', [])
        if trajectory:
            url = trajectory[-1].get('url', '')
            url_hash = hash(url) % 10000 / 10000.0
        else:
            url_hash = 0.0
        features.append(url_hash)
        
        # Action count (normalized by max 100)
        action_count = len(run_data.get('actions', []))
        features.append(min(action_count / 100.0, 1.0))
        
        # Duration (normalized by max 300s)
        duration = run_data.get('duration', 0)
        features.append(min(duration / 300.0, 1.0))
        
        # Success flag
        features.append(1.0 if run_data.get('success', False) else 0.0)
        
        # Trajectory diversity (unique URLs)
        unique_urls = len(set(step.get('url', '') for step in trajectory))
        features.append(min(unique_urls / 20.0, 1.0))
        
        # Shortcuts used
        shortcuts = len(run_data.get('shortcuts_used', []))
        features.append(min(shortcuts / 10.0, 1.0))
        
        # Recovery used
        recovery = len(run_data.get('recovery_strategies_used', []))
        features.append(min(recovery / 5.0, 1.0))
        
        # Pad to 32 dimensions
        while len(features) < 32:
            features.append(0.0)
        
        return np.array(features[:32], dtype=np.float32)
    
    def _calculate_curiosity_reward(self, run_data: dict) -> float:
        """
        Curiosity-Driven Exploration: Intrinsic reward for discovering new states
        
        Algorithm:
        1. Hash the trajectory/state sequence
        2. If never seen: +50 base reward, decreasing with repeated visits
        3. Formula: reward = base / sqrt(visit_count + 1)
        
        This encourages agent to explore new paths, essential for bug finding
        """
        # Build state representation from trajectory
        trajectory = run_data.get('trajectory', [])
        if not trajectory:
            return 0.0
        
        # Create state hash from trajectory sequence
        state_sequence = "_".join([
            f"{step.get('action', '')}@{step.get('url', '')}"
            for step in trajectory
        ])
        state_hash = hash(state_sequence) % (2**31)  # Positive hash
        
        # Count visits
        visit_count = self.state_visit_counts.get(state_hash, 0)
        self.state_visit_counts[state_hash] = visit_count + 1
        
        # Calculate curiosity reward (decreases with repeated visits)
        import math
        curiosity_reward = self.curiosity_bonus_base / math.sqrt(visit_count + 1)
        
        # Track if this is a completely new state
        if state_hash not in self.visited_states:
            self.visited_states.add(state_hash)
            # Extra bonus for first-time discovery
            curiosity_reward += 25.0
        
        return curiosity_reward

    def _detect_visual_loops(self, run_data: dict) -> bool:
        """
        Detect loops using screenshot-based visual state learning
        
        Args:
            run_data: Run data with 'screenshots' list of screenshot paths/bytes
            
        Returns:
            bool: True if visual loop detected
        """
        if not self.visual_learner:
            return False
        
        screenshots = run_data.get('screenshots', [])
        if len(screenshots) < 3:
            # Need at least 3 screenshots to detect loops
            return False
        
        # Analyze screenshots for visual loops
        # detect_loop() returns True if same visual state appears multiple times
        try:
            loop_detected = self.visual_learner.detect_loop(screenshots[-1])
            return loop_detected
        except Exception as e:
            # If visual detection fails, don't penalize
            print(f"   [WARN] Visual loop detection failed: {e}")
            return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print("REWARD SHAPER - Test & Demo")
    print("="*80 + "\n")

    shaper = RewardShaper()

    # Test cases
    test_cases = [
        {
            "name": "Baseline (golden path, normal speed)",
            "data": {
                'success': True,
                'duration': 48,
                'trajectory': [{'action': 'login'}, {'action': 'create_property'}],
                'shortcuts_used': [],
                'recovery_strategies_used': [],
                'exploration_paths': 0,
                'is_new_path': False,
                'loops': 0
            }
        },
        {
            "name": "Velocity (super rápido)",
            "data": {
                'success': True,
                'duration': 38,
                'trajectory': [{'action': 'login'}, {'action': 'create_property'}],
                'shortcuts_used': [],
                'recovery_strategies_used': [],
                'exploration_paths': 0,
                'is_new_path': False,
                'loops': 0
            }
        },
        {
            "name": "Shortcuts (1 atalho descoberto)",
            "data": {
                'success': True,
                'duration': 45,
                'trajectory': [{'action': 'login'}, {'action': 'property_shortcut'}],
                'shortcuts_used': ['property_shortcut'],
                'recovery_strategies_used': [],
                'exploration_paths': 0,
                'is_new_path': False,
                'loops': 0
            }
        },
        {
            "name": "JACKPOT! (Atalho + Recovery + Rápido)",
            "data": {
                'success': True,
                'duration': 42,
                'trajectory': [{'action': 'login'}, {'action': 'shortcut'}, {'action': 'recovery'}],
                'shortcuts_used': ['shortcut'],
                'recovery_strategies_used': ['self_healing_v1'],
                'exploration_paths': 0,
                'is_new_path': False,
                'loops': 0
            }
        },
        {
            "name": "Failed (não completou)",
            "data": {
                'success': False,
                'duration': 30,
                'trajectory': [{'action': 'login'}, {'action': 'error'}],
                'shortcuts_used': [],
                'recovery_strategies_used': [],
                'exploration_paths': 0,
                'is_new_path': False,
                'loops': 0
            }
        }
    ]

    for test in test_cases:
        reward = shaper.calculate(test['data'])
        shaper.save_run(test['data'], reward)
        print(f"[OK] {test['name']:<45} Reward: {reward:+.0f}")

    print("\n" + "="*80)
    print("METRICS EXPORT")
    print("="*80)
    metrics = shaper.export_metrics()
    print(json.dumps(metrics, indent=2))
    print("\n")
