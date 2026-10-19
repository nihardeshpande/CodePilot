"""API request and response models."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

MAX_DIFF_LENGTH = 100_000


class ReviewRequest(BaseModel):
    """A unified diff submitted for review."""

    diff: str = Field(
        min_length=1,
        max_length=MAX_DIFF_LENGTH,
        description="Unified diff text to review.",
    )

    @field_validator("diff")
    @classmethod
    def diff_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("diff must not be blank")
        return value


class Finding(BaseModel):
    """A single issue identified in the submitted diff."""

    severity: Literal["low", "medium", "high", "critical"]
    file: str
    line: int = Field(ge=1)
    title: str
    explanation: str
    suggestion: str


class ReviewResponse(BaseModel):
    """Summary and findings produced by the review service."""

    summary: str
    findings: list[Finding]
