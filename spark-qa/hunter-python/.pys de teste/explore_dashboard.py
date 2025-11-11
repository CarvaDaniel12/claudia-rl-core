"""
EXPLORER: Dashboard (Landing Page)
Primeira tela após login - mapeia estrutura inicial da plataforma
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

config = Config()

print("\n DASHBOARD EXPLORER - Mapeando Landing Page\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=300)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})

    # LOGIN
    print("1⃣ Login...")
    page.goto(config.BASE_URL)
    page.fill('input[type="email"]', config.EMAIL)
    page.fill('input[type="password"]', config.PASSWORD)
    page.click('button[type="submit"]')
    time.sleep(3)

    current_url = page.url
    print(f"   [OK] Logado - URL: {current_url}\n")

    # EXPLORAR DASHBOARD
    print("="*80)
    print("[SEARCH] MAPEANDO DASHBOARD")
    print("="*80 + "\n")

    findings = {
        "url": current_url,
        "navigation_menu": [],
        "buttons": [],
        "links": [],
        "cards": [],
        "main_sections": []
    }

    # 1. MENU DE NAVEGAÇÃO (lateral/topo)
    print("[LIST] MENU DE NAVEGAÇÃO:")
    nav_items = page.locator('[role="navigation"] a, nav a, [class*="nav"] a, [class*="menu"] a').all()

    for item in nav_items[:20]:  # Limitar a 20 primeiros
        try:
            if item.is_visible():
                text = item.inner_text().strip()
                href = item.get_attribute('href') or ''
                testid = item.get_attribute('data-testid') or ''
                box = item.bounding_box()

                if text:  # Só pegar itens com texto
                    data = {
                        'text': text,
                        'href': href,
                        'testid': testid,
                        'position': {
                            'x': round(box['x'], 1) if box else None,
                            'y': round(box['y'], 1) if box else None
                        }
                    }
                    findings['navigation_menu'].append(data)
                    print(f"   • {text:30} | testid={testid:30} | href={href[:40]}")
        except:
            pass

    print(f"   Total: {len(findings['navigation_menu'])} itens de navegação\n")

    # 2. BOTÕES PRINCIPAIS
    print(" BOTÕES PRINCIPAIS:")
    buttons = page.locator('button').all()
    button_list = []

    for btn in buttons[:30]:  # Limitar a 30
        try:
            if btn.is_visible():
                text = btn.inner_text().strip()
                testid = btn.get_attribute('data-testid') or ''
                classes = btn.get_attribute('class') or ''
                box = btn.bounding_box()

                if text or testid:
                    data = {
                        'text': text,
                        'testid': testid,
                        'classes': classes[:50],
                        'position': {
                            'x': round(box['x'], 1) if box else None,
                            'y': round(box['y'], 1) if box else None
                        }
                    }
                    button_list.append(data)
                    print(f"   • '{text:25}' | testid={testid}")
        except:
            pass

    findings['buttons'] = button_list
    print(f"   Total: {len(button_list)} botões\n")

    # 3. LINKS IMPORTANTES
    print("[LINK] LINKS PRINCIPAIS:")
    links = page.locator('a[href]').all()
    link_list = []

    for link in links[:30]:  # Limitar a 30
        try:
            if link.is_visible():
                text = link.inner_text().strip()
                href = link.get_attribute('href') or ''
                testid = link.get_attribute('data-testid') or ''

                # Filtrar links vazios ou só com ícones
                if text and len(text) > 1:
                    data = {
                        'text': text,
                        'href': href,
                        'testid': testid
                    }
                    link_list.append(data)
                    print(f"   • {text:30} → {href[:50]}")
        except:
            pass

    findings['links'] = link_list
    print(f"   Total: {len(link_list)} links\n")

    # 4. CARDS/WIDGETS (seções principais do dashboard)
    print("[CHART] CARDS/WIDGETS:")
    cards = page.locator('[class*="card"], [class*="widget"], [class*="panel"]').all()
    card_list = []

    for card in cards[:15]:  # Limitar a 15
        try:
            if card.is_visible():
                text = card.inner_text().strip()[:100]  # Primeiros 100 chars
                classes = card.get_attribute('class') or ''
                testid = card.get_attribute('data-testid') or ''

                data = {
                    'preview_text': text,
                    'classes': classes[:50],
                    'testid': testid
                }
                card_list.append(data)
                print(f"   • {text[:50]}...")
        except:
            pass

    findings['cards'] = card_list
    print(f"   Total: {len(card_list)} cards/widgets\n")

    # 5. TODOS OS DATA-TESTID DA PÁGINA
    print("  TODOS OS DATA-TESTID:")
    all_testids = page.evaluate('''() => {
        const elements = document.querySelectorAll('[data-testid]');
        return Array.from(elements).map(el => ({
            testid: el.getAttribute('data-testid'),
            tag: el.tagName,
            text: el.innerText?.substring(0, 50) || '',
            visible: el.offsetParent !== null
        }));
    }''')

    testid_list = [t for t in all_testids if t['visible']][:50]  # Só visíveis, limitar a 50
    findings['all_testids'] = testid_list

    for t in testid_list[:20]:  # Mostrar só 20 no console
        print(f"   • {t['testid']:40} | <{t['tag']:10}> | {t['text'][:30]}")

    print(f"   Total: {len(testid_list)} testids visíveis\n")

    # SALVAR RELATÓRIO
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'url': current_url,
        'findings': findings,
        'summary': {
            'navigation_items': len(findings['navigation_menu']),
            'buttons': len(button_list),
            'links': len(link_list),
            'cards': len(card_list),
            'testids': len(testid_list)
        }
    }

    with open('DASHBOARD_EXPLORATION_REPORT.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # SCREENSHOT
    print(" Capturando screenshots...")
    page.screenshot(path="DASHBOARD_FULL_PAGE.png", full_page=True)
    page.screenshot(path="DASHBOARD_VIEWPORT.png")  # Só viewport visível

    print("\n" + "="*80)
    print("[OK] EXPLORAÇÃO DO DASHBOARD COMPLETA!")
    print(f"   [LIST] Relatório: DASHBOARD_EXPLORATION_REPORT.json")
    print(f"    Screenshots: DASHBOARD_FULL_PAGE.png + DASHBOARD_VIEWPORT.png")
    print("="*80)
    print("\n[SEARCH] PRÓXIMO PASSO:")
    print("   1. Olhe os screenshots e o JSON")
    print("   2. Identifique o caminho para 'Properties' (criar/listar)")
    print("   3. Me diga qual link/botão usar para começar o fluxo")
    print("\n")

    input("⏸  Pressione ENTER para fechar...")
    browser.close()
