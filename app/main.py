"""FastAPI application and review endpoint."""

from fastapi import FastAPI

from app.review_service import analyze_diff
from app.schemas import ReviewRequest, ReviewResponse

app = FastAPI(
    title="CodePilot",
    description="A deterministic, rule-based code review API.",
    version="0.1.0",
)


@app.post("/api/v1/reviews", response_model=ReviewResponse)
def create_review(request: ReviewRequest) -> ReviewResponse:
    """Analyze a submitted diff and return supported findings."""
    return analyze_diff(request.diff)
