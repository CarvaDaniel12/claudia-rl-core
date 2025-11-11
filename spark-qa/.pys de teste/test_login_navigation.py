"""
Test Runner: Login → Dashboard → Properties Navigation

Tests the foundational flow with new RL-optimized architecture:
- Multi-selector fallback (_find_element)
- Fuzzy validation (validate_state)
- Structured JSON outputs for RL consumption

Expected outputs:
- Structured dicts with {state_from, state_to, actions, selectors_used, success}
- Screenshots at each checkpoint
- Logs showing which selectors worked
"""

import sys
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

# Add hunter-python directory to path
# .pys de teste is at root level, hunter-python is sibling folder
root_path = Path(__file__).parent.parent
hunter_python_path = root_path / "hunter-python"
sys.path.insert(0, str(hunter_python_path))

from flows.ultimate_platform_flow_V2 import UltimatePlatformFlowV2

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


def main():
    print("=" * 80)
    print("[TEST] TEST: Login → Dashboard → Properties Navigation")
    print("=" * 80)

    config = {
        "base_url": "https://platform.test.hostfully.com/app/#/login",
        "username": "daniel+pmp@hostfully.com",
        "password": "pas123"
    }

    # Store results for RL analysis
    results = {
        "test_name": "login_navigation_flow",
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
                print("\n[FAIL] Navigation failed")
            else:
                print("\n[OK] Navigation successful")

            time.sleep(2)

            # =====================================================================
            # SAVE RESULTS
            # =====================================================================
            print("\n" + "=" * 80)
            print("Saving Test Results")
            print("=" * 80)

            output_file = "LOGIN_NAVIGATION_TEST_RESULTS.json"
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

            print("\n" + "=" * 80)

            # Keep browser open for inspection
            print("\n⏸  Browser kept open for inspection. Press Enter to close...")
            input()

        except Exception as e:
            print(f"\n[FAIL] Test failed with exception: {str(e)}")
            import traceback
            traceback.print_exc()

            # Save error state
            results["error"] = str(e)
            with open("LOGIN_NAVIGATION_TEST_ERROR.json", 'w') as f:
                json.dump(results, f, indent=2)

            print("\n⏸  Browser kept open for debugging. Press Enter to close...")
            input()

        finally:
            browser.close()
            print("\n[OK] Test complete!")


if __name__ == "__main__":
    main()
