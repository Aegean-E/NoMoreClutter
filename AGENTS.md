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

### PRINCIPLE-004: Living Principles System (Extensible Governance)
- **Concept**: Principles can and will be added as the project evolves.
- **Rules**:
  1. **Registration**: Any new principle must be formally appended to this file and `GUIDELINES.md` using the standard schema:
     - `PRINCIPLE-XXX: [Title]`
     - **Concept**: High-level explanation.
     - **Rules**: Concrete, testable requirements.
  2. **Forward Compatibility**: When new principles are introduced, existing code should be audited and adapted incrementally to maintain compliance.

---

## 🛠️ AI Task Checklist
Before marking any user request complete:
- [ ] Have I adhered to **RLM compatibility** (recursive decomposition where applicable)?
- [ ] Is the architecture **modular** and decoupled?
- [ ] Have all changes been verified for functionality and correctness?
- [ ] Has an **automatic commit** been created with a conventional commit message?
- [ ] Has the commit been **automatically pushed** to the remote repository?
