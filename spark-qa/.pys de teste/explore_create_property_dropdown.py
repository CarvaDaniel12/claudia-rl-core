"""
EXPLORATION: Create Property Dropdown Options

Maps what happens when you click "Adicionar propriedade":
- Dropdown menu options (tipos de propriedade)
- Cada opção (House, Apartment, Condo, etc)
- Links/actions de cada opção

Output: CREATE_PROPERTY_DROPDOWN.json + screenshots
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
    print("[SEARCH] EXPLORATION: Create Property Dropdown")
    print("=" * 80)

    config = {
        "base_url": "https://platform.test.hostfully.com/app/#/login",
        "username": "daniel+pmp@hostfully.com",
        "password": "pas123"
    }

    findings = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dropdown_options": [],
        "screenshots": []
    }

    with sync_playwright() as p:
        print("\n Launching browser...")
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        try:
            # Initialize flow
            flow = UltimatePlatformFlowV2(page, config, headless=False)

            # Login
            print("\n Logging in...")
            login_result = flow.login()
            if not login_result["success"]:
                print(f"[FAIL] Login failed: {login_result.get('error')}")
                return
            print("[OK] Login successful")
            time.sleep(2)

            # Navigate to properties
            print("\n Navigating to Properties...")
            nav_result = flow.navigate_to_properties()
            if not nav_result["success"]:
                print(f"[FAIL] Navigation failed: {nav_result.get('error')}")
                return
            print("[OK] Navigation successful")
            time.sleep(2)

            # Screenshot BEFORE clicking dropdown
            base_path = Path(__file__).parent.parent / "hunter-python"
            screenshot_before = base_path / "CREATE_DROPDOWN_BEFORE.png"
            page.screenshot(path=str(screenshot_before))
            print(f"\n Screenshot before: {screenshot_before}")
            findings["screenshots"].append(str(screenshot_before))

            # Find and click "Adicionar propriedade" button
            print("\n Looking for 'Adicionar propriedade' button...")

            add_button = flow._find_element([
                {"type": "testid", "value": "add-property-button"},
                {"type": "text", "value": "Adicionar propriedade"},
                {"type": "class", "value": "dropdown-toggle"},
            ], "add property button")

            if not add_button:
                print("[FAIL] Could not find add property button")
                return

            print("[OK] Found button, clicking...")
            add_button.click()
            time.sleep(1)

            # Screenshot AFTER clicking dropdown
            screenshot_after = base_path / "CREATE_DROPDOWN_AFTER.png"
            page.screenshot(path=str(screenshot_after))
            print(f" Screenshot after: {screenshot_after}")
            findings["screenshots"].append(str(screenshot_after))

            # Map dropdown options
            print("\n Mapping dropdown options...")

            # Try multiple patterns to find dropdown menu
            dropdown_patterns = [
                {"selector": ".dropdown-menu:visible", "type": "class"},
                {"selector": "[role='menu']:visible", "type": "role"},
                {"selector": ".dropdown-menu.show", "type": "class"},
                {"selector": "ul.dropdown-menu", "type": "tag"},
            ]

            dropdown_menu = None
            for pattern in dropdown_patterns:
                try:
                    menu = page.locator(pattern["selector"]).first
                    if menu.is_visible():
                        dropdown_menu = menu
                        print(f"[OK] Found dropdown via {pattern['type']}: {pattern['selector']}")
                        break
                except:
                    pass

            if not dropdown_menu:
                print("[WARNING]  Could not find dropdown menu - trying to find menu items directly")
                # Try to find menu items directly
                menu_items = page.locator("a, button, li").all()
            else:
                # Get items within dropdown
                menu_items = dropdown_menu.locator("a, button, li").all()

            print(f"\n[SEARCH] Found {len(menu_items)} potential menu items, analyzing...")

            for i, item in enumerate(menu_items):
                try:
                    if not item.is_visible():
                        continue

                    item_data = {
                        "index": i,
                        "tag": item.evaluate("el => el.tagName"),
                        "text": item.inner_text()[:100],
                        "href": item.get_attribute("href"),
                        "testid": item.get_attribute("data-testid"),
                        "class": item.get_attribute("class"),
                        "role": item.get_attribute("role"),
                    }

                    # Filter out empty or irrelevant items
                    if item_data["text"].strip():
                        findings["dropdown_options"].append(item_data)
                        print(f"  Option #{i}: '{item_data['text'][:50]}' href={item_data['href']}")

                except Exception as e:
                    print(f"  [WARNING]  Item #{i} error: {str(e)[:50]}")

            # Save findings
            output_path = base_path / "CREATE_PROPERTY_DROPDOWN.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(findings, f, indent=2, ensure_ascii=False)

            print(f"\n[SAVE] Exploration data saved: {output_path}")

            # Summary
            print("\n" + "=" * 80)
            print("[CHART] SUMMARY")
            print("=" * 80)
            print(f"Dropdown options found: {len(findings['dropdown_options'])}")

            if findings['dropdown_options']:
                print("\n[TARGET] PROPERTY TYPE OPTIONS:")
                for opt in findings['dropdown_options']:
                    print(f"  - '{opt['text'][:60]}' (href={opt['href']})")

            print("\n[OK] Exploration complete!")
            print("\n⏸  Closing in 5 seconds (check dropdown on screen)...")
            time.sleep(5)

        except Exception as e:
            print(f"\n[FAIL] Exploration failed: {str(e)}")
            import traceback
            traceback.print_exc()

            print("\n⏸  Closing in 5 seconds...")
            time.sleep(5)

        finally:
            browser.close()
            print("[LOCKED] Browser closed")


if __name__ == "__main__":
    main()
