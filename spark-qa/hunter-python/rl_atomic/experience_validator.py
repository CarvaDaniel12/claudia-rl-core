#!/usr/bin/env python3
"""
[SEARCH] EXPERIENCE VALIDATOR - Valida qualidade e freshness de experiences

PROBLEMA IDENTIFICADO:
- 215 experiences em experience_buffer.json
- Não sabemos quantas são stale (>24h)
- Não sabemos quantas são duplicatas
- Não sabemos qual a qualidade real

VALIDAÇÕES:
1. Freshness: Remove experiences >24h (stale)
2. Duplicates: Detecta trajectories duplicadas
3. Quality: Valida success_rate e duration
4. Completeness: Verifica campos obrigatórios

REFERÊNCIA: Andy Jones - "Sample staleness must be stable"
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib


class ExperienceValidator:
    """
    Valida experiences antes de usar no RL

    Remove:
    - Stale experiences (>24h)
    - Duplicates (mesma trajectory)
    - Low quality (muito lentas, sem sucesso)
    - Incomplete (campos faltando)
    """

    def __init__(self, max_age_hours: int = 24):
        """
        Args:
            max_age_hours: Máximo age para considerar experience válida
        """
        self.max_age_hours = max_age_hours
        self.stats = {
            'total': 0,
            'valid': 0,
            'stale': 0,
            'duplicates': 0,
            'low_quality': 0,
            'incomplete': 0
        }

    def validate_experiences(
        self,
        experiences: List[Dict],
        min_success_rate: float = 0.5,
        max_duration: float = 300.0
    ) -> Tuple[List[Dict], Dict]:
        """
        Valida lista de experiences e retorna apenas válidas

        Args:
            experiences: Lista de experiences
            min_success_rate: Success rate mínimo (0.0-1.0)
            max_duration: Duração máxima em segundos

        Returns:
            (valid_experiences, validation_stats)
        """
        print("\n" + "="*70)
        print("[SEARCH] EXPERIENCE VALIDATOR - Starting validation")
        print("="*70)

        self.stats['total'] = len(experiences)
        print(f"\n[CHART] Total experiences to validate: {self.stats['total']}")

        # Phase 1: Freshness check
        fresh_experiences = self._filter_by_freshness(experiences)

        # Phase 2: Duplicate detection
        unique_experiences = self._filter_duplicates(fresh_experiences)

        # Phase 3: Quality check
        quality_experiences = self._filter_by_quality(
            unique_experiences,
            min_success_rate,
            max_duration
        )

        # Phase 4: Completeness check
        valid_experiences = self._filter_incomplete(quality_experiences)

        self.stats['valid'] = len(valid_experiences)

        # Generate report
        self._print_report()

        return valid_experiences, self.stats.copy()

    def _filter_by_freshness(self, experiences: List[Dict]) -> List[Dict]:
        """Remove stale experiences (>max_age_hours)"""
        print(f"\n Phase 1: Freshness Check (max age: {self.max_age_hours}h)")

        now = datetime.now()
        fresh = []

        for exp in experiences:
            timestamp_str = exp.get('timestamp')
            if not timestamp_str:
                self.stats['stale'] += 1
                continue

            try:
                exp_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                # Remove timezone info for comparison
                if exp_time.tzinfo:
                    exp_time = exp_time.replace(tzinfo=None)

                age_hours = (now - exp_time).total_seconds() / 3600

                if age_hours <= self.max_age_hours:
                    fresh.append(exp)
                else:
                    self.stats['stale'] += 1

            except Exception as e:
                print(f"   [WARNING]  Could not parse timestamp: {timestamp_str} ({e})")
                self.stats['stale'] += 1

        print(f"   [OK] Fresh: {len(fresh)}")
        print(f"   [FAIL] Stale (>{self.max_age_hours}h): {self.stats['stale']}")

        return fresh

    def _filter_duplicates(self, experiences: List[Dict]) -> List[Dict]:
        """Remove duplicate trajectories"""
        print(f"\n[SEARCH] Phase 2: Duplicate Detection")

        seen_signatures = set()
        unique = []

        for exp in experiences:
            signature = self._trajectory_signature(exp)

            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique.append(exp)
            else:
                self.stats['duplicates'] += 1

        print(f"   [OK] Unique: {len(unique)}")
        print(f"   [FAIL] Duplicates: {self.stats['duplicates']}")

        return unique

    def _trajectory_signature(self, experience: Dict) -> str:
        """
        Gera signature única para uma trajectory

        Baseado em:
        - Sequence de actions
        - Flow name
        - Success/failure
        """
        actions = experience.get('actions', [])

        # Extract action sequence
        action_seq = []
        for action in actions:
            if isinstance(action, dict):
                action_name = action.get('action', action.get('step', 'unknown'))
            else:
                action_name = str(action)
            action_seq.append(action_name)

        # Combine com flow name e success
        flow_name = experience.get('flow_name', 'unknown')
        success = experience.get('success', False)

        signature_str = f"{flow_name}:{success}:{'|'.join(action_seq)}"

        # Hash para evitar strings muito longas
        return hashlib.md5(signature_str.encode()).hexdigest()

    def _filter_by_quality(
        self,
        experiences: List[Dict],
        min_success_rate: float,
        max_duration: float
    ) -> List[Dict]:
        """Remove low quality experiences"""
        print(f"\n[STAR] Phase 3: Quality Check")
        print(f"   Min success rate: {min_success_rate:.0%}")
        print(f"   Max duration: {max_duration:.1f}s")

        quality = []

        for exp in experiences:
            success = exp.get('success', False)
            duration = exp.get('duration', 999999)

            # Quality criteria
            is_success = success if isinstance(success, bool) else success >= min_success_rate
            is_fast_enough = duration <= max_duration

            if is_success and is_fast_enough:
                quality.append(exp)
            else:
                self.stats['low_quality'] += 1

        print(f"   [OK] High quality: {len(quality)}")
        print(f"   [FAIL] Low quality: {self.stats['low_quality']}")

        return quality

    def _filter_incomplete(self, experiences: List[Dict]) -> List[Dict]:
        """Remove incomplete experiences (missing required fields)"""
        print(f"\n[LIST] Phase 4: Completeness Check")

        required_fields = ['timestamp', 'flow_name', 'actions', 'success', 'duration']
        complete = []

        for exp in experiences:
            missing_fields = [f for f in required_fields if f not in exp]

            if not missing_fields:
                complete.append(exp)
            else:
                self.stats['incomplete'] += 1

        print(f"   [OK] Complete: {len(complete)}")
        print(f"   [FAIL] Incomplete: {self.stats['incomplete']}")

        return complete

    def _print_report(self):
        """Print validation report"""
        print("\n" + "="*70)
        print("[CHART] VALIDATION REPORT")
        print("="*70)

        total = self.stats['total']
        valid = self.stats['valid']

        print(f"\n  Total experiences: {total}")
        print(f"  Valid experiences: {valid} ({valid/total*100:.1f}%)\n")

        print(f"  Removed:")
        print(f"    • Stale (>{self.max_age_hours}h): {self.stats['stale']}")
        print(f"    • Duplicates: {self.stats['duplicates']}")
        print(f"    • Low quality: {self.stats['low_quality']}")
        print(f"    • Incomplete: {self.stats['incomplete']}")

        # RED FLAGS
        if self.stats['stale'] > total * 0.5:
            print(f"\n  [WARNING]  RED FLAG: >50% stale experiences!")
            print(f"      Consider running more frequent training cycles")

        if self.stats['duplicates'] > total * 0.3:
            print(f"\n  [WARNING]  RED FLAG: >30% duplicates!")
            print(f"      RL is not exploring enough - stuck in local optima")

        print("\n" + "="*70 + "\n")


# ============================================================================
# DEMO & TEST
# ============================================================================

def demo():
    """Demo de validação de experiences"""
    print("[SEARCH] EXPERIENCE VALIDATOR DEMO\n")

    # Simulate experiences com diferentes problemas
    now = datetime.now()
    old_time = now - timedelta(hours=30)  # Stale!

    fake_experiences = [
        # Valid experience
        {
            'timestamp': now.isoformat(),
            'flow_name': 'PropertyCreation',
            'actions': [
                {'action': 'login'},
                {'action': 'navigate'},
                {'action': 'fill_form'}
            ],
            'success': True,
            'duration': 25.5
        },
        # Duplicate of above
        {
            'timestamp': now.isoformat(),
            'flow_name': 'PropertyCreation',
            'actions': [
                {'action': 'login'},
                {'action': 'navigate'},
                {'action': 'fill_form'}
            ],
            'success': True,
            'duration': 26.2
        },
        # Stale experience
        {
            'timestamp': old_time.isoformat(),
            'flow_name': 'PropertyCreation',
            'actions': [{'action': 'login'}],
            'success': True,
            'duration': 30.0
        },
        # Low quality (too slow)
        {
            'timestamp': now.isoformat(),
            'flow_name': 'PropertyCreation',
            'actions': [{'action': 'login'}],
            'success': True,
            'duration': 500.0  # Too slow!
        },
        # Incomplete (missing duration)
        {
            'timestamp': now.isoformat(),
            'flow_name': 'PropertyCreation',
            'actions': [{'action': 'login'}],
            'success': True
            # duration missing!
        }
    ]

    validator = ExperienceValidator(max_age_hours=24)
    valid_experiences, stats = validator.validate_experiences(
        fake_experiences,
        min_success_rate=0.5,
        max_duration=300.0
    )

    print(f"[OK] Validation complete!")
    print(f"   Input: {len(fake_experiences)} experiences")
    print(f"   Output: {len(valid_experiences)} valid experiences")


if __name__ == "__main__":
    demo()
