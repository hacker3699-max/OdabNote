# OdabNote — Wrong-Answer Vaccine System for AI Agents

[![Sponsor](https://img.shields.io/badge/Sponsor-♥-ea4aaa?style=for-the-badge&logo=github-sponsors)](https://github.com/sponsors/hacker3699-max)
[![License](https://img.shields.io/badge/License-All_Rights_Reserved-blue?style=for-the-badge)](LICENSE)

> **Teach AI agents to never repeat the same coding mistake twice.**

OdabNote is a local MCP (Model Context Protocol) server that captures error patterns, stores verified solutions, and automatically matches future errors against its database — acting as an immune system for AI coding agents.

---

## The Story Behind OdabNote

In Korea, students keep a notebook called **오답노트** (*odab-note*) — a "wrong-answer notebook." Every time they get a question wrong on an exam, they write it down: what they got wrong, why it was wrong, and the correct answer. Over time, this notebook becomes their most powerful study tool. They stop making the same mistakes.

**We built the same thing for AI agents.**

Working daily with Claude, Gemini, Codex, and other models, a pattern became obvious: **AI agents forget.** They make the same mistakes across sessions — using wrong paths, breaking naming conventions, ignoring project rules. Every new conversation starts from zero.

We tried the usual fixes:
- **System prompts and harnesses** — they work, but agents hit context limits and forget rules buried 50k tokens ago
- **Gate checks and linting** — they catch syntax, not logic errors or project-specific anti-patterns
- **Documentation** — agents skim it, miss details, and repeat mistakes anyway

None of these solutions *learn*. They're static. So we asked: **what if agents could build their own wrong-answer notebook?**

OdabNote is that notebook — a local MCP server that captures error patterns, stores verified fixes, and matches future errors against its database. It acts as an **immune system** for AI coding agents. Once a mistake is recorded, no agent repeats it.

---

## Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
pip install odab-note
```

Or install from source:

```bash
git clone https://github.com/hacker3699-max/OdabNote.git
cd OdabNote
pip install -e .
```

### Verify Installation

```bash
.venv/bin/odab --help
```

Expected output:
```
Usage: odab [OPTIONS] COMMAND [ARGS]...

  OdabNote CLI - Manage wrong-answer notes for AI Agents.

Commands:
  add         Add a new wrong-answer note manually (auto-verified).
  approve     Approve a wrong-answer note (Veto Pass).
  decay       Manually apply time-decay to decrease weights of obsolete notes.
  delete      Delete a wrong-answer note.
  graph       Visualize relations and conflicts of wrong-answer notes.
  link        Link two notes with relation (triggers or conflict).
  list        List all wrong-answer notes.
  resolve     Interactively resolve conflict between Note A and Note B.
  run-server  Run the OdabNote MCP server.
  show        Show details of a specific wrong-answer note.
```

---

## Usage Guide

### How It Works (Natural Language)

You don't need to type CLI commands. Just talk to your AI agent in natural language.

**Step 1 — Agent makes a mistake. You say: `오답 넣어` or `odab pull`**

> You asked the agent to modify `config.yaml`, but it created a new `config_new.yaml` instead.

```
You:  Why did you create a new file? I said modify the existing one. odab pull

Agent: ✅ Recorded (ID: 13, Model: claude-opus-4.6)
         Keyword: Created_New_File_Instead_Modifying
         Mistake: User asked to modify existing file but agent created a new file instead
         Fix: When user says 'modify', always edit the existing file in place.
              Never create a new file unless explicitly asked.
```

**Step 2 — Not happy with the note? Say: `오답 수정` or `odab fix`**

```
You:  odab fix I meant you should always back up config files before editing them

Agent: 📝 Revised note (ID: 13)
         Keyword: Config_File_Backup_First
         Mistake: Modified config file without creating a backup first
         Fix: Always create a backup copy before modifying any config file
```

**Step 3 — Want to remove it entirely? Say: `오답 삭제` or `odab del`**

```
You:  odab del

Agent: 🗑️ Deleted note (ID: 13)
         Keyword: Config_File_Backup_First
         Was: Modified config file without creating a backup first
```

**That's it.** Three phrases to remember:

| Korean | English | What it does |
|--------|---------|-------------|
| `오답 넣어` | `odab pull` | Record the last mistake |
| `오답 수정` | `odab fix` | Revise the note |
| `오답 삭제` | `odab del` | Delete the note |

---

### CLI Reference

#### 1. Record a Mistake

When you encounter an error and fix it, record it:

```bash
odab add \
  -k "ZeroDivisionPrevention" \
  -e "ZeroDivisionError: division by zero" \
  -f "Check if denominator == 0 before dividing and return a safe default value" \
  -m "all"
```

| Flag | Description |
|------|-------------|
| `-k` | Keyword name for this mistake (unique identifier) |
| `-e` | Error pattern (supports regex) |
| `-f` | The correct fix / solution |
| `-m` | Target model (`all`, `gemini-3.5-flash`, `claude-3.5-sonnet`, etc.) |

### 2. List All Mistakes

```bash
odab list
```

```
ID   | Keyword              | Model            | Count | Verified | Error Pattern
-----------------------------------------------------------------------------------------------
1    | ZeroDivisionPrev...  | all              | 1     | Yes      | ZeroDivisionError: division by...
2    | Surface_Only_Fix     | gemini-3.5-flash | 1     | Yes      | Fixed surface only, left old refs...
```

### 3. View Details

```bash
odab show 1
```

### 4. Visualize Relations

```bash
odab graph
```

```
[ Odab-Note Dependency & Conflict Graph 🕸️ ]

● [ID: 1] ZeroDivisionPrevention (Count: 1, Verified: ✓)
  └── (No active relations)

● [ID: 2] Surface_Only_Fix (Count: 1, Verified: ✓)
  └── 🔗 [Triggers] -> [ID: 3] No_Full_Audit_Before_Done
```

### 5. Link Related Mistakes

```bash
odab link 2 3 --type triggers
```

### 6. Resolve Conflicts

When two notes contradict each other:

```bash
odab resolve 1 2 --solution-c "Merged solution that combines both approaches"
```

### 7. Apply Time Decay

Decrease weight of notes not triggered in N days:

```bash
odab decay --days 30
```

---

## MCP Server Integration

After `pip install odab-note`, add to your MCP config:

### For Gemini (Antigravity)

Add to `~/.gemini/antigravity/mcp_config.json`:

```json
{
  "odab-note": {
    "command": "odab-note"
  }
}
```

### For Claude Code / Cursor / Cline

Add to your MCP settings (e.g. `.cursor/mcp.json` or `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "odab-note": {
      "command": "odab-note"
    }
  }
}
```

### Available MCP Tools

| Tool | Trigger | Description |
|------|---------|-------------|
| `auto_record` | `오답 넣어` / `odab pull` | Quick-record a mistake from plain language |
| `revise_last` | `오답 수정` / `odab fix` | Revise the most recent note |
| `delete_last` | `오답 삭제` / `odab del` | Delete the most recent note |
| `query_notes` | — | Search past mistakes by keyword |
| `match_error_trace` | — | Match a stack trace to find a known fix |
| `record_mistake` | — | Record with full control (keyword, regex, solution) |
| `propose_conflict_resolution` | — | Propose resolution for conflicting notes |
| `resolve_conflict_merge` | — | Execute a conflict merge |
| `register_skill` | — | Save a verified workflow command for reuse |

---

## Testing

### Run the E2E Verification Script

```bash
cd OdabNote
.venv/bin/python tests/test_mcp.py
```

Expected output:
```
🔍 [TEST 1] Query Notes with keyword 'SMC'...
Result:
Found 2 wrong-answer notes:
...

🔍 [TEST 2] Match Error Trace for SMC Timeout...
Result:
Found 1 matching wrong-answer notes:
...

🔍 [TEST 3] Match ZeroDivisionError Trace...
Result:
Found 1 matching wrong-answer notes:
  - Target Keyword: ZeroDivisionPrevention
  - Correct Solution: Check if denominator == 0 before dividing...
```

### Manual End-to-End Test

1. **Create a bug:**
   ```bash
   echo 'print(1/0)' > /tmp/bad.py
   python3 /tmp/bad.py  # ZeroDivisionError
   ```

2. **Record it:**
   ```bash
   odab add -k "DivByZero" -e "ZeroDivisionError" -f "Guard with if x != 0" -m "all"
   ```

3. **Verify it matches:**
   ```bash
   .venv/bin/python -c "
   from odab_note.server import match_error_trace
   print(match_error_trace('ZeroDivisionError: division by zero'))
   "
   ```

4. **Confirm the vaccine is prescribed** — the output should show the fix you recorded.

---

## Project Structure

```
OdabNote/
├── src/odab_note/
│   ├── __init__.py
│   ├── server.py      # FastMCP server with 6 tools
│   ├── database.py    # SQLite DB with regex matching, decay, relations
│   └── cli.py         # Click CLI with 10 subcommands
├── tests/
│   ├── test_mcp.py    # E2E MCP tool verification
│   └── buggy_script.py # Intentional bug for testing
├── docs/              # PRD, philosophy, tier matrix
├── SKILL.md           # Agent instruction file (for Claude Code, Codex, etc.)
├── pyproject.toml
└── README.md
```

## Database Location

The SQLite database is stored at:
```
~/.gemini/antigravity/odab_note.db
```

---

## License

© Logan's Company. All rights reserved.
