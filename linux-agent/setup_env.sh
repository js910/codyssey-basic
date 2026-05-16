#!/bin/bash
set -e
sed -i 's/\r$//' "$0" # 줄바꿈 기호 제거

# 환경 변수
REPO_PATH=$(pwd)
APP_PATH="/home/agent-admin/agent-app"
LOG_PATH="/var/log/agent-app"
ENV_PROFILE="/etc/profile.d/agent_env.sh"

# 필수 패키지 설치
[ -f /etc/ssh/sshd_config ] || (apt-get update && apt-get install -y openssh-server)
command -v ufw &>/dev/null || (apt-get update && apt-get install -y ufw)

# 1. SSH 설정
sed -i 's/^#\?Port .*/Port 20022/' /etc/ssh/sshd_config
sed -i 's/^#\?PermitRootLogin .*/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl daemon-reload
if systemctl list-unit-files | grep -q "ssh.socket"; then
    mkdir -p /etc/systemd/system/ssh.socket.d
    echo -e "[Socket]\nListenStream=\nListenStream=20022" > /etc/systemd/system/ssh.socket.d/listen.conf
    systemctl restart ssh.socket ssh
else
    # ssh.socket이 없는 환경 (22.04)
    systemctl restart ssh
fi

# 2. 방화벽 설정
ufw allow 20022/tcp && ufw allow 15034/tcp
(echo "y" | ufw enable) 2>/dev/null || true

# 3. 그룹 및 계정 세팅
groupadd -f agent-common && groupadd -f agent-core
for user in agent-admin agent-dev agent-test; do
    if ! id -u $user &>/dev/null; then
        useradd -m -s /bin/bash $user
        echo "$user:$user" | chpasswd
    fi
done
usermod -aG agent-common,agent-core agent-admin
usermod -aG agent-common,agent-core agent-dev
usermod -aG agent-common agent-test

# 4. 디렉토리 생성 및 로그 초기화
mkdir -p $APP_PATH/{upload_files,api_keys,bin} $LOG_PATH
echo "agent_api_key_test" > "$APP_PATH/api_keys/t_secret.key"
cp /dev/null $LOG_PATH/monitor.log

# 깃허브 파일 복사
cp "$REPO_PATH/agent_app.py" "$APP_PATH/agent_app.py"
cp "$REPO_PATH/monitor.sh" "$APP_PATH/bin/monitor.sh"
sed -i 's/\r$//' "$APP_PATH/agent_app.py"
sed -i 's/\r$//' "$APP_PATH/bin/monitor.sh"

# 권한 정리
chown -R agent-admin:agent-core $APP_PATH $LOG_PATH
chown agent-admin:agent-common $APP_PATH/upload_files
chmod -R 770 $APP_PATH $LOG_PATH
chmod 660 "$APP_PATH/api_keys/t_secret.key"
chmod 755 $APP_PATH/bin/monitor.sh

# agent-admin 계정 크론탭 등록
(crontab -u agent-admin -l 2>/dev/null | grep -v "monitor.sh" ; echo "* * * * * $APP_PATH/bin/monitor.sh") | crontab -u agent-admin -
systemctl restart cron

# 5. 환경 변수 등록
cat << 'EOF' > $ENV_PROFILE
export AGENT_HOME="$APP_PATH"
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR="$AGENT_HOME/upload_files"
export AGENT_KEY_PATH="$AGENT_HOME/api_keys/t_secret.key"
export AGENT_LOG_DIR="$LOG_PATH"
EOF
chmod +x $ENV_PROFILE

# 6. 설정 검증 및 상태 출력
echo -e "\n=== [AGENT INFRA SYSTEM CHECK] ==="
echo -e "\n1. SSH & Service Status:"
grep -E "^Port|^PermitRootLogin" /etc/ssh/sshd_config
echo "- Service active:" $(systemctl is-active ssh.socket ssh 2>/dev/null | grep active | head -n1)
echo -e "\n2. Firewall Rules:"
ufw status numbered
echo -e "\n3. Accounts & Groups:"
for u in agent-admin agent-dev agent-test; do id $u; done
echo -e "\n4. Permissions & Ownership:"
ls -ld $APP_PATH $APP_PATH/* $LOG_PATH | awk '{print $1, $3, $4, $9}'
echo -e "\n5. API Key Check:"
ls -l "$KEY_FILE" | awk '{print $1, $3, $4, $9}'
echo "- Key value:" $(cat "$KEY_FILE")
echo -e "\n6. Environment Variables:"
cat $ENV_PROFILE | grep "export"
echo -e "\n=================================="