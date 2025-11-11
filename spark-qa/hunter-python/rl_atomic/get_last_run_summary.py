"""
GET LAST RUN SUMMARY - Quick report of most recent run
"""
import json
from pathlib import Path
from datetime import datetime

def get_last_run_summary():
    """Get summary of most recent run"""
    barril = Path("../barril!!")
    
    # Find all run JSONs
    runs = list(barril.glob("Phase2_E2E_*.json"))
    if not runs:
        print("[WARN] No runs found in barril!!")
        return
    
    # Get most recent
    latest = max(runs, key=lambda p: p.stat().st_mtime)
    
    with open(latest, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract key info
    metrics = data.get('metrics', {})
    
    print("\n" + "="*70)
    print("LAST RUN SUMMARY")
    print("="*70)
    print(f"File: {latest.name}")
    print(f"Timestamp: {data.get('timestamp', 'unknown')}")
    print(f"Duration: {metrics.get('duration', 0):.1f}s")
    print()
    
    # Assertions
    if 'assertions' in metrics:
        ass = metrics['assertions']
        print(f"ASSERTIONS: {ass.get('passed', 0)}/{ass.get('total', 0)} passed ({ass.get('success_rate', 0):.1f}%)")
        
        if ass.get('failed_list'):
            print("\nFailed assertions:")
            for fail in ass['failed_list'][:5]:  # Show first 5
                print(f"  - {fail}")
    
    # Selectors
    if 'selectors' in metrics:
        sel = metrics['selectors']
        print(f"\nSELECTORS: {sel.get('success_count', 0)}/{sel.get('total_operations', 0)} succeeded ({sel.get('success_rate', 0):.1f}%)")
        print(f"  Avg fallback: {sel.get('avg_fallback', 0):.1f}")
    
    # Actions
    if 'actions' in data:
        actions = data['actions']
        print(f"\nACTIONS: {len(actions)} total")
        
        # Count failures
        failures = [a for a in actions if not a.get('success', True)]
        if failures:
            print(f"  Failed: {len(failures)}")
            print("\nFirst 3 failures:")
            for fail in failures[:3]:
                print(f"    [{fail.get('step', '?')}] {fail.get('description', 'unknown')}: {fail.get('error', '')[:60]}")
    
    # RL signals
    if 'observable_rewards' in data:
        obs = data['observable_rewards']
        print(f"\nOBSERVABLE SIGNALS:")
        print(f"  HTTP errors: {obs.get('http_errors', 0)}")
        print(f"  JS errors: {obs.get('js_errors', 0)}")
        print(f"  a11y violations: {obs.get('a11y_violations', 0)}")
    
    print("\n" + "="*70)
    print(f"Flow: {data.get('flow_name', 'unknown')}")
    print(f"Success: {metrics.get('success', False)}")
    print("="*70)

if __name__ == "__main__":
    get_last_run_summary()

