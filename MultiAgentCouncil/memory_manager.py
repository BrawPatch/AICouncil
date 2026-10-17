from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
MEMORY_STORE_DIR = BASE_DIR / 'MemoryStore'
CONTEXT_FILE = MEMORY_STORE_DIR / 'Context.md'
HISTORY_FILE = MEMORY_STORE_DIR / 'ChatHistory.md'

MEMORY_STORE_DIR.mkdir(parents=True, exist_ok=True)


def load_historical_memory() -> str:
    memory_blocks = []
    if CONTEXT_FILE.exists():
        try:
            with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
                memory_blocks.append(f'### [HISTORICAL GLOBAL CONTEXT]\n{f.read()}')
        except Exception as e:
            print(f'⚠️ Error reading global context file: {e}')
            
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history_data = f.read()
                tail_lines = history_data.split('\n')[-100:]
                memory_blocks.append(f'### [RECENT CHAT HISTORY RECORDS]\n...\n' + '\n'.join(tail_lines))
        except Exception as e:
            print(f'⚠️ Error reading execution history logs: {e}')
            
    return '\n\n'.join(memory_blocks) if memory_blocks else 'No historical memory discovered.'


def persist_session_knowledge(project_name: str, raw_story: str, specs: str, approved: bool):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status_str = 'APPROVED & DEPLOYED' if approved else 'PAUSED / REJECTED'
    
    context_markdown = (
        f'# System Operational Context Snapshot\n'
        f'- **Last Active Project:** `{project_name}`\n'
        f'- **Last Analyzed Timestamp:** {timestamp}\n'
        f'- **Status Gate Result:** `{status_str}`\n\n'
        f'## Active Technical Specification Matrix\n{specs}\n'
    )
    
    try:
        with open(CONTEXT_FILE, 'w', encoding='utf-8') as f:
            f.write(context_markdown.strip() + '\n')
        print(f'💾 Global state snapshot written to: {CONTEXT_FILE}')
    except Exception as e:
        print(f'❌ Failed to persist context file: {e}')

    promo_str = 'PASSED' if approved else 'FAILED / HALTED'
    history_entry = (
        f'\n## Session Audit Entry: {timestamp}\n'
        f'- **Target Project Workspace:** `{project_name}`\n'
        f'- **Source Input Story Card:** \"{raw_story}\"\n'
        f'- **Quality Promotion Gate Sign-Off:** `{promo_str}`\n'
        f'---\n'
    )
    
    try:
        if not HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                f.write('# Chat Session Execution History Logs\nAll pipeline run history is logged here automatically.\n')
        with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
            f.write(history_entry)
        print(f'📝 Incremental run logging entry appended to: {HISTORY_FILE}')
    except Exception as e:
        print(f'❌ Failed to append log entry: {e}')
