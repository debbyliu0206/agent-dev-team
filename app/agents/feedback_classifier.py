import pathlib
from google.adk.agents import Agent


def _prompt(name):
    return (pathlib.Path(__file__).parent / "prompts" / f"{name}.md").read_text(encoding="utf-8")


def create_feedback_classifier_agent():
    return Agent(
        name="feedback_classifier",
        model="gemini-2.5-flash",
        description="Classifies user feedback as bug, new requirement, or ambiguous",
        instruction=_prompt("feedback_classifier"),
        output_key="feedback_classification",
    )
