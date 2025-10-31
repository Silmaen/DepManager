"""
Pack command
"""

from copy import deepcopy
from pathlib import Path
from sys import stderr

from depmanager.api.internal.messaging import log, message

possible_info = ["pull", "push", "add", "del", "rm", "query", "ls", "clean"]
deprecated = {"del": "rm", "query": "ls"}


def pack(args, system=None):
    """
    Entry point for pack command.
    :param args: Command Line Arguments.
    :param system: The local system
    """
    from depmanager.api.internal.common import query_argument_to_dict
    from depmanager.api.package import PackageManager

    pacman = PackageManager(system)
    if args.what not in possible_info:
        return
    if args.what in deprecated.keys():
        log.warn(
            f"WARNING {args.what} is deprecated; use {deprecated[args.what]} instead."
        )
    remote_name = pacman.remote_name(args)
    # --- parameters check ----
    if args.default and args.name not in [None, ""]:
        log.warn("WARNING: No need for name if default set, using default.")
    if remote_name == "":
        if args.default:
            log.warn("WARNING: No Remotes defined.")
        if args.name not in [None, ""]:
            log.warn(f"WARNING: Remotes '{args.name}' not in remotes lists.")
    if args.what in ["add", "clean"] and remote_name != "":
        log.fatal(
            f"{args.what} command only work on local database. please do not defined remote."
        )
        exit(-666)
    if args.what in ["push", "pull"] and remote_name == "":
        args.default = True
        remote_name = pacman.remote_name(args)
        if remote_name == "":
            log.fatal(
                f"{args.what} command work by linking to a remote, please define a remote."
            )
            exit(-666)
    transitivity = False
    if args.what == "query":
        if args.transitive:
            transitivity = True
    if args.what == "add":
        if args.source in [None, ""]:
            log.fatal(f"please provide a source for package adding.")
            exit(-666)
        source_path = Path(args.source).resolve()
        if not source_path.exists():
            log.fatal(f"source path {source_path} does not exists.")
            exit(-666)
        if source_path.is_dir() and not (source_path / "edp.info").exists():
            log.fatal(
                f"source path folder {source_path} does not contains 'edp.info' file."
            )
            exit(-666)
        if source_path.is_file():
            suffixes = []
            if len(source_path.suffixes) > 0:
                suffixes = [source_path.suffixes[-1]]
                if suffixes == [".gz"] and len(source_path.suffixes) > 1:
                    suffixes = [source_path.suffixes[-2], source_path.suffixes[-1]]
            if suffixes not in [[".zip"], [".tgz"], [".tar", ".gz"]]:
                log.fatal(f"source file {source_path} is in unsupported format.")
                exit(-666)

        # --- treat command ---
        pacman.add_from_location(source_path)
        return
    query = query_argument_to_dict(args)
    if args.what == "push":
        deps = pacman.query(query)
    else:
        deps = pacman.query(query, remote_name, transitivity)
    if args.what in ["query", "ls"]:
        message("List of matching packages:")
        pacman.get_default_remote()
        for dep in deps:
            default_mark = ["", "*"][dep.get_source() == pacman.get_default_remote()]
            message(f"[{default_mark}{dep.get_source()}] {dep.properties.get_as_str()}")
        return
    if args.what == "clean":
        log.info(
            f"Do a {['','full '][args.full]} Cleaning of the local package repository."
        )
        if args.full:
            for dep in deps:
                log.info(f"Remove package {dep.properties.get_as_str()}")
                pacman.remove_package(dep, remote_name)
        else:
            for dep in deps:
                props = dep.properties
                props.version = "*"
                result = pacman.query(props, remote_name)
                if len(result) < 2:
                    log.info(f"Keeping package {dep.properties.get_as_str()}")
                    continue
                if result[0].version_greater(dep):
                    log.ingo(f"Remove package {dep.properties.get_as_str()}")
                    pacman.remove_package(dep, remote_name)
                else:
                    log.info(f"Keeping package {dep.properties.get_as_str()}")
        return
    if args.what in ["rm", "del", "pull", "push"]:
        if len(deps) == 0:
            log.warn("WARNING: No package matching the query.", file=stderr)
            return
        if len(deps) > 1 and not args.recurse:
            log.warn("WARNING: More than one package match the query, please precise:")
            for dep in deps:
                message(f"{dep.properties.get_as_str()}")
            return
        for dep in deps:
            if args.what in ["del", "rm"]:
                pacman.remove_package(dep, remote_name)
                continue
            props = deepcopy(dep.properties)
            props.version = "*"
            result = pacman.query(props, remote_name)
            if len(result) >= 2 and result[0].version_greater(dep):
                continue
            if args.what == "pull":
                pacman.add_from_remote(dep, remote_name)
            elif args.what == "push":
                pacman.add_to_remote(dep, remote_name)
        return
    log.warn(f"Command {args.what} is not yet implemented")


def add_pack_parameters(sub_parsers):
    """
    Definition of pack parameters.
    :param sub_parsers: The parent parser.
    """
    from depmanager.api.internal.common import (
        add_query_arguments,
        add_remote_selection_arguments,
        add_common_arguments,
    )

    pack_parser = sub_parsers.add_parser("pack")
    pack_parser.description = "Tool to search for dependency in the library"
    pack_parser.add_argument(
        "what",
        type=str,
        choices=possible_info,
        help="The information you want about the program",
    )
    add_common_arguments(pack_parser)  # add -v
    add_query_arguments(pack_parser)  # add -p -k -o -a -b
    add_remote_selection_arguments(pack_parser)  # add -n, -d
    pack_parser.add_argument(
        "--source",
        "-s",
        type=str,
        default="",
        help="""Location of the package to add. Provide a folder (with an edp.info file) of an archive.
            supported archive format: zip, tar.gz or tgz.
            """,
    )
    pack_parser.add_argument(
        "--recurse",
        "-r",
        action="store_true",
        default=False,
        help="""Allow operation on multiple packages.""",
    )
    pack_parser.add_argument(
        "--full",
        "-f",
        action="store_true",
        default=False,
        help="""Do a full cleaning, removing all local packages.""",
    )
    pack_parser.set_defaults(func=pack)
