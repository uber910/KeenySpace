from __future__ import annotations

import os
import shutil
from pathlib import Path

import structlog

log = structlog.get_logger(__name__)


def ensure_fs_root_layout(
    fs_root: Path, server_blueprints_image_dir: Path
) -> None:
    for subdir in ("workspaces", "blueprints", ".tmp"):
        (fs_root / subdir).mkdir(parents=True, exist_ok=True)

    default_target = fs_root / "blueprints" / "default"
    default_src = server_blueprints_image_dir / "default"
    if not default_target.exists():
        if default_src.exists():
            shutil.copytree(
                default_src,
                default_target,
                symlinks=False,
                dirs_exist_ok=False,
                ignore_dangling_symlinks=True,
            )
    elif default_src.exists():
        # G-3 (Phase 4 UAT): merge new image files into the on-disk blueprint
        # catalog on EVERY boot. First-boot path above does a full copytree;
        # this branch only fills in files added by later image upgrades
        # (e.g. _instructions/ingest.md landed in Plan 04-01 but never reached
        # existing fs_root volumes because the directory already existed).
        # Operator-customised files are NEVER overwritten (skip-on-exists).
        _merge_blueprint_tree(default_src, default_target)

    _sweep_stale_tmp(fs_root / ".tmp")


def _merge_blueprint_tree(src: Path, dst: Path) -> None:
    """Copy files present in ``src`` but missing in ``dst``; never overwrite.

    Best-effort: an OSError on an individual file logs a warning and continues
    (same shape as ``_sweep_stale_tmp``). Symlinks in ``src`` are skipped.
    """
    for src_root, dirnames, filenames in os.walk(src, followlinks=False):
        rel_root = Path(src_root).relative_to(src)
        # Skip symlinked sub-directories defence-in-depth (os.walk followlinks=False
        # already refuses to descend, but pruning here avoids touching the entries).
        dirnames[:] = [
            d for d in dirnames if not (Path(src_root) / d).is_symlink()
        ]
        dst_root = dst / rel_root
        try:
            dst_root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            log.warning(
                "fs.bootstrap.blueprint_merge_mkdir_failed",
                path=str(dst_root),
                error=str(exc),
            )
            continue
        for filename in filenames:
            src_file = Path(src_root) / filename
            dst_file = dst_root / filename
            if src_file.is_symlink():
                continue
            if dst_file.exists():
                continue
            try:
                shutil.copy2(src_file, dst_file)
            except OSError as exc:
                log.warning(
                    "fs.bootstrap.blueprint_merge_copy_failed",
                    src=str(src_file),
                    dst=str(dst_file),
                    error=str(exc),
                )


def _sweep_stale_tmp(tmp_root: Path) -> None:
    """Reap stale ``import_*`` / ``upload_*`` entries left by killed requests.

    WR-14: the in-request ``finally`` blocks in ``api/workspace_import.py``
    and ``ws/import_.py`` only run if the worker survives long enough to
    execute them. ``kill -9``, OOM-killer, container restart, or a stuck
    ``await file.read(...)`` mid-cancellation leave staged extractions and
    partial uploads on disk indefinitely. v1 ships single-worker uvicorn,
    so at startup no other process is mid-import; a sweep here is safe.

    Best-effort: failures to remove an entry log a warning and continue
    (a stuck mount or permission issue should not block server boot).
    """
    if not tmp_root.is_dir():
        return
    for entry in tmp_root.iterdir():
        if not entry.name.startswith(("import_", "upload_")):
            continue
        try:
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry, ignore_errors=True)
            else:
                entry.unlink(missing_ok=True)
        except OSError as exc:
            log.warning(
                "fs.startup.tmp_cleanup_failed",
                path=str(entry),
                error=str(exc),
            )
