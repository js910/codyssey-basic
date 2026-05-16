#!/bin/bash
set -e

# 환경변수 로드 및 기본 설정
export AGENT_HOME="/home/agent-admin/agent-app"
export AGENT_PORT=15034
LOG_FILE="/var/log/agent-app/monitor.log"
MAX_SIZE=$((10 * 1024 * 1024)) # 10MB
MAX_FILES=10

# 1. Health Check (실패 시 즉시 로그 남기고 종료)
APP_PID=$(pgrep -f "agent_app.py" | head -n1)
if [ -z "$APP_PID" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] agent_app.py is not running." >> "$LOG_FILE"
    exit 1
fi

if ! ss -tln | grep -q ":$AGENT_PORT "; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] Port $AGENT_PORT is not listening." >> "$LOG_FILE"
    exit 1
fi

# 2. 방화벽 상태 점검
UFW_WARN=""
if ! systemctl is-active --quiet ufw; then
    UFW_WARN="[WARNING] Firewall is inactive!"
fi

# 3. 자원 수집
CPU_USED=$(top -bn2 -d 0.5 | grep -i "cpu(s)" | tail -n 1 | sed 's/,/\n/g' | grep 'id' | awk '{print 100 - $1}')
MEM_USED=$(free | grep Mem | awk '{printf "%.2f", $3/$2 * 100}')
DISK_USED=$(df / | tail -n 1 | awk '{print $5}' | tr -d '%')

# 4. 임계값 경고 판단 (CPU > 20%, MEM > 10%, DISK > 80%)
CPU_WARN=""
MEM_WARN=""
DISK_WARN=""

if (( $(echo "$CPU_USED > 20" | bc -l 2>/dev/null || awk "BEGIN {print ($CPU_USED > 20)?1:0}") )); then CPU_WARN="[WARNING] High CPU usage!"; fi
if (( $(echo "$MEM_USED > 10" | bc -l 2>/dev/null || awk "BEGIN {print ($MEM_USED > 10)?1:0}") )); then MEM_WARN="[WARNING] High MEM usage!"; fi
[ "$DISK_USED" -gt 80 ] && DISK_WARN="[WARNING] High DISK usage!"

# 5. 로그 생성 및 기록
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_LINE="[$TIMESTAMP] PID:$APP_PID CPU:${CPU_USED}% MEM:${MEM_USED}% DISK_UD:${DISK_USED}%"

# 경고 연산자 교정 (-not -z 지우고 안전한 -n 문법으로 선언)
for warn in "$UFW_WARN" "$CPU_WARN" "$MEM_WARN" "$DISK_WARN"; do
    if [ -n "$warn" ]; then
        LOG_LINE="$LOG_LINE $warn"
    fi
done
echo "$LOG_LINE" >> "$LOG_FILE"

# 6. 로그 파일 용량 순환 관리
if [ -f "$LOG_FILE" ]; then
    FILE_SIZE=$(stat -c%s "$LOG_FILE")
    if [ "$FILE_SIZE" -gt "$MAX_SIZE" ]; then
        [ -f "${LOG_FILE}.${MAX_FILES}" ] && rm -f "${LOG_FILE}.${MAX_FILES}"
        for i in $(seq $((MAX_FILES - 1)) -1 1); do
            [ -f "${LOG_FILE}.$i" ] && mv "${LOG_FILE}.$i" "${LOG_FILE}.$((i + 1))"
        done
        mv "$LOG_FILE" "${LOG_FILE}.1"
        touch "$LOG_FILE"
        chmod 770 "$LOG_FILE"
    fi
fi