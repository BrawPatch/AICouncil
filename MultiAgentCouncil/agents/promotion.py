def run_promotion_agent(state):
    passed = state.get("test_results", {}).get("status") == "PASS"
    if passed:
        print("✅ [Promotion Gate] Quality gate passed. Build approved.")
    else:
        print("⛔ [Promotion Gate] Quality gate failed. Promotion rejected.")
    return {"promotion_approved": passed, "release_environment": "dev"}
