# Demo Video — Frame-by-Frame Script

**Target length:** 5:00 · **Narration:** ~640 words (comfortable reading pace)
**Track:** Agents for Business · **Deadline:** submit before Jul 6, 11:59 PM PT

---

## Footage inventory (Game Bar filenames = recording *end* times)

| File | Real time span | Length | Content |
|------|----------------|--------|---------|
| `...201554.mp4` | ~20:13–20:15 | 2:11 | First pipeline attempt — usable as a 3s "failure montage" flash |
| `...210152.mp4` | ~20:41–21:01 | 20:10 | **Full PM discovery interview** — best interactive footage |
| `...211513 / 211657 / 211933.mp4` | 21:13–21:19 | ~2:40 | Restart message → PM echoes spec → Architect starts |
| `...212736.mp4` | ~21:23–21:27 | 4:32 | TestWriter / Coder working |
| `...215842.mp4` | ~21:38–21:58 | 19:56 | **Build loop with live agent log — `tests passed: 30` moment at ≈ 15:11** |

## Shots still to record (~15 min)

| Shot | Content | How |
|------|---------|-----|
| **A** (~60s) | Import cascade: ✅ TRACKED / 🔁 MERGED / 🚫 REJECTED | Delete `demo-output/test.db` → start server → run `docs/demo/import_fixture.py` in a maximized terminal |
| **B** (~30s) | Swagger dashboard | `http://127.0.0.1:8001/docs` → Authorize (paste the demo JWT) → `GET /api/jobs` → Execute → scroll response |
| **C** (~15s) | Green suite | In `demo-output`: `./.venv/Scripts/python.exe -m pytest tests -q` → freeze on **`40 passed`** |
| **D** (optional, ~20s) | Antigravity cameo | Any clip of Antigravity in the workflow → upgrades coverage to 6/6 course concepts |

Server start: `cd demo-output && ./.venv/Scripts/python.exe -m uvicorn backend.main:app --port 8001`
Record A → B → C in one session so Shot B's dashboard shows Shot A's data.

---

## Scene-by-scene script

### Scene 1 — Hook & problem · 0:00–0:25
**Visual:** Title card → slow zoom on architecture PNG
> "Millions of people have software ideas but can't build them. AI coding assistants don't fix this — they hand non-engineers a wall of untested code. What these users need isn't an assistant. It's a team. So we built one: Agent Dev Team — fourteen specialized agents on Google's ADK that turn a plain-English conversation into a tested, security-scanned application."

### Scene 2 — Why agents · 0:25–0:50
**Visual:** Agent-roles table card
> "Why multiple agents? Because a real team's power is separation of duties. Our TestWriter and Coder never see each other's reasoning — both bind to a contract written by the Architect. Tests stay adversarial. An LLM judging its own code says 'done' too early; our done-signal is pytest, not opinion."

### Scene 3 — Architecture · 0:50–1:30
**Visual:** `docs/diagrams/agent-system-final.png`, highlight each phase in turn
> "Four phases. A PM agent interviews the user and won't let ambiguity through. The Architect turns the spec into a binding contract — exact status codes, exact error shapes. Tests are written *before* code. Then the build loop: code, security-scan, install, test, fix, snapshot — with a circuit breaker if progress stalls. Finally, human-in-the-loop verification with a plain-language test guide and Playwright browser QA."

### Scene 4 — The convergence journey · 1:30–2:00
**Visual:** `docs/diagrams/convergence-journey.png`, left panel
> "Convergence was earned, not free. Our first version oscillated between 47 and 76 percent passing, forever. Contract-first design, canonical file layout, and keep-best snapshots fixed it: our Study Tracker app converged to fifty-nine out of fifty-nine tests — fully autonomously."

### Scene 5 — Live build: the interview · 2:00–2:35
**Visual:** Interview footage (`210152`, two Q&A exchanges at 2× speed) + the "interview in progress" gate bubble
> "Here's the system building a second app, live: Job Radar, for my own job search. The PM interviews me in plain language — and notice: the build pipeline is gated; it cannot start until the spec is confirmed. That's a deterministic guard, not a prompt suggestion."

### Scene 6 — Live build: the team at work · 2:35–3:10
**Visual:** Build-loop footage (`215842`), live log window prominent; **freeze at ≈15:11 on `tests passed: 30, failed: 10`** with caption overlay
> "Then the team takes over. The live log shows exactly which agent is working — coder, applier, test runner — full traceability. Watch the test count climb… thirty of forty passing, autonomously. The session state recorded a peak of thirty-one."

### Scene 7 — The product · 3:10–3:50
**Visual:** Shot A (import cascade) → Shot B (Swagger dashboard) → Shot C (`40 passed`)
> "The finished product: I feed it fourteen job postings collected from Reddit and career pages. It tracks nine, merges two duplicates found on different sites, and rejects three that aren't target roles. The dashboard sorts by deadline, flags stale applications, and shows my funnel. Final suite: forty out of forty green."

### Scene 8 — Security & transparency · 3:50–4:25
**Visual:** `docs/diagrams/security-guardrails.png` → journey chart right panel (dashed segment)
> "Security is the differentiator: nothing an LLM writes touches disk without passing a code scanner, a secret scanner, and live PyPI verification against hallucinated packages. And full transparency: this hackathon provided no credits — after sixty dollars of self-funded API usage, our credits ran out at thirty-one of forty, and a human finished the last mile against the frozen agent-written tests. That handoff isn't a failure; it's Phase four of the architecture, working as designed."

### Scene 9 — Wrap · 4:25–5:00
**Visual:** Repo/README scroll → closing card with links (insert optional Shot D just before)
> "Everything is open: the pipeline, six guardrail modules with thirty-three tests, the eval suite, Docker deployment, and the full journey documented — including what broke. Agent Dev Team: not a coding assistant. A team. Links below."

---

## Division of labor

**Debby**
1. Record Shots A / B / C (+ D if Antigravity material exists) into `C:\Users\Debby\Videos\Screen Recordings`
2. Record narration — one audio file per scene, reading the quotes above (phone voice memo is fine) — **or** say the word and we go captions-only with music
3. Review the rough cut → upload to YouTube (public) → attach to the Kaggle writeup

**Claude**
1. Title / section / closing cards + cover image for the Kaggle writeup
2. Cut all segments to the timeline (speed-ramps, the 30/40 freeze-frame with caption)
3. Burn in captions (essential for judges who skim), assemble with ffmpeg into a 1080p master
4. Sync narration when delivered

**Trigger:** drop the new files in the recordings folder and say go — rough cut comes back in one pass.
