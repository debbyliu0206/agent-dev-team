from pydantic import BaseModel, Field
from typing import Literal

class Feature(BaseModel):
    id: str
    title: str
    description: str

class DataContract(BaseModel):
    node: str
    input: dict
    output: dict
    example: dict

class AcceptanceCriterion(BaseModel):
    id: str
    given: str
    when: str
    then_: str = Field(alias="then")

class TechStack(BaseModel):
    frontend: str
    backend: str
    db: str
    auth: str
    hosting: str

class Spec(BaseModel):
    features: list[Feature]
    data_contracts: list[DataContract]
    acceptance_criteria: list[AcceptanceCriterion]
    tech_stack: TechStack

class FileChange(BaseModel):
    path: str
    content: str
    action: Literal["create", "modify", "delete"]

class TestSuite(BaseModel):
    framework: str
    files: list[FileChange]
    covers_criteria: list[str]

class CodeChange(BaseModel):
    summary: str
    files: list[FileChange]

class TestFailure(BaseModel):
    test: str
    message: str
    trace: str

class TestResults(BaseModel):
    passed: int
    failed: int
    failures: list[TestFailure]
    logs: str

class Violation(BaseModel):
    rule: str
    file: str
    detail: str
    severity: Literal["block", "warn"]

class Review(BaseModel):
    compliant: bool
    violations: list[Violation]

class E2EFailure(BaseModel):
    criterion: str
    screenshot_path: str
    error: str

class E2EReport(BaseModel):
    stage: Literal["local", "production"]
    passed: int
    failed: int
    failures: list[E2EFailure]
