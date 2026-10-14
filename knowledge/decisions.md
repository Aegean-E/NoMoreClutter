# Architecture Decision Records (ADRs) 📜

This document preserves the rationale, context, and consequences of critical architectural decisions.

---

## ADR-001: RLM Hierarchical Decomposition vs. Flat Batching

### Context
Sending hundreds or thousands of raw file paths directly into an LLM prompt leads to:
1. Context window exhaustion.
2. Rapid exhaustion of free-tier rate limits (e.g. Groq TPM caps).
3. "Attention dilution" and hallucinated file names.
4. Latency spikes and cost increases.

### Decision
Implement a Recursive Language Model (RLM) engine (`services/rlm_organizer.py`). Files are first partitioned into logical category clusters. Each cluster is serialized into dense JSON payloads using relative IDs rather than long absolute paths. Responses are deterministically mapped by ID.

### Consequences
- **Positive**: Cuts token overhead by ~70%. Guarantees that free-tier rate limits are respected. Eliminates off-by-one mapping errors.
- **Negative**: Adds an intermediate clustering step before dispatching requests.

---

## ADR-002: Zero-Install Cloud Providers with Local Fallback (Hybrid AI)

### Context
Requiring users to download heavy desktop apps (LM Studio, Ollama) before organizing their first file introduces substantial friction and turns away casual users. However, power users demand local self-hosted privacy.

### Decision
Support both paradigms seamlessly via a pluggable provider abstraction (`services/providers/`). Provide pre-configured cloud presets (Groq with free keys, Google Gemini, OpenAI, OpenRouter) alongside local servers (LM Studio, Ollama) and a 100% offline heuristic fallback.

### Consequences
- **Positive**: "One-click and start" accessibility for new users while retaining full privacy and power for local users.
- **Negative**: Requires maintaining provider presets and testing multiple endpoint types.

---

## ADR-003: Collision Avoidance and Batch Undo Stack

### Context
File operations can be destructive if destination folders already contain files with the same name, or if the user is dissatisfied with AI organization decisions.

### Decision
1. Dynamic collision renaming: if `destination/file.ext` exists, automatically generate `destination/file (1).ext`.
2. Batch undo: every file move is recorded as a `FileMoveRecord(original, new, timestamp)` and pushed to an undo stack. Users can roll back the entire batch with one click.

### Consequences
- **Positive**: Zero risk of accidental file overwrites or data loss. High user confidence.
- **Negative**: Memory overhead for the undo stack (negligible for typical batches).

---

## ADR-004: Living Principles System & Automated Cross-AI Synchronization

### Context
Different developers and AI assistants (Gemini, Claude, Cursor, Copilot) enter this repository across different workflows. Disconnected guidelines lead to knowledge drift and conflicting changes.

### Decision
Establish `AGENTS.md` as the master canonical specification. Implement `scripts/sync_principles.py` and `scripts/update_knowledge_base.py` to programmatically synchronize all guidelines (`GEMINI.md`, `CLAUDE.md`, `.cursorrules`, `.agents/rules/`, `.github/copilot-instructions.md`) and validate the knowledge base.

### Consequences
- **Positive**: 100% consistency across all AI assistants; eliminates knowledge drift.
- **Negative**: AI assistants must run sync scripts whenever principles or architecture change.
