# Architecture Diagram Requirements — Ground Truth

## Architecture Accuracy

14 sub-agents + 1 human step. Every one gets its own box.

### Phase 1: Spec Discovery
- PM Agent (Gemini Pro) → output: `spec`
- Architect (Gemini Pro) → output: `api_contract` — consumes: `spec`

### Phase 2: TDD — Write Tests Before Code
- TestWriter (Gemini Flash) → output: `test_suite` — consumes: `spec` + `api_contract`

### Phase 3: Build Loop (LoopAgent, max 5 iterations)
Sequential within each iteration:
1. Coder (Gemini Pro) → output: `code_change` — consumes: `spec` + `api_contract` + `test_suite` + `test_results`
2. CodeApplier [deterministic] — runs code_scanner + secret_scanner, writes files (security behavior, annotate in box text)
3. DepInstaller [deterministic] — dependency_checker (slopsquatting), installs deps (security behavior, annotate in box text)
4. TestRunner 1st run [deterministic] — runs pytest on new code → output: `test_results`
5. TestFixer (Gemini Pro) — repairs broken test syntax/imports → output: `test_fix`
6. TestRunner 2nd run [deterministic] — re-runs pytest to verify fixes → output: `test_results`
7. KeepBest [deterministic] — snapshots best code or rolls back regression
8. SpecReviewer (Gemini Pro) — reviews code vs contract → output: `review`
9. Gate / Circuit Breaker [deterministic]:
   - `failed == 0` → EXIT (success)
   - stall 3 consecutive iterations → BREAK (save resources)
   - else → LOOP BACK to Coder (step 1)

### Phase 4: Verification (Human-in-the-Loop)
- UserTestGuide (Gemini Flash) → output: `user_test_guide`
- E2E-QA (Gemini Flash + Playwright MCP) → output: `e2e_report`
- HUMAN — manual review + testing
- FeedbackClassifier (Gemini Flash) → output: `feedback_classification` (advisory only, pipeline ends)

### External (not in pipeline)
- Deployability: Dockerfile (multi-stage) + docker-compose.yml + agents-cli deploy

## Visual Requirements

### Color Coding — 3 categories only
- **Purple** (`#d0bfff` / `#7048e8`): LLM Agent — calls Gemini model
- **Gray** (`#dee2e6` / `#495057`): Deterministic Agent — no LLM, programmatic logic (includes CodeApplier, DepInstaller, TestRunner, KeepBest, Gate)
- **Blue** (`#a5d8ff` / `#1971c2`): Human step

Security scanning is a *behavior* of CodeApplier and DepInstaller, not a separate agent type. Annotate it as text inside the gray box (e.g., "CodeApplier\nsecurity: code_scan + secret_scan"). Do NOT use a separate color for security.

### Arrow Content — 2 types

#### Type 1: Data Flow (on every sequential arrow)
Shows what data is passed downstream. Label sits near the arrow, between the two boxes.
Examples: `spec`, `api_contract`, `test_suite`, `code_change`, `test_results`, `review`

#### Type 2: Branching Condition (on decision/routing arrows)
Shows the condition that determines which path is taken. Used at Gate and FeedbackClassifier.
Format: condition → destination
Examples:
- Gate: `failed==0` → EXIT, `stall 3x` → BREAK, `else` → LOOP BACK
- FeedbackClassifier: `bug` → re-enter loop, `new_req` → update spec (advisory)

Both types must be present. Never skip labels on any arrow.

### Alignment — Consistent across phases

#### Phase zone alignment
- All phase zones left-align at the same X coordinate
- All phase zones have the same width (or proportionally justified)
- Phase title labels all positioned consistently (e.g., top-left inside zone)

#### Phase-to-phase arrows
- Always connect from the bottom-center of the last agent in the previous phase to the top-center of the first agent in the next phase
- Arrow style is consistent (same stroke width, same color family)

#### Within a phase
- Agent boxes in the same row are top-aligned (same Y)
- Agent boxes have consistent width within each phase
- Horizontal gaps between boxes in the same row are equal

### Layout Rules
- No long arrows spanning the entire screen horizontally or vertically
- Blocks should be distributed reasonably — not cramped, not too spread out
- The loop must be visually clear: you can immediately see where the loop goes back
- Arrows can go left→right or right→left, but the loop concept must be obvious
- No overlapping text, boxes, or arrows — zero tolerance
- Minimum 40px gap between any two elements
- Font size >= 14 for agent labels, >= 16 for phase titles
- Data flow labels: font size >= 11, positioned in the gap between boxes (not on top of arrows)

### Loop Visualization
- The build loop zone must clearly show the loop-back path from Gate → Coder
- The exit path from Gate → Phase 4 must be clearly different from the loop-back path
- Both paths must be labeled with their branching condition
- Loop-back arrow should be visually distinct (e.g., thicker, different color like red)
- Exit arrow should be visually distinct (e.g., green)

### Export
- Save as PNG only (not .excalidraw)
- Final output: `docs/diagrams/agent-system-final.png`

## Verification Checklist
After each iteration, check ALL of these:
1. [ ] All 15 boxes visible (14 agents + 1 human)?
2. [ ] Color coding correct? Only 3 colors: purple (LLM), gray (deterministic), blue (human)?
3. [ ] All data flow labels (Type 1) present on every sequential arrow?
4. [ ] Branching conditions (Type 2) labeled on Gate and FeedbackClassifier arrows?
5. [ ] No overlapping text, boxes, or arrows?
6. [ ] Loop-back arrow clearly visible from Gate → Coder, labeled with condition?
7. [ ] Exit arrow clearly visible from Gate → Phase 4, labeled with condition?
8. [ ] No arrows spanning the full width or height of the canvas?
9. [ ] All text readable (not too small, not truncated)?
10. [ ] Phase zones aligned consistently (same left X, same width)?
11. [ ] Phase-to-phase arrows consistent in style and alignment?
12. [ ] Agent boxes within each row are top-aligned with equal gaps?
13. [ ] Deployability annotation present?
