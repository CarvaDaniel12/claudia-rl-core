"""
Gera report conciso de 200-run training

Analisa todos runs e gera:
- Duration evolution (Run 1 vs 200)
- Selector reliability by type
- Learning curve metrics
- Pattern consolidation
- 50-100 linhas MAX de output
"""
import json
import statistics
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def generate_report():
    print("="*80)
    print("TRAINING REPORT - 200 RUNS PHASE 2")
    print("="*80)
    
    barril = Path(__file__).parent.parent.parent / 'barril!!'
    
    # Load all Phase2 runs
    runs = []
    for run_file in sorted(barril.glob("Phase2_*.json")):
        try:
            with open(run_file) as f:
                run = json.load(f)
                run['filename'] = run_file.name
                runs.append(run)
        except:
            pass
    
    if len(runs) < 10:
        print(f"\n[WARN] Only {len(runs)} runs found. Need 50+ for meaningful analysis.")
        return
    
    print(f"\nTotal runs analyzed: {len(runs)}")
    
    # 1. DURATION EVOLUTION
    print("\n" + "-"*80)
    print("1. DURATION EVOLUTION")
    print("-"*80)
    
    durations = [r['duration'] for r in runs if 'duration' in r]
    
    if len(durations) >= 10:
        first_10_avg = statistics.mean(durations[:10])
        last_10_avg = statistics.mean(durations[-10:])
        improvement = ((first_10_avg - last_10_avg) / first_10_avg) * 100
        
        print(f"First 10 runs avg: {first_10_avg:.1f}s")
        print(f"Last 10 runs avg: {last_10_avg:.1f}s")
        print(f"Improvement: {improvement:+.1f}% {'[LEARNING!]' if improvement > 5 else '[NO LEARNING]'}")
        
        # Quartiles
        q1 = statistics.median(durations[:len(durations)//4])
        q2 = statistics.median(durations[len(durations)//4:len(durations)//2])
        q3 = statistics.median(durations[len(durations)//2:3*len(durations)//4])
        q4 = statistics.median(durations[3*len(durations)//4:])
        
        print(f"\nQuartile progression:")
        print(f"  Q1 (runs 1-50):   {q1:.1f}s")
        print(f"  Q2 (runs 51-100): {q2:.1f}s")
        print(f"  Q3 (runs 101-150): {q3:.1f}s")
        print(f"  Q4 (runs 151-200): {q4:.1f}s")
    
    # 2. SELECTOR RELIABILITY
    print("\n" + "-"*80)
    print("2. SELECTOR RELIABILITY BY TYPE")
    print("-"*80)
    
    selector_stats = defaultdict(lambda: {'success': 0, 'total': 0})
    
    for run in runs:
        if 'selector_stats' not in run:
            continue
        
        by_type = run['selector_stats'].get('by_selector_type', {})
        for sel_type, stats in by_type.items():
            selector_stats[sel_type]['success'] += stats.get('success', 0)
            selector_stats[sel_type]['total'] += stats.get('success', 0) + stats.get('fail', 0)
    
    for sel_type, stats in sorted(selector_stats.items(), key=lambda x: x[1]['success'], reverse=True):
        if stats['total'] > 0:
            success_rate = (stats['success'] / stats['total']) * 100
            print(f"  {sel_type:10s}: {stats['success']:4d}/{stats['total']:4d} ({success_rate:5.1f}%)")
    
    # 3. ASSERTION SUCCESS RATE
    print("\n" + "-"*80)
    print("3. ASSERTION SUCCESS RATE EVOLUTION")
    print("-"*80)
    
    assertion_rates = []
    for run in runs:
        if 'validation_stats' in run:
            total = run['validation_stats'].get('total', 0)
            passed = run['validation_stats'].get('passed', 0)
            if total > 0:
                assertion_rates.append((passed / total) * 100)
    
    if assertion_rates:
        first_10_assertions = statistics.mean(assertion_rates[:10]) if len(assertion_rates) >= 10 else 0
        last_10_assertions = statistics.mean(assertion_rates[-10:]) if len(assertion_rates) >= 10 else 0
        
        print(f"First 10 runs: {first_10_assertions:.1f}% assertions passing")
        print(f"Last 10 runs: {last_10_assertions:.1f}% assertions passing")
        print(f"Improvement: {last_10_assertions - first_10_assertions:+.1f}%")
    
    # 4. PATTERN LEARNING
    print("\n" + "-"*80)
    print("4. PATTERN LEARNING STATUS")
    print("-"*80)
    
    patterns_file = barril / 'patterns_learned.json'
    if patterns_file.exists():
        with open(patterns_file) as f:
            patterns = json.load(f)
        
        total = patterns.get('total_patterns', 0)
        print(f"Total patterns learned: {total}")
        
        if 'patterns' in patterns:
            high_conf = sum(1 for p in patterns['patterns'].values() if p.get('confidence', 0) >= 0.9)
            print(f"High confidence (>=90%): {high_conf}")
    else:
        print("[WARN] No patterns_learned.json found")
    
    # 5. FAILURE ANALYSIS
    print("\n" + "-"*80)
    print("5. FAILURE ANALYSIS")
    print("-"*80)
    
    success_count = sum(1 for r in runs if r.get('success', False))
    fail_count = len(runs) - success_count
    
    print(f"Success: {success_count}/{len(runs)} ({success_count/len(runs)*100:.1f}%)")
    print(f"Failed: {fail_count}/{len(runs)}")
    
    # 6. KEY FINDINGS
    print("\n" + "="*80)
    print("KEY FINDINGS")
    print("="*80)
    
    if len(durations) >= 50:
        first_50 = statistics.mean(durations[:50])
        last_50 = statistics.mean(durations[-50:])
        evolution = ((first_50 - last_50) / first_50) * 100
        
        if evolution > 10:
            print(f"[PROVEN] RL IS LEARNING! {evolution:.1f}% faster over time")
        elif evolution > 5:
            print(f"[LIKELY] RL showing improvement: {evolution:.1f}% faster")
        elif evolution > -5:
            print(f"[INCONCLUSIVE] Marginal change: {evolution:+.1f}%")
        else:
            print(f"[CONCERN] Performance degraded: {evolution:+.1f}%")
    
    # Check if testid dominance increased
    if 'testid' in selector_stats:
        testid_rate = (selector_stats['testid']['success'] / selector_stats['testid']['total']) * 100
        if testid_rate > 98:
            print(f"[OK] testid selector dominant ({testid_rate:.1f}%) - reliable strategy")
    
    print("\n" + "="*80)
    
    # Save compact report
    report = {
        "total_runs": len(runs),
        "duration_first_10_avg": first_10_avg if len(durations) >= 10 else 0,
        "duration_last_10_avg": last_10_avg if len(durations) >= 10 else 0,
        "improvement_percent": improvement if len(durations) >= 10 else 0,
        "selector_reliability": {k: v['success']/v['total']*100 for k,v in selector_stats.items() if v['total'] > 0},
        "success_rate": success_count/len(runs)*100 if runs else 0,
        "timestamp": datetime.now().isoformat()
    }
    
    report_file = Path(__file__).parent / "training_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nFull data saved: {report_file.name}")


if __name__ == "__main__":
    generate_report()

