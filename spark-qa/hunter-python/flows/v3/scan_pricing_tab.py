#!/usr/bin/env python3
"""
Scan PRICING TAB elements during property edit
"""
import sys
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config

def scan_pricing_tab():
    print("="*70)
    print("SCANNING PRICING TAB")
    print("="*70)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        config = Config()
        
        print("Logging in...")
        page.goto(config.BASE_URL, timeout=60000)
        time.sleep(2)
        
        page.get_by_test_id("email").fill(config.EMAIL)
        page.get_by_test_id("password").fill(config.PASSWORD)
        page.get_by_test_id("submit-button").click()
        time.sleep(3)
        
        print("Navigating to Properties...")
        page.locator(".dropdown-toggle").first.click()
        time.sleep(1)
        page.locator("text=Propriedades").first.click()
        time.sleep(2)
        
        print("Clicking first property to edit...")
        # Click on first property in list
        first_property = page.locator("[data-testid^='property-list-item-']").first
        if first_property.is_visible(timeout=5000):
            first_property.click()
            time.sleep(3)
        
        print("Navigating to PRICING TAB...")
        pricing_tab = page.get_by_test_id("property-settings-tab-pricing")
        if pricing_tab.is_visible(timeout=5000):
            pricing_tab.click()
            time.sleep(3)
            print("PRICING TAB LOADED!")
            
            # Wait for page to fully load
            page.wait_for_load_state("networkidle", timeout=10000)
            time.sleep(2)
            
            # Scan elements
            scan_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tab_name": "Pricing",
                "url": page.url,
                "elements": {
                    "inputs": [],
                    "buttons": [],
                    "selects": [],
                    "checkboxes": [],
                    "radios": [],
                    "textareas": [],
                    "other": []
                }
            }
            
            print("\nScanning inputs...")
            inputs = page.locator("input").all()
            for inp in inputs:
                try:
                    if inp.is_visible():
                        scan_data["elements"]["inputs"].append({
                            "type": "input",
                            "visible": True,
                            "testid": inp.get_attribute("data-testid"),
                            "id": inp.get_attribute("id"),
                            "name": inp.get_attribute("name"),
                            "placeholder": inp.get_attribute("placeholder"),
                            "input_type": inp.get_attribute("type"),
                            "value": inp.input_value() if inp.input_value() else None
                        })
                except:
                    pass
            
            print(f"Found {len(scan_data['elements']['inputs'])} inputs")
            
            print("\nScanning buttons...")
            buttons = page.locator("button").all()
            for btn in buttons:
                try:
                    if btn.is_visible():
                        scan_data["elements"]["buttons"].append({
                            "type": "button",
                            "visible": True,
                            "testid": btn.get_attribute("data-testid"),
                            "text": btn.inner_text()[:50] if btn.inner_text() else None,
                            "disabled": btn.is_disabled()
                        })
                except:
                    pass
            
            print(f"Found {len(scan_data['elements']['buttons'])} buttons")
            
            print("\nScanning selects...")
            selects = page.locator("select").all()
            for sel in selects:
                try:
                    if sel.is_visible():
                        options = []
                        for opt in sel.locator("option").all():
                            options.append({
                                "value": opt.get_attribute("value"),
                                "text": opt.inner_text()
                            })
                        
                        scan_data["elements"]["selects"].append({
                            "type": "select",
                            "visible": True,
                            "testid": sel.get_attribute("data-testid"),
                            "name": sel.get_attribute("name"),
                            "options": options
                        })
                except:
                    pass
            
            print(f"Found {len(scan_data['elements']['selects'])} selects")
            
            # Save scan
            output_file = Path(__file__).parent / "scans_exploration" / "PRICING_TAB_SCAN.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(scan_data, f, indent=2, ensure_ascii=False)
            
            print()
            print(f"SCAN SAVED: {output_file.name}")
            print(f"  Inputs: {len(scan_data['elements']['inputs'])}")
            print(f"  Buttons: {len(scan_data['elements']['buttons'])}")
            print(f"  Selects: {len(scan_data['elements']['selects'])}")
            
        else:
            print("PRICING TAB NOT VISIBLE!")
        
        input("\nPress Enter to close browser...")
        browser.close()

if __name__ == "__main__":
    scan_pricing_tab()

