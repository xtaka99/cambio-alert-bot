"""Appends every fetched rate to a CSV file, building a history over time.

Open the file in Excel or Google Sheets to chart how rates moved.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path

from .rates import Quote


def append_history(path: str | Path, quotes: list[Quote]) -> None:
    file = Path(path)
    is_new = not file.exists()
    with file.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["checked_at_utc", "rate_date", "pair", "rate"])
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        for q in quotes:
            writer.writerow([now, q.date, q.pair, q.rate])
