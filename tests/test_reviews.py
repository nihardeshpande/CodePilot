"""Tests for the review endpoint and its response contract."""

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import MAX_DIFF_LENGTH

client = TestClient(app)


def test_valid_request_returns_finding_with_expected_structure() -> None:
    response = client.post(
        "/api/v1/reviews",
        json={
            "diff": (
                "diff --git a/example.py b/example.py\n"
                "--- a/example.py\n"
                "+++ b/example.py\n"
                "@@ -1,0 +1,2 @@\n"
                "+value = 1\n"
                "+result = eval(user_input)\n"
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == "Found 1 potential issue in the diff."
    assert len(body["findings"]) == 1
    assert body["findings"][0] == {
        "severity": "high",
        "file": "example.py",
        "line": 2,
        "title": "Dynamic code evaluation",
        "explanation": (
            "This added line calls eval(), which can execute arbitrary code "
            "if its input is not fully trusted."
        ),
        "suggestion": (
            "Avoid eval(); use an explicit parser or a restricted mapping of "
            "supported operations."
        ),
    }


def test_added_line_starting_with_plus_is_analyzed() -> None:
    response = client.post(
        "/api/v1/reviews",
        json={
            "diff": (
                "diff --git a/example.py b/example.py\n"
                "--- a/example.py\n"
                "+++ b/example.py\n"
                "@@ -1,0 +1 @@\n"
                "++eval(user_input)\n"
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["findings"][0]["line"] == 1


def test_review_endpoint_is_documented() -> None:
    docs_response = client.get("/docs")
    openapi_response = client.get("/openapi.json")

    assert docs_response.status_code == 200
    assert openapi_response.status_code == 200
    assert "/api/v1/reviews" in openapi_response.json()["paths"]


def test_empty_diff_is_rejected() -> None:
    response = client.post("/api/v1/reviews", json={"diff": ""})

    assert response.status_code == 422


def test_whitespace_only_diff_is_rejected() -> None:
    response = client.post("/api/v1/reviews", json={"diff": " \n\t"})

    assert response.status_code == 422


def test_missing_diff_is_rejected() -> None:
    response = client.post("/api/v1/reviews", json={})

    assert response.status_code == 422


def test_oversized_diff_is_rejected() -> None:
    response = client.post(
        "/api/v1/reviews",
        json={"diff": "x" * (MAX_DIFF_LENGTH + 1)},
    )

    assert response.status_code == 422


def test_diff_without_supported_issue_returns_empty_findings() -> None:
    response = client.post(
        "/api/v1/reviews",
        json={
            "diff": (
                "diff --git a/example.py b/example.py\n"
                "--- a/example.py\n"
                "+++ b/example.py\n"
                "@@ -1,0 +1 @@\n"
                "+value = 1\n"
            )
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "summary": "No supported issues found in this diff.",
        "findings": [],
    }


def test_analyzer_failure_returns_server_error(monkeypatch) -> None:
    def fail_analysis(_diff: str):
        raise RuntimeError("unexpected analyzer failure")

    monkeypatch.setattr("app.main.analyze_diff", fail_analysis)
    test_client = TestClient(app, raise_server_exceptions=False)

    response = test_client.post("/api/v1/reviews", json={"diff": "valid diff"})

    assert response.status_code == 500
