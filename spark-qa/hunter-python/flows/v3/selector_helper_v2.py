import time
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from playwright.sync_api import Page, Locator


class SelectorHelperV2:
    """
    Multi-selector helper with RL logging for self-healing
    
    Logs every selector attempt with:
    - element_name
    - selector_used (type + value)
    - fallback_reason (why previous selectors failed)
    - success/fail
    - timing (duration in ms)
    - context (page URL, action type)
    
    RL uses this data to learn which selectors are most reliable
    """
    
    def __init__(self, page: Page, log_file: str = "barril!!/rl_selector_log.json", fast_learner=None, adaptive_wait=None, action_masking=None, model_based=None):
        self.page = page
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.session_logs = []
        self.session_start = datetime.now().isoformat()
        
        self.selector_order = ["testid", "name", "id", "href", "text", "class", "css"]
        
        # RL-GUIDED SELECTOR SELECTION (NEW)
        self.fast_learner = fast_learner
        if self.fast_learner:
            print("[SelectorHelper] FastLearner enabled - selector order will be optimized by RL")
        
        # ADAPTIVE WAIT STRATEGIES (NEW)
        self.adaptive_wait = adaptive_wait
        self.default_timeout = 10000  # 10s default
        if self.adaptive_wait:
            print("[SelectorHelper] Adaptive Wait enabled - timeouts will be learned from history")
        
        # ACTION MASKING (NEW)
        self.action_masking = action_masking
        if self.action_masking:
            print("[SelectorHelper] Action Masking enabled - filters invalid/hidden/disabled actions")
        
        # MODEL-BASED GATE (NEW)
        self.model_based = model_based
        if self.model_based:
            print("[SelectorHelper] Model-Based gate enabled - predicts action outcomes, avoids dead-ends")
    
    def _log_selector_attempt(
        self,
        element_name: str,
        selector_type: str,
        selector_value: str,
        action: str,
        success: bool,
        duration_ms: float,
        fallback_attempts: int = 0,
        error_msg: str = ""
    ):
        """Registra tentativa de selector para o RL"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "element_name": element_name,
            "selector": {
                "type": selector_type,
                "value": selector_value
            },
            "action": action,
            "success": success,
            "duration_ms": round(duration_ms, 2),
            "fallback_attempts": fallback_attempts,
            "context": {
                "url": self.page.url,
                "page_title": self.page.title()
            }
        }
        
        if error_msg:
            log_entry["error"] = error_msg[:200]
        
        self.session_logs.append(log_entry)
    
    def _get_rl_guided_selector_order(self, element_name: str, selector_list: List[Dict]) -> List[Dict]:
        """
        Ask FastLearner to reorder selectors based on learned experience
        
        Args:
            element_name: Name of element being targeted
            selector_list: List of selector dicts [{"type": "testid", "value": "..."}, ...]
            
        Returns:
            Reordered selector list (best first according to RL)
        """
        if not self.fast_learner or not selector_list:
            return selector_list  # Return original if no RL or empty list
        
        # Build current state for RL
        current_state = f"{self.page.url}_{element_name}"
        
        # Build available actions (selector types)
        available_selector_types = [s["type"] for s in selector_list]
        
        # Ask FastLearner which selector type to try first
        try:
            suggested_type, confidence = self.fast_learner.suggest_next_action(
                current_state=current_state,
                available_actions=available_selector_types
            )
            
            if confidence > 0.3:  # Only use suggestion if confidence > 30%
                # Reorder list to put suggested selector first
                reordered = []
                suggested_selector = None
                
                # Find suggested selector
                for sel in selector_list:
                    if sel["type"] == suggested_type:
                        suggested_selector = sel
                    else:
                        reordered.append(sel)
                
                # Put suggested first, rest after
                if suggested_selector:
                    print(f"   [RL] FastLearner suggests {suggested_type} first (confidence: {confidence:.1%})")
                    return [suggested_selector] + reordered
            
        except Exception as e:
            print(f"   [WARN] FastLearner suggestion failed: {e}")
        
        # Fallback to original order if RL fails
        return selector_list
    
    def find_element(
        self,
        selectors_list: List[Dict],
        description: str = "element"
    ) -> Tuple[Optional[Locator], Dict]:
        """
        Multi-selector fallback with RL logging
        
        Args:
            selectors_list: List of selector dicts [{"type": "testid", "value": "..."}, ...]
            description: Element name for logging
        
        Returns:
            (Locator or None, log_data dict)
        """
        start_time = time.time()
        fallback_count = 0
        last_error = ""
        
        # ACTION MASKING DISABLED - Still too aggressive even with 500ms timeout
        # Blocks navigation links because they're checked before navigation happens
        # TODO: Only mask AFTER confirming we're on the right page
        # if self.action_masking:
        #     selectors_list = self.action_masking.compute_mask(self.page, selectors_list)
        #     if not selectors_list:
        #         print(f"  [{description}] All selectors masked out (none valid on current page)")
        #         return None, {"selector_used": "all_masked", "error": "No valid actions"}
        
        # RL-GUIDED SELECTOR ORDERING (NEW)
        # FastLearner reorders selectors based on learned experience
        selectors_list = self._get_rl_guided_selector_order(description, selectors_list)
        
        # MODEL-BASED GATE (NEW) - Predict if action will work before trying
        if self.model_based and selectors_list:
            state_str = f"{self.page.url}|{description}"
            for selector in selectors_list[:]:  # Copy list for modification
                action_str = f"{selector['type']}:{selector['value']}"
                is_useful, reason = self.model_based.predict_next_state_useful(state_str, action_str)
                if not is_useful:
                    print(f"  [{description}] Model-Based vetoed {selector['type']} ({reason})")
                    selectors_list.remove(selector)
        
        for selector in selectors_list:
            attempt_start = time.time()
            sel_type = selector.get("type")
            sel_value = selector.get("value")
            
            try:
                # Get adaptive timeout (learned from history)
                timeout_ms = self.default_timeout if not self.adaptive_wait else self.adaptive_wait.get_timeout(
                    description,
                    context={"page_url": self.page.url}
                )
                
                element = self._get_locator(selector)
                
                if element and element.count() > 0:
                    # Record actual wait time for learning
                    if self.adaptive_wait:
                        self.adaptive_wait.record_wait_time(description, duration * 1000, self.page.url)
                    duration = (time.time() - attempt_start) * 1000
                    
                    self._log_selector_attempt(
                        element_name=description,
                        selector_type=sel_type,
                        selector_value=str(sel_value),
                        action="find",
                        success=True,
                        duration_ms=duration,
                        fallback_attempts=fallback_count
                    )
                    
                    log_data = {
                        "selector_used": f"{sel_type}={sel_value}",
                        "fallback_attempts": fallback_count,
                        "duration_ms": round(duration, 2)
                    }
                    
                    print(f"  [{description}] Found via {sel_type}={sel_value} (fallback: {fallback_count})")
                    return element.first, log_data
                
            except Exception as e:
                last_error = str(e)
                duration = (time.time() - attempt_start) * 1000
                
                self._log_selector_attempt(
                    element_name=description,
                    selector_type=sel_type,
                    selector_value=str(sel_value),
                    action="find",
                    success=False,
                    duration_ms=duration,
                    fallback_attempts=fallback_count,
                    error_msg=last_error
                )
            
            fallback_count += 1
        
        total_duration = (time.time() - start_time) * 1000
        print(f"  [{description}] ERROR: All {len(selectors_list)} selectors failed ({total_duration:.0f}ms)")
        
        return None, {
            "selector_used": "none",
            "fallback_attempts": fallback_count,
            "duration_ms": round(total_duration, 2),
            "error": "All selectors failed"
        }
    
    def _get_locator(self, selector: Dict) -> Optional[Locator]:
        """Converte selector dict em Playwright locator"""
        sel_type = selector.get("type")
        sel_value = selector.get("value")
        
        if sel_type == "testid":
            return self.page.get_by_test_id(sel_value)
        elif sel_type == "name":
            return self.page.locator(f'[name="{sel_value}"]')
        elif sel_type == "id":
            return self.page.locator(f'#{sel_value}')
        elif sel_type == "href":
            return self.page.locator(f'a[href="{sel_value}"]')
        elif sel_type == "text":
            return self.page.get_by_text(sel_value, exact=False)
        elif sel_type == "class":
            return self.page.locator(f'.{sel_value}')
        elif sel_type == "css":
            return self.page.locator(sel_value)
        elif sel_type == "placeholder":
            return self.page.locator(f'[placeholder*="{sel_value}"]')
        elif sel_type == "role":
            return self.page.get_by_role(selector.get("role"), name=selector.get("name"))
        else:
            return None
    
    def safe_fill(
        self,
        selectors_list: List[Dict],
        value: str,
        description: str = "field"
    ) -> Tuple[bool, Dict]:
        """
        Fill field with multi-selector fallback + RL logging
        
        Returns:
            (success: bool, log_data: dict)
        """
        start_time = time.time()
        
        element, find_log = self.find_element(selectors_list, description)
        
        if element:
            try:
                element.click(timeout=10000)
                element.fill(str(value), timeout=10000)
                
                duration = (time.time() - start_time) * 1000
                
                self._log_selector_attempt(
                    element_name=description,
                    selector_type=find_log["selector_used"].split("=")[0],
                    selector_value=find_log["selector_used"].split("=")[1] if "=" in find_log["selector_used"] else "",
                    action="fill",
                    success=True,
                    duration_ms=duration,
                    fallback_attempts=find_log["fallback_attempts"]
                )
                
                return True, {**find_log, "action": "fill", "value_length": len(str(value))}
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                print(f"  [{description}] Fill failed: {str(e)[:50]}")
                return False, {**find_log, "action": "fill", "error": str(e)[:100]}
        
        return False, find_log
    
    def safe_click(
        self,
        selectors_list: List[Dict],
        description: str = "element"
    ) -> Tuple[bool, Dict]:
        """
        Click element with multi-selector fallback + RL logging
        
        Returns:
            (success: bool, log_data: dict)
        """
        start_time = time.time()
        
        element, find_log = self.find_element(selectors_list, description)
        
        if element:
            try:
                element.click(timeout=5000)
                
                duration = (time.time() - start_time) * 1000
                
                self._log_selector_attempt(
                    element_name=description,
                    selector_type=find_log["selector_used"].split("=")[0],
                    selector_value=find_log["selector_used"].split("=")[1] if "=" in find_log["selector_used"] else "",
                    action="click",
                    success=True,
                    duration_ms=duration,
                    fallback_attempts=find_log["fallback_attempts"]
                )
                
                return True, {**find_log, "action": "click"}
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                print(f"  [{description}] Click failed: {str(e)[:50]}")
                return False, {**find_log, "action": "click", "error": str(e)[:100]}
        
        return False, find_log
    
    def safe_select(
        self,
        selectors_list: List[Dict],
        value: str,
        description: str = "select"
    ) -> Tuple[bool, Dict]:
        """
        Select option with multi-selector fallback + RL logging
        
        Returns:
            (success: bool, log_data: dict)
        """
        start_time = time.time()
        
        element, find_log = self.find_element(selectors_list, description)
        
        if element:
            try:
                element.select_option(value=value, timeout=3000)
                duration = (time.time() - start_time) * 1000
                
                self._log_selector_attempt(
                    element_name=description,
                    selector_type=find_log["selector_used"].split("=")[0],
                    selector_value=find_log["selector_used"].split("=")[1] if "=" in find_log["selector_used"] else "",
                    action="select",
                    success=True,
                    duration_ms=duration,
                    fallback_attempts=find_log["fallback_attempts"]
                )
                
                return True, {**find_log, "action": "select", "option_value": value}
            except:
                try:
                    element.select_option(label=value, timeout=3000)
                    duration = (time.time() - start_time) * 1000
                    return True, {**find_log, "action": "select", "option_label": value}
                except Exception as e:
                    duration = (time.time() - start_time) * 1000
                    print(f"  [{description}] Select failed: {str(e)[:50]}")
                    return False, {**find_log, "action": "select", "error": str(e)[:100]}
        
        return False, find_log
    
    def save_logs(self):
        """Salva logs da sessão para o RL consumir"""
        if not self.session_logs:
            print("[SelectorHelperV2] No logs to save")
            return
        
        session_data = {
            "session_start": self.session_start,
            "session_end": datetime.now().isoformat(),
            "total_operations": len(self.session_logs),
            "success_rate": sum(1 for log in self.session_logs if log["success"]) / len(self.session_logs) * 100,
            "operations": self.session_logs
        }
        
        existing_data = {"sessions": []}
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except:
                pass
        
        existing_data["sessions"].append(session_data)
        
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n[SelectorHelperV2] Saved {len(self.session_logs)} operations to {self.log_file}")
        print(f"  Success rate: {session_data['success_rate']:.1f}%")
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas da sessão atual"""
        if not self.session_logs:
            return {}
        
        total = len(self.session_logs)
        success_count = sum(1 for log in self.session_logs if log["success"])
        
        by_selector_type = {}
        for log in self.session_logs:
            sel_type = log["selector"]["type"]
            if sel_type not in by_selector_type:
                by_selector_type[sel_type] = {"success": 0, "fail": 0}
            
            if log["success"]:
                by_selector_type[sel_type]["success"] += 1
            else:
                by_selector_type[sel_type]["fail"] += 1
        
        return {
            "total_operations": total,
            "success_count": success_count,
            "fail_count": total - success_count,
            "success_rate": (success_count / total * 100) if total > 0 else 0,
            "by_selector_type": by_selector_type,
            "avg_duration_ms": sum(log["duration_ms"] for log in self.session_logs) / total if total > 0 else 0
        }
    
    def print_stats(self):
        """Imprime estatísticas da sessão"""
        stats = self.get_stats()
        
        if not stats:
            print("\n[SelectorHelperV2] No stats available")
            return
        
        print("\n" + "="*70)
        print("SELECTOR HELPER V2 - SESSION STATS")
        print("="*70)
        print(f"Total operations: {stats['total_operations']}")
        print(f"Success: {stats['success_count']} | Fail: {stats['fail_count']}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        print(f"Avg duration: {stats['avg_duration_ms']:.1f}ms")
        
        print(f"\nBy selector type:")
        for sel_type, counts in stats["by_selector_type"].items():
            total = counts["success"] + counts["fail"]
            rate = (counts["success"] / total * 100) if total > 0 else 0
            print(f"  {sel_type:10} - {counts['success']:3}/{total:3} ({rate:.0f}%)")
        
        print("="*70)
