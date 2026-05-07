"""session.py — MultiTool 인스턴스/상태 추적 + function_map 항목 실행

Session.start(version, project=None)
Session.execute(orig_name, info, params)
Session.close()

조작 우선순위 (MultiToolScan 규약):
  1) shortcut + shortcut_verified=True
  2) menu_path UIA 탐색
  3) coordinates 좌표 클릭

device_config 다이얼로그(`DeviceConfigureView`) 항목은 메뉴 호출 후 inputs를
params로 채운다. 본 v1은 `Configure: CAN`의 Bit Rate / Enabled 만 실제 처리하고,
나머지는 호출만 수행한 채 결과를 보고한다(차후 매핑 보강 대상).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent.parent

DANGEROUS = {"Alt + F4"}


def decide_method(info: dict) -> tuple[str, str]:
    """function_map 항목 → (method, detail). 실제 조작 없이 우선순위만 결정.

    method ∈ {"shortcut", "menu", "coords", "shortcut_unverified", "none"}.
    실 dispatch와 dry-run에서 동일하게 사용.
    """
    sc       = info.get("shortcut") or ""
    verified = info.get("shortcut_verified", False)
    if sc and verified and sc not in DANGEROUS:
        return "shortcut", sc
    if info.get("menu_path"):
        return "menu", " > ".join(info["menu_path"])
    coords = info.get("coordinates") or []
    if len(coords) == 2:
        return "coords", f"{coords[0]},{coords[1]}"
    if sc and sc not in DANGEROUS:
        return "shortcut_unverified", sc
    return "none", ""


def _to_keys(sc: str) -> str:
    """'Ctrl + Shift + N' → '^+n' (pywinauto.keyboard syntax). fnscan/verify.py와 동일."""
    parts = [p.strip() for p in sc.split("+")]
    mods  = {"Ctrl": "^", "Shift": "+", "Alt": "%"}
    out   = ""
    for p in parts:
        if p in mods:
            out += mods[p]
        elif p.upper().startswith("F") and p[1:].isdigit():
            out += "{" + p.upper() + "}"
        else:
            out += p.lower()
    return out


def _wait_main(app, timeout: float = 60):
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(2)
        try:
            for w in app.windows():
                name = w.element_info.name or ""
                if name and "DynamicSplashScreen" not in name \
                        and ("MultiTool" in name or "Creator" in name):
                    time.sleep(2)
                    return w
        except Exception:
            pass
    return app.top_window()


class Session:
    def __init__(self, version: str = "8.4"):
        self.version = version
        self.app     = None
        self.win     = None
        self.project: Path | None = None
        self.log: list[dict] = []

    def start(self, project: str | Path | None = None):
        from pywinauto import Application, keyboard  # lazy
        exe = rf"C:\Program Files (x86)\Epec\MultiTool Creator {self.version}\MultiTool.exe"
        if not Path(exe).exists():
            raise FileNotFoundError(exe)
        self.app = Application(backend="uia").start(exe)
        self.win = _wait_main(self.app)
        if project:
            self.open_project(project)

    def open_project(self, project: str | Path):
        from pywinauto import keyboard
        p = Path(project).resolve()
        if not p.exists():
            raise FileNotFoundError(p)
        self.win.set_focus(); time.sleep(0.5)
        keyboard.send_keys("^+o", pause=0.05); time.sleep(2)
        keyboard.send_keys(str(p), pause=0.01, with_spaces=True); time.sleep(0.3)
        keyboard.send_keys("{ENTER}"); time.sleep(8)
        self.project = p
        self.log.append({"action": "open_project", "path": str(p)})

    def close(self):
        if not self.app:
            return
        try:
            self.app.kill()
        except Exception:
            pass
        self.app = self.win = None

    def execute(self, name: str, info: dict, params: dict[str, Any]) -> dict:
        """function_map 항목 실행. 우선순위에 따라 단축키 → 메뉴 → 좌표 폴백."""
        from pywinauto import keyboard
        if not self.win:
            raise RuntimeError("session not started")
        self.win.set_focus(); time.sleep(0.3)

        method, detail = self._dispatch(name, info)
        entry = {
            "function": name,
            "method":   method,
            "detail":   detail,
            "params":   params,
            "dialog":   info.get("dialog", "none"),
        }

        if info.get("dialog") and info["dialog"] != "none":
            time.sleep(1.0)
            entry["dialog_active"] = self._is_dialog_visible(info["dialog"])
            self._fill_dialog(info, params, entry)

        self.log.append(entry)
        return entry

    def _dispatch(self, name: str, info: dict) -> tuple[str, str]:
        from pywinauto import keyboard, mouse
        method, detail = decide_method(info)
        if method == "shortcut" or method == "shortcut_unverified":
            keyboard.send_keys(_to_keys(detail), pause=0.05)
            return method, detail
        if method == "menu" and self._try_menu(info["menu_path"]):
            return "menu", detail
        if method == "coords":
            c = info["coordinates"]
            mouse.click(coords=(c[0], c[1]))
            return "coords", detail
        raise RuntimeError(f"no executable path for {name}")

    def _try_menu(self, path: list[str]) -> bool:
        try:
            top = self.win.descendants(control_type="MenuItem")
        except Exception:
            return False
        for label in path:
            target = next((c for c in top if (c.element_info.name or "").strip() == label), None)
            if not target:
                return False
            try:
                target.invoke()
            except Exception:
                try:
                    target.click_input()
                except Exception:
                    return False
            time.sleep(0.4)
            try:
                top = self.win.descendants(control_type="MenuItem")
            except Exception:
                top = []
        return True

    # ───── XML 패치 tools (mtpatch 위임, GUI 우회) ─────
    def _require_project(self):
        if not self.project:
            raise RuntimeError("session.project 미설정 — --project로 시작하거나 open_project 후 사용")
        return self.project

    def _mtpatch(self):
        import importlib.util
        mod_path = Path(__file__).parent.parent / "mtpatch" / "run.py"
        spec = importlib.util.spec_from_file_location("mtpatch_run", mod_path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def xml_set_bitrate(self, can_number: int, bitrate: int) -> dict:
        rc = self._mtpatch().cmd_set_bitrate(self._require_project(), can_number, bitrate)
        entry = {"action": "xml_set_bitrate", "can_number": can_number,
                 "bitrate": bitrate, "rc": rc}
        self.log.append(entry)
        return entry

    def xml_set_buffering(self, can_number: int, enabled: bool) -> dict:
        rc = self._mtpatch().cmd_set_buffering(self._require_project(), can_number, enabled)
        entry = {"action": "xml_set_buffering", "can_number": can_number,
                 "enabled": enabled, "rc": rc}
        self.log.append(entry)
        return entry

    def xml_set_j1939(self, can_number: int, enabled: bool) -> dict:
        rc = self._mtpatch().cmd_set_j1939(self._require_project(), can_number, enabled)
        entry = {"action": "xml_set_j1939", "can_number": can_number,
                 "enabled": enabled, "rc": rc}
        self.log.append(entry)
        return entry

    def xml_show(self) -> dict:
        state = self._mtpatch().read_state(self._require_project())
        entry = {"action": "xml_show", **state}
        self.log.append(entry)
        return entry

    # ───── 보조 UI tools (LLM 노출용) ─────
    def aux_type_text(self, text: str) -> dict:
        from pywinauto import keyboard
        if not self.win:
            raise RuntimeError("session not started")
        keyboard.send_keys(text, with_spaces=True, pause=0.01)
        entry = {"action": "type_text", "text": text}
        self.log.append(entry)
        return entry

    def aux_press_key(self, key: str) -> dict:
        from pywinauto import keyboard
        if not self.win:
            raise RuntimeError("session not started")
        keymap = {"enter": "{ENTER}", "escape": "{ESC}", "tab": "{TAB}",
                  "space": " ",       "backspace": "{BACKSPACE}"}
        if key not in keymap:
            raise ValueError(f"unsupported key: {key}")
        keyboard.send_keys(keymap[key])
        entry = {"action": "press_key", "key": key}
        self.log.append(entry)
        return entry

    def aux_wait(self, seconds: float) -> dict:
        s = max(0.0, min(float(seconds), 30.0))   # 0~30초 클램프
        time.sleep(s)
        entry = {"action": "wait", "seconds": s}
        self.log.append(entry)
        return entry

    def _is_dialog_visible(self, dialog_id: str) -> bool:
        try:
            for c in self.win.descendants():
                ai = c.element_info.automation_id or c.element_info.class_name or ""
                if ai == dialog_id:
                    return True
        except Exception:
            pass
        return False

    def _fill_dialog(self, info: dict, params: dict, entry: dict):
        """v1: Bit Rate(ComboBox), Enabled(CheckBox) 등 일부 입력만 처리.

        params 키는 input의 정규화 이름(예: bit_rate, enabled, combobox_1)."""
        from pywinauto import keyboard
        applied = []
        for inp in info.get("inputs", []):
            nm = (inp.get("name") or "").strip()
            if not nm:
                continue
            key = nm.lower().replace(" ", "_").replace("/", "_")
            if key not in params:
                continue
            val = params[key]
            ty  = inp.get("type")
            try:
                ctrl = self.win.child_window(title=nm, control_type=ty)
                if ty == "CheckBox":
                    cur = ctrl.get_toggle_state() == 1
                    if cur != bool(val):
                        ctrl.toggle()
                elif ty == "ComboBox":
                    ctrl.select(str(val))
                elif ty == "Edit":
                    ctrl.set_edit_text(str(val))
                applied.append({"name": nm, "type": ty, "value": val})
            except Exception as e:
                applied.append({"name": nm, "type": ty, "value": val, "error": str(e)})
        entry["applied_inputs"] = applied


if __name__ == "__main__":
    import sys, json
    sys.stdout.reconfigure(encoding="utf-8")
    print("Session module — import-only smoke test")
    s = Session()
    print("instance:", s.version, "project:", s.project)
