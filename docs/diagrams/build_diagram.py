"""Build the architecture diagram on Excalidraw canvas.
Fixed filename — rerun to rebuild. See DIAGRAM_REQUIREMENTS.md for ground truth.
Canvas server must be running at http://127.0.0.1:3000
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

def get_json(path):
    with urllib.request.urlopen(f"{BASE}{path}") as r: return json.loads(r.read())

delete("/api/elements/clear")
print("Canvas cleared")

# ═══════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════
def zone(eid, x, y, w, h, bg, sc, sw=2, ss="solid"):
    return {"id":eid,"type":"rectangle","x":x,"y":y,"width":w,"height":h,
            "backgroundColor":bg,"strokeColor":sc,"strokeWidth":sw,
            "strokeStyle":ss,"roundness":{"type":3},"opacity":100}

def lbl(eid, x, y, text, fs=18, fc="#1e1e1e"):
    w = max(100, len(max(text.split('\n'), key=len)) * fs * 0.82)
    h = (text.count('\n')+1) * fs * 1.6
    return {"id":eid,"type":"text","x":x,"y":y,"width":w,"height":h,
            "text":text,"fontSize":fs,"fontFamily":"1","strokeColor":fc}

def box(eid, x, y, w, h, text, bg, sc="#1e1e1e", fs=14):
    return {"id":eid,"type":"rectangle","x":x,"y":y,"width":w,"height":h,
            "backgroundColor":bg,"strokeColor":sc,"strokeWidth":2,
            "roundness":{"type":3},
            "label":{"text":text,"fontSize":fs,"fontFamily":"1"}}

def arr_bind(eid, src, dst, sc="#495057", sw=2):
    return {"id":eid,"type":"arrow","x":0,"y":0,
            "start":{"id":src},"end":{"id":dst},
            "strokeColor":sc,"strokeWidth":sw,
            "roundness":{"type":2}}

def arr_pts(eid, x, y, pts, sc="#495057", sw=2):
    return {"id":eid,"type":"arrow","x":x,"y":y,
            "points":pts,"strokeColor":sc,"strokeWidth":sw,
            "roundness":{"type":2},"endArrowhead":"arrow"}

# ═══════════════════════════════════════════════════
# COLORS
# ═══════════════════════════════════════════════════
LLM_BG  = "#d0bfff";  LLM_SC  = "#7048e8"
DET_BG  = "#dee2e6";   DET_SC  = "#495057"
HUMAN_BG = "#a5d8ff";  HUMAN_SC = "#1971c2"
LOOP_BG = "#fff9db";   LOOP_SC = "#e8590c"
VER_BG  = "#c3fae8";   VER_SC  = "#0ca678"
PHASE_SC = "#7048e8"

# ═══════════════════════════════════════════════════
# LAYOUT
# ═══════════════════════════════════════════════════
LEFT = 50
ZONE_W = 1050
BW = 200
BH = 70
HGAP = 60
VGAP = 55
PHASE_GAP = 45

shapes = []

# ════════════════════════════════════════════
# TITLE
# ════════════════════════════════════════════
shapes.append(lbl("title", LEFT, 10,
    "Agent Dev Team — Multi-Agent Pipeline", fs=24, fc="#1e1e1e"))

# ════════════════════════════════════════════
# LEGEND (standalone, between title and Phase 1)
# ════════════════════════════════════════════
LEG_Y = 46
LEG_H = 48
shapes.append(zone("leg-bg", LEFT, LEG_Y, 500, LEG_H, "#ffffff", "#ced4da", sw=1))

SX = LEFT + 10;  SW_W = 18;  SW_H = 12;  TX = 24
SY1 = LEG_Y + 7;  SY2 = SY1 + 22

shapes.append(zone("sw-llm", SX, SY1, SW_W, SW_H, LLM_BG, LLM_SC, sw=1))
shapes.append(lbl("lt-llm", SX + TX, SY1 - 1, "LLM Agent (Gemini)", fs=11, fc="#1e1e1e"))
shapes.append(zone("sw-det", SX + 155, SY1, SW_W, SW_H, DET_BG, DET_SC, sw=1))
shapes.append(lbl("lt-det", SX + 155 + TX, SY1 - 1, "Deterministic", fs=11, fc="#1e1e1e"))
shapes.append(zone("sw-hum", SX + 275, SY1, SW_W, SW_H, HUMAN_BG, HUMAN_SC, sw=1))
shapes.append(lbl("lt-hum", SX + 275 + TX, SY1 - 1, "Human Step", fs=11, fc="#1e1e1e"))
shapes.append(zone("sw-seq", SX + 385, SY1, SW_W, SW_H, "#fff3bf", LOOP_SC, sw=1))
shapes.append(lbl("lt-seq", SX + 385 + TX, SY1 - 1, "Loop flow", fs=11, fc="#1e1e1e"))

shapes.append(zone("sw-red", SX, SY2, SW_W, SW_H, "#ffc9c9", "#e03131", sw=1))
shapes.append(lbl("lt-red", SX + TX, SY2 - 1, "Loop back", fs=11, fc="#1e1e1e"))
shapes.append(zone("sw-grn", SX + 155, SY2, SW_W, SW_H, "#b2f2bb", VER_SC, sw=1))
shapes.append(lbl("lt-grn", SX + 155 + TX, SY2 - 1, "Exit / success", fs=11, fc="#1e1e1e"))
shapes.append(zone("sw-ph", SX + 275, SY2, SW_W, SW_H, "#f3f0ff", PHASE_SC, sw=1))
shapes.append(lbl("lt-ph", SX + 275 + TX, SY2 - 1, "Phase transition", fs=11, fc="#1e1e1e"))

# ════════════════════════════════════════════
# PHASE 1: Spec Discovery
# ════════════════════════════════════════════
P1_Y = 105
P1_H = 100
shapes.append(zone("p1z", LEFT, P1_Y, ZONE_W, P1_H, "#f3f0ff", PHASE_SC))
shapes.append(lbl("p1l", LEFT + 15, P1_Y + 8, "Phase 1: Spec Discovery", fs=17, fc=PHASE_SC))

PM_X  = LEFT + 30;  PM_Y = P1_Y + 30
ARCH_X = PM_X + BW + HGAP;  ARCH_Y = PM_Y

shapes.append(box("pm",   PM_X,   PM_Y, BW, BH, "PM Agent\nGemini Pro", LLM_BG, LLM_SC))
shapes.append(box("arch", ARCH_X, ARCH_Y, BW, BH, "Architect\nGemini Pro", LLM_BG, LLM_SC))
shapes.append(lbl("d-spec", PM_X + BW + 12, PM_Y + 8, "spec", fs=12, fc=DET_SC))

# ════════════════════════════════════════════
# PHASE 2: TDD
# ════════════════════════════════════════════
P2_Y = P1_Y + P1_H + PHASE_GAP
P2_H = 100
shapes.append(zone("p2z", LEFT, P2_Y, ZONE_W, P2_H, "#f3f0ff", PHASE_SC))
shapes.append(lbl("p2l", LEFT + 15, P2_Y + 8,
    "Phase 2: TDD — Write Tests Before Code", fs=17, fc=PHASE_SC))

TW_X = LEFT + 30;  TW_Y = P2_Y + 30
shapes.append(box("tw", TW_X, TW_Y, BW, BH, "TestWriter\nGemini Flash", LLM_BG, LLM_SC))
shapes.append(lbl("tw-reads", TW_X + BW + 15, TW_Y + 5,
    "reads: spec + api_contract", fs=12, fc="#868e96"))
shapes.append(lbl("d-suite", TW_X + BW + 15, TW_Y + 25,
    "output: test_suite", fs=12, fc=DET_SC))

# Inter-phase data labels (positions calculated from box coords)
ROUTE_X_P1P2 = ARCH_X + BW + 25
shapes.append(lbl("d-p1p2", ROUTE_X_P1P2 + 5, ARCH_Y + BH // 2 + 20,
    "api_contract", fs=11, fc=DET_SC))
shapes.append(lbl("d-p2p3", LEFT - 8, TW_Y + BH + 15,
    "test_suite", fs=11, fc=DET_SC))

# ════════════════════════════════════════════
# PHASE 3: Build Loop — TRUE ZIGZAG
#
# Row 1 (L→R): [1.Coder] → [2.CA] → [3.DI] → [4.TR1]
#                                                   |
# Row 2 (R→L): [8.SR] ← [7.KB] ← [6.TR2] ← [5.TF]
#                |
# Row 3:       [9.Gate]
# ════════════════════════════════════════════
P3_Y = P2_Y + P2_H + PHASE_GAP

C1 = LEFT + 40
C2 = C1 + BW + HGAP
C3 = C2 + BW + HGAP
C4 = C3 + BW + HGAP

R1_Y = P3_Y + 42
R2_Y = R1_Y + BH + VGAP
R3_Y = R2_Y + BH + VGAP
GATE_H = 70

LOOP_H = R3_Y + GATE_H + 70 - P3_Y
shapes.append(zone("loopz", LEFT, P3_Y, ZONE_W, LOOP_H, LOOP_BG, LOOP_SC))
shapes.append(lbl("p3l", LEFT + 15, P3_Y + 8,
    "Phase 3: Build Loop (LoopAgent, max 5 iterations)", fs=17, fc=LOOP_SC))

# --- Row 1 (L→R) ---
shapes.append(box("coder", C1, R1_Y, BW, BH,
    "1. Coder\nGemini Pro", LLM_BG, LLM_SC))
shapes.append(box("ca", C2, R1_Y, BW, BH,
    "2. CodeApplier\ncode + secret scan", DET_BG, DET_SC, fs=12))
shapes.append(box("di", C3, R1_Y, BW, BH,
    "3. DepInstaller\ndep security check", DET_BG, DET_SC, fs=12))
shapes.append(box("tr1", C4, R1_Y, BW, BH,
    "4. TestRunner #1\nrun pytest", DET_BG, DET_SC, fs=13))

shapes.append(lbl("d-cc",  C1 + BW + 8, R1_Y + 8, "code_change", fs=11, fc=DET_SC))
shapes.append(lbl("d-af",  C2 + BW + 8, R1_Y + 8, "applied_files", fs=11, fc=DET_SC))
shapes.append(lbl("d-dep", C3 + BW + 8, R1_Y + 8, "dep_installed", fs=11, fc=DET_SC))

# --- Wrap: TR1(C4) ↓ TF(C4) ---
shapes.append(lbl("d-wrap1", C4 + BW + 8, R1_Y + BH + 12, "test_results", fs=11, fc=DET_SC))

# --- Row 2 (R→L): TF(C4) → TR2(C3) → KB(C2) → SR(C1) ---
shapes.append(box("tf",  C4, R2_Y, BW, BH,
    "5. TestFixer\nGemini Pro", LLM_BG, LLM_SC))
shapes.append(box("tr2", C3, R2_Y, BW, BH,
    "6. TestRunner #2\nverify fixes", DET_BG, DET_SC, fs=13))
shapes.append(box("kb",  C2, R2_Y, BW, BH,
    "7. KeepBest\nsnapshot / rollback", DET_BG, DET_SC, fs=12))
shapes.append(box("sr",  C1, R2_Y, BW, BH,
    "8. SpecReviewer\nGemini Pro", LLM_BG, LLM_SC))

shapes.append(lbl("d-fix",  C3 + BW + 8, R2_Y + 8, "test_fix", fs=11, fc=DET_SC))
shapes.append(lbl("d-tr2r", C2 + BW + 8, R2_Y + 8, "test_results", fs=11, fc=DET_SC))
shapes.append(lbl("d-snap", C1 + BW + 8, R2_Y + 8, "snapshot", fs=11, fc=DET_SC))

# --- Row 3: Gate at C1 (leftmost), SR drops straight down ---
shapes.append(box("gate", C1, R3_Y, BW, GATE_H,
    "9. Gate / Circuit Breaker\nfailed==0→EXIT | stall 3x→BREAK\nelse→LOOP",
    DET_BG, DET_SC, fs=11))

# Data label: SR → Gate
shapes.append(lbl("d-review", C1 + BW + 8, R2_Y + BH + 10, "review", fs=11, fc=DET_SC))

# Branching labels next to Gate
shapes.append(lbl("lbl-loop", C1 - 40, R3_Y + 5,
    "else:\nLOOP\nBACK", fs=12, fc="#e03131"))
shapes.append(lbl("lbl-exit", LEFT - 30, R3_Y + GATE_H + 15,
    "failed==0:\nEXIT", fs=12, fc=VER_SC))

# ════════════════════════════════════════════
# PHASE 4: Verification (Human-in-the-Loop)
# ════════════════════════════════════════════
P4_Y = P3_Y + LOOP_H + PHASE_GAP
P4_H = 110
shapes.append(zone("p4z", LEFT, P4_Y, ZONE_W, P4_H, "#e6fcf5", VER_SC))
shapes.append(lbl("p4l", LEFT + 15, P4_Y + 8,
    "Phase 4: Verification (Human-in-the-Loop)", fs=17, fc=VER_SC))

P4_Y_BOX = P4_Y + 35
shapes.append(box("utg", C1, P4_Y_BOX, BW, BH,
    "UserTestGuide\nGemini Flash", LLM_BG, LLM_SC, fs=13))
shapes.append(box("e2e", C2, P4_Y_BOX, BW, BH,
    "E2E-QA\nPlaywright MCP\nGemini Flash", LLM_BG, LLM_SC, fs=11))
shapes.append(box("human", C3, P4_Y_BOX, BW, BH,
    "HUMAN\nManual review\n+ testing", HUMAN_BG, HUMAN_SC, fs=13))
shapes.append(box("fc", C4, P4_Y_BOX, BW, BH,
    "FeedbackClassifier\nGemini Flash", LLM_BG, LLM_SC, fs=12))

shapes.append(lbl("d-utg", C1 + BW + 8, P4_Y_BOX + 8, "test_guide", fs=11, fc=DET_SC))
shapes.append(lbl("d-e2e", C2 + BW + 8, P4_Y_BOX + 8, "e2e_report", fs=11, fc=DET_SC))
shapes.append(lbl("d-hf",  C3 + BW + 8, P4_Y_BOX + 8, "feedback", fs=11, fc=DET_SC))

shapes.append(lbl("fc-note", C1, P4_Y + P4_H + 5,
    "FeedbackClassifier (advisory, pipeline ends):  bug → re-enter loop  |  new_req → update spec  |  ambiguous → clarify",
    fs=12, fc="#868e96"))

# ════════════════════════════════════════════
# EXTERNAL: Deployability
# ════════════════════════════════════════════
DEP_Y = P4_Y + P4_H + 32
shapes.append(zone("depz", LEFT, DEP_Y, ZONE_W, 80, "#f8f9fa", DET_SC, sw=1, ss="dashed"))
shapes.append(lbl("dep-txt", LEFT + 20, DEP_Y + 10,
    "Deployability (external):  Dockerfile (multi-stage) + docker-compose.yml + agents-cli deploy",
    fs=13, fc=DET_SC))
shapes.append(lbl("sum", LEFT + 20, DEP_Y + 42,
    "14 sub-agents: 7 LLM (purple) + 7 deterministic (gray) + 1 human step (blue)",
    fs=14, fc=DET_SC))

# ════════════════════════════════════════════
# CREATE SHAPES
# ════════════════════════════════════════════
res = post("/api/elements/batch", {"elements": shapes})
print(f"Created {len(shapes)} shapes")

# ═══════════════════════════════════════════════════
# ARROWS
# ═══════════════════════════════════════════════════
arrows = []

# --- Phase 1: PM → Arch (bound) ---
arrows.append(arr_bind("a-pm-arch", "pm", "arch", sc=LLM_SC))

# --- Phase 1 → Phase 2: Architect RIGHT edge → down (right side, past titles) → TW RIGHT edge ---
# Route on the right side of the zone to avoid crossing any phase title text
ARCH_RX = ARCH_X + BW        # Architect right edge X = 540
ARCH_RY = ARCH_Y + BH // 2   # Architect right edge midpoint Y
TW_RX   = TW_X + BW          # TW right edge X = 280
TW_RY   = TW_Y + BH // 2     # TW right edge midpoint Y
ROUTE_X = ARCH_RX + 25        # routing column just right of Architect
arrows.append(arr_pts("a-p1-p2", ARCH_RX, ARCH_RY,
    [[0, 0],
     [ROUTE_X - ARCH_RX, 0],                          # right to routing column
     [ROUTE_X - ARCH_RX, TW_RY - ARCH_RY],            # down to TW level
     [TW_RX - ARCH_RX, TW_RY - ARCH_RY]],             # left to TW right edge
    sc=PHASE_SC))

# --- Phase 2 → Phase 3: TW LEFT edge → left margin → down → Coder LEFT edge ---
TW_LX = TW_X;              TW_LY = TW_Y + BH // 2
CODER_LY_MID = R1_Y + BH // 2
P2P3_MARGIN = LEFT - 10
arrows.append(arr_pts("a-p2-p3", TW_LX, TW_LY,
    [[0, 0],
     [P2P3_MARGIN - TW_LX, 0],                           # left to margin
     [P2P3_MARGIN - TW_LX, CODER_LY_MID - TW_LY],       # down to Coder level
     [C1 - TW_LX, CODER_LY_MID - TW_LY]],               # right to Coder left edge
    sc=PHASE_SC))

# --- Build loop Row 1 (L→R) ---
arrows.append(arr_bind("a-c-ca",   "coder", "ca",  sc=LOOP_SC))
arrows.append(arr_bind("a-ca-di",  "ca",    "di",  sc=LOOP_SC))
arrows.append(arr_bind("a-di-tr1", "di",    "tr1", sc=LOOP_SC))

# --- Zigzag wrap: TR1(C4) ↓ TF(C4) ---
arrows.append(arr_pts("a-tr1-tf", C4 + BW // 2, R1_Y + BH,
    [[0, 0], [0, R2_Y - (R1_Y + BH)]],
    sc=LOOP_SC))

# --- Build loop Row 2 (R→L) ---
arrows.append(arr_bind("a-tf-tr2", "tf",  "tr2", sc=LOOP_SC))
arrows.append(arr_bind("a-tr2-kb", "tr2", "kb",  sc=LOOP_SC))
arrows.append(arr_bind("a-kb-sr",  "kb",  "sr",  sc=LOOP_SC))

# --- SR(C1) → Gate(C1): straight down (both at C1) ---
arrows.append(arr_pts("a-sr-gate", C1 + BW // 2, R2_Y + BH,
    [[0, 0], [0, R3_Y - (R2_Y + BH)]],
    sc=LOOP_SC))

# --- LOOP-BACK: Gate LEFT → small left margin → UP → Coder LEFT ---
GATE_LY = R3_Y + GATE_H // 2
CODER_LY = R1_Y + BH // 2
LB_MARGIN = C1 - 25   # left margin for loop-back
arrows.append(arr_pts("loop-back", C1, GATE_LY,
    [[0, 0],
     [LB_MARGIN - C1, 0],                     # left to margin
     [LB_MARGIN - C1, CODER_LY - GATE_LY],    # up to Coder level
     [0, CODER_LY - GATE_LY]],                # right back to C1 (Coder left edge)
    sc="#e03131", sw=3))

# --- EXIT: Gate LEFT edge (lower) → left margin → DOWN → RIGHT → UTG LEFT edge ---
GATE_EXIT_Y = R3_Y + GATE_H - 12   # near bottom of Gate left edge
UTG_LX = C1
UTG_LY = P4_Y_BOX + BH // 2
EXIT_MARGIN = LEFT - 25
arrows.append(arr_pts("exit-arr", C1, GATE_EXIT_Y,
    [[0, 0],
     [EXIT_MARGIN - C1, 0],                            # left to far margin
     [EXIT_MARGIN - C1, UTG_LY - GATE_EXIT_Y],         # down to UTG level
     [UTG_LX - C1, UTG_LY - GATE_EXIT_Y]],             # right to UTG left edge
    sc=VER_SC, sw=3))

# --- Phase 4 (L→R) ---
arrows.append(arr_bind("a-utg-e2e",   "utg",   "e2e",   sc=VER_SC))
arrows.append(arr_bind("a-e2e-human", "e2e",   "human", sc=VER_SC))
arrows.append(arr_bind("a-human-fc",  "human", "fc",    sc=VER_SC))

# ════════════════════════════════════════════
# CREATE ARROWS
# ════════════════════════════════════════════
res = post("/api/elements/batch", {"elements": arrows})
print(f"Created {len(arrows)} arrows")

data = get_json("/api/elements")
els = data.get("elements", data) if isinstance(data, dict) else data
print(f"Total elements on canvas: {len(els)}")
print("Done.")
