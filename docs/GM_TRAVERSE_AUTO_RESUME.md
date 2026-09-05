# Traverse 자동 재출발 수정 후보

대상: 2023 Traverse, C4, SDGM 하네스, SASCM, openpilot 종방향 제어.
기준 소스: `225fc5e7e4328b3c43c04dea01009c302662b30a`.

## 변경한 동작

1. 인게이지 상태에서 완전 정차를 0.5초 확인하고 기존 앞차 출발 조건을 0.2초 확인한다.
2. `starting` 상태와 가속 출력을 같은 제어 주기에서 전달한다. GM 마찰제동 0 명령을 먼저 생성한다.
3. 그 다음 주기에 순정 버튼 수신 시각과 counter를 저장하고, 이후 도착한 새 순정 프레임부터 RES를 보낸다. 현재 구현은 기존 bus 0/2 송신 경로를 유지한다.
4. 원본 counter가 연속이고 프레임이 신선한 동안 RES 4회와 UNPRESS 1회를 보낸다. RES 간격은 최소 25 ms이며, 약 30 ms인 원본 주기를 따른다. 누락 프레임을 짧은 간격으로 몰아 보내지 않는다.
5. 차량이 반환한 크루즈 상태가 정상 ACTIVE로 0.2초 유지되면 재출발 요청이 수용된 것으로 판정한다. Traverse의 raw PCM 상태 1이 ACTIVE, 4가 STANDSTILL이다. CAN 유효성 및 fault 상태도 확인한다.
6. 2초 내 수용되지 않거나 앞차/제어 조건이 사라지면 기존 감속·정차 제어로 돌아간다. 출발 도중 PCM이 다시 정차 상태로 돌아와도 실패 처리한다. 바퀴가 조금 굴러도 제한 시간을 초기화하지 않는다. 실패한 동일 정차에서 합성 RES를 반복하지 않는다.
7. 물리 RES는 운전자의 재시도로 처리한다. 물리 버튼 위에 합성 UNPRESS를 덮어쓰지 않으며, Panda는 물리 버튼을 수신하면 순정 전달 차단을 해제한다. 성공 후 실제 이동을 거쳐 다시 정차하면 최고 속도가 1.5 m/s 미만이어도 다음 자동 재출발을 준비한다.

사용자가 확인한 **브레이크 해제 후 RES가 동작하는 순서**를 반영했다. ECU ACK를 기다리며 유압 홀드를 계속 유지하는 방식이 아니다.

## 판정의 의미와 남은 확인

- 성공 판정에 사용하는 것은 `cruiseState.standstill` 해제와 정상 PCM ACTIVE 상태다. 바퀴 속도로 계산한 `CarState.standstill` 해제, 송신한 악셀 명령, Panda 송신 반환 echo만으로는 성공 판정하지 않는다.
- 직접적인 엔진 토크/악셀 명령 수용 피드백은 이번 변경에 추가하지 않았다. 따라서 ECU 정차 상태 해제와 실제 지속적인 재가속은 별도 관측 사항이다.
- 브레이크 0 CAN 명령을 먼저 생성했음을 보장한다. 실제 유압이 0이 된 시각이나 수신 ECU에서의 적용 순서까지 측정한 것은 아니다.
- 순정 bus 0에 이미 존재하는 버튼 프레임은 Python이나 `0 → 2` 전달 차단으로 제거할 수 없다. 새 프레임 대기는 기존 첫 두 RES의 10 ms 간격 문제를 해결하지만, 모든 물리 네트워크의 원자적인 버튼 치환을 보장하지 않는다.
- Panda에서 전달 처리가 RX보다 먼저 실행되므로 운전자 버튼의 첫 프레임은 이미 차단됐을 수 있다. 이후 프레임부터 순정 전달을 복구한다. CANCEL은 기존 즉시 릴레이 경로도 유지한다.
- 이 변경은 제동/가속 최대치, 기존 저속 RES 안전 허용 범위 또는 SASCM 펌웨어를 변경하지 않는다.

## 회귀 검증

실제 cereal 스키마, CAN parser/packer, GM 제어기, 호스트에서 컴파일한 C safety 코드를 사용한다. 테스트에서 차량 CAN을 송신하지 않는다.

2026-09-06 검증 결과: 종방향 및 통합 39개, GM 차량 90개, GM safety 538개 통과. 하위 subtest는 각각 0/26/688개 통과했다. GM safety의 공통 기반 및 해당 구성에 적용되지 않는 325개 항목은 skip됐다. 변경한 Python 파일의 Ruff 및 `git diff --check`도 통과했다. C4 전체 빌드와 실차 수용 여부는 이 결과에 포함되지 않는다.

```sh
PYTHONPATH=.:opendbc_repo python -m pytest -q -o addopts='' --confcutdir=selfdrive/controls/tests selfdrive/controls/tests/test_longcontrol.py selfdrive/controls/tests/test_gm_resume_integration.py
PYTHONPATH=.:opendbc_repo python -m pytest -q -o addopts='' --confcutdir=opendbc_repo/opendbc/car/gm/tests opendbc_repo/opendbc/car/gm/tests
PYTHONPATH=.:opendbc_repo python -m pytest -q -o addopts='' --confcutdir=opendbc_repo/opendbc/safety/tests opendbc_repo/opendbc/safety/tests/test_gm.py
```

`test_resume.py`의 fixture는 실제 실패 route 49/7에서 개인정보 없이 버튼 수신 시각과 counter만 추출했다. 기존 RES 요청 간격은 10.129/29.727/31.480 ms였다. 이 원본 수신 위상을 재생한 새 스케줄러 테스트에서는 30/30/30 ms로 나온다. 이는 오프라인 재현 결과이며 실제 ECU 수용 실험 결과가 아니다.

## 적용 상태

별도 `codex/gm-resume-fresh-frame` 브랜치에서 수정했다. C4 실행 소스와 Panda 펌웨어는 이 작업에서 교체하지 않았다. C4는 SSH로 기준 커밋과 오프로드 상태를 확인했다. 기존 기기 변경 파일은 보존했다.

배포 단위에는 Python 제어 코드와 `opendbc/safety/modes/gm.h` 변경이 함께 포함된다. 소스 복사만으로 Panda 펌웨어가 바뀌었다고 판단하면 안 된다. 실제 적용 후에는 동일 조건의 로그에서 브레이크 해제, RES 송신 간격, PCM 정차 해제, 운전자 페달 입력, 실패 복귀를 확인해야 한다.
