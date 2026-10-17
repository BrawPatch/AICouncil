# Multi-Agent Council Architecture and Setup Context

This document captures the finalized system design parameters, multi-agent orchestrations, and complete build files for running an agentic Scrum/TDD engineering council locally on Apple Silicon hardware.

## System Hardware & LLM Configuration Parameters
- **Target Hardware Architecture:** MacBook Pro (M-Series) with 24GB Unified Memory.
- **Local Context Host Subsystem:** Ollama (Background execution).
- **VRAM Allocation Budget Constraints:** Models are configured with a keep-alive window of 0 (`OLLAMA_KEEP_ALIVE=0s`) to force immediate unloading after execution nodes finish. This prevents memory swaps by keeping active memory usage inside a safe 15GB profile.
- **Model Distribution Matrix:**
  1. **Chairman / Scrum Master Tasks:** `llama3.1:8b` (Synthesizer & Router)
  2. **Research & Deep Logic Tasks:** `mistral:7b` (Security Craftsman)
  3. **Coding & Implementation Tasks:** `qwen2.5-coder:7b` (TDD Software Engineer)

## Operational Workflow Graph Design
The control fabric is built on top of **LangGraph**, enabling explicit state loops and cyclical bug-fixing passes between the QA Validator node and the Coding Agent node.

