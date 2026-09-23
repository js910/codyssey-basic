from datetime import datetime


def validate_date(value: str) -> str:
    """YYYY-MM-DD 형식을 검증한다."""
    try:
        datetime.strptime(value, "%Y-%m-%d")  # noqa: DTZ007
    except ValueError as e:
        raise ValueError("날짜 형식이 올바르지 않다. (YYYY-MM-DD)") from e

    return value


def validate_month(value: str) -> str:
    """YYYY-MM 형식을 검증한다."""
    try:
        datetime.strptime(value, "%Y-%m")  # noqa: DTZ007
    except ValueError as e:
        raise ValueError("월 형식이 올바르지 않다. (YYYY-MM)") from e

    return value


def validate_amount(value: str) -> int:
    """양의 정수 금액을 검증한다."""
    try:
        amount = int(value)
    except ValueError as e:
        raise ValueError("금액은 정수로 입력해야 한다.") from e

    if amount <= 0:
        raise ValueError("금액은 0보다 커야 한다.")

    return amount


def validate_type(value: str) -> str:
    """거래 타입을 검증한다."""
    if value in {"income", "expense"}:
        return value
    else:
        raise ValueError("타입은 income 또는 expense만 사용할 수 있다.")
