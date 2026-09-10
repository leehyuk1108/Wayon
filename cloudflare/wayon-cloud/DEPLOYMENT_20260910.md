# 2026-09-10 실기기 적용 및 검증 결과

## 결론

Wayon 차량의 콤마, 폰의 My Traverse New·Hylink Dev, 운영 Cloudflare에
이번 클라우드 사용량 절감 변경을 적용했다. 앱 실행/실제 데이터 표시,
콤마 상태 전송과 기존 파일 보존을 확인했다. **실차 주행 검증이나
carrotpilot/wip의 차량 측 Hylink 이식 완료를 뜻하지 않는다.**

| 대상 | 적용 내용 | 확인 결과 |
|---|---|---|
| Wayon 운영 서버 | 동기화 쿼리 3곳과 복합 인덱스 3개 | 운영 배포, 인증/실제 조회, 인덱스 사용 확인 |
| Wayon 콤마 | 업로더 수정 + 새 `wayon_cloud_policy.py` | 기기 내 테스트, 프로세스 교체, 다음 heartbeat 성공 |
| My Traverse New | `2.0-preview.14-cloud-budget`, code 23 | 기존 서명으로 업데이트, 기존 데이터 표시, APK 해시 대조 |
| Hylink Dev | `1.3.1-cloud-budget-debug`, code 5 | 기존 연결 유지, 데이터/지도 표시, APK 해시 대조 |
| carrotpilot/wip 차량 | 이번 실기기 배포 대상 아님 | 차량 측 이식 및 해당 차량 검증은 아직 남음 |

## 타임라인 (한국 시간)

- 약 15:00: Cloudflare 배포 도구 인증, 운영 Worker 소스·설정 확인 및 백업.
- 약 15:06~15:09: 인덱스 생성과 Worker 새 버전 배포. 기존 연결 설정 22개
  전체 내용이 동일한지 확인. 운영본의 기존 기능을 유지하고 쿼리 3곳만 변경.
- 약 15:12~15:15: 연결된 Time Machine에서 이전 Android 서명 키를 찾고
  설치된 두 앱의 인증서와 대조. 기존 위젯을 포함한 My Traverse New와
  Hylink 전체 빌드/테스트 완료.
- 약 15:15: 콤마 업로더 파일 교체와 업로더 프로세스만 재시작.
  폰의 두 앱은 `adb install -r`로 데이터 삭제 없이 업데이트.
- 15:15:43, 15:20:46: 같은 새 업로더 프로세스의 heartbeat 성공 확인.
- 약 15:17~15:23: 앱 실제 화면에서 Hylink 지도 공급자의 API 키 경고 발견.
  홈 지도 공급원을 기존 OSM 방식으로 통일하고 출처 표시를 보완한
  1.3.1을 다시 설치. 경고 타일 제거와 정상 지도 표시를 확인.
- 이후: 설치 APK를 폰에서 다시 가져와 빌드 산출물과 SHA-256 일치 확인.
  인증된 읽기 API 5종 모두 200/JSON 응답 확인.

## 서버: 운영본을 보존한 최소 변경

Git 소스 변경 기준은 `f1d97af327b2aef01904c363f75f1cf1dc9c1e7f`이다.
그러나 운영 서버에는 Git 기준과 다른 기존 주행 리포트·health 병합 기능이
있었다. Git 번들을 통째로 배포하지 않고, 내려받은 운영 번들에서 동일한
cursor 변경 3곳만 적용했다. 기존 `server+d1` 주행 기록 병합도 유지된다.

- 이전 Worker 버전: `5fb7ebfe-8dea-4c13-af90-7f0a1d7ef307`
- 적용 Worker 버전: `b4c54a5f-5ac0-4777-9b36-1db750397a6f` (100%)
- 적용 번들 SHA-256:
  `6b6fafff6bc703cd416aa28a56ddc587494ef9ef4fe29c44efe82f965b9d8a67`
- 연결 설정 22개: 이름/타입뿐 아니라 API 반환 메타데이터 전체 동일.
- 기존 정적 자산과 비밀값 유지. 신규 과금/저장소 이전/기존 자료 삭제 없음.
- `0009_sync_cursor_indexes.sql`만 실행. 처리 결과 6,850 rows written.
- 인덱스 생성 전 대상 건수: trips 600, snapshots 5,834, impact_events 413.
- 운영 EXPLAIN: 세 쿼리 모두 복합 인덱스로 SEARCH. 빈 결과 조회는 각각
  `rows_read=1`, `rows_written=0`이었다. 이는 해당 점검 쿼리의 실측값이지
  하루 사용량이나 5대 운영 비용 보장이 아니다.

운영 번들 대조 테스트는 6종 통과. 기존 Git의 `test_server_trip_fallback`
fixture 1종은 운영본의 `server+d1` 병합을 가정하지 않아 변경 전후 동일하게
실패했다. 해당 핸들러가 바이트 단위로 동일함을 확인했고, 실제 인증 조회에서
`/api/trips`의 `server+d1` 응답도 확인했다. 이를 전체 운영 회귀 테스트 통과로
과장하지 않는다. 향후 통째 배포 전 운영 기능을 Git 소스와 먼저 통합해야 한다.

## 콤마: 기존 주행 수정은 그대로 보존

기기는 `83b817334d7b1f4178fd2e0aca06894a6a60f1d6` 위에 미커밋 수정이
있는 상태였다. 특히 업로더에 기존 `DriveReportAccumulator` 변경이 있었다.
브랜치 전체 checkout/pull/reboot는 하지 않았다.

기존 업로더를 백업하고 이번 변경만 병합한 파일과 새 정책 모듈을 적용했다.
기존 주행 제어·충격·중계 등 다른 수정 파일 13개의 SHA-256이 적용 전후 같았다.
기기 Git HEAD가 최신 브랜치 커밋으로 바뀐 것은 아니다. 향후 Git 업데이트 때
이 현장 수정본과 기존 미커밋 작업을 먼저 통합해야 한다.

- 안전 확인: `IsOffroad=true`, `IsOnroad=false`, 살아 있는 deviceState의
  `started=false`, Panda ignition 2종 false, `noOutput`, faults 없음.
  비주행이라 carState는 수신되지 않았으며 주행 중 CAN 상태를 검증한 것은 아니다.
- 실제 Python: `/usr/local/venv/bin/python`. 저장소 `.venv` 링크 및 단순
  `/usr/bin/python3`은 현재 기기의 실제 서비스 환경과 달랐다. 환경은 수정하지 않았다.
- 대상 변경을 staging import한 기기 테스트: 18 passed.
- 적용 후 실제 모듈에 대한 기존 업로더 테스트: 15 passed.
- 프로세스 PID: 14307 → 435489. 5분 뒤에도 같은 PID에서 전송 성공.
- 업로더 SHA-256:
  `8f3cf311950dff7e4436d05d83f99d1e423bfa57969f5309f7139eb970006760`
- 정책 모듈 SHA-256:
  `2caf78e7d99dcbacf03739058d08be3ef8b4adee912fda6efee5738e19b63fc1`
- 기기 백업: `/data/wayon_cloud/deploy-backups/20260910-cloud-budget/`

점검 중 SSH 연결이 끊긴 사례가 있었다. 기존 relay는 같은 역할의 새 연결이
오면 이전 연결을 `replaced`로 종료한다. 진단 SSH를 겹쳐 열지 않고 직렬로
실행한 마지막 검증은 끝까지 통과했다. 이를 새 CAN 오류나 모든 네트워크
안정성 문제의 해결로 해석하지 않는다.

## 앱: 기존 서명과 기능 보존

My Traverse New 설치본의 `main.html` 해시가 기존 로컬 작업본과 같았고,
설치 DEX에도 Mini Home 위젯 클래스가 있었다. 이 기존 작업을 별도 브랜치에
보존한 뒤 조회 정책만 적용했다. 원래 dirty checkout은 변경하지 않았다.
Firebase 설정이 활성화된 release 빌드 및 23개 테스트가 통과했다.

Hylink는 전체 debug 빌드 및 4개 테스트, 별도 캐시/백오프 정책 테스트와
지도 공급원/출처 검사에 통과했다. 홈 지도의 CARTO API 키 요구 경고는
실제 화면에서 발견한 별도 문제였으며, 이미 쓰던 OpenStreetMap으로 통일했다.
앱 식별 User-Agent와 기본 HTTP 캐시를 유지하며 대량 타일 수집은 추가하지 않았다.
[OpenStreetMap 타일 정책](https://operations.osmfoundation.org/policies/tiles/)

- My Traverse 소스: `codex/my-traverse-device-20260910`,
  `d59546f26bb1acd1b027056c98341a3bb1a95730`
- Hylink 소스: `codex/hylink-dev-budget-20260910`,
  `1354fc8718a8308fa5a306102e11e7fb790e853a`
- My Traverse 설치 APK SHA-256:
  `f679a89bd2e56447a6faf9f665a6e55311d1af4be1cc71840ff4f13a9988d8d7`
- Hylink 설치 APK SHA-256:
  `0755d01ce1aa11675d18c90e3464be6fe0f430faebca650b992fa26b2c2137f8`

기존 인증서와 일치하는 Time Machine 키로 서명했다. 키와 실제 설정은 Git에
올리지 않았다. 기존 앱 삭제/데이터 초기화를 하지 않았고, 두 앱의 기존 차량
데이터 표시와 필터링한 실행 로그에서 치명적 오류가 없음을 확인했다.

## 남은 검증과 복구 기준

- 실제 주행, 정차 후 재출발, CAN/ACC 경고 여부: 이번 비주행 점검으로 보장하지 못함.
- 실제 차량 조작, 실시간 카메라/SSH의 주행 전환, 실제 충격·푸시 알림: 미실행.
- carrotpilot/wip 차량 측 Hylink 이식과 해당 차량 적용: 미완료.
  이번 Hylink 앱 점검은 기존에 연결된 Wayon 차량으로 시행했다.
- 5대 동시 운용 및 일일/장기 한도: 아직 실측 검증하지 않음.
- KV 저장소 이전·보관 기간 정책, 외부 서버 poll 최적화: 별도 남은 작업.

문제가 있으면 비주행 확인 후 콤마의 백업 업로더로 복구하고 해당 프로세스만
재시작한다. 서버는 이전 Worker 버전으로 되돌릴 수 있으며 추가 인덱스는
이전 Worker와 호환되므로 지울 필요가 없다. 앱의 이전 APK도 로컬 보존했으나
versionCode 하향 설치는 별도 안전한 절차가 필요하다. 앱 삭제로 되돌리지 않는다.

배포 APK·이전 APK·현장 파일·화면 증거는 로컬 `release/cloud-budget-20260910`
폴더에 보관했다. 위치가 포함된 화면, 서명 키, 운영 설정 백업은 Git 미포함이다.
