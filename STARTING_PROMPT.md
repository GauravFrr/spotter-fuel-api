# Starting prompt for the Antigravity agent
(Paste everything below the line into the agent's first message. Open the project folder as the workspace first, with `AGENT.md`, `context/`, and the two data files already inside.)

---

You are building a backend assessment project for a job application. I'm the developer; the deadline is tight, so I need a small, correct, fast, well-documented result.

**Start by reading, in this order:**
1. `AGENT.md` (your rules and decisions)
2. `context/01_ASSIGNMENT.md` (the exact assignment and requirement checklist)
3. `context/02_DATA_NOTES.md` (what is wrong/missing in the fuel CSV, and how we handle it)
4. `context/03_ARCHITECTURE.md` (design, algorithm, API contract)
5. `context/04_BUILD_PLAN.md` (phases with acceptance criteria)
6. `context/05_DELIVERABLES.md` (README, Postman, Loom, submission)
7. `PROJECT_STRUCTURE.md` (target folder layout)

**Then:**
- Reply with a short summary (max 10 lines) of what you understood, plus any real blockers. Do not restate the docs.
- Create an implementation plan artifact that follows the phases in `context/04_BUILD_PLAN.md`, then start Phase 1 immediately. Don't wait for approval unless something in the docs is contradictory.

**Rules for the whole session:**
- Follow the stack and decisions in `AGENT.md`. No DRF, no extra services.
- Routing API: max one call per request. Start/finish are resolved offline from the bundled US cities table.
- After every phase, run the code and show me real output (test results, a real `curl` response). Never say "should work".
- I could not verify OSRM from my planning environment, so you must test the live OSRM call yourself in Phase 3. If the public server fails or is rate-limited, tell me and propose a fallback instead of silently changing providers.
- Keep commits small. Keep the project small.

**First action:** inspect `data/fuel_prices.csv` and confirm the numbers in `context/02_DATA_NOTES.md` match what you see. If they don't, tell me.
