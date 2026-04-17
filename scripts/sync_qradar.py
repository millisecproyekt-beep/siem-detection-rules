import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Secret-ləri sənin şəklinə uyğun çağırırıq
QRADAR_BASE = os.getenv('QRADAR_URL', '').strip()
QRADAR_TOKEN = os.getenv('QRADAR_TOKEN', '').strip()

# Əgər URL 'https://' ilə başlamırsa, onu avtomatik əlavə edirik
if QRADAR_BASE and not QRADAR_BASE.startswith('http'):
    QRADAR_BASE = f"https://{QRADAR_BASE}"

headers = {
    'SEC': QRADAR_TOKEN,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def get_all_rules():
    """QRadar-dakı mövcud qaydaları çəkir"""
    url = f"{QRADAR_BASE}/api/analytics/rules"
    res = requests.get(url, headers=headers, verify=False)
    return res.json() if res.status_code == 200 else []

def update_rule(rule_id, github_payload):
    """Mövcud qaydanı ID üzərindən POST ilə yeniləyir"""
    url = f"{QRADAR_BASE}/api/analytics/rules/{rule_id}"
    
    # QRadar-ın yenilənməyə icazə vermədiyi daxili sahələri təmizləyirik
    forbidden = ['id', 'identifier', 'owner', 'creation_date', 'modification_date', 'origin']
    clean_payload = {k: v for k, v in github_payload.items() if k not in forbidden}
    
    res = requests.post(url, headers=headers, json=clean_payload, verify=False)
    return res.status_code

def sync():
    print(f"--- QRadar Sinxronizasiyası: {QRADAR_BASE} ---")
    
    if not QRADAR_BASE or not QRADAR_TOKEN:
        print("XƏTA: Secret-lər boşdur! GitHub Settings-i yoxla.")
        return

    qradar_rules = get_all_rules()
    path = "qradar/"
    
    for filename in os.listdir(path):
        if filename.endswith(".json"):
            with open(os.path.join(path, filename), 'r') as f:
                local_rule = json.load(f)
                rule_name = local_rule.get('name').strip()
                
                # QRadar-dakı qayda ilə adı müqayisə edirik
                match = next((r for r in qradar_rules if r['name'].strip() == rule_name), None)
                
                if match:
                    r_id = match['id']
                    print(f"Yenilənir: '{rule_name}' (ID: {r_id})")
                    status = update_rule(r_id, local_rule)
                    print(f"  [OK] Status: {status}" if status in [200, 201, 202] else f"  [XƏTA] Status: {status}")
                else:
                    print(f"  [!] '{rule_name}' tapılmadı. Manual yaradılan adı yoxla.")

if __name__ == "__main__":
    sync()
