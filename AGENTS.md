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

## 🛠️ AI Task Checklists

### 🛫 Pre-Flight Checklist (Run at Cold Start / Before Coding)
- [ ] **Context Verification**: Have I reviewed active principles (`PRINCIPLE-001` through `PRINCIPLE-012`) and repo state?
- [ ] **Knowledge Base Context**: Have I checked relevant guides in `knowledge/` to understand existing patterns (**PRINCIPLE-010**)?
- [ ] **Necessity Assessment**: Why is this change needed, and what specific problem does it address?
- [ ] **Benefit Projection**: How will this directly enhance user value, modularity, or RLM architecture?
- [ ] **Test Coverage Plan**: Have I planned unit tests to validate this change and prevent regressions (**PRINCIPLE-011**)?
- [ ] **Crash Resilience & Atomicity Plan**: Are file writes, settings, and undo logs protected against power-loss corruption (**PRINCIPLE-012**)?
- [ ] **Code Conciseness & Token Budget Plan**: Is the code concise, and are LLM prompts token-budgeted and compact (**PRINCIPLE-009**)?
- [ ] **Performance & Resource Plan**: Is the solution designed for optimal speed, minimal latency, and lean dependencies (**PRINCIPLE-007**)?
- [ ] **Friction & Accessibility Check**: Does the solution maintain "one-click start" without forcing external app installs (**PRINCIPLE-008**)?
- [ ] **Risk / Harm Analysis**: What could break, regress, or introduce latency/fragility, and how will I prevent it?
- [ ] **Quality Standard**: Does the proposed design uphold premium quality without cutting corners?

### 🛬 Post-Flight Checklist (Run Before Completion)
- [ ] Have I adhered to **RLM compatibility** (recursive decomposition where applicable)?
- [ ] Is the architecture **modular** and decoupled?
- [ ] Is the code **concise, lean, and token-frugal** without context waste (**PRINCIPLE-009**)?
- [ ] Are code paths **optimized for speed, responsiveness, and lean resource consumption** (**PRINCIPLE-007**)?
- [ ] Does the app maintain **one-click zero-install accessibility** while preserving local servers (**PRINCIPLE-008**)?
- [ ] Are all state changes and logs **crash-resilient and written atomically** (**PRINCIPLE-012**)?
- [ ] Have all **automated unit tests passed with 100% success** (`python -m unittest discover tests`) (**PRINCIPLE-011**)?
- [ ] Have all **AI guideline files been automatically synchronized** if principles changed (**PRINCIPLE-004**)?
- [ ] Has the **AI knowledge base in `knowledge/` been updated and verified** (**PRINCIPLE-010**)?
- [ ] Has **README.md been updated** to reflect all changes (**PRINCIPLE-005**)?
- [ ] Has an **automatic commit** been created with a conventional commit message (**PRINCIPLE-002**)?
- [ ] Has the commit been **automatically pushed** to the remote repository (**PRINCIPLE-002**)?



