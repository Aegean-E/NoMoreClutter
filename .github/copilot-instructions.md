# GitHub Copilot Instructions

All GitHub Copilot interactions in this repository must align with the architectural rules in `AGENTS.md` and `GUIDELINES.md`.

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
11. **PRINCIPLE-011: Automated Test Verification & Continuous Test Coverage (Regression Shield)**:
   - Every code modification, new feature, bug fix, or refactoring must be accompanied by automated unit or integration tests wherever technically feasible. Before finalizing any task, the full automated test suite must be executed and confirmed passing to guarantee zero regressions.
12. **PRINCIPLE-012: Crash Resilience, State Atomicity & Power-Loss Recovery (Fail-Safe Operations)**:
   - The application must remain fail-safe and self-healing against abrupt disruptions—such as sudden power outages, battery exhaustion, OS crashes, or external process termination. User files, application settings, and undo transaction logs must never be left in a corrupted, half-written, or unrecoverable state due to unexpected power loss.
13. **PRINCIPLE-013: Incremental Progress Checkpointing & Disruption Recovery (Zero-Progress-Loss Workflow)**:
   - Development workflows and AI execution sessions must be resilient against abrupt disruptions—such as sudden power outages, battery depletion, OS crashes, or process termination. Progress must never be treated as an all-or-nothing end-of-turn artifact; it must be recorded through incremental, atomic micro-checkpoints, persistent task ledgers, and immediate cold-start recovery protocols to guarantee zero work loss without compromising code quality.
14. **PRINCIPLE-014: Empirical Grounding & Anti-Hallucination Invariant (Verify-Before-Execution)**:
   - The AI must operate under strict empirical grounding. An agent must never make assumptions about codebase state, API contracts, imported symbols, or data contents without empirically verifying them against disk first. Intuitive guesses, phantom imports, and ungrounded hallucinations are strictly prohibited.
15. **PRINCIPLE-015: Attentional Drift Prevention & Compaction Resilience (Context Anchor Protocol)**:
   - In long-running sessions, large contexts induce attentional drift (the AI forgetting rules, skipping checklists, or losing constraints) and conversation compaction discards transient conversational context. To remain permanently immune to amnesia, all critical task state must be externalized to persistent disk artifacts, and the agent must continuously re-anchor against the repository's ground truth.
16. **PRINCIPLE-016: Universal Operational Dogfooding & Chaos Verification (The AI Must Use What It Builds)**:
   - A task is never complete simply because code compiles or unit tests pass. Before shipping any feature, refactor, or architectural change, the AI must actively execute, drive, and "live inside" the software it creates—simulating real human interaction, chaotic user behavior, dirty external data, and verifying every single corner and subsystem end-to-end. Token frugality must never compromise comprehensive verification; reasonable token usage is expected and prioritized to ensure deep operational integrity, while strictly guarding against ridiculous or runaway operations (such as unbounded directory dumps or infinite loops).
