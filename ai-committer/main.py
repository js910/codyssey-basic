import argparse
import os
import re
import subprocess

from google import genai
from google.genai import types


DEFAULT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 500


# =========================
# Git 명령 실행
# =========================

def run_git_command(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        if result.returncode != 0:
            print(f"[ERROR] Git 명령 실행 실패: {' '.join(command)}")
            print(result.stderr)
            return None

        return result.stdout

    except FileNotFoundError:
        print("[ERROR] Git이 설치되어 있지 않습니다.")
        return None


def get_git_status():
    return run_git_command(["git", "status", "--short"])


def get_git_diff():
    return run_git_command(["git", "diff"])


# =========================
# Safe Mode
# =========================

def mask_sensitive_data(text):
    """
    AI API로 보내기 전에 민감정보를 마스킹한다.

    현재 마스킹 대상:
    - API Key
    - Bearer Token
    - 이메일 주소
    """

    masked = text

    # -------------------------
    # API Key
    # -------------------------

    masked = re.sub(
        r'(?i)(api[_-]?key\s*[:=]\s*["\']?)[A-Za-z0-9_\-\.]+',
        r'\1[REDACTED]',
        masked,
    )

    # -------------------------
    # Bearer Token
    # -------------------------

    masked = re.sub(
        r'(?i)(bearer\s+)[A-Za-z0-9_\-\.]+',
        r'\1[REDACTED]',
        masked,
    )

    # -------------------------
    # 이메일
    # -------------------------

    masked = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        '[REDACTED_EMAIL]',
        masked,
    )

    return masked


# =========================
# Gemini
# =========================

def create_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("[ERROR] GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        print('예: export GEMINI_API_KEY="YOUR_API_KEY"')
        return None

    return genai.Client(api_key=api_key)


def ask_gemini(
    client,
    prompt,
    model,
    temperature,
    max_tokens,
):
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )

        return response.text

    except Exception as e:
        print(f"[ERROR] Gemini API 호출 실패: {e}")
        return None


# =========================
# Commit 생성
# =========================

def generate_commit(
    client,
    git_status,
    git_diff,
    model,
    temperature,
    max_tokens,
):
    prompt = f"""
당신은 Git 커밋 메시지를 작성하는 개발 보조 AI입니다.

아래 Git 변경 내용을 분석해서 커밋 메시지를 작성하세요.

[Git Status]
{git_status}

[Git Diff]
{git_diff}

규칙:
- 커밋 제목은 반드시 첫 번째 줄에 작성하세요.
- 제목은 최대 72자 이내로 작성하세요.
- feat, fix, docs, refactor, chore 등의 prefix를 적절하게 사용하세요.
- 실제 변경 내용만 설명하세요.
- 코드에 없는 내용을 추측하지 마세요.
- 필요한 경우 본문에 핵심 변경 사항을 1~2개의 bullet으로 작성하세요.

결과만 출력하세요.
"""

    return ask_gemini(
        client,
        prompt,
        model,
        temperature,
        max_tokens,
    )


# =========================
# PR 생성
# =========================

def generate_pr(
    client,
    git_status,
    git_diff,
    model,
    temperature,
    max_tokens,
):
    prompt = f"""
당신은 GitHub Pull Request 작성 도우미입니다.

아래 Git 변경 내용을 분석해서 PR 제목과 본문을 작성하세요.

[Git Status]
{git_status}

[Git Diff]
{git_diff}

반드시 아래 형식을 지키세요.

PR_TITLE: 제목

PR_BODY:
## Why
- 변경 배경 또는 목적

## What
- 핵심 변경 사항

## How to Test
- 테스트 방법

규칙:
- PR 제목은 최대 80자입니다.
- Why, What, How to Test 섹션을 반드시 포함하세요.
- 각 섹션에는 최소 1개의 bullet이 있어야 합니다.
- 실제 변경 내용만 작성하세요.
- 코드에 없는 내용을 추측하지 마세요.

결과만 출력하세요.
"""

    return ask_gemini(
        client,
        prompt,
        model,
        temperature,
        max_tokens,
    )


# =========================
# PR 결과 검증
# =========================

def validate_pr(result):
    errors = []

    lines = result.strip().splitlines()

    # PR 제목 확인
    title = ""

    for line in lines:
        if line.startswith("PR_TITLE:"):
            title = line.replace("PR_TITLE:", "", 1).strip()
            break

    if not title:
        errors.append("PR 제목이 없습니다.")
    elif len(title) > 80:
        errors.append(
            f"PR 제목이 80자를 초과했습니다. 현재 {len(title)}자입니다."
        )

    # 필수 섹션
    required_sections = [
        "## Why",
        "## What",
        "## How to Test",
    ]

    for section in required_sections:
        if section not in result:
            errors.append(f"{section} 섹션이 없습니다.")

    # Why
    if "## Why" in result:
        why_start = result.index("## Why")

        if "## What" in result:
            why_end = result.index("## What")
            why_content = result[why_start:why_end]
        else:
            why_content = result[why_start:]

        if not has_bullet(why_content):
            errors.append("Why 섹션에 bullet이 없습니다.")

    # What
    if "## What" in result:
        what_start = result.index("## What")

        if "## How to Test" in result:
            what_end = result.index("## How to Test")
            what_content = result[what_start:what_end]
        else:
            what_content = result[what_start:]

        if not has_bullet(what_content):
            errors.append("What 섹션에 bullet이 없습니다.")

    # How to Test
    if "## How to Test" in result:
        test_start = result.index("## How to Test")
        test_content = result[test_start:]

        if not has_bullet(test_content):
            errors.append("How to Test 섹션에 bullet이 없습니다.")

    return errors


def has_bullet(text):
    for line in text.splitlines():
        if line.strip().startswith("- ") or line.strip().startswith("* "):
            return True

    return False


# =========================
# Git 변경사항 확인
# =========================

def collect_changes(safe_mode):
    git_status = get_git_status()

    if git_status is None:
        return None, None

    if not git_status.strip():
        print("[INFO] 변경 사항이 없습니다.")
        return None, None

    print("[INFO] Git status 수집 완료")
    print(git_status)

    git_diff = get_git_diff()

    if git_diff is None:
        return None, None

    if not git_diff.strip():
        print("[INFO] Git diff가 비어 있습니다.")
        return None, None

    print("[INFO] Git diff 수집 완료")
    print(f"[INFO] Diff 길이: {len(git_diff)} 문자")

    # Safe Mode 적용
    if safe_mode:
        git_diff = mask_sensitive_data(git_diff)
        print("[INFO] Safe Mode: 민감정보 마스킹 적용")

    return git_status, git_diff


# =========================
# CLI
# =========================

def main():
    parser = argparse.ArgumentParser(
        description="AI 기반 Git 커밋 메시지 및 PR 생성 도구"
    )

    parser.add_argument(
        "command",
        choices=["commit", "pr"],
        help="생성할 결과: commit 또는 pr",
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"사용할 Gemini 모델 (기본값: {DEFAULT_MODEL})",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=DEFAULT_TEMPERATURE,
        help=f"AI temperature (기본값: {DEFAULT_TEMPERATURE})",
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"최대 출력 토큰 수 (기본값: {DEFAULT_MAX_TOKENS})",
    )

    parser.add_argument(
        "--safe-mode",
        action="store_true",
        help="AI API로 전송하기 전에 민감정보를 마스킹합니다.",
    )

    args = parser.parse_args()

    print("========================================")
    print(" AI Git Generator")
    print("========================================")

    print(f"[INFO] Model: {args.model}")
    print(f"[INFO] Temperature: {args.temperature}")
    print(f"[INFO] Max tokens: {args.max_tokens}")
    print(f"[INFO] Safe Mode: {'ON' if args.safe_mode else 'OFF'}")

    git_status, git_diff = collect_changes(args.safe_mode)

    if git_status is None:
        return

    client = create_gemini_client()

    if client is None:
        return

    print("\n[INFO] Gemini API 요청 중...")

    # =========================
    # Commit
    # =========================

    if args.command == "commit":
        result = generate_commit(
            client,
            git_status,
            git_diff,
            args.model,
            args.temperature,
            args.max_tokens,
        )

        if not result:
            return

        print("\n========================================")
        print(" Commit Message")
        print("========================================")
        print(result.strip())
        print("========================================")

    # =========================
    # PR
    # =========================

    elif args.command == "pr":
        result = generate_pr(
            client,
            git_status,
            git_diff,
            args.model,
            args.temperature,
            args.max_tokens,
        )

        if not result:
            return

        errors = validate_pr(result)

        print("\n========================================")
        print(" Pull Request")
        print("========================================")

        if errors:
            print("[WARNING] PR 형식 검증 결과")

            for error in errors:
                print(f"- {error}")
        else:
            print("[OK] PR 형식 검증 통과")

        print("\n" + result.strip())

        print("========================================")


if __name__ == "__main__":
    main()
