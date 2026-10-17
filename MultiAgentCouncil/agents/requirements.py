from llm_client import query_local_llm, CHAIRMAN_MODEL


def run_requirements_agent(state):
    print("📝 [Requirements Refiner] Expanding the user story into specs...")
    story = state["raw_user_story"]
    lang = state["target_lang"]
    memory = state.get("historical_memory", "")

    specs = query_local_llm(CHAIRMAN_MODEL, f"""You are a business analyst. Turn this user story into concise
functional specifications for a {lang} implementation. Use short bullet points only.

User story: {story}

Prior project context (may be empty):
{memory}
""")
    criteria = query_local_llm(CHAIRMAN_MODEL, f"""Write TDD acceptance criteria for these specifications as a
numbered list of testable Given/When/Then statements.

{specs}
""")
    return {"functional_specs": specs, "tdd_criteria": criteria}
