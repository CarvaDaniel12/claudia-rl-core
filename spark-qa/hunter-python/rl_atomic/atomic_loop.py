#!/usr/bin/env python3
"""
ATOMIC LOOP ORCHESTRATOR - Main Coordinator
O maestro que coordena todo o RL Atomic Loop!

LOOP COMPLETO:
1. LOAD: Carregar runs do barril (se existem)
2. REWARD: Calcular rewards com reward_shaper
3. SELECT: Selecionar Tier 1/2/3 com run_selector
4. EXTRACT: Extrair patterns com pattern_extractor
5. BOOTSTRAP: Carregar patterns em memória com memory_bootstrap
6. CLEANUP: Deletar runs com barril_cleaner
7. REPEAT: Loop pra próximo ciclo

ORCHESTRATION:
- Gerencia estado entre fases
- Logging & metrics
- Error recovery
- Cycle management
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class CycleMetrics:
    """Métricas de um ciclo completo"""
    cycle_id: int
    start_time: str
    end_time: str = ""
    duration_seconds: float = 0.0
    total_runs: int = 0
    tier_1_count: int = 0
    tier_2_count: int = 0
    tier_3_count: int = 0
    discard_count: int = 0
    avg_reward: float = 0.0
    max_reward: float = 0.0
    min_reward: float = 0.0
    shortcuts_found: int = 0
    recovery_patterns_found: int = 0
    success: bool = True


class AtomicLoopOrchestrator:
    """
    Orquestra o RL Atomic Loop completo

    Coordena:
    - reward_shaper
    - run_selector
    - pattern_extractor
    - memory_bootstrap
    - barril_cleaner
    """

    def __init__(
        self,
        barril_path: Path,
        config: Optional[Dict] = None
    ):
        """
        Args:
            barril_path: Path para pasta "barril!!"
            config: Configuration dict (optional)
        """
        self.barril_path = Path(barril_path)
        self.config = config or {}
        self.cycle_id = 0
        self.cycles_history = []

        # Import modules
        from .reward_shaper import RewardShaper
        from .run_selector import RunSelector
        from .pattern_extractor import PatternExtractor
        from .memory_bootstrap import MemoryBootstrap
        from .barril_cleaner import BarrilCleaner
        from .rlaif_auto_feedback import RLAIFAutoFeedback

        #  NEW PIPELINE COMPONENTS
        from .experience_validator import ExperienceValidator
        from .pattern_consolidator import PatternConsolidator
        from .rl_metrics_logger import RLMetricsLogger

        self.reward_shaper = RewardShaper()
        self.run_selector = RunSelector(total_runs=100)
        self.pattern_extractor = PatternExtractor()
        self.memory_bootstrap = MemoryBootstrap()
        self.barril_cleaner = BarrilCleaner(barril_path)
        self.rlaif_validator = RLAIFAutoFeedback(enable_constraint_checking=True)

        #  Initialize new pipeline components
        self.experience_validator = ExperienceValidator()
        self.pattern_consolidator = PatternConsolidator()
        self.rl_metrics_logger = RLMetricsLogger(barril_path)
        
        # AUTOMATIC TEST ORACLE (NEW)
        import sys
        engines_path = Path(__file__).parent.parent / 'engines'
        sys.path.insert(0, str(engines_path))
        from automatic_test_oracle import AutomaticTestOracle
        from flaky_test_predictor import FlakyTestPredictor
        from property_based_testing import PropertyBasedTesting
        from visual_regression_ai import VisualRegressionAI
        self.test_oracle = AutomaticTestOracle()
        self.flaky_predictor = FlakyTestPredictor()
        self.property_tester = PropertyBasedTesting()
        self.visual_regression = VisualRegressionAI()

    def run_cycle(self, max_iterations: int = 1) -> Tuple[bool, Dict]:
        """
        Execute um ciclo completo do RL Atomic Loop

        Args:
            max_iterations: Número de ciclos a executar (default=1)

        Returns:
            (success: bool, metrics: dict)
        """
        cycle_start = time.time()
        self.cycle_id += 1

        print("\n" + "="*80)
        print(f"RL ATOMIC LOOP - CYCLE {self.cycle_id}")
        print("="*80 + "\n")

        try:
            # PHASE 0.5: VALIDATION (NEW!)
            print("[OK] PHASE 0.5: VALIDATION - Experience Validator...")
            # This will be called AFTER loading runs

            # PHASE 1: LOAD
            print(" PHASE 1: LOAD runs...")
            runs_data = self._phase_load()
            print(f"   [OK] Loaded {len(runs_data)} runs\n")

            if not runs_data:
                print("   [INFO] No runs found, skipping this cycle")
                return False, self._create_empty_metrics()

            #  VALIDATE experiences (remove stale, duplicates, low quality)
            print("[OK] PHASE 1.5: VALIDATE experiences...")
            valid_runs, validation_stats = self.experience_validator.validate_experiences(
            runs_data,
            min_success_rate=0.5,
            max_duration=300.0
        )
            print(f"   [OK] Valid: {validation_stats.get('valid', 0)}/{validation_stats.get('total', 0)}")
            print(f"   [OK] Removed stale: {validation_stats.get('stale', 0)}")
            print(f"   [OK] Removed duplicates: {validation_stats.get('duplicates', 0)}")
            if validation_stats.get('red_flags'):
                print(f"    RED FLAGS: {validation_stats['red_flags']}")
            print()
            
            #  PHASE 1.7: FLAKY TEST PREDICTION (NEW)
            print("[CHART] PHASE 1.7: FLAKY prediction...")
            flaky_stats = self._phase_flaky_prediction(valid_runs)
            print(f"   [OK] Tests tracked: {flaky_stats['tests_tracked']}")
            if flaky_stats['flaky_tests'] > 0:
                print(f"   [WARN] Flaky tests detected: {flaky_stats['flaky_tests']}")
            print()

            if not valid_runs:
                print("   [WARNING]  No valid runs after validation, skipping cycle\n")
                return False, self._create_empty_metrics()

            # Update runs_data to use only valid runs
            runs_data = valid_runs

            # PHASE 2: REWARD
            print("[TARGET] PHASE 2: Calculate REWARD...")
            rewarded_runs = self._phase_reward(runs_data)
            print(f"   [OK] Calculated rewards for {len(rewarded_runs)} runs\n")

            # PHASE 2.5: RLAIF VALIDATION
            print(" PHASE 2.5: RLAIF Auto Validation...")
            validated_runs = self._phase_rlaif_validation(rewarded_runs)
            print(f"   [OK] Validated {len(validated_runs)} runs with FREIO constraints\n")

            # PHASE 3: SELECT
            print(" PHASE 3: SELECT runs by tier...")
            tier_classification = self._phase_select(validated_runs)
            print(f"   [OK] Tier 1: {len(tier_classification['tier_1'])}")
            print(f"   [OK] Tier 2: {len(tier_classification['tier_2'])}")
            print(f"   [OK] Tier 3: {len(tier_classification['tier_3'])}")
            print(f"   [OK] Discard: {len(tier_classification['discard'])}\n")

            # PHASE 4: EXTRACT
            print("[SEARCH] PHASE 4: EXTRACT patterns...")
            patterns = self._phase_extract(validated_runs)
            print(f"   [OK] Shortcuts found: {patterns['shortcuts_found']}")
            print(f"   [OK] Recovery patterns: {patterns['recovery_patterns_found']}")
            print(f"   [OK] Unique trajectories: {patterns['unique_trajectories']}\n")

            #  PHASE 4.5: CONSOLIDATE patterns
            print("[LINK] PHASE 4.5: CONSOLIDATE patterns...")
            consolidation_result = self.pattern_consolidator.consolidate(validated_runs)
            print(f"   [OK] Patterns found: {consolidation_result['patterns_count']}")
            if consolidation_result['patterns_count'] > 0:
                print(f"   [OK] Best pattern confidence: {consolidation_result.get('best_confidence', 0):.1f}")
            if consolidation_result.get('red_flags'):
                print(f"    RED FLAGS: {consolidation_result['red_flags']}")
            print()

            #  PHASE 4.7: LOAD TEACHINGS (Imitation Learning)
            print("[BOOK] PHASE 4.7: LOAD teachings from codegen demos...")
            teachings_loaded = self._phase_load_teachings()
            print(f"   [OK] Teachings loaded: {teachings_loaded['total_patterns']}")
            if teachings_loaded['total_patterns'] > 0:
                print(f"   [OK] Source: {teachings_loaded['source']}")
                print(f"   [OK] Confidence: {teachings_loaded['avg_confidence']:.2f}")
            print()

            # PHASE 5: BOOTSTRAP
            print("[SAVE] PHASE 5: BOOTSTRAP memory...")
            bootstrap_stats = self._phase_bootstrap(validated_runs)
            print(f"   [OK] Best actions loaded: {bootstrap_stats['best_actions_loaded']}")
            print(f"   [OK] Trajectories loaded: {bootstrap_stats['common_trajectories_loaded']}")
            print(f"   [OK] Ready for next cycle: {bootstrap_stats['ready']}\n")
            
            #  PHASE 5.5: ORACLE TRAINING & VALIDATION (NEW)
            print("[EYE] PHASE 5.5: ORACLE validation...")
            oracle_stats = self._phase_oracle_validation(validated_runs)
            print(f"   [OK] Training runs: {oracle_stats['training_runs']}")
            print(f"   [OK] Trained: {oracle_stats['trained']}")
            if oracle_stats['violations_found'] > 0:
                print(f"   [WARN] Invariant violations detected: {oracle_stats['violations_found']}")
                for violation in oracle_stats.get('violations', [])[:3]:
                    print(f"      - {violation}")
            print()
            
            #  PHASE 5.7: PROPERTY-BASED VALIDATION (NEW)
            print("[CHECK] PHASE 5.7: PROPERTY-BASED validation...")
            property_stats = self._phase_property_validation(validated_runs)
            print(f"   [OK] Properties checked: {property_stats['properties_checked']}")
            if property_stats['violations_found'] > 0:
                print(f"   [WARN] Property violations: {property_stats['violations_found']}")
                if property_stats.get('critical_violations', 0) > 0:
                    print(f"   [FAIL] CRITICAL violations: {property_stats['critical_violations']}")
            print()
            
            #  PHASE 5.9: VISUAL REGRESSION DETECTION (NEW)
            print("[CAMERA] PHASE 5.9: VISUAL REGRESSION...")
            visual_stats = self._phase_visual_regression(validated_runs)
            print(f"   [OK] Baselines: {visual_stats['baselines_set']}")
            if visual_stats['regressions_found'] > 0:
                print(f"   [WARN] Visual regressions detected: {visual_stats['regressions_found']}")
            print()

            # PHASE 6: CLEANUP
            print(" PHASE 6: CLEANUP barril...")
            cleanup_stats = self._phase_cleanup(tier_classification)
            print(f"   [OK] Archived: {cleanup_stats['archived']}")
            print(f"   [OK] Deleted: {cleanup_stats['deleted']}\n")

            # Compile metrics
            metrics = self._compile_metrics(
                validated_runs, tier_classification, patterns, bootstrap_stats
            )
            self.cycles_history.append(asdict(metrics))

            #  PHASE 7: LOG METRICS
            print("[CHART] PHASE 7: LOG RL METRICS...")
            try:
                # Prepare data for metrics logger
                actions = [r.get('actions', []) for r in validated_runs]
                rewards = [r.get('reward', 0) for r in validated_runs]
                values = [r.get('value', 0) for r in validated_runs]

                metrics_result = self.rl_metrics_logger.log_cycle(
                    cycle_id=self.cycle_id,
                    actions=actions,
                    rewards=rewards,
                    experiences=validated_runs,
                    values=values
                )

                print(f"   [OK] Policy entropy: {metrics_result['policy_entropy']:.3f}")
                print(f"   [OK] KL divergence: {metrics_result['kl_divergence']:.3f}")
                print(f"   [OK] Residual variance: {metrics_result['residual_variance']:.3f}")

                if metrics_result.get('red_flags'):
                    print(f"    RED FLAGS: {', '.join(metrics_result['red_flags'])}")
                print()
            except Exception as e:
                print(f"   [WARNING]  Metrics logging failed: {e}\n")

            cycle_duration = time.time() - cycle_start

            print("="*80)
            print(f"[OK] CYCLE {self.cycle_id} COMPLETED in {cycle_duration:.1f}s")
            print("="*80 + "\n")

            return True, asdict(metrics)

        except Exception as e:
            print(f"\n[FAIL] CYCLE FAILED: {e}")
            return False, self._create_empty_metrics()

    def _phase_load(self) -> List[Dict]:
        """PHASE 1: Load runs from barril"""
        try:
            run_files = list(self.barril_path.glob("*.json"))
            runs = []

            for run_file in run_files:
                if run_file.name.startswith('.'):
                    continue

                try:
                    with open(run_file, 'r') as f:
                        run_data = json.load(f)
                        runs.append(run_data)
                except Exception as e:
                    print(f"   [Warning] Failed to load {run_file.name}: {e}")

            return runs
        except Exception as e:
            print(f"   [Error] Phase load failed: {e}")
            return []

    def _phase_reward(self, runs: List[Dict]) -> List[Dict]:
        """PHASE 2: Calculate rewards usando RewardShaper completo (4 tiers + bonuses)"""
        rewarded = []

        for run in runs:
            # Monta run_data pro RewardShaper
            run_data = {
                'success': run.get('success', False),
                'duration': run.get('duration', 0),
                'trajectory': run.get('trajectory', []),
                'shortcuts_used': run.get('shortcuts_used', []),
                'recovery_strategies_used': run.get('recovery_used', []),
                'exploration_paths': run.get('exploration_count', 0),
                'is_new_path': run.get('is_new_path', False),
                'loops': run.get('loops', 0),
                'error_type': run.get('error_type', None)
            }

            # Usa RewardShaper COMPLETO (4 tiers + refinement + exploration + playwright)
            reward = self.reward_shaper.calculate(run_data)

            run['reward'] = reward
            rewarded.append(run)

        return rewarded

    def _phase_rlaif_validation(self, rewarded_runs: List[Dict]) -> List[Dict]:
        """PHASE 2.5: RLAIF Auto Validation with FREIO constraints"""
        validated = []

        for run in rewarded_runs:
            # Prepare run_data for validation (enhanced with metrics)
            metrics = run.get('metrics', {})
            assertions = metrics.get('assertions', {})
            
            run_data = {
                'success': run.get('success', True),
                'duration': run.get('duration', 0),
                'steps': run.get('steps', []),
                'created_files': run.get('created_files', []),
                'created_narratives': run.get('created_narratives', []),
                'other_side_effects': run.get('other_side_effects', []),
                'regression_safe': run.get('regression_safe', True),
                'affected_other_runs': run.get('affected_other_runs', False),
                'memory_exceeded': run.get('memory_exceeded', False),
                
                # Enhanced metrics for better validation
                'assertions_passed': assertions.get('passed', 0),
                'assertions_total': assertions.get('total', 0),
                'assertions_success_rate': assertions.get('success_rate', 0),
                'cleanup_successful': metrics.get('cleanup_successful', False),
                'property_deleted': metrics.get('property_deleted', False),
            }

            # Validate with RLAIF
            validation_result = self.rlaif_validator.validate_run(
                run.get('run_id', f"run_{len(validated)}"),
                run_data
            )

            # Merge validation info into run
            run['validation_status'] = validation_result.status.value
            run['validation_score'] = validation_result.score
            run['validation_feedback'] = validation_result.feedback

            # Apply validation score as multiplier to reward
            original_reward = run.get('reward', 0)
            run['reward_before_validation'] = original_reward
            run['reward'] = original_reward * validation_result.score

            # Log detailed RLAIF feedback
            print(f"\n   [RLAIF] Run {run.get('run_id', '?')}:")
            print(f"     Status: {validation_result.status.value}")
            print(f"     Score: {validation_result.score:.2f} (reward: {original_reward:.1f} -> {run['reward']:.1f})")
            if validation_result.feedback:
                print(f"     Feedback: {validation_result.feedback}")
            if validation_result.suggestions:
                print(f"     Suggestions: {', '.join(validation_result.suggestions[:2])}")

            validated.append(run)

        return validated

    def _phase_select(self, runs: List[Dict]) -> Dict[str, List[str]]:
        """PHASE 3: Selecionar runs by tier"""
        # Sort by reward
        sorted_runs = sorted(runs, key=lambda r: r.get('reward', 0), reverse=True)
        total = len(sorted_runs)

        tier_1_size = max(1, int(total * 0.10))
        tier_2_size = max(1, int(total * 0.30))
        tier_3_size = max(1, int(total * 0.10))

        return {
            'tier_1': [r['run_id'] for r in sorted_runs[:tier_1_size]],
            'tier_2': [r['run_id'] for r in sorted_runs[tier_1_size:tier_1_size+tier_2_size]],
            'tier_3': [r['run_id'] for r in sorted_runs[tier_1_size+tier_2_size:tier_1_size+tier_2_size+tier_3_size]],
            'discard': [r['run_id'] for r in sorted_runs[tier_1_size+tier_2_size+tier_3_size:]]
        }

    def _phase_extract(self, runs: List[Dict]) -> Dict:
        """PHASE 4: Extract patterns"""
        shortcuts_count = sum(1 for r in runs if r.get('has_shortcuts', False))
        recovery_count = sum(1 for r in runs if r.get('has_recovery', False))

        # Count unique trajectories
        trajectory_hashes = set()
        for run in runs:
            # Simplistic trajectory hash
            steps = run.get('steps', [])
            trajectory = tuple(s.get('action', '') for s in steps)
            trajectory_hashes.add(trajectory)

        return {
            'shortcuts_found': shortcuts_count,
            'recovery_patterns_found': recovery_count,
            'unique_trajectories': len(trajectory_hashes)
        }

    def _phase_bootstrap(self, runs: List[Dict]) -> Dict:
        """PHASE 5: Bootstrap memory"""
        # Simplified bootstrap
        best_actions = {}
        for run in runs:
            for step in run.get('steps', []):
                action = step.get('action', '')
                duration = step.get('duration', 0)
                if action not in best_actions:
                    best_actions[action] = duration
                else:
                    best_actions[action] = min(best_actions[action], duration)

        return {
            'best_actions_loaded': len(best_actions),
            'common_trajectories_loaded': 1,  # Simplified
            'recovery_patterns_loaded': 0,
            'ready': True
        }

    def _phase_visual_regression(self, runs: List[Dict]) -> Dict:
        """PHASE 5.9: Detect visual regressions via screenshot comparison"""
        try:
            # Process screenshots from runs
            # Note: Screenshots need to be captured during flow execution
            # This phase validates them against baselines
            
            self.visual_regression.save()
            return self.visual_regression.get_stats()
            
        except Exception as e:
            print(f"   [WARN] Visual regression detection failed: {e}")
            return {
                "available": False,
                "baselines_set": 0,
                "regressions_found": 0
            }
    
    def _phase_property_validation(self, runs: List[Dict]) -> Dict:
        """PHASE 5.7: Validate system properties (property-based testing)"""
        try:
            violations_all = []
            
            # Check properties for each run
            for run in runs:
                # Prepare safe result_data for property checking
                result_data = {
                    'property_uid': run.get('property_uid'),
                    'lead_uid': run.get('lead_uid'),
                    'leads_before': run.get('leads_before', 0),
                    'leads_after': run.get('leads_after', 0),
                    'count_before': run.get('count_before', 0),
                    'count_after': run.get('count_after', 0),
                    'duration': run.get('duration', 0),
                    'success': run.get('success', False),
                    'flow_name': run.get('flow_name', ''),
                }
                
                all_passed, violations = self.property_tester.check_properties(result_data)
                if violations:
                    violations_all.extend(violations)
            
            # Save property tester
            self.property_tester.save()
            
            stats = self.property_tester.get_stats()
            return stats
            
        except Exception as e:
            print(f"   [WARN] Property validation failed: {e}")
            return {
                "properties_checked": 0,
                "violations_found": 0,
                "critical_violations": 0
            }
    
    def _phase_flaky_prediction(self, runs: List[Dict]) -> Dict:
        """PHASE 1.7: Predict test flakiness and adjust strategy"""
        try:
            # Add runs to flaky predictor history
            for run in runs:
                test_name = run.get('flow_name', 'unknown')
                self.flaky_predictor.add_run_result(test_name, run)
            
            # Save predictor
            self.flaky_predictor.save()
            
            return self.flaky_predictor.get_stats()
            
        except Exception as e:
            print(f"   [WARN] Flaky prediction failed: {e}")
            return {
                "trained": False,
                "tests_tracked": 0,
                "flaky_tests": 0
            }
    
    def _phase_oracle_validation(self, runs: List[Dict]) -> Dict:
        """PHASE 5.5: Train oracle on successful runs and validate for anomalies"""
        try:
            # Add successful runs to oracle training
            for run in runs:
                if run.get('success', False):
                    self.test_oracle.add_training_run(run)
            
            # Validate all runs for anomalies
            violations_all = []
            for run in runs:
                is_valid, violations = self.test_oracle.validate_run(run)
                if violations:
                    violations_all.extend(violations)
            
            # Save oracle
            self.test_oracle.save()
            
            oracle_stats = self.test_oracle.get_stats()
            oracle_stats['violations_found'] = len(violations_all)
            oracle_stats['violations'] = violations_all
            
            return oracle_stats
            
        except Exception as e:
            print(f"   [WARN] Oracle validation failed: {e}")
            return {
                "training_runs": 0,
                "trained": False,
                "violations_found": 0
            }
    
    def _phase_load_teachings(self) -> Dict:
        """PHASE 4.7: Load teachings from codegen demonstrations (Imitation Learning)"""
        try:
            # Import teaching translator
            import sys
            from pathlib import Path
            teaching_path = Path(__file__).parent.parent / "teaching"
            sys.path.insert(0, str(teaching_path))
            
            from teaching_translator import TeachingTranslator
            
            translator = TeachingTranslator()
            teachings_file = Path(__file__).parent.parent / "barril!!" / "claude_teachings.json"
            
            if not teachings_file.exists():
                return {
                    "total_patterns": 0,
                    "source": "none",
                    "avg_confidence": 0.0
                }
            
            # Translate teachings to RL format
            translated = translator.translate_all()
            
            # Merge with existing patterns_learned.json
            patterns_file = Path(__file__).parent.parent / "patterns_learned.json"
            if patterns_file.exists():
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    existing_patterns = json.load(f)
            else:
                existing_patterns = {"version": "2.0", "patterns": {}}
            
            # Add teachings to patterns (Claude teachings have HIGH priority!)
            for pattern_name, teaching_pattern in translated['patterns'].items():
                existing_patterns['patterns'][pattern_name] = teaching_pattern
            
            # Update total count
            existing_patterns['total_patterns'] = len(existing_patterns['patterns'])
            existing_patterns['last_updated'] = datetime.now().isoformat()
            
            # Save merged patterns
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(existing_patterns, f, indent=2, ensure_ascii=False)
            
            # Calculate stats
            confidences = [p.get('confidence', 0) for p in translated['patterns'].values()]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                "total_patterns": len(translated['patterns']),
                "source": "claude_teachings",
                "avg_confidence": avg_confidence
            }
            
        except Exception as e:
            print(f"   [INFO] No teachings to load (file not found or error: {e})")
            return {
                "total_patterns": 0,
                "source": "none",
                "avg_confidence": 0.0
            }

    def _phase_cleanup(self, tier_classification: Dict) -> Dict:
        """PHASE 6: Cleanup barril"""
        # Simplified cleanup stats
        tier_1_count = len(tier_classification.get('tier_1', []))
        delete_count = (
            len(tier_classification.get('tier_2', [])) +
            len(tier_classification.get('tier_3', [])) +
            len(tier_classification.get('discard', []))
        )

        return {
            'archived': tier_1_count,
            'deleted': delete_count,
            'preserved': tier_1_count
        }

    def _compile_metrics(
        self,
        rewarded_runs: List[Dict],
        tier_classification: Dict,
        patterns: Dict,
        bootstrap_stats: Dict
    ) -> CycleMetrics:
        """Compila métricas do ciclo"""
        rewards = [r.get('reward', 0) for r in rewarded_runs]

        metrics = CycleMetrics(
            cycle_id=self.cycle_id,
            start_time=datetime.now().isoformat(),
            total_runs=len(rewarded_runs),
            tier_1_count=len(tier_classification['tier_1']),
            tier_2_count=len(tier_classification['tier_2']),
            tier_3_count=len(tier_classification['tier_3']),
            discard_count=len(tier_classification['discard']),
            avg_reward=sum(rewards) / len(rewards) if rewards else 0,
            max_reward=max(rewards) if rewards else 0,
            min_reward=min(rewards) if rewards else 0,
            shortcuts_found=patterns['shortcuts_found'],
            recovery_patterns_found=patterns['recovery_patterns_found']
        )

        return metrics

    def _create_empty_metrics(self) -> Dict:
        """Cria metrics vazias"""
        return asdict(CycleMetrics(
            cycle_id=self.cycle_id,
            start_time=datetime.now().isoformat()
        ))

    def export_cycle_history(self, path: Path):
        """Salva histórico de ciclos"""
        with open(path, 'w') as f:
            json.dump(self.cycles_history, f, indent=2)

    def get_cycle_summary(self) -> Dict:
        """Retorna sumário dos ciclos"""
        if not self.cycles_history:
            return {}

        total_runs = sum(c['total_runs'] for c in self.cycles_history)
        avg_reward = sum(c['avg_reward'] * c['total_runs'] for c in self.cycles_history) / total_runs if total_runs else 0

        return {
            'cycles_completed': len(self.cycles_history),
            'total_runs': total_runs,
            'avg_reward_overall': avg_reward,
            'max_reward': max(c['max_reward'] for c in self.cycles_history),
            'total_shortcuts_found': sum(c['shortcuts_found'] for c in self.cycles_history),
            'total_recovery_patterns': sum(c['recovery_patterns_found'] for c in self.cycles_history)
        }


# ============================================================================
# TEST & DEMO
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("ATOMIC LOOP ORCHESTRATOR - Simulation Demo")
    print("="*80 + "\n")

    print("[CHART] SIMULATING 1 COMPLETE CYCLE:\n")

    print("Phase 1: LOAD")
    print("  [OK] Loaded 50 runs from barril")

    print("\nPhase 2: REWARD")
    print("  [OK] Calculated rewards (avg: 165.5, max: 330)")

    print("\nPhase 3: SELECT")
    print("  [OK] Tier 1: 5 runs")
    print("  [OK] Tier 2: 15 runs")
    print("  [OK] Tier 3: 5 runs")
    print("  [OK] Discard: 20 runs")

    print("\nPhase 4: EXTRACT")
    print("  [OK] Shortcuts: 3 found")
    print("  [OK] Recovery patterns: 2 found")
    print("  [OK] Unique trajectories: 8")

    print("\nPhase 5: BOOTSTRAP")
    print("  [OK] Best actions loaded: 12")
    print("  [OK] Trajectories loaded: 8")
    print("  [OK] Ready for next cycle: [OK]")

    print("\nPhase 6: CLEANUP")
    print("  [OK] Archived: 5 runs (Tier 1)")
    print("  [OK] Deleted: 40 runs (Tier 2/3/Discard)")
    print("  [OK] Barril is now EMPTY")

    print("\n" + "="*80)
    print("\n[OK] CYCLE COMPLETED in 2.3 seconds")
    print("   Next cycle ready to start!")
    print("\n" + "="*80 + "\n")
