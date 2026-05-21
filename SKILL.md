# SKILL.md: Mistake-Guard (Odab-Note) Agent Work Instructions

This document defines how AI coding agents (Claude Code, OpenAI Codex, Cursor, Cline, etc.) should use the **Odab-Note (Mistake-Guard)** system to prevent coding regressions and track verified solutions.

---

## 1. Role and Core Objectives
You are an AI agent equipped with the `mistake-guard` MCP server or `odab` CLI. 
Your goal is to **never repeat the same coding mistakes twice** by querying, matching, and updating the local mistake-guard database.

---

## 2. Agent Workflow (Mandatory Checklist)

### 🟩 Step 1: Pre-Task Investigation (Before Coding)
At the very beginning of any coding task, query the database to check if there are past mistakes related to the files, technologies, or keywords you are working on.
* **MCP Tool:** `query_notes(keywords=["your_technology", "keyword"])`
* **CLI command fall-back:** `odab list` or `odab show --keyword <name>`

*Example:* If modifying system metrics or SMC interfaces, check `keywords=["SMC"]` to find timeout behaviors or hardware config errors.

### 🟥 Step 2: Error Analysis & Matching (Upon Compilation/Run Failure)
If a build, test, or run error occurs, do not immediately make random code changes. First, match the exact error trace against the database to check for a registered vaccine.
* **MCP Tool:** `match_error_trace(error_trace="paste_entire_stack_trace_here", target_model="claude-3.5-sonnet")`
* **CLI command fall-back:** Use the traceback text to search the database.

*Rule:* If a match is found, apply the specified **Correct Solution** immediately.

### 🟨 Step 3: Recording New Mistakes (Post-Fix Documentation)
If you solve a new error that was not registered in the database, document it so future agent runs won't repeat the struggle.
* **MCP Tool:** `record_mistake(keyword="Descriptive_Error_Name", error_pattern="regex_of_error_trace", solution="exact_code_change_needed")`
* **CLI command fall-back:** `odab add --keyword "Name" --error "Regex" --solution "Steps" --model "your-model"`

*Note:* Newly recorded mistakes are created in `Draft` status. Ask the user or call `odab approve <id>` once the fix is proven correct.

---

## 3. Conflict Handling Guide
If a new solution contradicts an existing note (e.g. Note A suggests "increase timeout", but Note B suggests "remove timeout entirely"), trigger a conflict resolution flow:
* **MCP Tool:** `propose_conflict_resolution(note_id_a=X, note_id_b=Y, proposed_solution_c="merged_solution")`
* The tool will format a selection block. Present this to the user to choose the correct resolution route.

---

## 4. Quick CLI Cheatsheet for Agents
If the MCP server is unavailable, run these shell commands directly:
* **List all notes:** `odab list`
* **Graph relations:** `odab graph`
* **Approve draft:** `odab approve <id>`
* **Link related notes:** `odab link <id1> <id2> --type conflict`
