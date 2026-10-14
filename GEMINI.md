# AI Guidelines & Project Principles

See full specification in [AGENTS.md](file:///c:/Users/Yunus-Emre/Desktop/NoMoreClutter/NoMoreClutter/AGENTS.md) and [GUIDELINES.md](file:///c:/Users/Yunus-Emre/Desktop/NoMoreClutter/NoMoreClutter/GUIDELINES.md).

## Core Principles Summary:
1. **PRINCIPLE-001: RLM Compatibility (Recursive Language Model)**:
   - Recursive hierarchical problem decomposition for directory structures and categorizations.
   - Bounded context windows, recursive validation, and self-refinement.
2. **PRINCIPLE-002: Automatic Git Workflow (Commit & Push)**:
   - Automatically stage, commit (Conventional Commits), and push upon completing any task/milestone.
3. **PRINCIPLE-003: Modularity & Pluggable Architecture**:
   - Decoupled pluggable AI providers (Cloud APIs, Embedded local, Local server).
   - Clear separation between UI (`main.py`) and services (`services/`).
4. **PRINCIPLE-004: Living Principles System**:
   - Extensible governance: new principles can be registered anytime under `PRINCIPLE-XXX`.
5. **PRINCIPLE-005: AI Cold-Start Readiness & Living README Sync**:
   - Repository must be 100% self-describing for any cold-starting AI agent.
   - Mandatory `README.md` update after every single functional or architectural change.
