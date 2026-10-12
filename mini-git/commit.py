
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Commit:
    hash: str
    message: str
    author: str
    timestamp: datetime
    parents: list[str] = field(default_factory=list)


class Repository:
    def __init__(self) -> None:
        self.commits: dict[str, Commit] = {}
        self.branches: dict[str, str] = {}
        self.current_branch: str | None = None
        self.author: str | None = None

    def init(self, author: str) -> None:
        self.commits.clear()
        self.branches.clear()

        self.author = author
        self.current_branch = "main"
        self.branches["main"] = ""

    def add_commit(self, commit: Commit) -> None:
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
        self.branches[self.current_branch] = commit.hash

    def create_branch(self, branch_name: str) -> None:
        if self.current_branch is None:
            raise ValueError("Repository is not initialized.")

        if branch_name in self.branches:
            raise ValueError("Branch already exists.")

        self.branches[branch_name] = self.branches[
            self.current_branch
        ]

    def switch_branch(self, branch_name: str) -> None:
        if branch_name not in self.branches:
            raise ValueError("Branch does not exist.")

        self.current_branch = branch_name

    def get_commit(self, commit_hash: str) -> Commit:
        if commit_hash not in self.commits:
            raise ValueError("Commit does not exist.")

        return self.commits[commit_hash]

    def get_current_commit(self) -> Commit | None:
        if self.current_branch is None:
            return None

        commit_hash = self.branches[self.current_branch]

        if not commit_hash:
            return None

        return self.commits[commit_hash]
