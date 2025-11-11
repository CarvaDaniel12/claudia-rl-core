"""
Analisa checkpoints de training e retorna resumo conciso

Usage: python analyze_training.py
"""
import json
from pathlib import Path
from datetime import datetime


def analyze_training():
    print("="*70)
    print("TRAINING ANALYSIS")
    print("="*70)
    
    barril = Path(__file__).parent.parent.parent / 'barril!!'
    checkpoints_dir = Path(__file__).parent
    
    # Count runs
    phase2_runs = list(barril.glob("Phase2_*.json"))
    print(f"\nTotal runs in barril: {len(phase2_runs)}")
    
    # Read checkpoints
    checkpoints = sorted(checkpoints_dir.glob("checkpoint_*.json"))
    
    if checkpoints:
        print(f"\nCheckpoints found: {len(checkpoints)}")
        
        for cp_file in checkpoints:
            with open(cp_file) as f:
                cp = json.load(f)
            print(f"\n{cp_file.name}:")
            print(f"  Completed: {cp.get('runs_completed', 0)}")
            print(f"  Success: {cp.get('runs_success', 0)}")
            print(f"  Failed: {cp.get('runs_failed', 0)}")
            print(f"  Avg duration: {cp.get('avg_duration', 0):.1f}s")
    
    # Check patterns learned
    patterns_file = barril / 'patterns_learned.json'
    if patterns_file.exists():
        with open(patterns_file) as f:
            patterns = json.load(f)
        print(f"\nPatterns learned: {patterns.get('total_patterns', 0)}")
    
    # Latest 3 runs detail
    latest_runs = sorted(phase2_runs, key=lambda x: x.stat().st_mtime, reverse=True)[:3]
    
    if latest_runs:
        print(f"\nLatest 3 runs:")
        for run_file in latest_runs:
            with open(run_file) as f:
                run = json.load(f)
            print(f"\n{run_file.name}:")
            print(f"  Success: {run.get('success', False)}")
            print(f"  Duration: {run.get('duration', 0):.1f}s")
            print(f"  Steps: {run.get('total_steps', 0)}")
            if 'selector_stats' in run:
                print(f"  Selector success: {run['selector_stats'].get('success_rate', 0):.1f}%")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    analyze_training()

