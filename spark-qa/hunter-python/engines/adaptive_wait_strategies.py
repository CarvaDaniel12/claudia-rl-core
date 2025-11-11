"""
ADAPTIVE WAIT STRATEGIES - Smart timeout adjustment

PROBLEM: Fixed timeouts waste time or cause failures
SOLUTION: Learn optimal wait times from historical data

STRATEGIES:
1. Element-specific waits (some elements slower than others)
2. Page-context waits (some pages need longer)
3. Network-adaptive (adjust based on observed latency)
4. Progressive backoff (increase timeout on retry)
5. Predictive wait (ML predicts element load time)

LEARNING:
- Track actual element appearance times
- Calculate mean + 2*std as safe timeout
- Adjust in real-time based on current run performance

INTEGRATION:
- SelectorHelper uses adaptive timeouts
- Reduces false failures (timeout too short)
- Reduces wasted time (timeout too long)
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from collections import defaultdict
import statistics


class AdaptiveWaitStrategies:
    """
    Learns optimal wait times for elements and pages
    """
    
    def __init__(self, wait_file: str = "barril!!/adaptive_waits.json"):
        self.wait_file = Path(wait_file)
        self.wait_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Historical wait times: element_name -> [actual_wait_times]
        self.element_wait_history = defaultdict(list)
        
        # Page load times: page_url -> [load_times]
        self.page_load_history = defaultdict(list)
        
        # Learned timeouts: element_name -> timeout_ms
        self.learned_timeouts = {}
        
        # Network baseline (rolling average)
        self.network_baseline_ms = 1000.0  # Default 1s
        self.network_samples = []
        
        # Config
        self.min_samples = 5  # Need 5+ samples to trust learned timeout
        self.safety_margin = 2.0  # mean + 2*std (covers 95% of cases)
        self.default_timeout = 5000  # 5s default
        
        self._load()
    
    def _load(self):
        """Load learned wait strategies"""
        if self.wait_file.exists():
            try:
                with open(self.wait_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.learned_timeouts = data.get('learned_timeouts', {})
                    self.network_baseline_ms = data.get('network_baseline_ms', 1000.0)
                    print(f"[AdaptiveWait] Loaded {len(self.learned_timeouts)} learned timeouts")
            except Exception as e:
                print(f"[AdaptiveWait] Failed to load: {e}")
    
    def save(self):
        """Save learned wait strategies"""
        data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "learned_timeouts": self.learned_timeouts,
            "network_baseline_ms": self.network_baseline_ms,
            "elements_tracked": len(self.element_wait_history),
            "total_samples": sum(len(v) for v in self.element_wait_history.values())
        }
        
        try:
            with open(self.wait_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[AdaptiveWait] Saved - {len(self.learned_timeouts)} timeouts learned")
        except Exception as e:
            print(f"[AdaptiveWait] Failed to save: {e}")
    
    def record_wait_time(self, element_name: str, actual_wait_ms: float, page_url: str = ""):
        """Record actual time it took for element to appear"""
        self.element_wait_history[element_name].append(actual_wait_ms)
        
        if page_url:
            self.page_load_history[page_url].append(actual_wait_ms)
        
        # Update learned timeout if we have enough samples
        if len(self.element_wait_history[element_name]) >= self.min_samples:
            self._update_learned_timeout(element_name)
        
        # Update network baseline (rolling average of last 50 samples)
        self.network_samples.append(actual_wait_ms)
        self.network_samples = self.network_samples[-50:]
        self.network_baseline_ms = statistics.mean(self.network_samples)
    
    def _update_learned_timeout(self, element_name: str):
        """Calculate optimal timeout for an element"""
        wait_times = self.element_wait_history[element_name]
        
        if len(wait_times) < self.min_samples:
            return
        
        mean_wait = statistics.mean(wait_times)
        std_wait = statistics.stdev(wait_times) if len(wait_times) > 1 else 0
        
        # Safe timeout: mean + 2*std (covers 95% of cases)
        safe_timeout = mean_wait + self.safety_margin * std_wait
        
        # Add network baseline adjustment
        adjusted_timeout = safe_timeout + (self.network_baseline_ms * 0.2)
        
        # Cap between 1s and 30s
        final_timeout = max(1000, min(30000, adjusted_timeout))
        
        self.learned_timeouts[element_name] = round(final_timeout)
    
    def get_timeout(self, element_name: str, context: Optional[Dict] = None) -> int:
        """
        Get optimal timeout for an element
        
        Args:
            element_name: Name of element
            context: Optional context (page_url, etc) for further refinement
            
        Returns:
            Timeout in milliseconds
        """
        # 1. Check learned timeout
        if element_name in self.learned_timeouts:
            return self.learned_timeouts[element_name]
        
        # 2. Check page-specific baseline
        if context and context.get('page_url'):
            page_url = context['page_url']
            if page_url in self.page_load_history:
                page_times = self.page_load_history[page_url]
                if len(page_times) >= 3:
                    mean_page = statistics.mean(page_times)
                    return int(mean_page + 1000)  # Page mean + 1s buffer
        
        # 3. Use network baseline
        if self.network_baseline_ms > 1000:
            return int(self.network_baseline_ms * 2)  # 2x network baseline
        
        # 4. Fallback to default
        return self.default_timeout
    
    def get_progressive_timeout(self, element_name: str, retry_count: int) -> int:
        """
        Get timeout with progressive backoff for retries
        
        Args:
            retry_count: Current retry attempt (0 = first try)
            
        Returns:
            Timeout in milliseconds (increases with retries)
        """
        base_timeout = self.get_timeout(element_name)
        
        # Progressive backoff: timeout * (1.5 ^ retry_count)
        backoff_multiplier = 1.5 ** retry_count
        progressive_timeout = base_timeout * backoff_multiplier
        
        # Cap at 60s
        return int(min(progressive_timeout, 60000))
    
    def get_stats(self) -> Dict:
        """Get adaptive wait statistics"""
        return {
            "learned_timeouts": len(self.learned_timeouts),
            "elements_tracked": len(self.element_wait_history),
            "network_baseline_ms": round(self.network_baseline_ms),
            "total_samples": sum(len(v) for v in self.element_wait_history.values()),
            "fastest_element": min(self.learned_timeouts.items(), key=lambda x: x[1]) if self.learned_timeouts else None,
            "slowest_element": max(self.learned_timeouts.items(), key=lambda x: x[1]) if self.learned_timeouts else None
        }


# Demo
if __name__ == "__main__":
    print("\n" + "="*70)
    print("ADAPTIVE WAIT STRATEGIES - Demo")
    print("="*70 + "\n")
    
    wait_mgr = AdaptiveWaitStrategies()
    
    # Simulate recording wait times
    import random
    
    # Fast element (login button)
    for _ in range(10):
        wait_mgr.record_wait_time("login_button", 500 + random.uniform(-100, 100), "/login")
    
    # Slow element (property save)
    for _ in range(10):
        wait_mgr.record_wait_time("save_button", 2000 + random.uniform(-500, 500), "/properties")
    
    # Very variable element (lead search)
    for _ in range(10):
        wait_mgr.record_wait_time("lead_search", random.uniform(500, 3000), "/pipeline")
    
    # Get timeouts
    print("Learned Timeouts:")
    print(f"  login_button: {wait_mgr.get_timeout('login_button')}ms")
    print(f"  save_button: {wait_mgr.get_timeout('save_button')}ms")
    print(f"  lead_search: {wait_mgr.get_timeout('lead_search')}ms")
    print(f"  unknown_element: {wait_mgr.get_timeout('unknown_element')}ms (default)")
    
    # Progressive backoff
    print("\nProgressive Backoff (login_button retries):")
    for retry in range(4):
        timeout = wait_mgr.get_progressive_timeout("login_button", retry)
        print(f"  Retry {retry}: {timeout}ms")
    
    # Stats
    print(f"\nStats: {wait_mgr.get_stats()}")
    
    wait_mgr.save()
    print("\n[OK] Demo complete")

