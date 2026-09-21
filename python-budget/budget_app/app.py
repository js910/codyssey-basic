import csv
from functools import wraps
from pathlib import Path
from typing import Callable

from .models import Transaction, Category, Budget
from .repository import (
    TransactionRepository,
    CategoryRepository,
    BudgetRepository,
)
from .validators import (
    validate_date,
    validate_month,
    validate_amount,
    validate_type,
)


def handle_errors(func: Callable) -> Callable:
    """공통 예외를 처리한다."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            print(f"[오류] {e}")
            return False
        except FileNotFoundError:
            print("[오류] 파일을 찾을 수 없다.")
            return False
        except Exception as e:
            print(f"[오류] 처리 중 문제가 발생했다: {e}")
            return False

    return wrapper


class BudgetApp:
    """가계부의 핵심 기능을 제공한다."""

    def __init__(self, data_dir: str = "data"):
        self.transactions = TransactionRepository(data_dir)
        self.categories = CategoryRepository(data_dir)
        self.budgets = BudgetRepository(data_dir)
        self._initialize_categories()

    def _initialize_categories(self) -> None:
        """기본 카테고리를 준비한다."""
        if any(self.categories.stream()):
            return

        for name in (
            "food",
            "transport",
            "rent",
            "shopping",
            "medical",
            "salary",
            "etc",
        ):
            self.categories.add(Category(name))

    def _category_exists(self, name: str) -> bool:
        """카테고리 존재 여부를 확인한다."""
        return any(
            category.name == name
            for category in self.categories.stream()
        )

    def _generate_id(self) -> str:
        """새 거래 ID를 생성한다."""
        max_number = 0

        for transaction in self.transactions.stream():
            try:
                number = int(transaction.id.split("-")[1])
                max_number = max(max_number, number)
            except (IndexError, ValueError):
                continue

        return f"TX-{max_number + 1:06d}"

    @staticmethod
    def _parse_tags(tags: str) -> list[str]:
        """태그 문자열을 리스트로 변환한다."""
        return [
            tag.strip()
            for tag in tags.split(",")
            if tag.strip()
        ]

    def _filter_transactions(
        self,
        month: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list[Transaction]:
        """날짜 조건에 맞는 거래를 반환한다."""
        results = []

        for transaction in self.transactions.stream():
            if month and not transaction.date.startswith(month):
                continue
            if from_date and transaction.date < from_date:
                continue
            if to_date and transaction.date > to_date:
                continue

            results.append(transaction)

        return results

    @handle_errors
    def add_transaction(
        self,
        date: str,
        transaction_type: str,
        category: str,
        amount: str,
        memo: str = "",
        tags: str = "",
    ) -> bool:
        """새로운 거래를 추가한다."""
        date = validate_date(date)
        transaction_type = validate_type(transaction_type)
        amount = validate_amount(amount)

        if not self._category_exists(category):
            raise ValueError(
                f"등록되지 않은 카테고리다: {category}"
            )

        transaction = Transaction(
            id=self._generate_id(),
            type=transaction_type,
            date=date,
            amount=amount,
            category=category,
            memo=memo,
            tags=self._parse_tags(tags),
        )

        self.transactions.add(transaction)

        print(f"[저장 완료] id={transaction.id}")
        return True

    def list_transactions(
        self,
        limit: int = 10,
    ) -> list[Transaction]:
        """거래 목록을 최신순으로 반환한다."""
        if limit <= 0:
            raise ValueError("limit은 1 이상이어야 한다.")

        return sorted(
            self.transactions.stream(),
            key=lambda transaction: transaction.date,
            reverse=True,
        )[:limit]

    def search_transactions(
        self,
        from_date: str | None = None,
        to_date: str | None = None,
        category: str | None = None,
        transaction_type: str | None = None,
        query: str | None = None,
        tag: str | None = None,
    ) -> list[Transaction]:
        """조건에 맞는 거래를 최신순으로 반환한다."""
        if from_date:
            from_date = validate_date(from_date)

        if to_date:
            to_date = validate_date(to_date)

        if transaction_type:
            transaction_type = validate_type(transaction_type)

        results = []

        for transaction in self.transactions.stream():
            if from_date and transaction.date < from_date:
                continue
            if to_date and transaction.date > to_date:
                continue
            if category and transaction.category != category:
                continue
            if transaction_type and transaction.type != transaction_type:
                continue
            if query and query.lower() not in transaction.memo.lower():
                continue
            if tag and tag not in transaction.tags:
                continue

            results.append(transaction)

        return sorted(
            results,
            key=lambda transaction: transaction.date,
            reverse=True,
        )

    def summary(
        self,
        month: str,
        top: int = 3,
    ) -> dict:
        """특정 월의 수입, 지출, 잔액을 집계한다."""
        month = validate_month(month)

        if top <= 0:
            raise ValueError("top은 1 이상이어야 한다.")

        total_income = 0
        total_expense = 0
        category_expenses: dict[str, int] = {}

        for transaction in self.transactions.stream():
            if not transaction.date.startswith(month):
                continue

            if transaction.type == "income":
                total_income += transaction.amount
                continue

            total_expense += transaction.amount
            category_expenses[transaction.category] = (
                category_expenses.get(transaction.category, 0)
                + transaction.amount
            )

        if total_income == 0 and total_expense == 0:
            print(f"[안내] {month} 거래 데이터가 없다.")
            return {}

        budget = next(
            (
                item
                for item in self.budgets.stream()
                if item.month == month
            ),
            None,
        )

        budget_amount = budget.amount if budget else None

        return {
            "month": month,
            "income": total_income,
            "expense": total_expense,
            "balance": total_income - total_expense,
            "budget": budget_amount,
            "budget_usage": (
                total_expense / budget_amount * 100
                if budget_amount
                else None
            ),
            "category_expenses": sorted(
                category_expenses.items(),
                key=lambda item: item[1],
                reverse=True,
            )[:top],
        }

    @handle_errors
    def set_budget(
        self,
        month: str,
        amount: str,
    ) -> bool:
        """월별 예산을 저장한다."""
        month = validate_month(month)
        amount = validate_amount(amount)

        self.budgets.save(
            Budget(
                month=month,
                amount=amount,
            )
        )

        print(f"[저장 완료] {month} 예산 {amount:,}원")
        return True

    @handle_errors
    def add_category(self, name: str) -> bool:
        """카테고리를 추가한다."""
        name = name.strip()

        if not name:
            raise ValueError("카테고리명을 입력해야 한다.")

        if self._category_exists(name):
            raise ValueError("이미 존재하는 카테고리다.")

        self.categories.add(Category(name))

        print(f"[저장 완료] category={name}")
        return True

    def list_categories(self) -> list[str]:
        """등록된 카테고리 목록을 반환한다."""
        return [
            category.name
            for category in self.categories.stream()
        ]

    @handle_errors
    def remove_category(self, name: str) -> bool:
        """사용 중인 카테고리는 삭제하지 않는다."""
        if not self._category_exists(name):
            raise ValueError("존재하지 않는 카테고리다.")

        if any(
            transaction.category == name
            for transaction in self.transactions.stream()
        ):
            raise ValueError(
                "사용 중인 카테고리는 삭제할 수 없다."
            )

        categories = [
            category
            for category in self.categories.stream()
            if category.name != name
        ]

        self.categories.rewrite(categories)

        print(f"[삭제 완료] category={name}")
        return True

    @handle_errors
    def update_transaction(
        self,
        transaction_id: str,
        date: str | None = None,
        transaction_type: str | None = None,
        category: str | None = None,
        amount: str | None = None,
        memo: str | None = None,
        tags: str | None = None,
    ) -> bool:
        """거래 정보를 수정한다."""
        transactions = list(self.transactions.stream())

        target = next(
            (
                transaction
                for transaction in transactions
                if transaction.id == transaction_id
            ),
            None,
        )

        if target is None:
            raise ValueError("해당 ID의 거래가 없다.")

        if date is not None:
            target.date = validate_date(date)

        if transaction_type is not None:
            target.type = validate_type(transaction_type)

        if category is not None:
            if not self._category_exists(category):
                raise ValueError(
                    f"등록되지 않은 카테고리다: {category}"
                )
            target.category = category

        if amount is not None:
            target.amount = validate_amount(amount)

        if memo is not None:
            target.memo = memo

        if tags is not None:
            target.tags = self._parse_tags(tags)

        self.transactions.rewrite(transactions)

        print(f"[수정 완료] id={transaction_id}")
        return True

    @handle_errors
    def delete_transaction(self, transaction_id: str) -> bool:
        """거래를 삭제한다."""
        transactions = list(self.transactions.stream())

        filtered = [
            transaction
            for transaction in transactions
            if transaction.id != transaction_id
        ]

        if len(transactions) == len(filtered):
            raise ValueError("해당 ID의 거래가 없다.")

        self.transactions.rewrite(filtered)

        print(f"[삭제 완료] id={transaction_id}")
        return True

    @handle_errors
    def export_csv(
        self,
        output: str,
        month: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> bool:
        """조건에 맞는 거래를 CSV로 내보낸다."""
        if not month and not (from_date or to_date):
            raise ValueError(
                "--month 또는 --from/--to 조건이 필요하다."
            )

        if month:
            month = validate_month(month)

        if from_date:
            from_date = validate_date(from_date)

        if to_date:
            to_date = validate_date(to_date)

        transactions = self._filter_transactions(
            month,
            from_date,
            to_date,
        )

        fieldnames = [
            "date",
            "type",
            "category",
            "amount",
            "memo",
            "tags",
        ]

        with Path(output).open(
            "w",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
            )
            writer.writeheader()

            for transaction in transactions:
                writer.writerow(
                    {
                        "date": transaction.date,
                        "type": transaction.type,
                        "category": transaction.category,
                        "amount": transaction.amount,
                        "memo": transaction.memo,
                        "tags": ",".join(transaction.tags),
                    }
                )

        print(f"[완료] {output} ({len(transactions)} records)")
        return True

    @handle_errors
    def import_csv(self, input_file: str) -> bool:
        """CSV 파일의 거래 데이터를 가져온다."""
        imported = 0
        skipped = 0

        with Path(input_file).open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(file)
            required = {"date", "type", "category", "amount"}

            if not required.issubset(reader.fieldnames or []):
                raise ValueError("CSV 필수 컬럼이 부족하다.")

            for row in reader:
                try:
                    category = row["category"].strip()

                    if not self._category_exists(category):
                        raise ValueError(
                            f"등록되지 않은 카테고리: {category}"
                        )

                    transaction = Transaction(
                        id=self._generate_id(),
                        date=validate_date(row["date"]),
                        type=validate_type(row["type"]),
                        category=category,
                        amount=validate_amount(row["amount"]),
                        memo=row.get("memo", ""),
                        tags=self._parse_tags(row.get("tags", "")),
                    )

                    self.transactions.add(transaction)
                    imported += 1

                except (ValueError, KeyError):
                    skipped += 1

        print(f"[완료] imported={imported}, skipped={skipped}")
        return True
