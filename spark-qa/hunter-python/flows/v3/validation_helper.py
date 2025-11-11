"""
Validation and assertion patterns for E2E flows

Provides reusable assertion methods for:
- Success states
- Error states
- Warning states
- Disabled states
- Field validation
- Modal presence/absence
"""
from typing import Optional, List, Dict
from playwright.sync_api import Page, Locator


class ValidationHelper:
    """Assertion patterns for E2E testing with detailed logging"""
    
    def __init__(self, page: Page):
        self.page = page
        self.assertions_passed = 0
        self.assertions_failed = 0
        self.assertion_log = []
    
    def _log_assertion(self, name: str, success: bool, details: str = ""):
        """Log assertion result"""
        self.assertion_log.append({
            "name": name,
            "success": success,
            "details": details,
            "url": self.page.url
        })
        
        if success:
            self.assertions_passed += 1
            print(f"  [PASS {self.assertions_passed}] {name}")
        else:
            self.assertions_failed += 1
            print(f"  [FAIL] {name}: {details}")
    
    # URL ASSERTIONS
    
    def assert_url_contains(self, expected: str, name: str = None) -> bool:
        """Assert current URL contains expected string"""
        name = name or f"URL contains '{expected}'"
        current_url = self.page.url
        success = expected in current_url
        
        if not success:
            self._log_assertion(name, False, f"Expected '{expected}' in '{current_url}'")
        else:
            self._log_assertion(name, True)
        
        return success
    
    def assert_url_equals(self, expected: str, name: str = None) -> bool:
        """Assert current URL equals expected"""
        name = name or f"URL = '{expected}'"
        current_url = self.page.url
        success = current_url == expected
        
        if not success:
            self._log_assertion(name, False, f"Expected '{expected}', got '{current_url}'")
        else:
            self._log_assertion(name, True)
        
        return success
    
    # ELEMENT PRESENCE ASSERTIONS
    
    def assert_element_visible(
        self,
        selector: str,
        name: str = None,
        timeout: int = 5000
    ) -> bool:
        """Assert element is visible"""
        name = name or f"Element '{selector}' visible"
        
        try:
            element = self.page.locator(selector).first
            is_visible = element.is_visible(timeout=timeout)
            
            if is_visible:
                self._log_assertion(name, True)
            else:
                self._log_assertion(name, False, "Element not visible")
            
            return is_visible
        except Exception as e:
            self._log_assertion(name, False, str(e)[:100])
            return False
    
    def assert_element_not_visible(
        self,
        selector: str,
        name: str = None,
        timeout: int = 2000
    ) -> bool:
        """Assert element is NOT visible"""
        name = name or f"Element '{selector}' not visible"
        
        try:
            element = self.page.locator(selector).first
            is_visible = element.is_visible(timeout=timeout)
            
            if not is_visible:
                self._log_assertion(name, True)
            else:
                self._log_assertion(name, False, "Element is visible (should not be)")
            
            return not is_visible
        except:
            self._log_assertion(name, True, "Element not found (expected)")
            return True
    
    def assert_element_count(
        self,
        selector: str,
        expected_count: int,
        name: str = None
    ) -> bool:
        """Assert element count matches expected"""
        name = name or f"Element count '{selector}' = {expected_count}"
        
        actual_count = self.page.locator(selector).count()
        success = actual_count == expected_count
        
        if not success:
            self._log_assertion(name, False, f"Expected {expected_count}, got {actual_count}")
        else:
            self._log_assertion(name, True)
        
        return success
    
    # TEXT ASSERTIONS
    
    def assert_element_text_contains(
        self,
        selector: str,
        expected_text: str,
        name: str = None
    ) -> bool:
        """Assert element text contains expected string"""
        name = name or f"Text contains '{expected_text}'"
        
        try:
            element = self.page.locator(selector).first
            actual_text = element.inner_text()
            success = expected_text in actual_text
            
            if not success:
                self._log_assertion(name, False, f"Expected '{expected_text}' in '{actual_text[:50]}'")
            else:
                self._log_assertion(name, True)
            
            return success
        except Exception as e:
            self._log_assertion(name, False, str(e)[:100])
            return False
    
    def assert_element_text_equals(
        self,
        selector: str,
        expected_text: str,
        name: str = None
    ) -> bool:
        """Assert element text equals expected"""
        name = name or f"Text = '{expected_text}'"
        
        try:
            element = self.page.locator(selector).first
            actual_text = element.inner_text().strip()
            success = actual_text == expected_text
            
            if not success:
                self._log_assertion(name, False, f"Expected '{expected_text}', got '{actual_text}'")
            else:
                self._log_assertion(name, True)
            
            return success
        except Exception as e:
            self._log_assertion(name, False, str(e)[:100])
            return False
    
    # FIELD VALUE ASSERTIONS
    
    def assert_input_value(
        self,
        selector: str,
        expected_value: str,
        name: str = None
    ) -> bool:
        """Assert input field value equals expected"""
        name = name or f"Input value = '{expected_value}'"
        
        try:
            element = self.page.locator(selector).first
            actual_value = element.input_value()
            success = actual_value == expected_value
            
            if not success:
                self._log_assertion(name, False, f"Expected '{expected_value}', got '{actual_value}'")
            else:
                self._log_assertion(name, True)
            
            return success
        except Exception as e:
            self._log_assertion(name, False, str(e)[:100])
            return False
    
    def assert_select_value(
        self,
        selector: str,
        expected_value: str,
        name: str = None
    ) -> bool:
        """Assert select field value equals expected"""
        name = name or f"Select value = '{expected_value}'"
        
        try:
            element = self.page.locator(selector).first
            actual_value = element.input_value()
            success = actual_value == expected_value
            
            if not success:
                self._log_assertion(name, False, f"Expected '{expected_value}', got '{actual_value}'")
            else:
                self._log_assertion(name, True)
            
            return success
        except Exception as e:
            self._log_assertion(name, False, str(e)[:100])
            return False
    
    # STATE ASSERTIONS
    
    def assert_element_disabled(
        self,
        selector: str,
        name: str = None
    ) -> bool:
        """Assert element is disabled"""
        name = name or f"Element '{selector}' disabled"
        
        try:
            element = self.page.locator(selector).first
            is_disabled = element.is_disabled()
            
            if is_disabled:
                self._log_assertion(name, True)
            else:
                self._log_assertion(name, False, "Element is enabled (should be disabled)")
            
            return is_disabled
        except Exception as e:
            self._log_assertion(name, False, str(e)[:100])
            return False
    
    def assert_element_enabled(
        self,
        selector: str,
        name: str = None
    ) -> bool:
        """Assert element is enabled"""
        name = name or f"Element '{selector}' enabled"
        
        try:
            element = self.page.locator(selector).first
            is_disabled = element.is_disabled()
            
            if not is_disabled:
                self._log_assertion(name, True)
            else:
                self._log_assertion(name, False, "Element is disabled (should be enabled)")
            
            return not is_disabled
        except Exception as e:
            self._log_assertion(name, False, str(e)[:100])
            return False
    
    def assert_checkbox_checked(
        self,
        selector: str,
        name: str = None
    ) -> bool:
        """Assert checkbox is checked"""
        name = name or f"Checkbox '{selector}' checked"
        
        try:
            element = self.page.locator(selector).first
            is_checked = element.is_checked()
            
            if is_checked:
                self._log_assertion(name, True)
            else:
                self._log_assertion(name, False, "Checkbox not checked")
            
            return is_checked
        except Exception as e:
            self._log_assertion(name, False, str(e)[:100])
            return False
    
    def assert_checkbox_unchecked(
        self,
        selector: str,
        name: str = None
    ) -> bool:
        """Assert checkbox is NOT checked"""
        name = name or f"Checkbox '{selector}' unchecked"
        
        try:
            element = self.page.locator(selector).first
            is_checked = element.is_checked()
            
            if not is_checked:
                self._log_assertion(name, True)
            else:
                self._log_assertion(name, False, "Checkbox is checked (should be unchecked)")
            
            return not is_checked
        except Exception as e:
            self._log_assertion(name, False, str(e)[:100])
            return False
    
    # MESSAGE ASSERTIONS (success, warning, error)
    
    def assert_success_message(
        self,
        expected_text: Optional[str] = None,
        name: str = "Success message displayed",
        timeout: int = 5000
    ) -> bool:
        """Assert success message is displayed"""
        success_selectors = [
            "text=/sucesso|success|salvo|saved/i",
            "[class*='success']",
            "[class*='alert-success']",
            ".toast-success",
        ]
        
        for selector in success_selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible(timeout=timeout):
                    if expected_text:
                        actual_text = element.inner_text()
                        if expected_text.lower() in actual_text.lower():
                            self._log_assertion(name, True, f"Found: '{actual_text[:50]}'")
                            return True
                    else:
                        self._log_assertion(name, True)
                        return True
            except:
                continue
        
        self._log_assertion(name, False, "No success message found")
        return False
    
    def assert_error_message(
        self,
        expected_text: Optional[str] = None,
        name: str = "Error message displayed",
        timeout: int = 5000
    ) -> bool:
        """Assert error message is displayed"""
        error_selectors = [
            "text=/erro|error|falhou|failed/i",
            "[class*='error']",
            "[class*='alert-danger']",
            ".toast-error",
        ]
        
        for selector in error_selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible(timeout=timeout):
                    if expected_text:
                        actual_text = element.inner_text()
                        if expected_text.lower() in actual_text.lower():
                            self._log_assertion(name, True, f"Found: '{actual_text[:50]}'")
                            return True
                    else:
                        self._log_assertion(name, True)
                        return True
            except:
                continue
        
        self._log_assertion(name, False, "No error message found")
        return False
    
    def assert_warning_message(
        self,
        expected_text: Optional[str] = None,
        name: str = "Warning message displayed",
        timeout: int = 5000
    ) -> bool:
        """Assert warning message is displayed"""
        warning_selectors = [
            "text=/aviso|warning|atenção|attention/i",
            "[class*='warning']",
            "[class*='alert-warning']",
            ".toast-warning",
        ]
        
        for selector in warning_selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible(timeout=timeout):
                    if expected_text:
                        actual_text = element.inner_text()
                        if expected_text.lower() in actual_text.lower():
                            self._log_assertion(name, True, f"Found: '{actual_text[:50]}'")
                            return True
                    else:
                        self._log_assertion(name, True)
                        return True
            except:
                continue
        
        self._log_assertion(name, False, "No warning message found")
        return False
    
    # MODAL ASSERTIONS
    
    def assert_modal_open(
        self,
        name: str = "Modal is open",
        timeout: int = 5000
    ) -> bool:
        """Assert modal is open/visible"""
        modal_selectors = [
            ".modal.show",
            "[role='dialog']",
            ".modal-content",
        ]
        
        for selector in modal_selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible(timeout=timeout):
                    self._log_assertion(name, True)
                    return True
            except:
                continue
        
        self._log_assertion(name, False, "No modal found")
        return False
    
    def assert_modal_closed(
        self,
        name: str = "Modal is closed",
        timeout: int = 2000
    ) -> bool:
        """Assert modal is closed/not visible"""
        modal_selectors = [
            ".modal.show",
            "[role='dialog']",
        ]
        
        for selector in modal_selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible(timeout=timeout):
                    self._log_assertion(name, False, "Modal is still visible")
                    return False
            except:
                continue
        
        self._log_assertion(name, True)
        return True
    
    # STATS AND REPORTING
    
    def get_stats(self) -> Dict:
        """Get assertion statistics"""
        total = self.assertions_passed + self.assertions_failed
        return {
            "total": total,
            "passed": self.assertions_passed,
            "failed": self.assertions_failed,
            "success_rate": (self.assertions_passed / total * 100) if total > 0 else 0
        }
    
    def print_summary(self):
        """Print assertion summary"""
        stats = self.get_stats()
        
        print("\n" + "="*70)
        print("VALIDATION SUMMARY")
        print("="*70)
        print(f"Total assertions: {stats['total']}")
        print(f"Passed: {stats['passed']}")
        print(f"Failed: {stats['failed']}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        
        if self.assertions_failed > 0:
            print(f"\nFailed assertions:")
            for log in self.assertion_log:
                if not log["success"]:
                    print(f"  - {log['name']}: {log['details']}")
        
        print("="*70)
    
    def reset(self):
        """Reset assertion counters"""
        self.assertions_passed = 0
        self.assertions_failed = 0
        self.assertion_log = []
