# Universal AI Guidelines & Engineering Principles

> **PORTABLE SPECIFICATION FOR ALL FUTURE PROJECTS & REPOSITORIES**
> Drop this file into any repository root (as `AGENTS.md`, `CLAUDE.md`, or `.cursorrules`) to immediately empower any AI coding assistant to operate with maximum autonomy, quality, crash resilience, and self-testing capability.

---

## 🏛️ Core Principles

### PRINCIPLE-001: RLM Compatibility & Hierarchical Decomposition
- Large datasets, directory structures, and complex reasoning must be decomposed hierarchically with bounded contexts rather than dumped into monolithic flat contexts.

### PRINCIPLE-002: Automatic Git Workflow (Commit & Push)
- After completing any logical, verified milestone, the AI must automatically stage, commit using Conventional Commits (`feat`, `fix`, `refactor`, `docs`, `chore`), and push to the remote repository.

### PRINCIPLE-003: Modularity & Pluggable Architecture
- Decouple user interface, orchestration, and business logic. Adhere strictly to the Single Responsibility Principle with pluggable provider/strategy abstractions.

### PRINCIPLE-004: Living Principles System & Automated Governance
- When principles evolve, all AI guideline targets across the repository must be automatically synchronized to maintain 100% consistency.

### PRINCIPLE-005: AI Cold-Start Readiness & Living Documentation (README Sync)
- The repository must be permanently self-describing for a cold-starting AI or developer. Keep `README.md` continuously synchronized with the latest features, run commands, and architecture.

### PRINCIPLE-006: Pre-flight Impact & Quality Checklist (Cold-Start Gate)
- Evaluate necessity, user benefits, potential regressions, and quality standards before making modifications.

### PRINCIPLE-007: Performance & Lean Resource Optimization
- Optimize for execution speed, low latency, $O(N)$ algorithmic complexity, non-blocking asynchronous execution, and minimal dependency footprint.

### PRINCIPLE-008: Zero-Friction Onboarding & Hybrid Access (One-Click Start)
- Applications must be instantly usable out-of-the-box without requiring mandatory heavy external desktop setups, while retaining first-class support for self-hosted local power users.

### PRINCIPLE-009: Token Frugality & Lean Code Architecture (Context Budgeting)
- Keep implementations concise, avoid boilerplate bloat, budget LLM context windows strictly, and leverage compact serializations.

### PRINCIPLE-010: AI Knowledge Base & Continuous Codebase Mapping
- Maintain an active modular architectural knowledge base in `knowledge/` and update it whenever data models, APIs, or architectural boundaries shift.

### PRINCIPLE-011: Automated Test Verification & Continuous Coverage (Regression Shield)
- All new features and bug fixes must include isolated unit/integration tests. The test suite must pass with 100% success before staging changes.

### PRINCIPLE-012: Crash Resilience, State Atomicity & Power-Loss Recovery
- All persistent configuration, cache, and state files must be written via atomic temporary buffers with flush + `fsync` + atomic replacement (`os.replace`). Self-heal and isolate corrupted state gracefully.

### PRINCIPLE-013: Incremental Progress Checkpointing & Disruption Recovery
- Persist in-flight refactoring state to a disruption ledger (`.agents/task_ledger.json`). Commit working sub-tasks atomically to prevent progress loss upon power cuts or process terminations.

### PRINCIPLE-014: Empirical Grounding & Anti-Hallucination Invariant (Verify-Before-Execution)
- Never assume symbols, signatures, paths, or capabilities. Always read and verify existing codebase reality on disk before writing or editing code.

### PRINCIPLE-015: Attentional Drift Prevention & Compaction Resilience (Context Anchor Protocol)
- Externalize multi-step plans and decisions to persistent disk artifacts. Re-anchor to checklists and disk ground truth after conversation compaction or cold resumption.

### PRINCIPLE-016: Universal Operational Dogfooding & Chaos Verification (The AI Must Use What It Builds)
- **Concept**: A task is never complete simply because code compiles or unit tests pass. Before shipping any feature or refactor, the AI must actively execute, drive, and "live inside" the software it creates—simulating real human interaction, chaotic user behavior, and dirty external data while maintaining strict token frugality.
- **Rules Across All Stacks**:
  1. **Domain-Specific Interactive Dogfooding**:
     - *Desktop GUI*: Spawns the live window in-process, pumps the event loop, invokes buttons, traverses tabs, stress-tests mid-operation window destruction, and mechanically traps unhandled callback exceptions (e.g., `_tkinter.TclError`).
     - *Web Apps*: Launches the local dev server, uses browser/headless tools to interact with DOM elements, verifies forms and routing, and asserts zero console errors (`console.error`).
     - *CLI Applications*: Executes the binary in subshells with arguments, pipes stdin/stdout, tests interrupt signals (SIGINT), and verifies exit codes and error formatting.
     - *Backend APIs*: Boots the service, executes real HTTP requests with test clients, and asserts status codes and response contracts.
  2. **Zero-Token Chaos Fuzzing & Error Sanitization**: Test API parsing and resilience against malformed or non-deterministic outputs (integers, markdown codeblocks, truncated payloads, 429 rate limits, 504 timeouts) using deterministic offline chaos mocks at zero API token cost.
  3. **Micro-Canary Live Budgeting**: When testing against live cloud APIs or local model endpoints, strictly budget test runs to a maximum of 2 micro-files and `<150` prompt tokens. Never dump raw unbounded directory paths into live test prompts.
  4. **Terse Context Reporting**: Dogfood runner outputs in terminal/chat must be dense status dashboards (<10 lines). Verbose diagnostics and stack traces must be externalized to persistent disk logs (`.agents/dogfood_last_run.log`) to prevent conversational attentional drift and context compaction.
  5. **Pre-Ship Dogfooding Gate**: The interactive dogfooding suite must be executed and confirmed passing with 100% success alongside standard unit tests before staging changes.
  6. **Zero-Blast-Radius & Ephemeral Sandboxing (Safety Jail)**: Dogfooding must NEVER touch, scan, or mutate real user directories (Desktop, Documents, personal folders, or system files). All operational tests must run strictly inside ephemeral, isolated temporary sandboxes populated exclusively with synthetic test files, guarded by strict containment assertions, and wiped clean upon test completion.

