# Claude AI Assistant Guidelines

> **MANDATORY FOR CLAUDE CODE & CLAUDE ASSISTANTS:**
> Strictly follow all principles and guidelines defined in [AGENTS.md](AGENTS.md) and [GUIDELINES.md](GUIDELINES.md).

## Core Principles:
1. **PRINCIPLE-001: RLM Compatibility (Recursive Language Model)**:
   - Hierarchical recursive decomposition (Domain -> Category -> Sub-category -> File Action).
   - Bounded context windows, recursive validation, and self-refinement.
2. **PRINCIPLE-002: Automatic Git Workflow (Commit & Push)**:
   - Automatically stage, commit using Conventional Commits (`feat(...)`, `fix(...)`, `docs(...)`), and push to the remote branch upon task completion.
3. **PRINCIPLE-003: Modularity & Pluggable Architecture**:
   - Decoupled pluggable AI providers (Cloud APIs, Embedded local, Local server).
   - Clean separation of UI (`main.py`) and services (`services/`).
4. **PRINCIPLE-004: Living Principles System**:
   - Extensible governance: new principles can be registered anytime under `PRINCIPLE-XXX`.
5. **PRINCIPLE-005: AI Cold-Start Readiness & Living README Sync**:
   - Repository must remain 100% self-describing for cold-starting AI agents.
   - Mandatory `README.md` update after every single functional or architectural change.
6. **PRINCIPLE-006: Pre-flight Impact & Quality Checklist (Cold-Start Gate)**:
   - Mandatory evaluation at every cold start: why required, benefits, risks/harm, mitigations.
   - Quality non-diminution: safeguards must never justify degraded code or superficial implementations.
