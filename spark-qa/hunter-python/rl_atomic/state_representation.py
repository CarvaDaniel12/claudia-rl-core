#!/usr/bin/env python3
"""
STATE REPRESENTATION - RL Atomic Loop
Estende StateMapper de rl_core.py com campos adicionais

BASEADO EM: knowledge-machine/rl_core.py StateMapper
CUSTOMIZADO PARA: Histórico, constraints, budget, similarity

STATE STRUCTURE:
{
    'url': str,
    'page_name': str,
    'visible_elements': int,
    'action_history': list (last 5),
    'active_constraints': list,
    'step_budget': int (remaining),
    'similarity_to_best_runs': float (0-1),
    'timestamp': str
}
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict, deque


class StateRepresentation:
    """
    Representa estado atual com histórico e constraints
    Compatível com StateMapper existente
    """

    def __init__(self, max_history: int = 5):
        self.max_history = max_history
        self.state_encodings = {}  # Hash -> token mapping
        self.encoder_counter = 0
        self.action_history = deque(maxlen=max_history)
        self.best_runs_cache = {}

    def capture_state(
        self,
        url: str,
        page_name: str,
        visible_elements: int,
        active_constraints: Optional[List[str]] = None,
        step_budget: Optional[int] = None,
        best_runs_data: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Captura estado atual do agent

        Args:
            url: Current URL
            page_name: Current page name
            visible_elements: Number of visible elements
            active_constraints: Constraints ativas neste momento
            step_budget: Steps restantes
            best_runs_data: Runs anteriores pra comparar similaridade

        Returns:
            dict: State representation completo
        """
        state = {
            'url': url,
            'page_name': page_name,
            'visible_elements': visible_elements,
            'action_history': list(self.action_history),
            'active_constraints': active_constraints or [],
            'step_budget': step_budget,
            'similarity_to_best_runs': self._calculate_similarity(
                url, page_name, best_runs_data
            ),
            'timestamp': self._get_timestamp()
        }

        return state

    def add_action_to_history(self, action: Dict):
        """Adiciona ação ao histórico (últimas 5)"""
        self.action_history.append(action)

    def encode_state(self, state: Dict) -> int:
        """
        Codifica state em token (compatível com StateMapper)

        Usa hash SHA256 + mapeamento pra int
        """
        # Serializa state (exclui timestamp pra determinismo)
        state_copy = state.copy()
        state_copy.pop('timestamp', None)
        state_str = json.dumps(state_copy, sort_keys=True)

        # SHA256 hash
        state_hash = hashlib.sha256(state_str.encode()).hexdigest()

        # Mapeia pra int se não existe
        if state_hash not in self.state_encodings:
            self.state_encodings[state_hash] = self.encoder_counter
            self.encoder_counter += 1

        return self.state_encodings[state_hash]

    def decode_state(self, token: int) -> Optional[Dict]:
        """Decodifica token de volta pra state (best effort)"""
        for state_hash, encoded_token in self.state_encodings.items():
            if encoded_token == token:
                # Nota: Não conseguimos recuperar state original, só token
                # Isso é OK pra RL - token é o que importa
                return {'token': token, 'hash': state_hash}
        return None

    def _calculate_similarity(
        self,
        current_url: str,
        current_page: str,
        best_runs_data: Optional[List[Dict]] = None
    ) -> float:
        """
        Calcula similaridade com runs bem-sucedidos

        Compara URL + page_name com melhores runs
        Retorna score 0-1
        """
        if not best_runs_data:
            return 0.5  # Neutra

        matches = 0
        total = min(len(best_runs_data), 10)  # Compara com top 10

        for best_run in best_runs_data[:total]:
            if (best_run.get('url') == current_url and
                best_run.get('page_name') == current_page):
                matches += 1

        similarity = matches / total if total > 0 else 0.5
        return min(similarity, 1.0)

    def _get_timestamp(self) -> str:
        """Retorna timestamp ISO"""
        from datetime import datetime
        return datetime.now().isoformat()

    def export_for_policy(self) -> Dict:
        """
        Export state em formato que policy network possa usar
        Inclui: action_history, constraints, budget, similarity
        """
        return {
            'action_history': list(self.action_history),
            'encodings_count': len(self.state_encodings),
            'encoder_counter': self.encoder_counter
        }

    def save_encodings(self, path: Path):
        """Salva state encodings pra próximo ciclo"""
        data = {
            'state_encodings': self.state_encodings,
            'encoder_counter': self.encoder_counter
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_encodings(self, path: Path):
        """Carrega state encodings do ciclo anterior"""
        if not path.exists():
            return

        with open(path, 'r') as f:
            data = json.load(f)

        self.state_encodings = data.get('state_encodings', {})
        self.encoder_counter = data.get('encoder_counter', 0)


class ConstraintTracker:
    """
    Rastreia constraints ativas durante um run
    """

    def __init__(self):
        self.constraints = []
        self.constraint_violations = defaultdict(int)

    def add_constraint(self, constraint: str):
        """Adiciona constraint ativa"""
        if constraint not in self.constraints:
            self.constraints.append(constraint)

    def remove_constraint(self, constraint: str):
        """Remove constraint"""
        if constraint in self.constraints:
            self.constraints.remove(constraint)

    def log_violation(self, constraint: str):
        """Log violação de constraint"""
        self.constraint_violations[constraint] += 1

    def get_active_constraints(self) -> List[str]:
        """Retorna constraints ativas"""
        return self.constraints.copy()

    def get_violation_summary(self) -> Dict:
        """Retorna sumário de violações"""
        return dict(self.constraint_violations)


class BudgetTracker:
    """
    Rastreia budget (steps, tempo, etc)
    """

    def __init__(self, max_steps: int = 100, max_duration_seconds: int = 300):
        self.max_steps = max_steps
        self.max_duration_seconds = max_duration_seconds
        self.steps_taken = 0
        self.start_time = None

    def step(self):
        """Incrementa step counter"""
        self.steps_taken += 1

    def get_remaining_steps(self) -> int:
        """Retorna steps restantes"""
        return max(0, self.max_steps - self.steps_taken)

    def is_step_budget_exceeded(self) -> bool:
        """Checa se excedeu step budget"""
        return self.steps_taken >= self.max_steps

    def get_elapsed_time(self) -> float:
        """Retorna tempo decorrido em segundos"""
        if not self.start_time:
            return 0.0
        from datetime import datetime
        return (datetime.now() - self.start_time).total_seconds()

    def is_time_budget_exceeded(self) -> bool:
        """Checa se excedeu time budget"""
        return self.get_elapsed_time() >= self.max_duration_seconds

    def start(self):
        """Inicia contador"""
        from datetime import datetime
        self.start_time = datetime.now()


# ============================================================================
# TEST & DEMO
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("STATE REPRESENTATION - Test & Demo")
    print("="*80 + "\n")

    # Create instances
    state_rep = StateRepresentation(max_history=5)
    constraint_tracker = ConstraintTracker()
    budget_tracker = BudgetTracker(max_steps=50, max_duration_seconds=120)

    # Demo: Capture multiple states
    print(" CAPTURING STATES...\n")

    states = []
    for i in range(3):
        state = state_rep.capture_state(
            url=f"https://test.hostfully.com/page{i}",
            page_name=f"page_{i}",
            visible_elements=20 + i,
            active_constraints=['no_narratives', 'regression_safe'],
            step_budget=budget_tracker.get_remaining_steps()
        )
        states.append(state)
        print(f"State {i}: {state['page_name']} @ {state['url']}")
        print(f"  Active constraints: {state['active_constraints']}")
        print(f"  Budget: {state['step_budget']} steps remaining")

        # Simulate action
        state_rep.add_action_to_history({'action': f'action_{i}', 'duration': 0.5})
        budget_tracker.step()

    print("\n" + "="*80)
    print("STATE ENCODING")
    print("="*80 + "\n")

    # Encode states
    for i, state in enumerate(states):
        token = state_rep.encode_state(state)
        print(f"State {i} → Token: {token}")

    print(f"\nTotal encodings: {len(state_rep.state_encodings)}")

    print("\n" + "="*80)
    print("CONSTRAINTS & BUDGET")
    print("="*80 + "\n")

    constraint_tracker.add_constraint('no_narratives')
    constraint_tracker.add_constraint('regression_safe')
    constraint_tracker.log_violation('regression_safe')

    print(f"Active constraints: {constraint_tracker.get_active_constraints()}")
    print(f"Violations: {constraint_tracker.get_violation_summary()}")
    print(f"Steps remaining: {budget_tracker.get_remaining_steps()}/{budget_tracker.max_steps}")

    print("\n" + "="*80 + "\n")
