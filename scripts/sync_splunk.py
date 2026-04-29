import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# GitHub Secret-dən gələn məlumatı götürürük
RAW_INPUT = os.getenv('SPLUNK_URL', '').strip()
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN', '').strip()

# BÜTÜN PROBLEM BURADA HƏLL OLUNUR:
# http, https, slash və köhnə portları təmizləyib yalnız təmiz IP-ni saxlayırıq
clean_host = RAW_INPUT.replace("https://", "").replace("http://", "").split('/')[0].split(':')[0]

# Splunk API üçün mütləq https və 8089 portu lazımdır
API_BASE = f"https://{clean_host}:8089"

def sync_splunk():
    print(f"--- Düzgün API Ünvanı: {API_BASE} ---")
    
    headers = {
        "Authorization": f"Bearer {SPLUNK_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    path = "splunk/"
    if not os.path.exists(path):
        print(f"XƏTA: '{path}' qovluğu tapılmadı!")
        return

    for filename in os.listdir(path):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(path, filename), 'r', encoding='utf-8') as f:
                    rule = json.load(f)
                    
                    # API Endpoint (saved/searches)
                    api_url = f"{API_BASE}/services/saved/searches?output_mode=json"
                    
                    payload = {
                        "name": rule['name'],
                        "search": rule['search'],
                        "is_scheduled": 1,
                        "disabled": 0
                    }
                    
                    # Göndəririk
                    res = requests.post(api_url, data=payload, headers=headers, verify=False, timeout=15)
                    
                    if res.status_code in [200, 201]:
                        print(f"✅ UĞURLU: {filename}")
                    else:
                        print(f"❌ XƏTA: {filename} (Status: {res.status_code}) - {res.text[:100]}")
            except Exception as e:
                print(f"❌ XƏTA ({filename}): {str(e)}")

if __name__ == "__main__":
    sync_splunk()
