import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

QRADAR_URL = os.getenv('QRADAR_URL', '').strip()
QRADAR_TOKEN = os.getenv('QRADAR_TOKEN', '').strip()

headers = {
    "SEC": QRADAR_TOKEN,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def get_rule_id_by_name(rule_name):
    """Qaydanın adına görə ID-sini tapır"""
    url = f"{QRADAR_URL}/api/analytics/rules?filter=name%3D%22{rule_name}%22"
    res = requests.get(url, headers=headers, verify=False)
    if res.status_code == 200:
        data = res.json()
        return data[0]['id'] if data else None
    return None

def sync_qradar():
    print("\n--- QRadar Ağıllı Sinxronizasiya Başladı ---")
    path = "qradar/"
    
    for filename in os.listdir(path):
        if filename.endswith('.json'):
            with open(os.path.join(path, filename), 'r', encoding='utf-8') as f:
                new_rule_data = json.load(f)
                rule_name = new_rule_data['name']
                
                # 1. Qayda varmı? Yoxla.
                rule_id = get_rule_id_by_name(rule_name)
                
                if rule_id:
                    # 2. VARSA: Yenilə (Update)
                    print(f"Yenilənir (ID: {rule_id}): {rule_name}")
                    update_url = f"{QRADAR_URL}/api/analytics/rules/{rule_id}"
                    res = requests.post(update_url, json=new_rule_data, headers=headers, verify=False)
                else:
                    # 3. YOXDURSA: Yarat (Create)
                    print(f"Yeni yaradılır: {rule_name}")
                    create_url = f"{QRADAR_URL}/api/analytics/rules"
                    res = requests.post(create_url, json=new_rule_data, headers=headers, verify=False)
                
                if res.status_code in [200, 201]:
                    print(f"✅ UĞURLU: {rule_name}")
                else:
                    print(f"❌ XƏTA: {rule_name} (Status: {res.status_code}) - {res.text}")

if __name__ == "__main__":
    sync_qradar()
