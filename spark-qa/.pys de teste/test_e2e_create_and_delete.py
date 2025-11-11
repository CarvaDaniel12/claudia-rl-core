"""
TEST: Complete E2E Flow - Create Property + Delete (CLEANUP)

WHAT IT TESTS:
1. Login
2. Navigate to Properties
3. Create property (open form)
4. Fill all fields (progressive validation)
5. Save property
6. DELETE property (cleanup - avoid test data pollution!)

This is the GOLDEN PATH for E2E testing with proper cleanup!
"""

import sys
import os
from pathlib import Path

# Add hunter-python to path
hunter_path = Path(__file__).parent.parent / "hunter-python"
sys.path.insert(0, str(hunter_path))

from playwright.sync_api import sync_playwright
from flows.ultimate_platform_flow_V2 import UltimatePlatformFlowV2
from config import Config
import time

def main():
    print("\n" + "="*70)
    print("[TEST] TEST: Complete E2E - Create + Delete Property")
    print("="*70)

    config = Config()
    config_dict = {
        "base_url": config.BASE_URL,
        "email": config.EMAIL,
        "password": config.PASSWORD
    }

    results = {
        "test_name": "e2e_create_and_delete",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "steps": []
    }

    property_name = None  # Will store property name for cleanup

    with sync_playwright() as p:
        # Launch browser (headless=False to watch! slow_mo reduced for speed)
        browser = p.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # Initialize Flow V2
        flow = UltimatePlatformFlowV2(page, config_dict, headless=False)

        try:
            # ================================================================
            # STEP 1: Login
            # ================================================================
            print("\n" + "="*70)
            print(" STEP 1: Login")
            print("="*70)
            login_result = flow.login()
            results["steps"].append({"step": "login", "result": login_result})

            if not login_result["success"]:
                print("[FAIL] Login failed - aborting test")
                return

            print("[OK] Login successful")
            time.sleep(2)

            # ================================================================
            # STEP 2: Navigate to Properties
            # ================================================================
            print("\n" + "="*70)
            print(" STEP 2: Navigate to Properties")
            print("="*70)
            nav_result = flow.navigate_to_properties()
            results["steps"].append({"step": "navigate_to_properties", "result": nav_result})

            if not nav_result["success"]:
                print("[FAIL] Navigation failed - aborting test")
                return

            print("[OK] Navigation successful")
            time.sleep(2)

            # ================================================================
            # STEP 3: Create Property (Open Form)
            # ================================================================
            print("\n" + "="*70)
            print(" STEP 3: Create Property (Open Form)")
            print("="*70)
            create_result = flow.create_property(property_type="single")
            results["steps"].append({"step": "create_property", "result": create_result})

            if not create_result["success"]:
                print("[FAIL] Create property failed - aborting test")
                return

            print("[OK] Property creation form opened")
            time.sleep(2)

            # ================================================================
            # STEP 4: Fill Form (Progressive Validation)
            # ================================================================
            print("\n" + "="*70)
            print("[NOTE] STEP 4: Fill Form (Progressive Validation)")
            print("="*70)
            fill_result = flow.fill_and_validate_property_form()
            results["steps"].append({"step": "fill_and_validate_form", "result": fill_result})

            if not fill_result["success"]:
                print("\n[FAIL] Form filling failed!")
                print(f"Fields filled: {fill_result['fields_filled']}")
                print(f"Errors: {fill_result['errors']}")
                print("\n[WARNING] Continuing to cleanup anyway (if property was created)...")
            else:
                print("\n[OK] Form filled and saved successfully!")
                print(f"Validations tested: {fill_result['validations_tested']}")
                print(f"Fields filled: {fill_result['fields_filled']}")

            # Store property name for cleanup
            property_name = fill_result.get("property_name")
            if not property_name:
                print("[WARNING] Property name not found - cannot cleanup!")
                return

            print(f"\n Property created: {property_name}")
            time.sleep(3)

            # ================================================================
            # STEP 5: DELETE Property (CLEANUP!)
            # ================================================================
            print("\n" + "="*70)
            print("[TRASH] STEP 5: DELETE Property (CLEANUP)")
            print("="*70)
            print(f"Deleting property: {property_name}")
            print("[WARNING] This is CRITICAL to avoid polluting the account with test data!")

            delete_result = flow.delete_property(property_name)
            results["steps"].append({"step": "delete_property", "result": delete_result})

            if delete_result["success"]:
                print(f"\n[OK] Property '{property_name}' deleted successfully!")
                print("[OK] Cleanup complete - no test data left behind!")
            else:
                print(f"\n[FAIL] Failed to delete property '{property_name}'!")
                print(f"Errors: {delete_result['errors']}")
                print("[WARNING] MANUAL CLEANUP REQUIRED!")

            time.sleep(2)

            # ================================================================
            # FINAL RESULTS
            # ================================================================
            print("\n" + "="*70)
            print("[CHART] FINAL RESULTS")
            print("="*70)

            all_success = all(
                step["result"].get("success", False)
                for step in results["steps"]
            )

            if all_success:
                print("[PARTY] ALL STEPS PASSED!")
                print("="*70)
                print("[OK] Login")
                print("[OK] Navigate to Properties")
                print("[OK] Create Property Form")
                print("[OK] Fill & Validate Form")
                print("[OK] Delete Property (Cleanup)")
                print("="*70)
                print("\n E2E TEST COMPLETE - CLEAN RUN!")
            else:
                print("[WARNING] SOME STEPS FAILED")
                print("="*70)
                for step in results["steps"]:
                    status = "[OK]" if step["result"].get("success") else "[FAIL]"
                    print(f"{status} {step['step']}")
                print("="*70)

            # Keep browser open for inspection
            print("\n⏸ Browser will stay open for 10 seconds for inspection...")
            time.sleep(10)

        except Exception as e:
            print(f"\n[FAIL] TEST ERROR: {e}")
            import traceback
            traceback.print_exc()

            # Try to cleanup even if test failed
            if property_name:
                print(f"\n[TRASH] Attempting cleanup of property: {property_name}")
                try:
                    delete_result = flow.delete_property(property_name)
                    if delete_result["success"]:
                        print("[OK] Emergency cleanup successful!")
                    else:
                        print("[FAIL] Emergency cleanup failed - manual cleanup required!")
                except:
                    print("[FAIL] Could not perform emergency cleanup!")

        finally:
            browser.close()

    print("\n[OK] Test complete!")

if __name__ == "__main__":
    main()
