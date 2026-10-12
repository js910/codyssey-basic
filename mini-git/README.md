# Mini Git

Python으로 구현한 간단한 Git 스타일 CLI 프로그램입니다. 커밋과 브랜치를 관리하고, 커밋 그래프 탐색, 검색, 정렬 기능을 제공합니다.

## 1. 실행 환경

- Python 3.10 이상

## 2. 실행 방법

프로젝트 루트 디렉터리에서 다음 명령어를 실행합니다.

```bash
python main.py
```

프로그램이 실행되면 `mini-git>` 프롬프트에서 명령어를 입력할 수 있습니다.

## 3. 지원 명령어

| 명령어 | 설명 |
|---|---|
| `INIT <user_name>` | 저장소를 초기화하고 작성자를 설정합니다. |
| `BRANCH <branch_name>` | 새 브랜치를 생성합니다. |
| `SWITCH <branch_name>` | 작업 브랜치를 변경합니다. |
| `COMMIT <message>` | 새 커밋을 생성합니다. |
| `LOG` | 커밋을 위상 정렬 순서로 출력합니다. |
| `LOG --sort-by=date` | 날짜 기준으로 커밋을 정렬합니다. |
| `LOG --sort-by=author` | 작성자 기준으로 커밋을 정렬합니다. |
| `PATH <commit1> <commit2>` | 두 커밋 사이의 최단 경로를 찾습니다. |
| `ANCESTORS <commit_hash>` | 지정한 커밋의 모든 조상을 출력합니다. |
| `SEARCH <keyword>` | 커밋 메시지에서 키워드를 검색합니다. |
| `SEARCH --author=<name>` | 작성자로 커밋을 검색합니다. |
| `exit` 또는 `quit` | 프로그램을 종료합니다. |

## 4. 사용 예시

```text
mini-git> INIT Alice
mini-git> COMMIT "initial commit"
mini-git> COMMIT "add login"
mini-git> BRANCH feature
mini-git> SWITCH feature
mini-git> COMMIT "implement feature"
mini-git> LOG
mini-git> SEARCH login
mini-git> exit
```

## 5. 데이터 구조

### Commit

각 커밋은 다음 필드를 가집니다.

- `hash`: 커밋 식별자
- `message`: 커밋 메시지
- `author`: 작성자
- `timestamp`: 커밋 생성 시각
- `parents`: 부모 커밋 해시 목록

### Repository

- `commits`: 커밋 해시를 키로 사용하는 딕셔너리
- `branches`: 브랜치 이름과 최신 커밋 해시를 연결하는 딕셔너리
- `current_branch`: 현재 작업 중인 브랜치

## 6. 알고리즘

- **위상 정렬**: 부모 커밋이 자식 커밋보다 먼저 나오도록 정렬합니다.
- **DFS**: 지정한 커밋의 조상을 탐색합니다.
- **BFS**: 부모 연결을 양방향으로 간주해 최단 경로를 찾습니다.
- **역색인**: 메시지 키워드와 작성자별로 커밋 해시를 관리합니다.
- **병합 정렬**: Python 내장 정렬 함수 대신 날짜 또는 작성자 기준 정렬을 구현합니다.

## 7. 저장 방식

커밋과 브랜치 정보는 메모리에 저장됩니다. 프로그램을 종료하면 데이터가 사라집니다.

## 8. 테스트

테스트는 Python의 `unittest`를 사용해 실행할 수 있습니다.

```bash
python -m unittest discover -s tests -v
```
