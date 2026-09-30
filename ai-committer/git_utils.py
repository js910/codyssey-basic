import subprocess
import re


def run_git_command(command):
    """
    Git 명령 실행
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True
        )
        return result.stdout.strip()

    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip() or str(e)
        raise RuntimeError(f"Git 명령 실행 실패: {error_message}")


def get_git_status():
    return run_git_command(["git", "status", "--short"])


def get_git_diff():
    return run_git_command(["git", "diff"])


def get_git_changes():
    status = get_git_status()
    diff = get_git_diff()

    return status, diff


def get_current_branch():
    return run_git_command(
        ["git", "branch", "--show-current"]
    )


def mask_sensitive_data(text):
    """
    AI API로 보내기 전에 민감정보 마스킹
    """
    
    # API Key
    text = re.sub(
        r'(?i)(api[_-]?key\s*[=:]\s*)["\']?[\w\-]+["\']?',
        r'\1[REDACTED]',
        text
    )

    # Bearer Token
    text = re.sub(
        r'(?i)(Bearer\s+)[A-Za-z0-9\-._~+/]+=*',
        r'\1[REDACTED]',
        text
    )

    # 이메일
    text = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        '[REDACTED_EMAIL]',
        text
    )

    return text


def limit_diff(diff, max_files=10, max_lines=200):
    lines = diff.splitlines()

    if len(lines) <= max_lines:
        return diff

    limited_lines = lines[:max_lines]

    limited_lines.append("")
    limited_lines.append(
        f"[SAFE MODE] diff가 {max_lines}줄로 제한되었습니다."
    )

    return "\n".join(limited_lines)


def prepare_diff(diff, safe_mode=False):
    if not safe_mode:
        return diff

    diff = mask_sensitive_data(diff)
    diff = limit_diff(diff)

    return diff
