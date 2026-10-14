"""Targets = the rules the bot checks, e.g. "tell me when USD-BRL is below 5.20".

They live in config/targets.json so they can be changed without editing code.
"""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Target:
    base: str                      # currency you are buying, e.g. "USD"
    quote: str                     # currency you pay with, e.g. "BRL"
    below: float | None = None     # alert when the rate drops to this or lower
    above: float | None = None     # alert when the rate rises to this or higher
    note: str = ""                 # free text shown in the alert

    @property
    def pair(self) -> str:
        return f"{self.base}-{self.quote}"

    def is_hit(self, rate: float) -> bool:
        """True when the current rate satisfies this target."""
        if self.below is not None and rate <= self.below:
            return True
        if self.above is not None and rate >= self.above:
            return True
        return False

    def describe(self) -> str:
        parts = []
        if self.below is not None:
            parts.append(f"<= {self.below:g}")
        if self.above is not None:
            parts.append(f">= {self.above:g}")
        return " or ".join(parts)


def parse_pair(pair: str) -> tuple[str, str]:
    """ "usd-brl" -> ("USD", "BRL"). Raises ValueError on anything odd."""
    pieces = pair.upper().replace("/", "-").split("-")
    if len(pieces) != 2 or not all(len(p) == 3 and p.isalpha() for p in pieces):
        raise ValueError(f"Invalid currency pair: {pair!r} (expected e.g. 'USD-BRL')")
    return pieces[0], pieces[1]


def load_targets(path: str | Path) -> list[Target]:
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(f"Targets file not found: {file}")
    raw = json.loads(file.read_text(encoding="utf-8"))

    targets = []
    for entry in raw["targets"]:
        base, quote = parse_pair(entry["pair"])
        below, above = entry.get("below"), entry.get("above")
        if below is None and above is None:
            raise ValueError(f"{entry['pair']}: set 'below', 'above', or both")
        targets.append(Target(base, quote, below, above, entry.get("note", "")))
    return targets
