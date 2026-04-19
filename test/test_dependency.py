"""
Unit tests for Props / Dependency and helpers in
``depmanager.api.internal.dependency``.
"""

from __future__ import annotations

import datetime

import pytest

from depmanager.api.internal.dependency import (
    Dependency,
    Props,
    base_date,
    read_date,
    safe_to_int,
    version_lt,
)


class TestVersionLt:
    @pytest.mark.parametrize(
        "a, b, expected",
        [
            ("1.0.0", "1.0.1", True),
            ("1.0.1", "1.0.0", False),
            ("1.0.0", "1.0.0", False),
            ("1.2", "1.10", True),  # numeric, not lexicographic
            ("2.0", "10.0", True),
            ("1.0", "1.0.0", True),  # shorter lt longer when prefix equal
            ("1.0.0", "1.0", False),
            ("rc1", "rc2", True),  # safe_to_int skips leading non-digits
            ("1.0rc1", "1.0rc2", False),  # numeric chunk "0" == "0", suffix ignored
        ],
    )
    def test_comparisons(self, a, b, expected):
        assert version_lt(a, b) is expected


class TestSafeToInt:
    @pytest.mark.parametrize(
        "s, expected",
        [
            ("12", 12),
            ("rc12", 12),
            ("abc", 0),
            ("", 0),
            ("3abc", 3),
        ],
    )
    def test_extracts_leading_digits(self, s, expected):
        assert safe_to_int(s) == expected


class TestReadDate:
    def test_iso_utc(self):
        d = read_date("2024-06-15T10:20:30+00:00")
        assert isinstance(d, datetime.datetime)
        assert d.year == 2024 and d.month == 6 and d.day == 15

    def test_compact_date(self):
        d = read_date("20240615T102030")
        assert d.year == 2024 and d.hour == 10

    def test_garbage_returns_base(self):
        d = read_date("not-a-date")
        assert d == base_date

    def test_empty_returns_base(self):
        assert read_date("") == base_date


class TestPropsFromDict:
    def test_minimal(self):
        p = Props({"name": "foo", "version": "1.2.3"}, query=True)
        assert p.name == "foo"
        assert p.version == "1.2.3"

    def test_full_fields(self):
        data = {
            "name": "libbar",
            "version": "2.0.0",
            "os": "Linux",
            "arch": "x86_64",
            "kind": "static",
            "abi": "gnu",
            "glibc": "2.35",
            "dependencies": [{"name": "dep1", "version": "1.0"}],
        }
        p = Props(data)
        assert p.name == "libbar"
        assert p.os == "Linux"
        assert p.glibc == "2.35"
        assert p.dependencies == [{"name": "dep1", "version": "1.0"}]

    def test_deprecated_compiler_alias(self):
        p = Props({"name": "x", "compiler": "llvm"})
        assert p.abi == "llvm"


class TestPropsMatch:
    def _make(self, **overrides):
        base = {
            "name": "libfoo",
            "version": "1.0.0",
            "os": "Linux",
            "arch": "x86_64",
            "kind": "static",
            "abi": "gnu",
        }
        base.update(overrides)
        return Props(base)

    def test_exact_match(self):
        a = self._make()
        b = self._make()
        assert a.match(b)

    def test_name_mismatch(self):
        assert not self._make(name="libfoo").match(self._make(name="libbar"))

    def test_wildcard_name(self):
        query = self._make(name="*foo")
        assert self._make(name="libfoo").match(query)

    def test_kind_any_is_wildcard(self):
        query = Props({"name": "libfoo", "kind": "any"}, query=True)
        assert self._make(kind="static").match(query)

    def test_glibc_lower_or_equal_matches(self):
        pkg = self._make(glibc="2.31")
        query = self._make(glibc="2.35")  # system libc 2.35 accepts pkg built for 2.31
        assert pkg.match(query)

    def test_glibc_higher_does_not_match(self):
        pkg = self._make(glibc="2.40")
        query = self._make(glibc="2.35")
        assert not pkg.match(query)

    def test_glibc_exact_prefix(self):
        pkg = self._make(glibc="2.35")
        query = self._make(glibc="=2.35")
        assert pkg.match(query)
        query2 = self._make(glibc="=2.31")
        assert not pkg.match(query2)

    def test_glibc_any_or_empty(self):
        pkg = self._make(glibc="2.35")
        assert pkg.match(self._make(glibc="any"))
        assert pkg.match(self._make(glibc=""))


class TestPropsRoundtrip:
    def test_get_as_str_then_from_str(self):
        original = Props(
            {
                "name": "libfoo",
                "version": "1.2.3",
                "os": "Linux",
                "arch": "x86_64",
                "kind": "static",
                "abi": "gnu",
            }
        )
        as_str = original.get_as_str()
        round_tripped = Props(as_str)
        assert round_tripped.name == original.name
        assert round_tripped.version == original.version
        assert round_tripped.os == original.os
        assert round_tripped.arch == original.arch
        assert round_tripped.kind == original.kind
        assert round_tripped.abi == original.abi


class TestPropsHash:
    def test_stable_and_deterministic(self):
        p = Props({"name": "a", "version": "1"})
        h1 = p.hash()
        h2 = Props({"name": "a", "version": "1"}).hash()
        assert h1 == h2

    def test_changes_on_field_change(self):
        h1 = Props({"name": "a", "version": "1"}).hash()
        h2 = Props({"name": "a", "version": "2"}).hash()
        assert h1 != h2


class TestDependencyDeps:
    def test_has_dependency_false_on_empty(self):
        d = Dependency({"name": "x", "version": "1"})
        assert d.has_dependency() is False

    def test_has_dependency_true_with_list(self):
        d = Dependency(
            {
                "name": "x",
                "version": "1",
                "dependencies": [{"name": "y", "version": "1"}],
            }
        )
        assert d.has_dependency() is True

    def test_get_dependency_list_returns_raw_dicts(self):
        """Contract: dependencies are stored and returned as dicts (see add_from_remote bug fix)."""
        deps = [{"name": "y", "version": "1"}, {"name": "z", "version": "2"}]
        d = Dependency({"name": "x", "version": "1", "dependencies": deps})
        result = d.get_dependency_list()
        assert result == deps
        assert all(isinstance(sub, dict) for sub in result)


class TestDependencyVersionCompare:
    def test_has_minimal_version(self):
        d = Dependency({"name": "x", "version": "2.5.0"})
        assert d.has_minimal_version("2.0.0") is True
        assert d.has_minimal_version("2.5.0") is True
        assert d.has_minimal_version("3.0.0") is False
        assert d.has_minimal_version("") is False

    def test_version_greater(self):
        d = Dependency({"name": "x", "version": "2.5.0"})
        assert d.version_greater("2.0.0") is True
        assert d.version_greater("2.5.0") is False
        assert d.version_greater("3.0.0") is False
        assert d.version_greater("") is True
