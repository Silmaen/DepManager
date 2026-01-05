"""
Instance of toolsets manager.
"""

from pathlib import Path

from api.internal.messaging import log


class ToolsetsManager:
    """
    Toolset manager.
    """

    def __init__(self, system=None):
        from api.internal.system import LocalSystem
        from api.local import LocalManager

        if type(system) is LocalSystem:
            self.__sys = system
        elif type(system) is LocalManager:
            self.__sys = system.get_sys()
        else:
            self.__sys = LocalSystem()

    def get_toolset_list(self):
        """
        Get a list of toolsets.
        :return: List of toolsets.
        """
        return self.__sys.toolsets

    def get_toolset(self, name: str):
        """
        Access to toolset with given name.
        :param name: Name of the toolset.
        :return: The toolset or None.
        """
        return self.__sys.get_toolset(name)

    def get_default_toolset(self):
        """
        Access to the default toolset.
        :return: The toolset or None.
        """
        return self.__sys.get_toolset("")

    def add_toolset(
        self,
        name: str,
        compiler_path: str,
        abi: str = "",
        os: str = "",
        arch: str = "",
        glibc: str = "",
        default: bool = False,
    ):
        """
        Add a toolset to the list.
        :param name: Toolset's name.
        :param compiler_path: Compiler path.
        :param abi: Toolset's abi.
        :param os: Optional: the target os (empty for native).
        :param arch: Optional: the target arch (empty for native).
        :param glibc: Optional: the target glibc if applicable (empty for native).
        :param default:
        """

        data = {"name": name, "compiler_path": compiler_path, "abi": abi}
        if data["abi"] in ["", None]:
            # deduce the compiler's ABI:
            cl = Path(compiler_path)
            name = cl.stem
            if name.endswith("cl"):
                data["abi"] = "msvc"
            else:
                data["abi"] = "gnu"
        if os not in ["", None] and arch not in ["", None]:
            data["arch"] = arch
            data["os"] = os
            if os.lower() == "linux" and glibc not in ["", None]:
                data["glibc"] = glibc
        if self.check(data):
            self.__sys.add_toolset(name, data, default)
        else:
            log.error(f"Could not add tool set.")

    def remove_toolset(self, name: str):
        """
        Remove a toolset from the list.
        :param name: Toolset's name.
        """
        self.__sys.del_toolset(name)

    def check(self, data):
        status = True
        if data["abi"] not in ["gnu", "llvm", "msvc"]:
            log.error(f"ABI should be one of {['gnu', 'llvm', 'msvc']}.")
            status = False
        cl = Path(data["compiler_path"]).stem
        if data["abi"] == "gnu":
            if (
                not cl.startswith("gcc")
                and not cl.startswith("g++")
                and not cl.startswith("clang")
            ):
                log.error(f"for gnu abi compiler should be either gcc, g++ or clang")
                status = False
        elif data["abi"] == "llvm":
            if not cl.startswith("clang"):
                log.error(f"for llvm abi compiler should be clang")
                status = False
        elif data["abi"] == "msvc":
            if not cl.endswith("cl"):
                log.error(f"for msvc abi compiler should be either cl or clang-cl")
                status = False

        return status
