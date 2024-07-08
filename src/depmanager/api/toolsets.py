"""
Instance of toolsets manager.
"""


class ToolsetsManager:
    """
    Toolset manager.
    """

    def __init__(self, system=None, verbosity: int = 0):
        from depmanager.api.internal.system import LocalSystem
        from depmanager.api.local import LocalManager

        self.verbosity = verbosity
        if type(system) is LocalSystem:
            self.__sys = system
        elif type(system) is LocalManager:
            self.__sys = system.get_sys()
        else:
            self.__sys = LocalSystem(verbosity=verbosity)

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
        compiler: str,
        os: str = "",
        arch: str = "",
        glibc: str = "",
        default: bool = False,
    ):
        """
        Add a toolset to the list.
        :param name: Toolset's name.
        :param compiler: Toolset's compiler.
        :param os: Optional: the target os (empty for native).
        :param arch: Optional: the target arch (empty for native).
        :param glibc: Optional: the target glibc if applicable (empty for native).
        :param default:
        """
        data = {"name": name, "compiler": compiler}
        if os not in ["", None] and arch not in ["", None]:
            data["arch"] = arch
            data["os"] = os
            if os.lower() == "linux" and glibc not in ["", None]:
                data["glibc"] = glibc
        self.__sys.add_toolset(name, data, default)

    def remove_toolset(self, name: str):
        """
        Remove a toolset from the list.
        :param name: Toolset's name.
        """
        self.__sys.del_toolset(name)
