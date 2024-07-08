"""
Toolset defining tools, compiler and environment.
"""

from sys import stderr

from depmanager.api.internal.machine import Machine


class Toolset:

    def __init__(
        self,
        name: str,
        compiler: str = "",
        os: str = "",
        arch: str = "",
        glibc: str = "",
        default: bool = False,
    ):
        self.name = name
        self.compiler = compiler
        self.os = os
        self.arch = arch
        self.glibc = glibc
        self.default = default
        self.autofill = False

    def from_dict(self, data: dict):
        if "compiler" in data:
            self.compiler = data["compiler"]
        else:
            print(f"Bad toolchain {self.name}: no compiler defined.", file=stderr)
            return
        if ("or" in data) ^ ("arch" in data):
            print(f"Bad toolchin {self.name}: os/arch badly defined.", file=stderr)
            return
        if "default" in data:
            self.default = data["default"]
        if "os" in data:
            self.os = data["os"]
            self.arch = data["arch"]
            if "glibc" in data:
                self.glibc = data["glibc"]
        else:
            self.autofill = True
            mac = Machine(True)
            self.os = mac.os
            self.arch = mac.arch
            self.glibc = mac.glibc

    def to_dict(self) -> dict:
        ret = {"compiler": self.compiler}
        if self.default:
            ret["default"] = True
        if not self.autofill:
            ret["os"] = self.os
            ret["arch"] = self.arch
            if self.glibc not in [None, ""]:
                ret["glibc"] = self.glibc
        return ret
