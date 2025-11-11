#!/usr/bin/env python3
"""
PATTERN EXTRACTOR - Extract Learning Patterns from Runs
Extrai trajectories, atalhos, recovery patterns pra reutilização

BASEADO EM: knowledge-machine/experience_consolidator.py
CUSTOMIZADO PARA: Trajectory analysis, shortcut detection, recovery path extraction

PATTERNS:
- Trajectory: sequence de (url, action, duration)
- Shortcut: action que pula steps normalmente necessários
- Recovery: ação que recupera de falha
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
from datetime import datetime


@dataclass
class Step:
    """Um step em uma trajectory"""
    index: int
    url: str
    action: str
    duration: float
    status: str  # success, skip, recovery


@dataclass
class Trajectory:
    """Sequência de steps em um run"""
    run_id: str
    steps: List[Step]
    total_duration: float
    reward: float
    hash_value: str = ""

    def __post_init__(self):
        if not self.hash_value:
            self.hash_value = self._compute_hash()

    def _compute_hash(self) -> str:
        """Computa hash determinístico da trajectory"""
        trajectory_str = "|".join(f"{s.action}@{s.url}" for s in self.steps)
        return hashlib.sha256(trajectory_str.encode()).hexdigest()[:16]


@dataclass
class Shortcut:
    """Um padrão de atalho detectado"""
    name: str  # Nome do atalho
    from_state: str  # Estado inicial
    to_state: str  # Estado final (pulando steps)
    actions: List[str]  # Ações que o formam
    time_saved: float  # Segundos economizados
    occurrences: int = 1
    consistency: float = 1.0  # Quantas vezes funciona


@dataclass
class RecoveryPattern:
    """Um padrão de recuperação de falha"""
    name: str  # Nome do recovery
    trigger: str  # O que causa a falha
    actions: List[str]  # Ações para recuperar
    success_rate: float  # Taxa de sucesso
    examples: List[str] = None  # Run IDs onde funcionou


class PatternExtractor:
    """
    Extrai padrões de runs bem-sucedidos
    """

    def __init__(self):
        self.trajectories = []  # List[Trajectory]
        self.shortcuts = []  # List[Shortcut]
        self.recovery_patterns = []  # List[RecoveryPattern]
        self.trajectory_index = defaultdict(list)  # hash -> [Trajectory, ...]

    def add_run(
        self,
        run_id: str,
        steps_data: List[Dict],
        reward: float
    ):
        """
        Adiciona um run pra análise

        Args:
            run_id: ID do run
            steps_data: Lista de {index, url, action, duration, status}
            reward: Reward final do run
        """
        steps = [
            Step(
                index=s.get('index', i),
                url=s.get('url', ''),
                action=s.get('action', ''),
                duration=s.get('duration', 0),
                status=s.get('status', 'success')
            )
            for i, s in enumerate(steps_data)
        ]

        total_duration = sum(s.duration for s in steps)

        trajectory = Trajectory(
            run_id=run_id,
            steps=steps,
            total_duration=total_duration,
            reward=reward
        )

        self.trajectories.append(trajectory)
        self.trajectory_index[trajectory.hash_value].append(trajectory)

    def extract_shortcuts(self) -> List[Shortcut]:
        """
        Detecta atalhos na trajectória

        Atalho = sequência de ações que consegue o mesmo resultado com menos tempo
        """
        shortcuts_dict = defaultdict(lambda: {'count': 0, 'time_saved': 0, 'runs': []})

        # Compara trajectories similares pra encontrar atalhos
        for hash_val, trajectories in self.trajectory_index.items():
            if len(trajectories) < 2:
                continue  # Precisa de pelo menos 2 runs com mesmo padrão

            sorted_by_duration = sorted(trajectories, key=lambda t: t.total_duration)
            slowest = sorted_by_duration[-1]
            fastest = sorted_by_duration[0]

            if fastest.total_duration < slowest.total_duration * 0.8:  # 20%+ faster
                shortcut_name = f"shortcut_{hash_val[:8]}"
                time_saved = slowest.total_duration - fastest.total_duration

                # Identifica diferenças na trajectory
                different_actions = self._find_different_actions(
                    slowest.steps, fastest.steps
                )

                shortcuts_dict[shortcut_name]['count'] += 1
                shortcuts_dict[shortcut_name]['time_saved'] += time_saved
                shortcuts_dict[shortcut_name]['runs'].append(fastest.run_id)

        # Cria Shortcut objects
        self.shortcuts = [
            Shortcut(
                name=name,
                from_state=f"trajectory_{name}",
                to_state=f"trajectory_{name}_optimized",
                actions=["optimized_sequence"],
                time_saved=data['time_saved'] / data['count'],
                occurrences=data['count'],
                consistency=min(data['count'] / 10, 1.0)
            )
            for name, data in shortcuts_dict.items()
        ]

        return self.shortcuts

    def extract_recovery_patterns(self) -> List[RecoveryPattern]:
        """
        Detecta padrões de recuperação

        Recovery = ações que transformam run falhado em sucesso
        """
        recovery_dict = defaultdict(lambda: {
            'count': 0, 'success': 0, 'runs': []
        })

        for trajectory in self.trajectories:
            # Busca steps com status recovery
            for step in trajectory.steps:
                if step.status == 'recovery':
                    # Captura contexto (previous step + recovery action)
                    prev_action = (trajectory.steps[step.index - 1].action
                                   if step.index > 0 else "start")
                    recovery_name = f"recovery_{prev_action}_{step.action}"

                    recovery_dict[recovery_name]['count'] += 1
                    if trajectory.reward > 100:  # Considera sucesso se reward > 100
                        recovery_dict[recovery_name]['success'] += 1
                    recovery_dict[recovery_name]['runs'].append(trajectory.run_id)

        # Cria RecoveryPattern objects
        self.recovery_patterns = [
            RecoveryPattern(
                name=name,
                trigger=name.split('_')[1],  # Extracted from name
                actions=[name.split('_')[2]],  # Extracted from name
                success_rate=(data['success'] / data['count']
                              if data['count'] > 0 else 0),
                examples=data['runs'][:5]
            )
            for name, data in recovery_dict.items()
            if data['count'] > 0
        ]

        return self.recovery_patterns

    def _find_different_actions(
        self,
        steps_a: List[Step],
        steps_b: List[Step]
    ) -> List[str]:
        """Encontra ações diferentes entre 2 trajectories"""
        set_a = {s.action for s in steps_a}
        set_b = {s.action for s in steps_b}
        return list(set_a - set_b)

    def get_most_common_trajectory(self) -> Optional[Trajectory]:
        """Retorna trajectory mais comum"""
        if not self.trajectory_index:
            return None

        most_common_hash = max(
            self.trajectory_index.items(),
            key=lambda x: len(x[1])
        )[0]

        trajectories = self.trajectory_index[most_common_hash]
        return max(trajectories, key=lambda t: t.reward)

    def get_trajectory_diversity(self) -> Dict:
        """Retorna diversidade de trajectories"""
        return {
            'total_unique_trajectories': len(self.trajectory_index),
            'total_runs': len(self.trajectories),
            'most_common_count': (
                max(len(v) for v in self.trajectory_index.values())
                if self.trajectory_index else 0
            )
        }

    def export_patterns(self, path: Path):
        """Salva todos os padrões em arquivo"""
        # Extrai padrões se ainda não fez
        if not self.shortcuts:
            self.extract_shortcuts()
        if not self.recovery_patterns:
            self.extract_recovery_patterns()

        data = {
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'total_trajectories': len(self.trajectories),
                'unique_trajectories': len(self.trajectory_index),
                'shortcuts_found': len(self.shortcuts),
                'recovery_patterns_found': len(self.recovery_patterns)
            },
            'trajectories': [
                {
                    'run_id': t.run_id,
                    'hash': t.hash_value,
                    'total_duration': t.total_duration,
                    'reward': t.reward,
                    'steps_count': len(t.steps)
                }
                for t in self.trajectories
            ],
            'shortcuts': [asdict(s) for s in self.shortcuts],
            'recovery_patterns': [
                {
                    'name': rp.name,
                    'trigger': rp.trigger,
                    'actions': rp.actions,
                    'success_rate': rp.success_rate,
                    'examples': rp.examples or []
                }
                for rp in self.recovery_patterns
            ]
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)


# ============================================================================
# TEST & DEMO
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("PATTERN EXTRACTOR - Analysis Demo")
    print("="*80 + "\n")

    extractor = PatternExtractor()

    # Simula 5 runs com trajectory data
    print("[CHART] LOADING 5 RUNS WITH TRAJECTORIES...\n")

    runs_data = [
        {
            'run_id': 'run_001',
            'steps': [
                {'index': 0, 'url': '/login', 'action': 'login', 'duration': 2.0, 'status': 'success'},
                {'index': 1, 'url': '/dashboard', 'action': 'navigate_properties', 'duration': 1.5, 'status': 'success'},
                {'index': 2, 'url': '/properties', 'action': 'create_property', 'duration': 15.0, 'status': 'success'},
                {'index': 3, 'url': '/properties/123', 'action': 'fill_details', 'duration': 10.0, 'status': 'success'},
            ],
            'reward': 280
        },
        {
            'run_id': 'run_002',
            'steps': [
                {'index': 0, 'url': '/login', 'action': 'login', 'duration': 2.0, 'status': 'success'},
                {'index': 1, 'url': '/dashboard', 'action': 'navigate_properties', 'duration': 1.5, 'status': 'success'},
                {'index': 2, 'url': '/properties', 'action': 'create_property', 'duration': 8.0, 'status': 'success'},  # ATALHO!
                {'index': 3, 'url': '/properties/124', 'action': 'fill_details', 'duration': 8.0, 'status': 'success'},
            ],
            'reward': 330
        },
        {
            'run_id': 'run_003',
            'steps': [
                {'index': 0, 'url': '/login', 'action': 'login', 'duration': 2.0, 'status': 'success'},
                {'index': 1, 'url': '/dashboard', 'action': 'navigate_properties', 'duration': 1.5, 'status': 'success'},
                {'index': 2, 'url': '/properties', 'action': 'create_property', 'duration': 12.0, 'status': 'failure'},
                {'index': 3, 'url': '/properties', 'action': 'retry_create', 'duration': 8.0, 'status': 'recovery'},
            ],
            'reward': 150
        },
    ]

    for run_data in runs_data:
        extractor.add_run(
            run_id=run_data['run_id'],
            steps_data=run_data['steps'],
            reward=run_data['reward']
        )

    # Extract patterns
    print("[SEARCH] EXTRACTING PATTERNS...\n")

    shortcuts = extractor.extract_shortcuts()
    recovery_patterns = extractor.extract_recovery_patterns()

    print(f"[OK] Found {len(shortcuts)} shortcuts")
    print(f"[OK] Found {len(recovery_patterns)} recovery patterns")

    # Display trajectories
    print("\n" + "="*80)
    print("TRAJECTORIES")
    print("="*80 + "\n")

    for traj in extractor.trajectories:
        print(f"Run: {traj.run_id} (reward: {traj.reward}, duration: {traj.total_duration:.1f}s)")
        for step in traj.steps:
            print(f"  → {step.action:20s} @ {step.url:20s} ({step.duration:.1f}s)")
        print()

    # Display shortcuts
    if shortcuts:
        print("="*80)
        print("SHORTCUTS DETECTED")
        print("="*80 + "\n")
        for shortcut in shortcuts:
            print(f" {shortcut.name}")
            print(f"   Time saved: {shortcut.time_saved:.1f}s")
            print(f"   Occurrences: {shortcut.occurrences}")
            print(f"   Consistency: {shortcut.consistency:.0%}\n")

    # Display recovery patterns
    if recovery_patterns:
        print("="*80)
        print("RECOVERY PATTERNS")
        print("="*80 + "\n")
        for rp in recovery_patterns:
            print(f" {rp.name}")
            print(f"   Trigger: {rp.trigger}")
            print(f"   Success rate: {rp.success_rate:.0%}")
            print(f"   Examples: {', '.join(rp.examples)}\n")

    # Diversity
    diversity = extractor.get_trajectory_diversity()
    print("="*80)
    print("DIVERSITY METRICS")
    print("="*80)
    print(f"Total unique trajectories: {diversity['total_unique_trajectories']}")
    print(f"Total runs: {diversity['total_runs']}")
    print(f"Most common count: {diversity['most_common_count']}")

    print("\n" + "="*80 + "\n")
