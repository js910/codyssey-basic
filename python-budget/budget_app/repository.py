import json
from collections.abc import Iterator
from pathlib import Path

from .models import Budget, Category, Transaction


class BaseRepository:
    """공통 파일 I/O 및 안전한 쓰기(Atomic Write)를 담당하는 베이스 클래스"""

    def __init__(self, filename: str, model_class, data_dir: str = "data"):
        self.path = Path(data_dir) / filename
        self.model_class = model_class
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def stream(self) -> Iterator:
        """데이터를 한 줄씩 읽는다."""
        with self.path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    yield self.model_class(**json.loads(line))

    def add(self, item) -> None:
        """데이터를 파일 끝에 추가한다."""
        with self.path.open("a", encoding="utf-8") as file:
            file.write(
                json.dumps(
                    item.__dict__,
                    ensure_ascii=False,
                )
                + "\n"
            )

    def rewrite(self, items: list) -> None:
        """데이터를 임시 파일(.tmp)에 작성한 후 원본 파일로 안전하게 교체한다."""
        temp_path = self.path.with_suffix(".tmp")

        with temp_path.open("w", encoding="utf-8") as file:
            for item in items:
                file.write(
                    json.dumps(
                        item.__dict__,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

        temp_path.replace(self.path)


class TransactionRepository(BaseRepository):
    """거래 데이터를 transactions.jsonl에 저장한다."""

    def __init__(self, data_dir: str = "data"):
        super().__init__("transactions.jsonl", Transaction, data_dir)


class CategoryRepository(BaseRepository):
    """카테고리 데이터를 categories.jsonl에 저장한다."""

    def __init__(self, data_dir: str = "data"):
        super().__init__("categories.jsonl", Category, data_dir)


class BudgetRepository(BaseRepository):
    """예산 데이터를 budgets.jsonl에 저장한다."""

    def __init__(self, data_dir: str = "data"):
        super().__init__("budgets.jsonl", Budget, data_dir)

    def save(self, budget: Budget) -> None:
        """같은 월의 기존 예산을 교체한다."""
        budgets = [item for item in self.stream() if item.month != budget.month]
        budgets.append(budget)
        self.rewrite(budgets)
