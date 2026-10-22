
"""커밋 그래프 탐색, 검색 인덱스, 정렬 알고리즘을 제공한다."""

from collections import deque

from commit import Commit


def topological_sort(commits: dict[str, Commit]) -> list[Commit]:
    """부모 커밋이 자식 커밋보다 먼저 나오도록 위상 정렬한다."""

    # 각 커밋의 자식 커밋 목록을 저장
    children: dict[str, list[str]] = {
        commit_hash: [] for commit_hash in commits
    }

    # 각 커밋의 부모 개수(진입 차수)를 저장
    indegree: dict[str, int] = {
        commit_hash: 0 for commit_hash in commits
    }

    # 부모와 자식의 연결 관계를 만들고 진입 차수를 계산
    for commit_hash, commit in commits.items():
        for parent_hash in commit.parents:
            if parent_hash in commits:
                children[parent_hash].append(commit_hash)
                indegree[commit_hash] += 1

    # 부모가 없는 커밋부터 탐색 (deque 사용)
    queue = deque(
        commit_hash
        for commit_hash in commits
        if indegree[commit_hash] == 0
    )
    result: list[Commit] = []

    while queue:
        # 진입 차수가 0인 커밋을 꺼내 결과에 추가
        commit_hash = queue.popleft()
        result.append(commits[commit_hash])

        # 해당 커밋의 자식들은 부모 하나를 처리한 것으로 간주
        for child_hash in children[commit_hash]:
            indegree[child_hash] -= 1

            # 모든 부모를 처리했다면 다음 탐색 대상으로 추가
            if indegree[child_hash] == 0:
                queue.append(child_hash)

    # 모든 커밋을 처리하지 못했다면 순환 관계
    if len(result) != len(commits):
        raise ValueError("Commit graph contains a cycle.")

    return result


def find_ancestors(
    commit_hash: str,
    commits: dict[str, Commit],
) -> set[str]:
    """지정한 커밋의 모든 조상 커밋 해시를 반환한다."""

    if commit_hash not in commits:
        raise ValueError("Commit does not exist.")

    ancestors: set[str] = set()

    # 시작 커밋의 부모부터 역방향으로 탐색
    stack = list(commits[commit_hash].parents)

    while stack:
        parent_hash = stack.pop()

        # 이미 방문한 커밋
        if parent_hash in ancestors:
            continue

        # 저장소에 없는 해시
        if parent_hash not in commits:
            continue

        # 현재 부모를 조상 목록에 추가, 부모 탐색
        ancestors.add(parent_hash)
        stack.extend(commits[parent_hash].parents)

    return ancestors


def shortest_path(
    start_hash: str,
    end_hash: str,
    commits: dict[str, Commit],
) -> list[str] | None:
    """부모 관계를 양방향 간선으로 보고 최단 경로를 찾는다.

    최단 경로가 여러 개면 해시 문자열 기준 사전순으로 가장 작은 경로를 반환한다.
    """

    if start_hash not in commits or end_hash not in commits:
        raise ValueError("Commit does not exist.")

    # 시작점과 도착점이 같을 때
    if start_hash == end_hash:
        return [start_hash]

    # 커밋을 정점으로, 부모 관계를 양방향 간선으로 표현
    graph: dict[str, set[str]] = {
        commit_hash: set() for commit_hash in commits
    }

    for commit_hash, commit in commits.items():
        for parent_hash in commit.parents:
            if parent_hash in commits:
                # 자식에서 부모로 이동할 수 있도록 연결
                graph[commit_hash].add(parent_hash)

                # 부모에서 자식으로도 이동할 수 있도록 연결
                graph[parent_hash].add(commit_hash)

    # BFS에 사용할 큐에는 현재까지의 전체 경로를 저장
    queue = deque([[start_hash]])

    # 시작점에서 각 커밋까지 발견한 최단 거리 기록
    visited_distance = {start_hash: 0}

    # 가장 짧은 경로의 길이와 해당 길이를 가진 경로들 저장
    shortest_distance: int | None = None
    candidates: list[list[str]] = []

    # BFS: 간선 수가 적은 경로부터 탐색
    while queue:
        path = queue.popleft()
        current = path[-1]
        distance = len(path) - 1

        # 최단 경로 길이에 도달했으면 더 긴 경로는 탐색하지 않음
        if shortest_distance is not None and distance >= shortest_distance:
            continue

        # 현재 커밋과 연결된 이웃 커밋 목록
        neighbors = list(graph[current])

        # sorted() 대신 삽입 정렬을 사용해 해시를 사전순으로 정렬
        for i in range(1, len(neighbors)):
            current_hash = neighbors[i]
            j = i - 1

            # 현재 해시보다 큰 값을 오른쪽으로 이동
            while j >= 0 and neighbors[j] > current_hash:
                neighbors[j + 1] = neighbors[j]
                j -= 1

            # 비어 있는 위치에 현재 해시를 삽입
            neighbors[j + 1] = current_hash

        for neighbor in neighbors:
            next_distance = distance + 1

            # 이미 방문한 정점
            if neighbor in path:
                continue

            # 도착점에 도달하면 경로를 후보에 저장
            if neighbor == end_hash:
                new_path = path + [neighbor]
                shortest_distance = next_distance
                candidates.append(new_path)
                continue

            # 이전에 발견한 거리와 비교
            previous_distance = visited_distance.get(neighbor)

            if previous_distance is None or next_distance <= previous_distance:
                visited_distance[neighbor] = next_distance
                queue.append(path + [neighbor])

    # 도착점에 도달할 수 없음
    if not candidates:
        return None

    # 여러 최단 경로가 있다면 경로 전체를 사전순으로 비교
    best_path = candidates[0]

    for candidate in candidates[1:]:
        if candidate < best_path:
            best_path = candidate

    return best_path


def build_search_indexes(
    commits: dict[str, Commit],
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """메시지 키워드 인덱스와 작성자 인덱스를 생성한다."""

    # 키워드 또는 작성자를 키로, 해당 커밋 해시 집합을 값으로 저장
    keyword_index: dict[str, set[str]] = {}
    author_index: dict[str, set[str]] = {}

    for commit_hash, commit in commits.items():
        for keyword in commit.message.lower().split():
            # 처음 등장한 키워드라면 해시 집합 생성
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
    """특정 키워드가 등록된 커밋 해시 집합을 반환한다."""

    # copy() 사용: 원본 인덱스의 집합이 변경되지 않도록
    return keyword_index.get(keyword.lower(), set()).copy()


def search_author(
    author: str,
    author_index: dict[str, set[str]],
) -> set[str]:
    """특정 작성자가 등록된 커밋 해시 집합을 반환한다."""

    return author_index.get(author.lower(), set()).copy()


def merge_sort(
    items: list[Commit],
    key: str,
) -> list[Commit]:
    """내장 정렬 함수 없이 날짜 또는 작성자 기준으로 정렬한다."""

    if key not in {"date", "author"}:
        raise ValueError("Sort key must be 'date' or 'author'.")

    def sort_key(commit: Commit) -> tuple:
        """정렬 기준과 해시를 묶어 비교용 키를 만든다."""

        if key == "date":
            # 날짜가 같으면 해시 기준
            return (commit.timestamp, commit.hash)

        return (commit.author.lower(), commit.hash)

    def divide_and_merge(values: list[Commit]) -> list[Commit]:
        """리스트를 나눈 뒤 정렬된 두 부분을 병합한다."""

        # 원소가 0개 또는 1개면 이미 정렬된 상태
        if len(values) <= 1:
            return values

        # 리스트를 가운데 기준으로 두 부분으로 나눈다
        middle = len(values) // 2
        left = divide_and_merge(values[:middle])
        right = divide_and_merge(values[middle:])

        merged: list[Commit] = []
        left_index = 0
        right_index = 0

        # 두 부분의 현재 원소를 비교해 작은 것부터 결과에 추가
        while left_index < len(left) and right_index < len(right):
            if sort_key(left[left_index]) <= sort_key(right[right_index]):
                merged.append(left[left_index])
                left_index += 1
            else:
                merged.append(right[right_index])
                right_index += 1

        # 한쪽에 남은 원소들을 결과 뒤에 이어 붙인다
        merged.extend(left[left_index:])
        merged.extend(right[right_index:])

        return merged

    # 분할과 병합을 반복해 정렬된 새 리스트 반환
    return divide_and_merge(items)
