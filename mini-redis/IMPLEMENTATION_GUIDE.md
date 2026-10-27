# Mini Redis 구현 설명 및 평가 준비

## 프로젝트 소개

> 문자열 키에 값을 저장하고 조회하는 CLI 프로그램입니다. 해시맵, 이중 연결 리스트, 최소 힙을 직접 구현했습니다. 해시맵으로 데이터를 찾고, 연결 리스트로 최근 사용 순서를 관리하며, 최소 힙으로 가장 먼저 만료될 키를 찾습니다. 메모리는 키와 값의 UTF-8 바이트 수를 합산합니다.

```text
main.py                         프로그램 시작
mini_redis/cli.py               입력 분리, 명령 검사, 결과 출력
mini_redis/store.py             데이터, LRU, TTL, 메모리 관리
mini_redis/structures/
    hash_map.py                체이닝 해시맵
    linked_list.py             이중 연결 리스트
    min_heap.py                최소 힙
tests/test_mini_redis.py        자동 테스트
```

```powershell
python main.py
```

현재 테스트는 11개입니다. 핵심 구현에서 `dict`, `set`, `collections`, `heapq`를 사용하지 않습니다. 파이썬 리스트는 배열 저장 공간으로 사용합니다. `Store.set()`의 set은 저장 메서드 이름이며 내장 집합 자료형이 아닙니다.

## 항목 1: 기능 완성도 시연

### 1-1. String 기본 명령 6개

**관련 코드**

- `cli.py`: [CLI.execute()](mini_redis/cli.py#L29)
- `store.py`: [Store.set()](mini_redis/store.py#L56), [get()](mini_redis/store.py#L71), [delete()](mini_redis/store.py#L80), [exists()](mini_redis/store.py#L85)
- `structures/hash_map.py`: [size()](mini_redis/structures/hash_map.py#L75), [keys()](mini_redis/structures/hash_map.py#L67)

**시연**

```text
SET name "Alice Kim"
GET name
EXISTS name
DBSIZE
KEYS
DEL name
GET name
```

> SET은 값을 저장하고 GET은 값을 가져옵니다. EXISTS는 존재 여부, DBSIZE는 키 개수, KEYS는 키 목록을 반환합니다. DEL은 데이터를 삭제합니다. 명령 실행 전에 만료된 키를 정리하므로, 만료된 키는 목록과 개수에도 포함되지 않습니다. 마지막 GET은 없는 키이므로 nil입니다.

`KEYS`는 버킷과 항목을 순회합니다. 버킷 수를 b, 키 수를 n이라 하면 순회 비용은 O(b+n)이며 출력 비용도 추가됩니다.

### 1-2. LRU 자동 제거

**관련 코드**

- [Store.get()](mini_redis/store.py#L71): `self.lru.move_to_front(entry.node)`
- [Store.set()](mini_redis/store.py#L56): 메모리 제한 초과 시 반복 삭제
- [Store._delete()](mini_redis/store.py#L29): 데이터와 리스트 삭제, 메모리 차감

**시연**

```text
CONFIG SET maxmemory 4
SET a 1
SET b 2
GET a
SET c 3
GET b
INFO memory
```

> 각 항목은 키 1바이트와 값 1바이트로 총 2바이트입니다. a와 b를 저장한 뒤 a를 조회하면 a가 최근 사용한 키가 됩니다. c를 추가하면 총 6바이트가 되어 가장 오래 사용하지 않은 b를 삭제합니다. 삭제한 크기만큼 사용량을 줄이고 evicted_keys를 1 증가시킵니다.

```text
SET a → a
SET b → b ⇄ a
GET a → a ⇄ b
SET c → c ⇄ a ⇄ b → b 제거
```

앞이 MRU(가장 최근 사용), 뒤가 LRU(가장 오래 사용하지 않음)입니다. 성공한 SET과 GET만 사용 순서를 갱신합니다.

### 1-3. 메모리 정보와 UTF-8 공식

**관련 코드**

- [Entry.init()](mini_redis/store.py#L9): `self.bytes`
- [Store.set()](mini_redis/store.py#L56): 사용량 증가
- [Store._delete()](mini_redis/store.py#L29): 사용량 감소
- [CLI.execute()](mini_redis/cli.py#L29)의 INFO 처리

**시연**

```text
SET 가 나
INFO memory
```

> 글자 수가 아니라 UTF-8 바이트 수를 계산합니다. 영문 a와 숫자는 각각 1바이트이고 한글 가는 3바이트입니다. 입력을 구분하는 공백과 명령어는 저장하지 않습니다. 값을 덮어쓰면 이전 크기를 빼고 새 크기를 더합니다. 노드와 포인터의 크기는 과제 공식에서 제외합니다.

### 1-4. TTL과 lazy deletion

**관련 코드**

- `store.py`: [Store.expire()](mini_redis/store.py#L90), [ttl()](mini_redis/store.py#L105), **[purge_expired()](mini_redis/store.py#L39)**
- `structures/min_heap.py`: [peek()](mini_redis/structures/min_heap.py#L11), [push()](mini_redis/structures/min_heap.py#L15), [pop()](mini_redis/structures/min_heap.py#L20)

**시연**

```text
SET temp value
TTL temp
EXPIRE temp 3
TTL temp
```

3초를 기다린 뒤 다음 명령을 입력합니다.

```text
GET temp
TTL temp
```

- 만료 설정 전 TTL: `(integer) -1`
- 만료 후 GET: `(nil)`
- 만료 후 TTL: `(integer) -2`

> 힙에는 만료 시각, 키, 기록 번호를 저장합니다. 만료 시간을 다시 설정하면 이전 기록을 힙 중간에서 바로 지우지 않고 새 기록을 추가합니다. 이전 기록을 꺼냈을 때 현재 기록 번호와 다르면 무시합니다. 이것이 lazy deletion입니다.

데이터 해시맵의 `Entry.expire_at`, `Entry.version`에 최신 상태를 저장합니다.

**힙을 다시 만드는 시점**

```python
self.expirations.size() > max(64, self.data.size() * 2)
```

`purge_expired()`에서 검사합니다. 키 10개면 기록 65개 이상, 키 100개면 기록 201개 이상일 때 현재 유효한 만료 기록만 새 힙에 넣습니다.  재구성은 버킷 순회와 반복 push 비용이 듭니다.

**TTL 출력 규칙**

| 상황 | 의미 |
| --- | --- |
| `TTL a`가 -1 | 키는 있으나 만료 시간 없음 |
| `TTL a`가 -2 | 키 없음 |
| `TTL a`가 0 | 남은 시간이 1초 미만일 수 있음 |

양수 TTL의 시간이 지난 경우에는 다음 명령 실행 시 삭제합니다. GET뿐 아니라 KEYS와 DBSIZE도 정리하므로 만료된 키가 목록이나 개수에 출력되지 않습니다.

### 1-5. 에러 처리

**관련 코드**

- [CLI.execute()](mini_redis/cli.py#L29): cli 명령어 검사, `command_specs`
- [parse_integer()](mini_redis/cli.py#L11): cli 정수 형식과 64비트 범위 검사
- [Store.set()](mini_redis/store.py#L56): store 단일 항목 크기 검사

**시연**

```text
HELLO
GET
CONFIG SET maxmemory abc
CONFIG SET maxmemory 3
SET long value
```

> 알 수 없는 명령어, 인자 개수 오류, 정수 입력 오류를 구분합니다. SET은 새 항목 하나가 제한을 넘는지 먼저 검사합니다. 넘으면 기존 같은 키의 값과 TTL을 바꾸거나 다른 키를 제거하지 않고 OOM을 반환합니다.

최대 메모리 입력에는 음수를 허용하지 않습니다. EXPIRE의 음수는 즉시 삭제로 처리합니다. 큰따옴표가 닫히지 않으면 입력 형식 오류를 반환합니다.

## 항목 2: 기본 자료구조 설명

### 2-1. 이중 연결 리스트가 O(1)인 이유

**관련 코드**

- `structures.linked_list.py`: [Node](mini_redis/structures/linked_list.py#L2), [remove_node()](mini_redis/structures/linked_list.py#L42), [move_to_front()](mini_redis/structures/linked_list.py#L66)

> 각 노드는 prev, next, data를 가집니다. 삭제할 노드를 이미 알고 있다면 양옆 연결만 바꾸면 되므로 전체 목록을 순회하지 않습니다. 맨 앞으로 이동할 때도 일정한 수의 연결만 수정하므로 O(1)입니다. 만약 노드부터 찾아야 한다면 검색은 O(n)입니다.

```text
head → [A] ⇄ [B] ⇄ [C] ← tail
```

head와 tail은 첫 노드와 마지막 노드의 참조입니다. 노드 하나일 때는 같은 노드를 가리키고, 빈 리스트면 둘 다 None입니다. 첫 노드의 prev와 마지막 노드의 next는 None입니다. owner는 노드가 속한 리스트를 확인해 잘못된 삭제를 막습니다.

### 2-2. 직접 만든 해시 함수

**관련 코드**

- `structures.hash_map.py`: [_index()](mini_redis/structures/hash_map.py#L12)

> 키를 UTF-8 바이트로 바꾸고, 이전 값에 31을 곱한 다음 바이트를 더합니다. 계산값을 64비트 범위로 제한한 뒤 버킷 수로 나눈 나머지를 저장 위치로 사용합니다. 같은 키는 같은 버킷에 연결리스트로 저장합니다.

31은 계산이 단순한 소수로 선택한 것입니다. 충돌을 완전히 없애는 숫자는 아닙니다.

### 2-3. 체이닝 충돌 해결

**관련 코드**: [HashMap._find()](mini_redis/structures/hash_map.py#L19), [put()](mini_redis/structures/hash_map.py#L29), [remove()](mini_redis/structures/hash_map.py#L59)

> 서로 다른 키가 같은 버킷에 배정되면 충돌입니다. 각 버킷에 직접 만든 이중 연결 리스트를 두고 `(key, value)` 튜플을 이어 저장합니다. 조회할 때는 버킷을 찾은 뒤 그 안에서 실제 키를 비교합니다.

기본 버킷 수 8에서 a와 i는 같은 버킷에 배정됩니다. 테스트의 Aa와 BB도 현재 해시 함수에서 충돌합니다.

| 경우 | 조회 비용 | 이유 |
| --- | --- | --- |
| 평균 | O(1) | 키가 고르게 나뉘어 체인이 짧음 |
| 최악 | O(n) | 모든 키가 한 버킷에 몰려 n개 비교 |

### 2-4. 로드 팩터와 버킷 2배 확장

**관련 코드**: [HashMap.put()](mini_redis/structures/hash_map.py#L29) 내부 확장 부분. 별도 `_resize()`는 없습니다.

> 로드 팩터는 키 개수를 버킷 개수로 나눈 값입니다. 0.75를 초과하면 버킷을 두 배로 늘립니다. 버킷 수가 바뀌면 나머지 계산 결과도 달라질 수 있어서 기존 모든 키를 다시 배치합니다(리해싱).

```text
버킷 8개, 키 6개 → 0.75  → 유지
버킷 8개, 키 7개 → 0.875 → 버킷 16개로 확장
```

분산이 양호하고 키 길이가 일정하다는 가정에서 한 번의 확장은 O(n)입니다. 현재 구현은 재삽입에 put을 사용해 중복 키 검사도 하므로, 충돌이 극단적으로 집중되면 확장 자체도 최악 O(n²)까지 커질 수 있습니다. 확장은 매 삽입마다 발생하지 않습니다.

## 항목 3: 자료구조 조합 설명

### 3-1. LRU에 해시맵과 연결 리스트가 모두 필요한 이유

**관련 코드**: [Entry.node](mini_redis/store.py#L9), [Store.get()](mini_redis/store.py#L71), [DoublyLinkedList.move_to_front()](mini_redis/structures/linked_list.py#L66)

> 해시맵은 키를 빨리 찾지만 사용 순서를 표현하기 어렵습니다. 연결 리스트는 순서 변경이 빠르지만 키 검색이 느립니다. 해시맵으로 Entry를 찾고 Entry.node로 해당 리스트 노드를 바로 이동하면 두 장점을 함께 사용할 수 있습니다.

```text
데이터 해시맵: key → Entry
                    ├─ value
                    ├─ node → LRU 리스트 노드
                    ├─ bytes
                    ├─ expire_at
                    └─ version
```

충돌 해결용 버킷 연결 리스트와 사용 순서를 관리하는 LRU 연결 리스트는 서로 다른 리스트입니다.

### 3-2. TTL에 최소 힙을 사용한 이유

**관련 코드**: [min_heap.py](mini_redis/structures/min_heap.py) 전체, [Store.purge_expired()](mini_redis/store.py#L39)

**관련 테스트**: [StructuresTest.test_heap](tests/test_mini_redis.py#L46)

> 가장 먼저 만료될 키를 빠르게 찾는 것이 목적입니다. 최소 힙은 가장 이른 만료 시각을 루트에 유지합니다. 루트가 아직 만료되지 않았다면 나머지도 만료되지 않았으므로 검사를 멈출 수 있습니다.

힙 기록 수를 h라고 하면 peek는 O(1), push와 pop은 O(log h)입니다. 배열 저장소의 확장 비용을 포함한 push의 O(log h)는 분할상환 관점입니다. 오래된 기록이 남으므로 h가 현재 키 개수와 같지는 않습니다.

push는 배열 끝에 추가한 뒤 부모와 비교하며 올리고, pop은 마지막 항목을 루트로 옮긴 뒤 더 작은 자식과 비교하며 내립니다. 부모 인덱스는 `(i-1)//2`, 자식은 `2*i+1`, `2*i+2`입니다. 현재 프로젝트에서 힙은 TTL에만 사용합니다.

### 3-3. 메모리 초과 eviction 전체 흐름

**관련 코드**: [Store.set()](mini_redis/store.py#L56), [_delete()](mini_redis/store.py#L29)

1. 만료된 키를 정리합니다.
2. 새 단일 항목의 UTF-8 크기가 제한을 넘으면 OOM으로 저장을 거절합니다.
3. 같은 키가 있으면 이전 데이터와 LRU 노드를 삭제하고 크기를 차감합니다.
4. 새 키의 LRU 노드를 맨 앞에 넣고 Entry를 해시맵에 저장합니다.
5. 새 크기를 사용량에 더합니다. 새 Entry는 만료 시간이 없어 기존 TTL도 초기화됩니다.
6. 제한을 넘는 동안 tail의 키부터 삭제하고 evicted_keys를 증가시킵니다.

삭제 시 Entry와 LRU 노드는 제거되지만 과거 힙 기록은 남아 있을 수 있습니다. 키가 없거나 번호가 달라 무효로 처리되므로 유효한 TTL은 유지되지 않습니다.

maxmemory 0은 무제한입니다. CONFIG로 제한을 낮추는 순간에는 삭제하지 않고 다음 성공한 SET에서 제한을 맞춥니다. 제한 초과를 한 번에 해결하려고 여러 키를 제거할 수도 있으므로 SET 전체가 항상 O(1)은 아닙니다.

### 3-4. GET 전체 흐름

**관련 코드**: [CLI.execute()](mini_redis/cli.py#L29), [Store.get()](mini_redis/store.py#L71)

> 만료된 키를 정리하고 해시맵에서 Entry를 찾습니다. 없으면 None을 반환하고 CLI가 nil로 출력합니다. 있으면 해당 LRU 노드를 맨 앞으로 옮기고 값을 반환합니다. CLI가 큰따옴표로 감싸 출력합니다. 조회 실패 시에는 LRU를 갱신하지 않습니다.

```text
만료 정리 → 해시맵 조회 → 없으면 nil
                     → 있으면 LRU 이동 → 값 출력
```

만료 정리를 제외한 조회와 LRU 이동은 평균 O(1)입니다. 여러 만료 기록을 처리하거나 힙을 재구성하는 경우 GET 전체는 더 오래 걸릴 수 있습니다.

## 항목 4: 확장 질문 답변

### 4-1. LRU 대신 LFU라면?

> LRU는 마지막 사용 시점, LFU는 사용 횟수를 기준으로 제거합니다. LFU를 구현하려면 키마다 사용 횟수를 저장하고 가장 적은 횟수를 찾는 구조가 필요합니다. 간단하게는 빈도와 사용 순서를 기준으로 최소 힙을 사용할 수 있지만 갱신 비용이 있습니다. 평균 O(1)을 목표로 한다면 같은 빈도끼리 연결 리스트로 묶고 해시맵과 최소 빈도 값을 함께 관리할 수 있습니다.

같은 빈도 안에서는 오래 사용하지 않은 키를 먼저 제거하도록 정할 수 있습니다. 현재 코드에서는 Entry 정보와 LRU 관리 부분을 바꿔야 하며 LFU는 아직 구현하지 않았습니다.

### 4-2. 데이터가 10만 건이면 어디가 병목인가?

| 병목 후보 | 이유 | 개선 방향 |
| --- | --- | --- |
| KEYS | 모든 버킷과 키 순회, 문자열 생성과 출력 | 일부씩 나눠 조회 |
| 해시맵 확장 | 한 번에 기존 항목 재배치 | 여러 명령에 나눠 재배치 |
| 해시 충돌 | 버킷 내부 체인이 길어짐 | 분산 검사와 해시 개선 |
| 긴 키 | 해시 계산과 비교 비용 증가 | 키 길이 영향 측정 |
| 대량 만료 | 한 명령에서 여러 힙 기록 처리 | 한 번에 정리할 양 제한 |
| 힙 재구성 | 키 순회와 반복 삽입 | 위치를 추적하는 힙 등 검토 |

> 10만 건이라는 숫자만으로 병목을 단정할 수는 없습니다. 어떤 명령을 얼마나 사용하는지에 따라 달라집니다. 현재 구조에서는 전체 순회와 한꺼번에 처리되는 작업을 먼저 측정하겠습니다.

### 4-3. 자료구조 오버헤드도 used_memory에 포함한다면?

> 현재는 키와 값만 세는 논리적인 용량 제한입니다. 실제 메모리를 계산하려면 Entry, 노드, 참조, 버킷 배열, 힙 배열과 오래된 기록, Python 객체 자체의 공간까지 포함해야 합니다. 그 크기는 Python 버전과 실행 환경에 따라 달라집니다. 비교 기준을 먼저 정해야 합니다.

공정하게 비교하려면 다음 중 하나를 선택합니다.

- 과제처럼 키와 값의 바이트 합으로 통일합니다.
- 노드와 참조마다 고정된 가상 비용을 정합니다.
- 같은 Python 버전과 환경에서 객체를 중복 계산하지 않는 측정 규칙으로 실제 크기를 비교합니다.

공식을 바꾸면 기존 maxmemory 테스트의 기대값도 바꿔야 합니다. 현재 제한은 프로세스 전체 실제 메모리를 제한하는 기능이 아닙니다.

## 보충: CLI 설명

[main.py](main.py)는 [mini_redis.cli.main()](mini_redis/cli.py#L102)을 호출합니다. CLI 객체는 한 번 만들고 다음 순서를 반복합니다.

```text
input으로 한 줄 읽기
→ shlex.split으로 따옴표를 고려해 분리
→ 명령어 대문자 변환
→ command_specs로 명령어와 단어 개수 검사
→ 저장소 메서드 실행
→ 결과 문자열 출력
```

`('SET', 3)`은 명령 이름까지 포함해 `SET key value`가 세 단어라는 뜻입니다. `for ... else`의 else는 break 없이 목록 끝까지 갔을 때 실행되어 unknown command를 반환합니다.

execute의 반환값은 None이면 종료, 빈 문자열이면 출력 없이 다음 입력, 나머지 문자열이면 결과 출력입니다. 정수 입력은 `parse_integer()`로 검사하고 문자열 출력은 `json.dumps(..., ensure_ascii=False)`로 처리합니다.
