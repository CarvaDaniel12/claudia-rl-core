#!/usr/bin/env python3
"""
Scan PRICE RULE MODAL elements
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

def scan_price_rule_modal():
    print("="*70)
    print("SCANNING PRICE RULE MODAL")
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
        first_property = page.locator("[data-testid^='property-list-item-']").first
        if first_property.is_visible(timeout=5000):
            first_property.click()
            time.sleep(3)
        
        print("Navigating to PRICING TAB...")
        pricing_tab = page.get_by_test_id("property-settings-tab-pricing")
        if pricing_tab.is_visible(timeout=5000):
            pricing_tab.click()
            time.sleep(3)
        
        print("Clicking ADD RULE button...")
        add_rule_btn = page.get_by_test_id("price-rules-header-button")
        if add_rule_btn.is_visible(timeout=5000):
            add_rule_btn.click()
            time.sleep(3)
            print("PRICE RULE MODAL OPENED!")
            
            # Wait for modal to fully load
            page.wait_for_selector("[data-testid='price-rules-add-edit-modal']", state="visible", timeout=10000)
            time.sleep(2)
            
            # Scan modal elements
            scan_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "modal_name": "Price Rule Add/Edit Modal",
                "modal_testid": "price-rules-add-edit-modal",
                "elements": {
                    "inputs": [],
                    "buttons": [],
                    "selects": [],
                    "checkboxes": [],
                    "radios": [],
                    "textareas": []
                }
            }
            
            print("\nScanning modal inputs...")
            inputs = page.locator("[data-testid='price-rules-add-edit-modal'] input").all()
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
                            "class": inp.get_attribute("class")
                        })
                except:
                    pass
            
            print(f"Found {len(scan_data['elements']['inputs'])} inputs")
            
            print("\nScanning modal buttons...")
            buttons = page.locator("[data-testid='price-rules-add-edit-modal'] button").all()
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
            
            print("\nScanning modal selects...")
            selects = page.locator("[data-testid='price-rules-add-edit-modal'] select").all()
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
                            "id": sel.get_attribute("id"),
                            "options": options[:10]  # First 10 options
                        })
                except:
                    pass
            
            print(f"Found {len(scan_data['elements']['selects'])} selects")
            
            # Scan radio buttons
            print("\nScanning radios...")
            radios = page.locator("[data-testid='price-rules-add-edit-modal'] input[type='radio']").all()
            for radio in radios:
                try:
                    if radio.is_visible():
                        scan_data["elements"]["radios"].append({
                            "type": "radio",
                            "visible": True,
                            "testid": radio.get_attribute("data-testid"),
                            "name": radio.get_attribute("name"),
                            "value": radio.get_attribute("value"),
                            "checked": radio.is_checked()
                        })
                except:
                    pass
            
            print(f"Found {len(scan_data['elements']['radios'])} radios")
            
            # Save scan
            output_file = Path(__file__).parent / "scans_exploration" / "PRICE_RULE_MODAL_SCAN.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(scan_data, f, indent=2, ensure_ascii=False)
            
            print()
            print(f"SCAN SAVED: {output_file.name}")
            print(f"  Inputs: {len(scan_data['elements']['inputs'])}")
            print(f"  Buttons: {len(scan_data['elements']['buttons'])}")
            print(f"  Selects: {len(scan_data['elements']['selects'])}")
            print(f"  Radios: {len(scan_data['elements']['radios'])}")
            
        else:
            print("PRICING TAB NOT VISIBLE!")
        
        input("\nPress Enter to close browser...")
        browser.close()

if __name__ == "__main__":
    scan_price_rule_modal()

