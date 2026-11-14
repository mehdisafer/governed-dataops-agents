"""Structured operational logs; business payloads remain in the scoped audit store."""

import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        body = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("incident_id", "target_id", "phase"):
            if hasattr(record, key):
                body[key] = getattr(record, key)
        if record.exc_info:
            body["exception"] = self.formatException(record.exc_info)
        return json.dumps(body, ensure_ascii=True)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
