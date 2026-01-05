"""
Manage the toolsets
"""

from api.internal.messaging import log, message

possible_toolset = ["list", "ls", "add", "del", "rm"]
deprecated = {"list": "ls", "del": "rm"}


class ToolsetCommand:
    """
    Managing toolsets
    """

    def __init__(self, system=None):
        from api.toolsets import ToolsetsManager

        self.toolset_instance = ToolsetsManager(system)

    def list(self):
        """
        Lists the defined remotes.
        """
        toolsets = self.toolset_instance.get_toolset_list()
        if len(toolsets) == 0:
            log.warn("No toolset defined.")
            return
        message("List of toolsets:")
        for key, value in toolsets.items():
            default = [" ", "*"][value.default]
            message(f" {default} [ {key} ] {value.compiler_path} - {value.abi} - ")

    def add(
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
        Add a toolset to the list or modify the existing one.
        :param name: Toolset's name.
        :param compiler_path: Compiler path.
        :param abi: Toolset's abi.
        :param os: Optional: the target os (empty for native).
        :param arch: Optional: the target arch (empty for native).
        :param glibc: Optional: the target glibc if applicable (empty for native).
        :param default: If the toolset should be the new default.
        """
        if type(name) is not str or name in ["", None]:
            log.fatal(f"please give a name for adding a toolset.")
            exit(-666)
        if type(compiler_path) is not str or compiler_path in ["", None]:
            log.fatal(f"please give a compiler_path for adding a toolset.")
            exit(-666)
        log.debug(
            f"Adding toolset {name} with compiler {compiler_path}, abi {abi}, "
            f"os {os}, arch {arch}, glibc {glibc}, default {default}"
        )
        self.toolset_instance.add_toolset(
            name, compiler_path, abi, os, arch, glibc, default
        )

    def delete(self, name: str):
        """
        Remove a remote from the list.
        :param name: Remote's name.
        """
        if type(name) is not str or name in ["", None]:
            log.fatal(f"please give a name for removing a toolset.")
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
    rem = ToolsetCommand(system)
    if args.what in deprecated.keys():
        log.warn(
            f"WARNING {args.what} is deprecated; use {deprecated[args.what]} instead."
        )
    if args.what in ["list", "ls"]:
        rem.list()
    elif args.what == "add":
        rem.add(
            name=args.name,
            compiler_path=args.compiler,
            abi=args.abi,
            default=args.default,
        )
    elif args.what in ["del", "rm"]:
        rem.delete(args.name)


def add_toolset_parameters(sub_parsers):
    """
    Definition of toolset parameters.
    :param sub_parsers: The parent parser.
    """
    from api.internal.common import (
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
        "--name", "-n", type=str, default="", help="The toolset name."
    )
    info_parser.add_argument(
        "--abi",
        "-b",
        type=str,
        default="",
        help="The abi if different from the compiler's default.",
    )
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
