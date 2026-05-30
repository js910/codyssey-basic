#!/bin/bash

LOG_DIR="/var/log/agent-app"
ARCHIVE_DIR="/var/log/agent-app/archive"

# 1. 로그 디렉토리 존재 확인
if [ ! -d "$LOG_DIR" ]; then
    echo "[WARN] log dir not found"
    exit 1
fi

# 2. 아카이브 디렉토리 생성
if [ ! -d "$ARCHIVE_DIR" ]; then
    echo "[WARN] archive dir missing (creating)"
    mkdir -p "$ARCHIVE_DIR"
fi

# 3. 7일 이상 로그 압축 후 이동
find "$LOG_DIR" -type f -name "*.log" -mtime +7 | while read -r file; do
    gzip -f "$file"
    mv "${file}.gz" "$ARCHIVE_DIR/"
    echo "[INFO] archived: $file"
done

# 4. 30일 이상 아카이브 삭제
find "$ARCHIVE_DIR" -type f -name "*.gz" -mtime +30 | while read -r file; do
    rm -f "$file"
    echo "[INFO] deleted: $file"
done