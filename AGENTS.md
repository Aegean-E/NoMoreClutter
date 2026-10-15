# AI Assistant Guidelines & Project Principles

> **MANDATORY INSTRUCTION FOR ALL AI AGENTS & CODING ASSISTANTS:**
> You must strictly read, respect, and enforce all principles in this document when planning, implementing, reviewing, or refactoring code in this repository.

---

## 🏛️ Core Principles

### PRINCIPLE-001: RLM Compatibility (Recursive Language Model)
- **Concept**: The system must be built for Recursive Language Model processing. File organization and semantic categorization must support recursive decomposition rather than monolithic, flat-batch prompting.
- **Rules**:
  1. **Hierarchical Decomposition**: Large directory trees or deep file sets must be partitioned hierarchically (e.g., Root Domain $\rightarrow$ Category $\rightarrow$ Sub-category $\rightarrow$ File Rename & Action).
  2. **Bounded Context**: Never feed unbounded flat file lists into a single prompt. Decompose into recursive sub-tasks with well-defined base cases and max-depth limits.
  3. **Recursive Validation & Refinement**: Support recursive self-validation where an LLM checks and refines ambiguous categories or classifications.
  4. **State Propagation**: Child recursive steps must receive scoped context from parent decisions and return structured nodes back up the tree.

---

### PRINCIPLE-002: Automatic Git Workflow (Commit & Push)
- **Concept**: AI must maintain an active, clean, and reliable Git trail without requiring manual commit reminders from the user.
- **Rules**:
  1. **Automatic Commits**: After completing any meaningful task, feature implementation, refactoring, or documentation update, the AI must automatically stage and commit the changes.
  2. **Conventional Commits**: Commit messages must follow the Conventional Commits format (`feat(...)`, `fix(...)`, `refactor(...)`, `docs(...)`, `chore(...)`) with clear, descriptive explanations.
  3. **Automatic Push**: After committing, the AI must automatically push the commit to the active remote branch (`origin/main` or current working branch) and confirm the commit hash to the user.
  4. **Integrity Check**: Before committing, ensure the code builds/runs and no temporary or unwanted files are staged.

---

### PRINCIPLE-003: Modularity & Pluggable Architecture
- **Concept**: Every major component must be modular, decoupled, and adhere to the Single Responsibility Principle.
- **Rules**:
  1. **Pluggable AI Providers**: The AI service must use an abstract provider interface. It must support:
     - **Cloud AI (Zero-install)**: e.g., Groq, Google Gemini, OpenAI, OpenRouter.
     - **Embedded Local (In-process)**: e.g., lightweight GGUF / local inference without external desktop apps.
     - **Local Server**: e.g., LM Studio, Ollama.
  2. **Decoupled Business Logic**: The UI (`main.py`) must only handle presentation and user interactions. Business logic (scanning, RLM planning, file execution, undo management) must live strictly in modular `services/` and `models/`.
  3. **Extensibility**: Adding a new file type, provider, or organization strategy must require minimal changes and zero breaking changes to existing modules.

---

### PRINCIPLE-004: Living Principles System (Extensible Governance & Auto-Sync)
- **Concept**: Principles can and will be added as the project evolves. Whenever any principle is added, updated, or revised, all AI guideline documents across the repository must be automatically synchronized to maintain absolute consistency.
- **Rules**:
  1. **Canonical Schema**: Any new principle must follow the standard schema:
     - `PRINCIPLE-XXX: [Title]`
     - **Concept**: High-level explanation.
     - **Rules**: Concrete, testable requirements.
  2. **Automated Cross-AI Synchronization**: Whenever principles change, the AI MUST immediately update all guideline targets across the repository:
     - `AGENTS.md` (Master AI specification)
     - `GUIDELINES.md` (Human and architectural reference)
     - `GEMINI.md` (Gemini & Antigravity IDE)
     - `.agents/rules/principles.md` (Antigravity workspace rules)
     - `CLAUDE.md` (Anthropic Claude Code)
     - `.cursorrules` (Cursor IDE)
     - `.github/copilot-instructions.md` (GitHub Copilot)
     - `README.md` (Public documentation)
  3. **Automated Sync Tooling**: Maintain a synchronization script (`scripts/sync_principles.py`) to programmatically validate and propagate principle updates across all targets.
  4. **Forward Compatibility**: When new principles are introduced, existing code should be audited and adapted incrementally to maintain compliance.

---

### PRINCIPLE-005: AI Cold-Start Readiness & Living Documentation (README Sync)
- **Concept**: The repository must be permanently prepared for a "cold start" by any AI assistant or developer. Any new agent entering the project with zero prior conversational history must immediately understand the project state, run commands, architecture, and principles. To prevent knowledge drift, `README.md` must be systematically updated after every meaningful change.
- **Rules**:
  1. **Self-Describing Repository**: Every architectural decision, file structure, command, and configuration option must be documented explicitly in `README.md`, `GUIDELINES.md`, and code docstrings. No hidden or implicit assumptions are allowed.
  2. **Mandatory README Update After Every Change**: After completing any feature, UI update, configuration change, refactoring, or architectural modification, the AI must immediately update `README.md` to reflect the new state.
  3. **Zero-Ambiguity Quickstart**: The setup and run instructions in `README.md` must always remain functional and up to date for a cold-starting AI or user.

---

### PRINCIPLE-006: Pre-flight Impact & Quality Checklist (Cold-Start Gate)
- **Concept**: Before implementing code modifications, refactorings, or architecture changes—especially upon a cold start—the AI must evaluate a structured pre-flight impact checklist. This assessment ensures the AI clarifies the *why*, maximizes project *benefits*, preemptively identifies potential *harm/regressions*, and proactively guards quality.
- **Rules**:
  1. **Mandatory Cold-Start Assessment**:
     - **Why is this required?**: Articulate the exact user goal, pain point, or architectural gap being solved.
     - **How does it benefit the project?**: Identify concrete improvements to user experience, performance, RLM compatibility, or modularity.
     - **How could it harm the project?**: Preemptively analyze potential downsides (e.g., breaking changes, performance drops, API rate limit exposure, thread blocking, UI freezes, or complexity bloat).
     - **Mitigation Plan**: Implement defensive designs to neutralize identified risks before applying changes.
  2. **Quality Non-Diminution**:
     - Principles and checklists must **never** be used as an excuse to deliver substandard, crippled, or lazy implementations.
     - All code must maintain high visual polish, complete type safety, robust exception handling, and non-blocking asynchronous execution where applicable.
  3. **Continuous Enforcement**:
     - Run the pre-flight checklist mentally or in scratch plans at every cold start.
     - Complete all items in the task checklist before marking work finished.

---

### PRINCIPLE-007: Performance & Resource Optimization (Speed & Lean Architecture)
- **Concept**: Every code change, architectural modification, and dependency choice must be optimized for execution speed, low latency, optimal algorithmic complexity, and lean resource utilization (CPU, memory, disk I/O, and LLM token budget).
- **Rules**:
  1. **Algorithmic & I/O Efficiency**: All scanning, filtering, and path transformations must employ optimal algorithmic complexity ($O(N)$ scanning, set lookups, generator pipelines, buffered file operations).
  2. **Non-Blocking & Asynchronous Execution**: Heavy operations (file system walks, batch moves, network/LLM calls) must execute asynchronously or in worker threads, never blocking the UI or main event loop.
  3. **Lean Dependency Footprint**: Avoid introducing bloated, heavy third-party packages when standard library or lightweight modules suffice. Utilize lazy loading for heavy dependencies.
  4. **Token & Network Frugality**: LLM prompts, batch sizes, and recursive trees must be budgeted to minimize latency, token consumption, and API costs while preserving reasoning accuracy.
  5. **No Brittle Premature Hacks**: Optimization must remain readable, maintainable, modular (**PRINCIPLE-003**), and strictly tested.

---

### PRINCIPLE-008: Zero-Friction Onboarding & Hybrid AI Access (One-Click Start)
- **Concept**: The application must be instantly usable out of the box ("one-click and start") without forcing users to download, install, or configure heavy external desktop applications (like LM Studio or Ollama). At the same time, the system must retain first-class support for local self-hosted servers (Ollama, LM Studio) for users who demand total local control.
- **Rules**:
  1. **Zero Mandatory External Installations**: Never force users to install third-party desktop software to experience core AI organization. Offer immediate cloud pathways (e.g., free-tier Groq, Google Gemini, OpenAI) and intelligent heuristic fallbacks.
  2. **Preserve Local Power-User Freedom**: First-class support for Ollama, LM Studio, and custom local endpoints must remain intact, prominent, and easily selectable.
  3. **One-Click Provider Switching**: A unified provider dropdown in the UI allows instant switching between cloud zero-install providers and local servers, with prepopulated URLs and model recommendations.
  4. **Graceful Degradation**: If an AI provider is unreachable or unconfigured, the app must guide the user with clear instructions rather than crashing or freezing.

---

### PRINCIPLE-009: Token Frugality & Lean Code Architecture (Context Budgeting)
- **Concept**: Code must be concise, expressive, and devoid of unnecessary bloat. All interactions with LLMs must be strictly budgeted for tokens—leveraging RLM decomposition, compact representations, and hierarchical batching so requests never exhaust context windows, exceed rate limits (TPM), or waste user tokens.
- **Rules**:
  1. **Concise, High-Leverage Code**: Avoid gratuitous verbosity, bloated helper chains, or repetitive boilerplate. Write clean, modular, and concise implementations.
  2. **Strict Token Budgeting**: Prompts must never blindly dump raw, unbounded file lists into a single context. Enforce strict batch size caps and character limits.
  3. **Compact Serialization**: Use dense, compact payload formats (e.g., relative filenames instead of repeated multi-line absolute paths, terse JSON schemas) to cut prompt token consumption by 50–70%.
  4. **RLM Hierarchical Workarounds**: For large directories, partition files into small conceptual clusters before prompting. Resolve categorization recursively at the cluster level rather than prompting file-by-file when unnecessary.
  5. **Rate-Limit & TPM Guardrails**: Implement token-aware pacing and exponential backoff to seamlessly operate within free-tier limits (e.g., Groq's TPM caps).

---

### PRINCIPLE-010: AI Knowledge Base & Continuous Synchronization
- **Concept**: The repository must maintain an active, structured, and modular codebase knowledge base in `knowledge/`. Every AI assistant interacting with this codebase must consult the knowledge base for deep architectural context and systematically update it after any architectural, service, model, or UI change to eliminate knowledge drift.
- **Rules**:
  1. **Canonical Structure**: The knowledge base must reside in `knowledge/` with modular documentation (`INDEX.md`, `architecture.md`, `services.md`, `data_models.md`, `state_and_ui.md`, `decisions.md`, and `codebase_map.md`).
  2. **Mandatory Sync After Every Change**: Whenever classes, functions, architectural boundaries, or data models are added, modified, or refactored, the relevant knowledge base files must be updated immediately in the same task.
  3. **Automated Verification**: Run `python scripts/update_knowledge_base.py` to inspect the codebase AST, regenerate `knowledge/codebase_map.md`, and verify documentation completeness.
  4. **Cold-Start Acceleration**: A cold-starting AI assistant can read `knowledge/INDEX.md` to achieve comprehensive structural understanding without blind codebase searches.

---

### PRINCIPLE-011: Automated Test Verification & Continuous Test Coverage (Regression Shield)
- **Concept**: Every code modification, new feature, bug fix, or refactoring must be accompanied by automated unit or integration tests wherever technically feasible. Before finalizing any task, the full automated test suite must be executed and confirmed passing to guarantee zero regressions.
- **Rules**:
  1. **Test-Backed Changes**: Any new feature, service method, model, or bug fix must include dedicated unit tests in `tests/`.
  2. **Zero-Regression Gate**: The complete test suite (`python -m unittest discover tests`) must be executed and pass with 100% success before staging and committing.
  3. **Deterministic & Fast Tests**: Tests must be fully automated, fast (<1s), isolated, independent of external network APIs (using mocks/fakes where necessary), and clean up all temporary filesystem artifacts.
  4. **Continuous Test Expansion**: As the codebase evolves, edge cases, error conditions, and cross-platform path handling must be incrementally added to the test suite to fortify test coverage.
  5. **Pre-flight & Post-flight Integration**: The Pre-flight checklist must plan test coverage, and the Post-flight checklist must verify that all tests pass.

---

### PRINCIPLE-012: Crash Resilience, State Atomicity & Power-Loss Recovery (Fail-Safe Operations)
- **Concept**: The application must remain fail-safe and self-healing against abrupt disruptions—such as sudden power outages, battery exhaustion, OS crashes, or external process termination. User files, application settings, and undo transaction logs must never be left in a corrupted, half-written, or unrecoverable state due to unexpected power loss.
- **Rules**:
  1. **Atomic State & Configuration Persistence**: All persistent JSON state (`settings.json`, `history.json`, cache files) must be written via atomic temporary files with buffer flushing (`flush` + `os.fsync`) followed by atomic replacement (`os.replace`). Direct in-place truncation writes that risk 0-byte files on power cut are strictly prohibited.
  2. **Incremental Transaction Journaling (WAL)**: File movement and rename batches must record moves incrementally into persistent storage as each file is safely relocated, guaranteeing that an interrupted batch leaves an accurate, reversible trail up to the exact moment of failure.
  3. **Startup Self-Healing & Crash Tolerance**: On startup, if any persistent state file is detected to be damaged or malformed from an unclean shutdown, the application must automatically isolate the corrupted artifact, recover from backup or safe defaults, and report the event cleanly rather than crashing.
  4. **Non-Destructive File Guarantees**: Move operations must prioritize file retention over speed. Critical paths must verify target presence before source unlinking, and existing destination files must never be overwritten on collision.
  5. **Continuous Recovery Verification**: Automated tests must validate crash recovery behaviors, ensuring corrupted JSON, partial transactions, and unclean shutdowns are handled gracefully without application panic.

---

### PRINCIPLE-013: Incremental Progress Checkpointing & Disruption Recovery (Zero-Progress-Loss Workflow)
- **Concept**: Development workflows and AI execution sessions must be resilient against abrupt disruptions—such as sudden power outages, battery depletion, OS crashes, or process termination. Progress must never be treated as an all-or-nothing end-of-turn artifact; it must be recorded through incremental, atomic micro-checkpoints, persistent task ledgers, and immediate cold-start recovery protocols to guarantee zero work loss without compromising code quality.
- **Rules**:
  1. **Micro-Milestone Atomicity & Verified Commits**: For multi-step tasks or non-trivial implementations, the AI must checkpoint and commit working state incrementally after each logical, verified sub-task (e.g., service logic $\rightarrow$ verified commit; UI component $\rightarrow$ verified commit; docs/tests $\rightarrow$ verified commit) rather than accumulating large, vulnerable working-tree states that risk total loss upon power cut.
  2. **Pre-flight Disruption Audit on Cold Start**: Upon every cold start or conversation resumption, before beginning any new coding task, the AI must immediately audit the working tree (`git status`, uncommitted changes, untracked files, temp artifacts) to detect, preserve, and recover any uncommitted progress interrupted by an unclean shutdown.
  3. **Atomic File Write Integrity**: All script, source, and guideline modifications must be written atomically to disk via temporary buffers and atomic replacements (`os.replace`), ensuring that an abrupt power cut during a write operation never leaves 0-byte or corrupted source files.
  4. **Non-Breaking Micro-Checkpoints**: Every incremental commit must leave the repository in a stable, syntactically valid state with passing unit tests (`PRINCIPLE-011`), never committing broken or half-implemented code to the active branch.
  5. **Disruption Ledger & Resumption Protocol**: Interrupted tasks, ongoing refactors, and multi-step plans must be persisted to a local disruption ledger (`.agents/task_ledger.json`) so any incoming AI assistant or developer can immediately determine the exact point of interruption, review surviving files, and resume execution with zero duplicate effort.

---

### PRINCIPLE-014: Empirical Grounding & Anti-Hallucination Invariant (Verify-Before-Execution)
- **Concept**: The AI must operate under strict empirical grounding. An agent must never make assumptions about codebase state, API contracts, imported symbols, or data contents without empirically verifying them against disk first. Intuitive guesses, phantom imports, and ungrounded hallucinations are strictly prohibited.
- **Rules**:
  1. **Read-Before-Write Invariant**: Never edit a file, call an internal function, or instantiate a class without first reading or grepping its definition and signature from the local codebase.
  2. **Empirical Fact-Checking**: When referencing file paths, configuration keys, or third-party capabilities, verify their presence on disk or in the active runtime environment rather than presuming they exist.
  3. **Zero Assumption on Ambiguity**: When data or intent is ambiguous, fall back to safe deterministic patterns (e.g., date-based albums for photos, explicit exceptions for unsupported features) rather than guessing arbitrary categories or hallucinating contents.
  4. **Automated AST & Test Gating**: Rely on deterministic verification tools (`scripts/update_knowledge_base.py`, compiler/linter checks, and unit tests) to mechanically catch hallucinations before committing.

---

### PRINCIPLE-015: Attentional Drift Prevention & Compaction Resilience (Context Anchor Protocol)
- **Concept**: In long-running sessions, large contexts induce attentional drift (the AI forgetting rules, skipping checklists, or losing constraints) and conversation compaction discards transient conversational context. To remain permanently immune to amnesia, all critical task state must be externalized to persistent disk artifacts, and the agent must continuously re-anchor against the repository's ground truth.
- **Rules**:
  1. **Externalized Working Memory**: Never store task status, multi-step plans, or architectural decisions solely in transient conversation turns. Persist them immediately to structured artifacts (`.agents/task_ledger.json`, `knowledge/decisions.md`, or working scratch files).
  2. **Continuous Checklist Re-anchoring**: At the beginning of each turn and after any compaction event, the AI must actively re-anchor to the Pre-flight/Post-flight checklist and active principles rather than relying on stale conversational inertia.
  3. **Context-Budgeted Information Retrieval**: When retrieving code or context, use targeted slice viewing (`StartLine`/`EndLine`, `grep_search`, AST outlines) rather than blindly dumping large files into context, preventing context bloating that accelerates compaction.
  4. **Compaction Self-Orientation**: Upon detecting a compaction resume or cold restart, the AI must immediately inspect `git status`, the latest commit log (`git log -n 1`), and the task ledger (`.agents/task_ledger.json`) to establish 100% factual grounding before proposing or executing code.

---

### PRINCIPLE-016: Universal Operational Dogfooding & Chaos Verification (The AI Must Use What It Builds)
- **Concept**: A task is never complete simply because code compiles or unit tests pass. Before shipping any feature, refactor, or architectural change, the AI must actively execute, drive, and "live inside" the software it creates—simulating real human interaction, chaotic user behavior, dirty external data, and verifying every single corner and subsystem end-to-end. Token frugality must never compromise comprehensive verification; reasonable API usage is expected and prioritized to ensure deep operational integrity, while strictly guarding against ridiculous or runaway operations (such as unbounded directory dumps or infinite loops).
- **Rules**:
  1. **Domain-Specific Interactive Dogfooding**:
     - *Desktop GUI*: Spawns the live window in-process, pumps the event loop, invokes buttons, traverses tabs, stress-tests mid-operation window destruction, and mechanically traps unhandled callback exceptions (e.g., `_tkinter.TclError`).
     - *Web Apps*: Launches the local dev server, uses browser/headless tools to interact with DOM elements, verifies forms and routing, and asserts zero console errors (`console.error`).
     - *CLI Applications*: Executes the binary in subshells with arguments, pipes stdin/stdout, tests interrupt signals (SIGINT), and verifies exit codes and error formatting.
     - *Backend APIs*: Boots the service, executes real HTTP requests with test clients, and asserts status codes and response contracts.
  2. **Exhaustive Corner Verification & End-to-End Execution**: Every critical path, modal, dialog, toggle, setting, and error handler must be explicitly driven and tested under realistic conditions. Never assume untested UI corners or backend branches will function.
  3. **Realistic Live Budgeting & Sanity Guardrails**: When testing against live cloud APIs or local model endpoints, exercise real-world multi-file and multi-turn workflows (realistic batches of diverse file types, real renames, vision analysis) rather than artificial micro-stubs. Ensure sanity guardrails prevent ridiculous waste: strictly forbid dumping thousands of unbounded raw files into a prompt or spawning uncontrolled retry loops.
  4. **Offline Chaos Fuzzing & Malformed Output Resilience**: Complement live tests with offline deterministic chaos fuzzing to verify graceful recovery from malformed JSON, integer types, markdown codeblocks, rate limits, and network dropouts at zero token cost.
  5. **Zero-Blast-Radius & Ephemeral Sandboxing (Safety Jail)**: Dogfooding must NEVER touch, scan, or mutate real user directories (Desktop, Documents, personal folders, or system files). All operational tests must run strictly inside ephemeral, isolated temporary sandboxes populated exclusively with synthetic test files, guarded by strict containment assertions, and wiped clean upon test completion.
  6. **Terse Context Reporting**: Dogfood runner outputs in terminal/chat must remain concise status dashboards (<15 lines). Verbose diagnostics and stack traces must be externalized to persistent disk logs (`.agents/dogfood_last_run.log`) to prevent conversational attentional drift and context compaction (**PRINCIPLE-009**, **PRINCIPLE-015**).
  7. **Pre-Ship Dogfooding Gate**: The interactive dogfooding suite must be executed and confirmed passing with 100% success alongside standard unit tests before staging changes.


---

## 🛠️ AI Task Checklists

### 🛫 Pre-Flight Checklist (Run at Cold Start / Before Coding)
- [ ] **Context Verification**: Have I reviewed active principles (`PRINCIPLE-001` through `PRINCIPLE-016`) and repo state?
- [ ] **Compaction & Disruption Audit**: Have I inspected `git status`, `git log -n 1`, and `.agents/task_ledger.json` to ground myself after any compaction or disruption (**PRINCIPLE-013**, **PRINCIPLE-015**)?
- [ ] **Empirical Grounding**: Have I verified relevant file paths, signatures, and imports on disk before proposing edits (**PRINCIPLE-014**)?
- [ ] **Knowledge Base Context**: Have I checked relevant guides in `knowledge/` to understand existing patterns (**PRINCIPLE-010**)?
- [ ] **Dogfooding & Operational Verification Plan**: How will the AI actively drive, test, and stress-test the real application (GUI/API/CLI/Web) before shipping (**PRINCIPLE-016**)?
- [ ] **Necessity Assessment**: Why is this change needed, and what specific problem does it address?
- [ ] **Benefit Projection**: How will this directly enhance user value, modularity, or RLM architecture?
- [ ] **Test Coverage Plan**: Have I planned unit tests to validate this change and prevent regressions (**PRINCIPLE-011**)?
- [ ] **Crash Resilience & Atomicity Plan**: Are file writes, settings, and undo logs protected against power-loss corruption (**PRINCIPLE-012**, **PRINCIPLE-013**)?
- [ ] **Code Conciseness & Token Budget Plan**: Is the code concise, and are LLM prompts token-budgeted and compact (**PRINCIPLE-009**, **PRINCIPLE-015**)?
- [ ] **Performance & Resource Plan**: Is the solution designed for optimal speed, minimal latency, and lean dependencies (**PRINCIPLE-007**)?
- [ ] **Friction & Accessibility Check**: Does the solution maintain "one-click start" without forcing external app installs (**PRINCIPLE-008**)?
- [ ] **Risk / Harm Analysis**: What could break, regress, or introduce latency/fragility, and how will I prevent it?
- [ ] **Quality Standard**: Does the proposed design uphold premium quality without cutting corners?

### 🛬 Post-Flight Checklist (Run Before Completion)
- [ ] Have I adhered to **RLM compatibility** (recursive decomposition where applicable)?
- [ ] Is the architecture **modular** and decoupled?
- [ ] Is the code **concise, lean, and token-frugal** without context waste (**PRINCIPLE-009**, **PRINCIPLE-015**)?
- [ ] Are all code changes **empirically grounded with zero hallucinated imports or assumptions** (**PRINCIPLE-014**)?
- [ ] Are code paths **optimized for speed, responsiveness, and lean resource consumption** (**PRINCIPLE-007**)?
- [ ] Does the app maintain **one-click zero-install accessibility** while preserving local servers (**PRINCIPLE-008**)?
- [ ] Are all state changes and logs **crash-resilient and written atomically** (**PRINCIPLE-012**, **PRINCIPLE-013**)?
- [ ] Have intermediate milestones been **safely checkpointed and disruption-protected** (**PRINCIPLE-013**, **PRINCIPLE-015**)?
- [ ] Have all **automated unit tests passed with 100% success** (`python -m unittest discover tests`) (**PRINCIPLE-011**)?
- [ ] Has the **interactive dogfooding suite executed and passed with 100% operational success** (`python scripts/dogfood_app.py` or equivalent) (**PRINCIPLE-016**)?
- [ ] Have all **AI guideline files been automatically synchronized** if principles changed (**PRINCIPLE-004**)?
- [ ] Has the **AI knowledge base in `knowledge/` been updated and verified** (**PRINCIPLE-010**)?
- [ ] Has **README.md been updated** to reflect all changes (**PRINCIPLE-005**)?
- [ ] Has an **automatic commit** been created with a conventional commit message (**PRINCIPLE-002**)?
- [ ] Has the commit been **automatically pushed** to the remote repository (**PRINCIPLE-002**)?





