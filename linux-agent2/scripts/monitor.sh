#!/bin/bash

LOG_FILE="/var/log/agent-app/monitor.log"

mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

FOUND=0

while true
do
    APP_PID=$(pgrep -f "agent-leak-app" | while read p
    do
        ps -p "$p" -o pid=,rss=
    done | sort -k2 -nr | head -1 | awk '{print $1}')

    if [ -z "$APP_PID" ]; then
        if [ "$FOUND" -eq 1 ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] PROCESS:agent-leak-app TERMINATED" >> "$LOG_FILE"
            break
        fi

        sleep 3
        continue
    fi

    FOUND=1

    CPU_USED=$(ps -p "$APP_PID" -o %cpu= | awk '{print $1}')
    MEM_USED=$(ps -p "$APP_PID" -o rss= | awk '{printf "%.2f", $1/1024}')

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] PROCESS:agent-leak-app PID:$APP_PID CPU:${CPU_USED}% MEM:${MEM_USED}MB" >> "$LOG_FILE"

    sleep 3
done