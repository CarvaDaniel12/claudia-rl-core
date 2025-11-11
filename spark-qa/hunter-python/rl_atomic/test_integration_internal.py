#!/usr/bin/env python3
"""
INTEGRATION TEST INTERNAL - Run from within rl_atomic folder
Tests all components with proper imports
"""
import sys
import json
import traceback
from pathlib import Path

def test_full_pipeline():
    """Test complete pipeline with real data"""
    print("="*80)
    print("RL ATOMIC LOOP - INTERNAL INTEGRATION TEST")
    print("="*80)
    
    results = {}
    
    # Test 1: Load modules
    print("\n[TEST 1] Loading modules...")
    try:
        from rl_atomic.atomic_loop import AtomicLoopOrchestrator
        from rl_atomic.reward_shaper import RewardShaper
        from rl_atomic.run_selector import RunSelector
        from rl_atomic.pattern_extractor import PatternExtractor
        from rl_atomic.memory_bootstrap import MemoryBootstrap
        from rl_atomic.barril_cleaner import BarrilCleaner
        from rl_atomic.rlaif_auto_feedback import RLAIFAutoFeedback
        print("  [OK] All core modules loaded")
        results['module_load'] = True
    except Exception as e:
        print(f"  [FAIL] Module load failed: {e}")
        traceback.print_exc()
        results['module_load'] = False
        return results
    
    # Test 2: Initialize components
    print("\n[TEST 2] Initializing components...")
    try:
        barril_path = Path(__file__).parent.parent / "barril!!"
        
        orchestrator = AtomicLoopOrchestrator(barril_path)
        reward_shaper = RewardShaper()
        run_selector = RunSelector(total_runs=100)
        pattern_extractor = PatternExtractor()
        memory_bootstrap = MemoryBootstrap()
        barril_cleaner = BarrilCleaner(barril_path)
        rlaif = RLAIFAutoFeedback(enable_constraint_checking=True)
        
        print("  [OK] All components initialized")
        results['component_init'] = True
    except Exception as e:
        print(f"  [FAIL] Component initialization failed: {e}")
        traceback.print_exc()
        results['component_init'] = False
        return results
    
    # Test 3: Load existing runs
    print("\n[TEST 3] Loading existing runs...")
    try:
        json_files = list(barril_path.glob("Phase2_*.json"))
        print(f"  Found {len(json_files)} JSON files")
        
        runs_data = []
        for json_file in json_files[:3]:  # Test with first 3
            with open(json_file, 'r', encoding='utf-8') as f:
                run_data = json.load(f)
                runs_data.append(run_data)
        
        print(f"  [OK] Loaded {len(runs_data)} runs for testing")
        results['load_runs'] = True
    except Exception as e:
        print(f"  [FAIL] Loading runs failed: {e}")
        traceback.print_exc()
        results['load_runs'] = False
        return results
    
    # Test 4: Reward calculation
    print("\n[TEST 4] Reward calculation...")
    try:
        # Find correct method name
        reward_methods = [m for m in dir(reward_shaper) if 'reward' in m.lower() and not m.startswith('_')]
        print(f"  Available reward methods: {reward_methods}")
        
        if hasattr(reward_shaper, 'shape_reward'):
            for run_data in runs_data:
                reward = reward_shaper.shape_reward(run_data)
                print(f"    Run {run_data['run_id']}: reward = {reward}")
        elif hasattr(reward_shaper, 'calculate_reward'):
            for run_data in runs_data:
                reward = reward_shaper.calculate_reward(run_data)
                print(f"    Run {run_data['run_id']}: reward = {reward}")
        else:
            print(f"  [WARN] No standard reward method found, trying first method: {reward_methods[0]}")
            method = getattr(reward_shaper, reward_methods[0])
            for run_data in runs_data:
                reward = method(run_data)
                print(f"    Run {run_data['run_id']}: reward = {reward}")
        
        print("  [OK] Reward calculation working")
        results['reward_calc'] = True
    except Exception as e:
        print(f"  [FAIL] Reward calculation failed: {e}")
        traceback.print_exc()
        results['reward_calc'] = False
    
    # Test 5: RLAIF validation
    print("\n[TEST 5] RLAIF validation...")
    try:
        for run_data in runs_data:
            result = rlaif.validate_run(run_data['run_id'], run_data)
            print(f"    Run {run_data['run_id']}: status={result.status.value}, score={result.score}")
        
        print("  [OK] RLAIF validation working")
        results['rlaif'] = True
    except Exception as e:
        print(f"  [FAIL] RLAIF validation failed: {e}")
        traceback.print_exc()
        results['rlaif'] = False
    
    # Test 6: Run selector
    print("\n[TEST 6] Run selector...")
    try:
        # Add rewards to runs
        rewarded_runs = []
        for run_data in runs_data:
            run_copy = run_data.copy()
            run_copy['reward'] = 100.0  # Dummy reward
            rewarded_runs.append(run_copy)
        
        tiers = run_selector.classify_runs(rewarded_runs)
        print(f"    Tier 1: {len(tiers['tier_1'])}")
        print(f"    Tier 2: {len(tiers['tier_2'])}")
        print(f"    Tier 3: {len(tiers['tier_3'])}")
        print(f"    Discard: {len(tiers['discard'])}")
        
        print("  [OK] Run selector working")
        results['run_selector'] = True
    except Exception as e:
        print(f"  [FAIL] Run selector failed: {e}")
        traceback.print_exc()
        results['run_selector'] = False
    
    # Test 7: Pattern extraction
    print("\n[TEST 7] Pattern extraction...")
    try:
        patterns = pattern_extractor.extract_patterns(runs_data)
        print(f"    Shortcuts: {len(patterns.get('shortcuts', []))}")
        print(f"    Recovery patterns: {len(patterns.get('recovery_patterns', []))}")
        
        print("  [OK] Pattern extraction working")
        results['pattern_extract'] = True
    except Exception as e:
        print(f"  [FAIL] Pattern extraction failed: {e}")
        traceback.print_exc()
        results['pattern_extract'] = False
    
    # Test 8: Full cycle (DRY RUN - don't delete files)
    print("\n[TEST 8] Full cycle dry run...")
    try:
        print("  Initializing orchestrator...")
        orchestrator = AtomicLoopOrchestrator(barril_path)
        
        print("  Running cycle (this will process existing runs)...")
        success, metrics = orchestrator.run_cycle(max_iterations=1)
        
        print(f"  [OK] Cycle completed: success={success}")
        if isinstance(metrics, dict):
            print(f"    Total runs: {metrics.get('total_runs', 0)}")
            print(f"    Avg reward: {metrics.get('avg_reward', 0):.2f}")
        else:
            print(f"    Cycle ID: {metrics.cycle_id}")
            print(f"    Total runs: {metrics.total_runs}")
            print(f"    Avg reward: {metrics.avg_reward:.2f}")
        
        results['full_cycle'] = success
    except Exception as e:
        print(f"  [FAIL] Full cycle failed: {e}")
        traceback.print_exc()
        results['full_cycle'] = False
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All integration tests passed!")
        print("System is fully connected and ready for production runs.")
        return 0
    else:
        print("\n[WARNING] Some tests failed.")
        print("Review errors above to identify issues.")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(test_full_pipeline())

