#!/bin/bash
set -e
sed -i 's/\r$//' "$0" 2>/dev/null || true # 줄바꿈 기호 제거

# 환경 변수
ENV_PROFILE="/etc/profile.d/agent_env.sh"
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# 글로벌 환경 변수 등록
cat << 'EOF' > $ENV_PROFILE
export AGENT_HOME="/home/agent-admin/agent-app"
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR="$AGENT_HOME/upload_files"
export AGENT_KEY_PATH="$AGENT_HOME/api_keys/t_secret.key"
export AGENT_LOG_DIR="/var/log/agent-app"
EOF
chmod +x $ENV_PROFILE
. $ENV_PROFILE

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
    systemctl daemon-reload
    systemctl restart ssh.socket ssh
else
    # ssh.socket이 없는 환경 (22.04)
    systemctl restart ssh
fi

# 2. 방화벽 설정
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 20022/tcp
ufw allow 15034/tcp
ufw --force enable

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

# 4. 디렉토리 구조 생성 및 파일 배치
mkdir -p $AGENT_HOME/{upload_files,api_keys,bin} $AGENT_LOG_DIR
echo "agent_api_key_test" > "$AGENT_KEY_PATH"
cp /dev/null $AGENT_LOG_DIR/monitor.log
cp /dev/null $AGENT_LOG_DIR/report_cron.log
cp /dev/null $AGENT_LOG_DIR/policy_cron.log

cp "scripts/agent_app.py" "$AGENT_HOME/agent_app.py"
cp "scripts/monitor.sh" "$AGENT_HOME/bin/monitor.sh"
cp "scripts/report.sh" "$AGENT_HOME/bin/report.sh"
cp "scripts/log_policy.sh" "$AGENT_HOME/bin/log_policy.sh" 
sed -i 's/\r$//' "$AGENT_HOME/agent_app.py"
for f in monitor.sh report.sh log_policy.sh; do
    sed -i 's/\r$//' "$AGENT_HOME/bin/$f"
done

# 5. 권한 세팅
chown -R agent-admin:agent-core $AGENT_HOME $AGENT_LOG_DIR
chown agent-admin:agent-common $AGENT_UPLOAD_DIR
chmod 770 $AGENT_UPLOAD_DIR
chmod 770 $AGENT_HOME/api_keys
chmod 770 $AGENT_LOG_DIR
chmod 660 "$AGENT_KEY_PATH"
chown agent-dev:agent-core $AGENT_HOME/bin/monitor.sh
chmod 750 $AGENT_HOME/bin/monitor.sh

chown agent-dev:agent-core $AGENT_HOME/bin
chmod 770 $AGENT_HOME/bin
chown agent-admin:agent-core $AGENT_LOG_DIR/monitor.log
chmod 660 $AGENT_LOG_DIR/monitor.log
chmod +x $AGENT_HOME/bin/report.sh
chmod +x $AGENT_HOME/bin/log_policy.sh

# agent-admin 계정 크론탭 등록
cat << EOF | crontab -u agent-admin -
* * * * * /bin/bash /home/agent-admin/agent-app/bin/monitor.sh >> /tmp/monitor_cron.log 2>&1
*/10 * * * * /bin/bash /home/agent-admin/agent-app/bin/report.sh >> /var/log/agent-app/report_cron.log 2>&1
0 3 * * * /bin/bash /home/agent-admin/agent-app/bin/log_policy.sh >> /var/log/agent-app/policy_cron.log 2>&1
EOF
systemctl restart cron 2>/dev/null || service cron restart 2>/dev/null || true

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
ls -ld $AGENT_HOME $AGENT_HOME/* $AGENT_LOG_DIR | awk '{print $1, $3, $4, $9}'
echo -e "\n5. API Key Check:"
ls -l "$AGENT_KEY_PATH" | awk '{print $1, $3, $4, $9}'
echo "- Key value:" $(cat "$AGENT_KEY_PATH")
echo -e "\n6. Environment Variables:"
cat $ENV_PROFILE | grep "export"
echo -e "\n=================================="