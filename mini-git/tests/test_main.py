
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from io import StringIO
from unittest.mock import patch

from algorithms import (
    build_search_indexes,
    find_ancestors,
    merge_sort,
    search_author,
    search_keyword,
    shortest_path,
    topological_sort,
)
from cli import MiniGitCLI
from commit import Commit, Repository


def make_commit(
    commit_hash: str,
    message: str,
    author: str = "Alice",
    parents: list[str] | None = None,
    timestamp: datetime | None = None,
) -> Commit:
    """테스트에 사용할 커밋 객체를 생성한다."""
    return Commit(
        hash=commit_hash,
        message=message,
        author=author,
        timestamp=timestamp or datetime.now(timezone.utc),
        parents=parents or [],
    )


def capture_output(function, *args, **kwargs) -> str:
    """함수 실행 중 출력된 내용을 문자열로 반환한다."""
    output = StringIO()

    with redirect_stdout(output):
        function(*args, **kwargs)

    return output.getvalue()


class RepositoryTests(unittest.TestCase):
    """Repository의 저장소 및 브랜치 관리 기능을 검증한다."""

    def setUp(self) -> None:
        self.repository = Repository()
        self.repository.init("Alice")

    def test_init_creates_empty_main_branch(self) -> None:
        self.assertEqual(self.repository.author, "Alice")
        self.assertEqual(self.repository.current_branch, "main")
        self.assertEqual(self.repository.branches, {"main": ""})
        self.assertEqual(self.repository.commits, {})
        self.assertEqual(self.repository.keyword_index, {})
        self.assertEqual(self.repository.author_index, {})

    def test_init_resets_existing_repository(self) -> None:
        self.repository.add_commit(make_commit("a1", "initial"))
        self.repository.create_branch("feature")

        self.repository.init("Bob")

        self.assertEqual(self.repository.author, "Bob")
        self.assertEqual(self.repository.current_branch, "main")
        self.assertEqual(self.repository.branches, {"main": ""})
        self.assertEqual(self.repository.commits, {})
        self.assertEqual(self.repository.keyword_index, {})
        self.assertEqual(self.repository.author_index, {})

    def test_add_commit_updates_repository_and_main_head(self) -> None:
        commit = make_commit("a1", "Initial Commit")
        self.repository.add_commit(commit)

        self.assertIs(self.repository.commits["a1"], commit)
        self.assertEqual(self.repository.branches["main"], "a1")

    def test_add_commit_updates_keyword_index_case_insensitively(self) -> None:
        self.repository.add_commit(
            make_commit("a1", "Add Login Feature")
        )
        self.repository.add_commit(
            make_commit("b1", "Fix LOGIN")
        )

        self.assertEqual(
            self.repository.keyword_index["login"],
            {"a1", "b1"},
        )
        self.assertEqual(
            self.repository.keyword_index["feature"],
            {"a1"},
        )

    def test_add_commit_updates_author_index_case_insensitively(self) -> None:
        self.repository.add_commit(
            make_commit("a1", "first", author="Alice")
        )
        self.repository.add_commit(
            make_commit("b1", "second", author="ALICE")
        )

        self.assertEqual(
            self.repository.author_index["alice"],
            {"a1", "b1"},
        )

    def test_add_commit_rejects_duplicate_hash(self) -> None:
        self.repository.add_commit(make_commit("a1", "first"))

        with self.assertRaisesRegex(ValueError, "already exists"):
            self.repository.add_commit(make_commit("a1", "duplicate"))

    def test_add_commit_rejects_missing_parent(self) -> None:
        commit = make_commit("b1", "invalid", parents=["missing"])

        with self.assertRaisesRegex(ValueError, "Parent commit not found"):
            self.repository.add_commit(commit)

        self.assertNotIn("b1", self.repository.commits)

    def test_add_commit_rejects_uninitialized_repository(self) -> None:
        repository = Repository()

        with self.assertRaisesRegex(ValueError, "not initialized"):
            repository.add_commit(make_commit("a1", "initial"))

    def test_add_commit_updates_only_current_branch_head(self) -> None:
        self.repository.add_commit(make_commit("a1", "initial"))
        self.repository.create_branch("feature")
        self.repository.switch_branch("feature")
        self.repository.add_commit(
            make_commit("b1", "feature work", parents=["a1"])
        )

        self.assertEqual(self.repository.branches["main"], "a1")
        self.assertEqual(self.repository.branches["feature"], "b1")

    def test_create_branch_copies_current_head(self) -> None:
        self.repository.add_commit(make_commit("a1", "initial"))

        self.repository.create_branch("feature")

        self.assertEqual(self.repository.branches["feature"], "a1")
        self.assertEqual(self.repository.current_branch, "main")

    def test_create_branch_from_empty_repository(self) -> None:
        self.repository.create_branch("feature")

        self.assertEqual(self.repository.branches["feature"], "")

    def test_create_branch_rejects_duplicate_name(self) -> None:
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.repository.create_branch("main")

    def test_create_branch_rejects_uninitialized_repository(self) -> None:
        repository = Repository()

        with self.assertRaisesRegex(ValueError, "not initialized"):
            repository.create_branch("feature")

    def test_switch_branch_changes_current_branch(self) -> None:
        self.repository.create_branch("feature")

        self.repository.switch_branch("feature")

        self.assertEqual(self.repository.current_branch, "feature")

    def test_switch_branch_rejects_unknown_branch(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not exist"):
            self.repository.switch_branch("missing")

    def test_get_commit_returns_commit(self) -> None:
        commit = make_commit("a1", "initial")
        self.repository.add_commit(commit)

        self.assertIs(self.repository.get_commit("a1"), commit)

    def test_get_commit_rejects_unknown_hash(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not exist"):
            self.repository.get_commit("missing")

    def test_get_current_commit_returns_head_commit(self) -> None:
        commit = make_commit("a1", "initial")
        self.repository.add_commit(commit)

        self.assertIs(self.repository.get_current_commit(), commit)

    def test_get_current_commit_returns_none_on_empty_branch(self) -> None:
        self.assertIsNone(self.repository.get_current_commit())

    def test_get_current_commit_returns_none_before_init(self) -> None:
        repository = Repository()

        self.assertIsNone(repository.get_current_commit())


class AlgorithmTests(unittest.TestCase):
    """커밋 그래프, 검색 인덱스, 정렬 알고리즘을 검증한다."""

    def setUp(self) -> None:
        self.commits = {
            "a": make_commit("a", "initial"),
            "b": make_commit("b", "add login", parents=["a"]),
            "c": make_commit("c", "fix login", parents=["b"]),
            "d": make_commit("d", "update docs", parents=["a"]),
        }

    def test_topological_sort_places_parents_before_children(self) -> None:
        result = topological_sort(self.commits)

        self.assertEqual(len(result), len(self.commits))

        positions = {
            commit.hash: index
            for index, commit in enumerate(result)
        }

        for commit in result:
            for parent_hash in commit.parents:
                self.assertLess(
                    positions[parent_hash],
                    positions[commit.hash],
                )

    def test_topological_sort_handles_empty_graph(self) -> None:
        self.assertEqual(topological_sort({}), [])

    def test_topological_sort_detects_cycle(self) -> None:
        commits = {
            "a": make_commit("a", "first", parents=["b"]),
            "b": make_commit("b", "second", parents=["a"]),
        }

        with self.assertRaisesRegex(ValueError, "cycle"):
            topological_sort(commits)

    def test_find_ancestors_returns_all_ancestors(self) -> None:
        self.assertEqual(
            find_ancestors("c", self.commits),
            {"a", "b"},
        )

    def test_find_ancestors_returns_empty_set_for_root(self) -> None:
        self.assertEqual(find_ancestors("a", self.commits), set())

    def test_find_ancestors_rejects_unknown_hash(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not exist"):
            find_ancestors("missing", self.commits)

    def test_find_ancestors_handles_shared_ancestors(self) -> None:
        commits = {
            "a": make_commit("a", "root"),
            "b": make_commit("b", "left", parents=["a"]),
            "c": make_commit("c", "right", parents=["a"]),
            "d": make_commit("d", "merge", parents=["b", "c"]),
        }

        self.assertEqual(
            find_ancestors("d", commits),
            {"a", "b", "c"},
        )

    def test_shortest_path_finds_path_between_commits(self) -> None:
        self.assertEqual(
            shortest_path("c", "d", self.commits),
            ["c", "b", "a", "d"],
        )

    def test_shortest_path_returns_single_node_for_same_commit(self) -> None:
        self.assertEqual(
            shortest_path("a", "a", self.commits),
            ["a"],
        )

    def test_shortest_path_returns_none_when_disconnected(self) -> None:
        commits = {
            "a": make_commit("a", "first"),
            "b": make_commit("b", "second"),
        }

        self.assertIsNone(shortest_path("a", "b", commits))

    def test_shortest_path_rejects_unknown_start(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not exist"):
            shortest_path("missing", "a", self.commits)

    def test_shortest_path_rejects_unknown_end(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not exist"):
            shortest_path("a", "missing", self.commits)

    def test_shortest_path_chooses_lexicographically_smallest_path(self) -> None:
        commits = {
            "a": make_commit("a", "root"),
            "b": make_commit("b", "left", parents=["a"]),
            "c": make_commit("c", "right", parents=["a"]),
            "z": make_commit("z", "target", parents=["b", "c"]),
        }

        self.assertEqual(
            shortest_path("a", "z", commits),
            ["a", "b", "z"],
        )

    def test_build_search_indexes(self) -> None:
        keyword_index, author_index = build_search_indexes(
            self.commits
        )

        self.assertEqual(keyword_index["login"], {"b", "c"})
        self.assertEqual(keyword_index["initial"], {"a"})
        self.assertEqual(author_index["alice"], {"a", "b", "c", "d"})

    def test_build_search_indexes_normalizes_case(self) -> None:
        commits = {
            "a": make_commit("a", "Fix LOGIN", author="Alice"),
            "b": make_commit("b", "fix login", author="ALICE"),
        }

        keyword_index, author_index = build_search_indexes(commits)

        self.assertEqual(keyword_index["fix"], {"a", "b"})
        self.assertEqual(keyword_index["login"], {"a", "b"})
        self.assertEqual(author_index["alice"], {"a", "b"})

    def test_search_keyword_is_case_insensitive(self) -> None:
        keyword_index, _ = build_search_indexes(self.commits)

        self.assertEqual(
            search_keyword("LOGIN", keyword_index),
            {"b", "c"},
        )

    def test_search_keyword_returns_empty_set_for_unknown_word(self) -> None:
        keyword_index, _ = build_search_indexes(self.commits)

        self.assertEqual(search_keyword("missing", keyword_index), set())

    def test_search_keyword_result_does_not_mutate_index(self) -> None:
        keyword_index, _ = build_search_indexes(self.commits)

        result = search_keyword("login", keyword_index)
        result.clear()

        self.assertEqual(keyword_index["login"], {"b", "c"})

    def test_search_author_is_case_insensitive(self) -> None:
        _, author_index = build_search_indexes(self.commits)

        self.assertEqual(
            search_author("ALICE", author_index),
            {"a", "b", "c", "d"},
        )

    def test_search_author_returns_empty_set_for_unknown_author(self) -> None:
        _, author_index = build_search_indexes(self.commits)

        self.assertEqual(search_author("Bob", author_index), set())

    def test_search_author_result_does_not_mutate_index(self) -> None:
        _, author_index = build_search_indexes(self.commits)

        result = search_author("alice", author_index)
        result.clear()

        self.assertEqual(author_index["alice"], {"a", "b", "c", "d"})

    def test_merge_sort_by_author(self) -> None:
        commits = [
            make_commit("b", "second", author="Bob"),
            make_commit("a", "first", author="Alice"),
            make_commit("c", "third", author="alice"),
        ]

        result = merge_sort(commits, "author")

        self.assertEqual(
            [(commit.author.lower(), commit.hash) for commit in result],
            [("alice", "a"), ("alice", "c"), ("bob", "b")],
        )

    def test_merge_sort_by_date(self) -> None:
        earlier = datetime(2024, 1, 1, tzinfo=timezone.utc)
        later = datetime(2025, 1, 1, tzinfo=timezone.utc)

        commits = [
            make_commit("b", "later", timestamp=later),
            make_commit("a", "earlier", timestamp=earlier),
        ]

        result = merge_sort(commits, "date")

        self.assertEqual(
            [commit.hash for commit in result],
            ["a", "b"],
        )

    def test_merge_sort_uses_hash_to_break_date_ties(self) -> None:
        timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
        commits = [
            make_commit("b", "second", timestamp=timestamp),
            make_commit("a", "first", timestamp=timestamp),
        ]

        result = merge_sort(commits, "date")

        self.assertEqual(
            [commit.hash for commit in result],
            ["a", "b"],
        )

    def test_merge_sort_does_not_modify_input(self) -> None:
        commits = [
            make_commit("b", "second", author="Bob"),
            make_commit("a", "first", author="Alice"),
        ]
        original = commits.copy()

        merge_sort(commits, "author")

        self.assertEqual(commits, original)

    def test_merge_sort_rejects_invalid_key(self) -> None:
        with self.assertRaisesRegex(ValueError, "Sort key"):
            merge_sort([], "invalid")


class CLITests(unittest.TestCase):
    """MiniGitCLI의 명령어 처리와 출력을 검증한다."""

    def setUp(self) -> None:
        self.cli = MiniGitCLI()

    def execute_and_capture(self, command: str) -> str:
        return capture_output(self.cli.execute, command)

    def initialize(self) -> None:
        self.execute_and_capture("INIT Alice")

    def test_init_command(self) -> None:
        output = self.execute_and_capture("INIT Alice")

        self.assertEqual(self.cli.repository.author, "Alice")
        self.assertIn("Initialized repository for Alice", output)

    def test_init_requires_exactly_one_argument(self) -> None:
        with self.assertRaisesRegex(ValueError, "Usage: INIT"):
            self.cli.execute("INIT")

        with self.assertRaisesRegex(ValueError, "Usage: INIT"):
            self.cli.execute("INIT Alice Bob")

    def test_unknown_command_raises_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown command"):
            self.cli.execute("UNKNOWN")

    def test_empty_command_does_nothing(self) -> None:
        self.cli.execute("   ")

        self.assertIsNone(self.cli.repository.author)

    def test_commands_require_initialized_repository(self) -> None:
        commands = [
            "BRANCH feature",
            "SWITCH main",
            "COMMIT initial",
            "LOG",
            "PATH a b",
            "ANCESTORS a",
            "SEARCH login",
        ]

        for command in commands:
            with self.subTest(command=command):
                with self.assertRaisesRegex(ValueError, "Run INIT first"):
                    self.cli.execute(command)

    def test_commit_command_preserves_quoted_message(self) -> None:
        self.initialize()

        output = self.execute_and_capture(
            'COMMIT "initial commit with spaces"'
        )

        self.assertEqual(len(self.cli.repository.commits), 1)

        commit = next(iter(self.cli.repository.commits.values()))
        self.assertEqual(commit.message, "initial commit with spaces")
        self.assertEqual(commit.author, "Alice")
        self.assertEqual(commit.parents, [])
        self.assertIn("initial commit with spaces", output)

    def test_commit_command_requires_message(self) -> None:
        self.initialize()

        with self.assertRaisesRegex(ValueError, "Usage: COMMIT"):
            self.cli.execute("COMMIT")

    def test_second_commit_uses_current_head_as_parent(self) -> None:
        self.initialize()
        self.execute_and_capture("COMMIT first")
        self.execute_and_capture("COMMIT second")

        commits = list(self.cli.repository.commits.values())
        second = next(commit for commit in commits if commit.message == "second")

        first = next(commit for commit in commits if commit.message == "first")
        self.assertEqual(second.parents, [first.hash])

    def test_branch_command_creates_branch(self) -> None:
        self.initialize()
        self.execute_and_capture("COMMIT first")

        output = self.execute_and_capture("BRANCH feature")

        self.assertEqual(
            self.cli.repository.branches["feature"],
            self.cli.repository.branches["main"],
        )
        self.assertIn("Created branch feature", output)

    def test_branch_command_requires_one_argument(self) -> None:
        self.initialize()

        with self.assertRaisesRegex(ValueError, "Usage: BRANCH"):
            self.cli.execute("BRANCH")

        with self.assertRaisesRegex(ValueError, "Usage: BRANCH"):
            self.cli.execute("BRANCH feature extra")

    def test_switch_command_changes_branch(self) -> None:
        self.initialize()
        self.execute_and_capture("BRANCH feature")

        output = self.execute_and_capture("SWITCH feature")

        self.assertEqual(self.cli.repository.current_branch, "feature")
        self.assertIn("Switched to feature", output)

    def test_switch_command_requires_one_argument(self) -> None:
        self.initialize()

        with self.assertRaisesRegex(ValueError, "Usage: SWITCH"):
            self.cli.execute("SWITCH")

    def test_log_prints_commits(self) -> None:
        self.initialize()
        self.execute_and_capture("COMMIT first")
        self.execute_and_capture("COMMIT second")

        output = self.execute_and_capture("LOG")

        self.assertIn("Author: Alice", output)
        self.assertIn("first", output)
        self.assertIn("second", output)

    def test_log_supports_date_sort(self) -> None:
        self.initialize()
        self.execute_and_capture("COMMIT first")
        self.execute_and_capture("COMMIT second")

        output = self.execute_and_capture("LOG --sort-by=date")

        self.assertIn("first", output)
        self.assertIn("second", output)

    def test_log_supports_author_sort(self) -> None:
        self.initialize()
        self.execute_and_capture("COMMIT first")

        output = self.execute_and_capture("LOG --sort-by=author")

        self.assertIn("first", output)

    def test_log_rejects_invalid_sort_option(self) -> None:
        self.initialize()

        with self.assertRaisesRegex(ValueError, "Usage: LOG"):
            self.cli.execute("LOG --sort-by=invalid")

        with self.assertRaisesRegex(ValueError, "Usage: LOG"):
            self.cli.execute("LOG extra extra")

    def test_path_command_prints_shortest_path(self) -> None:
        self.initialize()
        self.execute_and_capture("COMMIT first")
        self.execute_and_capture("COMMIT second")

        commits = self.cli.repository.commits
        first = next(c for c in commits.values() if c.message == "first")
        second = next(c for c in commits.values() if c.message == "second")

        output = self.execute_and_capture(
            f"PATH {first.hash} {second.hash}"
        )

        self.assertEqual(
            output.strip(),
            f"{first.hash} -> {second.hash}",
        )

    def test_path_command_rejects_unknown_commit(self) -> None:
        self.initialize()
        self.execute_and_capture("COMMIT first")

        commit_hash = next(iter(self.cli.repository.commits))

        with self.assertRaisesRegex(ValueError, "does not exist"):
            self.cli.execute(f"PATH {commit_hash} missing")

    def test_ancestors_command_requires_one_argument(self) -> None:
        self.initialize()

        with self.assertRaisesRegex(ValueError, "Usage: ANCESTORS"):
            self.cli.execute("ANCESTORS")

    def test_ancestors_command_prints_all_ancestors_in_hash_order(self) -> None:
        self.initialize()
        self.execute_and_capture("COMMIT first")
        self.execute_and_capture("COMMIT second")
        self.execute_and_capture("COMMIT third")

        commits = self.cli.repository.commits
        target = next(c for c in commits.values() if c.message == "third")
        expected = [
            commit.hash
            for commit in commits.values()
            if commit.hash != target.hash
        ]
        if expected[0] > expected[1]:
            expected[0], expected[1] = expected[1], expected[0]

        output = self.execute_and_capture(f"ANCESTORS {target.hash}")

        self.assertEqual(output.splitlines(), expected)

    def test_search_keyword_command(self) -> None:
        self.initialize()
        self.execute_and_capture("COMMIT login")
        self.execute_and_capture("COMMIT documentation")

        output = self.execute_and_capture("SEARCH login")

        self.assertIn("login", output)
        self.assertNotIn("documentation", output)

    def test_search_author_command(self) -> None:
        self.initialize()
        self.execute_and_capture("COMMIT first")

        output = self.execute_and_capture("SEARCH --author=alice")

        self.assertIn("Alice", output)
        self.assertIn("first", output)

    def test_search_rejects_empty_author(self) -> None:
        self.initialize()

        with self.assertRaisesRegex(ValueError, "Usage: SEARCH"):
            self.cli.execute("SEARCH --author=")

    def test_search_rejects_too_many_arguments(self) -> None:
        self.initialize()

        with self.assertRaisesRegex(ValueError, "Usage: SEARCH"):
            self.cli.execute("SEARCH login extra")

    def test_search_reports_no_matching_commits(self) -> None:
        self.initialize()

        output = self.execute_and_capture("SEARCH nonexistent")

        self.assertIn("No matching commits found.", output)

    def test_run_exits_on_quit(self) -> None:
        with patch("builtins.input", side_effect=["quit"]):
            self.cli.run()

    def test_run_reports_invalid_command_and_continues(self) -> None:
        with patch(
            "builtins.input",
            side_effect=["UNKNOWN", "quit"],
        ):
            output = capture_output(self.cli.run)

        self.assertIn("Error: Unknown command", output)

    def test_run_exits_on_eof(self) -> None:
        with patch("builtins.input", side_effect=EOFError):
            self.cli.run()


if __name__ == "__main__":
    unittest.main()
