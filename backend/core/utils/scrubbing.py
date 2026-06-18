# -*- coding: utf-8 -*-
import logging
import re
from typing import Any

logger = logging.getLogger("animetix.security.scrubbing")

# Patterns for sensitive data detection
SENSITIVE_PATTERNS = {
    "api_key": r"(?i)(api[-_]?key|secret|token|auth|credential|password|signature)[\s:=]+['\"]?([a-zA-Z0-9_\-\.\/]{8,})['\"]?",
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    "stripe": r"(?i)(sk|pk|cs)_(test|live)_[a-zA-Z0-9]{24,}",
    "jwt": r"ey[a-zA-Z0-9._-]{20,}",
}


def scrub_sensitive_data(data: Any) -> Any:
    """
    Recursively scrubs sensitive information (keys, secrets, emails) from strings,
    lists, and dictionaries. Replaces sensitive values with [REDACTED].
    """
    if isinstance(data, str):
        scrubbed = data
        for label, pattern in SENSITIVE_PATTERNS.items():
            # If the string matches a sensitive pattern directly or contains it
            if label == "api_key":
                # For keys, we scrub the value part specifically
                scrubbed = re.sub(pattern, r"\1: [REDACTED]", scrubbed)
            else:
                scrubbed = re.sub(pattern, "[REDACTED]", scrubbed)
        return scrubbed

    if isinstance(data, list):
        return [scrub_sensitive_data(item) for item in data]

    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            # Scrub key names that look like secrets
            k_str = str(k).lower()
            if any(
                secret_word in k_str
                for secret_word in [
                    "key",
                    "secret",
                    "token",
                    "auth",
                    "password",
                    "credential",
                ]
            ):
                new_dict[k] = "[REDACTED]"
            else:
                new_dict[k] = scrub_sensitive_data(v)
        return new_dict

    return data


class SensitiveScrubbingFilter(logging.Filter):
    """
    Logging filter that automatically scrubs sensitive data from log records.
    """

    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = scrub_sensitive_data(record.msg)

        if record.args:
            if isinstance(record.args, dict):
                record.args = scrub_sensitive_data(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(scrub_sensitive_data(arg) for arg in record.args)

        return True
