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

## 3. Triggers — When to Act Automatically

### On `odab pull` (User-Initiated Quick Record)
When the user says: `오답 넣어` or `odab pull`:

**You must immediately:**
1. Analyze the recent conversation to identify what went wrong and what fixed it.
2. Call `auto_record(what_went_wrong="...", what_fixed_it="...", target_model="your-model-name")`.
3. **REPORT** what you recorded to the user.

**The user should NOT need to specify any details.** You already have the context.

### On `오답 수정` / `odab fix` (Revise Last Note)
When the user says `오답 수정` or `odab fix` followed by feedback:
1. Call `revise_last(correction="user's corrected interpretation")`.
2. **REPORT** the revised content to the user.

### On `오답 삭제` / `odab del` (Delete Last Note)
When the user says `오답 삭제` or `odab del`:
1. Call `delete_last()`.
2. **REPORT** what was deleted to the user.

### On Command Failure (exit code ≠ 0)
When any shell command you execute fails:
1. Capture the stderr/traceback.
2. Call `match_error_trace(error_trace=stderr_content)` to check for a known fix.
3. If a match is found, apply the fix immediately and **REPORT** what you found.
4. If no match and you solve it yourself, call `auto_record()` and **REPORT**.

---

## Mandatory Reporting Rule

> **After EVERY odab action, you MUST report to the user what happened.**
> Do not silently record, revise, or delete. Always show the result.

---

## 4. Trigger Quick Reference

| User says | Agent action | MCP tool |
|-----------|-------------|----------|
| `오답 넣어` / `odab pull` | Record last mistake | `auto_record()` |
| `오답 수정` / `odab fix` | Revise last note | `revise_last()` |
| `오답 삭제` / `odab del` | Delete last note | `delete_last()` |

---

## 4. Conflict Handling

If a new solution contradicts an existing note (e.g. Note A says "increase timeout", Note B says "remove timeout entirely"):
* **MCP Tool:** `propose_conflict_resolution(note_id_a=X, note_id_b=Y, proposed_solution_c="merged_solution")`

---

## 5. CLI Quick Reference

| Command | Description |
|---------|-------------|
| `odab pull 'mistake' 'fix'` | **Quick-record** — auto-generates keyword |
| `odab list` | List all notes |
| `odab show <id>` | View note details |
| `odab add -k ... -e ... -f ... -m ...` | Manual add with full control |
| `odab approve <id>` | Verify a draft note |
| `odab delete <id>` | Delete a note |
| `odab graph` | Visualize note relations |
| `odab link <id1> <id2> -t conflict` | Link two notes |
| `odab decay -d 30` | Apply time decay (30 days) |
| `odab resolve <idA> <idB> -c "solution"` | Resolve conflicting notes |
