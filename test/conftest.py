"""
Shared pytest fixtures for the DepManager test suite.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_edm_home(tmp_path, monkeypatch):
    """
    Isolate DEPMANAGER_HOME in a temporary directory.

    Ensures tests never touch the user's real ~/.edm/. Yields the tmp path so
    tests can inspect it. The standard subdirectories (data, tmp) are created
    up front to mirror what LocalSystem would do.

    :return: Path to the isolated DEPMANAGER_HOME.
    """
    home = tmp_path / ".edm"
    (home / "data").mkdir(parents=True)
    (home / "tmp").mkdir(parents=True)
    monkeypatch.setenv("DEPMANAGER_HOME", str(home))
    return home


@pytest.fixture
def make_package(tmp_edm_home):
    """
    Factory building a minimal valid package directory inside the local cache.

    The returned callable accepts the package fields and drops an ``info.yaml``
    file where LocalDatabase expects it. Useful for LocalDatabase integration
    tests without shelling out to the CLI.

    :return: Callable(name, version, **overrides) -> Path of the created package.
    """
    import yaml

    def _make(
        name: str = "libdummy",
        version: str = "1.0.0",
        os_name: str = "Linux",
        arch: str = "x86_64",
        kind: str = "static",
        abi: str = "gnu",
        glibc: str = "",
        dependencies: list | None = None,
    ) -> Path:
        pkg_dir = tmp_edm_home / "data" / f"{name}-{version}"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        info = {
            "name": name,
            "version": version,
            "os": os_name,
            "arch": arch,
            "kind": kind,
            "abi": abi,
            "build_date": "2024-01-01T00:00:00+00:00",
            "dependencies": dependencies or [],
        }
        if glibc:
            info["glibc"] = glibc
        with open(pkg_dir / "info.yaml", "w") as fp:
            yaml.dump(info, fp)
        return pkg_dir

    return _make
