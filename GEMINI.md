# AI Guidelines & Project Principles

See full specification in [AGENTS.md](file:///c:/Users/Yunus-Emre/Desktop/NoMoreClutter/NoMoreClutter/AGENTS.md) and [GUIDELINES.md](file:///c:/Users/Yunus-Emre/Desktop/NoMoreClutter/NoMoreClutter/GUIDELINES.md).

## Core Principles Summary:
1. **PRINCIPLE-001: RLM Compatibility (Recursive Language Model)**:
   - The system must be built for Recursive Language Model processing. File organization and semantic categorization must support recursive decomposition rather than monolithic, flat-batch prompting.
2. **PRINCIPLE-002: Automatic Git Workflow (Commit & Push)**:
   - AI must maintain an active, clean, and reliable Git trail without requiring manual commit reminders from the user.
3. **PRINCIPLE-003: Modularity & Pluggable Architecture**:
   - Every major component must be modular, decoupled, and adhere to the Single Responsibility Principle.
4. **PRINCIPLE-004: Living Principles System (Extensible Governance & Auto-Sync)**:
   - Principles can and will be added as the project evolves. Whenever any principle is added, updated, or revised, all AI guideline documents across the repository must be automatically synchronized to maintain absolute consistency.
5. **PRINCIPLE-005: AI Cold-Start Readiness & Living Documentation (README Sync)**:
   - The repository must be permanently prepared for a "cold start" by any AI assistant or developer. Any new agent entering the project with zero prior conversational history must immediately understand the project state, run commands, architecture, and principles. To prevent knowledge drift, `README.md` must be systematically updated after every meaningful change.
6. **PRINCIPLE-006: Pre-flight Impact & Quality Checklist (Cold-Start Gate)**:
   - Before implementing code modifications, refactorings, or architecture changes—especially upon a cold start—the AI must evaluate a structured pre-flight impact checklist. This assessment ensures the AI clarifies the *why*, maximizes project *benefits*, preemptively identifies potential *harm/regressions*, and proactively guards quality.
7. **PRINCIPLE-007: Performance & Resource Optimization (Speed & Lean Architecture)**:
   - Every code change, architectural modification, and dependency choice must be optimized for execution speed, low latency, optimal algorithmic complexity, and lean resource utilization (CPU, memory, disk I/O, and LLM token budget).
8. **PRINCIPLE-008: Zero-Friction Onboarding & Hybrid AI Access (One-Click Start)**:
   - The application must be instantly usable out of the box ("one-click and start") without forcing users to download, install, or configure heavy external desktop applications (like LM Studio or Ollama). At the same time, the system must retain first-class support for local self-hosted servers (Ollama, LM Studio) for users who demand total local control.
9. **PRINCIPLE-009: Token Frugality & Lean Code Architecture (Context Budgeting)**:
   - Code must be concise, expressive, and devoid of unnecessary bloat. All interactions with LLMs must be strictly budgeted for tokens—leveraging RLM decomposition, compact representations, and hierarchical batching so requests never exhaust context windows, exceed rate limits (TPM), or waste user tokens.
10. **PRINCIPLE-010: AI Knowledge Base & Continuous Synchronization**:
   - The repository must maintain an active, structured, and modular codebase knowledge base in `knowledge/`. Every AI assistant interacting with this codebase must consult the knowledge base for deep architectural context and systematically update it after any architectural, service, model, or UI change to eliminate knowledge drift.
