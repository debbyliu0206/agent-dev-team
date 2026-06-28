import json
import re


def extract_json(text):
    """Best-effort extraction of a JSON object/array from an LLM response.

    Handles values that are already dict/list, ```json fenced blocks, and prose
    surrounding a JSON object. Returns the parsed object or None.
    """
    if text is None:
        return None
    if isinstance(text, (dict, list)):
        return text
    s = str(text).strip()

    # Pull contents out of a ```...``` fence if present.
    if "```" in s:
        m = re.search(r"```(?:json)?\s*(.*?)```", s, re.DOTALL)
        if m:
            s = m.group(1).strip()

    # Narrow to the outermost {...} or [...] span.
    starts = [i for i in (s.find("{"), s.find("[")) if i != -1]
    ends = [i for i in (s.rfind("}"), s.rfind("]")) if i != -1]
    if starts and ends:
        s = s[min(starts): max(ends) + 1]

    try:
        return json.loads(s)
    except Exception:
        return None
