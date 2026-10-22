
"""커밋 정보와 저장소의 브랜치 및 검색 인덱스"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Commit:
    """커밋 하나의 정보와 부모 커밋 관계를 저장한다."""
    hash: str
    message: str
    author: str
    timestamp: datetime
    parents: list[str] = field(default_factory=list)


class Repository:
    """커밋, 브랜치, 현재 사용자 및 검색 인덱스를 관리한다."""

    def __init__(self) -> None:
        self.commits: dict[str, Commit] = {}
        self.branches: dict[str, str] = {}
        self.current_branch: str | None = None
        self.author: str | None = None

        # 검색할 키워드나 작성자로 관련 커밋을 빠르게 찾기 위한 역색인
        self.keyword_index: dict[str, set[str]] = {}
        self.author_index: dict[str, set[str]] = {}

    def init(self, author: str) -> None:
        """저장소를 초기화하고 main 브랜치와 사용자를 설정한다."""
        self.commits.clear()
        self.branches.clear()
        self.keyword_index.clear()
        self.author_index.clear()

        self.author = author
        self.current_branch = "main"
        self.branches["main"] = ""

    def add_commit(self, commit: Commit) -> None:
        """커밋을 저장하고 현재 브랜치와 검색 인덱스를 갱신한다."""

        if self.current_branch is None:
            raise ValueError("Repository is not initialized.")

        if commit.hash in self.commits:
            raise ValueError("Commit hash already exists.")

        for parent_hash in commit.parents:
            if parent_hash not in self.commits:
                raise ValueError(
                    f"Parent commit not found: {parent_hash}"
                )

        self.commits[commit.hash] = commit

        # 현재 브랜치가 새 커밋을 가리키도록 HEAD를 갱신
        self.branches[self.current_branch] = commit.hash

        for keyword in commit.message.lower().split():
            # 처음 등장한 키워드라면 집합을 생성
            if keyword not in self.keyword_index:
                self.keyword_index[keyword] = set()

            self.keyword_index[keyword].add(commit.hash)

        author_key = commit.author.lower()

        # 처음 등장한 작성자라면 집합을 생성
        if author_key not in self.author_index:
            self.author_index[author_key] = set()

        self.author_index[author_key].add(commit.hash)

    def create_branch(self, branch_name: str) -> None:
        """현재 브랜치의 HEAD를 가리키는 새 브랜치를 생성한다."""

        if self.current_branch is None:
            raise ValueError("Repository is not initialized.")

        if branch_name in self.branches:
            raise ValueError("Branch already exists.")

        self.branches[branch_name] = self.branches[
            self.current_branch
        ]

    def switch_branch(self, branch_name: str) -> None:
        """현재 작업 브랜치를 지정한 브랜치로 변경한다."""

        if branch_name not in self.branches:
            raise ValueError("Branch does not exist.")

        self.current_branch = branch_name

    def get_commit(self, commit_hash: str) -> Commit:
        """해시로 커밋을 조회한다."""

        if commit_hash not in self.commits:
            raise ValueError("Commit does not exist.")

        return self.commits[commit_hash]

    def get_current_commit(self) -> Commit | None:
        """현재 브랜치의 HEAD에 해당하는 커밋을 반환한다."""

        if self.current_branch is None:
            return None

        commit_hash = self.branches[self.current_branch]

        if not commit_hash:
            return None

        return self.commits[commit_hash]
