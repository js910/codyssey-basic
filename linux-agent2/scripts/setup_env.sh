#!/bin/bash
set -e
ENV_PROFILE="/etc/profile.d/agent_env.sh"

# 글로벌 환경 변수 등록
cat << 'EOF' > $ENV_PROFILE
export AGENT_HOME="/home/agent-admin/agent-app"
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR="$AGENT_HOME/upload_files"
export AGENT_KEY_PATH="$AGENT_HOME/api_keys"
export AGENT_LOG_DIR="/var/log/agent-app"

# 트러블슈팅용 제어 변수
export MEMORY_LIMIT=50
export CPU_MAX_OCCUPY=20
export MULTI_THREAD_ENABLE=true
EOF
source "$ENV_PROFILE"

# 1. SSH 및 방화벽
groupadd -f agent-core
id -u agent-admin &>/dev/null || (useradd -m -s /bin/bash agent-admin && echo "agent-admin:agent-admin" | chpasswd)
usermod -aG agent-core agent-admin

# 2. 디렉토리 구조 생성
mkdir -p "$AGENT_HOME/upload_files" "$AGENT_HOME/api_keys" "$AGENT_LOG_DIR"
echo "agent_api_key_test" > "$AGENT_HOME/api_keys/secret.key"
unzip -o agent-app-leak.zip -d "$AGENT_HOME"
chmod +x "$AGENT_HOME"/agent-leak-app-*
chown agent-admin:agent-core "$AGENT_HOME"/agent-leak-app-*
cp /home/user/monitor.sh "$AGENT_HOME"
chown agent-admin:agent-core "$AGENT_HOME"/monitor.sh
chmod +x "$AGENT_HOME"/monitor.sh

# 3. 권한 세팅
chown -R agent-admin:agent-core "$AGENT_HOME" "$AGENT_LOG_DIR"
chmod 770 "$AGENT_HOME/upload_files" "$AGENT_HOME/api_keys" "$AGENT_LOG_DIR"
chmod 660 "$AGENT_HOME/api_keys/secret.key"

echo "=== 인프라 세팅 완료 ==="