import re

def clean_response(text: str) -> str:
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^[\*\-\•]+\s*", "", line)
        line = re.sub(r"\*+", "", line)
        lines.append(line)

    cleaned = " ".join(lines)

    # remove any Action: ... part
    cleaned = re.sub(r"Action:.*", "", cleaned, flags=re.I).strip()

    return cleaned
