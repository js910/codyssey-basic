import argparse

from git_utils import (
    get_git_changes,
    get_current_branch,
    prepare_diff,
)

from gemini import generate_text

from prompts import (
    build_commit_prompt,
    build_pr_prompt,
)

from validator import (
    validate_commit,
    extract_pr,
    validate_pr,
)


def print_header():
    print("=" * 40)
    print(" AI Git Generator")
    print("=" * 40)


def collect_changes(safe_mode=False):
    status, diff = get_git_changes()

    if not status and not diff:
        print("[INFO] 변경 사항이 없습니다.")
        return None, None

    print("[INFO] Git status 수집 완료")
    print(status)

    print()
    print("[INFO] Git diff 수집 완료")
    print(f"[INFO] Diff 길이: {len(diff)} 문자")

    if safe_mode:
        print("[INFO] Safe Mode 적용")
        diff = prepare_diff(diff, safe_mode=True)

    return status, diff


def generate_commit(args):
    status, diff = collect_changes(args.safe_mode)

    if status is None:
        return

    prompt = build_commit_prompt(status, diff)

    print()
    print("[INFO] Gemini API 요청 중...")

    result = generate_text(
        prompt=prompt,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    valid, errors = validate_commit(result)

    print()
    print("=" * 40)
    print(" Commit Message")
    print("=" * 40)

    print(result)

    if valid:
        print("=" * 40)
        print("[INFO] 커밋 메시지 형식 검증 완료")
    else:
        print()
        print("[WARNING] 커밋 메시지 검증 실패")

        for error in errors:
            print(f"- {error}")


def generate_pr(args):
    status, diff = collect_changes(args.safe_mode)

    if status is None:
        return

    branch = get_current_branch()

    print(f"[INFO] 현재 브랜치: {branch}")

    prompt = build_pr_prompt(
        status,
        diff,
        branch
    )

    print()
    print("[INFO] Gemini API 요청 중...")

    result = generate_text(
        prompt=prompt,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    title, body = extract_pr(result)

    print()
    print("=" * 40)
    print(" Pull Request")
    print("=" * 40)

    if title is None or body is None:
        print(result)
        print()
        print("[WARNING] PR 형식을 분석할 수 없습니다.")
        return

    print()
    print("PR Title")
    print("-" * 40)
    print(title)

    print()
    print("PR Body")
    print("-" * 40)
    print(body)

    valid, errors = validate_pr(
        title,
        body
    )

    print()
    print("=" * 40)

    if valid:
        print("[INFO] PR 형식 검증 완료")
    else:
        print("[WARNING] PR 형식 검증 실패")

        for error in errors:
            print(f"- {error}")


def create_parser():
    parser = argparse.ArgumentParser(
        description="Git 변경 사항을 분석하여 Commit / PR 초안을 생성합니다."
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    commit_parser = subparsers.add_parser(
        "commit",
        help="커밋 메시지 생성"
    )

    pr_parser = subparsers.add_parser(
        "pr",
        help="Pull Request 생성"
    )

    for command_parser in [
        commit_parser,
        pr_parser,
    ]:
        command_parser.add_argument(
            "--model",
            default="gemini-3.5-flash-lite",
            help="사용할 Gemini 모델"
        )

        command_parser.add_argument(
            "--temperature",
            type=float,
            default=0.3,
            help="AI 생성 temperature"
        )

        command_parser.add_argument(
            "--max-tokens",
            type=int,
            default=500,
            help="최대 생성 토큰 수"
        )

        command_parser.add_argument(
            "--safe-mode",
            action="store_true",
            help="민감정보 마스킹 및 diff 제한"
        )

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    print_header()

    print(f"[INFO] Model: {args.model}")
    print(f"[INFO] Temperature: {args.temperature}")
    print(f"[INFO] Max tokens: {args.max_tokens}")

    try:
        if args.command == "commit":
            generate_commit(args)

        elif args.command == "pr":
            generate_pr(args)

    except RuntimeError as e:
        print()
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
