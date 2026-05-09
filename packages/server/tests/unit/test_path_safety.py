from __future__ import annotations

import os
from pathlib import Path

import pytest
from keenyspace_server.fs.path_safety import UnsafePath, open_workspace_page, validate_relative_path


@pytest.mark.parametrize(
    "path,should_raise",
    [
        ("../etc/passwd", True),
        ("/etc/passwd", True),
        ("\\windows\\sys", True),
        ("..\x00..", True),
        (".obsidian/config", True),
        (".git/HEAD", True),
        ("valid/path", False),
        ("valid", False),
        ("concepts/architecture", False),
        ("a" * 513, True),
        ("", True),
        ("evil/../../escape", True),
        ("legit/../still-legit/../still-legit/page", True),
    ],
)
def test_validate_relative_path(path: str, should_raise: bool) -> None:
    if should_raise:
        with pytest.raises(UnsafePath):
            validate_relative_path(path)
    else:
        result = validate_relative_path(path)
        assert result.endswith(".md")


def test_validate_appends_md_extension() -> None:
    result = validate_relative_path("concepts/architecture")
    assert result == "concepts/architecture.md"


def test_validate_keeps_md_extension() -> None:
    result = validate_relative_path("page.md")
    assert result == "page.md"


def test_open_workspace_page_valid(tmp_path: Path) -> None:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir()
    (ws_root / "page.md").write_text("# Hello")

    fd, _resolved = open_workspace_page(ws_root, "page")
    try:
        content = os.read(fd, 1024)
        assert b"# Hello" in content
    finally:
        os.close(fd)


def test_open_workspace_page_traversal(tmp_path: Path) -> None:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir()

    with pytest.raises(UnsafePath):
        open_workspace_page(ws_root, "../escape")


def test_open_workspace_page_hidden_component(tmp_path: Path) -> None:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir()

    with pytest.raises(UnsafePath):
        open_workspace_page(ws_root, ".obsidian/config")


def test_open_workspace_page_symlink_final(tmp_path: Path) -> None:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir()
    real_file = tmp_path / "secret.md"
    real_file.write_text("secret")
    link = ws_root / "link.md"
    link.symlink_to(real_file)

    with pytest.raises((UnsafePath, OSError)):
        fd, _ = open_workspace_page(ws_root, "link")
        os.close(fd)
