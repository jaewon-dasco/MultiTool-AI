#!/usr/bin/env python3
"""UI→XML mapping learning: snapshot .mtproject + .exp before/after each user UI action, produce step diffs."""
import sys, json, hashlib, shutil, re, difflib, datetime, glob
from pathlib import Path

ROOT = Path(r"d:\4_AIProject\4_CoDeSys\AI_MutiTool")
PROJ_DIR = ROOT / "MultiToolProject" / "E2EProject"
PROJ_FILE = PROJ_DIR / "DasDemoProject.mtproject"
LEARN_ROOT = ROOT / "logs" / "e2e" / "learning"

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now(): return datetime.datetime.now().isoformat(timespec="seconds")

def gather_exp_files():
    """All .exp files under E2EProject (in any subfolder)."""
    return sorted(str(p) for p in PROJ_DIR.rglob("*.exp"))

def snapshot(step_dir: Path, label: str):
    step_dir.mkdir(parents=True, exist_ok=True)
    info = {"label": label, "ts": now(), "mtproject": None, "exp": []}
    # mtproject
    dst = step_dir / f"{label}_mtproject_DasDemoProject.mtproject"
    if PROJ_FILE.exists():
        shutil.copy(PROJ_FILE, dst)
        info["mtproject"] = {"src": str(PROJ_FILE), "dst": str(dst), "sha": sha(dst), "size": dst.stat().st_size}
    # exp files
    for exp in gather_exp_files():
        p = Path(exp)
        dst = step_dir / f"{label}_exp_{p.parent.name}_{p.name}"
        shutil.copy(p, dst)
        info["exp"].append({"src": exp, "dst": str(dst), "sha": sha(dst), "size": dst.stat().st_size})
    return info

def xml_changes(before_path, after_path):
    """Categorize line-level diff into intent vs side-effect heuristics."""
    if not before_path or not after_path: return None
    b = Path(before_path).read_text(encoding="utf-8", errors="replace").splitlines()
    a = Path(after_path).read_text(encoding="utf-8", errors="replace").splitlines()
    diff = list(difflib.unified_diff(b, a, n=0, lineterm=""))
    added = [ln[1:] for ln in diff if ln.startswith("+") and not ln.startswith("+++")]
    removed = [ln[1:] for ln in diff if ln.startswith("-") and not ln.startswith("---")]
    # Heuristics
    guid_re = re.compile(r'Guid="[0-9a-f-]{36}"')
    value_re = re.compile(r"<(\w+)>([^<>]+)</\1>")
    cats = {"value_changes": [], "guid_regen": 0, "bom_or_decl": 0, "new_elements": [], "removed_elements": [], "raw_added": len(added), "raw_removed": len(removed)}
    # paired removed/added lines: detect value changes
    for r_line in removed:
        if guid_re.search(r_line): cats["guid_regen"] += 1
        if "?xml" in r_line or "﻿" in r_line: cats["bom_or_decl"] += 1
        m = value_re.search(r_line)
        if m and not guid_re.search(r_line):
            # see if a corresponding added line has same tag
            for a_line in added:
                m2 = value_re.search(a_line)
                if m2 and m.group(1) == m2.group(1) and m.group(2) != m2.group(2):
                    cats["value_changes"].append({"tag": m.group(1), "old": m.group(2), "new": m2.group(2)})
                    break
    # New tag elements
    for a_line in added:
        m = re.search(r"<(\w+)\b", a_line)
        if m and not any(m.group(1) == c.get("tag") for c in cats["value_changes"]):
            cats["new_elements"].append({"tag": m.group(1), "line": a_line[:200]})
    for r_line in removed:
        m = re.search(r"<(\w+)\b", r_line)
        if m and not any(m.group(1) == c.get("tag") for c in cats["value_changes"]):
            cats["removed_elements"].append({"tag": m.group(1), "line": r_line[:200]})
    return cats

def diff_step(prev_info, curr_info):
    out = {"mtproject": None, "exp": []}
    if prev_info.get("mtproject") and curr_info.get("mtproject"):
        b, a = prev_info["mtproject"]["dst"], curr_info["mtproject"]["dst"]
        if prev_info["mtproject"]["sha"] != curr_info["mtproject"]["sha"]:
            out["mtproject"] = {"sha_before": prev_info["mtproject"]["sha"][:16], "sha_after": curr_info["mtproject"]["sha"][:16],
                                "size_delta": curr_info["mtproject"]["size"] - prev_info["mtproject"]["size"],
                                "changes": xml_changes(b, a)}
    # exp files keyed by basename of original src
    prev_exp = {Path(e["src"]).name: e for e in prev_info.get("exp", [])}
    curr_exp = {Path(e["src"]).name: e for e in curr_info.get("exp", [])}
    for name in sorted(set(prev_exp) | set(curr_exp)):
        if name not in prev_exp:
            out["exp"].append({"name": name, "status": "added", "size": curr_exp[name]["size"]})
        elif name not in curr_exp:
            out["exp"].append({"name": name, "status": "removed"})
        elif prev_exp[name]["sha"] != curr_exp[name]["sha"]:
            ch = xml_changes(prev_exp[name]["dst"], curr_exp[name]["dst"])
            out["exp"].append({"name": name, "status": "changed", "size_delta": curr_exp[name]["size"] - prev_exp[name]["size"], "changes": ch})
    return out

def load_state(session_dir):
    sp = session_dir / "state.json"
    return json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else None

def save_state(session_dir, state):
    (session_dir / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def cmd_init(name):
    session_dir = LEARN_ROOT / name
    if session_dir.exists() and (session_dir / "state.json").exists():
        print(f"Session '{name}' already exists. Delete first or use different name."); sys.exit(1)
    session_dir.mkdir(parents=True, exist_ok=True)
    baseline = snapshot(session_dir / "step00_baseline", "step00_baseline")
    state = {"session": name, "started": now(), "steps": [{"i": 0, "label": "baseline", "info": baseline, "diff": None}]}
    save_state(session_dir, state)
    print(f"INIT session={name}")
    print(f"  baseline mtproject sha={baseline['mtproject']['sha'][:16] if baseline['mtproject'] else 'N/A'} size={baseline['mtproject']['size'] if baseline['mtproject'] else 0}")
    print(f"  baseline exp files: {len(baseline['exp'])}")
    print(f"  dir: {session_dir}")

def cmd_capture(name, description):
    session_dir = LEARN_ROOT / name
    state = load_state(session_dir)
    if not state: print(f"FAIL: session '{name}' not initialized"); sys.exit(1)
    i = len(state["steps"])
    label = f"step{i:02d}_{re.sub(r'[^A-Za-z0-9_-]+', '_', description)[:40]}"
    info = snapshot(session_dir / label, label)
    prev = state["steps"][-1]["info"]
    diff = diff_step(prev, info)
    state["steps"].append({"i": i, "label": label, "description": description, "info": info, "diff": diff, "ts": now()})
    save_state(session_dir, state)
    # Print summary
    print(f"CAPTURE step={i:02d} '{description}'")
    if diff["mtproject"]:
        m = diff["mtproject"]; c = m["changes"]
        print(f"  mtproject: {m['sha_before']} -> {m['sha_after']} size_delta={m['size_delta']:+d}")
        if c:
            if c["value_changes"]:
                print(f"    value changes ({len(c['value_changes'])}):")
                for v in c["value_changes"][:10]:
                    print(f"      <{v['tag']}>: {v['old']} -> {v['new']}")
            print(f"    guid_regen={c['guid_regen']}  bom_or_decl={c['bom_or_decl']}  +elems={len(c['new_elements'])} -elems={len(c['removed_elements'])}")
    else:
        print("  mtproject: unchanged")
    if diff["exp"]:
        print(f"  exp changes:")
        for e in diff["exp"]:
            print(f"    [{e['status']}] {e['name']}{' size_delta='+str(e.get('size_delta','')) if e.get('size_delta') is not None else ''}")
    else:
        print("  exp: no change")

def cmd_report(name):
    session_dir = LEARN_ROOT / name
    state = load_state(session_dir)
    if not state: print(f"FAIL: session '{name}' not initialized"); sys.exit(1)
    lines = []
    lines.append(f"# UI→XML 매핑 학습 — 세션 {name}")
    lines.append("")
    lines.append(f"시작: {state['started']} · step 수: {len(state['steps'])-1} (baseline 제외)")
    lines.append("")
    lines.append("## Step 요약")
    lines.append("")
    lines.append("| # | 설명 | mtproject Δ size | value changes | guid_regen | exp changed |")
    lines.append("| - | ---- | ---------------- | ------------- | ---------- | ----------- |")
    for st in state["steps"][1:]:
        m = st["diff"]["mtproject"]
        size_d = f"{m['size_delta']:+d}" if m else "0"
        vc = len(m["changes"]["value_changes"]) if m and m.get("changes") else 0
        gr = m["changes"]["guid_regen"] if m and m.get("changes") else 0
        exp_ch = sum(1 for e in st["diff"]["exp"] if e["status"] != "unchanged")
        lines.append(f"| {st['i']} | {st['description'][:60]} | {size_d} | {vc} | {gr} | {exp_ch} |")
    lines.append("")
    lines.append("## Step별 상세")
    lines.append("")
    for st in state["steps"][1:]:
        lines.append(f"### Step {st['i']}: {st['description']}")
        lines.append("")
        m = st["diff"]["mtproject"]
        if m and m.get("changes"):
            c = m["changes"]
            if c["value_changes"]:
                lines.append("**value 변경**:")
                lines.append("")
                lines.append("| tag | old | new |")
                lines.append("| --- | --- | --- |")
                for v in c["value_changes"][:30]:
                    lines.append(f"| `{v['tag']}` | `{v['old'][:40]}` | `{v['new'][:40]}` |")
                lines.append("")
            if c["new_elements"]:
                lines.append(f"**신규 요소** (top 5): {', '.join(set(e['tag'] for e in c['new_elements'][:20]))}")
                lines.append("")
            if c["removed_elements"]:
                lines.append(f"**제거 요소** (top 5): {', '.join(set(e['tag'] for e in c['removed_elements'][:20]))}")
                lines.append("")
            lines.append(f"기타: guid_regen={c['guid_regen']}, bom_or_decl={c['bom_or_decl']}, raw_added={c['raw_added']}, raw_removed={c['raw_removed']}")
            lines.append("")
        if st["diff"]["exp"]:
            lines.append("**exp 영향**:")
            lines.append("")
            for e in st["diff"]["exp"]:
                lines.append(f"- [{e['status']}] `{e['name']}` size_delta={e.get('size_delta','-')}")
            lines.append("")
    out = session_dir / "learning_log.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"REPORT written: {out}")

def cmd_status(name):
    session_dir = LEARN_ROOT / name
    state = load_state(session_dir)
    if not state: print(f"no session '{name}'"); return
    print(f"session={name} started={state['started']} steps={len(state['steps'])-1}")
    for st in state["steps"]:
        d = st.get("description","baseline")
        m = st["diff"]["mtproject"] if st.get("diff") else None
        size_d = m["size_delta"] if m else 0
        print(f"  step{st['i']:02d} {d[:60]:60} Δ={size_d:+d}")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h","--help"):
        print("Usage:\n  ui_learn.py --init <session>\n  ui_learn.py --capture <session> '<description>'\n  ui_learn.py --report <session>\n  ui_learn.py --status <session>")
        return
    cmd = sys.argv[1]
    if cmd == "--init":
        cmd_init(sys.argv[2])
    elif cmd == "--capture":
        cmd_capture(sys.argv[2], sys.argv[3])
    elif cmd == "--report":
        cmd_report(sys.argv[2])
    elif cmd == "--status":
        cmd_status(sys.argv[2])
    else:
        print(f"unknown cmd: {cmd}")

if __name__ == "__main__":
    main()
