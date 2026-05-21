from mcp.server.fastmcp import FastMCP
from odab_note.database import OdabNoteDB
import json
import re

# FastMCP 인스턴스 생성
mcp = FastMCP("OdabNote")
db = OdabNoteDB()

@mcp.tool()
def query_notes(keywords: list[str]) -> str:
    """Query past mistakes and correct actions by keywords.

    Use this at the beginning of a task to fetch relevant wrong-answer notes to avoid repeating past mistakes.
    """
    notes = db.query_notes(keywords)
    if not notes:
        return "No relevant past mistakes found for keywords: " + ", ".join(keywords)

    result = [f"Found {len(notes)} wrong-answer notes:"]
    for idx, note in enumerate(notes, 1):
        status = "Verified" if note['is_verified'] else "Draft (Not Verified)"
        result.append(
            f"{idx}. [{status}] (Weight: {note['occurrence_count']})\n"
            f"   - Target Keyword: {note['keyword']}\n"
            f"   - Error/Mistake Pattern: {note['error_pattern']}\n"
            f"   - Correct Solution: {note['solution']}"
        )
    return "\n\n".join(result)

@mcp.tool()
def record_mistake(keyword: str, error_pattern: str, solution: str, target_model: str = "all") -> str:
    """Record a new mistake or error pattern with its correct solution.

    Use this tool when a build error occurs, or when you receive negative feedback from the user.
    target_model can be set to a specific model name (e.g. 'gemini-3.5-flash', 'claude-3.5-sonnet') to track model-specific mistakes.
    """
    note_id = db.add_mistake(keyword, error_pattern, solution, target_model=target_model)
    return f"Successfully recorded mistake (ID: {note_id}, Model: {target_model}). Status is set to Draft. Ask the user or CLI to verify it."

@mcp.tool()
def propose_conflict_resolution(note_id_a: int, note_id_b: int, proposed_solution_c: str) -> str:
    """Propose a resolution for two conflicting wrong-answer notes A and B.

    This generates an option block for the user to select A, B, or a merged solution C.
    """
    # A와 B의 관계를 conflict로 기록
    db.add_relation(note_id_a, note_id_b, 'conflict')
    
    notes = db.list_all_notes()
    note_a = next((n for n in notes if n['id'] == note_id_a), None)
    note_b = next((n for n in notes if n['id'] == note_id_b), None)
    
    if not note_a or not note_b:
        return "Failed to propose resolution: One or both notes not found."

    report = (
        f"[Odab-Note Conflict Alert 🚨]\n"
        f"A conflict has been detected between note {note_id_a} and note {note_id_b}.\n\n"
        f"- Note A (Existing/Failed): [ID: {note_id_a}] Keyword: {note_a['keyword']}\n"
        f"  * Error: {note_a['error_pattern']}\n"
        f"  * Solution: {note_a['solution']}\n\n"
        f"- Note B (New/Recent): [ID: {note_id_b}] Keyword: {note_b['keyword']}\n"
        f"  * Error: {note_b['error_pattern']}\n"
        f"  * Solution: {note_b['solution']}\n\n"
        f"- Proposed Merged Option C:\n"
        f"  * Solution: {proposed_solution_c}\n\n"
        f"Please run the CLI to resolve this conflict:\n"
        f"  `odab-note resolve {note_id_a} {note_id_b} --solution-c \"{proposed_solution_c}\"`\n"
        f"Or choose to reject B and keep A by running:\n"
        f"  `odab-note delete {note_id_b}`"
    )
    return report

@mcp.tool()
def resolve_conflict_merge(keep_id: int, delete_id: int, merged_solution: str, merged_keyword: str) -> str:
    """Resolve a conflict by merging note `delete_id` into `keep_id` and updating it with `merged_solution`."""
    success = db.merge_and_replace_notes(keep_id, delete_id, merged_solution, merged_keyword)
    if success:
        return f"Successfully merged note {delete_id} into note {keep_id} with new solution."
    else:
        return "Failed to resolve conflict."

@mcp.tool()
def register_skill(name: str, cmd: str, desc: str) -> str:
    """Register a verified, reusable skill (workflow command).

    Use this to save successful execution commands or steps for future runs.
    """
    success = db.register_skill(name, cmd, desc)
    if success:
        return f"Successfully registered skill '{name}'."
    else:
        return f"Failed to register skill '{name}'."

@mcp.tool()
def match_error_trace(error_trace: str, target_model: str = "all", only_verified: bool = False) -> str:
    """Match a stack trace or compilation error against database regexes.

    Use this tool when an execution or compilation error occurs during coding to find a correction.
    """
    notes = db.match_error_trace(error_trace, target_model=target_model, only_verified=only_verified)
    if not notes:
        return "No matching past error patterns found."

    result = [f"Found {len(notes)} matching wrong-answer notes:"]
    for idx, note in enumerate(notes, 1):
        status = "Verified" if note['is_verified'] else "Draft"
        result.append(
            f"{idx}. [{status}] (Weight: {note['occurrence_count']}, Model: {note.get('target_model', 'all')})\n"
            f"   - Target Keyword: {note['keyword']}\n"
            f"   - Match Pattern: {note['error_pattern']}\n"
            f"   - Correct Solution: {note['solution']}"
        )
    return "\n\n".join(result)

@mcp.tool()
def auto_record(what_went_wrong: str, what_fixed_it: str, target_model: str = "all") -> str:
    """Quick-record a mistake from plain language. This is the 'odab pull' trigger.

    When the user says any of: '오답 넣어', 'odab pull', 'record that mistake', or similar:
    1. Analyze your recent conversation to identify the error and the fix.
    2. Call this tool with a plain-language description. No regex needed.
    3. The keyword is auto-generated from the description.

    Args:
        what_went_wrong: Plain description of the mistake (e.g. 'used LKS venv instead of local venv')
        what_fixed_it: Plain description of the fix (e.g. 'created dedicated .venv inside project dir')
        target_model: Which model made this mistake (e.g. 'gemini-3.5-flash', 'claude-3.5-sonnet', 'all')
    """
    # Auto-generate keyword from description
    clean = re.sub(r'[^\w\s]', '', what_went_wrong)
    words = [w.capitalize() for w in clean.split() if len(w) > 2][:4]
    keyword = "_".join(words) if words else "Unknown_Error"

    note_id = db.add_mistake(keyword, what_went_wrong, what_fixed_it, target_model=target_model)
    return (
        f"✅ Recorded (ID: {note_id}, Model: {target_model})\n"
        f"   Keyword: {keyword}\n"
        f"   Mistake: {what_went_wrong}\n"
        f"   Fix: {what_fixed_it}"
    )

@mcp.tool()
def revise_last(correction: str) -> str:
    """Revise the most recently recorded note based on user feedback.

    Trigger: '오답 수정', 'fix that note', 'that's wrong, change it to...'

    The user may say something like:
      '오답 수정 파일명을 그렇게 바꾸지 말라는거야 다른거랑 맞춰서 넣어야지'

    You must:
    1. Get the latest note from the database.
    2. Re-interpret the user's feedback to update the mistake description and/or fix.
    3. Call this tool with the corrected content.
    4. REPORT what changed to the user.

    Args:
        correction: The corrected content. Format as 'mistake: ... | fix: ...' or just the part to change.
    """
    latest = db.get_latest_note()
    if not latest:
        return "❌ No notes found to revise."

    note_id = latest['id']

    # Parse correction — if it contains 'mistake:' and 'fix:', split them
    if '|' in correction:
        parts = correction.split('|', 1)
        new_mistake = parts[0].strip()
        new_fix = parts[1].strip()
        db.update_note(note_id, error_pattern=new_mistake, solution=new_fix)
        # Regenerate keyword
        clean = re.sub(r'[^\w\s]', '', new_mistake)
        words = [w.capitalize() for w in clean.split() if len(w) > 2][:4]
        keyword = "_".join(words) if words else latest['keyword']
        db.update_note(note_id, keyword=keyword)
    else:
        # Update the solution/fix part only
        db.update_note(note_id, solution=correction)
        keyword = latest['keyword']
        new_mistake = latest['error_pattern']
        new_fix = correction

    return (
        f"📝 Revised note (ID: {note_id})\n"
        f"   Keyword: {keyword}\n"
        f"   Mistake: {new_mistake}\n"
        f"   Fix: {new_fix}"
    )

@mcp.tool()
def delete_last() -> str:
    """Delete the most recently recorded note.

    Trigger: '오답 삭제', 'delete that note', 'undo that'

    You must REPORT what was deleted to the user.
    """
    latest = db.get_latest_note()
    if not latest:
        return "❌ No notes found to delete."

    note_id = latest['id']
    keyword = latest['keyword']
    db.delete_note(note_id)
    return (
        f"🗑️ Deleted note (ID: {note_id})\n"
        f"   Keyword: {keyword}\n"
        f"   Was: {latest['error_pattern']}"
    )

def run():
    mcp.run()

if __name__ == "__main__":
    run()
