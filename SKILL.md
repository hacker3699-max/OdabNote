---
name: odab-note
description: Wrong-answer vaccine system for AI agents. Learns error patterns and prevents repeated mistakes.
---

# OdabNote — Agent Work Instructions

This document defines how AI coding agents (Claude Code, OpenAI Codex, Cursor, Cline, etc.) should use the **OdabNote** system to prevent coding regressions and track verified solutions.

---

## 1. Role and Core Objective

You are an AI agent equipped with the `odab-note` MCP server or `odab` CLI.
Your goal: **Never repeat the same coding mistake twice.** Achieve this by querying, matching, and updating the local OdabNote database.

---

## 2. Agent Workflow (Mandatory Checklist)

### 🟩 Step 1: Pre-Task Investigation (Before Coding)
At the start of any coding task, query the database for past mistakes related to the files, technologies, or keywords you are working on.
* **MCP Tool:** `query_notes(keywords=["technology", "keyword"])`
* **CLI fallback:** `odab list`

*Example:* If modifying SMC interfaces, check `keywords=["SMC"]` to find timeout-related errors.

### 🟥 Step 2: Error Matching (On Compile/Run Failure)
When a build, test, or runtime error occurs, do NOT immediately make random code changes. First, match the exact error trace against the database.
* **MCP Tool:** `match_error_trace(error_trace="paste_full_stack_trace", target_model="gemini-3.5-flash")`
* **Rule:** If a match is found, apply the specified **Correct Solution** immediately.

### 🟨 Step 3: Record New Mistakes (After Fixing)
If you solve an error not yet in the database, record it so future runs won't repeat the struggle.
* **MCP Tool:** `record_mistake(keyword="Error_Name", error_pattern="regex_pattern", solution="exact_fix", target_model="gemini-3.5-flash")`
* **CLI fallback:** `odab add -k "Name" -e "regex" -f "fix" -m "model"`

*Note:* New records start as `Draft`. Call `odab approve <id>` once the fix is proven correct.

---

## 3. Conflict Handling

If a new solution contradicts an existing note (e.g. Note A says "increase timeout", Note B says "remove timeout entirely"):
* **MCP Tool:** `propose_conflict_resolution(note_id_a=X, note_id_b=Y, proposed_solution_c="merged_solution")`

---

## 4. CLI Quick Reference

| Command | Description |
|---------|-------------|
| `odab list` | List all notes |
| `odab show <id>` | View note details |
| `odab add -k ... -e ... -f ... -m ...` | Add a new note |
| `odab approve <id>` | Verify a draft note |
| `odab delete <id>` | Delete a note |
| `odab graph` | Visualize note relations |
| `odab link <id1> <id2> -t conflict` | Link two notes |
| `odab decay -d 30` | Apply time decay (30 days) |
| `odab resolve <idA> <idB> -c "solution"` | Resolve conflicting notes |
