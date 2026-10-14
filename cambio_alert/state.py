"""Remembers which alerts were already sent, so the bot does not nag.

Logic: alert once when a target becomes hit. Stay quiet while it stays hit.
When the rate moves back out of range, re-arm so the next hit alerts again.
"""

import json
from pathlib import Path


class AlertState:
    def __init__(self, path: str | Path | None):
        # path=None means "no memory": every hit alerts (used by scheduled CI runs).
        self.path = Path(path) if path else None
        self.active: set[str] = set()
        if self.path and self.path.exists():
            try:
                self.active = set(json.loads(self.path.read_text(encoding="utf-8")))
            except (ValueError, TypeError):
                self.active = set()          # corrupted file: start fresh

    def should_alert(self, key: str, is_hit: bool) -> bool:
        """Update memory for this target and say whether to send an alert."""
        if not is_hit:
            self.active.discard(key)         # re-arm
            return False
        if self.path is None:
            return True
        if key in self.active:
            return False                     # already told the user
        self.active.add(key)
        return True

    def save(self) -> None:
        if self.path:
            self.path.write_text(json.dumps(sorted(self.active)), encoding="utf-8")
