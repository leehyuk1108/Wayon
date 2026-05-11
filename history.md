# StarPilot C4/Mici 작업 이력

최종 업데이트: 2026-05-11 KST

이 문서는 `HyukLee-og/StarPilot`의 `StarPilot` 브랜치를 로컬로 클론한 뒤, C4/Mici 기기에 맞춰 진행한 작업을 다음 작업자가 바로 이어받을 수 있게 정리한 기록이다.

## 현재 기준 상태

- 로컬 repo: `/Users/ijonghyeog/Desktop/starpilot`
- 원격 repo: `https://github.com/HyukLee-og/StarPilot.git`
- 로컬 브랜치: `StarPilot`
- 로컬 기준 HEAD: `2e7036ab`
- 실제 기기: `comma@comma-db5ce68d.local`
- 실제 기기 IP: `192.168.35.175`
- 기기 repo 경로: `/data/openpilot`
- 기기 브랜치/HEAD: `StarPilot` / `2e7036ab`
- 기기 하드웨어 확인: `HARDWARE Tici`, `DEVICE_TYPE mici`
- 기기 상태 확인 시점: `IsOffroad=1`, `IsOnroad=0`, `IsEngaged=0`
- 기기 UI 프로세스: `selfdrive.ui.ui`, 마지막 재시작 후 PID `59072`
- 기기 offroad wake watcher: 수동 백그라운드 실행 중, PID `59006`
- 기기 언어 파라미터: `LanguageSetting=main_ko`
- 단위 파라미터: `IsMetric=1`

현재 작업은 아직 커밋하지 않은 working tree 변경 상태다. 재부팅만으로는 일반적으로 `/data/openpilot`의 working tree가 자동으로 원격 원본으로 되돌아가지 않는다. 다만 업데이트/브랜치 전환/강제 reset/재설치/overlay 갱신 작업을 하면 덮일 수 있으므로, 장기 보존하려면 커밋하거나 별도 백업이 필요하다.

## 초기 확인

### C4/Mici 사용 가능성

- 이 브랜치는 C4/Mici에서 Python/Raylib UI 경로를 사용한다.
- 관련 근거:
  - `system/manager/process_config.py`에 C4/Mici가 Python UI path를 사용한다는 주석/분기가 있음.
  - 실제 기기에서 `HARDWARE Tici`, `DEVICE_TYPE mici`로 확인됨.
- 따라서 UI 수정 시 Qt 경로만 보면 안 되고, 주로 `selfdrive/ui/mici/...`와 `system/ui/...`를 확인해야 한다.

### Chevrolet Traverse 2023 지원 확인

- `opendbc_repo/opendbc/car/gm/values.py`에 `CHEVROLET_TRAVERSE`가 등록되어 있다.
- 문서상 대상은 `Chevrolet Traverse 2022-23`, 조건은 `RS, Premier, or High Country Trim`.
- `opendbc_repo/opendbc/car/gm/fingerprints.py`에도 `CAR.CHEVROLET_TRAVERSE` fingerprint가 있다.
- `opendbc_repo/opendbc/car/gm/interface.py`에서 Traverse/Blazer 전용 설정 분기가 있다.
- `SDGM_CAR`에도 Traverse가 포함되어 있다.

## 기기 설치/반영 방식

작업 대상 기기는 같은 네트워크의 `comma-db5ce68d.local`이고 SSH 사용자는 `comma`다.

주로 사용한 방식:

```bash
ssh comma@comma-db5ce68d.local
scp <local-file> comma@comma-db5ce68d.local:/data/openpilot/<same-path>
```

Python 검증은 기기 기본 `python3`만 쓰면 dependency가 부족할 수 있으므로, `/data/openpilot/launch_env.sh`를 source한 뒤 실행했다.

```bash
cd /data/openpilot
. ./launch_env.sh
python3 -m py_compile <files>
```

UI 파일을 바꾼 뒤 즉시 화면 반영이 필요하면 기기가 offroad인지 확인한 뒤 UI 프로세스만 재시작했다.

```bash
cat /data/params/d/IsOffroad
cat /data/params/d/IsOnroad
cat /data/params/d/IsEngaged
pkill -x selfdrive.ui.ui
```

마지막 UI 재시작은 offroad 상태에서 수행했고, PID가 `64023 -> 66926`으로 바뀐 것을 확인했다.

## 한국어 이벤트/알림 작업

### 수정 파일

- `selfdrive/selfdrived/events.py`
- `selfdrive/ui/translations/app_ko.po`
- `selfdrive/ui/mici/widgets/button.py`
- `selfdrive/ui/mici/widgets/dialog.py`
- `system/ui/widgets/slider.py`
- `system/ui/lib/multilang.py`
- `selfdrive/ui/mici/layouts/settings/device.py`

### 변경 내용

- `events.py`의 주요 openpilot/StarPilot 이벤트 문구를 한국어로 변경했다.
- `NoEntryAlert`, `SoftDisableAlert`, `ImmediateDisableAlert`, `StartupAlert` 같은 공통 Alert 생성자 기본 문구도 한국어로 바꿨다.
- Mici의 startup alert에서는 기본 안전 문구가 중복으로 보이지 않도록 device type이 `mici`일 때 두 번째 줄을 비우는 로직을 유지했다.
- `belowSteerSpeed`는 사용자가 실제 화면에서 거슬려 하던 stopped-state alert 계열이라 문구와 성격을 부드럽게 조정했다.
  - 제목: `조향 보조 꺼짐`
  - 설명: `최소 속도 ...`
  - `AlertStatus.normal`, `AudibleAlert.none`, 짧은 duration으로 낮춤.
- `app_ko.po`를 추가해 Mici/설정 화면의 일반 UI 문구도 한국어로 받을 수 있게 했다.
  - 현재 `msgstr`이 채워진 항목은 약 475개.
  - `starpilot-c4-mici-localization` 주석이 달린 별도 항목들도 포함되어 있다.
- `device ID`, `serial`처럼 Mici device info 화면에 남던 영어는 `tr()`를 통과하도록 바꿨다.
- Mici의 `BigButton`, dialog option, input hint, slider label처럼 동적으로 들어오는 텍스트도 `tr()`를 적용하도록 했다.
- 줄바꿈이 있는 버튼 문자열은 줄 단위로 번역 fallback을 시도하도록 `display_text()` helper를 추가했다.
- `LanguageSetting`이 `main_ko` 형태로 저장되어도 내부 언어 코드는 `ko`로 정규화되도록 `system/ui/lib/multilang.py`를 수정했다.

### 주의

- 아직 모든 화면의 모든 문자열을 직접 눌러 검증한 것은 아니다.
- 동적 문자열이 코드에서 조합되는 경우 `app_ko.po`에 있어도 표시 위치에서 `tr()`를 통과하지 않으면 영어가 남을 수 있다.
- Mici 경로에서 영어가 남으면 먼저 `selfdrive/ui/mici/...`, `system/ui/...`, `selfdrive/ui/translations/app_ko.po` 세 군데를 같이 확인해야 한다.

## 한국어 폰트/Pretendard 작업

### 입력 자료

- 사용자가 제공한 파일: `/Users/ijonghyeog/Downloads/Pretendard-1.3.9.zip`
- 적용 폰트: `Pretendard-SemiBold`

### 수정/생성 파일

- `selfdrive/assets/fonts/Pretendard-SemiBold.otf`
- `selfdrive/assets/fonts/Pretendard-SemiBold.fnt`
- `selfdrive/assets/fonts/Pretendard-SemiBold.png`
- `selfdrive/assets/fonts/process.py`
- `system/ui/lib/application.py`

### 변경 내용

- `FontWeight.KOREAN = "Pretendard-SemiBold.fnt"`를 추가했다.
- 언어가 `ko`이면 일반 `unifont`가 아니라 `Pretendard-SemiBold.fnt`를 fallback font로 쓰도록 했다.
- `rl.gui_set_font()`도 한국어일 때 Pretendard fallback이 기본 GUI 폰트로 들어가도록 바꿨다.
- `process.py`에서 Pretendard 계열도 CJK/unifont glyph set을 사용해 atlas를 만들도록 했다.
- 한국어 glyph 누락을 줄이기 위해 아래 source의 문자들을 Korean atlas에 포함하도록 했다.
  - `selfdrive/selfdrived/events.py`
  - `selfdrive/ui/mici/**/*.py`
  - `system/ui/**/*.py`
- 홈 화면에서 쓰는 `안녕하세요`, `안전한 주행 되세요` 등도 extra chars에 포함했다.

### 확인된 상태

- 로컬 폰트 파일:
  - `Pretendard-SemiBold.otf` 약 1.5 MB
  - `Pretendard-SemiBold.fnt` 약 169 KB
  - `Pretendard-SemiBold.png` 약 1.5 MB
- 기기에도 `/data/openpilot/selfdrive/assets/fonts/` 아래 같은 Pretendard 파일이 존재한다.
- 재부팅 후 한국어 폰트가 실제로 적용되는 것을 확인했다.

### 주의

- 폰트 atlas가 바뀌면 단순 UI 재시작보다 재부팅이 더 확실할 때가 있었다.
- `Pretendard-SemiBold.otf`는 현재 untracked로 잡혀 있다.
- `Pretendard-SemiBold.fnt/png`는 작업 중 생성/반영된 파일이므로 누락되면 한글이 다시 깨질 수 있다.

## 기기 언어 설정

- 기기 언어는 한국어로 바꾸는 작업을 진행했다.
- 현재 기기 파라미터는 `LanguageSetting=main_ko`로 확인된다.
- 코드에서는 `main_ko`를 `ko`로 정규화하도록 수정했다.
- 처음에는 여전히 영어가 많이 남았고, 이후 `app_ko.po`, `display_text()`, widget-level `tr()` 적용으로 범위를 넓혔다.

## Mici Home 화면 변경

### 수정 파일

- `selfdrive/ui/mici/layouts/home.py`

### 진행 순서

1. 기존 home 화면은 `starpilot`, 버전, 날짜, branch/model, 하단 아이콘을 보여주는 형태였다.
2. Galaxy 웹 설정에는 drives/km/hours가 나오지만 기기 home에서는 값이 0으로 보이는 문제가 있었다.
3. 사용자가 주행 통계 대신 단순 greeting 화면을 원해서 통계 표시를 제거했다.
4. 최종 구조는 아래 두 줄만 보이도록 했다.
   - `안녕하세요!`
   - `안전한 주행 되세요`
5. 이후 글씨가 너무 작다는 피드백에 따라 폰트 크기를 키웠다.

### 현재 구현

- `안녕하세요!`
  - `UnifiedLabel`
  - `font_size=72`
  - `FontWeight.KOREAN`
  - 중앙 정렬
- `안전한 주행 되세요`
  - `UnifiedLabel`
  - `font_size=40`
  - `FontWeight.KOREAN`
  - 회색 텍스트
  - 중앙 정렬
- render 위치:
  - 첫 줄: `self.rect.y + 28`, 높이 `96`
  - 둘째 줄: `self.rect.y + 132`, 높이 `58`
- 홈 화면을 눌렀을 때 설정 창으로 들어가는 callback은 유지했다.
- 기존 하단 아이콘, 네트워크 아이콘, experimental/mic 아이콘, 버전/branch 표시, long press experimental toggle 코드는 제거된 상태다.

### 기기 반영

- `/data/openpilot/selfdrive/ui/mici/layouts/home.py`에 복사 완료.
- 기기에서 `python3 -m py_compile selfdrive/ui/mici/layouts/home.py` 통과.
- offroad 상태 확인 후 `selfdrive.ui.ui`를 재시작했고 PID `66926`으로 새 코드가 로드됐다.

## Mici Onroad path/차선 및 sunnypilot UI 요소 이식

### 수정 파일

- `selfdrive/ui/mici/onroad/augmented_road_view.py`
- `selfdrive/ui/mici/onroad/model_renderer.py`
- `selfdrive/ui/mici/onroad/alert_renderer.py`
- `selfdrive/ui/mici/onroad/hud_renderer.py`
- `selfdrive/ui/mici/onroad/blind_spot_indicators.py`
- `selfdrive/ui/mici/onroad/circular_alerts.py`
- `selfdrive/ui/ui_state.py`
- `selfdrive/assets/icons/autohold.png`
- `selfdrive/assets/icons/parking.png`
- `selfdrive/assets/images/green_light.png`
- `selfdrive/assets/images/lead_depart.png`

### 변경 내용

- Onroad UI 가장자리에 뜨던 StarPilot 상태색 테두리는 제거했고, 이후 sunnypilot처럼 검은 rounded border를 다시 그리도록 바꿨다.
  - 현재 `_draw_border()`는 `rl.draw_rectangle_rounded_lines_ex(self._content_rect, 0.2 * 1.02, 10, 50, rl.BLACK)`만 수행한다.
- `model_renderer.py`의 path/차선 색을 sunnypilot 방식에 맞췄다.
  - engaged 상태에서 일반 차선은 흰색, 중앙/인접 차선은 초록색.
  - 토크가 강하게 걸리면 해당 쪽 차선이 주황색으로 섞인다.
  - disengaged 상태에서는 path/차선/lead marker를 그리지 않는다.
  - StarPilot Mici 전용 `PathColor`, `LaneLinesColor`, `PathEdgesColor`, `ModelUI`, `DynamicPathWidth` 커스텀 색/폭 분기는 Mici path 렌더러에서 제거했다.
  - rainbow path 값도 sunnypilot에 맞춰 `8 segments`, `speed 50`, `base alpha 0.8` 계열로 조정했다.
- `alert_renderer.py`에 sunnypilot식 중앙 autohold/parking brake timer를 추가했다.
  - `resumeRequired` 이벤트는 중앙에 autohold 아이콘과 `MM:SS` 타이머를 크게 표시한다.
  - `carState.parkingBrake`가 true이면 parking 아이콘과 `MM:SS` 타이머를 표시한다.
  - `parkBrake`/`silentParkBrake` 계열은 일반 top gradient 대신 중앙 timer를 사용한다.
- `greenPrompt`/green light/lead departing 계열 alert는 sunnypilot 녹색 배경을 쓰도록 했다.
- StarPilot의 `starpilotSelfdriveState`와 `starpilotOnroadEvents`를 Mici UI SubMaster에 추가했다.
  - Mici UI가 StarPilot 전용 `greenLight`, `leadDeparting` alert를 읽을 수 있게 하기 위함이다.
- `BlindSpotIndicators`를 Mici HUD에 추가했다.
  - `carState.leftBlindspot`/`rightBlindspot`에 따라 좌우 blind spot 아이콘이 pulsing alpha로 표시된다.
- `CircularAlertsRenderer`를 Mici HUD에 추가했다.
  - StarPilot `greenLight`/`leadDeparting` 이벤트를 받아 sunnypilot asset 기반 원형 알림을 표시한다.
- 필요한 asset은 Desktop의 sunnypilot에서 가져왔다.

### 주의

- 이 변경은 로컬과 기기 양쪽에서 `py_compile` 검증까지 완료했다.
- 2026-05-11 12:52 KST 기준 새 IP `192.168.35.175`로 접속 성공:
  - 대상: `comma@192.168.35.175:/data/openpilot`
	  - 확인: `/proc/device-tree/model` = `comma mici`, branch = `StarPilot`, HEAD = `2e7036ab`
	  - 복사 파일: Mici onroad renderer 5개, `ui_state.py`, autohold/parking/green_light/lead_depart asset
	  - 기기 검증: `REMOTE_COMPILE_OK`
	  - 당시 상태: `IsOffroad=0`, `IsOnroad=1`, `IsEngaged=0`, UI PID `48543`
	  - 처음에는 onroad 상태였으므로 UI 프로세스 재시작을 보류했다.
- 2026-05-11 12:55 KST 기준 사용자가 정차 중이라고 확인해 UI 재시작을 진행했다.
  - 1차 재시작 후 `CircularAlertsRenderer`에서 `starpilotOnroadEvents` 키가 없는 런타임을 직접 참조해 `KeyError`가 발생했다.
  - `circular_alerts.py`와 `alert_renderer.py`에서 StarPilot 전용 SubMaster 키를 `recv_frame.get(..., -1)` 방식으로 방어 처리했다.
  - 패치 후 기기에서 `REMOTE_PATCH_COMPILE_OK` 확인.
  - 2차 UI 재시작 후 새 UI PID `66324`가 5초/15초 후에도 유지됐고, `/data/error_logs/error.txt` mtime 변화가 없었다.
- 2026-05-11 13:54 KST 기준 사운드와 정차 타이머 후속 수정 적용.
  - `common/params_keys.h`의 `SoundPack` 기본값을 `frog`에서 `stock`으로 변경했다.
  - sunnypilot에만 있던 `prompt_single_high.wav`, `prompt_single_low.wav`를 `selfdrive/assets/sounds/`에 추가했다.
  - 기존 기본 sound wav들은 sunnypilot과 SHA-256 해시가 동일했다.
  - 기기 파라미터를 `SoundPack=frog -> stock`으로 변경하고 `StarPilotTogglesUpdated` 플래그를 세웠다.
  - 기기 active sound target은 `/data/openpilot/selfdrive/assets/sounds`로 확인했다.
  - `alert_renderer.py`의 autohold/parking 중앙 타이머는 offroad 전환 또는 새 onroad cycle 시작 시 start time을 초기화하도록 변경했다.
  - 기기에서 `REMOTE_SOUND_TIMER_COMPILE_OK` 확인 후 UI를 재시작했고, 새 UI PID `49899`가 유지됐다.
- 동일 이름의 border/path 관련 코드가 Qt 또는 large UI 경로에도 있지만, 사용자가 지적한 대상은 C4/Mici이므로 `selfdrive/ui/mici/...` 중심으로 수정했다.

## 로컬 UI preview

README 기준:

```bash
./c3  # large UI
./c4  # small UI
```

- C4/Mici 확인에는 `./c4`가 맞다.
- 이전에 기본 버전이 뜨는 문제가 있었고, 수정된 checkout의 코드가 뜨도록 로컬 repo 기준 preview를 맞췄다.
- 현재 시점에 로컬 preview 프로세스는 계속 켜져 있지 않다.

## GM 계기판 속도 보정

### 배경

- 목표: GM 차량에서 comma 화면 표시 속도가 계기판 기준과 맞도록 보정.
- 예: 기존 comma 화면 95 km/h, 차량 계기판 100 km/h이면 comma 화면도 100 km/h가 되도록 한다.
- 내부 제어용 raw 속도, wheel speed, safety 속도는 건드리지 않고 display/cluster-facing 값만 보정한다.

### 수정 파일

- `opendbc_repo/opendbc/car/gm/cluster_speed.py`
- `opendbc_repo/opendbc/car/gm/carstate.py`
- `opendbc_repo/opendbc/car/gm/gmcan.py`
- `opendbc_repo/opendbc/car/gm/carcontroller.py`

### 변경 내용

- `cluster_speed.py`를 새로 추가했다.
- 실측 기반 table은 `(cluster_display_kph, openpilot_raw_display_kph)` 구조다.
- 제공된 공식 흐름을 그대로 사용한다.
  - raw m/s -> raw display kph
  - 실측 table 보간으로 cluster display kph
  - 다시 cluster m/s로 저장
- 역변환도 추가했다.
  - cluster m/s -> cluster display kph
  - 실측 table 보간으로 raw display kph
  - 다시 raw m/s
- 핵심 함수:
  - `gm_cluster_display_kph_from_raw_display_kph()`
  - `gm_raw_display_kph_from_cluster_display_kph()`
  - `gm_cluster_cruise_speed_from_raw_ms()`
  - `gm_raw_cruise_speed_from_cluster_ms()`
- `carstate.py`에서 기존 단순 `cluster_offset` 곱셈을 제거하고 아래 값을 채우도록 했다.
  - `ret.vEgoCluster`
  - `ret.cruiseState.speedCluster`
- `gmcan.py`의 `create_gm_cc_spam_command()`는 현재 크루즈 설정속도를 읽을 때 `speedCluster`를 우선 사용한다.
- 버튼 기반 크루즈 목표 계산은 cluster 표시 기준으로 비교하고, raw 기준 비교가 필요한 곳은 역변환을 사용한다.
- `carcontroller.py`의 gas override decel 조건도 raw/cluster가 섞이지 않게 `display_set_speed`, `display_v_ego`로 비교하도록 바꿨다.

### C4/Mici HUD 확인

- `selfdrive/ui/mici/onroad/hud_renderer.py`는 이미 `car_state.vCruiseCluster`와 `car_state.vEgoCluster`를 우선 사용하고 있었다.
- `selfdrive/ui/qt/onroad/hud.cc`도 `vEgoCluster`를 우선 사용하며, `use_wheel_speed` toggle이 있으면 기존 의도를 유지한다.
- Mici Python HUD 쪽에는 `use_wheel_speed` 옵션 흐름이 별도로 없었다.

### 검증

로컬:

```bash
python3 -m py_compile \
  opendbc_repo/opendbc/car/gm/cluster_speed.py \
  opendbc_repo/opendbc/car/gm/carstate.py \
  opendbc_repo/opendbc/car/gm/carcontroller.py \
  opendbc_repo/opendbc/car/gm/gmcan.py
```

변환 검증:

```python
from opendbc.car.gm.cluster_speed import (
  gm_cluster_display_kph_from_raw_display_kph,
  gm_raw_display_kph_from_cluster_display_kph,
)

assert round(gm_cluster_display_kph_from_raw_display_kph(95.0)) == 100
assert round(gm_raw_display_kph_from_cluster_display_kph(100.0)) == 95
```

기기:

- GM 관련 4개 파일을 `/data/openpilot/opendbc_repo/opendbc/car/gm/`에 복사 완료.
- 기기에서 `launch_env.sh` 적용 후 `py_compile` 통과.
- 기기에서 변환 검증 `95 -> 100`, `100 -> 95` 통과.

### 주의

- `opendbc`는 기기/로컬 모두 `opendbc_repo/opendbc` symlink 구조다.
- GM 보정은 GM 경로에만 들어갔다. 다른 브랜드 차량에는 영향을 주지 않는 구조다.
- `carstate.py`가 `vEgoCluster`와 `speedCluster`를 채우는 것이 핵심이다.
- table은 실측 기반이므로 단순 비율 보정으로 바꾸면 안 된다.

## 현재 modified/untracked 파일 목록

현재 로컬 `git status --short` 기준:

```text
 M opendbc_repo/opendbc/car/gm/carcontroller.py
 M opendbc_repo/opendbc/car/gm/carstate.py
 M opendbc_repo/opendbc/car/gm/gmcan.py
 M selfdrive/assets/fonts/process.py
 M selfdrive/selfdrived/events.py
 M selfdrive/ui/mici/layouts/home.py
 M selfdrive/ui/mici/layouts/settings/device.py
 M selfdrive/ui/mici/onroad/augmented_road_view.py
 M selfdrive/ui/mici/widgets/button.py
 M selfdrive/ui/mici/widgets/dialog.py
 M selfdrive/ui/translations/app_ko.po
 M system/ui/lib/application.py
 M system/ui/lib/multilang.py
 M system/ui/widgets/slider.py
?? opendbc_repo/opendbc/car/gm/cluster_speed.py
?? selfdrive/assets/fonts/Pretendard-SemiBold.otf
```

`history.md` 자체도 이 문서 생성 후 untracked 또는 modified로 추가된다.

## 기기에 복사/반영된 주요 파일

기기 경로는 모두 `/data/openpilot` 기준이다.

- `selfdrive/selfdrived/events.py`
- `selfdrive/ui/translations/app_ko.po`
- `system/ui/lib/application.py`
- `system/ui/lib/multilang.py`
- `system/ui/widgets/slider.py`
- `selfdrive/ui/mici/widgets/button.py`
- `selfdrive/ui/mici/widgets/dialog.py`
- `selfdrive/ui/mici/layouts/settings/device.py`
- `selfdrive/ui/mici/layouts/home.py`
- `selfdrive/ui/mici/layouts/main.py`
- `selfdrive/ui/ui_state.py`
- `selfdrive/ui/mici/onroad/augmented_road_view.py`
- `selfdrive/assets/fonts/process.py`
- `selfdrive/assets/fonts/Pretendard-SemiBold.otf`
- `selfdrive/assets/fonts/Pretendard-SemiBold.fnt`
- `selfdrive/assets/fonts/Pretendard-SemiBold.png`
- `opendbc_repo/opendbc/car/gm/cluster_speed.py`
- `opendbc_repo/opendbc/car/gm/carstate.py`
- `opendbc_repo/opendbc/car/gm/carcontroller.py`
- `opendbc_repo/opendbc/car/gm/gmcan.py`

## 검증 완료한 것

- 로컬 `home.py` py_compile 통과.
- 기기 `home.py` py_compile 통과.
- 로컬 GM cluster speed 관련 파일 py_compile 통과.
- 기기 GM cluster speed 관련 파일 py_compile 통과.
- 로컬/기기 모두 `95 -> 100`, `100 -> 95` 변환 검증 통과.
- 기기 `HARDWARE Tici`, `DEVICE_TYPE mici` 확인.
- 기기 offroad 상태에서 UI 재시작 확인.
- 로컬/기기 `selfdrive/ui/mici/layouts/main.py` py_compile 통과.
- 로컬/기기 `selfdrive/ui/ui_state.py` py_compile 통과.
- 기기 `LanguageSetting=main_ko` 확인.
- 재부팅 후 Pretendard 기반 한국어 폰트가 적용되는 것 확인.

## 아직 주의해야 할 점

- 이 변경들은 아직 커밋되지 않았다.
- 기기와 로컬 모두 같은 HEAD 위에 working tree patch가 얹힌 상태다.
- 업데이트/branch switch/reset이 들어가면 기기 변경이 덮일 수 있다.
- Mici UI에서 영어가 새로 보이면 해당 문자열이 `tr()`를 통과하는지부터 확인해야 한다.
- 홈 화면의 기존 version/network/status 아이콘을 제거했기 때문에, 해당 정보가 필요해지면 별도 화면이나 gesture로 다시 설계해야 한다.
- GM cluster speed 보정은 display/cluster 값 전용이다. 제어 로직의 raw speed를 보정값으로 바꾸면 안 된다.
- Onroad border는 Mici 경로에서만 제거했다. 다른 UI 경로에서 비슷한 border가 보이면 별도 파일을 확인해야 한다.

## 다음 사람이 이어서 할 때 추천 순서

1. `git status --short`로 현재 dirty 파일을 확인한다.
2. 기기 상태를 확인한다.

```bash
ssh comma@comma-db5ce68d.local 'cat /data/params/d/IsOffroad; cat /data/params/d/IsOnroad; cat /data/params/d/IsEngaged'
```

3. UI 작업이면 `selfdrive/ui/mici/...`를 먼저 본다.
4. 한국어 글자 깨짐이면 `system/ui/lib/application.py`, `selfdrive/assets/fonts/process.py`, `selfdrive/assets/fonts/Pretendard-SemiBold.*`를 먼저 본다.
5. GM 속도 표시 문제면 `opendbc_repo/opendbc/car/gm/cluster_speed.py`와 `carstate.py`의 `vEgoCluster`/`speedCluster` 채움 여부를 먼저 본다.
6. 변경을 장기 보존하려면 커밋하거나 최소한 patch 백업을 만든다.

## 2026-05-11 추가: Mici home/onroad 스크롤 제거 및 fade 전환

사용자 요청: offroad home 화면에서 오른쪽 스크롤로 onroad UI가 나오는 구조를 없애고, 시동 ON/OFF에 따라 home/offroad와 onroad가 부드럽게 fade in/out 전환되도록 변경.

추가 수정: 최초 구현에서 메인 가로 스크롤을 완전히 제거해 수동 알림 페이지 진입 경로까지 사라지는 문제가 있었다. 이후 구조를 다시 조정해서 `alerts ↔ home` 오프로드 스크롤은 남기고, `home → onroad` 스크롤만 제거했다.

추가 수정 2: 별도 `self._offroad_scroller` 방식은 기존 Mici 스크롤 감각과 다르게 느껴질 수 있어 제거했다. 최종 구조는 다시 `MiciMainLayout(Scroller)`를 직접 상속하고, 원래 `self._scroller`에 `alerts`, `home` 두 페이지만 넣어 기존 Scroller 메커니즘을 그대로 사용한다. `onroad`만 Scroller item에서 제외하고 fade 전환용 별도 surface로 렌더한다.

추가 수정 3: 2페이지 구성에서 손을 뗀 뒤 중간 offset에 멈추는 문제가 남아, Scroller 코어를 수정하지 않고 메인 레이아웃에서만 release/steady 시 가까운 페이지로 `self._scroller.scroll_to(..., smooth=True, block_interaction=True)`를 호출하도록 보정했다. offset을 직접 고정하는 방식이 아니라 기존 Scroller의 smooth auto-scroll 경로를 사용한다.

수정 파일:

- `selfdrive/ui/mici/layouts/main.py`

구현 방식:

- `MiciMainLayout(Scroller)` 상속은 유지한다.
- 기존과 같은 `self._scroller`에 `alerts`, `home` 두 페이지만 등록한다.
- `onroad`는 `self._scroller.add_widgets(...)`에서 제거하고 `self._child(AugmentedRoadView(...))`로 별도 보관한다.
- 수동 스와이프/스크롤로 onroad 화면에 접근하는 동작만 제거.
- 알림 페이지는 기존처럼 offroad home에서 좌우 스와이프로 접근 가능하다.
- 별도 강제 snap 보정(`ScrollState`/`OFFROAD_SNAP_EPS`)은 제거했다. `alerts ↔ home`은 원래 `Scroller(snap_items=True, spacing=0, pad=0, scroll_indicator=False, edge_shadows=False)` 동작을 그대로 따른다.
- 단, 손을 뗀 뒤 중간 offset이 남으면 `ScrollState.STEADY` 또는 release 프레임에서 가까운 페이지를 계산해 기존 `scroll_to(..., block_interaction=True)`로 자동 스냅을 시작한다.
- `ui_state.started`가 `True`가 되면 기존 `ONROAD_DELAY = 2.5s` 후 nav stack을 main으로 정리하고 onroad로 fade 전환.
- `ui_state.started`가 `False`가 되면 offroad surface로 fade 전환.
- offroad surface는 기존 `self._scroller`이며, active offroad alert가 있으면 알림 페이지로, 없으면 home 페이지로 자동 위치를 맞춘다.
- 전환은 `FADE_DURATION = 0.55s` 동안 검은 overlay를 smoothstep alpha로 올렸다가 내리는 방식이다. 렌더 텍스처를 새로 만들지 않아 camera/vision 렌더 경로를 건드리지 않는다.
- offroad로 돌아갈 때는 onroad renderer가 이미 offroad 상태 문구를 그리는 순간적인 flash를 줄이기 위해 target 화면을 검은 화면에서 fade in하는 방식으로 처리했다.
- `home`과 `alerts`는 원래 Scroller item lifecycle을 따른다. `onroad`는 별도 렌더 surface라 `self._child(...)`로 등록했다.
- settings 화면은 nav stack으로 push되는 별도 화면이므로 child로 등록하지 않았다.

검증:

- 로컬: `python3 -m py_compile selfdrive/ui/mici/layouts/main.py`
- 로컬: `git diff --check -- selfdrive/ui/mici/layouts/main.py`
- 기기: `/usr/local/venv/bin/python3 -m py_compile selfdrive/ui/mici/layouts/main.py`
- 기기 확인: `/proc/device-tree/model = comma mici`
- 기기 확인: `/data/openpilot` branch/head = `StarPilot` / `2e7036ab`
- 기기 반영: `COPYFILE_DISABLE=1 tar cf - selfdrive/ui/mici/layouts/main.py | ssh comma@192.168.35.175 'cd /data/openpilot && tar xf - ...'`
- 기기 UI 재시작: `pkill -x selfdrive.ui.ui`
- 재시작 후 확인: `UI_PID=55904`, `IsOffroad=1`, `IsOnroad=0`, `IsEngaged=0`
- 최신 error log는 이번 변경 이전 시각인 `2026-05-11 13:01:18 KST`의 과거 로그였고, 수정 파일 반영 후 새 crash log는 증가하지 않았다.

## 2026-05-11 추가: 화면 꺼짐 후 짧은 탭 wake 보정

사용자 보고: comma 화면이 꺼진 뒤 화면을 눌러도 켜지지 않는 증상.

수정 파일:

- `selfdrive/ui/ui_state.py`

구현 방식:

- 기존 `Device._update_wakefulness()`는 interaction timeout reset 조건으로 `ev.left_down`만 확인했다.
- 짧은 탭에서는 프레임/터치 이벤트 타이밍에 따라 `left_pressed` 이벤트만 들어오고 `left_down`을 놓칠 가능성이 있어, 깨우기 입력 조건을 `ev.left_down or ev.left_pressed`로 확장했다.
- 기존에 이 파일에 추가되어 있던 `starpilotOnroadEvents`, `starpilotSelfdriveState` 구독 변경은 유지했다.

검증:

- 로컬: `python3 -m py_compile selfdrive/ui/ui_state.py selfdrive/ui/mici/layouts/main.py`
- 로컬: `git diff --check -- selfdrive/ui/ui_state.py selfdrive/ui/mici/layouts/main.py`
- 기기: `/usr/local/venv/bin/python3 -m py_compile selfdrive/ui/ui_state.py`
- 기기 반영 후 UI 재시작.
- 재시작 후 확인: `UI_PID=54504`, `IsOffroad=1`, `IsOnroad=0`, `IsEngaged=0`
- 최신 error log는 여전히 `2026-05-11 13:01:18 KST`의 과거 로그이며 새 crash log는 증가하지 않았다.

## 2026-05-11 추가: C4/Mici offroad 문 열림 welcome wake

사용자 요청: `/Users/ijonghyeog/Desktop/frogpilot-testing-v1`의 `testing-v1-apn` 브랜치에 있던 “시동 OFF 상태에서 차량 문을 열면 openpilot 기기 화면이 켜지는 웰컴 기능”을 현재 StarPilot C4/Mici 기기에 적용.

참고 원본:

- `/Users/ijonghyeog/Desktop/frogpilot-testing-v1/frogpilot/system/offroad_wake_watcher.py`
- `/Users/ijonghyeog/Desktop/frogpilot-testing-v1/selfdrive/ui/ui.cc`의 `OffroadWakeCounter` 소비 로직

수정 파일:

- `starpilot/system/offroad_wake_watcher.py` 신규 추가
- `system/manager/process_config.py`
- `selfdrive/ui/ui_state.py`
- `common/params_keys.h`

구현 방식:

- `starpilot.system.offroad_wake_watcher`를 새로 추가했다.
- watcher는 `CarMake`가 GM 계열(`Buick`, `Cadillac`, `Chevrolet`, `Gmc`, `Holden`)일 때만 동작한다.
- 현재 기기 persistent params 확인 결과: `CarMake=Chevrolet`, `CarModel=CHEVROLET_TRAVERSE`.
- 시동이 꺼져 있고 `deviceState.started == False`, panda ignition이 꺼져 있을 때만 CAN을 감시한다.
- 감시 DBC/signals:
  - `gm_global_a_lowspeed_1818125`: `Door_Open_Switch_Status_LS`, `Door_Handle_Switch_Status_LS`
  - `gm_global_a_lowspeed`: `DriverDoorStatus`
  - `gm_global_a_powertrain_generated`: `BCMDoorBeltStatus`
- door/handle 신호가 active이거나, 감시 bus에서 짧은 CAN burst가 들어오면 `OffroadWakeCounter`를 증가시킨다.
- `selfdrive/ui/ui_state.py`의 Mici Python `Device._update_wakefulness()`가 `OffroadWakeCounter` 변화를 감지하면 `_reset_interactive_timeout()`을 호출해 꺼진 화면을 다시 켠다.
- 짧은 화면 탭 wake 보정(`ev.left_down or ev.left_pressed`)도 유지했다.

중요한 구현 메모:

- 현재 기기의 `common/params_pyx.so`는 새 `OffroadWakeCounter` key를 아직 모르는 상태라, live 적용은 `/dev/shm/params/d/OffroadWakeCounter` raw memory file fallback으로 동작하게 했다.
- `common/params_keys.h`에도 `OffroadWakeCounter`를 추가했지만, 완전한 빌드/재부팅 환경에서 정식 key로 쓰려면 params extension 재빌드가 필요할 수 있다.
- `system/manager/process_config.py`에 `PythonProcess("offroad_wake_watcher", "starpilot.system.offroad_wake_watcher", only_offroad, enabled=not PC)`를 추가했다. 다음 manager 재시작/재부팅부터는 offroad에서만 manager가 자동 실행하고, onroad 진입 시 manager가 종료한다.
- 이번 live 반영에서는 `systemctl restart comma.service`가 권한 문제(`Interactive authentication required`)로 실패했기 때문에, watcher를 수동 백그라운드 프로세스로 실행했다.
- 수동 실행 명령은 다음 형태였다.

```bash
cd /data/openpilot
PYTHONPATH=/data/openpilot/starpilot/third_party:/data/openpilot \
  nohup /usr/local/venv/bin/python3 -m starpilot.system.offroad_wake_watcher \
  >/tmp/offroad_wake_watcher.log 2>&1 &
```

주의: 수동 실행된 watcher는 현재 boot/session에서는 살아 있지만 manager-supervised 상태는 아니다. 재부팅 또는 manager 재시작 후에는 process_config 변경에 의해 manager가 실행해야 한다.

검증:

- 로컬: `python3 -m py_compile starpilot/system/offroad_wake_watcher.py selfdrive/ui/ui_state.py system/manager/process_config.py`
- 로컬: `git diff --check -- starpilot/system/offroad_wake_watcher.py selfdrive/ui/ui_state.py system/manager/process_config.py common/params_keys.h`
- 기기: `/usr/local/venv/bin/python3 -m py_compile starpilot/system/offroad_wake_watcher.py selfdrive/ui/ui_state.py system/manager/process_config.py`
- 기기 import 확인: `import starpilot.system.offroad_wake_watcher`
- raw memory counter 확인: `/dev/shm/params/d/OffroadWakeCounter`, 테스트로 `0 -> 1` 증가 성공.
- watcher 실행 확인: `PID=59006`, command `/usr/local/venv/bin/python3 -m starpilot.system.offroad_wake_watcher`
- Mici UI 재시작 확인: `UI_PID=59072`, 상태 `IsOffroad=1`, `IsOnroad=0`, `IsEngaged=0`
- 최신 error log는 여전히 `2026-05-11 13:01:18 KST`의 과거 로그이며 새 crash log는 증가하지 않았다.

## 2026-05-11 추가: Mici 화면 wake fade-in

사용자 요청: 화면이 꺼졌다가 켜질 때도 고급스럽게 fade-in으로 서서히 켜지게 변경.

수정 파일:

- `selfdrive/ui/mici/layouts/main.py`

구현 방식:

- Mici 메인 레이아웃에 `SCREEN_WAKE_FADE_DURATION = 0.85`초를 추가했다.
- offroad 상태에서 interaction timeout이 발생해 화면이 꺼질 때 `_screen_wake_fade_pending = True`로 표시한다.
- 다음에 터치 또는 offroad 문 열림 welcome wake 등으로 `device.awake`가 다시 true가 되고 렌더링이 재개되면 `_screen_wake_fade_start_time`을 잡는다.
- 이후 전체 화면 검은 오버레이 알파를 `1.0 -> 0.0`으로 smoothstep 곡선(`progress * progress * (3 - 2 * progress)`)으로 줄여서 화면이 부드럽게 드러나게 했다.
- 기존 offroad/onroad fade 전환과 겹칠 경우 `max(fade_alpha, wake_fade_alpha)`만 그려서 검은 오버레이가 중복으로 진해지지 않게 했다.

중요한 구현 메모:

- 처음에는 `selfdrive/ui/ui_state.py`의 `Device`에 새 메서드를 추가하는 방식으로 시도했지만, live manager 재시작 없이 UI 프로세스만 재시작하면 기존 Python module cache와 충돌해 `AttributeError: 'Device' object has no attribute 'wake_fade_alpha'` 크래시가 났다.
- 최종 구현은 `Device` 새 메서드에 의존하지 않고 Mici layout 내부 상태만 사용한다. 따라서 live UI 재시작만으로 적용 가능하다.
- 위 크래시 로그는 `/data/error_logs/2026-05-11--15-00-38.log`, `/data/error_logs/2026-05-11--15-00-50.log`, `/data/error_logs/2026-05-11--15-02-30.log`에 남아 있지만, 최종 패치 이후에는 같은 최신 로그가 증가하지 않고 UI가 정상 실행 중이다.

검증:

- 로컬: `python3 -m py_compile selfdrive/ui/ui_state.py selfdrive/ui/mici/layouts/main.py`
- 로컬: `git diff --check -- selfdrive/ui/ui_state.py selfdrive/ui/mici/layouts/main.py`
- 기기 확인: `/proc/device-tree/model = comma mici`, repo `/data/openpilot`, HEAD `2e7036ab`
- 기기: `/usr/local/venv/bin/python3 -m py_compile selfdrive/ui/ui_state.py selfdrive/ui/mici/layouts/main.py`
- 기기 코드 확인: `selfdrive/ui/mici/layouts/main.py`에 `SCREEN_WAKE_FADE_DURATION`, `_screen_wake_fade_alpha()`, `screen_fade_alpha` 반영 확인.
- Mici UI 재시작 확인: `UI_PID=63342`, 상태 `IsOffroad=1`, `IsOnroad=0`, `IsEngaged=0`
- offroad wake watcher 유지 확인: `PID=59006`, command `/usr/local/venv/bin/python3 -m starpilot.system.offroad_wake_watcher`

## 2026-05-11 추가: offroad wake watcher 실행 조건 최적화

사용자 요청: 차량 시동이 켜져 onroad로 들어가면 문 열림 감지 watcher가 꺼지고, offroad로 돌아오면 다시 켜지게 변경.

수정 파일:

- `system/manager/process_config.py`

구현 방식:

- `offroad_wake_watcher` manager 조건을 `always_run`에서 `only_offroad`로 변경했다.
- 이제 manager-supervised 상태에서는 `started == True`인 onroad 동안 watcher 프로세스가 종료되고, `started == False`인 offroad에서 다시 실행된다.
- 기능 자체는 기존처럼 GM 차량의 offroad 문/핸들 CAN 감지와 `OffroadWakeCounter` 증가 방식을 사용한다.

검증:

- 로컬: `python3 -m py_compile system/manager/process_config.py`
- 로컬: `git diff --check -- system/manager/process_config.py history.md`
- 기기(`/data/openpilot`): `/usr/local/venv/bin/python3 -m py_compile system/manager/process_config.py`
- 기기 조건 확인: `offroad_should_run=True`, `onroad_should_run=False`
- 기기 manager 재시작 후 `managerState` 확인: `offroad_wake_watcher=True`, `ui=True`, `pandad=True`, `hardwared=True`
- 기존 수동 실행 watcher는 `pkill -f "offroad_wake_watche[r]"`로 정리했고, 이후 PID `72105`가 manager 자식 프로세스(`PPID=72025`)로 실행되는 것을 확인했다.

## 2026-05-11 추가: 재부팅 후 한국어 폰트 깨짐 수정

문제:

- 재부팅/launch 이후 Mici 화면의 한국어 글자가 다시 깨졌다.
- 기기 `/data/openpilot/selfdrive/assets/fonts/`에는 `Pretendard-SemiBold.otf`만 남아 있고, raylib가 실제 렌더링에 쓰는 `Pretendard-SemiBold.fnt`, `Pretendard-SemiBold.png` atlas 파일이 없었다.
- 원인은 `selfdrive/assets/.gitignore`가 `fonts/*.fnt`, `fonts/*.png`를 무시하고 있어 Pretendard atlas 파일이 git 커밋에 포함되지 않은 상태였기 때문이다.

수정 파일:

- `selfdrive/assets/.gitignore`
- `selfdrive/assets/fonts/Pretendard-SemiBold.fnt`
- `selfdrive/assets/fonts/Pretendard-SemiBold.png`

구현 방식:

- `selfdrive/assets/.gitignore`에 `!fonts/Pretendard-SemiBold.fnt`, `!fonts/Pretendard-SemiBold.png` 예외를 추가했다.
- 로컬 git에 두 atlas 파일을 강제로 추가했다.
- 기기에도 두 파일을 다시 복사했다.
- Mici UI만 재시작해 새 폰트 atlas를 다시 로드하게 했다.

검증:

- 기기 `LanguageSetting=main_ko` 확인.
- 기기 `Pretendard-SemiBold.fnt/png/otf` 존재와 checksum 확인.
- 기기 Python import-resource 경로 확인: `/data/openpilot/openpilot/selfdrive/assets/fonts/Pretendard-SemiBold.fnt`, `.png`, `.otf` 모두 존재.
- 로컬/기기에서 `Pretendard-SemiBold.fnt`에 `안녕하세요`, `안전한 주행 되세요`, `신호가 초록불로 바뀌었습니다`, `앞차가 출발했습니다` 글리프가 모두 포함되어 있음을 확인했다.
- UI 재시작 후 `managerState` 기준 `ui=True` 확인.

## 2026-05-11 추가: Mici onroad 안전벨트 미착용 오버레이

사용자 요청: 안전벨트 미착용 시 onroad 화면 상단에 빨간색 그라데이션이 pulse되고, 화면 중앙에 `icons/seatbelt.png` 아이콘이 표시되게 변경.

수정 파일:

- `selfdrive/ui/mici/onroad/augmented_road_view.py`
- `selfdrive/assets/icons_mici/onroad/seatbelt.png`

구현 방식:

- 루트 `icons/seatbelt.png`를 Mici UI asset loader가 읽을 수 있도록 `selfdrive/assets/icons_mici/onroad/seatbelt.png`로 복사했다.
- `SeatbeltOverlay`를 추가해 `ui_state.sm["carState"].seatbeltUnlatched`가 true일 때만 표시한다.
- 상단에는 빨간색 solid band + vertical gradient를 그리고, alpha를 0.8초 주기로 pulse한다.
- 화면 중앙에는 seatbelt 아이콘을 표시하고, 가독성을 위해 약한 검은 radial shadow를 같이 그린다.
- reverse camera / driver camera stream에서는 표시하지 않고, 일반 road/wide onroad view에서만 표시한다.

검증:

- 로컬: `python3 -m py_compile selfdrive/ui/mici/onroad/augmented_road_view.py`
- 로컬: `git diff --check -- selfdrive/ui/mici/onroad/augmented_road_view.py selfdrive/assets/icons_mici/onroad/seatbelt.png`
- 로컬 프리뷰: `.codex_tmp/seatbelt_overlay_preview.py`로 Mici road 영역과 같은 비율에서 0.8초 pulse 표시 확인.
- 기기: `/usr/local/venv/bin/python3 -m py_compile selfdrive/ui/mici/onroad/augmented_road_view.py`
- 기기 코드 확인: `PULSE_PERIOD_SECONDS = 0.8`
- Mici UI 재시작 확인: `UI_PID=61369`, 적용 시점 `deviceState.started=False`

## 2026-05-11 추가: BSM 아이콘 pulse 조건 보정

사용자 요청: 사각지대 차량 감지 시에는 BSM 아이콘이 단순히 켜지고, 감지된 상태에서 같은 방향 방향지시등이 켜졌을 때만 빠르게 pulse되게 변경.

수정 파일:

- `selfdrive/ui/mici/onroad/blind_spot_indicators.py`

구현 방식:

- 기존 구현은 `carState.leftBlindspot` / `rightBlindspot`이 true이면 항상 `0.65`초 주기로 pulse했다.
- 변경 후 동작:
  - 왼쪽 BSM만 감지: 왼쪽 아이콘 alpha `1.0` 고정 표시
  - 오른쪽 BSM만 감지: 오른쪽 아이콘 alpha `1.0` 고정 표시
  - 왼쪽 BSM + 왼쪽 방향지시등: 왼쪽 아이콘 빠른 pulse
  - 오른쪽 BSM + 오른쪽 방향지시등: 오른쪽 아이콘 빠른 pulse
  - 반대 방향 방향지시등은 해당 BSM 아이콘 pulse 조건에 영향을 주지 않는다.
- 빠른 pulse 주기는 `BLIND_SPOT_FAST_PULSE_PERIOD = 0.32`초로 설정했다.
- fade-in/out 부드러움은 기존 `FirstOrderFilter(0, 0.06, 1 / gui_app.target_fps)`를 유지했다.

검증:

- 로컬: `python3 -m py_compile selfdrive/ui/mici/onroad/blind_spot_indicators.py`
- 기기: `/usr/local/venv/bin/python3 -m py_compile selfdrive/ui/mici/onroad/blind_spot_indicators.py`
- 기기 코드 확인: `BLIND_SPOT_FAST_PULSE_PERIOD`, `BLIND_SPOT_SOLID_ALPHA`, `car_state.leftBlinker`, `car_state.rightBlinker` 반영 확인.
- Mici UI 재시작 확인: `UI_PID=64883`, 상태 `IsOffroad=1`, `IsOnroad=0`, `IsEngaged=0`
- 최신 error log는 `/data/error_logs/2026-05-11--15-02-30.log` 그대로이며, 이번 재시작 후 새 로그는 생기지 않았다.

## 2026-05-11 확인: 전방 차량 출발 알림 / 초록불 알림

사용자 질문: 전방 차량 출발 알림과 신호 변경 알림이 구현되어 있는지 확인.

확인 파일:

- `starpilot/controls/lib/starpilot_events.py`
- `selfdrive/selfdrived/events.py`
- `selfdrive/selfdrived/selfdrived.py`
- `selfdrive/ui/ui_state.py`
- `selfdrive/ui/mici/onroad/circular_alerts.py`
- `selfdrive/ui/mici/onroad/alert_renderer.py`
- `selfdrive/ui/soundd.py`

구현 상태:

- 전방 차량 출발 알림은 구현되어 있다.
  - `starpilot/controls/lib/starpilot_events.py`에서 정차 중 앞차를 추적하고 있을 때 기준 거리보다 `1m` 이상 멀어지고 `vLead >= 1`이면 `StarPilotEventName.leadDeparting`을 발생시킨다.
  - `LeadDepartingAlert` 토글이 켜져 있을 때만 발생한다.
  - `selfdrive/selfdrived/events.py`의 한국어 문구는 `앞차가 출발했습니다`이다.
- 초록불/신호 변경 알림도 구현되어 있다.
  - 정차 중, 이전에 stop light로 멈춘 상태였고 모델이 더 이상 정지 상태가 아니라고 판단하면 `StarPilotEventName.greenLight`를 발생시킨다.
  - `GreenLightAlert` 토글이 켜져 있을 때만 발생한다.
  - `selfdrive/selfdrived/events.py`의 한국어 문구는 `신호가 초록불로 바뀌었습니다`이다.
- `selfdrive/selfdrived/selfdrived.py`는 `starpilotOnroadEvents`와 `starpilotSelfdriveState`를 publish한다.
- `selfdrive/ui/ui_state.py`는 Mici UI에서 `starpilotOnroadEvents`, `starpilotSelfdriveState`를 구독한다.
- `selfdrive/ui/mici/onroad/circular_alerts.py`는 `greenLight`, `leadDeparting` 이벤트를 보고 원형 알림을 3초간 표시한다.
  - 사용 이미지: `selfdrive/assets/images/green_light.png`, `selfdrive/assets/images/lead_depart.png`
- `selfdrive/ui/mici/onroad/alert_renderer.py`는 StarPilot alert가 일반 openpilot alert보다 우선 표시될 수 있도록 `starpilotSelfdriveState`를 읽는다.
- `selfdrive/ui/soundd.py`는 `starpilotSelfdriveState.alertSound`를 읽어서 StarPilot 알림 소리를 재생한다.

기기 확인:

- 기기 `/data/params/d` 기준:
  - `CustomAlerts=1`
  - `GreenLightAlert=1`
  - `LeadDepartingAlert=1`
- 기기 enum 확인:
  - `greenLight = 4`
  - `leadDeparting = 7`

주의:

- 초록불/신호 변경 알림은 실제 신호등 전용 센서가 아니라 openpilot E2E 모델 추정 기반이다. 따라서 실제 신호가 바뀌지 않았는데도 울릴 수 있다.

## 2026-05-11 추가: Mici offroad home 주행 종료 요약

사용자 요청: 주행 종료 후 offroad home 화면에 이번 주행 통계를 표시하고, 10분 뒤에는 기존 인사 문구로 되돌아가게 변경.

수정 파일:

- `selfdrive/ui/mici/layouts/home.py`
- `selfdrive/ui/mici/layouts/main.py`
- `selfdrive/assets/fonts/Pretendard-SemiBold.fnt`
- `selfdrive/assets/fonts/Pretendard-SemiBold.png`
- `.codex_tmp/home_summary_preview.py` (Mac 미리보기 전용, 기기 배포 대상 아님)

구현 방식:

- 실제 Mici/C4 UI 논리 해상도는 `536x240`이다.
  - 코드 기준: `system/ui/lib/application.py`의 작은 UI 기본값 `536x240`
  - 기기 확인: `/sys/class/drm/card0-DSI-1/modes = 240x536`, UI는 가로로 `536x240` 사용
- `selfdrive/ui/mici/layouts/main.py`에서 `ui_state.started` 동안 이번 주행 값을 직접 적산한다.
  - 거리: `carState.vEgoCluster`가 0이 아니면 우선 사용하고, 없으면 `carState.vEgo`를 사용한다.
  - 시간: onroad started 상태로 유지된 시간을 누적한다.
  - frame/tick 지연으로 값이 튀지 않도록 샘플 간격은 최대 `1.0`초로 제한한다.
- `started True -> False` 전환 시 `MiciHomeLayout.set_trip_summary(distance_m, duration_s)`로 이번 주행 요약을 넘긴다.
- `selfdrive/ui/mici/layouts/home.py`는 최근 주행 요약이 있으면 10분 동안 통계 화면을 표시한다.
  - 10분이 지나면 자동으로 기존 `안녕하세요!` / `안전한 주행 되세요` 화면으로 돌아간다.
- 상단 문구는 사용자 요청대로 `수고하셨습니다`로 변경했다.
- 중앙은 좌우 2열 구성:
  - 왼쪽: 실제 주행 거리 / `주행 거리`
  - 오른쪽: 실제 주행 시간 / `주행 시간`
- 하단 `주행 완료` 문구와 주행 거리/시간 아래 가로 바는 제거했다.
- `수고하셨습니다`의 `셨` 글자가 기존 Pretendard atlas에 없어서 `Pretendard-SemiBold.fnt/.png`에 해당 glyph를 추가했다.

검증:

- 로컬: `python3 -m py_compile selfdrive/ui/mici/layouts/home.py selfdrive/ui/mici/layouts/main.py`
- 로컬: `.venv/bin/python3 -m py_compile .codex_tmp/home_summary_preview.py`
- 로컬: `수고하셨습니다`, `안녕하세요!`, `안전한 주행 되세요`, `주행 거리`, `주행 시간` glyph 포함 확인.
- 기기: `/usr/local/venv/bin/python3 -m py_compile selfdrive/ui/mici/layouts/home.py selfdrive/ui/mici/layouts/main.py`
- 기기: 위 한글 문구 glyph 포함 확인.
- 기기 적용: `deviceState.started=False` 상태에서 파일 복사 후 Mici UI만 재시작, `UI_PID=70810`, `ui_running=True`

## 2026-05-11 추가: 기본 comma 부팅 로고 적용

사용자 요청: 부팅 시 표시되는 개구리 + `StarPilot` 로고를 기본 comma 로고로 변경.

확인한 파일/상태:

- 현재 개구리 로고 원본은 `starpilot/assets/other_images/starpilot_boot_logo.jpg`이다.
- 기기 실제 부팅 배경은 `/usr/comma/bg.jpg`이고, 기존 상태에서 위 StarPilot 로고와 md5가 동일했다.
- 기본 comma 로고 파일은 `starpilot/assets/other_images/stock_bg.jpg`이다.
- 기기 파라미터는 기존 `BootLogo=starpilot`이었다.

구현 방식:

- `starpilot/common/starpilot_functions.py`의 `update_boot_logo(starpilot=True, selected_logo=...)`에서 `selected_logo`가 `stock` 또는 `default`이면 `stock_bg.jpg`를 `/usr/comma/bg.jpg`로 복사하도록 수정했다.
- 기기 `/data/params/d/BootLogo`는 `stock`으로 설정했다.
- 단순히 `/usr/comma/bg.jpg`만 덮지 않고 부팅 함수도 고친 이유:
  - manager 부팅 시 `install_starpilot()`가 다시 `update_boot_logo(starpilot=True, selected_logo=params.get("BootLogo"))`를 호출한다.
  - 코드 수정 없이 파일만 덮으면 다음 부팅 때 StarPilot 기본 개구리 로고가 다시 적용될 수 있다.

## 2026-05-11 추가: Wayon / 웨이온 GitHub README 브랜딩

사용자 요청: openpilot 기반 커스텀 포크의 프로젝트명을 `Wayon / 웨이온`으로 정하고, GitHub 저장소용 README와 소개 문구를 이 브랜드 방향에 맞게 제작.

수정 파일:

- `README.md`

구현 방식:

- 기존 StarPilot 중심 README를 Wayon 브랜드 README로 교체했다.
- 상단 제목은 `# Wayon`, tagline은 `Your drive, always on.`으로 구성했다.
- `Way + On` 의미를 한국어로 설명했다.
- Wayon을 openpilot 기반 커스텀 주행 보조 포크로 명확히 설명했다.
- 완전 자율주행을 강조하지 않고, 운전자를 대체하지 않는 현실적인 운전 보조 파트너라는 톤으로 작성했다.
- 주요 컨셉, 기능 방향, 한국 사용자 고려 사항, 안전 고지, 책임 제한, attribution 섹션을 포함했다.
- 영어 프로젝트명 `Wayon`과 한국어 표기 `웨이온`을 함께 사용했다.

검증:

- `git diff --check -- README.md history.md`

## 2026-05-11 추가: onroad 진입 시 UI 크래시 루프 수정

사용자 보고: offroad 상태에서 시동을 걸어 onroad로 진입하면 화면이 꺼지는 듯하다가 comma 로고가 반복 표시되고, 시동을 끌 때까지 무한 재시작처럼 보임.

확인한 원인:

- 기기 IP: `10.52.51.173`
- 기기 모델: `comma mici`
- 최근 로그: `/data/error_logs/2026-05-11--20-06-22.log`
- traceback:
  - `selfdrive/ui/mici/onroad/augmented_road_view.py`
  - `SeatbeltOverlay.render()`
  - `_with_alpha(rl.WHITE, icon_alpha)`
  - `AttributeError: 'tuple' object has no attribute 'r'`
- `rl.WHITE`가 이 런타임에서는 `rl.Color` 객체가 아니라 tuple로 전달되어, 기존 `_with_alpha()`가 `color.r/color.g/color.b/color.a` 접근 중 크래시했다.
- 안전벨트 미착용 상태에서 onroad 진입하면 Seatbelt overlay가 표시되며 이 경로가 실행되어 UI가 반복 크래시했다. 사용자가 본 comma 로고 반복은 실제 전체 시스템 재부팅이라기보다 UI 크래시/재시작 루프에 가까웠다.

수정 파일:

- `selfdrive/ui/mici/onroad/augmented_road_view.py`

구현 방식:

- `SeatbeltOverlay._with_alpha()`가 `rl.Color` 객체와 `(r, g, b, a)` tuple/list를 모두 처리하도록 수정했다.
- alpha는 `0.0~1.0` 범위로 clamp한다.

검증:

- 로컬/기기 `py_compile`
- 기기에서 `SeatbeltOverlay._with_alpha(rl.WHITE, 0.5)` 호출 확인
- 결과: `with_alpha= 255 255 255 127`
- 기기 offroad 상태에서 Mici UI만 재시작, 새 UI PID `52763`

## 2026-05-11 추가: 안전벨트 아이콘 크기 70% 축소

사용자 요청: onroad 안전벨트 미착용 overlay의 중앙 seatbelt 아이콘이 너무 커서, 현재를 100%로 보면 약 70% 크기로 줄임.

수정 파일:

- `selfdrive/ui/mici/onroad/augmented_road_view.py`

구현 방식:

- `SeatbeltOverlay`의 seatbelt texture target size를 `170x252`에서 `119x176`으로 변경했다.
- pulse 주기 `0.8s`, 상단 빨간 gradient, 표시 조건은 유지했다.

기기 반영:

- 대상 IP: `192.168.0.5`
- 모델 확인: `comma mici`
- 적용 시점 상태: `deviceState.started=False`
- 기기 `py_compile` 통과
- Mici UI만 재시작, 새 UI PID `54212`

## 2026-05-11 추가: onroad -> offroad 전환도 동일 crossfade 적용

사용자 요청: offroad에서 onroad로 넘어갈 때 만든 전환처럼, onroad에서 offroad로 돌아갈 때도 같은 crossfade 느낌으로 전환되게 변경.

수정 파일:

- `selfdrive/ui/mici/layouts/main.py`

구현 방식:

- 기존 onroad -> offroad 전환은 `_start_transition(SURFACE_OFFROAD, fade_from_black=True)`를 사용해, onroad 화면에서 자연스럽게 이어지는 방식이 아니라 검은 화면에서 offroad가 나타나는 형태였다.
- 이를 `_start_transition(SURFACE_OFFROAD)`로 변경해 offroad -> onroad와 같은 전환 경로를 사용하게 했다.
- 주행 종료 통계 저장(`_finish_trip_tracking()`), offroad scroll 위치 동기화(`_sync_offroad_scroll()`), 10분 주행 요약 표시 로직은 유지했다.

검증:

- 로컬/기기 `py_compile`
- 대상 IP: `192.168.0.5`
- 모델 확인: `comma mici`
- 적용 시점 상태: `deviceState.started=False`
- 기기 offroad 상태에서 Mici UI만 재시작, 새 UI PID `55093`

## 2026-05-11 추가: 주행 종료 통계 표기와 `셨` 글리프 보정

사용자 요청:

- 주행 종료 통계 화면의 `수고하셨습니다`에서 `셨` 글자가 깨져 보임.
- 주행 시간이 60분 이상이면 `3시간 0분`처럼 시간/분으로 표시.
- 주행 거리 값은 `40.0 km`가 아니라 `40.0km`처럼 숫자와 단위 사이 공백 제거.

수정 파일:

- `selfdrive/ui/mici/layouts/home.py`
- `selfdrive/assets/fonts/Pretendard-SemiBold.fnt`
- `selfdrive/assets/fonts/Pretendard-SemiBold.png`

구현 방식:

- `MiciHomeLayout._distance_text()`를 `"{km:.1f}km"` 형식으로 변경했다.
- `MiciHomeLayout._duration_text()`에서 총 분이 60분 이상이면 `hours = minutes // 60`, `remaining_minutes = minutes % 60`로 나눠 `N시간 M분` 형식으로 표시한다.
- Pretendard atlas에서 `셨`(`char id=49512`)의 기존 좌표가 일부 문장부호 영역과 겹치는 것을 확인했다.
- `Pretendard-SemiBold.otf` 원본에서 `셨` 글리프만 다시 렌더링해 atlas의 빈 영역 `x=6, y=2762`에 배치하고 `.fnt` 좌표를 해당 위치로 갱신했다.
- 기존 한글 font weight 경로(`FontWeight.KOREAN = Pretendard-SemiBold.fnt`)는 유지했다.

기기 반영:

- 대상 IP: `192.168.0.5`
- 모델 확인: `comma mici`
- 적용 시점 상태: `deviceState.started=False`
- 기기 폰트 파일과 `home.py` MD5가 로컬과 일치함을 확인했다.
- 주행 요약 프리뷰용 임시 `home.py`를 한 번만 올려 `40000m, 10800s` 데모 값을 표시한 뒤, 디스크에는 정식 `home.py`를 다시 복원했다.
- 현재 실행 중인 UI 프로세스는 임시 프리뷰 데이터를 이미 소비했고, `/tmp/wayon_trip_summary_preview` 마커는 삭제된 상태다.

검증:

- 로컬 `python3 -m py_compile selfdrive/ui/mici/layouts/home.py`
- 로컬 font atlas 겹침 검사: `char id=49512`가 다른 glyph rectangle과 겹치지 않음
- 기기 `/usr/local/venv/bin/python3 -m py_compile selfdrive/ui/mici/layouts/home.py`
- 기기 UI PID 확인: `64184 selfdrive.ui.ui`

## 2026-05-11 추가: 주행 종료 통계 화면 레이아웃 정리

사용자 요청:

- 주행 거리/주행 시간 값 아래의 작은 `주행 거리`, `주행 시간` 캡션 제거.
- 상단 `수고하셨습니다` 글씨 크기 확대.
- `km` 값과 시간 값을 조금 아래로 이동.

수정 파일:

- `selfdrive/ui/mici/layouts/home.py`

구현 방식:

- `_distance_caption_label`, `_duration_caption_label` 생성과 render 호출을 제거했다.
- `수고하셨습니다` title font size를 `30`에서 `42`로 키웠다.
- title 영역 높이를 `38`에서 `56`으로 넓혔다.
- 거리/시간 값의 y 위치를 `self.rect.y + 84`에서 `self.rect.y + 104`로 내려, 제목과 값 사이 여백을 더 자연스럽게 만들었다.
- 중앙 divider는 값 영역에 맞춰 `self.rect.y + 98`, height `82`로 조정했다.

기기 반영:

- 대상 IP: `192.168.0.5`
- 모델 확인: `comma mici`
- 적용 시점 상태: `deviceState.started=False`
- `/data/openpilot`과 `/data/safe_staging/merged`의 `home.py`가 정식 파일로 복원되어 있고, 임시 프리뷰 marker는 소비 후 삭제됨.
- 프리뷰는 `40000m, 10800s` 데모 값으로 한 번 띄웠다.

검증:

- 로컬 `python3 -m py_compile selfdrive/ui/mici/layouts/home.py`
- 기기 `/usr/local/venv/bin/python3 -m py_compile /data/openpilot/selfdrive/ui/mici/layouts/home.py`
- 기기 `/usr/local/venv/bin/python3 -m py_compile /data/safe_staging/merged/selfdrive/ui/mici/layouts/home.py`
- 기기 UI PID 확인: `66004 selfdrive.ui.ui`

## 2026-05-11 추가: Mici offroad 화면 자동 꺼짐 5분 적용

사용자 요청:

- offroad 자동 화면 꺼짐 시간을 10분으로 바꾸려다가, 최종적으로 5분으로 변경 요청.

확인한 문제:

- `ScreenTimeout` param은 이미 초 단위 정수로 존재하며 기본값은 `30`초였다.
- Qt UI 경로는 `selfdrive/ui/ui.cc`에서 `ScreenTimeout`/`ScreenTimeoutOnroad`를 읽지만, 현재 C4/Mici Python UI 경로는 `selfdrive/ui/ui_state.py`의 `Device.interactive_timeout`에서 offroad timeout을 `30`초로 하드코딩하고 있었다.
- 따라서 param만 `300`으로 바꾸면 Galaxy/설정 값은 바뀌어도 Mici 실제 화면 꺼짐에는 반영되지 않을 수 있었다.

수정 파일:

- `selfdrive/ui/ui_state.py`
- `selfdrive/ui/layouts/settings/starpilot/system_settings.py`
- `starpilot/system/the_pond/assets/components/tools/device_settings_layout.json`
- `starpilot/ui/qt/offroad/device_settings.cc`

구현 방식:

- Mici `Device.interactive_timeout`이 `ui_state.params.get_int("ScreenTimeout")` 또는 onroad 시 `ScreenTimeoutOnroad`를 읽도록 변경했다.
- 값이 0 이하일 때만 기존 fallback을 사용한다.
- offroad screen timeout 설정 UI의 최대값을 `60`초에서 `300`초로 늘렸다.
- Galaxy/The Pond device settings layout에서도 `ScreenTimeout` 최대값을 `300`초로 늘렸다.
- Qt device settings의 offroad `ScreenTimeout` 최대값도 `300`초로 맞추고, onroad `ScreenTimeoutOnroad`는 기존 `60`초를 유지했다.

기기 반영:

- 대상 IP: `192.168.0.5`
- 모델 확인: `comma mici`
- 적용 시점 상태: `deviceState.started=False`
- 기기 param:
  - `ScreenTimeout=300`
  - `ScreenTimeoutOnroad=30`
  - `ScreenManagement=True`
- `/data/openpilot`과 `/data/safe_staging/merged`의 Mici UI 파일을 모두 갱신했다.
- Mici UI만 재시작, 새 UI PID `74483`

검증:

- 로컬 `python3 -m py_compile selfdrive/ui/ui_state.py selfdrive/ui/layouts/settings/starpilot/system_settings.py`
- 기기 `/usr/local/venv/bin/python3 -m py_compile selfdrive/ui/ui_state.py selfdrive/ui/layouts/settings/starpilot/system_settings.py`
- 기기 `/usr/local/venv/bin/python3 -m py_compile /data/safe_staging/merged/selfdrive/ui/ui_state.py /data/safe_staging/merged/selfdrive/ui/layouts/settings/starpilot/system_settings.py`
- `/data/openpilot/selfdrive/ui/ui_state.py`와 `/data/safe_staging/merged/selfdrive/ui/ui_state.py` MD5 일치 확인

## 2026-05-11 추가: Mici 화면 꺼짐 fade-out 적용

사용자 요청:

- 화면이 켜질 때 fade-in되는 것처럼, offroad 자동 화면 꺼짐 때도 fade-out으로 부드럽게 꺼지게 변경.

수정 파일:

- `selfdrive/ui/ui_state.py`
- `selfdrive/ui/mici/layouts/main.py`

구현 방식:

- `Device.delay_sleep_for(duration)`을 추가해, timeout 직후 display power를 즉시 끄지 않고 지정 시간 동안 렌더링을 유지할 수 있게 했다.
- `Device.timed_out` property를 추가해 Mici 레이아웃이 현재 timeout 상태인지 확인할 수 있게 했다.
- offroad timeout callback에서 `SCREEN_SLEEP_FADE_DURATION = 0.85`초 동안 sleep을 지연시키고, Mici main renderer가 검은 overlay를 `0 -> 100%`로 올려 fade-out을 그리도록 했다.
- 기존 화면 켜짐 fade-in(`SCREEN_WAKE_FADE_DURATION = 0.85`)은 유지하고, fade-in 시작 시 진행 중인 fade-out 상태를 정리한다.
- timeout 도중 터치/시동 등으로 interaction timer가 리셋되면 `device.timed_out`이 false가 되어 fade-out이 취소된다.

기기 반영:

- 대상 IP: `192.168.0.5`
- 모델 확인: `comma mici`
- 적용 시점 상태: `deviceState.started=False`
- `ScreenTimeout=300`, `ScreenTimeoutOnroad=30` 유지 확인.
- `/data/openpilot`과 `/data/safe_staging/merged`의 `ui_state.py`, `mici/layouts/main.py`를 모두 갱신했다.
- Mici UI만 재시작, 새 UI PID `75201`

검증:

- 로컬 `python3 -m py_compile selfdrive/ui/ui_state.py selfdrive/ui/mici/layouts/main.py`
- 기기 `/usr/local/venv/bin/python3 -m py_compile selfdrive/ui/ui_state.py selfdrive/ui/mici/layouts/main.py`
- 기기 `/usr/local/venv/bin/python3 -m py_compile /data/safe_staging/merged/selfdrive/ui/ui_state.py /data/safe_staging/merged/selfdrive/ui/mici/layouts/main.py`
- `/data/openpilot`과 `/data/safe_staging/merged`의 파일 MD5 일치 확인

## 2026-05-11 추가: Mici fade-out 후 UI 크래시 루프 안정화

사용자 보고:

- 화면이 꺼진 뒤 comma 로고가 반복 표시되며 혼자 재부팅하는 것처럼 보임.

확인한 원인:

- 실제 OS 재부팅은 아니었다. `uptime` 기준 기기는 계속 켜져 있었고, `ui` 프로세스가 반복 크래시/재시작하면서 comma 로고가 반복 표시됐다.
- `/data/error_logs/*.log`에 아래 traceback이 반복 기록됨:
  - `selfdrive/ui/mici/layouts/main.py`
  - `_on_interactive_timeout()`
  - `device.delay_sleep_for(SCREEN_SLEEP_FADE_DURATION)`
  - `AttributeError: 'Device' object has no attribute 'delay_sleep_for'`
- 기기 runtime import 경로가 `/data/openpilot/openpilot/...`와 `/data/openpilot/...` 양쪽을 사용하므로, fade-out 보조 메서드가 없는 stale `Device` 객체가 잡히는 순간 UI가 죽을 수 있었다.

수정 파일:

- `selfdrive/ui/mici/layouts/main.py`

구현 방식:

- `device.delay_sleep_for` 호출을 `getattr(device, "delay_sleep_for", None)`로 방어했다.
- `device.timed_out` 접근도 `getattr(device, "timed_out", True)`로 방어했다.
- 새 `Device` API가 있으면 기존처럼 sleep delay + fade-out을 사용하고, 없으면 기존 방식처럼 즉시 꺼지는 쪽으로 빠져 UI 크래시를 막는다.

기기 반영:

- 대상 IP: `192.168.0.5`
- `/data/openpilot/selfdrive/ui/mici/layouts/main.py`
- `/data/openpilot/openpilot/selfdrive/ui/mici/layouts/main.py`
- `/data/safe_staging/merged/selfdrive/ui/mici/layouts/main.py`
- `/data/safe_staging/merged/openpilot/selfdrive/ui/mici/layouts/main.py`
- 위 네 경로를 모두 같은 파일로 맞췄다.
- 관련 `__pycache__`를 삭제한 뒤 Mici UI만 재시작했다.
- display power와 screen brightness를 강제로 한 번 켰다.

검증:

- 로컬 `python3 -m py_compile selfdrive/ui/mici/layouts/main.py selfdrive/ui/ui_state.py`
- 기기 네 경로 `py_compile`
- Mici UI 새 PID `79419`
- 60초 이상 모니터링 중 PID가 유지됨.
- 최신 error log 이후 새 로그가 생성되지 않음.
