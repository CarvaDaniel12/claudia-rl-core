#!/usr/bin/env python3
"""
RLAIF AUTO FEEDBACK - Reinforcement Learning from AI Feedback
Auto-validates runs, provides feedback for RL learning

RLAIF PROCESS:
1. Agent executes run (golden path)
2. System analyzes result
3. System validates against constraints
4. System provides score + feedback
5. Score used as reward multiplier in atomic loop

Result: Autonomous RL without human annotation
"""

import json
import time
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class ValidationStatus(Enum):
    """Status de validação"""
    PASS = "pass"
    PASS_WITH_WARNINGS = "pass_with_warnings"
    FAIL = "fail"
    FAIL_CONSTRAINT_VIOLATION = "fail_constraint_violation"


@dataclass
class ValidationResult:
    """Resultado de validação de um run"""
    run_id: str
    status: ValidationStatus
    score: float  # 0-1, used as confidence multiplier
    feedback: str
    constraints_violated: List[str]
    suggestions: List[str]
    constraint_violations: Dict = None  # Constraint violations with severity
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.constraint_violations is None:
            self.constraint_violations = {}


class RLAIFAutoFeedback:
    """
    Auto feedback for RL validation
    Validates runs against quality constraints
    """

    def __init__(self, enable_constraint_checking: bool = True):
        """
        Args:
            enable_constraint_checking: Use constraint validation
        """
        self.enable_constraint_checking = enable_constraint_checking
        self.validation_history = []

    def validate_run(
        self,
        run_id: str,
        run_data: Dict,
        rules_config: Optional[Dict] = None
    ) -> ValidationResult:
        """
        Valida um run completado

        Args:
            run_id: ID do run
            run_data: {
                'success': bool,
                'duration': float,
                'steps': [...]
                'created_files': [...],
                'created_narratives': [...],
                'other_side_effects': [...]
            }
            rules_config: Rules pra validação (optional)

        Returns:
            ValidationResult com score + feedback
        """
        constraints_violated = []
        score = 1.0
        feedback_parts = []
        suggestions = []

        # CHECK 1: Basic Success
        if not run_data.get('success', False):
            constraints_violated.append('execution_failed')
            score *= 0.5
            feedback_parts.append("Run did not complete successfully")
            suggestions.append("Check for execution errors in logs")

        # CHECK 2: Basic Constraint Violations
        if self.enable_constraint_checking:
            # Check for narrative files
            if run_data.get('created_narratives', []):
                constraints_violated.append('narrative_files_created')
                score *= 0.7
                feedback_parts.append("Created narrative files (should use JSON)")
            
            # Check for regression
            if not run_data.get('regression_safe', True):
                constraints_violated.append('regression_broken')
                score *= 0.7
                feedback_parts.append("Regression tests failed")

        # CHECK 3: Performance (Duration)
        duration = run_data.get('duration', 0)
        if duration > 120:  # > 2 minutes
            score *= 0.9
            feedback_parts.append(f"Run took {duration:.1f}s (slower than baseline)")
            suggestions.append("Look for optimization opportunities")

        # CHECK 4: Narrative Files (Anti-pattern)
        narrative_files = self._detect_narrative_files(run_data)
        if narrative_files:
            constraints_violated.append('narrative_files_created')
            score *= 0.7
            feedback_parts.append(f"Created forbidden narrative files: {narrative_files}")
            suggestions.append("Remove narrative file creation")

        # CHECK 5: Side Effects
        side_effects = run_data.get('other_side_effects', [])
        if side_effects:
            for effect in side_effects:
                if effect.get('type') == 'file_creation':
                    constraints_violated.append(f"unexpected_file_{effect.get('name', 'unknown')}")
                    score *= 0.8
        
        # CHECK 6: Cleanup Validation (CRITICAL for production)
        if not run_data.get('cleanup_successful', False):
            score *= 0.7
            feedback_parts.append("Cleanup failed - test data may still exist in platform")
            suggestions.append("Verify cleanup logic in finally block")
        
        # CHECK 7: Assertion Success Rate
        assertions_rate = run_data.get('assertions_success_rate', 100)
        if assertions_rate < 80:
            score *= 0.8
            feedback_parts.append(f"Low assertion success: {assertions_rate:.1f}% (expected >80%)")
            suggestions.append("Investigate failing assertions - may indicate real bugs")

        # Determine overall status
        if not constraints_violated:
            if score >= 0.95:
                status = ValidationStatus.PASS
            else:
                status = ValidationStatus.PASS_WITH_WARNINGS
        elif any(v.startswith('fail_') for v in constraints_violated):
            status = ValidationStatus.FAIL_CONSTRAINT_VIOLATION
        else:
            status = ValidationStatus.FAIL

        # Compile feedback
        feedback = " | ".join(feedback_parts) if feedback_parts else "Validation passed"

        result = ValidationResult(
            run_id=run_id,
            status=status,
            score=max(0.0, score),  # Clamp to [0, 1]
            feedback=feedback,
            constraints_violated=constraints_violated,
            suggestions=suggestions
        )

        self.validation_history.append(result)
        return result

    def _check_constraints(self, run_data: Dict) -> Dict:
        """
        Valida constraints usando 7 FREIO layers + PROACTIVITY_RULES

        Returns:
            {
                'violations': [list of constraint violations],
                'severity_multiplier': float (0-1),
                'message': str,
                'suggestions': [...],
                'freio_violations': {layer: [violations]}
            }
        """
        violations = []
        severity_multiplier = 1.0
        suggestions = []
        freio_violations = {}

        # FREIO LAYER 1: No narrative files
        if self._has_narrative_files(run_data):
            violations.append('freio_l1_no_narratives')
            severity_multiplier *= 0.5
            freio_violations['layer_1_narratives'] = ['SESSION_*.md', 'EXPLORATION_LOG_*', 'DESCOBERTAS_*']
            suggestions.append("[FAIL] FREIO L1: Remove narrative file creation")

        # FREIO LAYER 2: No self-reporting
        if self._has_self_reporting(run_data):
            violations.append('freio_l2_no_self_reporting')
            severity_multiplier *= 0.6
            freio_violations['layer_2_self_reporting'] = ['log_state', 'write_summary', 'report_status']
            suggestions.append("[FAIL] FREIO L2: Remove self-reporting behavior")

        # FREIO LAYER 3: Regression safety
        if not run_data.get('regression_safe', True):
            violations.append('freio_l3_regression_broken')
            severity_multiplier *= 0.7
            freio_violations['layer_3_regression'] = ['tests_failed', 'existing_data_corrupted']
            suggestions.append("[FAIL] FREIO L3: Ensure regression tests still pass")

        # FREIO LAYER 4: Execution isolation
        if run_data.get('affected_other_runs', False):
            violations.append('freio_l4_execution_isolation_broken')
            severity_multiplier *= 0.8
            freio_violations['layer_4_isolation'] = ['side_effects_on_other_runs']
            suggestions.append("[FAIL] FREIO L4: Ensure execution isolation")

        # FREIO LAYER 5: File creation restrictions
        if self._check_file_creation_violations(run_data):
            violations.append('freio_l5_file_restrictions')
            severity_multiplier *= 0.75
            freio_violations['layer_5_files'] = ['unauthorized_file_creation']
            suggestions.append("[FAIL] FREIO L5: Check file creation restrictions")

        # FREIO LAYER 6: Memory constraints
        if run_data.get('memory_exceeded', False):
            violations.append('freio_l6_memory_constraints')
            severity_multiplier *= 0.8
            freio_violations['layer_6_memory'] = ['memory_limit_exceeded']
            suggestions.append("[FAIL] FREIO L6: Memory constraints violated")

        # FREIO LAYER 7: Proactivity rules enforcement
        proactivity_violations = self._check_proactivity_rules(run_data)
        if proactivity_violations:
            violations.append('freio_l7_proactivity_rules')
            severity_multiplier *= 0.85
            freio_violations['layer_7_proactivity'] = proactivity_violations
            suggestions.append("[FAIL] FREIO L7: Check proactivity rules compliance")

        # Compile final message
        if violations:
            num_violations = len(set(violations))  # Unique violations
            message = f"FREIO validation found {num_violations} constraint violations"
        else:
            message = "All FREIO constraints passed [OK]"

        return {
            'violations': violations,
            'severity_multiplier': severity_multiplier,
            'message': message,
            'suggestions': suggestions,
            'freio_violations': freio_violations
        }

    def _check_file_creation_violations(self, run_data: Dict) -> bool:
        """Checa se violou restrições de criação de files"""
        forbidden_extensions = ['.pyc', '.pyo', '__pycache__']
        forbidden_prefixes = ['~', '.']

        created_files = run_data.get('created_files', [])
        for file in created_files:
            # Check extensions
            if any(file.endswith(ext) for ext in forbidden_extensions):
                return True
            # Check prefixes
            basename = Path(file).name
            if any(basename.startswith(prefix) for prefix in forbidden_prefixes):
                return True

        return False

    def _check_proactivity_rules(self, run_data: Dict) -> List[str]:
        """Checa proactivity rules do PROACTIVITY_RULES.json"""
        violations = []

        if not self.proactivity_rules:
            return violations

        # Check core principles (section 1)
        if 'core_principles' in self.proactivity_rules:
            principles = self.proactivity_rules['core_principles']
            for principle in principles:
                rule_id = principle.get('id')
                # Simple check: if run violates the principle, record it
                if not self._validate_principle(run_data, principle):
                    violations.append(f"proactivity_{rule_id}")

        return violations

    def _validate_principle(self, run_data: Dict, principle: Dict) -> bool:
        """Valida um single proactivity principle"""
        # This is a simplified check - in production would be more sophisticated
        principle_name = principle.get('name', '')

        # Example: "Never log decisions" principle
        if 'Never log decisions' in principle_name:
            steps = run_data.get('steps', [])
            for step in steps:
                if 'log' in step.get('action', '').lower():
                    return False

        return True

    def _detect_narrative_files(self, run_data: Dict) -> List[str]:
        """Detecta forbidden narrative files"""
        narrative_patterns = [
            'SESSION_',
            'SUMMARY_',
            'HANDOFF_',
            'EXPLORATION_LOG_',
            'DESCOBERTAS_'
        ]

        created_files = run_data.get('created_files', [])
        narrative_files = [
            f for f in created_files
            if any(f.startswith(pattern) for pattern in narrative_patterns)
        ]

        return narrative_files

    def _has_narrative_files(self, run_data: Dict) -> bool:
        """Checa se criou narrative files"""
        return len(self._detect_narrative_files(run_data)) > 0

    def _has_self_reporting(self, run_data: Dict) -> bool:
        """Checa se fez self-reporting (logging de estado, etc)"""
        # Look for suspicious patterns in logs or outputs
        steps = run_data.get('steps', [])
        for step in steps:
            action = step.get('action', '').lower()
            if any(keyword in action for keyword in ['report', 'log_state', 'write_summary']):
                return True
        return False

    def get_validation_score(self, run_id: str) -> Optional[float]:
        """Retorna validation score de um run"""
        for result in self.validation_history:
            if result.run_id == run_id:
                return result.score
        return None

    def get_validation_summary(self) -> Dict:
        """Retorna sumário de validações com FREIO coverage"""
        if not self.validation_history:
            return {}

        passed = sum(1 for r in self.validation_history if r.status == ValidationStatus.PASS)
        passed_with_warnings = sum(1 for r in self.validation_history if r.status == ValidationStatus.PASS_WITH_WARNINGS)
        failed = sum(1 for r in self.validation_history if r.status in [ValidationStatus.FAIL, ValidationStatus.FAIL_CONSTRAINT_VIOLATION])

        avg_score = sum(r.score for r in self.validation_history) / len(self.validation_history)

        # FREIO layer violation counts
        freio_layer_stats = {}
        for result in self.validation_history:
            for layer, violations in result.freio_violations.items():
                if violations:
                    freio_layer_stats[layer] = freio_layer_stats.get(layer, 0) + len(violations)

        return {
            'total_validations': len(self.validation_history),
            'passed': passed,
            'passed_with_warnings': passed_with_warnings,
            'failed': failed,
            'avg_score': avg_score,
            'most_common_violations': self._get_most_common_violations(),
            'freio_layer_stats': freio_layer_stats
        }

    def _get_most_common_violations(self) -> Dict:
        """Retorna violações mais comuns"""
        violation_counts = {}
        for result in self.validation_history:
            for violation in result.constraints_violated:
                violation_counts[violation] = violation_counts.get(violation, 0) + 1

        return dict(sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)[:5])

    def export_validation_history(self, path: Path):
        """Salva histórico de validações"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'summary': self.get_validation_summary(),
            'validations': [asdict(r) for r in self.validation_history]
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)


# ============================================================================
# TEST & DEMO
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("RLAIF AUTO FEEDBACK - Demo")
    print("="*80 + "\n")

    validator = RLAIFAutoFeedback(enable_constraint_checking=True)

    # Simula 3 runs com diferentes resultados
    print("🧪 VALIDATING 3 RUNS:\n")

    runs = [
        {
            'run_id': 'run_001',
            'success': True,
            'duration': 45.0,
            'steps': [
                {'action': 'login', 'duration': 2.0},
                {'action': 'create_property', 'duration': 15.0},
            ],
            'created_files': [],
            'created_narratives': [],
            'other_side_effects': [],
            'regression_safe': True
        },
        {
            'run_id': 'run_002',
            'success': True,
            'duration': 125.0,  # Slow
            'steps': [
                {'action': 'login', 'duration': 2.0},
                {'action': 'create_property', 'duration': 50.0},  # Very slow
            ],
            'created_files': ['SESSION_001.md'],  # Narrative!
            'created_narratives': ['SESSION_001.md'],
            'other_side_effects': [],
            'regression_safe': True
        },
        {
            'run_id': 'run_003',
            'success': False,
            'duration': 30.0,
            'steps': [],
            'created_files': [],
            'created_narratives': [],
            'other_side_effects': [],
            'regression_safe': False
        }
    ]

    results = []
    for run in runs:
        result = validator.validate_run(run['run_id'], run)
        results.append(result)

        print(f"Run {run['run_id']}:")
        print(f"  Status: {result.status.value}")
        print(f"  Score: {result.score:.2f}")
        print(f"  Feedback: {result.feedback}")
        if result.constraints_violated:
            print(f"  Violations: {', '.join(result.constraints_violated)}")
        if result.suggestions:
            print(f"  Suggestions: {result.suggestions[0]}")
        print()

    # Summary
    print("="*80)
    print("VALIDATION SUMMARY:")
    print("="*80)

    summary = validator.get_validation_summary()
    for key, value in summary.items():
        if key != 'most_common_violations':
            print(f"  {key}: {value}")

    if summary.get('most_common_violations'):
        print(f"\n  Most common violations:")
        for violation, count in list(summary['most_common_violations'].items())[:3]:
            print(f"    - {violation}: {count} times")

    print("\n" + "="*80 + "\n")
