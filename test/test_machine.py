"""
Unit tests for ``depmanager.api.internal.machine``.

The full introspection path relies on ``platform.*`` and therefore is only
lightly covered: we verify that format helpers reject unknown values and that
``Machine`` starts empty unless ``do_init`` is requested or ``__repr__`` forces
introspection.
"""

from __future__ import annotations

import platform

import pytest

from depmanager.api.internal.machine import (
    Machine,
    arches,
    format_arch,
    format_os,
    oses,
)


class TestFormatOs:
    @pytest.mark.parametrize("os_str", oses)
    def test_known_values_pass_through(self, os_str):
        assert format_os(os_str) == os_str

    def test_unknown_exits(self):
        with pytest.raises(SystemExit):
            format_os("Haiku")


class TestFormatArch:
    def test_amd64_normalizes_to_x86_64(self):
        assert format_arch("AMD64") == "x86_64"

    @pytest.mark.parametrize("arch", arches)
    def test_known_values_pass_through(self, arch):
        assert format_arch(arch) == arch

    def test_unknown_exits(self):
        with pytest.raises(SystemExit):
            format_arch("mips64")


class TestMachine:
    def test_uninitiated_state(self):
        m = Machine(do_init=False)
        assert m.initiated is False
        assert m.os == ""
        assert m.arch == ""

    def test_do_init_sets_host_values(self):
        m = Machine(do_init=True)
        assert m.initiated is True
        # Host values depend on the CI runner; just assert they match format
        # helpers' accepted values.
        assert m.os in oses
        assert m.arch in arches or m.arch == format_arch(platform.machine())

    def test_default_abi_overridden_by_toolset(self):
        class FakeToolset:
            abi = "llvm"

        m = Machine(do_init=True, toolset=FakeToolset())
        assert m.default_abi == "llvm"

    def test_repr_forces_introspection(self):
        m = Machine(do_init=False)
        s = repr(m)
        assert m.initiated is True
        assert isinstance(s, str) and len(s) > 0
