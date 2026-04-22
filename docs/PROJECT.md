# 프로젝트 상세 문서

## 프로젝트 정보

| 항목     | 내용                         |
|---------|------------------------------|
| 프로젝트 | DasDemoProject               |
| 컨트롤러 | EPEC CU-3606-21              |
| 개발환경 | EPEC MultiTool + CoDeSys 2.3 |
| 언어     | IEC 61131-3 (ST, LD, FBD)    |
| 통신     | CANopen (CAN1), J1939 (CAN2) |

## 핵심 기능

| 기능      | 파라미터 그룹   | 설명                        |
|----------|---------------|-----------------------------|
| 조이스틱  | `UpDnJoystick`  | 업/다운 방향 신호 처리      |
| 비례밸브  | `UpDnPairValve` | 전류 기반 PWM 출력          |
| 각도 센서 | `AngleSensor`   | 아날로그 센서 보정·진단     |
| 조절 제어 | `Regulation`    | 위치/압력 피드백 제어       |

## 하드웨어 I/O (CU_3606_21)

| 핀    | 기능                  | 변수명               |
|------|-----------------------|----------------------|
| 1.14 | DI — 풋 스위치        | `SW_FOOT`            |
| 1.15 | DI — 비상 정지        | `SW_EMERGENCY`       |
| 1.20 | AI — 조이스틱 전압    | `JOYSTICK_MV`        |
| 1.21 | AI — 각도 센서 전압   | `SENSOR_MV`          |
| 1.22 | AI — 밸브 전류 피드백 | `VALVE_UPDN_CURRENT` |

**내부 측정값**

| 변수             | 정상 범위                             |
|----------------|---------------------------------------|
| `SupplyVolt`     | 900~3300 (0.01V, 즉 9~33V)          |
| `PcbTemperature` | -400~1050 (0.1°C, 즉 -40~105°C)     |
| `Ref5V`          | 450~550 (0.01V)                      |
| `Ref2_5V`        | 200~300 (0.01V)                      |

## 초기화 순서

| 단계 | 플래그                      |
|-----|------------------------------|
| 1   | `G_InitEntryReady`           |
| 2   | `G_InitFlashReady`           |
| 3   | `G_InitIOReady`              |
| 4   | `G_InitBusReady`             |
| 5   | `G_InitProtocolsCan1Ready`   |
| 6   | `G_InitProtocolsCan2Ready`   |
| 7   | `G_InitEventsReady`          |
| 8   | `G_InitExitReady`            |

## CANopen OD 구성

| OD 인덱스 | 파라미터 그룹   | 내용                     |
|----------|----------------|--------------------------|
| `0x2200` | UpDnJoystick   | 조이스틱 위치 설정       |
| `0x2201` | AngleSensor    | 각도 센서 보정·진단 설정 |
| `0x2202` | UpDnPairValve  | 비례밸브 전류·램프 설정  |

**PDO (CAN1)**: TPDO 2개 (송신), RPDO 1개 (수신)

## 파라미터 상세

### UpDnJoystick

| 파라미터    | 기본값 | 범위   | 단위 |
|------------|-------|--------|------|
| MaxPosition |   900 | 0~1000 | 0.1% |
| MidPosition |   500 | 0~1000 | 0.1% |

### UpDnPairValve

| 파라미터          | 기본값 | 범위   | 단위 |
|------------------|-------|--------|------|
| PosDirMaxCurrent  |   150 | 0~1000 | mA   |
| PosDirMinCurrent  |    30 | 0~1000 | mA   |
| NegDirMaxCurrent  |   150 | 0~1000 | mA   |
| NegDirMinCurrent  |    30 | 0~1000 | mA   |
| PosDirAscendRamp  |   300 | 0~1000 | ms   |
| PosDirDescendRamp |   300 | 0~1000 | ms   |
| NegDirAscendRamp  |   300 | 0~1000 | ms   |
| NegDirDescendRamp |   300 | 0~1000 | ms   |

### AngleSensor

| 파라미터                  | 기본값 | 범위          | 단위  |
|--------------------------|-------|---------------|-------|
| HighSensorValue           |   450 | 0~1000        | 0.01V |
| LowSensorValue            |    50 | 0~1000        | 0.01V |
| HighCalibratedValue       |  1800 | -32768~32767  | —     |
| LowCalibratedValue        | -1800 | -32768~32767  | —     |
| SensorValueErrorLimitHigh |   480 | 0~1000        | 0.01V |
| SensorValueErrorLimitLow  |    20 | 0~1000        | 0.01V |

## 라이브러리 버전

| 라이브러리                           | 버전  | 용도                       |
|-------------------------------------|-------|----------------------------|
| 3606int.lib                          | 1.6.2 | CU-3606 내부 I/O           |
| CANopen.lib                          | 1.6.7 | CANopen 프로토콜           |
| J1939.lib                            | 1.3.5 | J1939 프로토콜             |
| ProportionalValveControl.lib         | 1.0.7 | 비례밸브 제어 FB           |
| JoystickCalibrationAndDiagnostic.lib | 1.3.1 | 조이스틱 보정·진단         |
| SensorCalibrationAndDiagnostic.lib   | 1.0.2 | 센서 보정·진단             |
| EventLog.lib                         | 1.4.3 | 이벤트 로그                |
| NetworkManager.lib                   | 1.3.0 | CAN 네트워크 관리          |
| Filters.lib                          | 1.0.2 | 신호 필터링                |
| Ramp.lib                             | 1.1.0 | 램프 함수                  |
| FileSys.lib                          | 1.3.0 | 파일시스템 (파라미터 저장) |

## 파일 형식

| 확장자       | 설명                                  |
|-------------|---------------------------------------|
| `.mtproject` | EPEC MultiTool 프로젝트 (XML)         |
| `.pro`       | CoDeSys 2.3 프로젝트 — **편집 금지** |
| `.exp`       | CoDeSys 변수·POU 익스포트 (텍스트)   |
| `.csf`       | CAN 네트워크 설정                     |
| `.dbc`       | CAN 데이터베이스 (Vector 형식)        |
| `.csv`       | 파라미터·이벤트 정의                  |
| `.HEX/.BIN`  | 빌드 결과물                           |
| `.lib`       | CoDeSys 라이브러리                    |

## 주의사항

| 대상                      | 주의사항                                     |
|--------------------------|----------------------------------------------|
| `.pro`                    | 직접 편집 금지 — CoDeSys IDE 전용            |
| `Parameters_NETWORK1.csv` | 편집 후 MultiTool에서 임포트 필요            |
| `.HEX/.BIN`               | MultiTool Download로 컨트롤러에 전송         |
| 핀 표기                   | `번호.핀명` — 예: `1.20 AI JOYSTICK_MV`     |
| OD 인덱스                 | 항상 16진수 — 예: `0x2201`                   |
