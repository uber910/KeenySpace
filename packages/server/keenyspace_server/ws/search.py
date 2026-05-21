from __future__ import annotations

import re
from pathlib import Path

from keenyspace_server.ws.scan import iter_md_files


def list_md_paths(ws_root: Path, prefix: str | None = None) -> list[str]:
    if not ws_root.is_dir():
        return []
    rels: list[str] = []
    for _abs, rel in iter_md_files(ws_root):
        rel_str = rel.as_posix()
        if prefix is not None and not rel_str.startswith(prefix):
            continue
        rels.append(rel_str)
    rels.sort()
    return rels


def search_workspace_files(ws_root: Path, pattern: re.Pattern[str]) -> list[str]:
    if not ws_root.is_dir():
        return []
    matches: list[str] = []
    for abs_path, rel in iter_md_files(ws_root):
        rel_str = rel.as_posix()
        if pattern.search(rel_str):
            matches.append(rel_str)
            continue
        try:
            content = abs_path.read_bytes().decode("utf-8", errors="replace")
        except OSError:
            continue
        if pattern.search(content):
            matches.append(rel_str)
    matches.sort()
    return matches
