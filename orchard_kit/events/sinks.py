"""
sinks.py — event sinks and backpressure-safe dispatcher.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass
from queue import Empty, Full, Queue
from typing import Any, Callable, Protocol
from urllib import request

logger = logging.getLogger("orchard.events")


class EventSink(Protocol):
    """Minimal sink interface for telemetry events."""

    def emit(self, event: dict[str, Any]) -> None:
        """Persist or forward one event."""


@dataclass
class FileEventSink:
    """Append-only JSONL sink for local audit retention."""

    path: str

    def emit(self, event: dict[str, Any]) -> None:
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, sort_keys=True))
            fh.write("\n")


@dataclass
class HttpEventSink:
    """POST each event as JSON to a remote ingestion endpoint."""

    url: str
    timeout_seconds: float = 2.0
    headers: dict[str, str] | None = None

    def emit(self, event: dict[str, Any]) -> None:
        body = json.dumps(event).encode("utf-8")
        headers = {"Content-Type": "application/json", **(self.headers or {})}
        req = request.Request(self.url, data=body, headers=headers, method="POST")
        with request.urlopen(req, timeout=self.timeout_seconds) as resp:
            if resp.status >= 400:
                raise RuntimeError(f"event sink HTTP failure: {resp.status}")


@dataclass
class CallbackEventSink:
    """Invoke custom callback for each event."""

    callback: Callable[[dict[str, Any]], None]

    def emit(self, event: dict[str, Any]) -> None:
        self.callback(event)


class EventDispatcher:
    """Bounded asynchronous fan-out dispatcher with drop-on-overflow safety."""

    def __init__(
        self,
        sinks: list[EventSink] | None = None,
        queue_size: int = 1024,
        worker_poll_seconds: float = 0.25,
    ):
        self.sinks = sinks or []
        self.queue: Queue[dict[str, Any]] = Queue(maxsize=max(1, queue_size))
        self.worker_poll_seconds = max(0.05, worker_poll_seconds)
        self._dropped = 0
        self._stop = threading.Event()
        self._worker: threading.Thread | None = None

        if self.sinks:
            self._worker = threading.Thread(
                target=self._drain,
                name="orchard-event-dispatcher",
                daemon=True,
            )
            self._worker.start()

    @property
    def dropped_events(self) -> int:
        return self._dropped

    def publish(self, event: dict[str, Any]) -> None:
        """Non-blocking enqueue; drops on sustained backpressure."""
        if not self.sinks:
            return
        try:
            self.queue.put_nowait(event)
        except Full:
            self._dropped += 1
            logger.warning(
                "event.backpressure_drop: dropped=%s queue_size=%s",
                self._dropped,
                self.queue.maxsize,
            )

    def flush(self, timeout_seconds: float = 2.0) -> None:
        """Best-effort wait for queue to drain."""
        deadline = time.time() + max(0.0, timeout_seconds)
        while not self.queue.empty() and time.time() < deadline:
            time.sleep(0.01)

    def close(self, timeout_seconds: float = 2.0) -> None:
        """Stop worker after best-effort flush."""
        if not self._worker:
            return
        self.flush(timeout_seconds=timeout_seconds)
        self._stop.set()
        self._worker.join(timeout=max(0.1, timeout_seconds))

    def _drain(self) -> None:
        while not self._stop.is_set() or not self.queue.empty():
            try:
                event = self.queue.get(timeout=self.worker_poll_seconds)
            except Empty:
                continue

            for sink in self.sinks:
                try:
                    sink.emit(event)
                except Exception as exc:
                    logger.warning("event.sink_error: sink=%s err=%s", sink, exc)
            self.queue.task_done()
