# CoDeSys 프로그래밍 가이드

## IEC 61131-3 언어

| 언어                   | 약어 | 용도                         |
| ---------------------- | ---- | ---------------------------- |
| Structured Text        | ST   | 연산·제어 알고리즘 (주 언어) |
| Ladder Diagram         | LD   | 릴레이 로직, 간단한 인터락   |
| Function Block Diagram | FBD  | 함수블록 연결, 신호 흐름     |

## POU 종류

| 종류             | 용도                         |
| ---------------- | ---------------------------- |
| `PROGRAM`        | 메인 사이클 로직             |
| `FUNCTION_BLOCK` | 재사용 가능한 상태 보유 로직 |
| `FUNCTION`       | 상태 없는 순수 연산          |

## 변수 선언 규칙

### 네이밍 컨벤션

| 접두사          | 범위              | 예시                          |
| --------------- | ----------------- | ----------------------------- |
| `G_`            | 글로벌 변수       | `G_SystemOk`, `G_ActiveError` |
| `G_AIBufferOf_` | AI 버퍼 인스턴스  | `G_AIBufferOf_SENSOR_MV`      |
| `G_DebounceDI_` | 디바운스 인스턴스 | `G_DebounceDI_SW_FOOT`        |
| `G_CAN1_`       | CAN1 글로벌       | `G_CAN1_CANopenDevice`        |

### 선언 위치

```pascal
VAR_GLOBAL                          (* Code_Template_globals *)
    G_SystemOk : BOOL := FALSE;
    G_ActiveError : BOOL;
END_VAR

VAR_GLOBAL CONSTANT
    G_MAX_NUMBER_OF_COBIDS : DWORD := 100;
END_VAR
```

## ST 기본 데이터 타입

| 타입    | 크기  | 범위         |
| ------- | ----- | ------------ |
| `BOOL`  | 1bit  | TRUE/FALSE   |
| `BYTE`  | 8bit  | 0~255        |
| `INT`   | 16bit | -32768~32767 |
| `UINT`  | 16bit | 0~65535      |
| `DINT`  | 32bit | -2^31~2^31-1 |
| `DWORD` | 32bit | 0~2^32-1     |
| `REAL`  | 32bit | 부동소수점   |

## ST 제어 구문

```pascal
IF G_SystemOk AND bValveActive THEN
    iCurrentmA := 150;
ELSIF NOT G_SystemOk THEN
    iCurrentmA := 0;
END_IF

CASE iState OF
    0: iState := 1;
    1: bValveActive := TRUE;
    ELSE iState := 0;
END_CASE

FOR i := 1 TO 10 DO arr[i] := 0; END_FOR
```

## EPEC 라이브러리 사용법

### ProportionalValveControl.lib

```pascal
fbValve(
    Enable           := G_SystemOk,
    CommandInput     := iJoystickPos,   (* -1000~+1000 *)
    PosDirMaxCurrent := 150,
    PosDirMinCurrent := 30,
    NegDirMaxCurrent := 150,
    NegDirMinCurrent := 30,
    AscendRamp       := 300,            (* ms *)
    DescendRamp      := 300
);
```

### JoystickCalibrationAndDiagnostic.lib

```pascal
fbJoystick(
    RawInput := wJoystickRaw,
    MaxPos   := 900, MidPos := 500, MinPos := 100  (* 0.1% *)
);
iPosition := fbJoystick.CalibratedOutput;  (* -1000~+1000 *)
```

### SensorCalibrationAndDiagnostic.lib

```pascal
fbSensor(
    RawInput            := wSensorRaw,
    HighSensorValue     := 450, LowSensorValue     := 50,   (* 0.01V *)
    HighCalibratedValue := 1800, LowCalibratedValue := -1800
);
iAngle := fbSensor.CalibratedOutput;
```

### Filters.lib

```pascal
fbDebounce(Input := bRawInput, OnDelay := 50, OffDelay := 50);
bFilteredInput := fbDebounce.Output;
```

### Ramp.lib

```pascal
fbRamp(Enable := TRUE, Target := iTargetCurrent, RampUp := 300, RampDown := 300);
iRampedOutput := fbRamp.Output;
```

### EventLog.lib

```pascal
IF G_ActiveError THEN
    fbEvent(Enable := TRUE, EventId := 16#1001, EventType := EVENT_TYPE_ERROR);
END_IF
```

## 초기화 패턴 (SFC CASE)

```pascal
CASE iInitStep OF
    0: IF G_InitEntryReady            THEN iInitStep := 1; END_IF
    1: IF G_InitFlashReady            THEN iInitStep := 2; END_IF
    2: IF G_InitIOReady               THEN iInitStep := 3; END_IF
    3: IF G_InitBusReady              THEN iInitStep := 4; END_IF
    4: IF G_InitProtocolsCan1Ready
          AND G_InitEventsReady       THEN G_SystemOk := TRUE; iInitStep := 5; END_IF
    5: RunApplication();
END_CASE
```

## AI 버퍼 처리

```pascal
(* 글로벌에서 자동 생성 — mode=7(FB) 핀만 *)
G_AIBufferOf_SENSOR_MV : IO_SET_AI_BUFFER;
wSensorRaw := G_AIBufferOf_SENSOR_MV.FilteredValue;
```

## 코드 품질 규칙

- 변수명: 영어 카멜케이스 (`bValveEnable`, `iCurrentmA`)
- 매직 넘버 대신 상수·파라미터 변수 사용
- FB는 Enable 입력으로 활성화 제어
- `SW_EMERGENCY` 안전 로직 최우선 처리
- 시스템 활성화 조건은 `G_SystemOk` AND 결합
