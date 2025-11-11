"""
TEST: Visual Explorer - Captura posição visual + hierarquia
Vamos testar se conseguimos correlacionar o que o humano vê com o que o agente vê
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

print("\n[SEARCH] VISUAL EXPLORER - TESTE SIMPLES\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=300)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    
    # 1. LOGIN
    print("1⃣ Login...")
    page.goto(config.BASE_URL)
    page.fill('input[type="email"]', config.EMAIL)
    page.fill('input[type="password"]', config.PASSWORD)
    page.click('button[type="submit"]')
    time.sleep(3)
    print(f"   [OK] Logado\n")
    
    # 2. CRIAR PROPERTY (código que funciona)
    print("2⃣ Criando property...")
    page.goto("https://platform.test.hostfully.com/app/#/properties", timeout=30000)
    time.sleep(2)
    
    page.get_by_test_id("add-property-button").click()
    time.sleep(1)
    page.get_by_role("menuitem", name="Propriedade única").click()
    time.sleep(2)
    
    prop_type_field = page.get_by_test_id("propertyDetails.propertyType")
    prop_type_field.wait_for(state="visible", timeout=15000)
    prop_type_field.scroll_into_view_if_needed()
    time.sleep(1)
    
    page.get_by_test_id("propertyDetails.propertyType").select_option("CONDO")
    property_name = f"VisualTest_{int(time.time())}"
    page.get_by_test_id("propertyDetails.propertyName").fill(property_name)
    page.get_by_test_id("propertyDetails.weblink").fill("https://example.com")
    page.get_by_test_id("propertyDetails.floorCount").fill("2")
    page.get_by_test_id("propertyDetails.propertySize").fill("125")
    
    page.get_by_test_id("propertyAddress.addressLine1").fill("123 Main St")
    page.get_by_test_id("propertyAddress.city").fill("TestCity")
    page.get_by_test_id("propertyAddress.zipCode").fill("12345")
    
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
    
    save_button = page.get_by_test_id("form-footer").get_by_test_id("save-button")
    save_button.click()
    
    page.wait_for_url(re.compile(r"/property/[a-f0-9-]{36}"), timeout=30000)
    print(f"   [OK] Property criada: {property_name}\n")
    
    # 3. IR PARA AMENITIES
    print("3⃣ Navegando para Amenities...")
    page.get_by_test_id("property-settings-tab-amenities").click()
    time.sleep(3)
    print("   [OK] Amenities carregado\n")
    
    # 4. EXPLORAR APENAS OS BOTÕES "save-button"
    print("="*80)
    print("[SEARCH] ANALISANDO BOTÕES 'save-button'")
    print("="*80 + "\n")
    
    # Encontrar TODOS os botões com testid="save-button"
    save_buttons = page.locator('[data-testid="save-button"]').all()
    
    findings = []
    
    print(f"[CHART] Encontrados: {len(save_buttons)} botões com testid='save-button'\n")
    
    for i, btn in enumerate(save_buttons, 1):
        try:
            # Capturar dados visuais + hierárquicos
            box = btn.bounding_box()
            text = btn.inner_text().strip()
            
            # Pegar informações do parent
            parent_eval = btn.evaluate('''(element) => {
                const parent = element.parentElement;
                return {
                    tag: parent.tagName,
                    class: parent.className,
                    id: parent.id,
                    testid: parent.getAttribute('data-testid')
                };
            }''')
            
            # Pegar computed style (para detectar position: fixed/sticky)
            style_eval = btn.evaluate('''(element) => {
                const style = window.getComputedStyle(element);
                const parentStyle = window.getComputedStyle(element.parentElement);
                return {
                    position: style.position,
                    parent_position: parentStyle.position,
                    z_index: style.zIndex,
                    parent_z_index: parentStyle.zIndex
                };
            }''')
            
            data = {
                "index": i,
                "text": text,
                "testid": "save-button",
                "visual_position": {
                    "x": round(box['x'], 1) if box else None,
                    "y": round(box['y'], 1) if box else None,
                    "width": round(box['width'], 1) if box else None,
                    "height": round(box['height'], 1) if box else None
                },
                "parent": parent_eval,
                "styling": style_eval,
                "is_visible": btn.is_visible()
            }
            
            findings.append(data)
            
            # Print formatado
            print(f" BOTÃO #{i}:")
            print(f"   Texto: '{text}'")
            print(f"   Posição Visual: x={data['visual_position']['x']}, y={data['visual_position']['y']}")
            print(f"   Tamanho: {data['visual_position']['width']} x {data['visual_position']['height']}")
            print(f"   Parent: <{parent_eval['tag']}> class='{parent_eval['class'][:50]}'")
            print(f"   Position CSS: {style_eval['position']} (parent: {style_eval['parent_position']})")
            print(f"   Visível: {data['is_visible']}")
            print()
            
        except Exception as e:
            print(f"   [WARNING] Erro no botão #{i}: {str(e)[:100]}\n")
    
    # Salvar relatório
    report = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "property_name": property_name,
        "total_save_buttons": len(save_buttons),
        "buttons": findings
    }
    
    with open('VISUAL_TEST_REPORT.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Screenshot marcado
    print(" Capturando screenshot...")
    page.screenshot(path="VISUAL_TEST_SCREENSHOT.png", full_page=True)
    
    print("\n" + "="*80)
    print("[OK] TESTE COMPLETO!")
    print(f"   [LIST] Relatório: VISUAL_TEST_REPORT.json")
    print(f"    Screenshot: VISUAL_TEST_SCREENSHOT.png")
    print("="*80)
    print("\n[SEARCH] AGORA ANALISE:")
    print("   1. Olhe o screenshot e identifique qual botão você quer")
    print("   2. Olhe o JSON e encontre qual tem a posição visual correspondente")
    print("   3. Me diga: 'Quero o botão #X que está em y=XXX'")
    print("\n")
    
    input("⏸  Pressione ENTER para fechar...")
    browser.close()
