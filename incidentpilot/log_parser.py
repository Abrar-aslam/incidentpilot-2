import re
from collections import Counter
from datetime import datetime

LEVELS = ("TRACE", "DEBUG", "INFO", "WARN", "WARNING", "ERROR", "FATAL", "CRITICAL")
TIMESTAMP_RE = re.compile(
    r"(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)"
)
LEVEL_RE = re.compile(r"\b(TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\b", re.I)
REQUEST_RE = re.compile(r"\b(?:request[_ -]?id|trace[_ -]?id)\s*[:=]\s*([A-Za-z0-9._-]+)", re.I)

def parse_logs(text: str):
    rows = []
    for number, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip():
            continue
        ts_match = TIMESTAMP_RE.search(raw)
        level_match = LEVEL_RE.search(raw)
        request_match = REQUEST_RE.search(raw)
        rows.append({
            "line": number,
            "timestamp": ts_match.group("ts") if ts_match else None,
            "level": level_match.group(1).upper() if level_match else "UNKNOWN",
            "request_id": request_match.group(1) if request_match else None,
            "message": raw.strip(),
        })
    return rows

def summarize_logs(rows):
    levels = Counter(row["level"] for row in rows)
    errors = [r for r in rows if r["level"] in {"ERROR", "FATAL", "CRITICAL"}]
    warnings = [r for r in rows if r["level"] in {"WARN", "WARNING"}]
    return {
        "total_lines": len(rows),
        "levels": dict(levels),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "request_ids": sorted({r["request_id"] for r in rows if r["request_id"]}),
        "first_timestamp": next((r["timestamp"] for r in rows if r["timestamp"]), None),
        "last_timestamp": next((r["timestamp"] for r in reversed(rows) if r["timestamp"]), None),
    }

def search_logs(rows, query, limit=20):
    terms = [term.lower() for term in query.split() if term.strip()]
    if not terms:
        return []
    matches = [
        row for row in rows
        if all(term in row["message"].lower() for term in terms)
    ]
    return matches[:max(1, min(int(limit), 50))]

def get_timeline(rows, limit=30):
    return rows[:max(1, min(int(limit), 100))]
