#!/usr/bin/env python3
"""
BARRIL CLEANER - Organize & Delete Runs by Tier
Limpa barril!! ao final de cada ciclo

Lógica:
- Archive Tier 1 runs (melhores) pra referência
- Delete Tier 2/3/DISCARD (depois de extrair patterns)
- Deixar barril vazio pro próximo ciclo
- Manter apenas metadata pra learning

EM PORTUGUÊS: "Barril" = folder com todos os JSON files dos runs
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class BarrilCleaner:
    """
    Limpa barril!! (folder de runs)
    """

    def __init__(self, barril_path: Path):
        """
        Args:
            barril_path: Path para pasta "barril!!" com runs
        """
        self.barril_path = Path(barril_path)
        self.archive_path = self.barril_path.parent / "_archives" / "runs_archive"
        self.metadata_path = self.barril_path.parent / ".rl_atomic_metadata"

        # Criar directories se não existem
        self.archive_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path.mkdir(parents=True, exist_ok=True)

    def organize_by_tier(
        self,
        tier_classification: Dict
    ) -> Dict[str, int]:
        """
        Organiza runs em folders by tier

        Args:
            tier_classification: {
                'tier_1': [run_ids...],
                'tier_2': [run_ids...],
                'tier_3': [run_ids...],
                'discard': [run_ids...]
            }

        Returns:
            {
                'archived': count,
                'deleted': count,
                'preserved': count
            }
        """
        stats = {'archived': 0, 'deleted': 0, 'preserved': 0}

        # TIER 1: Archive pra referência
        tier_1_archive = self.archive_path / f"tier_1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        tier_1_archive.mkdir(parents=True, exist_ok=True)

        for run_id in tier_classification.get('tier_1', []):
            if self._move_run_to_archive(run_id, tier_1_archive):
                stats['archived'] += 1

        # TIER 2/3/DISCARD: Delete (depois de extrair patterns)
        for tier in ['tier_2', 'tier_3', 'discard']:
            for run_id in tier_classification.get(tier, []):
                if self._delete_run(run_id):
                    stats['deleted'] += 1

        stats['preserved'] = stats['archived']

        return stats

    def _move_run_to_archive(self, run_id: str, archive_path: Path) -> bool:
        """Move run file pra archive"""
        try:
            # Procura arquivo (pode ser .json, .txt, etc)
            run_files = list(self.barril_path.glob(f"{run_id}*"))

            for run_file in run_files:
                dest = archive_path / run_file.name
                shutil.move(str(run_file), str(dest))
                return True

            return False
        except Exception as e:
            print(f"  [Archive Error] {run_id}: {e}")
            return False

    def _delete_run(self, run_id: str) -> bool:
        """Delete run file from barril"""
        try:
            run_files = list(self.barril_path.glob(f"{run_id}*"))

            for run_file in run_files:
                run_file.unlink()
                return True

            return False
        except Exception as e:
            print(f"  [Delete Error] {run_id}: {e}")
            return False

    def create_metadata_summary(
        self,
        tier_classification: Dict,
        patterns_extracted: Dict,
        run_summaries: Dict
    ) -> Path:
        """
        Cria arquivo de metadata pra próximo ciclo

        Inclui:
        - Tier classification
        - Extracted patterns
        - Run summaries (avg reward, etc)
        """
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'cycle_info': {
                'tier_1_count': len(tier_classification.get('tier_1', [])),
                'tier_2_count': len(tier_classification.get('tier_2', [])),
                'tier_3_count': len(tier_classification.get('tier_3', [])),
                'discard_count': len(tier_classification.get('discard', [])),
            },
            'run_summaries': run_summaries,
            'patterns_extracted': patterns_extracted,
        }

        metadata_file = self.metadata_path / f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        return metadata_file

    def cleanup_barril(self) -> Dict[str, int]:
        """
        Cleanup completo do barril

        Deleta TODOS os runs (use só no final do ciclo!)
        """
        stats = {'deleted': 0, 'errors': 0}

        try:
            # List todos os arquivos
            run_files = list(self.barril_path.glob("*"))

            for run_file in run_files:
                if run_file.name.startswith('.'):
                    continue  # Skip hidden files

                try:
                    if run_file.is_file():
                        run_file.unlink()
                        stats['deleted'] += 1
                    elif run_file.is_dir():
                        shutil.rmtree(run_file)
                        stats['deleted'] += 1
                except Exception as e:
                    print(f"  [Cleanup Error] {run_file.name}: {e}")
                    stats['errors'] += 1

        except Exception as e:
            print(f"  [Cleanup Error] {e}")
            stats['errors'] += 1

        return stats

    def get_barril_size(self) -> Dict:
        """Retorna info sobre tamanho do barril"""
        try:
            run_files = list(self.barril_path.glob("*"))
            run_files = [f for f in run_files if not f.name.startswith('.')]

            total_size = sum(f.stat().st_size for f in run_files if f.is_file())

            return {
                'file_count': len(run_files),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'files': [f.name for f in run_files[:10]]  # First 10
            }
        except Exception as e:
            print(f"  [Size Error] {e}")
            return {'file_count': 0, 'total_size_mb': 0, 'files': []}

    def get_archive_summary(self) -> Dict:
        """Retorna sumário de archives"""
        archive_dirs = list(self.archive_path.glob("tier_1_*"))

        summary = {
            'total_archives': len(archive_dirs),
            'archives': []
        }

        for archive_dir in archive_dirs[-5:]:  # Last 5 archives
            files = list(archive_dir.glob("*"))
            summary['archives'].append({
                'name': archive_dir.name,
                'files_count': len(files)
            })

        return summary


# ============================================================================
# TEST & DEMO
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("BARRIL CLEANER - Cleanup Demo")
    print("="*80 + "\n")

    # Demo: Simular tier classification
    tier_classification = {
        'tier_1': ['run_001', 'run_002', 'run_003', 'run_004', 'run_005'],
        'tier_2': ['run_006', 'run_007', 'run_008', 'run_009', 'run_010'],
        'tier_3': ['run_011', 'run_012'],
        'discard': ['run_013', 'run_014', 'run_015']
    }

    patterns_extracted = {
        'shortcuts_found': 3,
        'recovery_patterns_found': 2,
        'trajectory_patterns': 5
    }

    run_summaries = {
        'total_runs': 15,
        'avg_reward': 165.5,
        'avg_duration': 52.3,
        'success_rate': 0.87
    }

    print("[CHART] TIER CLASSIFICATION:")
    print(f"  Tier 1: {len(tier_classification['tier_1'])} runs (archive)")
    print(f"  Tier 2: {len(tier_classification['tier_2'])} runs (delete)")
    print(f"  Tier 3: {len(tier_classification['tier_3'])} runs (delete)")
    print(f"  Discard: {len(tier_classification['discard'])} runs (delete)")

    print(f"\n[TRENDING_UP] PATTERNS EXTRACTED:")
    for key, value in patterns_extracted.items():
        print(f"  {key}: {value}")

    print(f"\n[CHART] RUN SUMMARIES:")
    for key, value in run_summaries.items():
        print(f"  {key}: {value}")

    print("\n" + ""*80)
    print("\n CLEANUP SIMULATION:")
    print("  [OK] Tier 1 runs (5) → ARCHIVED")
    print("  [OK] Tier 2 runs (5) → DELETED")
    print("  [OK] Tier 3 runs (2) → DELETED")
    print("  [OK] Discard runs (3) → DELETED")
    print("  [OK] Total deleted: 10")
    print("  [OK] Barril is now EMPTY")

    print("\n" + "="*80)
    print("\n[SAVE] METADATA PRESERVED:")
    print("  [OK] cycle_20251105_120000.json created")
    print("    - Tier classification")
    print("    - Run summaries")
    print("    - Extracted patterns")

    print("\n[PACKAGE] ARCHIVES:")
    print("  [OK] tier_1_20251105_120000/ (5 files)")
    print("    Preserved for reference & reuse")

    print("\n" + "="*80 + "\n")
