import sys
from langgraph.graph import StateGraph, END

from state_schema import CouncilState
from memory_manager import load_historical_memory, persist_session_knowledge

from agents.requirements import run_requirements_agent
from agents.security import run_security_agent
from agents.scrum_master import run_scrum_master_agent
from agents.coder import run_coding_agent
from agents.qa import run_qa_agent
from agents.promotion import run_promotion_agent

workflow = StateGraph(CouncilState)

workflow.add_node('requirements_refiner', run_requirements_agent)
workflow.add_node('security_hardening', run_security_agent)
workflow.add_node('scrum_master', run_scrum_master_agent)
workflow.add_node('coder', run_coding_agent)
workflow.add_node('qa_validator', run_qa_agent)
workflow.add_node('promotion_gate', run_promotion_agent)

workflow.set_entry_point('requirements_refiner')
workflow.add_edge('requirements_refiner', 'security_hardening')
workflow.add_edge('security_hardening', 'scrum_master')
workflow.add_edge('scrum_master', 'coder')
workflow.add_edge('coder', 'qa_validator')


MAX_REPAIR_ATTEMPTS = 5


def route_qa_verdict(state: CouncilState):
    status = state.get('test_results', {}).get('status', 'FAIL')
    if status != 'FAIL':
        return 'promotion_gate'
    if state.get('repair_attempts', 0) >= MAX_REPAIR_ATTEMPTS:
        print('🛑 Repair attempts exhausted. Sending failing build to the promotion gate for rejection.')
        return 'promotion_gate'
    print('⚠️ QA validation suite failed. Routing back to coder.')
    return 'coder'


workflow.add_conditional_edges(
    'qa_validator',
    route_qa_verdict,
    {
        'coder': 'coder',
        'promotion_gate': 'promotion_gate'
    }
)
workflow.add_edge('promotion_gate', END)

app = workflow.compile()


def start_execution_harness():
    loaded_memory = load_historical_memory()
    print('📖 Loaded global context files from storage ecosystem successfully.')

    print('\n💬 --- Welcome to the Agile Council Configuration Matrix ---')
    user_story = input('⌨️ Provide input User Story: ').strip()
    if not user_story:
        user_story = 'As a Customer, I want to securely pay via an API endpoint, so that my account credentials remain encrypted.'
    
    lang_stack = input('⌨️ Choose target language [Python/JavaScript/Go] (Default: Python): ').strip()
    if not lang_stack:
        lang_stack = 'Python'

    initial_input: CouncilState = {
        'project_name': 'modular_billing_system',
        'target_lang': lang_stack,
        'raw_user_story': user_story,
        'historical_memory': loaded_memory,
        'functional_specs': '',
        'tdd_criteria': '',
        'security_standards': '',
        'backlog': [],
        'current_task': {},
        'source_code': {},
        'test_results': {},
        'bug_list': [],
        'release_environment': 'dev',
        'promotion_approved': False,
        'repair_attempts': 0
    }
    
    print('\n🚀 Triggering modular state workflow engine...')
    final_output = app.invoke(initial_input, {'recursion_limit': 60})
    
    persist_session_knowledge(
        project_name=final_output['project_name'],
        raw_story=final_output['raw_user_story'],
        specs=final_output['functional_specs'],
        approved=final_output['promotion_approved']
    )
    print('\n[✨ Success] Execution finished cleanly.')


if __name__ == '__main__':
    start_execution_harness()
