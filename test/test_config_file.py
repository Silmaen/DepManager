"""
Unit tests for ``depmanager.api.internal.config_file.ConfigFile``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from depmanager.api.internal.config_file import ConfigFile


def _write_yaml(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


class TestConfigFileEmpty:
    def test_missing_file(self, tmp_path):
        cfg = ConfigFile(tmp_path / "no_such_file.yml")
        assert cfg.data is None
        assert cfg.has_remote() is False
        assert cfg.has_packages() is False
        assert cfg.server_to_add() == {}
        assert cfg.do_pull() is False
        assert cfg.do_pull_newer() is False
        assert cfg.get_packages() == {}

    def test_malformed_yaml(self, tmp_path):
        f = _write_yaml(tmp_path / "bad.yml", "remote: [oops\n  - this : is ]] broken")
        cfg = ConfigFile(f)
        assert cfg.has_remote() is False


class TestConfigFileRemote:
    def test_server_section(self, tmp_path):
        f = _write_yaml(
            tmp_path / "c.yml",
            """
remote:
  server:
    name: srv1
    kind: srvs
    url: https://example.net
  pull: true
""",
        )
        cfg = ConfigFile(f)
        assert cfg.has_remote() is True
        assert cfg.server_to_add()["name"] == "srv1"
        assert cfg.do_pull() is True
        assert cfg.do_pull_newer() is False

    def test_pull_newer_implies_pull(self, tmp_path):
        f = _write_yaml(
            tmp_path / "c.yml",
            """
remote:
  pull-newer: true
""",
        )
        cfg = ConfigFile(f)
        assert cfg.do_pull() is True
        assert cfg.do_pull_newer() is True

    def test_remote_without_server_section(self, tmp_path):
        f = _write_yaml(
            tmp_path / "c.yml",
            """
remote:
  pull: true
""",
        )
        cfg = ConfigFile(f)
        assert cfg.has_remote() is True
        assert cfg.server_to_add() == {}


class TestConfigFilePackages:
    def test_packages_section(self, tmp_path):
        f = _write_yaml(
            tmp_path / "c.yml",
            """
packages:
  libfoo:
    version: 1.2.3
  libbar:
    version: 0.5.0
""",
        )
        cfg = ConfigFile(f)
        assert cfg.has_packages() is True
        pkgs = cfg.get_packages()
        assert "libfoo" in pkgs and pkgs["libfoo"]["version"] == "1.2.3"

    def test_no_packages_section(self, tmp_path):
        f = _write_yaml(tmp_path / "c.yml", "remote:\n  pull: true\n")
        cfg = ConfigFile(f)
        assert cfg.has_packages() is False
        assert cfg.get_packages() == {}


class TestConfigFileBoth:
    def test_both_sections(self, tmp_path):
        f = _write_yaml(
            tmp_path / "c.yml",
            """
remote:
  pull: true
packages:
  libfoo:
    version: "1.0"
""",
        )
        cfg = ConfigFile(f)
        assert cfg.has_remote() is True
        assert cfg.has_packages() is True
