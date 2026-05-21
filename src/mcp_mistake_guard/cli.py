import click
from mcp_mistake_guard.database import MistakeGuardDB
from mcp_mistake_guard.server import mcp

db = MistakeGuardDB()

@click.group()
def main():
    """OdabNote CLI - Manage wrong-answer notes (오답노트) for AI Agents."""
    pass

@main.command()
def list():
    """List all wrong-answer notes."""
    notes = db.list_all_notes()
    if not notes:
        click.echo("No wrong-answer notes found.")
        return

    click.echo(f"{'ID':<4} | {'Keyword':<15} | {'Model':<15} | {'Count':<5} | {'Verified':<8} | {'Error Pattern'}")
    click.echo("-" * 95)
    for n in notes:
        verified = "Yes" if n['is_verified'] else "No"
        model = n.get('target_model', 'all')
        # 에러 패턴은 첫 줄만 요약해서 보여줌
        err_summary = n['error_pattern'].split('\n')[0]
        if len(err_summary) > 40:
            err_summary = err_summary[:37] + "..."
        click.echo(f"{n['id']:<4} | {n['keyword']:<15} | {model:<15} | {n['occurrence_count']:<5} | {verified:<8} | {err_summary}")

@main.command()
@click.argument('note_id', type=int)
def show(note_id):
    """Show details of a specific wrong-answer note."""
    notes = db.list_all_notes()
    note = next((n for n in notes if n['id'] == note_id), None)
    if not note:
        click.echo(f"Note with ID {note_id} not found.")
        return

    verified = "Yes" if note['is_verified'] else "No"
    click.echo(f"ID: {note['id']}")
    click.echo(f"Keyword: {note['keyword']}")
    click.echo(f"Occurrence Count: {note['occurrence_count']}")
    click.echo(f"Verified (Veto Passed): {verified}")
    click.echo("-" * 40)
    click.echo(f"Error Pattern:\n{note['error_pattern']}")
    click.echo("-" * 40)
    click.echo(f"Correct Solution:\n{note['solution']}")

@main.command()
@click.option('--keyword', '-k', required=True, help="Target keyword or file name.")
@click.option('--error', '-e', required=True, help="Error or mistake pattern.")
@click.option('--fix', '-f', required=True, help="Correct action or fix pattern.")
@click.option('--model', '-m', default='all', help="Target AI model (e.g. claude-3.5-sonnet, gemini-1.5-pro, all).")
def add(keyword, error, fix, model):
    """Add a new wrong-answer note manually (auto-verified)."""
    note_id = db.add_mistake(keyword, error, fix, target_model=model, is_verified=True)
    click.echo(f"Successfully added verified note (ID: {note_id}, Model: {model}).")

@main.command()
@click.argument('note_id', type=int)
def approve(note_id):
    """Approve a wrong-answer note (Veto Pass)."""
    if db.update_verification(note_id, True):
        click.echo(f"Note {note_id} approved successfully.")
    else:
        click.echo(f"Failed to approve note {note_id} (not found).")

@main.command()
@click.argument('note_id', type=int)
def delete(note_id):
    """Delete a wrong-answer note."""
    if db.delete_note(note_id):
        click.echo(f"Note {note_id} deleted successfully.")
    else:
        click.echo(f"Failed to delete note {note_id} (not found).")

@main.command()
@click.argument('note_id_a', type=int)
@click.argument('note_id_b', type=int)
@click.option('--solution-c', '-c', required=True, help="Proposed merged solution C.")
def resolve(note_id_a, note_id_b, solution_c):
    """Interactively resolve conflict between Note A and Note B."""
    notes = db.list_all_notes()
    note_a = next((n for n in notes if n['id'] == note_id_a), None)
    note_b = next((n for n in notes if n['id'] == note_id_b), None)
    
    if not note_a or not note_b:
        click.echo("Error: One or both notes not found.")
        return

    click.echo("\n[MistakeGuard Conflict Alert 🚨]")
    click.echo(f"- Note A (Existing/Failed): [ID: {note_id_a}] Keyword: {note_a['keyword']}")
    click.echo(f"  * Error: {note_a['error_pattern']}")
    click.echo(f"  * Solution: {note_a['solution']}")
    click.echo("-" * 40)
    click.echo(f"- Note B (New/Recent): [ID: {note_id_b}] Keyword: {note_b['keyword']}")
    click.echo(f"  * Error: {note_b['error_pattern']}")
    click.echo(f"  * Solution: {note_b['solution']}")
    click.echo("-" * 40)
    click.echo(f"- Proposed Merged Option C:")
    click.echo(f"  * Solution: {solution_c}")
    click.echo("-" * 40)

    click.echo("\nHow would you like to resolve this conflict?")
    click.echo("1. Keep Note A (Existing/Failed) and discard B")
    click.echo("2. Keep Note B (New/Recent) and discard A")
    click.echo("3. Merge A & B into Option C (New Solution)")
    
    choice = click.prompt("Enter option", type=click.Choice(['1', '2', '3']))
    
    if choice == '1':
        db.delete_note(note_id_b)
        click.echo(f"Resolved: Kept Note {note_id_a}, deleted Note {note_id_b}.")
    elif choice == '2':
        db.delete_note(note_id_a)
        # Note B를 verified 처리
        db.update_verification(note_id_b, True)
        click.echo(f"Resolved: Kept Note {note_id_b}, deleted Note {note_id_a}.")
    elif choice == '3':
        db.merge_and_replace_notes(note_id_a, note_id_b, solution_c, note_a['keyword'])
        click.echo(f"Resolved: Note {note_id_b} merged into Note {note_id_a} with Merged Solution C.")

@main.command()
@click.option('--days', '-d', default=7, type=int, help="Days threshold for time decay.")
def decay(days):
    """Manually apply time-decay to decrease weights of obsolete notes."""
    affected = db.apply_decay(days_threshold=days)
    click.echo(f"Applied time decay (Threshold: {days} days). Affected {affected} notes.")

@main.command()
@click.argument('from_id', type=int)
@click.argument('to_id', type=int)
@click.option('--type', '-t', default='triggers', type=click.Choice(['conflict', 'triggers']), help="Relation type (conflict or triggers).")
def link(from_id, to_id, type):
    """Link two notes with relation (triggers or conflict)."""
    db.add_relation(from_id, to_id, type)
    click.echo(f"Successfully linked Note {from_id} -> Note {to_id} as '{type}'.")

@main.command()
def graph():
    """Visualize relations and conflicts of wrong-answer notes as a network tree."""
    notes = db.list_all_notes()
    if not notes:
        click.echo("No wrong-answer notes to visualize.")
        return

    click.echo("\n[ Odab-Note Dependency & Conflict Graph 🕸️ ]\n")
    for note in notes:
        note_id = note['id']
        conflicts = db.get_related_notes_by_type(note_id, 'conflict')
        triggers = db.get_related_notes_by_type(note_id, 'triggers')
        
        # 모델 정보가 all이 아닐 경우 괄호로 추가 표시
        model_str = f" ({note['target_model']})" if note.get('target_model') and note['target_model'] != 'all' else ""
        verified_str = "✓" if note['is_verified'] else "✗"
        
        click.echo(f"● [ID: {note_id}] {note['keyword']}{model_str} (Count: {note['occurrence_count']}, Verified: {verified_str})")
        
        for c in conflicts:
            click.echo(f"  ├── ⚡ [Conflict] -> [ID: {c['id']}] {c['keyword']}")
        for t in triggers:
            click.echo(f"  └── 🔗 [Triggers] -> [ID: {t['id']}] {t['keyword']}")
        
        if not conflicts and not triggers:
            click.echo("  └── (No active relations)")
        click.echo("")

@main.command()
def run_server():
    """Run the MistakeGuard MCP server."""
    click.echo("Starting MistakeGuard MCP Server...")
    mcp.run()

if __name__ == "__main__":
    main()
