# Traverse 자동 재출발과 수동 시험 버튼

대상: 2023 Traverse Redline, C4, SDGM 하네스, SASCM, openpilot 종방향 제어.
이번 변경은 Wayon/Sunnypilot의 `ee3aa0582` 위에 적용하며, 최근 정차·출발 완화와 40 km/h 이상 가속 상한 변경을 유지한다.

## 2026-09-06 주행에서 버튼이 보이지 않은 원인

기기 원본 qlog 153개 세그먼트, 네 주행을 확인했다. 모두 `a8ef5cfc`, dirty=false이며 Traverse/autoResumeSng/openpilotLongitudinalControl 설정은 정상이다.

| 주행 시작 KST | route | 인게이지 완전 정차 표본 | shouldStop=true |
| --- | --- | ---: | ---: |
| 15:11 | 0000004a--57c0338383 | 75 | 75 |
| 18:10 | 0000004b--5518a0fd26 | 1224 | 1223 |
| 20:44 | 0000004c--48461386ca | 320 | 301 |
| 22:18 | 0000004d--04163084da | 0 | 0 |

기존 UI는 실행 허용 조건을 표시 조건으로 사용했다. 정차 중 `longitudinalPlan.shouldStop=true`이면 버튼을 숨겨 1619개 중 1599개 표본(98.8%)에서 표시가 차단됐다. 이들은 정차 횟수가 아니라 qlog 표본 수다.

나머지 조건까지 통과한 qlog 표본은 route 4c의 5개뿐이었다. 해당 구간의 원본 rlog(21/22번 세그먼트)에서는 표시 조건이 열린 구간이 약 0.19초, 0.64초로 확인됐다. UI 메시지 수신 주파수 검사 내부 상태와 실제 화면 픽셀은 로그만으로 복원하지 못하므로, 그 순간 실제로 표시됐다고 단정하지 않는다. uiDebug는 약 59~60 Hz였으며 UI 미실행을 원인으로 볼 근거는 없다.

## 화면 동작

- Traverse 종방향 제어가 설정된 주행 화면에서 D/L 완전 정차 시 중앙에 **오토리슘**을 표시한다. PCM 정차 여부, 인게이지, 정차 계획은 버튼을 숨기는 조건으로 사용하지 않는다.
- 실행할 수 없으면 회색 버튼과 `전방 공간 확인 필요`, `크루즈 활성 필요`, `페달 해제 후 시험` 등 원인을 표시한다.
- 실행 가능하면 파란 버튼과 `앞차 없이 수동 시험`을 표시한다. 손을 뗄 때 한 번 요청한다.
- 앞차 없이 명시적으로 시험할 수 있다. 페달·주차브레이크·CAN 오류·제어 비활성·인지 메시지 누락 조건에서는 실행하지 않는다. 누른 요청을 저장했다가 나중에 출발시키지 않는다.
- 로컬 Unix socket 요청은 250 ms 이내 한 번만 소비하고 2.5초 이내 중복 입력을 막는다. controlsd에서 메시지 신선도와 실행 조건을 다시 검사한다.
- `요청 보냄`은 로컬 제어기 전달 상태이며 ECU 수용이나 실제 출발을 뜻하지 않는다.

완전 정차는 물리 standstill, raw 속도 절댓값 0.05 m/s 미만, 필터 속도 절댓값 0.1 m/s 미만으로 함께 확인한다. 실측 완전 정차에서 필터 속도만 약 -0.05 m/s로 흔들린 경우를 허용한다.

## 9월 7일 실차 재시험 후 수정

route `0000004f--740fd8bb3b`의 원본 rlog에서 버튼 요청 2회를 확인했다. 각각 monotonic 237.585/243.517초에 시작했고, 239.582/245.517초에 `timeout`으로 중단됐다. 출발 계획은 239.495/245.295초에 풀렸으므로 ECU 응답을 기다릴 시간은 약 0.09/0.22초뿐이었다. 두 번 모두 속도 제한이 아닌 기존 2초 전체 타임아웃이었다.

홀드 누락은 별도 문제였다. `CarInterface.update()`가 제어 적용 전 `update_auto_hold(None)`을 호출하면서 장기 홀드 플래그를 지웠다. 바퀴 속도 영점에서 벗어나면 다음 `apply()`가 이전 홀드를 이어받지 못했다. 여기에 실패 후 정차 완화 로직이 제동을 약하게 만들어, 로그에서 홀드가 빠지고 브레이크 출력이 400에서 4 수준으로 내려간 채 굴렀다.

수정 사항:

- 물리 standstill과 raw/filtered 속도 영점을 함께 확인해 홀드를 처음 걸고, 상태 읽기와 제어 적용 사이에도 플래그를 유지한다. 이미 잡은 홀드는 저절로 굴렀다는 이유로 해제하지 않는다. 명시적 출발·페달·기어·제어 해제가 홀드를 해제한다.
- 재출발 실패 후 정차 복귀에서는 편안한 정차를 위한 제동 완화를 생략하고 기존 정차 감속 램프를 유지한다. 실패 복귀를 브레이크 출력 4 수준으로 계속 제한하지 않는다.
- 통합 테스트는 실제 card의 `update()` 후 `apply()` 순서를 재현한다.

## 수동 크리프와 RES 단계

완전 정차에서 누른 명시적 버튼 요청에만 다음 단계를 사용한다. 정상 자동 앞차 출발 조건은 유지한다.

1. **브레이크 해제:** 최대 4초 동안 GM 가스 0·마찰제동 0을 생성한다. 이 단계에서는 RES를 보내지 않는다.
2. **크리프 확인:** 물리 standstill 해제와 raw 속도 0.1 m/s 이상을 3개 제어 표본에서 확인한다.
3. **RES 응답 대기:** 새로 2초 응답 창을 시작한다. 기존 200 ms 안정 대기와 새 순정 프레임 동기화 후 RES 5회를 요청한다. 양의 가속은 PCM 수용 전까지 만들지 않는다.
4. **정상 제어 복귀:** 계획기가 출발을 허용하고 PCM 상태가 정상 ACTIVE로 확인되면 기존 가속 제어로 넘긴다. 이미 ACTIVE였던 유압 홀드 요청은 실제 이동도 확인한다.

수동 요청 동안 1.0 m/s 이상 속도, 1.5 m 이상 누적 이동 추정, 후진 또는 잘못된 관측이 감지되면 정차 제어로 복귀한다. 2~3 km/h의 크리프가 종전 1.8 km/h 제한에 걸리지는 않도록 변경했다. 이 값은 감지 기준이며 실제 정지 거리 보장이 아니다.

최신 carState/selfdriveState/longitudinalPlan/radarState/modelV2가 필요하다. FCW 또는 두 lead 중 현재/2초 후 예상 간격이 4 m 이하이면 요청을 차단하고, 시도 도중 조건이 바뀌어도 중단한다. 계획기가 한 번 출발을 허용한 뒤의 새 정차 요구도 무시하지 않는다. 브레이크 해제·크리프 확인·수용·실패 사유는 `gm_manual_resume` 로그로 남긴다.

## 재출발 순서

1. 일반 자동 재출발은 인게이지 완전 정차 0.5초와 기존 앞차 출발 조건 0.2초를 확인한다. 화면 요청에만 앞차 조건을 생략한다.
2. 일반 출발은 기존 출발 완화 제어를 거쳐 마찰제동 0 명령을 생성한다. 정차 요구 중 명시적 수동 크리프에서는 가속 0으로 브레이크를 해제한다. 첫 0 명령 시각을 기록하고 200 ms 대기한다. 이는 실제 유압 해제 ACK가 아니다.
3. 최신 순정 버튼 수신 시각과 counter를 저장한 후 새 원본 프레임에 맞춰 RES 5회, UNPRESS 1회를 기존 bus 0/2 경로로 생성한다. 원본 counter 연속성과 신선도를 검사하고 최소 25 ms 송신 간격을 지킨다. 밀린 프레임을 몰아 보내지 않는다.
4. PCM 정차 상태에서 시작했다면 정상 PCM ACTIVE가 0.2초 유지돼야 수용으로 판정한다. 바퀴가 굴렀다는 이유만으로 PCM 수용을 추정하지 않는다.
5. PCM이 이미 ACTIVE인 유압 홀드 정차에서는 화면 요청으로 홀드를 해제하고 기존 가속 제어를 사용한다. 이 경로는 RES를 보내지 않으며, 실제 standstill 해제와 0.25 m/s 초과 이동을 0.2초 확인해야 성공으로 판정한다.
6. 일반 자동 요청의 2초 또는 수동 단계별 제한 내에 수용되지 않거나 수동 예외 밖에서 정차 요구·제어 조건 변화가 발생하면 기존 정차 제어로 돌아간다. 실패한 정차에서 자동으로 무한 반복하지 않는다. 물리 버튼과 페달이 우선한다.

## 물리 RES 기록과 변경 근거의 한계

`00000045--546df16918/23`, 소스 `225fc5e7`에서 물리 RES 시점에 속도 0, 물리/PCM standstill, 인게이지·종방향 활성, 페달 미입력을 확인했다. 물리 RES는 약 30 ms 간격의 5개 프레임이었다. 첫 물리 RES 약 79.6 ms 후 raw PCM 상태가 4에서 1로 바뀌었고 약 1.49초 뒤 이동이 관측됐다.

동일 정차에서 합성 RES와 브레이크 0 명령이 물리 RES보다 약 216.5 ms 먼저 있었다. 따라서 200 ms 대기는 이 순서를 참고한 구현 후보이며, 유압 해제에 필요한 시간이 200 ms라는 측정 결과가 아니다. 합성·물리 요청이 가까워 성공 원인을 물리 버튼만으로 분리할 수 없다. 이 후보가 실차에서 자동 재출발을 성공시킨다는 검증은 아직 없다.

원본 rlog SHA-256: `213c5aa2bd1f5c4c2ef684fce000f6da6faaef34224dec5c0a466cb846127505`.

Python 송신 데이터, Panda echo, PCM 상태 해제, 실제 엔진 토크와 지속 가속은 서로 다른 증거다. bus 0의 원본 물리 프레임을 제거할 수 없으므로 물리 네트워크 전체의 완전한 버튼 복제를 보장하지 않는다. 이번 변경은 Panda safety 코드, firmware, 제동/가속 상한을 변경하지 않는다.

## 검증

실제 cereal, CAN parser/packer, LongControl, GM controller, 호스트 컴파일 safety를 사용하며 차량 CAN을 송신하지 않는다. 원본 프레임 동기화, 200 ms 대기, 5회 송신, PCM ACK/타임아웃, 앞차 없는 명시적 요청, 기존 ACTIVE 오판 방지, 정차 요구 중 버튼 표시와 요청 차단, 한국어 글꼴과 터치를 검사한다.

```sh
PYTHONPATH=.:opendbc_repo python -m pytest -q -o addopts='' --confcutdir=selfdrive/controls/tests selfdrive/controls/tests/test_longcontrol.py selfdrive/controls/tests/test_gm_resume_integration.py selfdrive/controls/tests/test_gm_manual_resume.py
PYTHONPATH=.:opendbc_repo python -m pytest -q -o addopts='' --confcutdir=opendbc_repo/opendbc/car/gm/tests opendbc_repo/opendbc/car/gm/tests
PYTHONPATH=.:opendbc_repo python -m pytest -q -o addopts='' --confcutdir=opendbc_repo/opendbc/safety/tests opendbc_repo/opendbc/safety/tests/test_gm.py
PYTHONPATH=.:opendbc_repo python -m pytest -q -o addopts='' --confcutdir=selfdrive/ui/tests selfdrive/ui/tests/test_gm_resume_button.py
```

실제 화면 표시와 자동 재가속은 다음 실차 로그·관측으로 별도 확인해야 한다.
