"""
EXPLORATION: Property Creation Form Fields

Maps the initial property creation form structure:
- Internal name field
- Address field
- Property type dropdown (House, Apartment, Condo, etc.)
- Any other visible fields on the creation modal
- Save button

This is the FIRST form that appears after clicking "Propriedade única".

Output: PROPERTY_CREATION_FORM.json + screenshots
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


def explore_form_fields(page):
    """
    Explore all fields in the property creation form
    """
    print("\n[SEARCH] EXPLORING: Form Fields")
    print("=" * 80)

    findings = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "page_url": page.url,
        "inputs": [],
        "textareas": [],
        "selects": [],
        "buttons": [],
        "labels": [],
        "form_structure": {}
    }

    # 1. Find all INPUT fields
    print("\n Searching for INPUT fields...")
    inputs = page.locator("input").all()
    print(f"   Found {len(inputs)} inputs")

    for i, input_elem in enumerate(inputs):
        try:
            if not input_elem.is_visible():
                continue

            input_data = {
                "index": i,
                "type": input_elem.get_attribute("type"),
                "name": input_elem.get_attribute("name"),
                "placeholder": input_elem.get_attribute("placeholder"),
                "value": input_elem.get_attribute("value"),
                "testid": input_elem.get_attribute("data-testid"),
                "id": input_elem.get_attribute("id"),
                "class": input_elem.get_attribute("class"),
                "required": input_elem.get_attribute("required"),
                "disabled": input_elem.get_attribute("disabled"),
                "is_visible": input_elem.is_visible()
            }

            findings["inputs"].append(input_data)
            print(f"   [{i}] type={input_data['type']}, name={input_data['name']}, placeholder={input_data['placeholder']}")

        except Exception as e:
            print(f"   [WARNING]  Error reading input {i}: {e}")

    # 2. Find all TEXTAREA fields
    print("\n Searching for TEXTAREA fields...")
    textareas = page.locator("textarea").all()
    print(f"   Found {len(textareas)} textareas")

    for i, textarea in enumerate(textareas):
        try:
            if not textarea.is_visible():
                continue

            textarea_data = {
                "index": i,
                "name": textarea.get_attribute("name"),
                "placeholder": textarea.get_attribute("placeholder"),
                "value": textarea.get_attribute("value"),
                "testid": textarea.get_attribute("data-testid"),
                "id": textarea.get_attribute("id"),
                "class": textarea.get_attribute("class"),
                "required": textarea.get_attribute("required"),
                "is_visible": textarea.is_visible()
            }

            findings["textareas"].append(textarea_data)
            print(f"   [{i}] name={textarea_data['name']}, placeholder={textarea_data['placeholder']}")

        except Exception as e:
            print(f"   [WARNING]  Error reading textarea {i}: {e}")

    # 3. Find all SELECT dropdowns
    print("\n Searching for SELECT dropdowns...")
    selects = page.locator("select").all()
    print(f"   Found {len(selects)} selects")

    for i, select in enumerate(selects):
        try:
            if not select.is_visible():
                continue

            # Get options
            options = []
            option_elements = select.locator("option").all()
            for opt in option_elements:
                options.append({
                    "value": opt.get_attribute("value"),
                    "text": opt.text_content()
                })

            select_data = {
                "index": i,
                "name": select.get_attribute("name"),
                "testid": select.get_attribute("data-testid"),
                "id": select.get_attribute("id"),
                "class": select.get_attribute("class"),
                "required": select.get_attribute("required"),
                "options": options,
                "is_visible": select.is_visible()
            }

            findings["selects"].append(select_data)
            print(f"   [{i}] name={select_data['name']}, options_count={len(options)}")

        except Exception as e:
            print(f"   [WARNING]  Error reading select {i}: {e}")

    # 4. Find all BUTTONS
    print("\n Searching for BUTTONS...")
    buttons = page.locator("button").all()
    print(f"   Found {len(buttons)} buttons")

    for i, button in enumerate(buttons):
        try:
            if not button.is_visible():
                continue

            button_data = {
                "index": i,
                "type": button.get_attribute("type"),
                "text": button.text_content().strip(),
                "testid": button.get_attribute("data-testid"),
                "id": button.get_attribute("id"),
                "class": button.get_attribute("class"),
                "disabled": button.get_attribute("disabled"),
                "is_visible": button.is_visible()
            }

            findings["buttons"].append(button_data)
            print(f"   [{i}] text='{button_data['text'][:50]}', type={button_data['type']}")

        except Exception as e:
            print(f"   [WARNING]  Error reading button {i}: {e}")

    # 5. Find all LABELS (to understand field meanings)
    print("\n Searching for LABELS...")
    labels = page.locator("label").all()
    print(f"   Found {len(labels)} labels")

    for i, label in enumerate(labels):
        try:
            if not label.is_visible():
                continue

            label_data = {
                "index": i,
                "text": label.text_content().strip(),
                "for": label.get_attribute("for"),
                "testid": label.get_attribute("data-testid"),
                "class": label.get_attribute("class"),
                "is_visible": label.is_visible()
            }

            findings["labels"].append(label_data)
            print(f"   [{i}] text='{label_data['text'][:50]}', for={label_data['for']}")

        except Exception as e:
            print(f"   [WARNING]  Error reading label {i}: {e}")

    # 6. Try to identify SPECIFIC fields by common patterns
    print("\n[TARGET] Identifying specific fields...")

    # Name field
    name_candidates = page.locator("input[name*='name'], input[placeholder*='name'], input[placeholder*='Nome']").all()
    if name_candidates:
        findings["form_structure"]["name_field_candidates"] = len(name_candidates)
        print(f"   [OK] Found {len(name_candidates)} name field candidates")

    # Address field
    address_candidates = page.locator("input[name*='address'], input[placeholder*='address'], input[placeholder*='Endereço'], textarea[name*='address']").all()
    if address_candidates:
        findings["form_structure"]["address_field_candidates"] = len(address_candidates)
        print(f"   [OK] Found {len(address_candidates)} address field candidates")

    # Property type dropdown
    type_candidates = page.locator("select[name*='type'], select[name*='propertyType']").all()
    if type_candidates:
        findings["form_structure"]["property_type_candidates"] = len(type_candidates)
        print(f"   [OK] Found {len(type_candidates)} property type field candidates")

    # Save button
    save_candidates = page.locator("button:has-text('Salvar'), button:has-text('Save'), button[type='submit']").all()
    if save_candidates:
        findings["form_structure"]["save_button_candidates"] = len(save_candidates)
        print(f"   [OK] Found {len(save_candidates)} save button candidates")

    return findings


def main():
    print("=" * 80)
    print("[SEARCH] EXPLORATION: Property Creation Form")
    print("=" * 80)

    config = {
        "base_url": "https://platform.test.hostfully.com/app/#/login",
        "username": "daniel+pmp@hostfully.com",
        "password": "pas123"
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

            # Click "Adicionar propriedade" dropdown
            print("\n Clicking 'Adicionar propriedade' dropdown...")

            # Try multiple selectors for the dropdown button
            dropdown_selectors = [
                "button:has-text('Adicionar propriedade')",
                "button:has-text('Add property')",
                "[data-testid='add-property-button']",
                "button[class*='dropdown']"
            ]

            dropdown_clicked = False
            for selector in dropdown_selectors:
                try:
                    dropdown = page.locator(selector).first
                    if dropdown.is_visible():
                        dropdown.click()
                        dropdown_clicked = True
                        print(f"   [OK] Clicked dropdown with selector: {selector}")
                        break
                except:
                    continue

            if not dropdown_clicked:
                print("[FAIL] Could not click dropdown button")
                return

            time.sleep(1)

            # Screenshot dropdown opened
            base_path = Path(__file__).parent.parent / "hunter-python"
            screenshot_dropdown = base_path / "FORM_DROPDOWN_OPENED.png"
            page.screenshot(path=str(screenshot_dropdown))
            print(f" Screenshot: {screenshot_dropdown}")

            # Click "Propriedade única"
            print("\n Clicking 'Propriedade única'...")

            single_property_selectors = [
                "a:has-text('Propriedade única')",
                "a[href*='single']",
                "li:has-text('Propriedade única')"
            ]

            clicked = False
            for selector in single_property_selectors:
                try:
                    option = page.locator(selector).first
                    if option.is_visible():
                        option.click()
                        clicked = True
                        print(f"   [OK] Clicked 'Propriedade única' with selector: {selector}")
                        break
                except:
                    continue

            if not clicked:
                print("[FAIL] Could not click 'Propriedade única'")
                return

            # Wait for form to load
            print("\n[HOURGLASS] Waiting for form to load...")
            time.sleep(3)

            # Screenshot form loaded
            screenshot_form = base_path / "FORM_LOADED.png"
            page.screenshot(path=str(screenshot_form), full_page=True)
            print(f" Screenshot: {screenshot_form}")

            # EXPLORE FORM
            findings = explore_form_fields(page)
            findings["screenshots"] = [
                str(screenshot_dropdown),
                str(screenshot_form)
            ]

            # Save findings
            output_file = base_path / "PROPERTY_CREATION_FORM.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(findings, f, indent=2, ensure_ascii=False)

            print("\n" + "=" * 80)
            print("[OK] EXPLORATION COMPLETE")
            print("=" * 80)
            print(f"[FILE] Report saved: {output_file}")
            print(f" Screenshots: {len(findings['screenshots'])} saved")
            print(f"\n[CHART] Summary:")
            print(f"   - Inputs: {len(findings['inputs'])}")
            print(f"   - Textareas: {len(findings['textareas'])}")
            print(f"   - Selects: {len(findings['selects'])}")
            print(f"   - Buttons: {len(findings['buttons'])}")
            print(f"   - Labels: {len(findings['labels'])}")

            # Keep browser open for manual inspection
            print("\n Browser will stay open for 10s for manual inspection...")
            time.sleep(10)

        except Exception as e:
            print(f"\n[FAIL] Exploration failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
