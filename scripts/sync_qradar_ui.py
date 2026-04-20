import os
import json
import time
from playwright.sync_api import sync_playwright

QRADAR_URL = os.getenv('QRADAR_URL', '').strip()
QRADAR_USER = os.getenv('QRADAR_USER', '').strip()
QRADAR_PASS = os.getenv('QRADAR_PASS', '').strip()

if QRADAR_URL and not QRADAR_URL.startswith('https'):
    QRADAR_URL = f"https://{QRADAR_URL}"

def create_rule_with_robot(rule_name):
    with sync_playwright() as p:
        print(f"--- [Robot] '{rule_name}' üçün Chrome brauzeri açılır ---")
        
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        try:
            print("1. QRadar-a daxil olunur...")
            page.goto(f"{QRADAR_URL}/console/login.jsp", wait_until="networkidle")

            page.fill("input[name='j_username']", QRADAR_USER)
            page.fill("input[name='j_password']", QRADAR_PASS)
            page.press("input[name='j_password']", "Enter")
            
            page.wait_for_timeout(5000) 
            print("  -> Uğurla daxil olduq!")

            # Lisenziya və ya Alert Pop-up-larını bağlamaq
            print("  [>] Alert pəncərələri yoxlanılır...")
            ok_button = page.locator("button:has-text('OK'), button:has-text('Close')").first
            if ok_button.is_visible(timeout=5000):
                ok_button.click(force=True)
                print("    - 'OK' klikləndi.")
                page.wait_for_timeout(2000)

            print("2. Offenses menyusuna keçid edilir...")
            # 'Offenses' tabına klikləyirik
            offenses_tab = page.locator("#Core_Offenses, text='Offenses'").first
            offenses_tab.wait_for(state="visible", timeout=15000)
            offenses_tab.click(force=True)
            
            # Tələbinə uyğun olaraq: 20 saniyə gözlə
            print("  [WAIT] 'Offenses' sonrası 20 saniyə gözlənilir...")
            page.wait_for_timeout(20000)

            print("3. Rules menyusuna keçid edilir...")
            # 'Rules' linkinə klikləyirik
            rules_link = page.locator("#Core_Rules, text='Rules'").first
            rules_link.wait_for(state="visible", timeout=15000)
            rules_link.click(force=True)
            
            # Tələbinə uyğun olaraq: Yenə 20 saniyə gözlə
            print("  [WAIT] 'Rules' sonrası 20 saniyə gözlənilir...")
            page.wait_for_timeout(20000)

            print(f"4. '{rule_name}' qaydası yaradılır...")
            
            # QRadar-ın daxili iframe-ni tapırıq (Rules səhifəsi adətən iframe içindədir)
            frame = page.frame(name="core_iframe") or page.frame_locator("iframe[name='core_iframe']")
            if not frame:
                frame = page 

            # Actions menyusuna kliklə
            actions_menu = frame.locator("text='Actions'").first
            actions_menu.click(force=True)
            page.wait_for_timeout(2000)

            # Yeni Rule yaradılmasını başlat
            new_rule_btn = frame.locator("text='New Event Rule'").first
            new_rule_btn.click(force=True)
            page.wait_for_timeout(5000) 

            # Wizard (sehirbaz) pəncərəsi ilə işləmək
            wizard_frame = page.frame(name="wizard_iframe") or page.frame_locator("iframe[src*='RuleWizard']")
            
            target = wizard_frame if wizard_frame else page
            
            target.locator("button:has-text('Next >')").first.click(force=True)
            page.wait_for_timeout(2000)

            target.fill("input[name='ruleName'], input.ruleNameInput", rule_name)
            target.locator("button:has-text('Finish')").first.click(force=True)

            page.wait_for_timeout(3000)
            print(f"  [OK] '{rule_name}' müvəffəqiyyətlə yaradıldı!")

        except Exception as e:
            print(f"  [XƏTA] Robot proses zamanı ilişdi: {str(e)}")

        finally:
            browser.close()
            time.sleep(1)

def main():
    if not QRADAR_URL or not QRADAR_USER or not QRADAR_PASS:
        print("XƏTA: Giriş məlumatları (Secrets) tapılmadı!")
        return

    path = "qradar/"
    for filename in os.listdir(path):
        if filename.endswith(".json"):
            with open(os.path.join(path, filename), 'r') as f:
                try:
                    local_rule = json.load(f)
                    rule_name = local_rule.get('name', '').strip()
                    if rule_name:
                        create_rule_with_robot(rule_name)
                except Exception as e:
                    print(f"  [!] Fayl oxunarkən xəta: {filename}")

if __name__ == "__main__":
    main()

