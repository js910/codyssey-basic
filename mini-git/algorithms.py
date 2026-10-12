
from collections import deque

from commit import Commit


def topological_sort(commits: dict[str, Commit]) -> list[Commit]:
    """부모 커밋이 자식 커밋보다 먼저 나오도록 정렬한다."""
    children: dict[str, list[str]] = {
        commit_hash: [] for commit_hash in commits
    }
    indegree: dict[str, int] = {
        commit_hash: 0 for commit_hash in commits
    }

    for commit_hash, commit in commits.items():
        for parent_hash in commit.parents:
            if parent_hash in commits:
                children[parent_hash].append(commit_hash)
                indegree[commit_hash] += 1

    queue = deque(
        commit_hash
        for commit_hash in commits
        if indegree[commit_hash] == 0
    )
    result: list[Commit] = []

    while queue:
        commit_hash = queue.popleft()
        result.append(commits[commit_hash])

        for child_hash in children[commit_hash]:
            indegree[child_hash] -= 1

            if indegree[child_hash] == 0:
                queue.append(child_hash)

    if len(result) != len(commits):
        raise ValueError("Commit graph contains a cycle.")

    return result


def find_ancestors(
    commit_hash: str,
    commits: dict[str, Commit],
) -> set[str]:
    """지정한 커밋의 모든 조상 해시를 반환한다."""
    if commit_hash not in commits:
        raise ValueError("Commit does not exist.")

    ancestors: set[str] = set()
    stack = list(commits[commit_hash].parents)

    while stack:
        parent_hash = stack.pop()

        if parent_hash in ancestors:
            continue

        if parent_hash not in commits:
            continue

        ancestors.add(parent_hash)
        stack.extend(commits[parent_hash].parents)

    return ancestors


def shortest_path(
    start_hash: str,
    end_hash: str,
    commits: dict[str, Commit],
) -> list[str] | None:
    """부모 관계를 양방향 간선으로 보고 최단 경로를 찾는다.

    최단 경로가 여러 개면 해시 문자열 기준 사전순으로
    가장 작은 경로를 반환한다.
    """
    if start_hash not in commits or end_hash not in commits:
        raise ValueError("Commit does not exist.")

    if start_hash == end_hash:
        return [start_hash]

    graph: dict[str, set[str]] = {
        commit_hash: set() for commit_hash in commits
    }

    for commit_hash, commit in commits.items():
        for parent_hash in commit.parents:
            if parent_hash in commits:
                graph[commit_hash].add(parent_hash)
                graph[parent_hash].add(commit_hash)

    queue = deque([[start_hash]])
    visited_distance = {start_hash: 0}
    shortest_distance: int | None = None
    candidates: list[list[str]] = []

    while queue:
        path = queue.popleft()
        current = path[-1]
        distance = len(path) - 1

        if shortest_distance is not None and distance >= shortest_distance:
            continue

        neighbors = sorted(graph[current])

        for neighbor in neighbors:
            next_distance = distance + 1

            if neighbor in path:
                continue

            if neighbor == end_hash:
                new_path = path + [neighbor]
                shortest_distance = next_distance
                candidates.append(new_path)
                continue

            previous_distance = visited_distance.get(neighbor)

            if previous_distance is None or next_distance <= previous_distance:
                visited_distance[neighbor] = next_distance
                queue.append(path + [neighbor])

    if not candidates:
        return None

    best_path = candidates[0]

    for candidate in candidates[1:]:
        if candidate < best_path:
            best_path = candidate

    return best_path


def build_search_indexes(
    commits: dict[str, Commit],
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """메시지 키워드 인덱스와 작성자 인덱스를 만든다."""
    keyword_index: dict[str, set[str]] = {}
    author_index: dict[str, set[str]] = {}

    for commit_hash, commit in commits.items():
        for keyword in commit.message.lower().split():
            if keyword not in keyword_index:
                keyword_index[keyword] = set()

            keyword_index[keyword].add(commit_hash)

        author_key = commit.author.lower()

        if author_key not in author_index:
            author_index[author_key] = set()

        author_index[author_key].add(commit_hash)

    return keyword_index, author_index


def search_keyword(
    keyword: str,
    keyword_index: dict[str, set[str]],
) -> set[str]:
    """메시지에 특정 키워드가 포함된 커밋 해시를 반환한다."""
    return keyword_index.get(keyword.lower(), set()).copy()


def search_author(
    author: str,
    author_index: dict[str, set[str]],
) -> set[str]:
    """작성자가 일치하는 커밋 해시를 반환한다."""
    return author_index.get(author.lower(), set()).copy()


def merge_sort(
    items: list[Commit],
    key: str,
) -> list[Commit]:
    """내장 정렬 함수 없이 날짜 또는 작성자 기준으로 정렬한다."""
    if key not in {"date", "author"}:
        raise ValueError("Sort key must be 'date' or 'author'.")

    def sort_key(commit: Commit) -> tuple:
        if key == "date":
            return (commit.timestamp, commit.hash)

        return (commit.author.lower(), commit.hash)

    def divide_and_merge(values: list[Commit]) -> list[Commit]:
        if len(values) <= 1:
            return values

        middle = len(values) // 2
        left = divide_and_merge(values[:middle])
        right = divide_and_merge(values[middle:])

        merged: list[Commit] = []
        left_index = 0
        right_index = 0

        while left_index < len(left) and right_index < len(right):
            if sort_key(left[left_index]) <= sort_key(right[right_index]):
                merged.append(left[left_index])
                left_index += 1
            else:
                merged.append(right[right_index])
                right_index += 1

        merged.extend(left[left_index:])
        merged.extend(right[right_index:])

        return merged

    return divide_and_merge(items)
