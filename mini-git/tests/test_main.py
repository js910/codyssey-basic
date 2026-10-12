
import unittest
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
from cli import MiniGitCLI
from commit import Commit, Repository


def make_commit(
    commit_hash: str,
    message: str,
    author: str = "Alice",
    parents: list[str] | None = None,
    timestamp: datetime | None = None,
) -> Commit:
    return Commit(
        hash=commit_hash,
        message=message,
        author=author,
        timestamp=timestamp or datetime.now(timezone.utc),
        parents=parents or [],
    )


class RepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = Repository()
        self.repository.init("Alice")

    def test_init_creates_main_branch(self) -> None:
        self.assertEqual(self.repository.author, "Alice")
        self.assertEqual(self.repository.current_branch, "main")
        self.assertIn("main", self.repository.branches)

    def test_add_commit_updates_branch(self) -> None:
        commit = make_commit("a1", "initial")
        self.repository.add_commit(commit)

        self.assertIn("a1", self.repository.commits)
        self.assertEqual(self.repository.branches["main"], "a1")

    def test_create_and_switch_branch(self) -> None:
        self.repository.add_commit(make_commit("a1", "initial"))
        self.repository.create_branch("feature")
        self.repository.switch_branch("feature")

        self.assertEqual(self.repository.current_branch, "feature")
        self.assertEqual(self.repository.branches["feature"], "a1")

    def test_duplicate_branch_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            self.repository.create_branch("main")

    def test_missing_parent_raises_error(self) -> None:
        commit = make_commit("b1", "invalid", parents=["missing"])

        with self.assertRaises(ValueError):
            self.repository.add_commit(commit)


class AlgorithmTests(unittest.TestCase):
    def setUp(self) -> None:
        self.commits = {
            "a": make_commit("a", "initial"),
            "b": make_commit("b", "add login", parents=["a"]),
            "c": make_commit("c", "fix login", parents=["b"]),
            "d": make_commit("d", "update docs", parents=["a"]),
        }

    def test_topological_sort_places_parents_first(self) -> None:
        result = topological_sort(self.commits)
        positions = {
            commit.hash: index
            for index, commit in enumerate(result)
        }

        for commit in result:
            for parent in commit.parents:
                self.assertLess(positions[parent], positions[commit.hash])

    def test_find_ancestors(self) -> None:
        self.assertEqual(find_ancestors("c", self.commits), {"a", "b"})

    def test_shortest_path(self) -> None:
        self.assertEqual(shortest_path("c", "d", self.commits), ["c", "b", "a", "d"])

    def test_shortest_path_for_same_commit(self) -> None:
        self.assertEqual(shortest_path("a", "a", self.commits), ["a"])

    def test_shortest_path_when_disconnected(self) -> None:
        commits = {
            "a": make_commit("a", "first"),
            "b": make_commit("b", "second"),
        }

        self.assertIsNone(shortest_path("a", "b", commits))

    def test_keyword_search(self) -> None:
        keyword_index, _ = build_search_indexes(self.commits)
        self.assertEqual(search_keyword("LOGIN", keyword_index), {"b", "c"})

    def test_author_search(self) -> None:
        _, author_index = build_search_indexes(self.commits)
        self.assertEqual(search_author("alice", author_index), {"a", "b", "c", "d"})

    def test_merge_sort_by_author(self) -> None:
        commits = [
            make_commit("b", "second", author="Bob"),
            make_commit("a", "first", author="Alice"),
        ]

        result = merge_sort(commits, "author")
        self.assertEqual([commit.author for commit in result], ["Alice", "Bob"])

    def test_merge_sort_by_date(self) -> None:
        earlier = datetime(2024, 1, 1, tzinfo=timezone.utc)
        later = datetime(2025, 1, 1, tzinfo=timezone.utc)

        commits = [
            make_commit("b", "later", timestamp=later),
            make_commit("a", "earlier", timestamp=earlier),
        ]

        result = merge_sort(commits, "date")
        self.assertEqual([commit.hash for commit in result], ["a", "b"])


class CLITests(unittest.TestCase):
    def setUp(self) -> None:
        self.cli = MiniGitCLI()

    def test_init_command(self) -> None:
        self.cli.execute("INIT Alice")
        self.assertEqual(self.cli.repository.author, "Alice")

    def test_commit_command(self) -> None:
        self.cli.execute("INIT Alice")
        self.cli.execute('COMMIT "initial commit"')

        self.assertEqual(len(self.cli.repository.commits), 1)
        commit = next(iter(self.cli.repository.commits.values()))
        self.assertEqual(commit.message, "initial commit")
        self.assertEqual(commit.author, "Alice")

    def test_commit_command_requires_message(self) -> None:
        self.cli.execute("INIT Alice")

        with self.assertRaises(ValueError):
            self.cli.execute("COMMIT")


if __name__ == "__main__":
    unittest.main()
