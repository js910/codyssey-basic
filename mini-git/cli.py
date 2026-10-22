
"""Mini Git 명령어 인터페이스."""

import hashlib
import shlex
from datetime import datetime, timezone

from algorithms import (
    find_ancestors,
    merge_sort,
    search_author,
    search_keyword,
    shortest_path,
    topological_sort,
)
from commit import Commit, Repository


class MiniGitCLI:
    """사용자 명령어를 입력받아 저장소 기능을 실행한다."""

    def __init__(self) -> None:
        # 커밋과 브랜치 정보를 관리할 저장소 객체를 생성
        self.repository = Repository()

    def run(self) -> None:
        """명령어를 반복해서 입력받는 CLI 실행 루프."""
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
        """입력 문자열을 분석하고 해당 명령어의 처리 메서드를 호출한다."""

        # 따옴표로 묶인 문자열을 하나의 인자로 처리
        parts = shlex.split(line)

        if not parts:
            return

        command = parts[0].upper()
        args = parts[1:]

        # 명령어와 실행할 메서드 연결
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
        """저장소가 초기화되었는지 확인하고 저장소 객체를 반환한다."""

        if self.repository.author is None:
            raise ValueError("Run INIT first.")

        return self.repository

    def init(self, args: list[str]) -> None:
        """사용자 이름을 받아 저장소를 초기화한다."""

        if len(args) != 1:
            raise ValueError("Usage: INIT <user_name>")

        self.repository.init(args[0])
        print(f"Initialized repository for {args[0]}")

    def branch(self, args: list[str]) -> None:
        """현재 HEAD를 기준으로 새 브랜치를 생성한다."""

        repository = self.require_repository()

        if len(args) != 1:
            raise ValueError("Usage: BRANCH <branch_name>")

        repository.create_branch(args[0])
        print(f"Created branch {args[0]}")

    def switch(self, args: list[str]) -> None:
        """작업할 브랜치를 변경한다."""

        repository = self.require_repository()

        if len(args) != 1:
            raise ValueError("Usage: SWITCH <branch_name>")

        repository.switch_branch(args[0])
        print(f"Switched to {args[0]}")

    def commit(self, args: list[str]) -> None:
        """새 커밋을 생성하고 현재 브랜치에 추가한다."""

        repository = self.require_repository()

        if not args:
            raise ValueError("Usage: COMMIT <message>")

        message = " ".join(args)

        timestamp = datetime.now(timezone.utc)

        # 현재 브랜치의 HEAD를 부모 커밋으로 지정
        parent = repository.get_current_commit()
        parents = [parent.hash] if parent else []

        # 해시 충돌이 발생하면 다시 생성
        while True:
            timestamp = datetime.now(timezone.utc)

            # 메시지, 작성자, 생성 시각, 부모 정보를 해시 입력으로 사용
            hash_source = (
                f"{message}|{repository.author}|"
                f"{timestamp.isoformat()}|{parents}"
            )

            commit_hash = hashlib.sha1(
                hash_source.encode("utf-8")
            ).hexdigest()[:7]

            # 중복되지 않는 해시를 찾으면 반복을 종료
            if commit_hash not in repository.commits:
                break

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
        """커밋 목록을 출력한다."""

        repository = self.require_repository()

        if len(args) > 1:
            raise ValueError("Usage: LOG [--sort-by=date|author]")

        # 기본 LOG는 커밋의 부모 관계를 고려한 위상 정렬을 사용
        if not args:
            commits = topological_sort(repository.commits)

        # 날짜 기준 정렬은 병합 정렬을 사용
        elif args[0] == "--sort-by=date":
            commits = merge_sort(
                list(repository.commits.values()),
                "date",
            )

        # 작성자 기준 정렬도 병합 정렬을 사용
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
        """두 커밋 사이의 최단 경로를 찾아 출력한다."""

        repository = self.require_repository()

        if len(args) != 2:
            raise ValueError("Usage: PATH <commit1> <commit2>")

        # 커밋 그래프에서 두 커밋 사이의 최단 경로를 탐색
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
        """지정한 커밋의 모든 조상 커밋을 출력한다."""

        repository = self.require_repository()

        if len(args) != 1:
            raise ValueError("Usage: ANCESTORS <commit_hash>")

        result = find_ancestors(args[0], repository.commits)

        # 내장 정렬 API를 쓰지 않고 해시 기준 삽입 정렬로 출력
        ordered_hashes = list(result)
        for index in range(1, len(ordered_hashes)):
            commit_hash = ordered_hashes[index]
            previous = index - 1

            while previous >= 0 and ordered_hashes[previous] > commit_hash:
                ordered_hashes[previous + 1] = ordered_hashes[previous]
                previous -= 1

            ordered_hashes[previous + 1] = commit_hash

        for commit_hash in ordered_hashes:
            print(commit_hash)

    def search(self, args: list[str]) -> None:
        """커밋 메시지의 키워드 또는 작성자로 커밋을 검색한다."""

        repository = self.require_repository()

        # 작성자 검색: SEARCH --author=<name>
        if len(args) == 1 and args[0].startswith("--author="):
            author = args[0].split("=", 1)[1]

            if not author:
                raise ValueError("Usage: SEARCH --author=<name>")

            # 커밋 전체를 다시 순회하지 않고 저장된 작성자 인덱스를 사용
            results = search_author(author, repository.author_index)

        # 키워드 검색: SEARCH <keyword>
        elif len(args) == 1:
            results = search_keyword(
                args[0],
                repository.keyword_index,
            )

        else:
            raise ValueError(
                "Usage: SEARCH <keyword> or SEARCH --author=<name>"
            )

        for commit_hash in results:
            commit = repository.commits[commit_hash]
            print(f"{commit.hash} {commit.author}: {commit.message}")

        if not results:
            print("No matching commits found.")
