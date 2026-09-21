import argparse
import sys

from .app import BudgetApp


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
    search_parser.add_argument("--category")
    search_parser.add_argument("--type")
    search_parser.add_argument("--q")
    search_parser.add_argument("--tag")

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
    update_parser.add_argument("--date")
    update_parser.add_argument("--type")
    update_parser.add_argument("--category")
    update_parser.add_argument("--amount")
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
        print(
            f"예산: {budget:,}원 "
            f"(사용률 {result['budget_usage']:.1f}%)"
        )

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


def run_add(app: BudgetApp) -> bool:
    """대화형으로 거래를 추가한다."""
    values = [
        input("날짜(YYYY-MM-DD): "),
        input("타입(income/expense): "),
        input("카테고리: "),
        input("금액(양수): "),
        input("메모(선택): "),
        input("태그(쉼표로 구분, 없으면 엔터): "),
    ]

    return app.add_transaction(*values)


def main() -> None:
    """CLI 프로그램을 실행한다."""
    parser = create_parser()
    args = parser.parse_args()
    app = BudgetApp(args.data_dir)

    result = True

    if args.command == "add":
        result = run_add(app)

    elif args.command == "list":
        print_transactions(
            app.list_transactions(args.limit)
        )

    elif args.command == "search":
        print_transactions(
            app.search_transactions(
                args.from_date,
                args.to_date,
                args.category,
                args.type,
                args.q,
                args.tag,
            )
        )

    elif args.command == "summary":
        summary = app.summary(args.month, args.top)

        if summary:
            print_summary(summary, args.top)

    elif args.command == "budget":
        result = app.set_budget(
            args.month,
            args.amount,
        )

    elif args.command == "category":
        if args.category_command == "list":
            categories = app.list_categories()

            if categories:
                for category in categories:
                    print(f"- {category}")
            else:
                print("[안내] 등록된 카테고리가 없다.")

        elif args.category_command == "add":
            name = args.name or input("카테고리명: ")
            result = app.add_category(name)

        elif args.category_command == "remove":
            result = app.remove_category(args.name)

    elif args.command == "update":
        result = app.update_transaction(
            args.id,
            args.date,
            args.type,
            args.category,
            args.amount,
            args.memo,
            args.tags,
        )

    elif args.command == "delete":
        result = app.delete_transaction(args.id)

    elif args.command == "export":
        result = app.export_csv(
            args.out,
            args.month,
            args.from_date,
            args.to_date,
        )

    elif args.command == "import":
        result = app.import_csv(args.input_file)

    if result is False:
        sys.exit(1)
