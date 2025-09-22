#!/usr/bin/env python3
"""Convert GitHub issue form responses into daily KPI CSV rows.

This script is intended to run inside a GitHub Actions workflow:
  python scripts/issue_to_csv.py --input issue_body.txt --csv logs/daily.csv

If the target CSV does not exist, the header row will be created automatically.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, List, Optional

CSV_HEADER = [
    "date",
    "deru1000_solved",
    "deru1000_understood",
    "vocab_reviewed",
    "vocab_understood",
    "ichiojin_grammar_hours",
    "grammar_understood_ratio",
]

FIELD_MAP = {
    "date": "date",
    "deru1000 solved": "deru1000_solved",
    "deru1000 understood": "deru1000_understood",
    "vocabulary reviewed": "vocab_reviewed",
    "vocabulary understood": "vocab_understood",
    "grammar study hours": "ichiojin_grammar_hours",
    "grammar understood ratio": "grammar_understood_ratio",
}

INT_FIELDS = {
    "deru1000_solved",
    "deru1000_understood",
    "vocab_reviewed",
    "vocab_understood",
}

FLOAT_FIELDS = {
    "ichiojin_grammar_hours",
    "grammar_understood_ratio",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="-",
        help="Path to the issue body text. Use '-' to read from STDIN.",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("logs/daily.csv"),
        help="Destination CSV file",
    )
    return parser.parse_args()


def read_issue_body(path: str) -> str:
    if path == "-":
        import sys

        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def extract_sections(markdown: str) -> Dict[str, str]:
    sections: Dict[str, List[str]] = {}
    current_key: Optional[str] = None
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if line.startswith("### "):
            current_key = line[4:].strip().lower()
            sections[current_key] = []
            continue
        if current_key is None:
            continue
        sections[current_key].append(raw_line)

    result: Dict[str, str] = {}
    for key, lines in sections.items():
        # Keep first non-empty meaningful line, strip Markdown placeholders.
        cleaned = []
        for value_line in lines:
            stripped = value_line.strip()
            if not stripped:
                continue
            if stripped == "_No response_":
                continue
            cleaned.append(stripped)
        result[key] = "\n".join(cleaned).strip()
    return result


def normalise_field(name: str, value: Optional[str]) -> str:
    if value is None or not value.strip():
        return ""
    canonical = FIELD_MAP[name]
    text = value.strip()
    if canonical in INT_FIELDS:
        try:
            number = int(float(text))
        except ValueError as exc:
            raise ValueError(f"Invalid integer for '{name}': {value}") from exc
        return str(number)
    if canonical in FLOAT_FIELDS:
        try:
            number = float(text)
        except ValueError as exc:
            raise ValueError(f"Invalid float for '{name}': {value}") from exc
        # Compact formatting: remove trailing zeros while keeping at least one decimal if needed
        formatted = f"{number:.4f}".rstrip("0").rstrip(".")
        return formatted
    return text


def convert_issue_to_row(sections: Dict[str, str]) -> Dict[str, str]:
    row: Dict[str, str] = {column: "" for column in CSV_HEADER}
    for key, canonical in FIELD_MAP.items():
        if key not in sections:
            continue
        row[canonical] = normalise_field(key, sections[key])
    missing = [col for col in ("date", "deru1000_solved", "vocab_reviewed", "ichiojin_grammar_hours") if not row[col]]
    if missing:
        raise ValueError(
            "Missing required fields: " + ", ".join(missing)
        )
    return row


def append_row(csv_path: Path, row: Dict[str, str]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_HEADER)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main() -> None:
    args = parse_args()
    body = read_issue_body(args.input)
    sections = extract_sections(body)
    row = convert_issue_to_row(sections)
    append_row(args.csv, row)
    print(f"Appended daily log for {row['date']} -> {args.csv}")


if __name__ == "__main__":
    main()
