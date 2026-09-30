# AI Committer

Git 변경 사항을 분석하여 커밋 메시지와 Pull Request 초안을 생성하는 CLI 도구입니다.

## 📌 프로젝트 소개

Python과 Gemini API를 활용하여 Git의 변경 사항을 분석하고, 변경 내용에 맞는 커밋 메시지와 Pull Request 초안을 생성합니다.

`git status`와 `git diff`를 통해 현재 변경 사항을 수집하고, 수집한 내용을 프롬프트와 함께 Gemini API에 전달하여 결과를 생성합니다.

## 🛠 기술 스택

- Python 3.10+
- Google Gemini API
- google-genai
- Git / GitHub

## 📁 프로젝트 구조

```text
ai-committer/
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

## 주요 기능
### 1. Git 변경 사항 수집
Git 저장소에서 `git status`와 `git diff`를 실행하여 현재 변경된 파일과 변경 내용을 수집합니다.

변경 사항이 없는 경우 AI API를 호출하지 않고 프로그램을 종료합니다.

### 2. Commit Message 생성
```bash
python main.py commit
```

Git 변경 내용을 Gemini API에 전달하여 커밋 메시지를 생성합니다.

생성된 결과에는 커밋 제목과 주요 변경 사항이 포함되며, 사용자가 확인한 후 실제 Git 커밋에 사용할 수 있습니다.

예시:
```text
docs: 데이터 파일 형식 문서 수정 및 샘플 데이터 업데이트

- README.md의 데이터 파일 포맷 수정
- 예산 및 거래 내역 샘플 데이터 수정
```

### 3. Pull Request 생성
```bash
python main.py pr
```
Git 변경 내용을 기반으로 Pull Request 제목과 본문을 생성합니다.

PR 본문은 다음 형식을 사용합니다.
```text
## Why
- 변경 배경

## What
- 핵심 변경 사항

## How to Test
- 테스트 방법
```

### 4. PR 형식 검증
AI가 생성한 PR 결과를 Python 코드에서 다시 검사합니다.

다음 항목을 확인합니다.
- PR 제목 존재 여부
- PR 제목 80자 이하 여부
- Why 섹션 존재 여부
- What 섹션 존재 여부
- How to Test 섹션 존재 여부
- 각 섹션에 최소 1개의 bullet 존재 여부

검증은 별도의 AI API 요청 없이 프로그램 내부에서 처리합니다.

### 5. API 옵션
AI API 호출에 사용하는 주요 옵션을 CLI에서 변경할 수 있습니다.

```bash
python main.py commit --model gemini-3.5-flash-lite

python main.py commit --temperature 0.3

python main.py commit --max-tokens 500
```

여러 옵션을 함께 사용할 수도 있습니다.
```bash
python main.py commit \
  --model gemini-3.5-flash-lite \
  --temperature 0.3 \
  --max-tokens 500
```

### 6. Safe Mode
Git diff에 포함될 수 있는 민감정보를 마스킹한 후 AI API로 전송할 수 있습니다.
```bash
python main.py commit --safe-mode
```

현재 다음 패턴을 마스킹합니다.
- API Key
- Bearer Token
- 이메일 주소

예:
```text
API_KEY="abc123456"
email=test@example.com
Authorization: Bearer abcdef123456
```

Safe Mode 적용 후:
```text
API_KEY="[REDACTED]"
email=[REDACTED_EMAIL]
Authorization: Bearer [REDACTED]
```
Safe Mode는 모든 민감정보를 완벽하게 탐지하는 기능은 아니므로 AI API 요청 전에 Git diff를 확인하는 것을 권장합니다.

## 🔑 API Key 설정
Gemini API Key는 환경변수로 관리합니다.

```bash
export GEMINI_API_KEY="YOUR_API_KEY"
```

## 🚀 실행
프로젝트 디렉토리에서 가상환경을 활성화한 후 실행합니다.
```bash
# 가상환경 활성화
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 커밋 메시지 생성
python main.py commit

# Pull Request 생성
python main.py pr

# Safe Mode 사용
python main.py commit --safe-mode
```

## 🔄 실행 흐름
```text
git status
    ↓
git diff
    ↓
변경 사항 확인
    ↓
Safe Mode 적용
    ↓
Gemini API 요청
    ↓
Commit / PR 생성
    ↓
PR 형식 검증
    ↓
터미널 출력
```

Commit과 PR 생성은 각각 1회의 AI API 요청으로 처리하며, PR 형식 검증은 Python 코드에서 수행합니다.

## ⚠️ 주의사항
Git diff에는 API Key, Token, 이메일 등의 민감정보가 포함될 수 있습니다.

AI API로 변경 내용을 전송하기 전에 민감정보가 포함되어 있는지 확인하고, 필요한 경우 --safe-mode 옵션을 사용합니다.

또한 생성된 커밋 메시지와 PR 내용은 AI가 생성한 초안이므로 실제 Commit 또는 PR에 적용하기 전에 변경 내용을 직접 확인해야 합니다.
