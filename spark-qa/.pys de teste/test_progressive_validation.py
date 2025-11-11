"""
TEST: Progressive Validation Strategy

WHAT IT TESTS:
1. Fill propertyName → Try save (MUST FAIL - button disabled)
2. Fill each required field one by one → Try save after each (MUST FAIL)
3. Fill ALL optional fields (before last required)
4. Fill last required field → Save (MUST SUCCEED!)

EXPECTED BEHAVIOR:
- Save button DISABLED until ALL required fields filled
- Save button ENABLED after last required field
- Form saves successfully and redirects

Based on: PROPERTY_CREATION_FORM.json exploration
"""

import sys
import os
from pathlib import Path

# Add hunter-python to path
hunter_path = Path(__file__).parent.parent / "hunter-python"
sys.path.insert(0, str(hunter_path))

from playwright.sync_api import sync_playwright
from flows.ultimate_platform_flow_V2 import UltimatePlatformFlowV2
import time

def load_config():
    """Load credentials"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "hunter-python"))
    from config import Config

    config = Config()
    return {
        "base_url": config.BASE_URL,
        "email": config.EMAIL,
        "password": config.PASSWORD
    }

def main():
    print("\n" + "="*70)
    print("[TEST] TEST: Progressive Validation Strategy")
    print("="*70)

    config = load_config()

    results = {
        "test_name": "progressive_validation",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "steps": []
    }

    with sync_playwright() as p:
        # Launch browser (headless=False to watch the magic!)
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # Initialize Flow V2
        flow = UltimatePlatformFlowV2(page, config, headless=False)

        try:
            # STEP 1: Login
            print("\n STEP 1: Login")
            login_result = flow.login()
            results["steps"].append({"step": "login", "result": login_result})

            if not login_result["success"]:
                print("[FAIL] Login failed - aborting test")
                return

            print("[OK] Login successful")
            time.sleep(2)

            # STEP 2: Navigate to Properties
            print("\n STEP 2: Navigate to Properties")
            nav_result = flow.navigate_to_properties()
            results["steps"].append({"step": "navigate_to_properties", "result": nav_result})

            if not nav_result["success"]:
                print("[FAIL] Navigation failed - aborting test")
                return

            print("[OK] Navigation successful")
            time.sleep(2)

            # STEP 3: Open Property Creation Form
            print("\n STEP 3: Open Property Creation Form")
            create_result = flow.create_property(property_type="single")
            results["steps"].append({"step": "create_property", "result": create_result})

            if not create_result["success"]:
                print("[FAIL] Create property failed - aborting test")
                return

            print("[OK] Property creation form opened")
            time.sleep(2)

            # STEP 4: Fill Form with Progressive Validation
            print("\n[NOTE] STEP 4: Fill Form (Progressive Validation Strategy)")
            print("This will:")
            print("  1. Fill propertyName → Try save (should fail)")
            print("  2. Fill each required field → Try save after each (should fail)")
            print("  3. Fill ALL optional fields")
            print("  4. Fill last required → Save (should succeed!)")

            fill_result = flow.fill_and_validate_property_form()
            results["steps"].append({"step": "fill_and_validate_form", "result": fill_result})

            if fill_result["success"]:
                print("\n" + "="*70)
                print("[PARTY] TEST PASSED!")
                print("="*70)
                print(f"[OK] Validations tested: {fill_result['validations_tested']}")
                print(f"[OK] Fields filled: {fill_result['fields_filled']}")
                print(f"[OK] Property created: {fill_result['property_name']}")

                if fill_result["errors"]:
                    print(f"\n[WARNING] Warnings ({len(fill_result['errors'])}):")
                    for err in fill_result["errors"]:
                        print(f"  - {err}")
            else:
                print("\n" + "="*70)
                print("[FAIL] TEST FAILED!")
                print("="*70)
                print(f"Validations tested: {fill_result['validations_tested']}")
                print(f"Fields filled: {fill_result['fields_filled']}")
                print(f"\nErrors ({len(fill_result['errors'])}):")
                for err in fill_result["errors"]:
                    print(f"  - {err}")

            # Keep browser open for inspection
            print("\n⏸ Browser will stay open for 10 seconds for inspection...")
            time.sleep(10)

        except Exception as e:
            print(f"\n[FAIL] TEST ERROR: {e}")
            import traceback
            traceback.print_exc()

        finally:
            browser.close()

    print("\n[OK] Test complete!")

if __name__ == "__main__":
    main()
