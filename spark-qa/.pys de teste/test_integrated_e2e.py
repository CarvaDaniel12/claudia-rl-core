"""
Test Integrated E2E Flow
Tests the old E2E flow with V2 create/delete methods integrated
"""
import sys
sys.path.insert(0, 'c:\\Users\\User\\Desktop\\Spark QA tool face\\hunter-python')

from playwright.sync_api import sync_playwright
from flows.ultimate_platform_flow import UltimatePlatformFlow
from config import Config

def test_integrated_e2e():
    """
    Test old E2E with V2 integration:
    1. Login
    2. Create Property (V2 method)
    3. Delete Property (V2 method)

    This validates that V2 methods work correctly in the old flow structure!
    """
    print("="*70)
    print("[TEST] TEST: Integrated E2E (Old Flow + V2 Methods)")
    print("="*70)

    config = Config()

    # Convert Config object to dict for flows
    config_dict = {
        "base_url": "https://platform.test.hostfully.com/app/",
        "email": Config.EMAIL,
        "password": Config.PASSWORD
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()

        try:
            # Create flow instance with config dict
            flow = UltimatePlatformFlow(page, config_dict)

            print("\n" + "="*70)
            print(" STEP 1: Login")
            print("="*70)
            if not flow.login():
                print("[FAIL] Login failed!")
                return
            print("[OK] Login successful\n")

            print("="*70)
            print(" STEP 2: Create Property (V2 Method)")
            print("="*70)
            if not flow.create_property_complete():
                print("[FAIL] Property creation failed!")
                return
            print(f"[OK] Property created: {flow.property_name}\n")

            print("="*70)
            print("[TRASH] STEP 3: Delete Property (V2 Method)")
            print("="*70)
            if not flow._cleanup_property():
                print("[FAIL] Property deletion failed!")
                return
            print(f"[OK] Property deleted successfully!\n")

            print("="*70)
            print("[CHART] FINAL RESULTS")
            print("="*70)
            print("[PARTY] ALL STEPS PASSED!")
            print("="*70)
            print("[OK] Login")
            print("[OK] Create Property (V2)")
            print("[OK] Delete Property (V2)")
            print("="*70)
            print("\n INTEGRATION TEST COMPLETE - V2 METHODS WORK IN OLD FLOW!\n")

            # Keep browser open for inspection
            print("⏸ Browser will stay open for 10 seconds for inspection...")
            page.wait_for_timeout(10000)

        except Exception as e:
            print(f"\n[FAIL] TEST FAILED: {e}")
            page.screenshot(path="test_integrated_e2e_FAILED.png")
            # Keep browser open on error
            print("\n⏸ Browser will stay open for 30 seconds for debugging...")
            page.wait_for_timeout(30000)
            raise
        finally:
            browser.close()
            print("[OK] Test complete!")

if __name__ == "__main__":
    test_integrated_e2e()
