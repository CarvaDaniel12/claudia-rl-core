#!/usr/bin/env python3
"""
RL ATOMIC - Reinforcement Learning Atomic Loop Package

Complete autonomous RL system pra Hunter QA tool

MODULES:
1. reward_shaper.py      - 4-tier reward calculation (Phase 1.1)
2. state_representation.py - State capture + tracking (Phase 1.2)
3. golden_path_enhanced_V2.py - Self-healing golden path V2 (Phase 1.3)
4. run_selector.py       - Tier-based selection (Phase 2.1)
5. pattern_extractor.py  - Extract patterns (Phase 2.2)
6. barril_cleaner.py     - Archive & cleanup (Phase 2.3)
7. memory_bootstrap.py   - Pre-seed memory (Phase 3)
8. atomic_loop.py        - Main orchestrator (Phase 4)
9. rlaif_auto_feedback.py - Auto validation (Phase 5.1)

USAGE:
    from rl_atomic import AtomicLoopOrchestrator
    orchestrator = AtomicLoopOrchestrator(barril_path="./barril!!")
    success, metrics = orchestrator.run_cycle()
"""

from .reward_shaper import RewardShaper
from .state_representation import (
    StateRepresentation,
    ConstraintTracker,
    BudgetTracker
)
from .run_selector import RunSelector, RunTier, RunMetadata
from .pattern_extractor import (
    PatternExtractor,
    Trajectory,
    Shortcut,
    RecoveryPattern
)
from .barril_cleaner import BarrilCleaner
from .memory_bootstrap import (
    MemoryBootstrap,
    EfficiencyFrontier,
    WorkingMemory,
    MetaStat
)
from .atomic_loop import AtomicLoopOrchestrator, CycleMetrics
from .rlaif_auto_feedback import RLAIFAutoFeedback, ValidationResult, ValidationStatus

__version__ = "1.0.0"
__author__ = "Hunter RL Autonomous Loop"

__all__ = [
    "RewardShaper",
    "StateRepresentation",
    "ConstraintTracker",
    "BudgetTracker",
    "RunSelector",
    "RunTier",
    "RunMetadata",
    "PatternExtractor",
    "Trajectory",
    "Shortcut",
    "RecoveryPattern",
    "BarrilCleaner",
    "MemoryBootstrap",
    "EfficiencyFrontier",
    "WorkingMemory",
    "MetaStat",
    "AtomicLoopOrchestrator",
    "CycleMetrics",
    "RLAIFAutoFeedback",
    "ValidationResult",
    "ValidationStatus",
]
