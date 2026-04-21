import os
import json
import time
import re
from playwright.sync_api import sync_playwright

# GitHub Secrets-dən dəyərləri çəkirik
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
            # Networkidle əvəzinə domcontentloaded və 60 saniyə limit (Şəbəkə problemlərinə qarşı)
            page.goto(f"{QRADAR_URL}/console/login.jsp", wait_until="domcontentloaded", timeout=60000)

            page.fill("input[name='j_username']", QRADAR_USER)
            page.fill("input[name='j_password']", QRADAR_PASS)
            page.press("input[name='j_password']", "Enter")
            
            print("  [WAIT] Dashboard-un tam yüklənməsi və Pop-up-ların çıxması üçün 15 saniyə gözlənilir...")
            page.wait_for_timeout(15000) 
            print("  -> Uğurla daxil olduq!")

            print("  [>] Alert və Pop-up pəncərələri məcburi bağlanır...")
            # Lisenziya pəncərələrini bağlamaq üçün 4 dəfə Escape vururuq
            for _ in range(4):
                page.keyboard.press("Escape")
                page.wait_for_timeout(1000)
            
            # Hər ehtimala qarşı ekranda qalan OK/Close düyməsini axtarıb zorla vururuq
            try:
                page.locator("button:has-text('OK'), button:has-text('Close'), button:has-text('I Agree')").first.click(force=True, timeout=2000)
            except:
                pass

            print("2. Offenses menyusuna keçid edilir...")
            
            # ZİREHLİ AXTARIŞ (REGEX): Sözün ətrafındakı boşluqları və böyük/kiçik hərfləri vecinə almır
            offenses_regex = page.get_by_text(re.compile(r"^\s*Offenses\s*$", re.IGNORECASE)).first
            offenses_link = page.get_by_role("link", name=re.compile(r"Offenses", re.IGNORECASE)).first
            
            if offenses_regex.is_visible(timeout=5000):
                offenses_regex.click(force=True)
            elif offenses_link.is_visible(timeout=5000):
                offenses_link.click(force=True)
            else:
                # Ən son çıxış yolu: XPath
                page.locator("xpath=//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'offenses') and not(contains(text(), 'My'))]").first.click(force=True)
            
            print("  [WAIT] 'Offenses' sonrası 15 saniyə gözlənilir...")
            page.wait_for_timeout(15000)

            print("3. Rules menyusuna keçid edilir...")
            rules_regex = page.get_by_text(re.compile(r"^\s*Rules\s*$", re.IGNORECASE)).first
            rules_link = page.get_by_role("link", name=re.compile(r"Rules", re.IGNORECASE)).first
            
            if rules_regex.is_visible(timeout=5000):
                rules_regex.click(force=True)
            elif rules_link.is_visible(timeout=5000):
                rules_link.click(force=True)
            else:
                page.locator("text='Rules'").first.click(force=True)
            
            print("  [WAIT] 'Rules' sonrası 15 saniyə gözlənilir...")
            page.wait_for_timeout(15000)

            print(f"4. '{rule_name}' qaydası yaradılır...")
            
            frame = page.frame(name="core_iframe") or page.frame_locator("iframe[name='core_iframe']")
            if not frame:
                frame = page 

            actions_menu = frame.get_by_text(re.compile(r"Actions", re.IGNORECASE)).first
            if not actions_menu.is_visible(timeout=3000):
               actions_menu = frame.locator("text='Actions'").first
            actions_menu.click(force=True)
            page.wait_for_timeout(2000)

            new_rule_btn = frame.get_by_text(re.compile(r"New Event Rule", re.IGNORECASE)).first
            if not new_rule_btn.is_visible(timeout=3000):
               new_rule_btn = frame.locator("text='New Event Rule'").first
            new_rule_btn.click(force=True)
            page.wait_for_timeout(5000) 

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


