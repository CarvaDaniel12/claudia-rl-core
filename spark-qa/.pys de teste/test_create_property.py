"""
Test Runner: Login → Properties → Create Property

Tests the complete navigation flow including property creation:
- Login with OAuth fix (Enter key)
- Navigate to Properties
- Click "Adicionar propriedade" dropdown
- Select "Propriedade única"

Expected outputs:
- Structured JSON with state transitions
- Screenshots at each checkpoint
- Validation of property creation form loading
"""

import sys
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

# Add hunter-python to path
root_path = Path(__file__).parent.parent
hunter_python_path = root_path / "hunter-python"
sys.path.insert(0, str(hunter_python_path))

from flows.ultimate_platform_flow_V2 import UltimatePlatformFlowV2

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


def main():
    print("=" * 80)
    print("[TEST] TEST: Login → Properties → Create Property")
    print("=" * 80)

    config = {
        "base_url": "https://platform.test.hostfully.com/app/#/login",
        "username": "daniel+pmp@hostfully.com",
        "password": "pas123"
    }

    # Store results for RL analysis
    results = {
        "test_name": "create_property_flow",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "steps": []
    }

    with sync_playwright() as p:
        print("\n Launching browser...")
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # Capture console errors
        console_messages = []
        def handle_console(msg):
            console_messages.append(f"[{msg.type}] {msg.text}")
            if msg.type in ["error", "warning"]:
                print(f"[RED] CONSOLE {msg.type.upper()}: {msg.text}")

        page.on("console", handle_console)

        try:
            # Initialize flow
            flow = UltimatePlatformFlowV2(page, config, headless=False)

            # =====================================================================
            # STEP 1: Login
            # =====================================================================
            print("\n" + "=" * 80)
            print("STEP 1: Login")
            print("=" * 80)

            login_result = flow.login()
            results["steps"].append({
                "step": "login",
                "result": login_result
            })

            print("\n[CHART] Login Result:")
            print(json.dumps(login_result, indent=2))

            if not login_result["success"]:
                print("\n[FAIL] Login failed - aborting test")
                return

            print("\n[OK] Login successful")
            time.sleep(2)

            # =====================================================================
            # STEP 2: Navigate to Properties
            # =====================================================================
            print("\n" + "=" * 80)
            print("STEP 2: Navigate to Properties")
            print("=" * 80)

            nav_result = flow.navigate_to_properties()
            results["steps"].append({
                "step": "navigate_to_properties",
                "result": nav_result
            })

            print("\n[CHART] Navigation Result:")
            print(json.dumps(nav_result, indent=2))

            if not nav_result["success"]:
                print("\n[FAIL] Navigation failed - aborting test")
                return

            print("\n[OK] Navigation successful")
            time.sleep(2)

            # =====================================================================
            # STEP 3: Create Property (open dropdown + select type)
            # =====================================================================
            print("\n" + "=" * 80)
            print("STEP 3: Create Property (Dropdown + Select)")
            print("=" * 80)

            create_result = flow.create_property(property_type="single")
            results["steps"].append({
                "step": "create_property",
                "result": create_result
            })

            print("\n[CHART] Create Property Result:")
            print(json.dumps(create_result, indent=2))

            if not create_result["success"]:
                print("\n[FAIL] Create property failed")
            else:
                print("\n[OK] Property creation form opened successfully")

            time.sleep(3)

            # =====================================================================
            # SAVE RESULTS
            # =====================================================================
            print("\n" + "=" * 80)
            print("Saving Test Results")
            print("=" * 80)

            output_file = str(hunter_python_path / "CREATE_PROPERTY_TEST_RESULTS.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            print(f"\n[NOTE] Results saved to: {output_file}")

            # =====================================================================
            # SUMMARY
            # =====================================================================
            print("\n" + "=" * 80)
            print("TEST SUMMARY")
            print("=" * 80)

            total_steps = len(results["steps"])
            successful_steps = sum(1 for step in results["steps"] if step["result"]["success"])

            print(f"\n[OK] Successful steps: {successful_steps}/{total_steps}")

            for i, step in enumerate(results["steps"], 1):
                step_name = step["step"]
                step_result = step["result"]
                status = "[OK] PASS" if step_result["success"] else "[FAIL] FAIL"

                print(f"\n{i}. {step_name}: {status}")
                print(f"   State transition: {step_result['state_from']} → {step_result['state_to']}")
                print(f"   Actions: {len(step_result.get('actions', []))}")
                print(f"   Selectors used: {len(step_result.get('selectors_used', []))}")

                if not step_result["success"] and "error" in step_result:
                    print(f"   Error: {step_result['error']}")

            print("\n" + "=" * 80)
            print("[TARGET] RL LEARNING POINTS")
            print("=" * 80)

            # Analyze which selectors worked for RL learning
            for step in results["steps"]:
                step_name = step["step"]
                selectors = step["result"].get("selectors_used", [])

                if selectors:
                    print(f"\n{step_name}:")
                    for sel in selectors:
                        print(f"  - {sel}")

            # Check current URL
            print(f"\n Final URL: {page.url}")

            print("\n" + "=" * 80)
            print("\n⏸  Closing in 5 seconds (check property creation form on screen)...")
            time.sleep(5)

        except Exception as e:
            print(f"\n[FAIL] Test failed with exception: {str(e)}")
            import traceback
            traceback.print_exc()

            # Save error state
            results["error"] = str(e)
            error_file = str(hunter_python_path / "CREATE_PROPERTY_TEST_ERROR.json")
            with open(error_file, 'w') as f:
                json.dump(results, f, indent=2)

            print(f"\n[NOTE] Error state saved to: {error_file}")
            print("\n⏸  Closing in 5 seconds...")
            time.sleep(5)

        finally:
            browser.close()
            print("[LOCKED] Browser closed")
            print("\n[OK] Test complete!")


if __name__ == "__main__":
    main()
