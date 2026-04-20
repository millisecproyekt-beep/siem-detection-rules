import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

QRADAR_BASE = os.getenv('QRADAR_URL', '').strip()
QRADAR_TOKEN = os.getenv('QRADAR_TOKEN', '').strip()

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
    forbidden = ['id', 'identifier', 'owner', 'creation_date', 'modification_date', 'origin']
    clean_payload = {k: v for k, v in github_payload.items() if k not in forbidden}
    res = requests.post(url, headers=headers, json=clean_payload, verify=False)
    return res.status_code, res.text

def create_rule(github_payload):
    """QRadar-da olmayan yeni qaydanı sıfırdan yaradır"""
    url = f"{QRADAR_BASE}/api/analytics/rules"
    # Yeni yaradanda id olmamalıdır
    clean_payload = {k: v for k, v in github_payload.items() if k != 'id'}
    res = requests.post(url, headers=headers, json=clean_payload, verify=False)
    return res.status_code, res.text

def sync():
    print(f"--- QRadar Sinxronizasiyası: {QRADAR_BASE} ---")
    
    if not QRADAR_BASE or not QRADAR_TOKEN:
        print("XƏTA: Secret-lər boşdur! GitHub Settings -> Secrets bölməsini yoxla.")
        return

    qradar_rules = get_all_rules()
    path = "qradar/"
    
    for filename in os.listdir(path):
        if filename.endswith(".json"):
            with open(os.path.join(path, filename), 'r') as f:
                local_rule = json.load(f)
                rule_name = local_rule.get('name', '').strip()
                
                # QRadar-dakı qayda ilə adı müqayisə edirik
                match = next((r for r in qradar_rules if r.get('name', '').strip() == rule_name), None)
                
                if match:
                    r_id = match['id']
                    print(f"Yenilənir: '{rule_name}' (ID: {r_id})")
                    status, msg = update_rule(r_id, local_rule)
                    if status in [200, 201, 202]:
                        print(f"  [OK] Uğurla yeniləndi!")
                    else:
                        print(f"  [XƏTA] Status: {status} - Detal: {msg}")
                else:
                    print(f"YENİ YARADILIR: '{rule_name}'")
                    status, msg = create_rule(local_rule)
                    if status in [201, 202]: # QRadar uğurlu yaradılma üçün 201 qaytarır
                        print(f"  [OK] Uğurla yaradıldı!")
                    else:
                        print(f"  [XƏTA] Status: {status} - Detal: {msg}")

if __name__ == "__main__":
    sync()
