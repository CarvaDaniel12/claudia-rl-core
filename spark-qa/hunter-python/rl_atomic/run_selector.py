#!/usr/bin/env python3
"""
RUN SELECTOR - Tier Selection Logic for RL Atomic Loop
Classifica runs em Tier 1/2/3 pra bootstrap do próximo ciclo

BASEADO EM: knowledge-machine/reward_orchestrator.py ExperienceSelector
CUSTOMIZADO PARA: Tier-based selection (top rewards, diverse patterns, edge cases)

TIER LOGIC:
- Tier 1: Top 10% by reward (best performance)
- Tier 2: Next 30% + diverse patterns (learning)
- Tier 3: Edge cases + recovery scenarios (resilience)
- Discard: Bottom 60% (low value)
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime


class RunTier(Enum):
    """Tier classification"""
    TIER_1 = "tier_1"  # Top 10%, best rewards
    TIER_2 = "tier_2"  # Next 30%, diverse + learning
    TIER_3 = "tier_3"  # Edge cases + recovery
    DISCARD = "discard"  # Bottom 60%


@dataclass
class RunMetadata:
    """Metadata de um run"""
    run_id: str
    reward: float
    duration: float
    steps: int
    success: bool
    has_shortcuts: bool
    has_recovery: bool
    pattern_hash: str  # Hash da trajectory
    timestamp: str

    def to_dict(self):
        return asdict(self)


class RunSelector:
    """
    Seleciona runs para bootstrap do próximo ciclo

    Estratégia:
    1. Classifica por reward (top 10%)
    2. Seleciona por diversidade de padrões (next 30%)
    3. Seleciona edge cases (recovery scenarios)
    4. Descarta baixa performance (bottom 60%)
    """

    def __init__(self, total_runs: int = 100):
        self.total_runs = total_runs
        self.tier_1_size = max(1, int(total_runs * 0.10))  # Top 10%
        self.tier_2_size = max(1, int(total_runs * 0.30))  # Next 30%
        self.tier_3_size = max(1, int(total_runs * 0.10))  # Edge cases (10%)

        self.runs = []  # Lista de RunMetadata
        self.tiered_runs = {
            RunTier.TIER_1: [],
            RunTier.TIER_2: [],
            RunTier.TIER_3: [],
            RunTier.DISCARD: []
        }
        self.pattern_cache = {}  # pattern_hash -> count

    def add_run(
        self,
        run_id: str,
        reward: float,
        duration: float,
        steps: int,
        success: bool,
        has_shortcuts: bool = False,
        has_recovery: bool = False,
        pattern_hash: str = ""
    ):
        """Adiciona um run pra seleção"""
        run = RunMetadata(
            run_id=run_id,
            reward=reward,
            duration=duration,
            steps=steps,
            success=success,
            has_shortcuts=has_shortcuts,
            has_recovery=has_recovery,
            pattern_hash=pattern_hash or "unknown",
            timestamp=datetime.now().isoformat()
        )
        self.runs.append(run)

        # Cache de padrões
        if pattern_hash:
            self.pattern_cache[pattern_hash] = self.pattern_cache.get(pattern_hash, 0) + 1

    def select_tiered_runs(self) -> Dict[RunTier, List[RunMetadata]]:
        """
        Seleciona runs por tier

        Returns:
            dict: {RunTier: [RunMetadata, ...]}
        """
        if not self.runs:
            return self.tiered_runs

        # TIER 1: Top 10% by reward
        sorted_by_reward = sorted(self.runs, key=lambda r: r.reward, reverse=True)
        tier_1_candidates = sorted_by_reward[:self.tier_1_size]
        self.tiered_runs[RunTier.TIER_1] = tier_1_candidates

        # TIER 2: Next 30%, preferindo diverse patterns
        remaining = sorted_by_reward[self.tier_1_size:]
        tier_2_candidates = self._select_diverse_runs(
            remaining, self.tier_2_size
        )
        self.tiered_runs[RunTier.TIER_2] = tier_2_candidates

        # TIER 3: Edge cases (recovery scenarios + shortcuts)
        tier_3_candidates = self._select_edge_cases(remaining, self.tier_3_size)
        self.tiered_runs[RunTier.TIER_3] = tier_3_candidates

        # DISCARD: resto
        all_selected = (
            set(r.run_id for r in tier_1_candidates) |
            set(r.run_id for r in tier_2_candidates) |
            set(r.run_id for r in tier_3_candidates)
        )
        discarded = [r for r in self.runs if r.run_id not in all_selected]
        self.tiered_runs[RunTier.DISCARD] = discarded

        return self.tiered_runs

    def _select_diverse_runs(
        self,
        candidates: List[RunMetadata],
        count: int
    ) -> List[RunMetadata]:
        """Seleciona runs com padrões diversos"""
        selected = []
        pattern_diversity = {}

        for run in candidates:
            pattern = run.pattern_hash
            if pattern not in pattern_diversity:
                selected.append(run)
                pattern_diversity[pattern] = 1
                if len(selected) >= count:
                    break
            elif pattern_diversity[pattern] < 2:
                # Max 2 runs do mesmo padrão
                selected.append(run)
                pattern_diversity[pattern] += 1
                if len(selected) >= count:
                    break

        # Se ainda precisa mais, pega os melhores restantes
        if len(selected) < count:
            for run in candidates:
                if run not in selected and len(selected) < count:
                    selected.append(run)

        return selected[:count]

    def _select_edge_cases(
        self,
        candidates: List[RunMetadata],
        count: int
    ) -> List[RunMetadata]:
        """Seleciona edge cases (recovery + shortcuts)"""
        selected = []

        # Prioriza recovery scenarios
        recovery_candidates = [r for r in candidates if r.has_recovery]
        shortcut_candidates = [r for r in candidates if r.has_shortcuts]

        # Mix: metade recovery, metade shortcuts
        recovery_half = count // 2
        shortcuts_half = count - recovery_half

        selected.extend(recovery_candidates[:recovery_half])
        selected.extend(shortcut_candidates[:shortcuts_half])

        # Se ainda precisa, pega aleatoriamente
        while len(selected) < count:
            for r in candidates:
                if r not in selected and len(selected) < count:
                    selected.append(r)

        return selected[:count]

    def get_tier_summary(self) -> Dict:
        """Retorna sumário de runs por tier"""
        summary = {}
        for tier, runs in self.tiered_runs.items():
            if runs:
                avg_reward = sum(r.reward for r in runs) / len(runs)
                avg_duration = sum(r.duration for r in runs) / len(runs)
                success_rate = sum(1 for r in runs if r.success) / len(runs)
                summary[tier.value] = {
                    'count': len(runs),
                    'avg_reward': round(avg_reward, 2),
                    'avg_duration': round(avg_duration, 2),
                    'success_rate': round(success_rate, 2),
                    'runs': [r.run_id for r in runs[:5]]  # First 5
                }

        return summary

    def export_tiered_runs(self, path: Path):
        """Salva runs classificados em arquivo"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_runs': len(self.runs),
            'tier_summary': self.get_tier_summary(),
            'runs_by_tier': {
                tier.value: [r.to_dict() for r in runs]
                for tier, runs in self.tiered_runs.items()
            }
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_bootstrap_runs(self) -> List[RunMetadata]:
        """Retorna runs pra memory bootstrap (Tier 1 + Tier 2)"""
        return (
            self.tiered_runs[RunTier.TIER_1] +
            self.tiered_runs[RunTier.TIER_2]
        )

    def get_runs_to_delete(self) -> List[str]:
        """Retorna run_ids pra deletar (DISCARD + Tier 3)"""
        return [r.run_id for r in (
            self.tiered_runs[RunTier.DISCARD] +
            self.tiered_runs[RunTier.TIER_3]
        )]

    def get_pattern_diversity_score(self) -> float:
        """
        Score de diversidade de padrões (0-1)
        Quanto mais padrões distintos, melhor
        """
        if not self.runs:
            return 0.0

        unique_patterns = len(self.pattern_cache)
        total_runs = len(self.runs)

        # Score: unique_patterns / total_runs (capped at 1.0)
        # Se todos runs têm padrão diferente = 1.0
        # Se todos têm mesmo padrão = 1/total_runs
        return min(unique_patterns / total_runs, 1.0)


# ============================================================================
# TEST & DEMO
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("RUN SELECTOR - Tier Selection Demo")
    print("="*80 + "\n")

    selector = RunSelector(total_runs=50)

    # Simula 50 runs com diferentes rewards
    print("[CHART] SIMULATING 50 RUNS...\n")

    rewards_distribution = [
        # Tier 1 (top 10%): 250-300 reward
        *([250 + i*2 for i in range(5)]),
        # Tier 2 (next 30%): 150-200 reward
        *([150 + i*2 for i in range(15)]),
        # Tier 3 (edge cases): 100-150 reward
        *([100 + i*2 for i in range(5)]),
        # Discard (bottom 60%): 0-100 reward
        *([50 - i*2 for i in range(25)])
    ]

    for i, reward in enumerate(rewards_distribution):
        duration = 45 + (i % 30)  # 45-75 segundos
        steps = 20 + (i % 10)  # 20-30 steps
        pattern_hash = f"pattern_{i % 5}"  # 5 padrões diferentes
        has_recovery = (i % 4 == 0)  # 25% tem recovery
        has_shortcut = (i % 5 == 0)  # 20% tem shortcuts

        selector.add_run(
            run_id=f"run_{i:03d}",
            reward=reward,
            duration=duration,
            steps=steps,
            success=True if reward > 50 else False,
            has_shortcuts=has_shortcut,
            has_recovery=has_recovery,
            pattern_hash=pattern_hash
        )

    # Select tiered runs
    tiered = selector.select_tiered_runs()

    print("[TARGET] TIER SELECTION RESULTS:\n")
    summary = selector.get_tier_summary()

    for tier_name, tier_stats in summary.items():
        print(f" {tier_name.upper()}")
        print(f"  Count: {tier_stats['count']}")
        print(f"  Avg Reward: {tier_stats['avg_reward']}")
        print(f"  Avg Duration: {tier_stats['avg_duration']}s")
        print(f"  Success Rate: {tier_stats['success_rate']:.0%}")
        print(f"  Examples: {', '.join(tier_stats['runs'][:3])}")
        print(f"\n")

    # Bootstrap runs
    bootstrap = selector.get_bootstrap_runs()
    print(f"[SAVE] BOOTSTRAP RUNS (Tier 1 + 2): {len(bootstrap)} runs")
    print(f"   These will seed the next cycle\n")

    # Runs to delete
    to_delete = selector.get_runs_to_delete()
    print(f"[TRASH]  RUNS TO DELETE (Tier 3 + DISCARD): {len(to_delete)} runs")
    print(f"   {', '.join(to_delete[:5])}...")

    # Diversity
    diversity = selector.get_pattern_diversity_score()
    print(f"\n[TRENDING_UP] PATTERN DIVERSITY SCORE: {diversity:.2f}/1.0")

    print("\n" + "="*80 + "\n")
