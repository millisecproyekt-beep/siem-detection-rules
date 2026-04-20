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
        
        # headless=True arxa planda görünməz işləməsi üçündür. 
        # (Əgər test mərhələsində nə baş verdiyini gözlə görmək istəsən, öz lokalında headless=False edə bilərsən)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        try:
            # -----------------------------------------
            # 1. LOGIN MƏRHƏLƏSİ
            # -----------------------------------------
            print("1. QRadar-a daxil olunur...")
            page.goto(f"{QRADAR_URL}/console/login.jsp", wait_until="networkidle")

            page.fill("input[name='j_username']", QRADAR_USER)
            page.fill("input[name='j_password']", QRADAR_PASS)
            page.click("button[type='submit'], input[type='submit']")
            
            # Ana səhifənin yüklənməsini gözləyirik (QRadar ağır olduğu üçün bir az vaxt veririk)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000) 
            print("  -> Uğurla daxil olduq!")

            # -----------------------------------------
            # 2. OFFENSES -> RULES MENYUSUNA KEÇİD
            # -----------------------------------------
            print("2. Rules (Qaydalar) menyusuna keçid edilir...")
            
            # Yuxarı menyudan 'Offenses' tabını tapıb klikləyirik
            page.click("a:has-text('Offenses')")
            page.wait_for_timeout(2000)

            # Sol menyudan 'Rules' linkini tapıb klikləyirik
            page.click("a:has-text('Rules')")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)

            # -----------------------------------------
            # 3. YENİ QAYDA YARATMAQ (Actions -> New Event Rule)
            # -----------------------------------------
            print(f"3. '{rule_name}' qaydası yaradılır...")
            
            # QRadar qaydalar səhifəsini iframe-in içində açır, buna görə də o iframe-i tapmalıyıq
            # Adətən id-si "core_iframe" və ya "myIframe" olur.
            frame = page.frame(name="core_iframe") or page.frame_locator("iframe[name='core_iframe']")
            
            if not frame:
                print("  [!] Diqqət: 'core_iframe' tapılmadı, birbaşa səhifədə axtarılır...")
                frame = page # iframe yoxdursa ana səhifədə axtar

            # 'Actions' dropdown menyusuna basırıq
            frame.click("span:has-text('Actions')")
            page.wait_for_timeout(1000)

            # Açılan menyudan 'New Event Rule' seçirik
            frame.click("td:has-text('New Event Rule')")
            page.wait_for_timeout(4000) # Yeni pəncərənin açılmasını gözləyirik

            # -----------------------------------------
            # 4. RULE WIZARD (Qayda Sehrbazı) PƏNCƏRƏSİ
            # -----------------------------------------
            # QRadar Rule yaratmaq üçün yeni kiçik pop-up (window/iframe) açır.
            # Biz formun ilk səhifəsindəki 'Next' düyməsinə basırıq
            wizard_frame = page.frame(name="wizard_iframe") or page.frame_locator("iframe[src*='RuleWizard']")
            if wizard_frame:
                wizard_frame.click("button:has-text('Next >')")
            else:
                page.click("button:has-text('Next >')")
            
            page.wait_for_timeout(2000)

            # Rule Name (Qayda adı) xanasını tapıb adımızı yazırıq
            if wizard_frame:
                wizard_frame.fill("input[name='ruleName'], input.ruleNameInput", rule_name)
                # Save/Finish düyməsinə basırıq (Task yalnız "Placeholder" yaratmaq olduğu üçün dərhal finish edirik)
                wizard_frame.click("button:has-text('Finish')")
            else:
                page.fill("input[name='ruleName'], input.ruleNameInput", rule_name)
                page.click("button:has-text('Finish')")

            page.wait_for_timeout(3000)
            print(f"  [OK] '{rule_name}' müvəffəqiyyətlə yaradıldı!")

        except Exception as e:
            print(f"  [XƏTA] Robot '{rule_name}' qaydasını yaradarkən ilişdi: {str(e)}")
            # ÇOX VACİB: Xəta olan anın şəklini çəkib yadda saxlayır ki, səhvi vizual görə biləsən!
            page.screenshot(path=f"error_screenshot_{rule_name}.png") 

        finally:
            browser.close()
            time.sleep(1) # Növbəti qaydaya keçmədən əvvəl brauzerə bağlanmaq üçün vaxt veririk

def main():
    if not QRADAR_URL or not QRADAR_USER or not QRADAR_PASS:
        print("CRITICAL XƏTA: URL, USER və ya PASS secret-ləri tapılmadı!")
        return

    path = "qradar/"
    # JSON fayllarını tapırıq
    for filename in os.listdir(path):
        if filename.endswith(".json"):
            with open(os.path.join(path, filename), 'r') as f:
                try:
                    local_rule = json.load(f
