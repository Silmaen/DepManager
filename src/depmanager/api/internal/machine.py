"""
Machine identification.
"""
import platform
from sys import stderr

compilers = ["gnu", "msvc"]
oses = ["Windows", "Linux"]
arches = ["x86_64", "aarch64"]


def format_os(os_str: str):
    """
    Format the string for OS.
    :param os_str: the input OS.
    :return: The formatted os name.
    """
    if os_str not in oses:
        exit(666)
    return os_str


def format_arch(arch_str: str):
    """
    Formatted CPU architecture.
    :param arch_str: The input architecture.
    :return: The formatted architecture.
    """
    if arch_str == "AMD64":
        arch_str = "x86_64"
    if arch_str not in arches:
        exit(666)
    return arch_str


class Machine:
    """
    Class holding machine information
    """

    def __init__(self, do_init: bool = False):
        self.default_compiler = ""
        self.glibc = ""
        self.os = ""
        self.arch = ""
        self.os_version = ""
        self.initiated = False
        if do_init:
            self.__introspection()

    def __repr__(self):
        self.__introspection()
        sys_info = f"{self.os}, {self.os_version}, {self.arch}, {self.default_compiler}"
        if self.os == "Linux":
            sys_info += f", {self.glibc}"
        return sys_info

    def __introspection(self):
        if self.initiated:
            return
        self.os = format_os(platform.system())
        self.arch = format_arch(platform.machine())
        self.default_compiler = "gnu"
        if self.os == "Linux":
            self.glibc = platform.libc_ver()[1]
            try:
                details = platform.freedesktop_os_release()
                self.os_version = f"{details['PRETTY_NAME']}"
            except Exception as err:
                print(
                    f"WARNING: Exception during Linux system introspection: {err}.",
                    file=stderr,
                )
                self.os_version = "unknown"
        elif self.os == "Windows":
            try:
                version_str = platform.version().split(".")
                if int(version_str[0]) < 10:
                    self.os_version = version_str[0]
                else:
                    if int(version_str[2]) < 22000:
                        self.os_version = "10"
                    else:
                        self.os_version = "11"
            except Exception as err:
                print(
                    f"WARNING: Exception during Windows system introspection: {err}.",
                    file=stderr,
                )
                self.os_version = "unknown"
        else:
            exit(666)
        self.initiated = True
