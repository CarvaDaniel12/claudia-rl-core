#!/usr/bin/env python3
"""
INTEGRATION TEST - FULL PIPELINE VALIDATION
Tests every component of the RL Atomic Loop end-to-end
"""
import sys
import json
import traceback
from pathlib import Path

# Add paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "hunter-python"))
sys.path.insert(0, str(project_root / "hunter-python" / "rl_atomic"))

def test_json_parsing():
    """Test 1: Verify JSON files can be parsed without emoji issues"""
    print("\n" + "="*80)
    print("TEST 1: JSON PARSING")
    print("="*80)
    
    barril_path = project_root / "hunter-python" / "barril!!"
    json_files = list(barril_path.glob("Phase2_*.json"))
    
    print(f"Found {len(json_files)} run JSON files")
    
    passed = 0
    failed = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"  [OK] {json_file.name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {json_file.name}: {str(e)}")
            failed += 1
    
    print(f"\nResult: {passed} passed, {failed} failed")
    return failed == 0

def test_atomic_loop_import():
    """Test 2: Verify atomic_loop can be imported"""
    print("\n" + "="*80)
    print("TEST 2: ATOMIC LOOP IMPORT")
    print("="*80)
    
    try:
        from atomic_loop import AtomicLoopOrchestrator
        print("  [OK] AtomicLoopOrchestrator imported")
        return True
    except Exception as e:
        print(f"  [FAIL] Import failed: {str(e)}")
        traceback.print_exc()
        return False

def test_atomic_loop_initialization():
    """Test 3: Verify atomic_loop can be initialized"""
    print("\n" + "="*80)
    print("TEST 3: ATOMIC LOOP INITIALIZATION")
    print("="*80)
    
    try:
        from atomic_loop import AtomicLoopOrchestrator
        barril_path = project_root / "hunter-python" / "barril!!"
        
        orchestrator = AtomicLoopOrchestrator(barril_path)
        print("  [OK] Orchestrator initialized")
        print(f"  Barril path: {orchestrator.barril_path}")
        print(f"  Cycle ID: {orchestrator.cycle_id}")
        return True
    except Exception as e:
        print(f"  [FAIL] Initialization failed: {str(e)}")
        traceback.print_exc()
        return False

def test_load_runs():
    """Test 4: Verify runs can be loaded from barril"""
    print("\n" + "="*80)
    print("TEST 4: LOAD RUNS")
    print("="*80)
    
    try:
        from atomic_loop import AtomicLoopOrchestrator
        barril_path = project_root / "hunter-python" / "barril!!"
        
        orchestrator = AtomicLoopOrchestrator(barril_path)
        runs_data = orchestrator._phase_load()
        
        print(f"  [OK] Loaded {len(runs_data)} runs")
        if runs_data:
            print(f"  First run ID: {runs_data[0].get('run_id', 'unknown')}")
        return True
    except Exception as e:
        print(f"  [FAIL] Load failed: {str(e)}")
        traceback.print_exc()
        return False

def test_reward_calculation():
    """Test 5: Verify reward calculation works"""
    print("\n" + "="*80)
    print("TEST 5: REWARD CALCULATION")
    print("="*80)
    
    try:
        from reward_shaper import RewardShaper
        
        shaper = RewardShaper()
        
        # Test run data
        run_data = {
            'run_id': 'test_001',
            'success': True,
            'duration': 100.0,
            'steps': [],
            'actions': []
        }
        
        reward = shaper.calculate_reward(run_data)
        print(f"  [OK] Reward calculated: {reward}")
        return True
    except Exception as e:
        print(f"  [FAIL] Reward calculation failed: {str(e)}")
        traceback.print_exc()
        return False

def test_rlaif_validation():
    """Test 6: Verify RLAIF validation works"""
    print("\n" + "="*80)
    print("TEST 6: RLAIF VALIDATION")
    print("="*80)
    
    try:
        from rlaif_auto_feedback import RLAIFAutoFeedback
        
        validator = RLAIFAutoFeedback(enable_constraint_checking=True)
        
        # Test run data
        run_data = {
            'success': True,
            'duration': 100.0,
            'steps': [],
            'created_files': [],
            'created_narratives': []
        }
        
        result = validator.validate_run('test_001', run_data)
        print(f"  [OK] Validation status: {result.status.value}")
        print(f"  [OK] Validation score: {result.score}")
        print(f"  [OK] Feedback: {result.feedback[:50]}...")
        return True
    except Exception as e:
        print(f"  [FAIL] RLAIF validation failed: {str(e)}")
        traceback.print_exc()
        return False

def test_full_cycle_dry_run():
    """Test 7: Verify full cycle can run (with existing data)"""
    print("\n" + "="*80)
    print("TEST 7: FULL CYCLE DRY RUN")
    print("="*80)
    
    try:
        from atomic_loop import AtomicLoopOrchestrator
        barril_path = project_root / "hunter-python" / "barril!!"
        
        orchestrator = AtomicLoopOrchestrator(barril_path)
        
        print("  Starting cycle...")
        success, metrics = orchestrator.run_cycle(max_iterations=1)
        
        print(f"  [OK] Cycle completed: {success}")
        if isinstance(metrics, dict):
            print(f"  Total runs: {metrics.get('total_runs', 0)}")
            print(f"  Avg reward: {metrics.get('avg_reward', 0):.2f}")
        else:
            print(f"  Cycle ID: {metrics.cycle_id}")
            print(f"  Total runs: {metrics.total_runs}")
            print(f"  Avg reward: {metrics.avg_reward:.2f}")
        
        return success
    except Exception as e:
        print(f"  [FAIL] Full cycle failed: {str(e)}")
        traceback.print_exc()
        return False

def test_engine_integrations():
    """Test 8: Verify all engine components are accessible"""
    print("\n" + "="*80)
    print("TEST 8: ENGINE INTEGRATIONS")
    print("="*80)
    
    engines_path = project_root / "hunter-python" / "engines"
    sys.path.insert(0, str(engines_path))
    
    engines = [
        'fast_learner',
        'hierarchical_options',
        'adaptive_wait_strategies',
        'observable_rewards',
        'action_masking',
        'model_based_gate',
        'dom_graph_features',
        'rnd_curiosity',
        'automatic_test_oracle',
        'flaky_test_predictor',
        'property_based_testing',
        'visual_regression_ai'
    ]
    
    passed = 0
    failed = 0
    
    for engine in engines:
        try:
            __import__(engine)
            print(f"  [OK] {engine}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {engine}: {str(e)}")
            failed += 1
    
    print(f"\nResult: {passed}/{len(engines)} engines available")
    return failed == 0

def main():
    """Run all integration tests"""
    print("="*80)
    print("RL ATOMIC LOOP - FULL INTEGRATION TEST")
    print("="*80)
    print(f"Project root: {project_root}")
    print(f"Python: {sys.version}")
    
    results = {}
    
    # Run all tests
    results['json_parsing'] = test_json_parsing()
    results['atomic_import'] = test_atomic_loop_import()
    results['atomic_init'] = test_atomic_loop_initialization()
    results['load_runs'] = test_load_runs()
    results['reward_calc'] = test_reward_calculation()
    results['rlaif_validation'] = test_rlaif_validation()
    results['engine_integrations'] = test_engine_integrations()
    results['full_cycle'] = test_full_cycle_dry_run()
    
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
        print("System is fully connected and ready to run.")
        return 0
    else:
        print("\n[WARNING] Some tests failed.")
        print("Review errors above to identify disconnected components.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

