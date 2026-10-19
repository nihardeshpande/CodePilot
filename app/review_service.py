"""Deterministic, rule-based diff analysis."""

import re

from app.schemas import Finding, ReviewResponse

HUNK_HEADER = re.compile(
    r"^@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@"
)
EVAL_CALL = re.compile(r"\beval\s*\(")


def analyze_diff(diff: str) -> ReviewResponse:
    """Find supported patterns in added lines without executing any code."""
    findings: list[Finding] = []
    current_file = ""
    new_line_number: int | None = None
    old_lines_remaining = 0
    new_lines_remaining = 0

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            new_line_number = None
            continue

        hunk = HUNK_HEADER.match(line)
        if hunk:
            old_lines_remaining = int(hunk.group(1) or 1)
            new_line_number = int(hunk.group(2))
            new_lines_remaining = int(hunk.group(3) or 1)
            continue

        if old_lines_remaining == 0 and new_lines_remaining == 0:
            new_line_number = None

        if new_line_number is None and line.startswith("+++ "):
            current_file = line[4:]
            if current_file.startswith("b/"):
                current_file = current_file[2:]
            continue

        if new_line_number is None:
            continue

        if line.startswith("+"):
            if EVAL_CALL.search(line[1:]):
                findings.append(
                    Finding(
                        severity="high",
                        file=current_file,
                        line=new_line_number,
                        title="Dynamic code evaluation",
                        explanation=(
                            "This added line calls eval(), which can execute "
                            "arbitrary code if its input is not fully trusted."
                        ),
                        suggestion=(
                            "Avoid eval(); use an explicit parser or a "
                            "restricted mapping of supported operations."
                        ),
                    )
                )
            new_line_number += 1
            new_lines_remaining -= 1
        elif line.startswith(" "):
            new_line_number += 1
            old_lines_remaining -= 1
            new_lines_remaining -= 1
        elif line.startswith("\\"):
            continue
        elif line.startswith("-"):
            old_lines_remaining -= 1
        else:
            new_line_number = None

    if findings:
        count = len(findings)
        noun = "issue" if count == 1 else "issues"
        summary = f"Found {count} potential {noun} in the diff."
    else:
        summary = "No supported issues found in this diff."

    return ReviewResponse(summary=summary, findings=findings)
