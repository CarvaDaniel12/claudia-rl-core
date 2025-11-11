"""
TRAINING: 200 runs usando flow_e2e_phase2.py COMPLETO

Executa flow Phase 2 completo (37 assertions, 10 steps, multi-selector)
em loop com RL processing contínuo
"""
import sys
import time
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from rl_atomic.atomic_loop import AtomicLoopOrchestrator


def run_training_with_full_flow(num_runs: int = 200, headless: bool = True):
    """
    Execute N runs do flow_e2e_phase2.py completo com RL contínuo
    
    Args:
        num_runs: Total de runs (default: 200)
        headless: Browser headless (default: True)
    """
    print("="*80)
    print(f"TRAINING: {num_runs} RUNS - PHASE 2 FULL FLOW (37 ASSERTIONS)")
    print("="*80)
    print(f"Headless: {headless}")
    print(f"RL Processing: AFTER EACH RUN")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    training_start = time.time()
    stats = {
        'runs_completed': 0,
        'runs_success': 0,
        'runs_failed': 0,
        'total_duration': 0.0,
    }
    
    # Import flow Phase 2 completo
    sys.path.insert(0, str(Path(__file__).parent.parent / 'flows' / 'v3'))
    from flow_e2e_phase2 import flow_e2e_phase2
    
    barril_path = Path(__file__).parent.parent / 'barril!!'
    
    for run_num in range(1, num_runs + 1):
        print(f"\n{'='*80}")
        print(f"RUN {run_num}/{num_runs}")
        print(f"{'='*80}")
        
        run_start = time.time()
        
        try:
            # Execute flow completo
            flow_e2e_phase2(headless=headless)
            success = True
            
            run_duration = time.time() - run_start
            stats['runs_completed'] += 1
            stats['runs_success'] += 1
            
            # Save run JSON for RL (CRITICAL for RLAIF validation)
            run_id = f"Phase2_E2E_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{run_num:04d}"
            run_json = barril_path / f"{run_id}.json"
            
            run_data = {
                "run_id": run_id,
                "timestamp": datetime.now().isoformat(),
                "flow_name": "flow_e2e_phase2",
                "success": success,
                "duration": run_duration,
                "metrics": {"assertions": {"total": 37}},  # Placeholder
                "steps": [],  # Populated by flow
                "actions": []  # Populated by flow
            }
            
            with open(run_json, 'w', encoding='utf-8') as f:
                json.dump(run_data, f, indent=2, ensure_ascii=False)
            
            print(f"[OK] Run {run_num} completed in {run_duration:.1f}s")
            print(f"  Saved to: {run_json.name}")
                
            stats['total_duration'] += run_duration
            
        except Exception as e:
            run_duration = time.time() - run_start
            stats['runs_completed'] += 1
            stats['runs_failed'] += 1
            stats['total_duration'] += run_duration
            print(f"[FAIL] Run {run_num} exception: {str(e)[:100]}")
        
        # Process with RL after each run
        print(f"\n[RL] Processing run {run_num} to learn patterns...")
        try:
            orch = AtomicLoopOrchestrator(barril_path)
            rl_success, metrics = orch.run_cycle()
            
            if rl_success:
                avg_reward = metrics.get('avg_reward', 0) if isinstance(metrics, dict) else getattr(metrics, 'avg_reward', 0)
                print(f"  [OK] Patterns updated (reward: {avg_reward:.1f})")
            else:
                print(f"  [WARN] RL processing failed")
        except Exception as e:
            print(f"  [WARN] RL error: {str(e)[:80]}")
        
        # Save checkpoint every 10 runs
        if run_num % 10 == 0:
            checkpoint = {
                "runs_completed": stats['runs_completed'],
                "runs_success": stats['runs_success'],
                "runs_failed": stats['runs_failed'],
                "avg_duration": stats['total_duration'] / stats['runs_completed'] if stats['runs_completed'] > 0 else 0,
                "timestamp": datetime.now().isoformat()
            }
            
            checkpoint_file = Path(__file__).parent / f"checkpoint_full_run{run_num}.json"
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            
            print(f"[SAVED] Checkpoint {run_num}: avg {checkpoint['avg_duration']:.1f}s per run\n")
    
    # Final stats
    training_duration = time.time() - training_start
    stats['avg_duration'] = stats['total_duration'] / stats['runs_completed'] if stats['runs_completed'] > 0 else 0
    
    print("\n" + "="*80)
    print("TRAINING COMPLETE")
    print("="*80)
    print(f"Total runs: {stats['runs_completed']}/{num_runs}")
    print(f"Success: {stats['runs_success']}")
    print(f"Failed: {stats['runs_failed']}")
    print(f"Success rate: {stats['runs_success']/stats['runs_completed']*100:.1f}%")
    print(f"Avg duration: {stats['avg_duration']:.1f}s")
    print(f"Total time: {training_duration/3600:.1f} hours")
    print("="*80)
    
    # Generate final report automatically
    print("\n" + "="*80)
    print("GENERATING FINAL REPORT...")
    print("="*80)
    
    import subprocess
    report_script = Path(__file__).parent / 'generate_training_report.py'
    subprocess.run(['python', str(report_script)])
    
    return stats['runs_success'] / stats['runs_completed'] >= 0.8


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Train RL with Phase 2 FULL flow')
    parser.add_argument('--runs', type=int, default=200, help='Number of runs')
    parser.add_argument('--headless', action='store_true', default=True, help='Run headless')
    
    args = parser.parse_args()
    
    success = run_training_with_full_flow(args.runs, args.headless)
    sys.exit(0 if success else 1)

