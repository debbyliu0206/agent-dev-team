import logging
import time
from datetime import datetime
from typing import Optional, Dict

from google.adk.agents.callback_context import CallbackContext
from google.genai import types

logger = logging.getLogger('agent_progress')

class ProgressTracker:
    def __init__(self) -> None:
        self._start_times: Dict[str, float] = {}

    def make_before_callback(self, agent_name: str, description: str):
        async def before_callback(callback_context: CallbackContext) -> Optional[types.Content]:
            self._start_times[agent_name] = time.time()
            ts = datetime.now().strftime('%H:%M:%S')
            logger.info(f"[{ts}] {agent_name} started — {description}")
            return None
        return before_callback

    def make_after_callback(self, agent_name: str, output_key: Optional[str] = None):
        async def after_callback(callback_context: CallbackContext) -> Optional[types.Content]:
            start_time = self._start_times.get(agent_name)
            duration = time.time() - start_time if start_time else 0.0
            
            ts = datetime.now().strftime('%H:%M:%S')
            
            summary = ""
            state = getattr(callback_context, 'state', {})
            
            if output_key and output_key in state:
                out_val = state[output_key]
                if out_val:
                    summary_str = str(out_val)
                    if len(summary_str) > 100:
                        summary_str = summary_str[:97] + "..."
                    summary = f" — {summary_str}"
            
            # Special case for TestRunner
            if "test_runner" in agent_name and 'test_results' in state:
                test_results = state['test_results']
                if isinstance(test_results, dict):
                    passed = test_results.get('passed', 0)
                    failed = test_results.get('failed', 0)
                    summary = f" — tests passed: {passed}, failed: {failed}"
                else:
                    summary = f" — {test_results}"
                    
            # Special case for build loop iterations
            if 'iteration' in state:
                summary = f" — iteration: {state['iteration']}" + summary
                
            logger.info(f"[{ts}] {agent_name} done ({duration:.1f}s){summary}")
            return None
        return after_callback

AGENT_DESCRIPTIONS = {
    'pm': 'analyzing requirements',
    'architect': 'designing API contract + component layout',
    'test_writer': 'generating test pyramid',
    'coder': 'writing implementation code',
    'code_applier': 'applying code changes to disk',
    'dep_installer': 'installing dependencies into target venv',
    'test_runner': 'running pytest',
    'test_runner_2': 'running pytest (post-fix)',
    'test_fixer': 'repairing test mechanics',
    'keep_best': 'evaluating best snapshot',
    'spec_reviewer': 'reviewing code against spec',
    'gate': 'checking escalation criteria',
    'e2e_qa': 'running Playwright E2E tests',
}

def _compose(existing, new_cb):
    """Merge a new callback with whatever is already registered (ADK accepts a
    list). Preserves guard callbacks like the spec gate instead of clobbering
    them; the progress callback runs first since it never returns content."""
    if existing is None:
        return new_cb
    existing = existing if isinstance(existing, list) else [existing]
    return [new_cb] + existing


def register_all_callbacks(root_agent, tracker: ProgressTracker):
    """Recursively register callbacks on all agents in the tree."""
    agent_name = getattr(root_agent, 'name', 'unknown')
    description = AGENT_DESCRIPTIONS.get(agent_name, f"running {agent_name}")

    root_agent.before_agent_callback = _compose(
        root_agent.before_agent_callback,
        tracker.make_before_callback(agent_name, description))
    root_agent.after_agent_callback = _compose(
        root_agent.after_agent_callback,
        tracker.make_after_callback(agent_name, getattr(root_agent, 'output_key', None)))
    
    sub_agents = getattr(root_agent, 'sub_agents', None)
    if sub_agents:
        for sub_agent in sub_agents:
            register_all_callbacks(sub_agent, tracker)
