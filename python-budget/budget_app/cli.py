import argparse
import sys

from .app import BudgetApp


def _add_flags(parser: argparse.ArgumentParser, *flag_names: str) -> None:
    """여러 개의 선택 인자를 한 번에 추가한다."""
    for flag_name in flag_names:
        parser.add_argument(flag_name)


def create_parser() -> argparse.ArgumentParser:
    """CLI 명령어를 설정한다."""
    parser = argparse.ArgumentParser(
        prog="budget_app",
        description="콘솔 가계부 프로그램",
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="데이터 저장 폴더",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )
    subparsers.add_parser("add", help="거래 추가")

    list_parser = subparsers.add_parser("list", help="거래 목록")
    list_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="출력할 거래 수",
    )

    search_parser = subparsers.add_parser("search", help="거래 검색")
    search_parser.add_argument("--from", dest="from_date")
    search_parser.add_argument("--to", dest="to_date")
    _add_flags(search_parser, "--category", "--type", "--q", "--tag")

    summary_parser = subparsers.add_parser(
        "summary",
        help="월별 요약",
    )
    summary_parser.add_argument(
        "--month",
        required=True,
        help="조회할 월 (YYYY-MM)",
    )
    summary_parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="지출 카테고리 수",
    )

    budget_parser = subparsers.add_parser(
        "budget",
        help="예산 관리",
    )
    budget_subparsers = budget_parser.add_subparsers(
        dest="budget_command",
        required=True,
    )

    budget_set = budget_subparsers.add_parser(
        "set",
        help="월별 예산 설정",
    )
    budget_set.add_argument(
        "--month",
        required=True,
        help="예산 월 (YYYY-MM)",
    )
    budget_set.add_argument(
        "--amount",
        required=True,
        help="예산 금액",
    )

    category_parser = subparsers.add_parser(
        "category",
        help="카테고리 관리",
    )
    category_subparsers = category_parser.add_subparsers(
        dest="category_command",
        required=True,
    )
    category_subparsers.add_parser(
        "list",
        help="카테고리 목록",
    )

    category_add = category_subparsers.add_parser(
        "add",
        help="카테고리 추가",
    )
    category_add.add_argument(
        "name",
        nargs="?",
        help="카테고리명",
    )

    category_remove = category_subparsers.add_parser(
        "remove",
        help="카테고리 삭제",
    )
    category_remove.add_argument(
        "name",
        help="삭제할 카테고리명",
    )

    update_parser = subparsers.add_parser(
        "update",
        help="거래 수정",
    )
    update_parser.add_argument(
        "--id",
        required=True,
        help="거래 ID",
    )
    _add_flags(update_parser, "--date", "--type", "--category", "--amount")
    update_parser.add_argument("--memo")
    update_parser.add_argument("--tags")

    delete_parser = subparsers.add_parser(
        "delete",
        help="거래 삭제",
    )
    delete_parser.add_argument(
        "--id",
        required=True,
        help="거래 ID",
    )

    export_parser = subparsers.add_parser(
        "export",
        help="CSV 내보내기",
    )
    export_parser.add_argument(
        "--out",
        required=True,
        help="출력 CSV 파일",
    )
    export_parser.add_argument("--month")
    export_parser.add_argument(
        "--from",
        dest="from_date",
    )
    export_parser.add_argument(
        "--to",
        dest="to_date",
    )

    import_parser = subparsers.add_parser(
        "import",
        help="CSV 가져오기",
    )
    import_parser.add_argument(
        "--from",
        dest="input_file",
        required=True,
        help="가져올 CSV 파일",
    )

    return parser


def print_transactions(transactions) -> None:
    """거래 목록을 출력한다."""
    if not transactions:
        print("[안내] 거래 데이터가 없다.")
        return

    for transaction in transactions:
        tags = ",".join(transaction.tags)
        tag_text = f" | {tags}" if tags else ""

        print(
            f"{transaction.id} | "
            f"{transaction.date} | "
            f"{transaction.type} | "
            f"{transaction.category} | "
            f"{transaction.amount:,} | "
            f"{transaction.memo}"
            f"{tag_text}"
        )


def print_summary(result: dict, top: int) -> None:
    """월별 요약 결과를 출력한다."""
    print(f"총 수입: {result['income']:,}원")
    print(f"총 지출: {result['expense']:,}원")
    print(f"잔액: {result['balance']:,}원")

    budget = result["budget"]

    if budget is not None:
        print(f"예산: {budget:,}원 (사용률 {result['budget_usage']:.1f}%)")

        if result["expense"] > budget:
            print("[경고] 예산을 초과했습니다.")

    print(f"\n지출 TOP {top}")

    if not result["category_expenses"]:
        print("데이터 없음")
        return

    for index, (category, amount) in enumerate(
        result["category_expenses"],
        1,
    ):
        print(f"{index}) {category} {amount:,}원")


def _handle_add(app: BudgetApp, args) -> bool:
    """대화형으로 거래를 추가한다."""
    date_val = input("날짜(YYYY-MM-DD): ")
    type_val = input("타입(income/expense): ")
    category_val = input("카테고리: ")
    amount_val = input("금액(양수): ")
    memo_val = input("메모(선택): ")
    tags_val = input("태그(쉼표로 구분, 없으면 엔터): ")

    return app.add_transaction(
        date=date_val,
        transaction_type=type_val,
        category=category_val,
        amount=amount_val,
        memo=memo_val,
        tags=tags_val,
    )


def _handle_list(app: BudgetApp, args) -> None:
    transactions = app.list_transactions(args.limit)
    print_transactions(transactions)


def _handle_search(app: BudgetApp, args) -> None:
    transactions = app.search_transactions(
        from_date=args.from_date,
        to_date=args.to_date,
        category=args.category,
        transaction_type=args.type,
        query=args.q,
        tag=args.tag,
    )
    print_transactions(transactions)


def _handle_summary(app: BudgetApp, args) -> None:
    result = app.summary(args.month, args.top)
    if result:
        print_summary(result, args.top)


def _handle_budget(app: BudgetApp, args) -> bool:
    return app.set_budget(args.month, args.amount)


def _handle_category(app: BudgetApp, args) -> bool | None:
    """카테고리 관련 세부 명령을 처리한다."""
    if args.category_command == "list":
        categories = app.list_categories()
        if categories:
            for category in categories:
                print(f"- {category}")
        else:
            print("[안내] 등록된 카테고리가 없다.")
        return None

    if args.category_command == "add":
        name = args.name or input("카테고리명: ")
        return app.add_category(name)

    if args.category_command == "remove":
        return app.remove_category(args.name)

    return None


def _handle_update(app: BudgetApp, args) -> bool:
    return app.update_transaction(
        transaction_id=args.id,
        date=args.date,
        transaction_type=args.type,
        category=args.category,
        amount=args.amount,
        memo=args.memo,
        tags=args.tags,
    )


def _handle_delete(app: BudgetApp, args) -> bool:
    return app.delete_transaction(args.id)


def _handle_export(app: BudgetApp, args) -> bool:
    return app.export_csv(
        output=args.out,
        month=args.month,
        from_date=args.from_date,
        to_date=args.to_date,
    )


def _handle_import(app: BudgetApp, args) -> bool:
    return app.import_csv(args.input_file)


def _run_cli() -> None:
    """CLI 프로그램을 실행한다."""
    parser = create_parser()
    args = parser.parse_args()
    app = BudgetApp(args.data_dir)

    # 명령어와 처리 함수를 매핑 (딕셔너리 구조)
    command_map = {
        "add": _handle_add,
        "list": _handle_list,
        "search": _handle_search,
        "summary": _handle_summary,
        "budget": _handle_budget,
        "category": _handle_category,
        "update": _handle_update,
        "delete": _handle_delete,
        "export": _handle_export,
        "import": _handle_import,
    }

    handler = command_map.get(args.command)
    if handler is None:
        return

    result = handler(app, args)

    if result is False:
        sys.exit(1)


def main() -> None:
    _run_cli()
