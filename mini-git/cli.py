
import hashlib
import shlex
from datetime import datetime, timezone

from algorithms import (
    build_search_indexes,
    find_ancestors,
    merge_sort,
    search_author,
    search_keyword,
    shortest_path,
    topological_sort,
)
from commit import Commit, Repository


class MiniGitCLI:
    def __init__(self) -> None:
        self.repository = Repository()

    def run(self) -> None:
        while True:
            try:
                line = input("mini-git> ").strip()

                if not line:
                    continue

                if line.lower() in {"exit", "quit"}:
                    break

                self.execute(line)

            except (ValueError, IndexError) as error:
                print(f"Error: {error}")
            except EOFError:
                break

    def execute(self, line: str) -> None:
        parts = shlex.split(line)

        if not parts:
            return

        command = parts[0].upper()
        args = parts[1:]

        handlers = {
            "INIT": self.init,
            "BRANCH": self.branch,
            "SWITCH": self.switch,
            "COMMIT": self.commit,
            "LOG": self.log,
            "PATH": self.path,
            "ANCESTORS": self.ancestors,
            "SEARCH": self.search,
        }

        if command not in handlers:
            raise ValueError(f"Unknown command: {command}")

        handlers[command](args)

    def require_repository(self) -> Repository:
        if self.repository.author is None:
            raise ValueError("Run INIT first.")

        return self.repository

    def init(self, args: list[str]) -> None:
        if len(args) != 1:
            raise ValueError("Usage: INIT <user_name>")

        self.repository.init(args[0])
        print(f"Initialized repository for {args[0]}")

    def branch(self, args: list[str]) -> None:
        repository = self.require_repository()

        if len(args) != 1:
            raise ValueError("Usage: BRANCH <branch_name>")

        repository.create_branch(args[0])
        print(f"Created branch {args[0]}")

    def switch(self, args: list[str]) -> None:
        repository = self.require_repository()

        if len(args) != 1:
            raise ValueError("Usage: SWITCH <branch_name>")

        repository.switch_branch(args[0])
        print(f"Switched to {args[0]}")

    def commit(self, args: list[str]) -> None:
        repository = self.require_repository()

        if not args:
            raise ValueError("Usage: COMMIT <message>")

        message = " ".join(args)
        timestamp = datetime.now(timezone.utc)
        parent = repository.get_current_commit()
        parents = [parent.hash] if parent else []

        hash_source = (
            f"{message}|{repository.author}|"
            f"{timestamp.isoformat()}|{parents}"
        )
        commit_hash = hashlib.sha1(
            hash_source.encode("utf-8")
        ).hexdigest()[:7]

        commit = Commit(
            hash=commit_hash,
            message=message,
            author=repository.author,
            timestamp=timestamp,
            parents=parents,
        )

        repository.add_commit(commit)
        print(f"[{repository.current_branch} {commit.hash}] {message}")

    def log(self, args: list[str]) -> None:
        repository = self.require_repository()

        if len(args) > 1:
            raise ValueError("Usage: LOG [--sort-by=date|author]")

        if not args:
            commits = topological_sort(repository.commits)
        elif args[0] == "--sort-by=date":
            commits = merge_sort(
                list(repository.commits.values()),
                "date",
            )
        elif args[0] == "--sort-by=author":
            commits = merge_sort(
                list(repository.commits.values()),
                "author",
            )
        else:
            raise ValueError("Usage: LOG [--sort-by=date|author]")

        for commit in commits:
            print(f"commit {commit.hash}")
            print(f"Author: {commit.author}")
            print(f"Date: {commit.timestamp.isoformat()}")
            print(f"    {commit.message}")
            print()

    def path(self, args: list[str]) -> None:
        repository = self.require_repository()

        if len(args) != 2:
            raise ValueError("Usage: PATH <commit1> <commit2>")

        result = shortest_path(
            args[0],
            args[1],
            repository.commits,
        )

        if result is None:
            print("No path found.")
        else:
            print(" -> ".join(result))

    def ancestors(self, args: list[str]) -> None:
        repository = self.require_repository()

        if len(args) != 1:
            raise ValueError("Usage: ANCESTORS <commit_hash>")

        result = find_ancestors(args[0], repository.commits)

        for commit_hash in sorted(result):
            print(commit_hash)

    def search(self, args: list[str]) -> None:
        repository = self.require_repository()

        if len(args) == 1 and args[0].startswith("--author="):
            author = args[0].split("=", 1)[1]

            if not author:
                raise ValueError("Usage: SEARCH --author=<name>")

            _, author_index = build_search_indexes(repository.commits)
            results = search_author(author, author_index)

        elif len(args) == 1:
            keyword_index, _ = build_search_indexes(repository.commits)
            results = search_keyword(args[0], keyword_index)

        else:
            raise ValueError(
                "Usage: SEARCH <keyword> or SEARCH --author=<name>"
            )

        for commit_hash in results:
            commit = repository.commits[commit_hash]
            print(f"{commit.hash} {commit.author}: {commit.message}")

        if not results:
            print("No matching commits found.")
