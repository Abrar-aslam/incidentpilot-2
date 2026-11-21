import re
from typing import Any


# Sensitive key-value pairs, including common JSON-style fields.
SECRET_PATTERN = re.compile(
    r"""(?ix)
    \b(
        api[_-]?key |
        access[_-]?token |
        refresh[_-]?token |
        auth[_-]?token |
        client[_-]?secret |
        secret |
        password |
        passwd |
        pwd |
        authorization
    )\b
    (\s*[:=]\s*)
    ("[^"]*"|'[^']*'|[^\s,;]+)
    """
)

BEARER_PATTERN = re.compile(
    r"(?i)(\bBearer\s+)[A-Za-z0-9._~+/=-]+"
)

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# Passwords embedded in database URLs.
DATABASE_URL_PATTERN = re.compile(
    r"(?i)(://[^:/\s]+:)([^@/\s]+)(@)"
)


def redact_text(text: str) -> tuple[str, dict[str, int]]:
    """Redact common secrets and personal email addresses."""

    counts = {
        "secrets": 0,
        "bearer_tokens": 0,
        "emails": 0,
        "database_passwords": 0,
    }

    def replace_secret(match):
        counts["secrets"] += 1
        return f"{match.group(1)}{match.group(2)}[REDACTED]"

    def replace_bearer(match):
        counts["bearer_tokens"] += 1
        return f"{match.group(1)}[REDACTED]"

    def replace_email(match):
        counts["emails"] += 1
        return "[EMAIL_REDACTED]"

    def replace_database_password(match):
        counts["database_passwords"] += 1
        return f"{match.group(1)}[REDACTED]{match.group(3)}"

    # Redact database URL credentials first.
    redacted = DATABASE_URL_PATTERN.sub(
        replace_database_password, text
    )

    # Redact labelled secrets.
    redacted = SECRET_PATTERN.sub(replace_secret, redacted)

    # Redact bearer tokens.
    redacted = BEARER_PATTERN.sub(replace_bearer, redacted)

    # Redact email addresses.
    redacted = EMAIL_PATTERN.sub(replace_email, redacted)

    return redacted, counts


def redact_rows(rows: list[dict[str, Any]]) -> tuple[
    list[dict[str, Any]], dict[str, int]
]:
    """
    Return copied log rows with sensitive message content redacted.
    Original rows are not modified.
    """

    safe_rows = []
    total_counts = {
        "secrets": 0,
        "bearer_tokens": 0,
        "emails": 0,
        "database_passwords": 0,
    }

    for row in rows:
        safe_row = dict(row)

        # Common parser field names.
        message_field = next(
            (
                field for field in ("message", "msg", "content")
                if isinstance(safe_row.get(field), str)
            ),
            None,
        )

        if message_field:
            safe_message, counts = redact_text(
                safe_row[message_field]
            )
            safe_row[message_field] = safe_message

            for key, value in counts.items():
                total_counts[key] += value

        safe_rows.append(safe_row)

    return safe_rows, total_counts