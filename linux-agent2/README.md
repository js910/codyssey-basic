# Agent System Failure Analysis Report

본 프로젝트는 Linux 환경에서 실행되는 `agent-leak-app`을 대상으로  
Memory Leak, CPU Watchdog, Deadlock 장애를 분석하고  
관제 로그 기반으로 원인을 추론한 트러블슈팅 리포트입니다.

---

# 분석 대상 장애

- Memory Leak → OOM / MemoryGuard 종료
- CPU Spike → Watchdog 미발동 상태 분석
- Deadlock → 멀티스레드 교착 상태

---

# 실행 환경

- Linux (WSL / Ubuntu)

---

# 산출물

각 장애는 GitHub Issue 형식으로 작성됨:

- Issue #1 Memory Leak (OOM)
- Issue #2 CPU Watchdog
- Issue #3 Deadlock