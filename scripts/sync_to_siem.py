import os
import json
import requests
import urllib3

# SSL xətalarını görməzdən gəlmək üçün (Self-signed sertifikatlar üçün)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# GitHub Secrets-dən məlumatları oxuyuruq
SPLUNK_URL = os.getenv('SPLUNK_URL')
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN')

def sync_splunk_rules():
    print("--- Splunk Qaydaları Sinxronizasiya Edilir ---")
    rule_path = "splunk/" # Splunk qovluğundakı fayllar
    
    if not os.path.exists(rule_path):
        print("Splunk qovluğu tapılmadı!")
        return

    for filename in os.listdir(rule_path):
        if filename.endswith(".json"):
            with open(os.path.join(rule_path, filename), 'r', encoding='utf-8') as f:
                rule_data = json.load(f)
                
                # Splunk API Endpoint (Saved Searches)
                # Qeyd: Rule adındakı boşluqları API üçün uyğunlaşdırırıq
                api_url = f"{SPLUNK_URL}/services/saved/searches"
                
                headers = {
                    "Authorization": f"Splunk {SPLUNK_TOKEN}"
                }
                
                # API-ya göndəriləcək data
                payload = {
                    "name": rule_data['name'],
                    "search": rule_data['search'],
                    "description": rule_data.get('description', 'GitHub-dan idarə olunan rule'),
                    "cron_schedule": rule_data.get('cron_schedule', '*/15 * * * *'),
                    "is_scheduled": 1,
                    "actions": "email,webhook", # Ehtiyaca uyğun dəyişdirilə bilər
                    "output_mode": "json"
                }

                print(f"Göndərilir: {rule_data['name']}...")
                
                # Splunk API-na sorğu göndəririk
                response = requests.post(api_url, data=payload, headers=headers, verify=False)
                
                if response.status_code in [200, 201]:
                    print(f"Uğurlu: {rule_data['name']} yaradıldı/yeniləndi.")
                elif response.status_code == 409: # Artıq mövcuddursa update et
                     update_url = f"{api_url}/{rule_data['name']}"
                     requests.post(update_url, data=payload, headers=headers, verify=False)
                     print(f"Yeniləndi: {rule_data['name']}")
                else:
                    print(f"Xəta: {rule_data['name']} - Status: {response.status_code}")

if __name__ == "__main__":
    sync_splunk_rules()
