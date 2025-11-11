"""
EXPLORER: User Dropdown Menu
Mapeia o dropdown do usuário (gerenciadordeprop2) para encontrar seletores confiáveis
"""
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
from config import Config
import time
import json

config = Config()

print("\n USER DROPDOWN EXPLORER\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})

    # LOGIN
    print("1⃣ Login...")
    page.goto(config.BASE_URL)
    page.fill('input[type="email"]', config.EMAIL)
    page.fill('input[type="password"]', config.PASSWORD)
    page.click('button[type="submit"]')
    time.sleep(3)
    print(f"   [OK] Logado\n")

    # SCREENSHOT ANTES DE CLICAR
    page.screenshot(path="USER_DROPDOWN_CLOSED.png")
    print(" Screenshot do dropdown fechado: USER_DROPDOWN_CLOSED.png\n")

    # ENCONTRAR O DROPDOWN
    print("[SEARCH] Procurando o dropdown do usuário...\n")

    # Tentar vários seletores possíveis
    selectors_to_try = [
        ('text("gerenciadordeprop2")', 'Por texto exato'),
        ('[class*="user"]', 'Por class contendo "user"'),
        ('[class*="dropdown"]', 'Por class contendo "dropdown"'),
        ('[class*="account"]', 'Por class contendo "account"'),
        ('button:has-text("gerenciadordeprop2")', 'Button com texto'),
        ('a:has-text("gerenciadordeprop2")', 'Link com texto'),
        ('[role="button"]:has-text("gerenciadordeprop2")', 'Role button com texto'),
    ]

    dropdown_element = None
    working_selector = None

    for selector, description in selectors_to_try:
        try:
            element = page.locator(selector).first
            if element.is_visible():
                print(f"   [OK] ENCONTRADO: {description}")
                print(f"      Selector: {selector}")

                # Capturar detalhes
                testid = element.get_attribute('data-testid') or ''
                classes = element.get_attribute('class') or ''
                tag = element.evaluate('el => el.tagName')

                print(f"      Tag: {tag}")
                print(f"      TestID: {testid}")
                print(f"      Classes: {classes[:100]}")
                print()

                if not dropdown_element:
                    dropdown_element = element
                    working_selector = selector
        except:
            pass

    if not dropdown_element:
        print("   [FAIL] Não encontrei o dropdown!\n")
        input("Pressione ENTER...")
        browser.close()
        exit(1)

    # CLICAR NO DROPDOWN
    print(f"2⃣ Clicando no dropdown usando: {working_selector}\n")
    dropdown_element.click()
    time.sleep(1)

    # SCREENSHOT COM DROPDOWN ABERTO
    page.screenshot(path="USER_DROPDOWN_OPEN.png")
    print(" Screenshot do dropdown aberto: USER_DROPDOWN_OPEN.png\n")

    # MAPEAR ITENS DO MENU
    print("="*80)
    print("[LIST] ITENS DO MENU DROPDOWN:")
    print("="*80 + "\n")

    # Tentar pegar todos os links/itens visíveis
    menu_items = []

    # Estratégias para encontrar itens do menu
    menu_selectors = [
        'a:visible',
        'button:visible',
        '[role="menuitem"]',
        'li a',
        'li button',
        '[class*="menu-item"]',
        '[class*="dropdown-item"]'
    ]

    for selector in menu_selectors:
        try:
            items = page.locator(selector).all()
            for item in items:
                if item.is_visible():
                    text = item.inner_text().strip()
                    href = item.get_attribute('href') or ''
                    testid = item.get_attribute('data-testid') or ''
                    classes = item.get_attribute('class') or ''

                    # Filtrar só itens com texto relevante
                    if text and len(text) > 0 and len(text) < 100:
                        item_data = {
                            'text': text,
                            'href': href,
                            'testid': testid,
                            'classes': classes[:50],
                            'selector_found': selector
                        }

                        # Evitar duplicatas
                        if not any(m['text'] == text for m in menu_items):
                            menu_items.append(item_data)
        except:
            pass

    # Mostrar itens encontrados
    for i, item in enumerate(menu_items, 1):
        print(f"{i:2}. {item['text']:30}")
        if item['testid']:
            print(f"    TestID: {item['testid']}")
        if item['href']:
            print(f"    Href: {item['href']}")
        print(f"    Classes: {item['classes']}")
        print()

    # ENCONTRAR "PROPERTIES" ESPECIFICAMENTE
    print("="*80)
    print("[TARGET] SELETOR PARA 'PROPERTIES':")
    print("="*80 + "\n")

    properties_item = next((m for m in menu_items if 'propert' in m['text'].lower()), None)

    if properties_item:
        print(f"[OK] ENCONTRADO!")
        print(f"   Texto: {properties_item['text']}")
        print(f"   TestID: {properties_item['testid'] or 'N/A'}")
        print(f"   Href: {properties_item['href'] or 'N/A'}")
        print(f"   Selector que funcionou: {properties_item['selector_found']}")

        # Tentar clicar
        print(f"\n3⃣ Testando clique em 'Properties'...")
        try:
            if properties_item['testid']:
                page.get_by_test_id(properties_item['testid']).click()
            elif properties_item['href']:
                page.locator(f'a[href="{properties_item["href"]}"]').click()
            else:
                page.get_by_text(properties_item['text'], exact=True).click()

            time.sleep(2)
            print(f"   [OK] Clicou com sucesso!")
            print(f"   URL atual: {page.url}")

            # Screenshot final
            page.screenshot(path="AFTER_PROPERTIES_CLICK.png", full_page=True)
            print(f"    Screenshot: AFTER_PROPERTIES_CLICK.png")

        except Exception as e:
            print(f"   [FAIL] Erro ao clicar: {e}")
    else:
        print("[FAIL] NÃO ENCONTREI 'Properties' no menu!")

    # SALVAR RELATÓRIO
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'dropdown_selector': working_selector,
        'menu_items': menu_items,
        'properties_item': properties_item
    }

    with open('USER_DROPDOWN_REPORT.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Relatório salvo: USER_DROPDOWN_REPORT.json\n")

    input("⏸  Pressione ENTER para fechar...")
    browser.close()
