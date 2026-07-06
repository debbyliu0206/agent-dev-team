"""Verify the diagram: zoom to fit, screenshot, report element count.
Fixed filename — rerun without permission changes.
Requires: Excalidraw canvas at http://127.0.0.1:3000
          Playwright MCP available
Output: diagram-check.png in project root (overwritten each run)
"""
import json, urllib.request, subprocess, sys, time

BASE = "http://127.0.0.1:3000"

def get_json(path):
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return json.loads(r.read())

def post(path, data):
    req = urllib.request.Request(f"{BASE}{path}",
        data=json.dumps(data).encode(), headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req) as r: return json.loads(r.read())

# 1. Count elements
data = get_json("/api/elements")
els = data.get("elements", data) if isinstance(data, dict) else data
print(f"Elements on canvas: {len(els)}")

# 2. Count by type
types = {}
for e in els:
    t = e.get("type", "?")
    types[t] = types.get(t, 0) + 1
print(f"By type: {types}")

# 3. Check for required agent IDs
required = ["pm", "arch", "tw", "coder", "ca", "di", "tr1", "tf", "tr2", "kb", "sr", "gate", "utg", "e2e", "human", "fc"]
ids = {e.get("id") for e in els}
missing = [r for r in required if r not in ids]
if missing:
    print(f"MISSING agents: {missing}")
else:
    print(f"All {len(required)} required boxes present")

# 4. Zoom to fit
post("/api/viewport", {"scrollToContent": True})
print("Viewport: scrolled to content")

print("\nVerification done. Take screenshot via Playwright to visually inspect.")
