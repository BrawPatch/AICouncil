import json
import re

from llm_client import query_local_llm, CHAIRMAN_MODEL


def _parse_tasks(raw: str):
    """Extracts a JSON array of tasks from an LLM reply, tolerating code fences and chatter."""
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        return []
    try:
        tasks = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    return [t for t in tasks if isinstance(t, dict) and t.get("title")]


def run_scrum_master_agent(state):
    print("📋 [Scrum Master] Building the backlog...")
    raw = query_local_llm(CHAIRMAN_MODEL, f"""You are a Scrum Master. Break the work below into 1 to 3 small,
independently testable tasks. Reply with ONLY a JSON array; each item has the keys "title" and "description".

Specifications:
{state["functional_specs"]}

Acceptance criteria:
{state["tdd_criteria"]}
""")
    backlog = _parse_tasks(raw)
    if not backlog:
        backlog = [{"title": "Implement user story", "description": state["raw_user_story"]}]
    return {"backlog": backlog, "current_task": backlog[0], "repair_attempts": 0}
