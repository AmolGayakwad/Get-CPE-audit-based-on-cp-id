import requests
import csv
import os

BASE_URL = "https://demo.openspecimen.org"
USERNAME = "amol@krishagni.com"
PASSWORD = "Login@123"

def get_token():
    """Authenticate and get session token"""
    url = f"{BASE_URL}/rest/ng/sessions"
    data = {
        "loginName": USERNAME,
        "password": PASSWORD,
        "domainName": "openspecimen"
    }
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, json=data, headers=headers)
    resp.raise_for_status()
    return resp.json()["token"]

def get_cp_events(cp_id, token):
    """Fetch all collection protocol events by CP ID"""
    url = f"{BASE_URL}/rest/ng/collection-protocol-events?cpId={cp_id}"
    headers = {"X-OS-API-TOKEN": token}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

def export_events_to_csv(events, output_file):
    """Export fetched events to CSV"""
    if not events:
        print("No events found for this Collection Protocol.")
        return

    fieldnames = [
        "ID",
        "Event Label",
        "Collection Protocol",
        "defaultSite",
        "clinicalDiagnosis",
        "clinicalStatus",
        "activityStatus",
        "code"
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for event in events:
            writer.writerow({
                "ID": event.get("id"),
                "Event Label": event.get("eventLabel"),      
                "Collection Protocol": event.get("collectionProtocol"),
                "defaultSite": event.get("defaultSite"),
                "clinicalDiagnosis": event.get("clinicalDiagnosis"),
                "clinicalStatus": event.get("clinicalStatus"),
                "activityStatus": event.get("activityStatus"),
                "code": event.get("code")
            })

def main():
    cp_id = input("Enter Collection Protocol ID: ").strip()

    try:
        token = get_token()
        print(f"Fetching collection protocol events for CP ID: {cp_id}...")
        events = get_cp_events(cp_id, token)

        output_file = f"cp_{cp_id}_events.csv"
        export_events_to_csv(events, output_file)
        print(f"Export completed. File saved as: {output_file}")

    except requests.HTTPError as e:
        print(f"HTTP error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
