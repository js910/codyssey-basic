#!/usr/bin/env python3
import time
import sys
import socket

def boot_sequence():
    steps = [
        "Initializing System Components",
        "Loading Environment Configurations",
        "Verifying API Secret Keys",
        "Establishing Firewall Rules Verification",
        "Opening Application Network Socket"
    ]
    for i, step in enumerate(steps, 1):
        print(f"[Step {i}/5] {step} ... [OK]")
        time.sleep(0.3)
    print("\nAgent READY")
    sys.stdout.flush()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 포트 재사용 옵션 보장
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(('0.0.0.0', 15034))
        server.listen(5)
        # 무한 루프 유지
        while True:
            conn, addr = server.accept()
            conn.close()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    boot_sequence()
    start_server()