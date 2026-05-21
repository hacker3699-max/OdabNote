from mcp.server.fastmcp import FastMCP
from odab_note.database import OdabNoteDB
import json

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

def run():
    mcp.run()

if __name__ == "__main__":
    run()
