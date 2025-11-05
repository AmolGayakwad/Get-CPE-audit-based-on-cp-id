# Extract Collection Protocol Event Audit Logs from OpenSpecimen

This script exports audit logs for all events of a Collection Protocol in OpenSpecimen using the REST API. It downloads the audit logs as ZIP files for each CP event and generates a detailed CSV report.

---

## Introduction

This script performs the following tasks:

- Authenticates with OpenSpecimen using the REST API and obtains a session token.
- Accepts Collection Protocol (CP) ID as input from the user.
- Fetches all events linked to the given CP.
- Exports audit logs for each CP event via the OpenSpecimen audit API.
- Downloads the ZIP file containing audit data for each event.
- Extracts and processes the CSV file(s) inside the ZIP.
- Transforms the audit logs into a **CSV**, including:
  - Mapping `clinicalDiagnosis` and `clinicalStatus` IDs to their actual values.   
  - Adding **Event ID** and **Event Label** after the operation for clarity.  
- Merges all event CSVs into a single CSV for the CP.

The final CSV provides a complete history of modifications for each event in the CP, with readable field values.

---

## Requirements

- Python 3.x
- `requests` module
- `pandas` module

You can install dependencies using pip:

```bash
pip install requests pandas

## How to Run

1. Download or save the script event_audit.py to your system.
2. Open a terminal and navigate to the folder containing the script.
3. Run the script:

    python3 event_audit.py

    When prompted, enter:

       - Collection Protocol ID
       - The script will generate a merged CSV in the same folder:


## What I Learned

1. How to authenticate and work with OpenSpecimen’s REST API to get session tokens
2. How to fetch CP events and audit logs programmatically
3. How to handle ZIP files and extract CSV content in Python
4. How to parse and transform nested/structured CSV data (change logs) into a wide format
5. How to map IDs (like clinicalDiagnosis or clinicalStatus) to actual values using permissible value APIs
6. How to merge multiple CSV files into a single consolidated report
7. How to write clean, modular Python functions for API interaction, file handling, and data transformation
8. How to add meaningful progress logging for long-running tasks
9. How to clean up temporary files automatically after processing
