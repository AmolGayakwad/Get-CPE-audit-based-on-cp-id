import requests
import time
import os
import zipfile
import io
import csv
import pandas as pd
import re

BASE_URL = "<>"  // Enter Application URL
USERNAME = "<>"  // Enter Username 
PASSWORD = "<>" // Enter password

def get_token():
    url = f"{BASE_URL}/rest/ng/sessions"
    data = {"loginName": USERNAME, "password": PASSWORD, "domainName": "openspecimen"}
    resp = requests.post(url, json=data, headers={"Content-Type": "application/json"})
    resp.raise_for_status()
    return resp.json().get("token")

def get_cp_events(cp_id, token):
    url = f"{BASE_URL}/rest/ng/collection-protocol-events?cpId={cp_id}"
    resp = requests.get(url, headers={"X-OS-API-TOKEN": token})
    resp.raise_for_status()
    events = [{"id": e["id"], "label": e["eventLabel"]} for e in resp.json()]
    print(f"Found {len(events)} events")
    return events

def get_permissible_map(token, attr):
    url = f"{BASE_URL}/rest/ng/permissible-values/v?attribute={attr}&includeOnlyLeafValue=false"
    resp = requests.get(url, headers={"X-OS-API-TOKEN": token})
    resp.raise_for_status()
    return {str(d["id"]): d.get("value", d.get("name", "Not Specified")) for d in resp.json()}

def extract_id(val):
    m = re.search(r"id=(\d+)", val)
    return m.group(1) if m else None

def export_event_audit(event_id, token):
    now = int(time.time() * 1000)
    last_year = now - 365*24*60*60*1000
    payload = {
        "recordIds": [int(event_id)],
        "entities": ["CollectionProtocolEvent"],
        "includeModifiedProps": True,
        "startDate": last_year,
        "endDate": now
    }
    url = f"{BASE_URL}/rest/ng/audit/export-revisions"
    resp = requests.post(url, json=payload, headers={"X-OS-API-TOKEN": token, "Content-Type": "application/json"})
    resp.raise_for_status()
    return resp.json().get("fileId")

def wait_for_file(file_id, token, max_wait=60):
    url = f"{BASE_URL}/rest/ng/audit/revisions-file?fileId={file_id}"
    for i in range(max_wait // 5):
        resp = requests.get(url, headers={"X-OS-API-TOKEN": token}, stream=True)
        if resp.status_code == 200:
            return resp
        elif resp.status_code == 404:
            print(f"Waiting for file ({(i+1)*5}s)...")
            time.sleep(5)
        else:
            resp.raise_for_status()
    raise Exception("File not available within timeout.")

def split_changes(log):
    parts, cur, lvl = [], '', 0
    for ch in log:
        if ch == ',' and lvl == 0:
            parts.append(cur.strip())
            cur = ''
        else:
            if ch in '[{': lvl += 1
            elif ch in ']}': lvl -= 1
            cur += ch
    if cur: parts.append(cur.strip())
    return parts

def transform_csv(input_csv, output_csv, event_id, event_label, diag_map, status_map):
    grouped, all_fields = {}, set()
    with open(input_csv, encoding='utf-8') as f:
        for _ in range(7): next(f, None)
        reader = csv.DictReader(f)
        for row in reader:
            ch_log = row.get("Change Log","")
            if not ch_log: continue
            key = (row.get("Timestamp",""), row.get("User",""), row.get("Operation",""))
            if key not in grouped: grouped[key]={}
            for c in split_changes(ch_log):
                if "=" not in c: continue
                field, val = c.split("=",1)
                field, val = field.strip(), val.strip()
                # Map clinicalDiagnosis
                if field=="clinicalDiagnosis":
                    val_id = extract_id(val)
                    val = diag_map.get(val_id,val) if val_id else val
                # Map clinicalStatus and default to "Not Specified"
                elif field=="clinicalStatus":
                    val_id = extract_id(val)
                    val = status_map.get(val_id,"Not Specified")
                # Remove eventLabel from change log
                if field=="eventLabel":
                    continue
                # Default any {id=...} still left
                if re.match(r"\{id=\d+\}", val):
                    val = "Not Specified"
                grouped[key][field]=val
                all_fields.add(field)
    all_fields = sorted(all_fields)
    with open(output_csv,"w",newline="",encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["Modified Date","Modified By","Operation","Event ID","Event Label"] + all_fields
        writer.writerow(header)
        for (date,user,op), fields in grouped.items():
            row = [date,user,op,event_id,event_label]+[fields.get(f,"") for f in all_fields]
            writer.writerow(row)

def download_csv(file_id, token, folder, event_id, event_label, diag_map, status_map):
    resp = wait_for_file(file_id, token)
    zip_bytes = io.BytesIO(resp.content)
    with zipfile.ZipFile(zip_bytes,"r") as zf:
        csv_files = [f for f in zf.namelist() if f.startswith("os_core_objects_revisions_") and f.endswith(".csv")]
        if not csv_files: raise Exception("No CSV in ZIP")
        raw_path = os.path.join(folder,f"event_{event_id}_raw.csv")
        with zf.open(csv_files[0]) as src, open(raw_path,"wb") as out_f: out_f.write(src.read())
    wide_path = os.path.join(folder,f"event_{event_id}_{event_label.replace(' ','_')}_wide.csv")
    transform_csv(raw_path, wide_path, event_id, event_label, diag_map, status_map)
    os.remove(raw_path)
    print(f"Created {wide_path}")
    return wide_path

def merge_csvs(folder, merged_csv):
    files = [os.path.join(folder,f) for f in os.listdir(folder) if f.endswith("_wide.csv")]
    if not files: return
    pd.concat([pd.read_csv(f) for f in files],ignore_index=True).to_csv(merged_csv,index=False)
    print(f"Merged CSV: {merged_csv}")

def main():
    cp_id = input("Enter CP ID: ").strip()
    token = get_token()
    diag_map = get_permissible_map(token,"clinical_diagnosis")
    status_map = get_permissible_map(token,"clinical_status")
    events = get_cp_events(cp_id, token)
    if not events: 
        print("No events found for this CP.")
        return
    folder = f"event_audits_cp_{cp_id}"
    os.makedirs(folder,exist_ok=True)
    for e in events:
        print(f"Processing Event {e['label']} ({e['id']})")
        try:
            file_id = export_event_audit(e["id"],token)
            if file_id: download_csv(file_id, token, folder, e["id"], e["label"], diag_map, status_map)
        except Exception as ex:
            print(f"Failed {e['label']}: {ex}")
    merge_csvs(folder,f"cp_{cp_id}_merged_event_audit.csv")

if __name__=="__main__":
    main()
