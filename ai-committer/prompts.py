def build_commit_prompt(status, diff):
    return f"""
        당신은 Git 커밋 메시지를 작성하는 개발자입니다.

        아래 Git 변경 사항을 분석하여 커밋 메시지를 작성하세요.

        [Git Status]
        {status}

        [Git Diff]
        {diff}

        규칙:
        1. 커밋 제목은 한 줄로 작성하세요.
        2. 제목은 최대 72자 이내로 작성하세요.
        3. feat, fix, docs, refactor, chore 등의 Conventional Commits 형식을 사용하세요.
        4. 실제 변경 내용만 간결하게 설명하세요.
        5. 코드에 없는 내용을 추측하지 마세요.
        6. 핵심 변경 사항을 bullet으로 작성하세요.

        다음 형식으로만 답변하세요:

        커밋 제목

        - 핵심 변경 사항
        - 핵심 변경 사항
        """.strip()


def build_pr_prompt(status, diff, branch):
    return f"""
        당신은 GitHub Pull Request 설명을 작성하는 개발자입니다.

        현재 브랜치:
        {branch}

        [Git Status]
        {status}

        [Git Diff]
        {diff}

        변경 사항을 분석하여 Pull Request 제목과 본문을 작성하세요.

        규칙:
        1. PR 제목은 한 줄로 작성하세요.
        2. PR 제목은 최대 80자 이내로 작성하세요.
        3. 실제 diff에 없는 내용을 추측하지 마세요.
        4. 각 섹션에는 최소 1개의 bullet을 작성하세요.
        5. 설명은 한국어로 작성하세요.

        반드시 아래 형식을 지키세요.

        PR 제목:
        제목

        PR 본문:
        ## Why
        - 변경 배경 또는 목적

        ## What
        - 핵심 변경 사항

        ## How to Test
        - 테스트 방법
        """.strip()
