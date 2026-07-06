"""Root agent definition — the full software development pipeline.

Pipeline: PM → Architect → TestWriter → BuildLoop → UserTestGuide → E2E-QA → FeedbackClassifier

The build loop uses a convergent strategy learned from dogfooding: TDD (tests
written before code), keep-best rollback on regression, spec-reviewer to catch
drift, and a circuit breaker that detects stalled iterations.

Security guardrails are wired directly into the deterministic agents inside the
loop (CodeApplier scans code + secrets, DepInstaller verifies packages against
PyPI) so that unsafe artifacts never reach disk — regardless of what the LLM
produces.
"""

import logging
import pathlib
from dotenv import load_dotenv
load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents import SequentialAgent, LoopAgent
from google.adk.apps import App

from .agents.pm import create_pm_agent
from .agents.spec_gate import require_complete_spec
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
from .agents.user_test_guide import create_user_test_guide_agent
from .agents.feedback_classifier import create_feedback_classifier_agent
from .callbacks.progress import ProgressTracker, register_all_callbacks

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()],
)

# Phases 2-4 wrapped in one workflow agent so a single before_agent_callback
# (the spec gate) can hold the ENTIRE build back while the PM interview is
# still mid-conversation. See app/agents/spec_gate.py for why this must be a
# callback on the wrapper rather than a sub-agent setting end_invocation.
build_pipeline = SequentialAgent(
    name="build_pipeline",
    before_agent_callback=require_complete_spec,
    sub_agents=[
        create_architect_agent(),
        # Phase 2: TDD — write tests BEFORE code so the loop has a clear target
        create_test_writer_agent(),
        # Phase 3: Build loop — converge to green via code→test→fix→keep-best
        LoopAgent(name="build_loop", max_iterations=5, sub_agents=[
            create_coder_agent(),
            CodeApplier(name="code_applier"),       # security: code_scanner + secret_scanner
            DepInstaller(name="dep_installer"),      # security: dependency_checker (slopsquatting)
            TestRunner(name="test_runner"),
            create_test_fixer_agent(),
            TestRunner(name="test_runner_2"),
            KeepBest(name="keep_best"),              # rollback if test count regressed
            create_spec_reviewer_agent(),
            EscalationChecker(name="gate"),          # circuit breaker: stall + drift detection
        ]),
        # Phase 4: Human-in-the-loop verification
        create_user_test_guide_agent(),              # plain-language testing guide for non-tech users
        create_e2e_qa_agent(),                       # automated browser testing via Playwright MCP
        create_feedback_classifier_agent(),          # routes feedback → bug fix vs spec update
    ],
)

root_agent = SequentialAgent(name="dev_team", sub_agents=[
    # Phase 1: Spec — multi-turn discovery interview; the spec gate on
    # build_pipeline keeps everything below on hold until the spec is final.
    create_pm_agent(),
    build_pipeline,
])

tracker = ProgressTracker()
register_all_callbacks(root_agent, tracker)

app = App(name="app", root_agent=root_agent)
