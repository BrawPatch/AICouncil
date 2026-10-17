from typing import TypedDict, List, Dict, Any, Literal

class CouncilState(TypedDict):
    project_name: str
    target_lang: str
    raw_user_story: str
    historical_memory: str
    functional_specs: str
    tdd_criteria: str
    security_standards: str
    backlog: List[Dict[str, Any]]
    current_task: Dict[str, Any]
    source_code: Dict[str, str]
    test_results: Dict[str, Any]
    bug_list: List[Dict[str, Any]]
    release_environment: Literal['dev', 'test', 'production']
    promotion_approved: bool
    repair_attempts: int
