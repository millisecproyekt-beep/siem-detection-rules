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
            
            # QRadar-a nəfəs almaq üçün 5 saniyə vaxt veririk
            page.wait_for_timeout(5000) 
            print("  -> Uğurla daxil olduq!")

            # ZİREH 1: Əgər ekrana "Welcome/License" pop-up çıxıbsa, Escape vurub bağlayırıq
            page.keyboard.press("Escape")
            page.wait_for_timeout(1000)
            page.keyboard.press("Escape")

            print("2. Rules (Qaydalar) menyusuna keçid edilir...")
            
            # ZİREH 2: Tag-dan asılı olmayaraq (a, div, span) ekrandakı ilk 'Offenses' sözünü tapıb vururuq
            offenses_tab = page.locator("text='Offenses'").first
            offenses_tab.wait_for(state="visible", timeout=15000)
            offenses_tab.click(force=True) # force=True başqa element mane olsa belə məcburi klikləyir
            
            page.wait_for_timeout(3000)

            # Eyni məntiq ilə 'Rules' menyusunu tapıb vururuq
            rules_link = page.locator("text='Rules'").first
            rules_link.wait_for(state="visible", timeout=15000)
            rules_link.click(force=True)
            
            page.wait_for_timeout(4000)

            print(f"3. '{rule_name}' qaydası yaradılır...")
            
            frame = page.frame(name="core_iframe") or page.frame_locator("iframe[name='core_iframe']")
            if not frame:
                print("  [!] Diqqət: 'core_iframe' tapılmadı, birbaşa səhifədə axtarılır...")
                frame = page 

            actions_menu = frame.locator("text='Actions'").first
            actions_menu.click(force=True)
            page.wait_for_timeout(1500)

            new_rule_btn = frame.locator("text='New Event Rule'").first
            new_rule_btn.click(force=True)
            page.wait_for_timeout(5000) 

            wizard_frame = page.frame(name="wizard_iframe") or page.frame_locator("iframe[src*='RuleWizard']")
            
            # Rule Wizard səhifəsində Next düyməsi
            if wizard_frame:
                wizard_frame.locator("button:has-text('Next >')").first.click(force=True)
            else:
                page.locator("button:has-text('Next >')").first.click(force=True)
            
            page.wait_for_timeout(2000)

            # Rule Name yazmaq və Finish vurmaq
            if wizard_frame:
                wizard_frame.fill("input[name='ruleName'], input.ruleNameInput", rule_name)
                wizard_frame.locator("button:has-text('Finish')").first.click(force=True)
            else:
                page.fill("input[name='ruleName'], input.ruleNameInput", rule_name)
                page.locator("button:has-text('Finish')").first.click(force=True)

            page.wait_for_timeout(3000)
            print(f"  [OK] '{rule_name}' müvəffəqiyyətlə yaradıldı!")

        except Exception as e:
            print(f"  [XƏTA] Robot '{rule_name}' qaydasını yaradarkən ilişdi: {str(e)}")
            page.screenshot(path=f"error_screenshot_{rule_name}.png") 

        finally:
            browser.close()
            time.sleep(1)

def main():
    if not QRADAR_URL or not QRADAR_USER or not QRADAR_PASS:
        print("CRITICAL XƏTA: URL, USER və ya PASS secret-ləri tapılmadı!")
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
                    else:
                        print(f"  [!] Xəbərdarlıq: '{filename}' faylında 'name' parametri boşdur.")
                except json.JSONDecodeError:
                    print(f"  [!] Xəbərdarlıq: '{filename}' düzgün JSON formatında deyil.")

if __name__ == "__main__":
    main()
