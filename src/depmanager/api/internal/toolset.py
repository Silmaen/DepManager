"""
Toolset defining tools, abi and environment.
"""

from sys import stderr


class Toolset:

    def __init__(
        self,
        name: str,
        abi: str = "",
        compiler_path: str = "",
        default: bool = False,
    ):
        self.name = name
        self.abi = abi
        self.compiler_path = compiler_path
        self.default = default

    def from_dict(self, data: dict):
        if "compiler_path" in data:
            self.compiler_path = data["compiler_path"]
        else:
            print(f"Bad toolchain {self.name}: no compiler_path defined.", file=stderr)
            return
        if "abi" in data:
            self.abi = data["abi"]
        else:
            print(f"Bad toolchain {self.name}: no abi defined.", file=stderr)
            return
        if "default" in data:
            self.default = data["default"]

    def to_dict(self) -> dict:
        ret = {"abi": self.abi, "compiler_path": self.compiler_path}
        if self.default:
            ret["default"] = True
        else:
            ret["default"] = False
        return ret
