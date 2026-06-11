import json
import re


def parse_json(raw: str) -> dict:
    """Robustly parse a JSON string from Claude's response.

    Handles:
    - Markdown code fences (```json ... ```)
    - Literal newlines / control characters inside string values
    """
    text = raw.strip()

    # Strip markdown fences
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    # Remove literal control characters (newlines, tabs) that appear
    # inside JSON string values and make json.loads fail.
    # We replace them with their escaped equivalents only inside strings.
    def sanitise_string_values(m):
        return m.group(0).replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")

    # Match JSON string literals (naive but sufficient for our outputs)
    text = re.sub(r'"(?:[^"\\]|\\.)*"', sanitise_string_values, text, flags=re.DOTALL)

    return json.loads(text)
