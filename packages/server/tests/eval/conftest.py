from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_ROOT = Path(__file__).parent / "fixtures" / "compile"


@pytest.fixture
def vault_root(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    return vault


@pytest.fixture
def fixtures_root() -> Path:
    return FIXTURES_ROOT


@pytest.fixture
def golden_fixtures(fixtures_root: Path) -> list[Path]:
    return sorted(p for p in (fixtures_root / "golden").iterdir() if p.is_dir())


@pytest.fixture
def edge_fixtures(fixtures_root: Path) -> list[Path]:
    return sorted(p for p in (fixtures_root / "edge").iterdir() if p.is_dir())


@pytest.fixture
def adversarial_fixtures(fixtures_root: Path) -> list[Path]:
    return sorted(p for p in (fixtures_root / "adversarial").iterdir() if p.is_dir())


@pytest.fixture
def domain_fixtures(fixtures_root: Path) -> list[Path]:
    return sorted(p for p in (fixtures_root / "domain").iterdir() if p.is_dir())
