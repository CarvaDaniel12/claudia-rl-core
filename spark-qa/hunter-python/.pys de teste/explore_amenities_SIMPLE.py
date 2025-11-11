"""
SIMPLE AMENITIES EXPLORER
Vai direto ao ponto: cria uma property e explora a página de amenities
"""
import sys
import os

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
from config import Config
import time
import json
import re

config = Config()

print("\n[SEARCH] EXPLORANDO PÁGINA DE AMENITIES\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    
    # 1. LOGIN
    print("1⃣ Login...")
    page.goto(config.BASE_URL)
    page.fill('input[type="email"]', config.EMAIL)
    page.fill('input[type="password"]', config.PASSWORD)
    page.click('button[type="submit"]')
    time.sleep(3)
    print(f"   [OK] Logado - URL atual: {page.url}\n")
    
    # 2. CRIAR PROPERTY (COPIADO DO ULTIMATE_PLATFORM_FLOW QUE FUNCIONA!)
    print("2⃣ Criando property...")
    page.goto("https://platform.test.hostfully.com/app/#/properties", timeout=30000)
    time.sleep(2)
    
    page.get_by_test_id("add-property-button").click()
    time.sleep(1)
    page.get_by_role("menuitem", name="Propriedade única").click()
    time.sleep(2)
    
    # Wait for form to be ready
    prop_type_field = page.get_by_test_id("propertyDetails.propertyType")
    prop_type_field.wait_for(state="visible", timeout=15000)
    prop_type_field.scroll_into_view_if_needed()
    time.sleep(1)
    
    # Fill form (minimal fields)
    page.get_by_test_id("propertyDetails.propertyType").select_option("CONDO")
    property_name = f"ExploreAm_{int(time.time())}"
    page.get_by_test_id("propertyDetails.propertyName").fill(property_name)
    page.get_by_test_id("propertyDetails.weblink").fill("https://example.com")
    page.get_by_test_id("propertyDetails.floorCount").fill("2")
    page.get_by_test_id("propertyDetails.propertySize").fill("125")
    
    page.get_by_test_id("propertyAddress.addressLine1").fill("123 Main St")
    page.get_by_test_id("propertyAddress.city").fill("TestCity")
    page.get_by_test_id("propertyAddress.zipCode").fill("12345")
    
    # State (input field in staging)
    try:
        page.get_by_test_id("propertyAddress.state").fill("CA")
    except:
        page.get_by_test_id("propertyAddress.state").select_option("CA")
    
    page.get_by_test_id("capacityDetails.bedCount").select_option("3")
    page.get_by_test_id("capacityDetails.bathroomCount").select_option("4")
    page.get_by_test_id("capacityDetails.baseGuests").fill("5")
    page.get_by_test_id("capacityDetails.maxGuests").fill("10")
    page.get_by_test_id("capacityDetails.extraGuestFee").fill("15")
    
    page.get_by_test_id("propertyPricingFeesTaxes.currency").select_option("USD")
    page.get_by_test_id("propertyPricingFeesTaxes.nightlyBasePrice").fill("150")
    page.get_by_test_id("propertyPricingFeesTaxes.taxRate").fill("10")
    page.get_by_test_id("propertyPricingFeesTaxes.securityDeposit").fill("250")
    page.get_by_test_id("propertyPricingFeesTaxes.cleaningFee").fill("80")
    page.get_by_test_id("propertyPricingFeesTaxes.cleaningFeeTax").fill("10")
    
    # Save
    save_button = page.get_by_test_id("form-footer").get_by_test_id("save-button")
    save_button.click()
    
    # Wait for redirect
    page.wait_for_url(re.compile(r"/property/[a-f0-9-]{36}"), timeout=30000)
    print(f"   [OK] Property criada: {property_name}")
    print(f"   URL: {page.url}\n")
    
    # 3. IR PARA AMENITIES
    print("3⃣ Navegando para Amenities...")
    page.get_by_test_id("property-settings-tab-amenities").click()
    time.sleep(3)
    print("   [OK] Amenities carregado\n")
    
    # 4. SCREENSHOT FULL PAGE
    print(" Capturando página completa...")
    page.screenshot(path="AMENITIES_FULL_PAGE.png", full_page=True)
    print("   [OK] Screenshot: AMENITIES_FULL_PAGE.png\n")
    
    # 5. EXPLORAR ESTRUTURA
    print("="*80)
    print("[SEARCH] MAPEANDO ESTRUTURA DA PÁGINA")
    print("="*80 + "\n")
    
    findings = {}
    
    # BOTÕES
    print(" BUTTONS:")
    buttons = page.locator('button').all()
    button_list = []
    for btn in buttons:
        try:
            if btn.is_visible():
                text = btn.inner_text().strip()
                test_id = btn.get_attribute('data-testid') or ''
                classes = btn.get_attribute('class') or ''
                if text or test_id:
                    button_list.append({
                        'text': text,
                        'testid': test_id,
                        'classes': classes[:50]
                    })
                    print(f"   • '{text}' | testid={test_id}")
        except:
            pass
    findings['buttons'] = button_list
    print(f"   Total: {len(button_list)} botões visíveis\n")
    
    # ACCORDIONS / COLLAPSIBLE SECTIONS
    print(" ACCORDIONS/SECTIONS:")
    accordions = page.locator('[role="button"][aria-expanded]').all()
    accordion_list = []
    for acc in accordions:
        try:
            text = acc.inner_text().strip()
            expanded = acc.get_attribute('aria-expanded')
            test_id = acc.get_attribute('data-testid') or ''
            accordion_list.append({
                'text': text,
                'expanded': expanded,
                'testid': test_id
            })
            print(f"   • '{text}' | expanded={expanded} | testid={test_id}")
        except:
            pass
    findings['accordions'] = accordion_list
    print(f"   Total: {len(accordion_list)} accordions\n")
    
    # CHECKBOXES
    print("  CHECKBOXES:")
    checkboxes = page.locator('input[type="checkbox"]').all()
    checkbox_list = []
    for cb in checkboxes:
        try:
            if cb.is_visible():
                test_id = cb.get_attribute('data-testid') or ''
                name = cb.get_attribute('name') or ''
                checked = cb.is_checked()
                if test_id or name:
                    checkbox_list.append({
                        'testid': test_id,
                        'name': name,
                        'checked': checked
                    })
                    print(f"   • testid={test_id} | name={name} | checked={checked}")
        except:
            pass
    findings['checkboxes'] = checkbox_list
    print(f"   Total: {len(checkbox_list)} checkboxes\n")
    
    # SAVE REPORT
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'findings': findings,
        'summary': {
            'buttons': len(button_list),
            'accordions': len(accordion_list),
            'checkboxes': len(checkbox_list)
        }
    }
    
    with open('AMENITIES_EXPLORATION_REPORT.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("="*80)
    print("[OK] EXPLORAÇÃO COMPLETA!")
    print(f"   [LIST] Relatório: AMENITIES_EXPLORATION_REPORT.json")
    print(f"    Screenshot: AMENITIES_FULL_PAGE.png")
    print("="*80)
    
    input("\n⏸  Pressione ENTER para fechar o browser...")
    browser.close()
