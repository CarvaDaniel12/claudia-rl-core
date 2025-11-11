#!/usr/bin/env python3
"""
MASTER SCAN SCRIPT - Progressive scanning of all platform pages/modals
Edit this file to add more scans progressively
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

def scan_elements(page, container_selector=None):
    """Helper to scan all elements in page or container"""
    base = page if not container_selector else page.locator(container_selector)
    
    scan = {
        "inputs": [],
        "buttons": [],
        "selects": [],
        "checkboxes": [],
        "radios": [],
        "textareas": []
    }
    
    # Inputs
    for inp in base.locator("input").all():
        try:
            if inp.is_visible():
                scan["inputs"].append({
                    "testid": inp.get_attribute("data-testid"),
                    "id": inp.get_attribute("id"),
                    "name": inp.get_attribute("name"),
                    "type": inp.get_attribute("type"),
                    "placeholder": inp.get_attribute("placeholder"),
                    "value": inp.input_value() if inp.input_value() else None
                })
        except:
            pass
    
    # Buttons
    for btn in base.locator("button").all():
        try:
            if btn.is_visible():
                scan["buttons"].append({
                    "testid": btn.get_attribute("data-testid"),
                    "text": btn.inner_text()[:50] if btn.inner_text() else None,
                    "disabled": btn.is_disabled()
                })
        except:
            pass
    
    # Selects
    for sel in base.locator("select").all():
        try:
            if sel.is_visible():
                options = []
                for opt in sel.locator("option").all()[:20]:  # First 20 options
                    options.append({
                        "value": opt.get_attribute("value"),
                        "text": opt.inner_text()
                    })
                
                scan["selects"].append({
                    "testid": sel.get_attribute("data-testid"),
                    "name": sel.get_attribute("name"),
                    "options": options
                })
        except:
            pass
    
    return scan

def save_scan(name, data):
    """Save scan to JSON file"""
    output_dir = Path(__file__).parent / "scans_exploration"
    output_file = output_dir / f"{name}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"  SAVED: {name}.json")
    print(f"    Inputs: {len(data.get('elements', {}).get('inputs', []))}")
    print(f"    Buttons: {len(data.get('elements', {}).get('buttons', []))}")
    print(f"    Selects: {len(data.get('elements', {}).get('selects', []))}")
    return output_file

def run_scans():
    print("="*70)
    print("MASTER SCAN - PROGRESSIVE PLATFORM SCANNING")
    print("="*70)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        config = Config()
        
        # LOGIN
        print("\n[LOGIN]")
        page.goto(config.BASE_URL, timeout=60000)
        time.sleep(2)
        page.get_by_test_id("email").fill(config.EMAIL)
        page.get_by_test_id("password").fill(config.PASSWORD)
        page.get_by_test_id("submit-button").click()
        time.sleep(3)
        print("  Logged in")
        
        # Navigate to Properties
        print("\n[PROPERTIES PAGE]")
        page.locator(".dropdown-toggle").first.click()
        time.sleep(1)
        page.locator("text=Propriedades").first.click()
        time.sleep(2)
        print("  Navigated to properties")
        
        # Click first property
        print("\n[PROPERTY EDIT - OPENING]")
        first_property = page.locator("[data-testid^='property-list-item-']").first
        if first_property.is_visible(timeout=5000):
            first_property.click()
            time.sleep(3)
            print("  Property edit opened")
        
        # SCAN 1: FEE MODAL (in Fees & Taxes tab)
        print("\n[SCAN 1: FEE MODAL]")
        try:
            fees_tab = page.get_by_test_id("property-settings-tab-fees-and-policies")
            if fees_tab.is_visible(timeout=3000):
                fees_tab.click()
                time.sleep(3)
                print("  Fees & Taxes tab opened")
                
                add_fee_btn = page.get_by_test_id("property-fees-taxes-button")
                if add_fee_btn.is_visible(timeout=3000):
                    add_fee_btn.click()
                    time.sleep(2)
                    print("  Fee modal opened")
                    
                    # Wait for modal
                    page.wait_for_selector(".modal-content", state="visible", timeout=5000)
                    time.sleep(1)
                    
                    scan_data = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "modal_name": "Property Fee/Tax Add Modal",
                        "elements": scan_elements(page, ".modal-content")
                    }
                    
                    save_scan("FEE_MODAL_SCAN", scan_data)
                    
                    # Close modal
                    page.keyboard.press("Escape")
                    time.sleep(1)
                else:
                    print("  Add fee button not visible")
        except Exception as e:
            print(f"  Error: {str(e)[:60]}")
        
        # Add more scans here progressively...
        
        print("\n" + "="*70)
        print("SCANNING COMPLETE")
        print("="*70)
        
        input("\nPress Enter to close browser...")
        browser.close()

if __name__ == "__main__":
    run_scans()

