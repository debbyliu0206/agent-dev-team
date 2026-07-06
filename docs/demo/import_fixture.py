"""Demo feeder: plays the role of the pluggable crawler layer.

Reads job-postings-fixture.json (postings as a Reddit/careers-page collector
would deliver them) and pushes each one into the Job Radar ingestion API.
The radar itself decides what to keep: 201 = tracked, 200 = merged into an
existing entry (duplicate from another source), 422 = rejected (not a target
role).

Usage (from the generated app dir, so its venv has the deps):
    cd C:/Users/Debby/Desktop/Projects/demo-output
    ./.venv/Scripts/python.exe C:/Users/Debby/Desktop/Projects/agent-dev-team/docs/demo/import_fixture.py
"""
import json
import pathlib
import sys
import time

import httpx
from jose import jwt

# Windows consoles often default to cp1252, which can't print the emoji labels.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

API = "http://127.0.0.1:8001/api/jobs"
# Demo-only credentials: matches the SECRET_KEY in the generated backend/auth.py
TOKEN = jwt.encode(
    {"sub": "11111111-1111-4111-8111-111111111111"},
    "a_super_secret_key_that_is_long_and_secure",
    algorithm="HS256",
)

fixture = json.loads(
    (pathlib.Path(__file__).parent / "job-postings-fixture.json").read_text(encoding="utf-8")
)

OUTCOME = {201: "✅ TRACKED", 200: "🔁 MERGED (duplicate source)", 422: "🚫 REJECTED (not a target role)"}

added = merged = rejected = 0
with httpx.Client(headers={"Authorization": f"Bearer {TOKEN}"}) as client:
    for p in fixture["postings"]:
        payload = {
            "source_url": p["source_url"],
            "company_name": p["company"],
            "role_title": p["title"],
            "date_posted": p["posted_date"],
            "application_deadline": p.get("deadline"),
        }
        r = client.post(API, json=payload)
        label = OUTCOME.get(r.status_code, f"HTTP {r.status_code}")
        print(f"[{p['source']:<28}] {p['company']:<15} {p['title'][:45]:<47} -> {label}")
        added += r.status_code == 201
        merged += r.status_code == 200
        rejected += r.status_code == 422
        time.sleep(0.4)  # let the audience read each line in the recording

    print(f"\n{added} tracked, {merged} merged, {rejected} rejected")
    dash = client.get(API).json()
    s = dash["summary"]
    print(f"Dashboard: {s['total']} jobs | by category: {s['by_category']} | by status: {s['by_status']}")
