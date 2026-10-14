# Project Guidelines & Architecture Principles

This document defines the architectural guidelines and design principles for **NoMoreClutter**. All contributors, automated pipelines, and AI systems must adhere to these rules.

---

## 🧭 Principles Index

| ID | Title | Summary |
|---|---|---|
| **[PRINCIPLE-001](#principle-001-rlm-compatibility-recursive-language-model)** | RLM Compatibility | Hierarchical and recursive problem decomposition for file categorization. |
| **[PRINCIPLE-002](#principle-002-automatic-git-workflow-commit--push)** | Automatic Git Workflow | Automated conventional commits and pushes upon task completion. |
| **[PRINCIPLE-003](#principle-003-modularity--pluggable-architecture)** | Modularity | Pluggable providers (Cloud, Embedded, Local Server) and decoupled UI/services. |
| **[PRINCIPLE-004](#principle-004-living-principles-system)** | Living Principles | Formal protocol for adding and evolving project principles over time. |

---

## 📖 Principle Details

### PRINCIPLE-001: RLM Compatibility (Recursive Language Model)
- **Problem**: Flat batch processing fails when dealing with deep directory structures, thousands of files, or complex conceptual taxonomies.
- **Guideline**:
  - Implement recursive hierarchical processing: Root domain $\rightarrow$ high-level category $\rightarrow$ sub-category $\rightarrow$ file-level renaming.
  - Divide-and-conquer file sets recursively instead of feeding unbounded flat lists into single prompts.
  - Enable recursive validation and refinement loops for ambiguous files.

### PRINCIPLE-002: Automatic Git Workflow (Commit & Push)
- **Problem**: Uncommitted work leads to lost progress and inconsistent branches.
- **Guideline**:
  - The AI assistant automatically stages, commits, and pushes verified code changes upon task or milestone completion.
  - Always use [Conventional Commits](https://www.conventionalcommits.org/):
    - `feat(scope): ...`
    - `fix(scope): ...`
    - `refactor(scope): ...`
    - `docs(scope): ...`
    - `chore(scope): ...`

### PRINCIPLE-003: Modularity & Pluggable Architecture
- **Problem**: Monolithic scripts make it hard to introduce new AI backends, file types, or organization algorithms.
- **Guideline**:
  - **Provider Abstraction**: Decouple the LLM backend into pluggable providers:
    - *Cloud API Providers* (Groq, Google Gemini, OpenAI, OpenRouter) — zero desktop software needed.
    - *Embedded In-Process Models* — local inference directly in Python.
    - *Local Server Providers* — LM Studio, Ollama.
  - **Decoupled Architecture**: Keep `main.py` purely focused on UI/presentation, delegating all logic to `services/` and `models/`.

### PRINCIPLE-004: Living Principles System
- **Problem**: Projects evolve, and static rules become outdated.
- **Guideline**:
  - When new architectural patterns or project requirements emerge, register a new principle following the `PRINCIPLE-XXX` template.
  - Keep both `AGENTS.md` and `GUIDELINES.md` in sync.

---

## 📝 How to Add New Principles

To add a new principle:
1. Assign the next sequential ID (`PRINCIPLE-005`, etc.).
2. Define the **Problem/Concept** and concrete **Rules/Guidelines**.
3. Update `GUIDELINES.md` and `AGENTS.md`.
