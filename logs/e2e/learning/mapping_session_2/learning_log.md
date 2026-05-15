# UI→XML 매핑 학습 — 세션 mapping_session_2

시작: 2026-05-15T11:30:32 · step 수: 4 (baseline 제외)

## Step 요약

| #   | 설명                                 | mtproject Δ size | value changes | guid_regen | exp changed |
| --- | ------------------------------------ | ---------------- | ------------- | ---------- | ----------- |
| 1   | delete monitor 6807-220 CU4          | -198067          | 1             | 29         | 0           |
| 2   | delete NETWORK3 (1 member left)      | -705             | 3             | 4          | 4           |
| 3   | delete NETWORK2 (2 members active)   | -2223            | 4             | 9          | 4           |
| 4   | delete NETWORK1 + standalone 3724-01 | -72911           | 3             | 84         | 3           |

## Step별 상세

### Step 1: delete monitor 6807-220 CU4

**value 변경**:

| tag             | old      | new      |
| --------------- | -------- | -------- |
| `SystemVersion` | `1.0.13` | `1.0.14` |

**신규 요소** (top 5): Meta

**제거 요소** (top 5): Monitoring, TargetCanOpen, CAN, Device, Text, TargetDevice, AzureDevice, Meta, EditorNodes, Appearance, Node, DeviceTemplate, Color

기타: guid_regen=29, bom_or_decl=0, raw_added=2, raw_removed=4660

### Step 2: delete NETWORK3 (1 member left)

**value 변경**:

| tag             | old         | new         |
| --------------- | ----------- | ----------- |
| `SystemVersion` | `1.0.14`    | `1.0.15`    |
| `Color`         | `#FF003882` | `#FFEDEEEE` |
| `Color`         | `#FF003882` | `#FFEDEEEE` |

**신규 요소** (top 5): Meta

**제거 요소** (top 5): CAN, Text, Data, Meta, Network, Name, Bitrate, Appearance, ParameterFileTargetPath, Node

기타: guid_regen=4, bom_or_decl=0, raw_added=3, raw_removed=20

**exp 영향**:

- [changed] `EPEC_CU1.exp` size_delta=0
- [changed] `EPEC_CU2.exp` size_delta=0
- [changed] `EPEC_CU3.exp` size_delta=0
- [changed] `EPEC_CU5.exp` size_delta=0

### Step 3: delete NETWORK2 (2 members active)

**value 변경**:

| tag             | old         | new         |
| --------------- | ----------- | ----------- |
| `SystemVersion` | `1.0.15`    | `1.0.17`    |
| `Color`         | `#FF007CC2` | `#FFEDEEEE` |
| `Color`         | `#FF007CC2` | `#FFEDEEEE` |
| `Color`         | `#FF007CC2` | `#FFEDEEEE` |

**신규 요소** (top 5): Meta

**제거 요소** (top 5): Monitoring, TargetCanOpen, CAN, Text, TargetDevice, Data, Meta, Network, Monitors, Name, Bitrate, Appearance, ParameterFileTargetPath, Node

기타: guid_regen=9, bom_or_decl=0, raw_added=4, raw_removed=52

**exp 영향**:

- [changed] `EPEC_CU1.exp` size_delta=0
- [changed] `EPEC_CU2.exp` size_delta=-719
- [changed] `EPEC_CU3.exp` size_delta=0
- [changed] `EPEC_CU5.exp` size_delta=0

### Step 4: delete NETWORK1 + standalone 3724-01

**value 변경**:

| tag     | old         | new         |
| ------- | ----------- | ----------- |
| `Color` | `#FF33CCFF` | `#FFEDEEEE` |
| `Color` | `#FF33CCFF` | `#FFEDEEEE` |
| `Color` | `#FF33CCFF` | `#FFEDEEEE` |

**신규 요소** (top 5): Monitorings, Meta, Networks

**제거 요소** (top 5): Monitoring, TargetCanOpen, CAN, Networks, Device, NetworkMappings, TargetDevice, Meta, Network, Name, Monitorings, Bitrate, DeviceTemplate

기타: guid_regen=84, bom_or_decl=0, raw_added=6, raw_removed=1827

**exp 영향**:

- [changed] `EPEC_CU1.exp` size_delta=-719
- [changed] `EPEC_CU2.exp` size_delta=0
- [changed] `EPEC_CU3.exp` size_delta=-503
