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
            page.click("button[type='submit'], input[type='submit']")
            
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000) 
            print("  -> Uğurla daxil olduq!")

            print("2. Rules (Qaydalar) menyusuna keçid edilir...")
            
            page.click("a:has-text('Offenses')")
            page.wait_for_timeout(2000)

            page.click("a:has-text('Rules')")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)

            print(f"3. '{rule_name}' qaydası yaradılır...")
            
            frame = page.frame(name="core_iframe") or page.frame_locator("iframe[name='core_iframe']")
            
            if not frame:
                print("  [!] Diqqət: 'core_iframe' tapılmadı, birbaşa səhifədə axtarılır...")
                frame = page 

            frame.click("span:has-text('Actions')")
            page.wait_for_timeout(1000)

            frame.click("td:has-text('New Event Rule')")
            page.wait_for_timeout(4000) 

            wizard_frame = page.frame(name="wizard_iframe") or page.frame_locator("iframe[src*='RuleWizard']")
            if wizard_frame:
                wizard_frame.click("button:has-text('Next >')")
            else:
                page.click("button:has-text('Next >')")
            
            page.wait_for_timeout(2000)

            if wizard_frame:
                wizard_frame.fill("input[name='ruleName'], input.ruleNameInput", rule_name)
                wizard_frame.click("button:has-text('Finish')")
            else:
                page.fill("input[name='ruleName'], input.ruleNameInput", rule_name)
                page.click("button:has-text('Finish')")

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
