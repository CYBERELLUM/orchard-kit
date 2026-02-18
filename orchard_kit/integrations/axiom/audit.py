"""Structured event sink for Axiom governance integration."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable


class AxiomAuditSink:
    """Exports governance events to callback and/or JSONL file."""

    def __init__(
        self,
        callback: Callable[[dict[str, Any]], None] | None = None,
        jsonl_path: str | Path | None = None,
    ) -> None:
        self.callback = callback
        self.jsonl_path = Path(jsonl_path) if jsonl_path else None

    def emit(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Emit a structured governance event."""
        event = {
            "type": event_type,
            "ts": time.time(),
            "payload": payload,
        }

        if self.callback:
            self.callback(event)

        if self.jsonl_path:
            self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
            with self.jsonl_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")

        return event
