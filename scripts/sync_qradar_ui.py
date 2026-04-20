import os
import json
from playwright.sync_api import sync_playwright

QRADAR_URL = os.getenv('QRADAR_URL', '').strip()
QRADAR_USER = os.getenv('QRADAR_USER', '').strip()
QRADAR_PASS = os.getenv('QRADAR_PASS', '').strip()

def run_robot():
    with sync_playwright() as p:
        # Görünməz Chrome brauzeri açılır
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True) # SSL xətalarını keçmək üçün
        page = context.new_page()

        print(f"--- QRadar-a daxil olunur: {QRADAR_URL} ---")
        
        try:
            # Login səhifəsinə get
            page.goto(f"https://{QRADAR_URL}/console/login.jsp")
            
            # Login xanalarını doldur
            page.fill("input[name='j_username']", QRADAR_USER)
            page.fill("input[name='j_password']", QRADAR_PASS)
            
            # Login düyməsinə bas
            page.click("#login_button, .login-button, button[type='submit']")
            
            # Bir az gözlə ki, səhifə açılsın
            page.wait_for_timeout(5000) 
            
            # Yoxlama üçün ekranın şəklini çək
            page.screenshot(path="qradar_logged_in.png")
            print("Successfully logged in and captured screenshot!")
            
        except Exception as e:
            print(f"XƏTA: {str(e)}")
            page.screenshot(path="error_debug.png")
        
        browser.close()

if __name__ == "__main__":
    run_robot()
