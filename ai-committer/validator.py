import re


def validate_commit(text):
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return False, ["커밋 메시지가 비어 있습니다."]

    title = lines[0]

    errors = []

    if len(title) > 72:
        errors.append(
            f"커밋 제목이 72자를 초과합니다. 현재 {len(title)}자입니다."
        )

    return len(errors) == 0, errors


def extract_pr(text):
    title_match = re.search(
        r"PR 제목:\s*(.+)",
        text
    )

    body_match = re.search(
        r"PR 본문:\s*(.*)",
        text,
        re.DOTALL
    )

    if not title_match or not body_match:
        return None, None

    title = title_match.group(1).strip()
    body = body_match.group(1).strip()

    return title, body


def validate_pr(title, body):
    errors = []

    if not title:
        errors.append("PR 제목이 없습니다.")

    elif len(title) > 80:
        errors.append(
            f"PR 제목이 80자를 초과합니다. 현재 {len(title)}자입니다."
        )

    required_sections = [
        "## Why",
        "## What",
        "## How to Test",
    ]

    for section in required_sections:
        if section not in body:
            errors.append(
                f"{section} 섹션이 없습니다."
            )

    for section in required_sections:
        if section not in body:
            continue

        start = body.index(section)
        remaining = body[start + len(section):]

        next_section = re.search(
            r"\n## ",
            remaining
        )

        if next_section:
            section_content = remaining[:next_section.start()]
        else:
            section_content = remaining

        bullets = [
            line
            for line in section_content.splitlines()
            if line.strip().startswith("-")
        ]

        if not bullets:
            errors.append(
                f"{section} 섹션에 bullet이 없습니다."
            )

    return len(errors) == 0, errors
