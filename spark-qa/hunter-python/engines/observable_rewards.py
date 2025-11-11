"""
OBSERVABLE REWARDS - Dense signals tied to real defects

PROBLEM: Sparse reward (only at end) makes learning slow
SOLUTION: Track observable QA signals during execution

SIGNALS:
1. HTTP errors: 5xx (+1.0), 4xx (+0.5)
2. JS console errors: error (+1.0), warning (+0.3)
3. A11y violations: critical (+0.5), serious (+0.3), moderate (+0.1)
4. Coverage delta: line/branch increase (+0.1 per %)
5. Performance: FCP, LCP metrics

INTEGRATION:
- Playwright event listeners (console, response)
- axe-core for a11y (if available)
- Coverage via Istanbul/nyc (if build allows)
- Rewards added to base reward in reward_shaper

BENEFIT:
- Dense signal (reward every step, not just end)
- Tied to REAL defects (not proxy metrics)
- Guides exploration toward bug-rich areas
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from collections import defaultdict


class ObservableRewards:
    """
    Tracks observable QA signals and calculates rewards
    """
    
    def __init__(self, rewards_file: str = "barril!!/observable_rewards.json"):
        self.rewards_file = Path(rewards_file)
        self.rewards_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Signal collectors
        self.http_errors = []  # {status, url, method, timestamp}
        self.js_errors = []    # {message, source, line, timestamp}
        self.a11y_violations = []  # {impact, description, element, timestamp}
        self.perf_metrics = {}  # {fcp, lcp, tti, etc}
        
        # Reward weights
        self.weights = {
            "http_5xx": 1.0,
            "http_4xx": 0.5,
            "js_error": 1.0,
            "js_warning": 0.3,
            "a11y_critical": 0.5,
            "a11y_serious": 0.3,
            "a11y_moderate": 0.1,
            "coverage_line": 0.1,  # per % increase
            "coverage_branch": 0.1
        }
        
        # Stats
        self.total_signals = 0
        
        self._load()
    
    def _load(self):
        """Load signal history"""
        if self.rewards_file.exists():
            try:
                with open(self.rewards_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"[ObservableRewards] Loaded - {data.get('total_signals', 0)} signals tracked")
            except Exception as e:
                print(f"[ObservableRewards] Failed to load: {e}")
    
    def save(self):
        """Save signal data"""
        data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "total_signals": self.total_signals,
            "http_errors_count": len(self.http_errors),
            "js_errors_count": len(self.js_errors),
            "a11y_violations_count": len(self.a11y_violations),
            "weights": self.weights,
            "recent_http_errors": self.http_errors[-10:],
            "recent_js_errors": self.js_errors[-10:],
            "recent_a11y": self.a11y_violations[-10:]
        }
        
        try:
            with open(self.rewards_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ObservableRewards] Failed to save: {e}")
    
    def add_http_error(self, status: int, url: str, method: str = "GET"):
        """Record HTTP error"""
        self.http_errors.append({
            "status": status,
            "url": url,
            "method": method,
            "timestamp": datetime.now().isoformat()
        })
        self.total_signals += 1
    
    def add_js_error(self, message: str, source: str = "", line: int = 0, level: str = "error"):
        """Record JS console error/warning"""
        self.js_errors.append({
            "level": level,
            "message": message,
            "source": source,
            "line": line,
            "timestamp": datetime.now().isoformat()
        })
        self.total_signals += 1
    
    def add_a11y_violation(self, impact: str, description: str, element: str = ""):
        """Record accessibility violation"""
        self.a11y_violations.append({
            "impact": impact,  # critical, serious, moderate, minor
            "description": description,
            "element": element,
            "timestamp": datetime.now().isoformat()
        })
        self.total_signals += 1
    
    def calculate_reward(self) -> float:
        """
        Calculate total reward from observable signals
        
        Returns:
            Total reward (can be negative if many errors!)
        """
        reward = 0.0
        
        # HTTP errors
        for error in self.http_errors:
            status = error['status']
            if 500 <= status < 600:
                reward += self.weights['http_5xx']
            elif 400 <= status < 500:
                reward += self.weights['http_4xx']
        
        # JS errors
        for error in self.js_errors:
            level = error.get('level', 'error')
            if level == 'error':
                reward += self.weights['js_error']
            elif level == 'warning':
                reward += self.weights['js_warning']
        
        # A11y violations
        for violation in self.a11y_violations:
            impact = violation.get('impact', 'moderate')
            if impact == 'critical':
                reward += self.weights['a11y_critical']
            elif impact == 'serious':
                reward += self.weights['a11y_serious']
            elif impact == 'moderate':
                reward += self.weights['a11y_moderate']
        
        return reward
    
    def reset(self):
        """Reset signal collectors for new run"""
        self.http_errors = []
        self.js_errors = []
        self.a11y_violations = []
        self.perf_metrics = {}
    
    def get_summary(self) -> Dict:
        """Get summary of collected signals"""
        return {
            "http_errors": len(self.http_errors),
            "js_errors": len([e for e in self.js_errors if e.get('level') == 'error']),
            "js_warnings": len([e for e in self.js_errors if e.get('level') == 'warning']),
            "a11y_critical": len([v for v in self.a11y_violations if v.get('impact') == 'critical']),
            "a11y_serious": len([v for v in self.a11y_violations if v.get('impact') == 'serious']),
            "a11y_moderate": len([v for v in self.a11y_violations if v.get('impact') == 'moderate']),
            "total_signals": self.total_signals
        }
    
    def setup_playwright_listeners(self, page):
        """
        Attach Playwright event listeners to capture signals
        
        Usage:
            observable = ObservableRewards()
            observable.setup_playwright_listeners(page)
            # Run test
            reward = observable.calculate_reward()
        """
        # Console listener (JS errors/warnings)
        def on_console(msg):
            msg_type = msg.type
            if msg_type in ['error', 'warning']:
                self.add_js_error(
                    message=msg.text,
                    source=msg.location.get('url', '') if msg.location else '',
                    line=msg.location.get('lineNumber', 0) if msg.location else 0,
                    level=msg_type
                )
        
        page.on("console", on_console)
        
        # Response listener (HTTP errors)
        def on_response(response):
            status = response.status
            if status >= 400:
                self.add_http_error(
                    status=status,
                    url=response.url,
                    method=response.request.method
                )
        
        page.on("response", on_response)
        
        print("[ObservableRewards] Playwright listeners attached - tracking HTTP/JS errors")


# Demo
if __name__ == "__main__":
    print("\n" + "="*70)
    print("OBSERVABLE REWARDS - Demo")
    print("="*70 + "\n")
    
    obs = ObservableRewards()
    
    # Simulate signals
    obs.add_http_error(500, "https://api.example.com/create", "POST")
    obs.add_http_error(404, "https://example.com/missing")
    obs.add_js_error("Uncaught TypeError: Cannot read property 'x'", "app.js", 123, "error")
    obs.add_js_error("Deprecated API", "old.js", 45, "warning")
    obs.add_a11y_violation("critical", "Form has no label", "input#email")
    obs.add_a11y_violation("serious", "Image missing alt", "img.logo")
    
    # Calculate reward
    reward = obs.calculate_reward()
    print(f"Total observable reward: +{reward:.1f}")
    print(f"  (HTTP 5xx: +1.0, HTTP 4xx: +0.5, JS error: +1.0, JS warn: +0.3, a11y critical: +0.5, a11y serious: +0.3)")
    
    # Summary
    print(f"\nSignals summary: {obs.get_summary()}")
    
    obs.save()
    print("\n[OK] Demo complete")

