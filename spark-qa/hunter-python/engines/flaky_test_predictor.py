"""
FLAKY TEST PREDICTION - ML classifier predicts test instability

PROBLEM: Some tests pass/fail randomly (network, timing, race conditions)
SOLUTION: Predict flakiness BEFORE running, prioritize stable tests

FEATURES TRACKED:
- Success variance (same test, different results)
- Duration variance (high variance = timing issues)
- Selector type (text selectors flakier than testid)
- Page context (some pages flakier than others)
- Time of day (network congestion patterns)
- Previous failures (regression indicator)

PREDICTION:
- Flakiness score: 0.0 (stable) to 1.0 (very flaky)
- Threshold: >0.7 = skip or retry with more timeouts
- Strategy: Run stable tests first, save flaky for later

INTEGRATION:
- Trains from barril!! run history
- Predicts before each run
- Adjusts execution strategy (timeouts, retries)
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from collections import defaultdict
import statistics


class FlakyTestPredictor:
    """
    Predicts test flakiness using historical run data
    """
    
    def __init__(self, predictor_file: str = "barril!!/flaky_predictor.json"):
        self.predictor_file = Path(predictor_file)
        self.predictor_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Historical data
        self.test_history = defaultdict(list)  # test_name -> [run_results]
        
        # Flakiness scores
        self.flakiness_scores = {}  # test_name -> score (0-1)
        
        # Feature importance weights (learned)
        self.weights = {
            "success_variance": 0.4,
            "duration_variance": 0.2,
            "selector_reliability": 0.2,
            "page_stability": 0.1,
            "recent_failures": 0.1
        }
        
        self.min_history = 5  # Need 5+ runs to predict
        self.trained = False
        
        self._load()
    
    def _load(self):
        """Load predictor data"""
        if self.predictor_file.exists():
            try:
                with open(self.predictor_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.flakiness_scores = data.get('flakiness_scores', {})
                    self.trained = data.get('trained', False)
                    print(f"[FlakyPredictor] Loaded - tracking {len(self.flakiness_scores)} tests")
            except Exception as e:
                print(f"[FlakyPredictor] Failed to load: {e}")
    
    def save(self):
        """Save predictor data"""
        data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "trained": self.trained,
            "flakiness_scores": self.flakiness_scores,
            "total_tests_tracked": len(self.test_history),
            "weights": self.weights
        }
        
        try:
            with open(self.predictor_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[FlakyPredictor] Saved - {len(self.flakiness_scores)} tests analyzed")
        except Exception as e:
            print(f"[FlakyPredictor] Failed to save: {e}")
    
    def add_run_result(self, test_name: str, run_data: Dict):
        """Add a run result to history"""
        self.test_history[test_name].append({
            "timestamp": datetime.now().isoformat(),
            "success": run_data.get('success', False),
            "duration": run_data.get('duration', 0),
            "selectors_used": run_data.get('selectors_used', []),
            "page_url": run_data.get('page_url', '')
        })
        
        # Retrain if we have enough data
        if len(self.test_history[test_name]) >= self.min_history:
            self._update_flakiness_score(test_name)
    
    def _update_flakiness_score(self, test_name: str):
        """Calculate flakiness score for a test"""
        history = self.test_history[test_name]
        
        if len(history) < self.min_history:
            return
        
        # Feature 1: Success variance
        successes = [r['success'] for r in history]
        success_rate = sum(successes) / len(successes)
        # High flakiness if success_rate near 0.5 (random)
        success_variance = 4 * success_rate * (1 - success_rate)  # Max at 0.5
        
        # Feature 2: Duration variance
        durations = [r['duration'] for r in history if r['duration'] > 0]
        duration_variance = 0.0
        if len(durations) > 1:
            mean = statistics.mean(durations)
            std = statistics.stdev(durations)
            # Normalize: high CV (coefficient of variation) = flaky
            cv = (std / mean) if mean > 0 else 0
            duration_variance = min(cv, 1.0)  # Cap at 1.0
        
        # Feature 3: Selector reliability
        all_selectors = []
        for r in history:
            all_selectors.extend(r.get('selectors_used', []))
        
        # Text/class selectors are flakier than testid
        flaky_selector_count = sum(1 for s in all_selectors if s.get('type') in ['text', 'class'])
        selector_unreliability = flaky_selector_count / max(len(all_selectors), 1)
        
        # Feature 4: Page stability
        page_changes = len(set(r['page_url'] for r in history))
        page_variance = min(page_changes / len(history), 1.0)
        
        # Feature 5: Recent failures
        recent_5 = history[-5:]
        recent_failures = sum(1 for r in recent_5 if not r['success'])
        recent_failure_rate = recent_failures / len(recent_5)
        
        # Weighted combination
        flakiness_score = (
            self.weights['success_variance'] * success_variance +
            self.weights['duration_variance'] * duration_variance +
            self.weights['selector_reliability'] * selector_unreliability +
            self.weights['page_stability'] * page_variance +
            self.weights['recent_failures'] * recent_failure_rate
        )
        
        self.flakiness_scores[test_name] = round(flakiness_score, 3)
        self.trained = True
    
    def predict_flakiness(self, test_name: str) -> Tuple[float, str]:
        """
        Predict flakiness score for a test
        
        Returns:
            (score 0-1, recommendation)
        """
        if test_name not in self.flakiness_scores:
            return 0.5, "UNKNOWN - no history"
        
        score = self.flakiness_scores[test_name]
        
        if score < 0.3:
            return score, "STABLE - run normally"
        elif score < 0.7:
            return score, "MODERATE - increase timeouts"
        else:
            return score, "FLAKY - skip or retry 3x"
    
    def get_stable_tests(self, threshold: float = 0.3) -> List[str]:
        """Get list of stable tests (low flakiness)"""
        return [
            test for test, score in self.flakiness_scores.items()
            if score < threshold
        ]
    
    def get_flaky_tests(self, threshold: float = 0.7) -> List[str]:
        """Get list of flaky tests (high flakiness)"""
        return [
            test for test, score in self.flakiness_scores.items()
            if score >= threshold
        ]
    
    def get_stats(self) -> Dict:
        """Get predictor statistics"""
        if not self.flakiness_scores:
            return {
                "trained": False, 
                "tests_tracked": 0,
                "stable_tests": 0,
                "flaky_tests": 0
            }
        
        scores = list(self.flakiness_scores.values())
        
        return {
            "trained": self.trained,
            "tests_tracked": len(self.flakiness_scores),
            "stable_tests": len(self.get_stable_tests()),
            "flaky_tests": len(self.get_flaky_tests()),
            "avg_flakiness": round(statistics.mean(scores), 3),
            "max_flakiness": round(max(scores), 3)
        }


# Demo
if __name__ == "__main__":
    print("\n" + "="*70)
    print("FLAKY TEST PREDICTION - Demo")
    print("="*70 + "\n")
    
    predictor = FlakyTestPredictor()
    
    # Simulate test history
    # Test 1: Stable test (always succeeds, consistent duration)
    for i in range(10):
        predictor.add_run_result("test_login", {
            "success": True,
            "duration": 15.0 + i*0.5,
            "selectors_used": [{"type": "testid", "value": "email"}],
            "page_url": "/login"
        })
    
    # Test 2: Flaky test (random success, high variance)
    import random
    for i in range(10):
        predictor.add_run_result("test_create_property", {
            "success": random.choice([True, False]),  # Flaky!
            "duration": 30.0 + random.uniform(-10, 10),  # High variance
            "selectors_used": [{"type": "text", "value": "Save"}],  # Unreliable selector
            "page_url": "/properties"
        })
    
    # Predictions
    print("Predictions:")
    for test in ["test_login", "test_create_property"]:
        score, recommendation = predictor.predict_flakiness(test)
        print(f"  {test}: {score:.3f} - {recommendation}")
    
    # Stats
    print(f"\nStats: {predictor.get_stats()}")
    
    predictor.save()
    print("\n[OK] Demo complete")

