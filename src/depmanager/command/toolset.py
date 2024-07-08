"""
Manage the toolsets
"""

from sys import stderr

possible_toolset = ["list", "add", "del"]


class ToolsetCommand:
    """
    Managing toolsets
    """

    def __init__(self, verbosity=0, system=None):
        from depmanager.api.toolsets import ToolsetsManager

        self.toolset_instance = ToolsetsManager(system, verbosity)
        self.verbosity = verbosity

    def list(self):
        """
        Lists the defined remotes.
        """
        toolsets = self.toolset_instance.get_toolset_list()
        for key, value in toolsets.items():
            default = [" ", "*"][value.default]
            if self.verbosity == 0:
                print(f" {default} {key}")
            else:
                to_print = f" {default} [ {key} ] {value.compiler} - "
                if value.autofill:
                    to_print += "native"
                else:
                    to_print += f"{value.os}/{value.arch}"
                    if value.glibc not in [None, ""]:
                        to_print += f" glibc {value.glibc}"
                print(to_print)

    def add(
        self,
        name: str,
        compiler: str,
        os: str = "",
        arch: str = "",
        glibc: str = "",
        default: bool = False,
    ):
        """
        Add a toolset to the list or modify the existing one.
        :param name: Toolset's name.
        :param compiler: Toolset's compiler.
        :param os: Optional: the target os (empty for native).
        :param arch: Optional: the target arch (empty for native).
        :param glibc: Optional: the target glibc if applicable (empty for native).
        :param default: If the toolset should be the new default.
        """
        if type(name) is not str or name in ["", None]:
            print(f"ERROR please give a name for adding a toolset.", file=stderr)
            exit(-666)
        if type(compiler) is not str or compiler in ["", None]:
            print(f"ERROR please give a compiler for adding a toolset.", file=stderr)
            exit(-666)
        self.toolset_instance.add_toolset(name, compiler, os, arch, glibc, default)

    def delete(self, name: str):
        """
        Remove a remote from the list.
        :param name: Remote's name.
        """
        if type(name) is not str or name in ["", None]:
            print(f"ERROR please give a name for removing a toolset.", file=stderr)
            exit(-666)
        self.toolset_instance.remove_toolset(name)


def toolset(args, system=None):
    """
    Toolset entrypoint.
    :param args: Command Line Arguments.
    :param system: The local system
    """
    if args.what not in possible_toolset:
        return
    rem = ToolsetCommand(args.verbose, system)
    if args.what == "list":
        rem.list()
    elif args.what == "add":
        rem.add(args.name, args.compiler, args.os, args.arch, args.glibc, args.default)
    elif args.what == "del":
        rem.delete(args.name)


def add_toolset_parameters(sub_parsers):
    """
    Definition of toolset parameters.
    :param sub_parsers: The parent parser.
    """
    from depmanager.api.internal.common import (
        add_common_arguments,
    )

    info_parser = sub_parsers.add_parser("toolset")
    info_parser.description = "Tool to search for dependency in the library"
    info_parser.add_argument(
        "what",
        type=str,
        choices=possible_toolset,
        help="The information you want about the program",
    )
    add_common_arguments(info_parser)  # add -v
    info_parser.add_argument("--compiler", "-c", type=str, help="Compiler path.")
    info_parser.add_argument("--os", "-o", type=str, default="", help="The target os.")
    info_parser.add_argument(
        "--arch", "-a", type=str, default="", help="The target architecture."
    )
    info_parser.add_argument(
        "--glibc", "-g", type=str, default="", help="The target glibc."
    )
    info_parser.add_argument(
        "--default",
        "-d",
        action="store_true",
        help="If the new toolset should become the default.",
    )
    info_parser.set_defaults(func=toolset)
