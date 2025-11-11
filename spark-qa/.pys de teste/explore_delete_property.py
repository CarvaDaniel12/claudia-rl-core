"""
EXPLORER: Property Delete Flow

GOAL: Discover how to delete a property
- Search for property by name
- Click actions menu (3 dots)
- Explore dropdown options
- Click delete/remove option
- Handle confirmation modal
- Verify deletion

Based on: PROPERTIES_LIST_EXPLORATION.json
- propertySearch: testid="propertySearch", placeholder="Nome da propriedade ou UID"
- actions menu: testid="property-actions-menu"
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
import json

def explore_delete_flow(page, property_name="ExploreTest"):
    """
    Explore the property deletion flow

    Args:
        page: Playwright page object
        property_name: Name of property to search for and explore delete options
    """
    print(f"\n[SEARCH] EXPLORING: Delete Property Flow for '{property_name}'")

    findings = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "page_url": page.url,
        "property_searched": property_name,
        "search_field": {},
        "property_found": False,
        "actions_menu": {},
        "dropdown_options": [],
        "delete_option": {},
        "confirmation_modal": {},
        "steps_taken": []
    }

    try:
        # STEP 1: Find and use search field
        print("\n STEP 1: Searching for property...")

        search_selectors = [
            'input[data-testid="propertySearch"]',
            '[data-testid="propertySearch"]',
            'input[placeholder*="Nome da propriedade"]',
            'input.rbt-input-main',
        ]

        search_field = None
        for selector in search_selectors:
            try:
                search_field = page.locator(selector).first
                if search_field.is_visible(timeout=2000):
                    findings["search_field"] = {
                        "selector_found": selector,
                        "testid": "propertySearch",
                        "placeholder": search_field.get_attribute("placeholder")
                    }
                    print(f"[OK] Found search field: {selector}")
                    break
            except:
                continue

        if not search_field:
            raise Exception("Could not find search field!")

        # Fill search and press ENTER to filter
        search_field.click()
        search_field.fill(property_name)
        search_field.press("Enter")  # CRITICAL: Press Enter to actually filter!
        findings["steps_taken"].append(f"Searched for: {property_name} (pressed Enter)")
        print(f"[OK] Searched for: {property_name} + pressed Enter")
        time.sleep(2)  # Wait for filtered results

        page.screenshot(path="SEARCH_RESULTS.png", full_page=True)
        print(" Screenshot: SEARCH_RESULTS.png")

        # STEP 2: Check if property appears in results
        print("\n STEP 2: Checking if property exists in results...")

        # Look for property name in results
        try:
            property_element = page.locator(f"text={property_name}").first
            if property_element.is_visible(timeout=3000):
                findings["property_found"] = True
                print(f"[OK] Property '{property_name}' found in results!")
            else:
                findings["property_found"] = False
                print(f"[WARNING] Property '{property_name}' NOT found - might not exist yet")
                return findings
        except:
            findings["property_found"] = False
            print(f"[WARNING] Property '{property_name}' NOT found in search results")
            return findings

        # STEP 3: Find and click actions menu (3 dots)
        print("\n STEP 3: Finding actions menu (3 dots)...")

        actions_menu_selectors = [
            'button[data-testid="property-actions-menu"]',
            '[data-testid="property-actions-menu"]',
            'button.dropdown-toggle.btn-xs',
        ]

        actions_menu = None
        for selector in actions_menu_selectors:
            try:
                # Get all actions menus on page
                all_menus = page.locator(selector).all()
                print(f"  Found {len(all_menus)} actions menus on page")

                # Click the FIRST one (should be for our searched property)
                if len(all_menus) > 0:
                    actions_menu = all_menus[0]
                    findings["actions_menu"] = {
                        "selector_found": selector,
                        "testid": "property-actions-menu",
                        "count_on_page": len(all_menus)
                    }
                    print(f"[OK] Found actions menu: {selector}")
                    break
            except:
                continue

        if not actions_menu:
            raise Exception("Could not find actions menu!")

        # Click actions menu
        actions_menu.click()
        findings["steps_taken"].append("Clicked actions menu")
        print("[OK] Clicked actions menu")
        time.sleep(1)  # Wait for dropdown

        page.screenshot(path="ACTIONS_DROPDOWN_OPENED.png", full_page=True)
        print(" Screenshot: ACTIONS_DROPDOWN_OPENED.png")

        # STEP 4: Explore dropdown options
        print("\n STEP 4: Exploring dropdown options...")

        # Look for dropdown menu items
        dropdown_selectors = [
            'ul.dropdown-menu li a',
            '.dropdown-menu a',
            'ul.dropdown-menu li',
        ]

        options = []
        for selector in dropdown_selectors:
            try:
                elements = page.locator(selector).all()
                if len(elements) > 0:
                    print(f"  Found {len(elements)} dropdown options with: {selector}")

                    for i, elem in enumerate(elements):
                        try:
                            text = elem.inner_text(timeout=1000)
                            href = elem.get_attribute("href") or "N/A"
                            classes = elem.get_attribute("class") or ""

                            option = {
                                "index": i,
                                "text": text,
                                "href": href,
                                "class": classes,
                                "selector": selector
                            }
                            options.append(option)
                            print(f"    {i}: {text}")
                        except:
                            continue
                    break
            except:
                continue

        findings["dropdown_options"] = options
        print(f"[OK] Found {len(options)} dropdown options")

        # STEP 5: Find DELETE option
        print("\n STEP 5: Looking for DELETE option...")

        delete_keywords = ["apagar", "delete", "remover", "excluir", "deletar", "remove"]
        delete_option = None

        for option in options:
            text_lower = option["text"].lower()
            for keyword in delete_keywords:
                if keyword in text_lower:
                    delete_option = option
                    findings["delete_option"] = option
                    print(f"[OK] Found DELETE option: '{option['text']}'")
                    break
            if delete_option:
                break

        if not delete_option:
            print("[WARNING] DELETE option not found in dropdown!")
            return findings

        # STEP 6: Click DELETE option
        print("\n STEP 6: Clicking DELETE option...")

        delete_selector = f"{delete_option['selector']}:has-text('{delete_option['text']}')"
        delete_button = page.locator(delete_selector).first
        delete_button.click()
        findings["steps_taken"].append(f"Clicked delete option: {delete_option['text']}")
        print(f"[OK] Clicked: {delete_option['text']}")
        time.sleep(2)  # Wait for modal

        page.screenshot(path="DELETE_MODAL.png", full_page=True)
        print(" Screenshot: DELETE_MODAL.png")

        # STEP 7: Explore confirmation modal
        print("\n STEP 7: Exploring confirmation modal...")

        modal_findings = {
            "modal_found": False,
            "modal_text": "",
            "buttons": []
        }

        # Look for modal
        modal_selectors = [
            '.modal-content',
            '[role="dialog"]',
            '.modal',
        ]

        modal = None
        for selector in modal_selectors:
            try:
                modal = page.locator(selector).first
                if modal.is_visible(timeout=2000):
                    modal_findings["modal_found"] = True

                    # Get modal text
                    try:
                        modal_text = modal.inner_text(timeout=2000)
                        modal_findings["modal_text"] = modal_text
                        print(f"[OK] Modal text:\n{modal_text[:200]}...")
                    except:
                        pass

                    # Find buttons in modal
                    button_selectors = [
                        f'{selector} button',
                        f'{selector} .btn',
                    ]

                    for btn_sel in button_selectors:
                        try:
                            buttons = page.locator(btn_sel).all()
                            for i, btn in enumerate(buttons):
                                try:
                                    btn_text = btn.inner_text(timeout=1000)
                                    btn_class = btn.get_attribute("class") or ""
                                    btn_type = btn.get_attribute("type") or ""

                                    modal_findings["buttons"].append({
                                        "index": i,
                                        "text": btn_text,
                                        "class": btn_class,
                                        "type": btn_type
                                    })
                                    print(f"  Button {i}: {btn_text} ({btn_class})")
                                except:
                                    continue
                            break
                        except:
                            continue

                    break
            except:
                continue

        findings["confirmation_modal"] = modal_findings

        if not modal_findings["modal_found"]:
            print("[WARNING] Confirmation modal not found!")
        else:
            print(f"[OK] Found modal with {len(modal_findings['buttons'])} buttons")

        # DON'T actually confirm delete - just explore!
        print("\n[WARNING] NOT confirming delete - this is just exploration!")

    except Exception as e:
        print(f"\n[FAIL] Error during exploration: {e}")
        import traceback
        traceback.print_exc()
        findings["error"] = str(e)

    return findings


def main():
    print("\n" + "="*70)
    print("[SEARCH] EXPLORER: Property Delete Flow")
    print("="*70)

    config = Config()
    config_dict = {
        "base_url": config.BASE_URL,
        "email": config.EMAIL,
        "password": config.PASSWORD
    }

    with sync_playwright() as p:
        # Launch browser (headless=False to watch!)
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # Initialize Flow V2
        flow = UltimatePlatformFlowV2(page, config_dict, headless=False)

        try:
            # Login
            print("\n Logging in...")
            login_result = flow.login()
            if not login_result["success"]:
                print("[FAIL] Login failed")
                return
            print("[OK] Login successful")
            time.sleep(2)

            # Navigate to Properties
            print("\n Navigating to Properties...")
            nav_result = flow.navigate_to_properties()
            if not nav_result["success"]:
                print("[FAIL] Navigation failed")
                return
            print("[OK] Navigation successful")
            time.sleep(2)

            # Explore delete flow
            findings = explore_delete_flow(page, property_name="ExploreTest")

            # Save findings
            with open("DELETE_PROPERTY_EXPLORATION.json", "w", encoding="utf-8") as f:
                json.dump(findings, f, indent=2, ensure_ascii=False)

            print("\n" + "="*70)
            print("[OK] EXPLORATION COMPLETE")
            print("="*70)
            print(f"[FILE] Report saved: DELETE_PROPERTY_EXPLORATION.json")
            print(f" Screenshots: 3 saved")
            print(f"Property found: {findings['property_found']}")
            print(f"Delete option found: {len(findings.get('delete_option', {})) > 0}")
            print(f"Modal found: {findings.get('confirmation_modal', {}).get('modal_found', False)}")

            # Keep browser open for inspection
            print("\n⏸ Browser will stay open for 10 seconds...")
            time.sleep(10)

        except Exception as e:
            print(f"\n[FAIL] ERROR: {e}")
            import traceback
            traceback.print_exc()

        finally:
            browser.close()

    print("\n[OK] Explorer complete!")

if __name__ == "__main__":
    main()
