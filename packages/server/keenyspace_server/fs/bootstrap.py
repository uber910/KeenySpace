from __future__ import annotations

import shutil
from pathlib import Path


def ensure_fs_root_layout(
    fs_root: Path, server_blueprints_image_dir: Path
) -> None:
    for subdir in ("workspaces", "blueprints"):
        (fs_root / subdir).mkdir(parents=True, exist_ok=True)

    default_target = fs_root / "blueprints" / "default"
    if not default_target.exists():
        default_src = server_blueprints_image_dir / "default"
        if default_src.exists():
            shutil.copytree(
                default_src,
                default_target,
                symlinks=False,
                dirs_exist_ok=False,
                ignore_dangling_symlinks=True,
            )
