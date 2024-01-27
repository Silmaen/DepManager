"""
Pack command
"""
from pathlib import Path
from sys import stderr

possible_info = ["pull", "push", "add", "del", "query", "clean"]


def pack(args, system=None):
    """
    Entry point for pack command.
    :param args: Command Line Arguments.
    :param system: The local system
    """
    from depmanager.api.internal.common import query_argument_to_dict
    from depmanager.api.package import PackageManager

    pacman = PackageManager(system, args.verbose)
    if args.what not in possible_info:
        return
    remote_name = pacman.remote_name(args)
    # --- parameters check ----
    if args.default and args.name not in [None, ""]:
        print("WARNING: No need for name if default set, using default.", file=stderr)
    if remote_name == "":
        if args.default:
            print("WARNING: No Remotes defined.", file=stderr)
        if args.name not in [None, ""]:
            print(f"WARNING: Remotes '{args.name}' not in remotes lists.", file=stderr)
    if args.what in ["add", "clean"] and remote_name != "":
        print(
            f"ERROR: {args.what} command only work on local database. please do not defined remote.",
            file=stderr,
        )
        exit(-666)
    if args.what in ["push", "pull"] and remote_name == "":
        args.default = True
        remote_name = pacman.remote_name(args)
        if remote_name == "":
            print(
                f"ERROR: {args.what} command work by linking to a remote, please define a remote.",
                file=stderr,
            )
            exit(-666)
    transitivity = False
    if args.what == "query":
        if args.transitive:
            transitivity = True
    if args.what == "add":
        if args.source in [None, ""]:
            print(f"ERROR: please provide a source for package adding.", file=stderr)
            exit(-666)
        source_path = Path(args.source).resolve()
        if not source_path.exists():
            print(f"ERROR: source path {source_path} does not exists.", file=stderr)
            exit(-666)
        if source_path.is_dir() and not (source_path / "edp.info").exists():
            print(
                f"ERROR: source path folder {source_path} does not contains 'edp.info' file.",
                file=stderr,
            )
            exit(-666)
        if source_path.is_file():
            suffixes = []
            if len(source_path.suffixes) > 0:
                suffixes = [source_path.suffixes[-1]]
                if suffixes == [".gz"] and len(source_path.suffixes) > 1:
                    suffixes = [source_path.suffixes[-2], source_path.suffixes[-1]]
            if suffixes not in [[".zip"], [".tgz"], [".tar", ".gz"]]:
                print(
                    f"ERROR: source file {source_path} is in unsupported format.",
                    file=stderr,
                )
                exit(-666)

        # --- treat command ---
        pacman.add_from_location(source_path)
        return
    query = query_argument_to_dict(args)
    if args.what == "push":
        deps = pacman.query(query)
    else:
        deps = pacman.query(query, remote_name, transitivity)
    if args.what == "query":
        for dep in deps:
            print(f"[{dep.get_source()}] {dep.properties.get_as_str()}")
        return
    if args.what == "clean":
        if args.full:
            for dep in deps:
                pacman.remove_package(dep, remote_name)
        else:
            for dep in deps:
                props = dep.properties
                props.version = "*"
                result = pacman.query(props, remote_name)
                if len(result) < 2:
                    continue
                if result[0].version_greater(dep):
                    pacman.remove_package(dep, remote_name)
        return
    if args.what in ["del", "pull", "push"]:
        if len(deps) == 0:
            print("WARNING: No package matching the query.", file=stderr)
            return
        if len(deps) > 1 and not args.recurse:
            print(
                "WARNING: More than one package match the query, please precise:",
                file=stderr,
            )
            for dep in deps:
                print(f"{dep.properties.get_as_str()}")
            return
        for dep in deps:
            if args.what == "del":
                pacman.remove_package(dep, remote_name)
                continue
            props = dep.properties
            props.version = "*"
            result = pacman.query(props, remote_name)
            if len(result) >= 2 and result[0].version_greater(dep):
                continue
            if args.what == "pull":
                pacman.add_from_remote(dep, remote_name)
            elif args.what == "push":
                pacman.add_to_remote(dep, remote_name)
        return
    print(f"Command {args.what} is not yet implemented", file=stderr)


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
    add_query_arguments(pack_parser)  # add -p -k -o -a -c
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
