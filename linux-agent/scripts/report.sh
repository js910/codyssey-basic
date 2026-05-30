#!/bin/bash

LOG_FILE="/var/log/agent-app/monitor.log"

START="$1"
END="$2"

if [ ! -f "$LOG_FILE" ]; then
    echo "log file not found"
    exit 1
fi

# 로그 필터 (시간 범위 옵션)
if [ -n "$START" ] && [ -n "$END" ]; then
    LOGS=$(awk -v s="$START" -v e="$END" '
    $0 >= s && $0 <= e
    ' "$LOG_FILE")
else
    LOGS=$(cat "$LOG_FILE")
fi

# CPU / MEM / DISK 추출
CPU_LIST=$(echo "$LOGS" | grep -o 'CPU:[0-9.]*' | cut -d: -f2)
MEM_LIST=$(echo "$LOGS" | grep -o 'MEM:[0-9.]*' | cut -d: -f2)
DISK_LIST=$(echo "$LOGS" | grep -o 'DISK_UD:[0-9.]*' | cut -d: -f2)

calc() {
    awk '
    {
        sum=0
        min=999999
        max=0
        count=0

        for(i=1;i<=NF;i++){
            sum += $i
            if($i < min) min = $i
            if($i > max) max = $i
            count++
        }

        if(count==0){
            print "no data"
            exit
        }

        printf "avg=%.2f max=%.2f min=%.2f count=%d\n",
               sum/count, max, min, count
    }'
}

echo "===== CPU ====="
echo "$CPU_LIST" | tr '\n' ' ' | calc

echo "===== MEM ====="
echo "$MEM_LIST" | tr '\n' ' ' | calc

echo "===== DISK ====="
echo "$DISK_LIST" | tr '\n' ' ' | calc