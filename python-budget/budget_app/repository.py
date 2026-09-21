import json
from pathlib import Path
from typing import Iterator

from .models import Transaction, Category, Budget


class TransactionRepository:
    """거래 데이터를 transactions.jsonl에 저장한다."""

    def __init__(self, data_dir: str = "data"):
        self.path = Path(data_dir) / "transactions.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def stream(self) -> Iterator[Transaction]:
        """거래 데이터를 한 줄씩 읽는다."""
        with self.path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    yield Transaction(**json.loads(line))

    def add(self, transaction: Transaction) -> None:
        """거래를 추가한다."""
        with self.path.open("a", encoding="utf-8") as file:
            file.write(
                json.dumps(
                    transaction.__dict__,
                    ensure_ascii=False,
                )
                + "\n"
            )

    def rewrite(self, transactions: list[Transaction]) -> None:
        """거래 데이터를 임시 파일에 작성한 후 교체한다."""
        temp_path = self.path.with_suffix(".tmp")

        with temp_path.open("w", encoding="utf-8") as file:
            for transaction in transactions:
                file.write(
                    json.dumps(
                        transaction.__dict__,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

        temp_path.replace(self.path)


class CategoryRepository:
    """카테고리 데이터를 categories.jsonl에 저장한다."""

    def __init__(self, data_dir: str = "data"):
        self.path = Path(data_dir) / "categories.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def stream(self) -> Iterator[Category]:
        """카테고리를 한 줄씩 읽는다."""
        with self.path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    yield Category(**json.loads(line))

    def add(self, category: Category) -> None:
        """카테고리를 추가한다."""
        with self.path.open("a", encoding="utf-8") as file:
            file.write(
                json.dumps(
                    category.__dict__,
                    ensure_ascii=False,
                )
                + "\n"
            )

    def rewrite(self, categories: list[Category]) -> None:
        """카테고리 데이터를 임시 파일에 작성한 후 교체한다."""
        temp_path = self.path.with_suffix(".tmp")

        with temp_path.open("w", encoding="utf-8") as file:
            for category in categories:
                file.write(
                    json.dumps(
                        category.__dict__,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

        temp_path.replace(self.path)


class BudgetRepository:
    """예산 데이터를 budgets.jsonl에 저장한다."""

    def __init__(self, data_dir: str = "data"):
        self.path = Path(data_dir) / "budgets.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def stream(self) -> Iterator[Budget]:
        """예산 데이터를 한 줄씩 읽는다."""
        with self.path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    yield Budget(**json.loads(line))

    def save(self, budget: Budget) -> None:
        """같은 월의 기존 예산을 교체한다."""
        budgets = [
            item
            for item in self.stream()
            if item.month != budget.month
        ]

        budgets.append(budget)
        self.rewrite(budgets)

    def rewrite(self, budgets: list[Budget]) -> None:
        """예산 데이터를 임시 파일에 작성한 후 교체한다."""
        temp_path = self.path.with_suffix(".tmp")

        with temp_path.open("w", encoding="utf-8") as file:
            for budget in budgets:
                file.write(
                    json.dumps(
                        budget.__dict__,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

        temp_path.replace(self.path)
