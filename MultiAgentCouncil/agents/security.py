from llm_client import query_local_llm, SECURITY_MODEL


def run_security_agent(state):
    print("🔐 [Security Hardening] Defining security standards...")
    standards = query_local_llm(SECURITY_MODEL, f"""You are an application security engineer. For the specification
below, list the concrete security requirements the implementation must meet (input validation, secrets handling,
authentication, error handling, injection, logging). Be specific and brief.

{state["functional_specs"]}
""")
    return {"security_standards": standards}
