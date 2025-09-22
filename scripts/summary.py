#!/usr/bin/env python3
"""Generate KPI summary markdown from daily study logs and update README.

Usage (local):
    python scripts/summary.py --csv logs/daily.csv

The script expects the CSV to contain the columns:
    date, deru1000_solved, deru1000_understood,
    vocab_reviewed, vocab_understood,
    ichiojin_grammar_hours, grammar_understood_ratio

It replaces the block between <!--KPIS--> and <!--/KPIS--> in README.md.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Optional

GOAL_DERU1000_TOTAL = 1000
GOAL_VOCAB_PER_DAY = 200
GOAL_VOCAB_TOTAL = 2000
PHASE1_START = date(2025, 9, 22)
PHASE1_END = date(2025, 12, 31)


@dataclass
class DailyRecord:
    date: date
    deru1000_solved: int
    deru1000_understood: Optional[float]
    vocab_reviewed: int
    vocab_understood: Optional[float]
    ichiojin_grammar_hours: float
    grammar_understood_ratio: Optional[float]


def parse_int(value: str) -> int:
    if value is None:
        return 0
    text = value.strip()
    if not text:
        return 0
    return int(float(text))


def parse_float(value: str) -> float:
    if value is None:
        return 0.0
    text = value.strip()
    if not text:
        return 0.0
    return float(text)


def parse_optional_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    text = value.strip()
    if not text or text.lower() == "nan":
        return None
    return float(text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("logs/daily.csv"),
        help="Path to daily KPI CSV log",
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=Path("README.md"),
        help="README file to update",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print KPI block without writing the README",
    )
    return parser.parse_args()


def load_records(csv_path: Path) -> List[DailyRecord]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    records: List[DailyRecord] = []
    with csv_path.open(newline="") as fp:
        reader = csv.DictReader(fp)
        expected = {
            "date",
            "deru1000_solved",
            "deru1000_understood",
            "vocab_reviewed",
            "vocab_understood",
            "ichiojin_grammar_hours",
            "grammar_understood_ratio",
        }
        missing = expected.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"CSV missing columns: {', '.join(sorted(missing))}"
            )

        for row in reader:
            if not row["date"]:
                continue
            record_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
            hours_value = parse_optional_float(row.get("ichiojin_grammar_hours"))
            records.append(
                DailyRecord(
                    date=record_date,
                    deru1000_solved=parse_int(row["deru1000_solved"]),
                    deru1000_understood=parse_optional_float(
                        row.get("deru1000_understood")
                    ),
                    vocab_reviewed=parse_int(row["vocab_reviewed"]),
                    vocab_understood=parse_optional_float(
                        row.get("vocab_understood")
                    ),
                    ichiojin_grammar_hours=hours_value if hours_value is not None else 0.0,
                    grammar_understood_ratio=parse_optional_float(
                        row.get("grammar_understood_ratio")
                    ),
                )
            )

    if not records:
        raise ValueError("No daily records found in CSV")

    records.sort(key=lambda r: r.date)
    return records


def select_window(records: Iterable[DailyRecord], days: int) -> List[DailyRecord]:
    records = list(records)
    end = records[-1].date
    start = end - timedelta(days=days - 1)
    return [r for r in records if r.date >= start]


def format_progress(current: float, goal: float, width: int = 24, include_percent: bool = True) -> str:
    if goal <= 0:
        return "-"
    ratio = max(0.0, min(current / goal, 1.0))
    filled = math.floor(ratio * width)
    bar = "#" * filled + "." * (width - filled)
    percent = ratio * 100
    if include_percent:
        return f"`{bar}` {percent:5.1f}%"
    return f"`{bar}`"


def human_hours(value: float) -> str:
    return f"{value:.1f}h"


def human_int(value: float) -> str:
    return f"{int(round(value)):,}"


def latest_non_null(records: Iterable[DailyRecord], attribute: str) -> Optional[float]:
    for record in reversed(list(records)):
        value = getattr(record, attribute)
        if value is not None:
            return value
    return None


def format_goal_progress_row(label: str, current: Optional[float], goal: float) -> str:
    if current is None:
        progress = "-"
        detail = "-"
    else:
        bar = format_progress(current, goal, include_percent=False)
        ratio = max(0.0, min(current / goal, 1.0))
        percent = ratio * 100
        progress = f"{bar} {percent:.1f}%"
        detail = f"{human_int(current)} / {human_int(goal)}"
    return f"| **{label}** | {progress} | {detail} |"


def format_ratio_progress_row(label: str, ratio: Optional[float]) -> str:
    if ratio is None:
        progress = "-"
    else:
        clamped = max(0.0, min(ratio, 1.0))
        bar = format_progress(clamped, 1.0, include_percent=False)
        percent = clamped * 100
        progress = f"{bar} {percent:.1f}%"
    detail = "-"
    return f"| **{label}** | {progress} | {detail} |"


def render_markdown(records: List[DailyRecord]) -> str:
    latest = records[-1]
    window7 = select_window(records, days=7)
    total_solved = sum(r.deru1000_solved for r in records)
    total_vocab = sum(r.vocab_reviewed for r in records)
    total_grammar_hours = sum(r.ichiojin_grammar_hours for r in records)

    seven_day_solved = sum(r.deru1000_solved for r in window7)
    seven_day_vocab = sum(r.vocab_reviewed for r in window7)
    seven_day_hours = sum(r.ichiojin_grammar_hours for r in window7)

    phase_total_days = max((PHASE1_END - PHASE1_START).days, 0)
    if phase_total_days > 0:
        phase_elapsed_raw = (latest.date - PHASE1_START).days
        phase_elapsed_clamped = min(max(phase_elapsed_raw, 0), phase_total_days)
        phase_elapsed_percent = (phase_elapsed_clamped / phase_total_days) * 100
        phase_progress_bar = format_progress(
            phase_elapsed_clamped, phase_total_days, include_percent=False
        )
    else:
        phase_elapsed_clamped = 0
        phase_elapsed_percent = 0.0
        phase_progress_bar = "-"

    snapshot_records = sorted(window7, key=lambda r: r.date, reverse=True)

    lines = []
    lines.append("### Latest 7 Days Snapshot")
    lines.append("| Date | Deru1000 Solved | Vocabulary | Grammar Study |")
    lines.append("| --- | --- | --- | --- |")
    for record in snapshot_records:
        lines.append(
            "| {date} | {solved} questions | {vocab} words | {hours} |".format(
                date=record.date.isoformat(),
                solved=human_int(record.deru1000_solved),
                vocab=human_int(record.vocab_reviewed),
                hours=human_hours(record.ichiojin_grammar_hours),
            )
        )
    lines.append("")

    lines.append("### Progress Overview")
    lines.append("| Metric | Progress | Detail |")
    lines.append("| --- | --- | --- |")
    lines.append(
        "| **Phase 1 time elapsed** | {bar} {percent:.1f}% | day {day} / {total} |".format(
            bar=phase_progress_bar,
            percent=phase_elapsed_percent,
            day=phase_elapsed_clamped,
            total=phase_total_days,
        )
    )
    lines.append(
        format_goal_progress_row(
            "Deru1000 understood",
            latest_non_null(records, "deru1000_understood"),
            GOAL_DERU1000_TOTAL,
        )
    )
    lines.append(
        format_goal_progress_row(
            "Vocabulary understood",
            latest_non_null(records, "vocab_understood"),
            GOAL_VOCAB_TOTAL,
        )
    )
    lines.append(
        format_ratio_progress_row(
            "Grammar understood",
            latest_non_null(records, "grammar_understood_ratio"),
        )
    )
    lines.append("")
    lines.append("### Output Summary")
    lines.append("| Metric | Last 7 days | Cumulative |")
    lines.append("| --- | --- | --- |")
    lines.append(
        "| Deru1000 | {recent} questions | {total} questions |".format(
            recent=human_int(seven_day_solved),
            total=human_int(total_solved),
        )
    )
    lines.append(
        "| Vocabulary | {recent} words | {total} words |".format(
            recent=human_int(seven_day_vocab),
            total=human_int(total_vocab),
        )
    )
    lines.append(
        "| Grammar | {recent} | {total} |".format(
            recent=human_hours(seven_day_hours),
            total=human_hours(total_grammar_hours),
        )
    )
    return "\n".join(lines).strip() + "\n"


def update_readme(readme_path: Path, markdown_block: str) -> None:
    content = readme_path.read_text(encoding="utf-8")
    pattern = re.compile(r"<!--KPIS-->.*?<!--/KPIS-->", re.DOTALL)
    replacement = f"<!--KPIS-->\n{markdown_block}<!--/KPIS-->"
    if not pattern.search(content):
        raise ValueError("KPIS marker not found in README")
    new_content = pattern.sub(replacement, content)
    readme_path.write_text(new_content, encoding="utf-8")


def main() -> None:
    args = parse_args()
    records = load_records(args.csv)
    markdown = render_markdown(records)

    if args.dry_run:
        print(markdown)
        return

    update_readme(args.readme, markdown)
    print("README updated with KPI metrics")


if __name__ == "__main__":
    main()
