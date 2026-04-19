"""
Non-regression tests for ``PackageManager.add_from_remote``.

Covers the bug where ``get_dependency_list()`` returns ``dict`` entries that
were previously fed straight back into ``add_from_remote``. On the recursive
call the code tried ``dep.properties.hash()`` and crashed with
``AttributeError: 'dict' object has no attribute 'properties'``. The fix
resolves the dict to a real ``Dependency`` via ``remote.query(sub_dep)`` before
recursing.

These tests drive the code with fake remote / local / system collaborators
rather than spinning up a full ``LocalSystem``; the goal is to pin the
recursion contract, not re-test the full stack.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from depmanager.api.internal.dependency import Dependency
from depmanager.api.package import PackageManager


def _dep_str(name: str, version: str) -> str:
    return (
        f"{name}/{version} (2024-01-01T00:00:00+00:00) " f"[x86_64, static, Linux, gnu]"
    )


class FakeRemote:
    """Minimal stand-in for a remote database."""

    def __init__(self, catalog):
        self.catalog = catalog  # dict[name, Dependency]
        self.pull_calls: list[str] = []
        self.pull_returns = None  # reproduce the crash trigger

    def _name_of(self, q):
        if isinstance(q, dict):
            return q.get("name")
        if hasattr(q, "properties"):
            return q.properties.name
        return None

    def query(self, q):
        name = self._name_of(q)
        dep = self.catalog.get(name)
        return [dep] if dep is not None else []

    def pull(self, dep, destination):
        self.pull_calls.append(dep.properties.name)
        return self.pull_returns


class FakeLocalDB:
    def __init__(self, present_names: set | None = None):
        self.present_names = present_names or set()

    def query(self, q):
        name = q.get("name") if isinstance(q, dict) else getattr(q, "name", None)
        if name in self.present_names:
            return [Dependency(_dep_str(name, "1.0.0"))]
        return []


class FakeSystem:
    def __init__(self, remote: FakeRemote, local: FakeLocalDB, tmp: Path):
        self.remote_database = {"testremote": remote}
        self.local_database = local
        self.temp_path = tmp
        self.default_remote = "testremote"

    def get_source_list(self):
        return ["local", "testremote"]


def _make_manager(sys_):
    pm = PackageManager.__new__(PackageManager)
    pm._PackageManager__sys = sys_
    return pm


@pytest.fixture
def fixture_tmp(tmp_path):
    d = tmp_path / "tmp"
    d.mkdir()
    return d


def test_transitive_dict_dep_resolved_not_passed_raw(monkeypatch, fixture_tmp):
    """
    The bug reproducer: a package with a transitive dep (dict) must not be
    recursively passed as a dict. The fix resolves it via remote.query() and
    passes the resulting Dependency.
    """
    leaf = Dependency(_dep_str("leaf", "2.0.0"))
    root = Dependency(_dep_str("root", "1.0.0"))
    root.properties.dependencies = [
        {
            "name": "leaf",
            "version": "2.0.0",
            "os": "Linux",
            "arch": "x86_64",
            "kind": "static",
            "abi": "gnu",
        }
    ]

    remote = FakeRemote({"root": root, "leaf": leaf})
    remote.pull_returns = None  # triggers the old dep.properties.hash() path
    local = FakeLocalDB(present_names=set())  # nothing cached: force remote
    pm = _make_manager(FakeSystem(remote, local, fixture_tmp))
    monkeypatch.setattr(pm, "add_from_location", lambda path: None)

    # Must not raise AttributeError.
    pm.add_from_remote(root, "testremote")

    # Both root and the resolved leaf get pulled — order matters (root first).
    assert remote.pull_calls == ["root", "leaf"]


def test_transitive_dep_already_local_skips_remote(monkeypatch, fixture_tmp):
    """If the transitive dep is already in the local cache, no recursion."""
    root = Dependency(_dep_str("root", "1.0.0"))
    root.properties.dependencies = [
        {
            "name": "leaf",
            "version": "2.0.0",
            "os": "Linux",
            "arch": "x86_64",
            "kind": "static",
            "abi": "gnu",
        }
    ]

    remote = FakeRemote({"root": root})
    remote.pull_returns = None
    local = FakeLocalDB(present_names={"leaf"})
    pm = _make_manager(FakeSystem(remote, local, fixture_tmp))
    monkeypatch.setattr(pm, "add_from_location", lambda path: None)

    pm.add_from_remote(root, "testremote")

    assert remote.pull_calls == ["root"]  # leaf skipped


def test_missing_transitive_on_remote_logs_but_does_not_crash(monkeypatch, fixture_tmp):
    """If the transitive dep cannot be found on the remote, log and continue."""
    root = Dependency(_dep_str("root", "1.0.0"))
    root.properties.dependencies = [
        {
            "name": "ghost",
            "version": "9.9.9",
            "os": "Linux",
            "arch": "x86_64",
            "kind": "static",
            "abi": "gnu",
        }
    ]

    remote = FakeRemote({"root": root})  # no "ghost" in catalog
    remote.pull_returns = None
    local = FakeLocalDB(present_names=set())
    pm = _make_manager(FakeSystem(remote, local, fixture_tmp))
    monkeypatch.setattr(pm, "add_from_location", lambda path: None)

    pm.add_from_remote(root, "testremote")

    assert remote.pull_calls == ["root"]
