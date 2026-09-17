# Troubleshooting

## SSH 접속 실패

### 증상

EC2 인스턴스에 SSH로 접속하려 했으나 연결되지 않았다.

PowerShell에서 다음 명령을 실행했을 때 연결 시간 초과가 발생했다.

```text
PS C:\Users\82103\downloads> ssh -i "codyssey-key.pem" ec2-user@43.203.210.58
ssh: connect to host 43.203.210.58 port 22: Connection timed out
```

### 가설

EC2 인스턴스의 실행 상태나 SSH 설정 또는 Security Group의 인바운드 규칙에 문제가 있을 것으로 판단했다.

### 검증

EC2의 상태 검사가 2/2 통과한 것을 확인하여 인스턴스 자체의 부팅 문제는 아닌 것으로 판단했다.

이후 Security Group의 SSH 인바운드 규칙을 확인한 결과 현재 접속 환경의 IP 주소와 다른 IP가 SSH 허용 대상으로 설정되어 있는 것을 확인했다.

### 조치

SSH 인바운드 규칙의 소스 IP를 현재 접속 환경의 공인 IP인 `121.135.181.35/32`로 수정했다.

### 결과

SSH 클라이언트에서 EC2에 다시 접속한 결과 정상적으로 접속되었다.

### 예방

SSH 접속 문제가 발생하면 먼저 EC2 상태 검사와 Security Group의 22번 포트 및 허용 IP를 확인하도록 한다.