"""
EXPLORATION: Properties List Page

Maps the properties list page structure:
- Create Property button (all possible selectors)
- Table/list structure
- Filters, search, pagination
- Action buttons (edit, delete, etc.)

Output: PROPERTIES_LIST_EXPLORATION.json + screenshot
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


def explore_properties_list_page(page):
    """
    Explore properties list page structure
    """
    print("\n[SEARCH] EXPLORING: Properties List Page")
    print("=" * 80)

    findings = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "page_url": page.url,
        "buttons": [],
        "links": [],
        "inputs": [],
        "tables": [],
        "other_elements": []
    }

    # 1. Find all buttons
    print("\n Searching for buttons...")
    buttons = page.locator("button").all()
    for i, btn in enumerate(buttons):
        try:
            btn_data = {
                "index": i,
                "text": btn.inner_text()[:50] if btn.is_visible() else "",
                "testid": btn.get_attribute("data-testid"),
                "class": btn.get_attribute("class"),
                "type": btn.get_attribute("type"),
                "visible": btn.is_visible(),
            }

            # Try to get bounding box
            try:
                box = btn.bounding_box()
                if box:
                    btn_data["position"] = {
                        "x": box["x"],
                        "y": box["y"],
                        "width": box["width"],
                        "height": box["height"]
                    }
            except:
                pass

            findings["buttons"].append(btn_data)

            if btn.is_visible():
                print(f"  Button #{i}: '{btn_data['text'][:30]}' testid={btn_data['testid']}")
        except Exception as e:
            print(f"  [WARNING]  Button #{i} error: {str(e)[:50]}")

    # 2. Find all links (especially "Create" or "Add" links)
    print("\n Searching for links...")
    links = page.locator("a").all()
    for i, link in enumerate(links):
        try:
            link_data = {
                "index": i,
                "text": link.inner_text()[:50] if link.is_visible() else "",
                "href": link.get_attribute("href"),
                "testid": link.get_attribute("data-testid"),
                "class": link.get_attribute("class"),
                "visible": link.is_visible(),
            }
            findings["links"].append(link_data)

            if link.is_visible() and any(keyword in link_data['text'].lower() for keyword in ['create', 'add', 'new', 'property']):
                print(f"  [STAR] Link #{i}: '{link_data['text'][:30]}' href={link_data['href']}")
        except Exception as e:
            print(f"  [WARNING]  Link #{i} error: {str(e)[:50]}")

    # 3. Find input fields (search, filters)
    print("\n Searching for inputs...")
    inputs = page.locator("input").all()
    for i, inp in enumerate(inputs):
        try:
            inp_data = {
                "index": i,
                "type": inp.get_attribute("type"),
                "placeholder": inp.get_attribute("placeholder"),
                "testid": inp.get_attribute("data-testid"),
                "name": inp.get_attribute("name"),
                "class": inp.get_attribute("class"),
                "visible": inp.is_visible(),
            }
            findings["inputs"].append(inp_data)

            if inp.is_visible():
                print(f"  Input #{i}: type={inp_data['type']} placeholder='{inp_data['placeholder']}'")
        except Exception as e:
            print(f"  [WARNING]  Input #{i} error: {str(e)[:50]}")

    # 4. Find tables/grids
    print("\n Searching for tables...")
    tables = page.locator("table").all()
    for i, table in enumerate(tables):
        try:
            headers = table.locator("th").all()
            header_texts = [h.inner_text() for h in headers if h.is_visible()]

            table_data = {
                "index": i,
                "headers": header_texts,
                "row_count": table.locator("tr").count(),
                "testid": table.get_attribute("data-testid"),
                "class": table.get_attribute("class"),
            }
            findings["tables"].append(table_data)
            print(f"  Table #{i}: {len(header_texts)} columns, {table_data['row_count']} rows")
            print(f"    Headers: {', '.join(header_texts[:5])}")
        except Exception as e:
            print(f"  [WARNING]  Table #{i} error: {str(e)[:50]}")

    # 5. Look for specific "Create Property" patterns
    print("\n Looking for 'Create Property' element...")
    create_patterns = [
        {"selector": '[data-testid*="create"]', "type": "testid wildcard"},
        {"selector": '[data-testid*="add"]', "type": "testid wildcard"},
        {"selector": 'button:has-text("Create")', "type": "button text"},
        {"selector": 'button:has-text("Add")', "type": "button text"},
        {"selector": 'a:has-text("Create")', "type": "link text"},
        {"selector": 'a[href*="create"]', "type": "link href"},
        {"selector": 'a[href*="new"]', "type": "link href"},
    ]

    create_elements = []
    for pattern in create_patterns:
        try:
            elements = page.locator(pattern["selector"]).all()
            for el in elements:
                if el.is_visible():
                    create_elements.append({
                        "pattern": pattern["type"],
                        "selector": pattern["selector"],
                        "text": el.inner_text()[:50],
                        "testid": el.get_attribute("data-testid"),
                        "href": el.get_attribute("href"),
                    })
                    print(f"  [OK] Found via {pattern['type']}: '{el.inner_text()[:30]}'")
        except:
            pass

    findings["create_property_candidates"] = create_elements

    return findings


def main():
    print("=" * 80)
    print("[SEARCH] EXPLORATION: Properties List Page")
    print("=" * 80)

    config = {
        "base_url": "https://platform.test.hostfully.com/app/#/login",
        "username": "daniel+pmp@hostfully.com",
        "password": "pas123"
    }

    with sync_playwright() as p:
        print("\n Launching browser...")
        browser = p.chromium.launch(headless=False, slow_mo=300)
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

            # Explore the page
            findings = explore_properties_list_page(page)

            # Define output paths (absolute)
            base_path = Path(__file__).parent.parent / "hunter-python"
            screenshot_path = base_path / "PROPERTIES_LIST_PAGE.png"
            output_path = base_path / "PROPERTIES_LIST_EXPLORATION.json"

            # Take screenshot
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n Screenshot saved: {screenshot_path}")

            # Save findings
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(findings, f, indent=2, ensure_ascii=False)

            print(f"\n[SAVE] Exploration data saved: {output_path}")

            # Summary
            print("\n" + "=" * 80)
            print("[CHART] SUMMARY")
            print("=" * 80)
            print(f"Buttons found: {len(findings['buttons'])}")
            print(f"Links found: {len(findings['links'])}")
            print(f"Inputs found: {len(findings['inputs'])}")
            print(f"Tables found: {len(findings['tables'])}")
            print(f"Create Property candidates: {len(findings['create_property_candidates'])}")

            if findings['create_property_candidates']:
                print("\n[TARGET] CREATE PROPERTY CANDIDATES:")
                for candidate in findings['create_property_candidates']:
                    print(f"  - [{candidate['pattern']}] '{candidate['text'][:40]}' testid={candidate['testid']}")

            print("\n[OK] Exploration complete!")

            # Wait 3 seconds for visual inspection, then auto-close
            print("\n⏸  Closing in 3 seconds...")
            time.sleep(3)

        except Exception as e:
            print(f"\n[FAIL] Exploration failed: {str(e)}")
            import traceback
            traceback.print_exc()

            print("\n⏸  Closing in 5 seconds (check error above)...")
            time.sleep(5)

        finally:
            browser.close()
            print("[LOCKED] Browser closed")


if __name__ == "__main__":
    main()
