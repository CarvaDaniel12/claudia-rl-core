#!/usr/bin/env python3
"""
[CHART] RL METRICS LOGGER - Loga métricas críticas do RL (Andy Jones best practices)

PROBLEMA IDENTIFICADO:
- ZERO metrics sendo logadas
- Não sabemos se RL está aprendendo
- Não sabemos se policy colapsou
- Não sabemos se experiences estão stale

MÉTRICAS CRÍTICAS (Andy Jones):
1. Policy Entropy: Exploração (deve cair mas não a zero)
2. KL Divergence: Experience staleness (deve ser pequeno mas positivo)
3. Residual Variance: Value learning (deve cair rápido)
4. Advantage Distribution: MUST be mean-zero
5. Sample Staleness: Freshness das experiences (deve ser estável)

RED FLAGS AUTOMÁTICOS:
- Policy Entropy < 0.1: COLLAPSED POLICY (sem exploração)
- Policy Entropy = 1.0: NOT LEARNING (random policy)
- KL Divergence > 0.5: STALE EXPERIENCES (feeding old data)
- KL Divergence < 0: CALCULATION BUG
- Residual Variance = 1.0: VALUE NOT LEARNING
- Advantage Mean ≠ 0: BROKEN ADVANTAGE CALCULATION
- Sample Staleness crescendo: FEEDING OLDER AND OLDER DATA

REFERÊNCIA: Andy Jones - "The single most common issue for newbies"
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class RLMetricsLogger:
    """
    Loga métricas críticas do RL para detectar bugs

    Usage:
        logger = RLMetricsLogger()

        # Durante training:
        logger.log_cycle(
            cycle_id=1,
            actions=actions_taken,
            rewards=rewards_received,
            experiences=experiences_used,
            values=value_predictions
        )

        # Check red flags:
        logger.check_red_flags()
    """

    def __init__(self, log_dir: Optional[Path] = None):
        """
        Args:
            log_dir: Directory para salvar logs (default: barril!!/metrics/)
        """
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / "barril!!" / "metrics"

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.metrics_history = []
        self.red_flags = []

    def log_cycle(
        self,
        cycle_id: int,
        actions: List[str],
        rewards: List[float],
        experiences: List[Dict],
        values: Optional[List[float]] = None
    ) -> Dict:
        """
        Loga métricas de um ciclo de training

        Args:
            cycle_id: ID do ciclo
            actions: Actions tomadas
            rewards: Rewards recebidos
            experiences: Experiences usadas
            values: Value predictions (opcional, pra calcular residual variance)

        Returns:
            metrics: Dict com todas as métricas calculadas
        """
        print(f"\n[CHART] Logging RL metrics for cycle {cycle_id}...")

        metrics = {
            'cycle_id': cycle_id,
            'timestamp': datetime.now().isoformat(),
            'policy_entropy': self._calc_policy_entropy(actions),
            'kl_divergence': self._calc_kl_divergence(experiences),
            'residual_variance': self._calc_residual_variance(rewards, values),
            'advantage_mean': self._calc_advantage_mean(rewards, values),
            'advantage_std': self._calc_advantage_std(rewards, values),
            'sample_staleness': self._calc_sample_staleness(experiences),
            'reward_stats': self._calc_reward_stats(rewards),
            'red_flags': []
        }

        # Check red flags
        flags = self._check_red_flags(metrics)
        metrics['red_flags'] = flags

        # Save to history
        self.metrics_history.append(metrics)
        self.red_flags.extend(flags)

        # Print summary
        self._print_metrics(metrics)

        # Save to disk
        self._save_metrics(cycle_id, metrics)

        return metrics

    def _calc_policy_entropy(self, actions: List[str]) -> float:
        """
        Calcula policy entropy (exploração)

        Entropy = -Σ p(a) * log(p(a))

        HIGH ENTROPY (~1.0): Policy aleatória (explorando tudo)
        LOW ENTROPY (~0.0): Policy determinística (exploitando)
        COLLAPSED (~0.0 muito cedo): Policy colapsou (bug!)

        Referência: Andy Jones - "Should start ~1, fall rapidly, stabilize >0"
        """
        if not actions:
            return 0.0

        # Count action frequencies
        action_counts = defaultdict(int)
        for action in actions:
            action_counts[action] += 1

        # Calculate probabilities
        total = len(actions)
        probs = [count / total for count in action_counts.values()]

        # Calculate entropy
        entropy = -sum(p * np.log(p + 1e-10) for p in probs)

        # Normalize by max entropy (log of num actions)
        max_entropy = np.log(len(action_counts))
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0

        return round(normalized_entropy, 4)

    def _calc_kl_divergence(self, experiences: List[Dict]) -> float:
        """
        Calcula KL divergence (experience staleness)

        KL(old||new) mede o quão diferentes são as experiences antigas das novas

        SMALL BUT POSITIVE (0.01-0.1): Good! Experiences are fresh
        LARGE (>0.5): Stale! Feeding old data to learner
        NEGATIVE: Bug! Calculation error

        Referência: Andy Jones - "Should be small but positive"

        Simplificação: Usamos age distribution como proxy
        """
        if len(experiences) < 2:
            return 0.0

        now = datetime.now()
        ages = []

        for exp in experiences:
            timestamp_str = exp.get('timestamp', '')
            if timestamp_str:
                try:
                    exp_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if exp_time.tzinfo:
                        exp_time = exp_time.replace(tzinfo=None)
                    age_hours = (now - exp_time).total_seconds() / 3600
                    ages.append(age_hours)
                except:
                    pass

        if not ages:
            return 0.0

        # KL proxy: variance of ages (high variance = mixing old and new)
        mean_age = np.mean(ages)
        std_age = np.std(ages)

        # Normalize: KL proxy = std / (mean + 1)
        kl_proxy = std_age / (mean_age + 1)

        return round(kl_proxy, 4)

    def _calc_residual_variance(
        self,
        rewards: List[float],
        values: Optional[List[float]]
    ) -> float:
        """
        Calcula residual variance (value learning progress)

        Residual Variance = Var(targets - values) / Var(targets)

        STARTS AT ~1.0: Value network random (não aprendeu nada)
        FALLS RAPIDLY: Value learning está funcionando
        STAYS AT ~1.0: Value network NOT learning (bug!)

        Referência: Andy Jones - "Should start ~1, fall rapidly"
        """
        if not rewards or values is None or len(values) != len(rewards):
            return 1.0  # Assume not learning se não temos values

        rewards_arr = np.array(rewards)
        values_arr = np.array(values)

        # Calculate residuals (targets - predictions)
        residuals = rewards_arr - values_arr

        # Calculate variances
        var_residuals = np.var(residuals)
        var_targets = np.var(rewards_arr)

        if var_targets == 0:
            return 1.0

        residual_var = var_residuals / var_targets

        return round(residual_var, 4)

    def _calc_advantage_mean(
        self,
        rewards: List[float],
        values: Optional[List[float]]
    ) -> float:
        """
        Calcula mean de advantages

        Advantage = Q(s,a) - V(s) ≈ reward - value

        MUST BE ZERO: Se não for, advantage calculation está quebrada!

        Referência: Andy Jones - "Advantages must be mean-zero"
        """
        if not rewards or values is None or len(values) != len(rewards):
            return 0.0

        advantages = np.array(rewards) - np.array(values)
        return round(np.mean(advantages), 4)

    def _calc_advantage_std(
        self,
        rewards: List[float],
        values: Optional[List[float]]
    ) -> float:
        """Calcula std de advantages (para normalização)"""
        if not rewards or values is None or len(values) != len(rewards):
            return 1.0

        advantages = np.array(rewards) - np.array(values)
        return round(np.std(advantages), 4)

    def _calc_sample_staleness(self, experiences: List[Dict]) -> float:
        """
        Calcula sample staleness (age médio das experiences)

        STABLE: Age médio não muda muito (good!)
        GROWING: Age médio aumentando (feeding older and older data - bad!)

        Referência: Andy Jones - "Sample staleness should be stable"
        """
        if not experiences:
            return 0.0

        now = datetime.now()
        ages = []

        for exp in experiences:
            timestamp_str = exp.get('timestamp', '')
            if timestamp_str:
                try:
                    exp_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if exp_time.tzinfo:
                        exp_time = exp_time.replace(tzinfo=None)
                    age_hours = (now - exp_time).total_seconds() / 3600
                    ages.append(age_hours)
                except:
                    pass

        if not ages:
            return 0.0

        return round(np.mean(ages), 2)

    def _calc_reward_stats(self, rewards: List[float]) -> Dict:
        """Calcula stats de rewards (para validar escala)"""
        if not rewards:
            return {'min': 0, 'max': 0, 'mean': 0, 'std': 0}

        return {
            'min': round(float(np.min(rewards)), 2),
            'max': round(float(np.max(rewards)), 2),
            'mean': round(float(np.mean(rewards)), 2),
            'std': round(float(np.std(rewards)), 2)
        }

    def _check_red_flags(self, metrics: Dict) -> List[str]:
        """
        Check red flags automáticos

        Returns:
            List of red flag messages
        """
        flags = []

        # 1. Policy Entropy
        entropy = metrics['policy_entropy']
        if entropy < 0.1:
            flags.append(f"[RED] COLLAPSED POLICY! Entropy={entropy:.3f} (should be >0.1)")
        elif entropy > 0.95:
            flags.append(f"[YELLOW] NOT LEARNING! Entropy={entropy:.3f} (still random)")

        # 2. KL Divergence
        kl = metrics['kl_divergence']
        if kl > 0.5:
            flags.append(f"[RED] STALE EXPERIENCES! KL={kl:.3f} (should be <0.5)")
        elif kl < 0:
            flags.append(f"[RED] CALCULATION BUG! KL={kl:.3f} (should be >=0)")

        # 3. Residual Variance
        res_var = metrics['residual_variance']
        cycle_id = metrics['cycle_id']
        if res_var > 0.9 and cycle_id > 5:
            flags.append(f"[RED] VALUE NOT LEARNING! Residual Var={res_var:.3f} after {cycle_id} cycles")

        # 4. Advantage Mean
        adv_mean = metrics['advantage_mean']
        if abs(adv_mean) > 0.1:
            flags.append(f"[RED] BROKEN ADVANTAGES! Mean={adv_mean:.3f} (should be ~0)")

        # 5. Sample Staleness
        staleness = metrics['sample_staleness']
        if staleness > 24:
            flags.append(f"[YELLOW] OLD EXPERIENCES! Avg age={staleness:.1f}h (should be <24h)")

        # 6. Reward Scale
        reward_stats = metrics['reward_stats']
        if reward_stats['max'] > 100 or reward_stats['min'] < -100:
            flags.append(f"[YELLOW] REWARD SCALE! Range=[{reward_stats['min']}, {reward_stats['max']}] (should be [-10, +10])")

        return flags

    def _print_metrics(self, metrics: Dict):
        """Print metrics summary"""
        print(f"\n  Policy Entropy: {metrics['policy_entropy']:.3f}")
        print(f"  KL Divergence: {metrics['kl_divergence']:.3f}")
        print(f"  Residual Variance: {metrics['residual_variance']:.3f}")
        print(f"  Advantage Mean: {metrics['advantage_mean']:.3f} (±{metrics['advantage_std']:.3f})")
        print(f"  Sample Staleness: {metrics['sample_staleness']:.1f}h")
        print(f"  Reward Range: [{metrics['reward_stats']['min']}, {metrics['reward_stats']['max']}]")

        if metrics['red_flags']:
            print(f"\n  [WARNING]  RED FLAGS:")
            for flag in metrics['red_flags']:
                print(f"     {flag}")

    def _save_metrics(self, cycle_id: int, metrics: Dict):
        """Save metrics to disk"""
        filename = f"metrics_cycle_{cycle_id:04d}.json"
        filepath = self.log_dir / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2)
            print(f"\n  [SAVE] Metrics saved: {filepath.name}")
        except Exception as e:
            print(f"\n  [FAIL] Error saving metrics: {e}")

    def get_metrics_summary(self) -> Dict:
        """Get summary of all logged metrics"""
        if not self.metrics_history:
            return {'total_cycles': 0}

        return {
            'total_cycles': len(self.metrics_history),
            'total_red_flags': len(self.red_flags),
            'latest_metrics': self.metrics_history[-1],
            'all_red_flags': self.red_flags
        }


# ============================================================================
# DEMO & TEST
# ============================================================================

def demo():
    """Demo de RL metrics logging"""
    print("[CHART] RL METRICS LOGGER DEMO\n")

    logger = RLMetricsLogger()

    # Simulate 3 cycles with different behaviors

    # Cycle 1: Random policy (high entropy)
    print("\n" + "="*70)
    print("Cycle 1: Random policy (explorando tudo)")
    print("="*70)
    actions = ['login', 'navigate', 'logout', 'login', 'refresh']  # Muito variado
    rewards = [10, 20, 5, 15, 12]
    values = [8, 18, 7, 14, 11]  # Close to rewards (learning)
    experiences = [
        {'timestamp': datetime.now().isoformat()},
        {'timestamp': datetime.now().isoformat()},
    ]

    logger.log_cycle(1, actions, rewards, experiences, values)

    # Cycle 2: Learning policy (medium entropy)
    print("\n" + "="*70)
    print("Cycle 2: Policy learning (começando a convergir)")
    print("="*70)
    actions = ['login', 'navigate', 'login', 'navigate', 'login']  # Menos variado
    rewards = [25, 30, 28, 32, 27]
    values = [24, 29, 27, 31, 26]  # Very close (good learning!)
    experiences = [
        {'timestamp': datetime.now().isoformat()},
        {'timestamp': datetime.now().isoformat()},
    ]

    logger.log_cycle(2, actions, rewards, experiences, values)

    # Cycle 3: Collapsed policy (RED FLAG!)
    print("\n" + "="*70)
    print("Cycle 3: Collapsed policy (RED FLAG!)")
    print("="*70)
    actions = ['login', 'login', 'login', 'login', 'login']  # Sempre o mesmo!
    rewards = [30, 30, 30, 30, 30]
    values = [10, 10, 10, 10, 10]  # Not learning! (residual var = 1.0)
    old_time = datetime.now() - timedelta(hours=30)  # Stale!
    experiences = [
        {'timestamp': old_time.isoformat()},
        {'timestamp': old_time.isoformat()},
    ]

    logger.log_cycle(3, actions, rewards, experiences, values)

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    summary = logger.get_metrics_summary()
    print(f"\nTotal cycles logged: {summary['total_cycles']}")
    print(f"Total red flags: {summary['total_red_flags']}")
    print(f"\nAll red flags:")
    for flag in summary['all_red_flags']:
        print(f"  • {flag}")


if __name__ == "__main__":
    demo()
