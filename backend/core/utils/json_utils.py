import json
import logging
import re
from typing import Any, Dict, Type

import orjson
from pydantic import BaseModel

logger = logging.getLogger("animetix.json_utils")

# Regex to find JSON block in markdown backticks
MARKDOWN_JSON_RE = re.compile(
    r"```(?:json)?\s*(\{.*?\})\s*```",
    re.DOTALL | re.IGNORECASE,
)


def extract_json(text: Any) -> Dict[str, Any]:
    """
    Extracts and parses a dictionary from a string or object.
    Supports raw dictionary input, markdown code blocks, and find/rfind braces fallback.
    Returns an empty dictionary if parsing fails.
    """
    if isinstance(text, dict):
        return text

    if not text:
        return {}

    cleaned_text = str(text).split("---")[0].strip()

    # 1. Direct JSON load attempt
    try:
        data = orjson.loads(cleaned_text)
        if isinstance(data, dict):
            return data
    except orjson.JSONDecodeError:
        pass

    # 2. Markdown block regex attempt
    match = MARKDOWN_JSON_RE.search(cleaned_text)
    if match:
        try:
            data = orjson.loads(match.group(1))
            if isinstance(data, dict):
                return data
        except orjson.JSONDecodeError as e:
            logger.debug(f"JSON extraction markdown fallback failed: {e}")

    # 3. Find/rfind braces fallback
    start = cleaned_text.find("{")
    end = cleaned_text.rfind("}")
    if start != -1 and end != -1:
        try:
            data = orjson.loads(cleaned_text[start : end + 1])
            if isinstance(data, dict):
                return data
        except orjson.JSONDecodeError as e:
            logger.debug(f"JSON extraction braces fallback failed: {e}")

    # 4. Standard json fallback if orjson failed
    try:
        if start != -1 and end != -1:
            data = json.loads(cleaned_text[start : end + 1])
            if isinstance(data, dict):
                return data
    except Exception:
        pass

    logger.debug(
        f"Failed to parse JSON from AI output. Output was: {cleaned_text[:200]}..."
    )
    return {}


def extract_and_validate_json(text: Any, schema: Type[BaseModel]) -> Any:
    """
    Extracts a JSON block and validates it against the provided Pydantic schema.
    Raises ValueError or validation errors if it fails.
    """
    if isinstance(text, dict):
        return schema.model_validate(text)

    cleaned_text = str(text).strip()

    # Braces search
    start = cleaned_text.find("{")
    end = cleaned_text.rfind("}")
    if start != -1 and end != -1:
        json_str = cleaned_text[start : end + 1]
        try:
            data = orjson.loads(json_str)
        except orjson.JSONDecodeError:
            data = json.loads(json_str)
        return schema.model_validate(data)
    else:
        raise ValueError("No JSON block found in output")
