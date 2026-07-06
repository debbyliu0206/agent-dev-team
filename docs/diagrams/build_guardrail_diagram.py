"""Build the Security Guardrail Funnel diagram on the Excalidraw canvas.
Companion to build_diagram.py (same helpers/colors). Canvas server at :3000.
Shows: every Coder output crosses three deterministic scanners before disk;
blocked output returns to the Coder as a violation report; three standing
controls surround the loop.
"""
import json, urllib.request

BASE = "http://127.0.0.1:3000"

def post(path, data):
    req = urllib.request.Request(f"{BASE}{path}",
        data=json.dumps(data).encode(), headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req) as r: return json.loads(r.read())

def delete(path):
    req = urllib.request.Request(f"{BASE}{path}", method="DELETE")
    with urllib.request.urlopen(req) as r: return r.read()

delete("/api/elements/clear")
print("Canvas cleared")

def lbl(eid, x, y, text, fs=18, fc="#1e1e1e"):
    w = max(100, len(max(text.split('\n'), key=len)) * fs * 0.82)
    h = (text.count('\n')+1) * fs * 1.6
    return {"id":eid,"type":"text","x":x,"y":y,"width":w,"height":h,
            "text":text,"fontSize":fs,"fontFamily":"1","strokeColor":fc}

def box(eid, x, y, w, h, text, bg, sc="#1e1e1e", fs=14, ss="solid"):
    return {"id":eid,"type":"rectangle","x":x,"y":y,"width":w,"height":h,
            "backgroundColor":bg,"strokeColor":sc,"strokeWidth":2,
            "strokeStyle":ss,"roundness":{"type":3},
            "label":{"text":text,"fontSize":fs,"fontFamily":"1"}}

def arr_bind(eid, src, dst, sc="#495057", sw=2, ss="solid"):
    return {"id":eid,"type":"arrow","x":0,"y":0,
            "start":{"id":src},"end":{"id":dst},
            "strokeColor":sc,"strokeWidth":sw,"strokeStyle":ss,
            "roundness":{"type":2}}

LLM_BG  = "#d0bfff";  LLM_SC  = "#7048e8"
DET_BG  = "#dee2e6";  DET_SC  = "#495057"
OK_BG   = "#b2f2bb";  OK_SC   = "#2b8a3e"
BAD_SC  = "#e03131"

els = []

# Title
els.append(lbl("title", 60, 30, "Security Guardrails — every LLM output crosses this boundary before it touches disk", fs=22))

# ---- Main funnel row (left -> right) --------------------------------------
ROW_Y, BW, BH, GAP = 120, 235, 110, 70
X0 = 60
els.append(box("coder", X0, ROW_Y, BW, BH,
               "Coder (LLM)\nemits CodeChange JSON\n(decide, never apply)", LLM_BG, LLM_SC))
els.append(box("scan", X0 + (BW+GAP)*1, ROW_Y, BW, BH,
               "1. Code Scanner\neval/exec, subprocess,\nsockets, FFI, path escape", DET_BG, DET_SC))
els.append(box("secrets", X0 + (BW+GAP)*2, ROW_Y, BW, BH,
               "2. Secret Scanner\nkeys, passwords,\ncredentialed DB URLs", DET_BG, DET_SC))
els.append(box("deps", X0 + (BW+GAP)*3, ROW_Y, BW, BH,
               "3. Dependency Checker\nlive PyPI verification\n(slopsquatting defense)", DET_BG, DET_SC))
els.append(box("disk", X0 + (BW+GAP)*4, ROW_Y, BW, BH,
               "Write to sandbox\nTARGET_DIR only\n+ isolated app venv", OK_BG, OK_SC))

# ---- Block path ------------------------------------------------------------
BLOCK_Y = ROW_Y + BH + 90
els.append(box("blocked", X0 + (BW+GAP)*1, BLOCK_Y, (BW+GAP)*2 + BW, 80,
               "BLOCKED — nothing written. Violation report goes back to the Coder,\nwhich must regenerate without the violation (next loop iteration)",
               "#ffe3e3", BAD_SC))

# ---- Standing controls row --------------------------------------------------
CTRL_Y = BLOCK_Y + 80 + 90
els.append(lbl("ctl-title", 60, CTRL_Y - 40, "Standing controls around the whole loop:", fs=16, fc="#495057"))
CW = 385
els.append(box("policy", X0, CTRL_Y, CW, 90,
               "Permission Policy (2-tier)\nroutine sandboxed actions auto-approve;\nwrites / unknown packages need a human", DET_BG, DET_SC))
els.append(box("inject", X0 + CW + 60, CTRL_Y, CW, 90,
               "Prompt-Injection Sanitizer\ngenerated code re-entering LLM prompts is\ntokenized; only comments/strings sanitized", DET_BG, DET_SC))
els.append(box("breaker", X0 + (CW + 60)*2, CTRL_Y, CW, 90,
               "Circuit Breaker\nstall detection (3 flat iterations), intent-drift\nwarnings, tests-are-truth done signal", DET_BG, DET_SC))

# ---- Legend (3 items max) ---------------------------------------------------
LG_Y = CTRL_Y + 185  # clear of the control boxes, which auto-grow with wrapped labels
els.append(box("lg1", X0, LG_Y, 26, 26, "", LLM_BG, LLM_SC))
els.append(lbl("lg1t", X0 + 36, LG_Y + 2, "LLM agent", fs=14))
els.append(box("lg2", X0 + 170, LG_Y, 26, 26, "", DET_BG, DET_SC))
els.append(lbl("lg2t", X0 + 206, LG_Y + 2, "Deterministic guardrail", fs=14))
els.append(box("lg3", X0 + 430, LG_Y, 26, 26, "", "#ffe3e3", BAD_SC))
els.append(lbl("lg3t", X0 + 466, LG_Y + 2, "Block path", fs=14))

res = post("/api/elements/batch", {"elements": els})
print(f"Created {len(els)} shapes")

arrows = [
    arr_bind("a1", "coder", "scan", sc=DET_SC, sw=3),
    arr_bind("a2", "scan", "secrets", sc=DET_SC, sw=3),
    arr_bind("a3", "secrets", "deps", sc=DET_SC, sw=3),
    arr_bind("a4", "deps", "disk", sc=OK_SC, sw=3),
    # block paths from each scanner down to the blocked box
    arr_bind("b1", "scan", "blocked", sc=BAD_SC, sw=2, ss="dashed"),
    arr_bind("b2", "secrets", "blocked", sc=BAD_SC, sw=2, ss="dashed"),
    arr_bind("b3", "deps", "blocked", sc=BAD_SC, sw=2, ss="dashed"),
    # report loops back to the coder
    arr_bind("b4", "blocked", "coder", sc=BAD_SC, sw=2, ss="dashed"),
]
res = post("/api/elements/batch", {"elements": arrows})
print(f"Created {len(arrows)} arrows")
print("Done.")
