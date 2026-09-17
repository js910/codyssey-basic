# Cleanup Checklist

## AWS 리소스 정리

- [x] EC2 인스턴스 종료 확인: i-091bfb580e9bc5632 (codyssey-ec2) 종료됨
- [x] EBS 볼륨 삭제 확인: Volumes 목록 0개
- [x] Elastic IP Release 확인: Elastic IP 목록 0개
- [x] Internet Gateway Detach/Delete 확인: igw-0def856dde87db8b4 분리 및 삭제됨
- [x] Route Table 삭제 확인: rtb-07b36ff35fbe4efa2 삭제됨
- [x] Subnet 삭제 확인: subnet-0ec93b56368749a79 삭제됨
- [x] VPC 삭제 확인: vpc-0fc3f6cd3495bc113 삭제됨
- [x] Security Group 삭제 확인: VPC 삭제와 함께 제거됨

## 추가 리소스 확인

- [ ] NAT Gateway 삭제 확인 (생성한 경우): 미생성
- [ ] ELB/ALB 삭제 확인 (생성한 경우): 미생성
- [ ] RDS 삭제 확인 (생성한 경우): 미생성

## 최종 확인

- [ ] AWS 리소스 목록에서 실습 리소스가 남아있지 않은지 확인
- [ ] Billing Dashboard에서 과금 항목 확인