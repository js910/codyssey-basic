# 시스템 관제 자동화 스크립트 개발

<p>
   <img src="https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white">
   <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
   <img src="https://img.shields.io/badge/Bash-4EAA25?style=for-the-badge&logo=gnu-bash&logoColor=white">
   <img src="https://img.shields.io/badge/OpenSSH-002446?style=for-the-badge&logo=openssh&logoColor=white">
   <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white">
</p>

다중 사용자 환경에서의 네트워크 보안 설정, 파일 시스템 권한 분리, 시스템 관제 쉘 스크립트(`monitor.sh`) 자동화를 다루는 인프라 엔지니어링 프로젝트입니다.

<br>

## 1. 과제 목표

- **SSH 보안 강화**: 기본 포트 변경(22→20022) 및 Root 원격 접속 제한(`PermitRootLogin no`)을 통해 자동화된 무차별 대입 공격(Brute Force) 위험성 완화
- **방화벽(UFW) 최소 허용 정책**: 인바운드 기본 정책을 `Deny`로 설정, 필수 포트(`20022/tcp`, `15034/tcp`)만 허용하여 외부 노출 최소화
- **역할 기반 권한 분리(RBAC)**: 공용 협업 공간(`upload_files`)과 보안 격리 공간(`api_keys`, 로그 디렉토리)을 계정 그룹(`agent-common`, `agent-core`)별로 분리하여 내부 권한 오용을 방지
- **인프라 관제 및 자원 순환**: 프로세스/포트 상태 점검 및 자원(CPU/MEM/DISK) 임계치 관리, 로그 누적으로 인한 디스크 사용량 문제를 방지하기 위해 10MB/10개 파일 순환 저장(Log Rotation)

<br>

## 2. 실행 가이드 (Quick Start)

Step 1. 저장소 클론 및 루트 진입
```bash
git clone https://github.com/js910/codyssey-basic
cd codyssey-basic/linux-agent
```

Step 2. 권한 부여 및 환경 구축 (sudo 권한 필요)
```bash
chmod +x scripts/setup_env.sh
sudo ./scripts/setup_env.sh
```

Step 3. 애플리케이션 실행 및 로그 모니터링
```bash
su - agent-admin
python3 /home/agent-admin/agent-app/agent_app.py &
tail -f /var/log/agent-app/monitor.log
```

<br>

## 3. 개발 환경 및 프로젝트 구조

### 개발 환경
- **OS**: Ubuntu 22.04 LTS
- **Script/Lang**: Bash (Shell Script), Python3 (테스트 앱 구동용)
- **Security**: UFW (Uncomplicated Firewall), OpenSSH Server

### Repository 구조
```text
.
├── scripts
|	├── setup_env.sh           # 환경 구축 자동화 스크립트
|	├── monitor.sh             # 시스템 자원 관제 및 로그 수집 스크립트
|	└── agent_app.py           # 모니터링 애플리케이션
└── README.md              # 본 문서
```

<br>

## 4. 요구사항 수행 내역서 (Verification Checklist)

### ✅ 필수 항목 점검표
| 항목 | 점검 방법 |
|---|---|
| SSH 포트 변경 및 Root 접속 차단 | `sudo grep -E "^Port\|^PermitRootLogin" /etc/ssh/sshd_config` |
| SSH 포트 LISTEN 확인 | `ss -tulnp \| grep 20022` |
| UFW 활성화 및 허용 포트 확인 | `sudo ufw status numbered` |
| 계정 생성 확인 | `id agent-admin && id agent-dev && id agent-test` |
| 그룹 매핑 확인 | `groups agent-admin` |
| 디렉토리 권한 확인 | `sudo ls -ld /home/agent-admin/agent-app` |
| monitor.sh 권한 확인 | `sudo ls -l /home/agent-admin/agent-app/bin/monitor.sh` |
| 환경 변수 확인 | `cat /etc/profile.d/agent_env.sh` |
| API Key 생성 확인 | `sudo cat /home/agent-admin/agent-app/api_keys/t_secret.key` |
| 앱 실행 확인 | `ps -ef \| grep agent_app.py` |
| APP 포트 LISTEN 확인 | `ss -tulnp \| grep 15034` |
| monitor.log 기록 확인 | `sudo tail -f /var/log/agent-app/monitor.log` |
| cron 등록 확인 | `sudo crontab -l -u agent-admin` |
| cron 자동 실행 확인 | `sudo grep -i "cron" /var/log/syslog \| grep "monitor.sh" \| tail -n 10 \| awk '{print $1}'` |
| 로그 로테이션 확인 | `sudo ls -lh /var/log/agent-app/` |

### 📋 권한 및 디렉토리 격리 상세
| 경로 / 대상 | 소유자 : 그룹 | 권한(Numeric) | 접근 범위 및 보호 목적 |
| :--- | :--- | :---: | :--- |
| `upload_files/` | agent-admin : agent-common | `770` | 전체 계정(admin, dev, test) R/W 공용 업로드 폴더 |
| `api_keys/` | agent-admin : agent-core | `770` | 핵심 관리 권한자(admin, dev) 전용 격리 폴더 |
| `t_secret.key` | agent-admin : agent-core | `660` | 외부 유출을 제한하는 API Key 보안 토큰 파일 |
| `bin/monitor.sh` | agent-dev : agent-core | `750` | 개발자 작성 및 수정, 관리자(`agent-admin`)가 cron으로 실행 |
| `/var/log/agent-app/` | agent-admin : agent-core | `770` | 시스템 관제 로그 저장소 격리 보호 |


<br>

## 5. 인프라 구축 및 관제 데이터 결과 (터미널 로그)

### ① 인프라 구축 및 검증 (`./setup_env.sh` 실행 결과)
```bash
=== [AGENT INFRA SYSTEM CHECK] ===

1. SSH & Service Status:
Port 20022
PermitRootLogin no
- Service active: active

2. Firewall Rules:
Status: active
     To                   Action      From
     --                   ------      ----
[ 1] 20022/tcp            ALLOW IN    Anywhere
[ 2] 15034/tcp            ALLOW IN    Anywhere

3. Accounts & Groups:
uid=1001(agent-admin) gid=1003(agent-admin) groups=1003(agent-admin),1001(agent-common),1002(agent-core)
uid=1002(agent-dev) gid=1004(agent-dev) groups=1004(agent-dev),1001(agent-common),1002(agent-core)
uid=1003(agent-test) gid=1005(agent-test) groups=1005(agent-test),1001(agent-common)

4. Permissions & Ownership:
drwxr-xr-x agent-admin agent-core /home/agent-admin/agent-app
-rwxr-xr-x agent-admin agent-core /home/agent-admin/agent-app/agent_app.py
drwxrwx--- agent-admin agent-core /home/agent-admin/agent-app/api_keys
drwxrwx--- agent-dev   agent-core /home/agent-admin/agent-app/bin
drwxrwx--- agent-admin agent-common /home/agent-admin/agent-app/upload_files
drwxrwx--- agent-admin agent-core /var/log/agent-app

5. API Key Check:
-rw-rw---- agent-admin agent-core /home/agent-admin/agent-app/api_keys/t_secret.key
- Key value: agent_api_key_test

6. Environment Variables:
export AGENT_HOME="/home/agent-admin/agent-app"
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR="$AGENT_HOME/upload_files"
export AGENT_KEY_PATH="$AGENT_HOME/api_keys/t_secret.key"
export AGENT_LOG_DIR="/var/log/agent-app"
==================================
```

### ② 애플리케이션 실행
```bash
agent-admin@DESKTOP-PMFBEQE:~$ python3 /home/agent-admin/agent-app/agent_app.py &
[1] 4561
[Step 1/5] Initializing System Components ... [OK]
[Step 2/5] Loading Environment Configurations ... [OK]
[Step 3/5] Verifying API Secret Keys ... [OK]
[Step 4/5] Establishing Firewall Rules Verification ... [OK]
[Step 5/5] Opening Application Network Socket ... [OK]

Agent READY
```

### ③ 실시간 관제 및 누적 로그 (`monitor.log`)
* crontab 스케줄러에 의해 매분 리소스가 자동 수집된 결과 데이터
```bash
[2026-05-21 17:38:02] PID:4561 CPU:0.2% MEM:11.19% DISK_UD:1% [WARNING] High MEM usage!
[2026-05-21 17:39:02] PID:4561 CPU:0.2% MEM:11.15% DISK_UD:1% [WARNING] High MEM usage!
[2026-05-21 17:40:02] PID:4561 CPU:0.2% MEM:11.32% DISK_UD:1% [WARNING] High MEM usage!
```