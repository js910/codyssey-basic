# 용돈 기입장 프로그램 (Console Budget App)

Python 콘솔 환경에서 동작하는 파일 입출력 기반의 가계부 프로그램입니다.
제너레이터 스트리밍, 데코레이터 기반 공통 관심사 분리, 타입 힌트와 모듈화된 아키텍처를 적용하여 유지보수성을 높였습니다.

---

## 📂 프로젝트 구조 및 모듈 책임

프로젝트는 7개의 모듈로 구조화되어 있습니다.

- **`__init__.py`**: 패키지 초기화
- **`__main__.py`**: 프로그램 진입점
- **`cli.py`**: 사용자 입력(대화형 및 명령어 옵션 파싱) 및 결과 출력 담당
- **`app.py`**: 가계부 핵심 비즈니스 로직 (요약, 예산 대비 사용률 계산, 카테고리 무결성 검증 등)
- **`repository.py`**: 파일 I/O 담당 (JSONL/CSV 영구 저장, `yield` 기반 제너레이터 스트리밍, 임시 파일 교체를 통한 원자적 저장)
- **`models.py`**: 데이터 구조 정의 (`@dataclass` 기반 `Transaction`, `Budget` 등)
- **`validators.py`**: 날짜, 금액, 타입, 카테고리 형식 유효성 검증 로직

---

## 🚀 실행 방법

프로젝트 루트 디렉토리에서 아래 명령어로 실행할 수 있습니다.

```bash
# 기본 도움말 확인
python -m budget_app --help

# 특정 명령어 도움말 확인 (예: add)
python -m budget_app add --help
```

---

## 💡 주요 명령어 및 사용 예시

### 1. 거래 추가 (`add`)
대화형으로 날짜, 타입, 카테고리, 금액, 메모, 태그를 입력받아 저장합니다.
```bash
python -m budget_app add
```

*입력 예시:*
```text
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal
[저장 완료] id=TX-000012
```

### 2. 거래 목록 조회 (`list`)
최신순으로 거래 내역을 스트리밍 방식으로 출력합니다.
```bash
python -m budget_app list --limit 3
```

### 3. 카테고리 관리 (`category`)
카테고리 추가, 목록 조회, 삭제를 관리합니다.
```bash
# 카테고리 추가
python -m budget_app category add

# 카테고리 목록 조회
python -m budget_app category list
```

### 4. 예산 설정 (`budget set`)
특정 월의 예산을 설정합니다.
```bash
python -m budget_app budget set --month 2024-01 --amount 500000
```

### 5. 월별 요약 및 예산 확인 (`summary`)
해당 월의 총수입, 총지출, 잔액 및 지출 상위 카테고리(TOP N)를 조회합니다. 예산이 설정된 경우 사용률과 초과 경고를 함께 출력합니다.
```bash
python -m budget_app summary --month 2024-01 --top 3
```

### 6. 조건별 검색 (`search`)
기간, 카테고리, 타입, 키워드, 태그 조건으로 거래를 검색합니다.
```bash
python -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food
```

### 7. 내보내기 / 가져오기 (`export` / `import`)
```bash
# CSV로 내보내기
python -m budget_app export --out export.csv --month 2024-01

# CSV 파일 가져오기
python -m budget_app import --from import.csv
```

---

## 🗄️ 저장 파일 위치 및 형식

데이터는 기본적으로 `./data` 폴더 아래에 3개 이상의 파일로 영구 분리되어 저장됩니다.

1. **`data/transactions.jsonl`**: 거래 내역 (JSONL 포맷, 줄 단위 스트리밍 읽기 지원)
2. **`data/categories.json`**: 카테고리 목록
3. **`data/budgets.json`**: 월별 예산 정보

---

## 📋 Import / Export CSV 스키마

가져오기(`import`) 및 내보내기(`export`) 시 사용하는 CSV 파일의 공통 규칙은 다음과 같습니다.
- **인코딩**: UTF-8
- **헤더 필수 포함**

| 컬럼명 (Column) | 필수 여부 (Required) | 설명 |
| :--- | :---: | :--- |
| `date` | **Y** | 거래 일자 (`YYYY-MM-DD`) |
| `type` | **Y** | 거래 타입 (`income` 또는 `expense`) |
| `category` | **Y** | 등록된 카테고리명 |
| `amount` | **Y** | 금액 (0보다 큰 양수 정수) |
| `memo` | N | 메모 (문자열) |
| `tags` | N | 태그 (쉼표 `,`로 구분된 문자열) |