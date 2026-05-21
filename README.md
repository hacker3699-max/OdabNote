# OdabNote — Wrong-Answer Vaccine System for AI Agents

> **Teach AI agents to never repeat the same coding mistake twice.**

OdabNote is a local MCP (Model Context Protocol) server that captures error patterns, stores verified solutions, and automatically matches future errors against its database — acting as an immune system for AI coding agents.

---

## Why OdabNote?

AI coding agents (Claude Code, Codex, Cursor, Gemini, etc.) repeatedly make the same mistakes across sessions. They forget what went wrong last time. OdabNote solves this by:

1. **Recording** error patterns with their verified fixes
2. **Matching** new errors against the database in real-time
3. **Preventing** the same mistake from happening again
4. **Tracking** which AI models make which mistakes (model-specific blacklists)
5. **Decaying** outdated patterns so the knowledge stays fresh

---

## Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
git clone https://github.com/hacker3699-max/OdabNote.git
cd OdabNote
python3 -m venv .venv
.venv/bin/pip install -e .
```

### Verify Installation

```bash
.venv/bin/odab --help
```

Expected output:
```
Usage: odab [OPTIONS] COMMAND [ARGS]...

  OdabNote CLI - Manage wrong-answer notes (오답노트) for AI Agents.

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

**Step 1 — Agent makes a mistake. You say: `오답 넣어`**

> You asked the agent to modify `config.yaml`, but it created a new `config_new.yaml` instead.

```
You:  왜 새로 만들어? 기존 파일 수정하라고 했잖아. 오답 넣어

Agent: ✅ Recorded (ID: 13, Model: claude-opus-4.6)
         Keyword: Created_New_File_Instead_Modifying
         Mistake: User asked to modify existing file but agent created a new file instead
         Fix: When user says 'modify', always edit the existing file in place.
              Never create a new file unless explicitly asked.
```

**Step 2 — Not happy with the note? Say: `오답 수정`**

```
You:  오답 수정 그게 아니라 설정 파일 건드릴 때는 백업부터 하라는 뜻이야

Agent: 📝 Revised note (ID: 13)
         Keyword: Config_File_Backup_First
         Mistake: Modified config file without creating a backup first
         Fix: Always create a backup copy before modifying any config file
```

**Step 3 — Want to remove it entirely? Say: `오답 삭제`**

```
You:  오답 삭제

Agent: 🗑️ Deleted note (ID: 13)
         Keyword: Config_File_Backup_First
         Was: Modified config file without creating a backup first
```

**That's it.** Three phrases to remember:

| Phrase | What it does |
|--------|-------------|
| `오답 넣어` | Record the last mistake |
| `오답 수정` + feedback | Fix the note |
| `오답 삭제` | Delete the note |

> English alternatives: `odab pull`, `fix that note`, `delete that note`

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
2    | Surface_Only_Fix     | gemini-3.5-flash | 1     | Yes      | 표면만 고치고 내부 코드에...
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

### For Gemini (Antigravity)

Add to `~/.gemini/antigravity/mcp_config.json`:

```json
{
  "odab-note": {
    "command": "/path/to/OdabNote/.venv/bin/python",
    "args": ["-m", "odab_note.server"],
    "env": {
      "PYTHONPATH": "/path/to/OdabNote/src"
    }
  }
}
```

### For Claude Code / Cursor / Cline

Add to your MCP settings (e.g. `.cursor/mcp.json` or `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "odab-note": {
      "command": "/path/to/OdabNote/.venv/bin/python",
      "args": ["-m", "odab_note.server"],
      "env": {
        "PYTHONPATH": "/path/to/OdabNote/src"
      }
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `query_notes(keywords)` | Search past mistakes by keyword before starting work |
| `match_error_trace(error_trace, target_model)` | Match a stack trace against the database to find a known fix |
| `record_mistake(keyword, error_pattern, solution, target_model)` | Record a new mistake with its solution |
| `propose_conflict_resolution(note_id_a, note_id_b, proposed_solution_c)` | Propose resolution for conflicting notes |
| `resolve_conflict_merge(keep_id, delete_id, merged_solution, merged_keyword)` | Execute a conflict merge |
| `register_skill(name, cmd, desc)` | Save a verified workflow command for reuse |

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
