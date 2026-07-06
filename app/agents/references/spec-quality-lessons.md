# Spec-Quality Lessons — what makes a downstream build loop converge

These lessons come from dogfooding: building a multi-agent dev system and watching where the
spec→test→code loop converged vs. swung (47%↔76% passing) vs. reached green (100%). A vague spec
is the single biggest cause of a build that never converges. Drive the spec to satisfy all four:

## 1. Pin the API contract *precisely* — not just data shapes
Data-shape contracts are necessary but **not sufficient**. The independent test-author and coder
will silently diverge unless you also pin, for every endpoint:
- **Exact success status code** (e.g. `201` for create vs `200` for update — name it).
- **Exact error responses**: status codes *and* the error body/message shape.
- **Auth scheme**: exactly how a request authenticates, and the EXACT response (status + message)
  when auth is missing/invalid.
- **Explicit behavior choices** where two readings exist — pick ONE: e.g. "GET /settings returns 404
  when none exist" **OR** "auto-creates defaults and returns 200", never "either".

> Symptom when skipped: tests assert `200`, code returns `201` → `assert 201 == 200` forever. The
> code isn't wrong; the two agents built to different contracts.

## 2. Require a layered component design (SOLID single-responsibility)
Don't let the implementation become one giant file. Specify the layers and each function's single
responsibility up front: `routes` (thin) → `services` → `crud`/`repository` → `validators` → `schemas`.
Small single-purpose functions are independently testable and far easier to get green.

## 3. Specify a test pyramid, built bottom-up
Unit tests for the low-level functions first (the wide base: validators, crud, services), THEN
API/integration tests on top (the narrow top). A correct foundation makes the API layer fall into place.

## 4. Fix a canonical file layout up front
Declare exact file paths (`backend/schemas.py`, `backend/crud.py`, `tests/unit/...`, `tests/api/...`).
Every downstream step then edits the **same** files instead of inventing new names each pass — which
otherwise causes duplicate-file pollution (e.g. `main.py` *and* `backend/main.py`, three copies of a
test) that corrupts test collection and prevents convergence.

---

**Net:** contract precision (1) + layering (2) + test pyramid (3) + canonical layout (4) are what move
a build loop from "swinging and stuck" to "monotonic climb to green." Capture all four during discovery.
