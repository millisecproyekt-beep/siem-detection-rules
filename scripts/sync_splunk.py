import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Secret-dən gələn: http://45.55.59.89:8000
RAW_URL = os.getenv('SPLUNK_URL', '').strip()
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN', '').strip()

# IP-ni təmiz şəkildə çıxarırıq (Məsələn: 45.55.59.89)
clean_ip = RAW_URL.replace("http://", "").replace("https://", "").split(':')[0]
# API üçün mütləq 8089 portunu təyin edirik
API_BASE = f"https://{clean_ip}:8089"

def sync_splunk():
    print(f"--- Splunk API Bağlantısı: {API_BASE} ---")
    headers = {
        "Authorization": f"Bearer {SPLUNK_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    path = "splunk/"
    for filename in os.listdir(path):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(path, filename), 'r') as f:
                    rule = json.load(f)
                    # Splunk API Endpoint
                    api_url = f"{API_BASE}/services/saved/searches?output_mode=json"
                    
                    payload = {
                        "name": rule['name'],
                        "search": rule['search'],
                        "is_scheduled": 1,
                        "disabled": 0
                    }
                    
                    # 10 saniyə gözləyirik, cavab gəlməsə timeout verəcək
                    res = requests.post(api_url, data=payload, headers=headers, verify=False, timeout=10)
                    print(f"✅ {filename} göndərildi. Status: {res.status_code}")
            except Exception as e:
                print(f"❌ {filename} xətası: {str(e)}")

if __name__ == "__main__":
    sync_splunk()

