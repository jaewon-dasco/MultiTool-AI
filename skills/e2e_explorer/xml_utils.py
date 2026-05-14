"""`.mtproject` lxml read/write/diff/backup.

v0.2: XML element text 직접 편집 + canonical 비교.
"""
from __future__ import annotations

import hashlib
import logging
import shutil
import time
from pathlib import Path

from lxml import etree

log = logging.getLogger(__name__)


def parse(path: Path) -> etree._ElementTree:
    parser = etree.XMLParser(remove_blank_text=False)
    return etree.parse(str(path), parser)


def write(tree: etree._ElementTree, path: Path) -> None:
    tree.write(str(path), encoding="utf-8", xml_declaration=True, pretty_print=False)


def canonicalize(path: Path) -> bytes:
    """C14N으로 정규화된 XML bytes 반환 (의미적 비교용)."""
    tree = parse(path)
    return etree.tostring(tree, method="c14n")


def semantic_equal(a: Path, b: Path) -> bool:
    return hashlib.sha256(canonicalize(a)).hexdigest() == hashlib.sha256(canonicalize(b)).hexdigest()


def backup(path: Path, suffix: str | None = None) -> Path:
    suffix = suffix or time.strftime("%Y%m%d_%H%M%S")
    bak = path.with_suffix(path.suffix + f".bak.{suffix}")
    shutil.copy2(path, bak)
    return bak


def restore(path: Path, bak: Path) -> None:
    shutil.copy2(bak, path)


def get_text(path: Path, xpath: str) -> str | None:
    tree = parse(path)
    nodes = tree.xpath(xpath)
    if not nodes:
        return None
    node = nodes[0]
    return node.text if hasattr(node, "text") else str(node)


def set_text(path: Path, xpath: str, new_value: str) -> tuple[str | None, str]:
    """XPath로 단일 element를 찾아 text 설정. (old, new) 반환."""
    tree = parse(path)
    nodes = tree.xpath(xpath)
    if not nodes:
        raise ValueError(f"xpath matched nothing: {xpath}")
    if len(nodes) > 1:
        raise ValueError(f"xpath matched {len(nodes)} nodes (expected 1): {xpath}")
    node = nodes[0]
    old = node.text
    node.text = new_value
    write(tree, path)
    return old, new_value


def line_diff(a: Path, b: Path, context: int = 1) -> list[str]:
    """Canonical 형태로 라인 diff (디버깅 가독성용)."""
    import difflib
    a_text = canonicalize(a).decode("utf-8", errors="replace").splitlines()
    b_text = canonicalize(b).decode("utf-8", errors="replace").splitlines()
    return list(difflib.unified_diff(a_text, b_text, lineterm="", n=context))


def _cli() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--get", nargs=2, metavar=("PROJECT", "XPATH"))
    ap.add_argument("--set", nargs=3, metavar=("PROJECT", "XPATH", "VALUE"))
    ap.add_argument("--equal", nargs=2, metavar=("A", "B"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO)

    if args.get:
        print(get_text(Path(args.get[0]), args.get[1]))
    elif args.set:
        old, new = set_text(Path(args.set[0]), args.set[1], args.set[2])
        print(f"changed {old!r} → {new!r}")
    elif args.equal:
        print(semantic_equal(Path(args.equal[0]), Path(args.equal[1])))


if __name__ == "__main__":
    _cli()
