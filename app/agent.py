import os
import pathlib
from dotenv import load_dotenv
load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents import SequentialAgent, LoopAgent
from google.adk.apps import App

from .agents.pm import create_pm_agent
from .agents.architect import create_architect_agent
from .agents.test_writer import create_test_writer_agent
from .agents.coder import create_coder_agent
from .agents.spec_reviewer import create_spec_reviewer_agent
from .agents.e2e_qa import create_e2e_qa_agent
from .agents.escalation import EscalationChecker
from .agents.test_runner import TestRunner
from .agents.code_applier import CodeApplier
from .agents.dep_installer import DepInstaller
from .agents.test_fixer import create_test_fixer_agent
from .agents.keep_best import KeepBest

root_agent = SequentialAgent(name="dev_team", sub_agents=[
    create_pm_agent(),
    create_architect_agent(),
    create_test_writer_agent(),
    LoopAgent(name="build_loop", max_iterations=5, sub_agents=[
        create_coder_agent(),
        CodeApplier(name="code_applier"),
        DepInstaller(name="dep_installer"),
        TestRunner(name="test_runner"),
        create_test_fixer_agent(),
        TestRunner(name="test_runner_2"),
        KeepBest(name="keep_best"),
        create_spec_reviewer_agent(),
        EscalationChecker(name="gate"),
    ]),
    create_e2e_qa_agent(),
])

app = App(name="app", root_agent=root_agent)
