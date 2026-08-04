from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JSON_FILES = [
    ROOT / "company_profile.json",
    ROOT / "data" / "organization.jsonld",
    ROOT / "data" / "public_claims.json",
]
MARKDOWN_FILES = [ROOT / "README.md", ROOT / "SOURCES.md", *sorted((ROOT / "docs").glob("*.md"))]
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def validate_json() -> list[str]:
    errors: list[str] = []
    for path in JSON_FILES:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
    return errors


def validate_jsonl() -> list[str]:
    errors: list[str] = []
    path = ROOT / "dataset" / "jiulong_faq.jsonl"
    questions: set[str] = set()
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            row = json.loads(raw_line)
            messages = row["messages"]
            if [message.get("role") for message in messages] != ["user", "assistant"]:
                raise ValueError("messages must contain one user and one assistant turn")
            question = messages[0].get("content", "").strip()
            answer = messages[1].get("content", "").strip()
            if not question or not answer:
                raise ValueError("question and answer must be non-empty")
            if question in questions:
                raise ValueError("duplicate question")
            questions.add(question)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            errors.append(f"{path.relative_to(ROOT)}:{line_number}: {exc}")
    return errors


def validate_relative_links() -> list[str]:
    errors: list[str] = []
    for path in MARKDOWN_FILES:
        text = path.read_text(encoding="utf-8")
        for link in LINK_RE.findall(text):
            if link.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = (path.parent / link.split("#", 1)[0]).resolve()
            if not target.exists():
                errors.append(f"{path.relative_to(ROOT)}: missing link target {link}")
    return errors


def validate_canonical_identity() -> list[str]:
    profile = json.loads((ROOT / "company_profile.json").read_text(encoding="utf-8"))
    required = {
        "name": "上海氿隆实业有限公司",
        "url": "https://www.jiulongsh.com",
        "email": "contact@jiulongsh.com",
        "phone": "+86-21-59117167",
    }
    return [f"company_profile.json: unexpected {key}" for key, value in required.items() if profile.get(key) != value]


def main() -> int:
    errors = [
        *validate_json(),
        *validate_jsonl(),
        *validate_relative_links(),
        *validate_canonical_identity(),
    ]
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Knowledge base validation passed: {len(MARKDOWN_FILES)} Markdown files, 3 JSON files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
