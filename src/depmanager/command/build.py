"""
Build command.
"""

from pathlib import Path
from sys import stderr

from depmanager.api.builder import Builder


def build(args, system=None):
    """
    Entry point for build command.
    :param args: Command Line Arguments.
    :param system: The local system.
    """

    location = Path(args.location).resolve()
    if not location.exists():
        print(f"ERROR location {location} does not exists.", file=stderr)
        exit(-666)
    if not location.is_dir():
        print(f"ERROR location {location} must be a folder.", file=stderr)
        exit(-666)
    cross_info = {}
    if args.cross_c not in ["", None]:
        cross_info["C_COMPILER"] = args.cross_c
    if args.cross_cxx not in ["", None]:
        cross_info["CXX_COMPILER"] = args.cross_cxx
    if args.cross_arch not in ["", None]:
        cross_info["CROSS_ARCH"] = args.cross_arch
    if args.cross_os not in ["", None]:
        cross_info["CROSS_OS"] = args.cross_os
    cross_info["SINGLE_THREAD"] = args.single_thread

    depth = args.recursive_depth
    if args.recursive:
        depth = -1
    print(f"Search recursive until {depth}")
    builder = Builder(location, local=system, depth=depth, cross_info=cross_info)
    if not builder.has_recipes():
        print(f"ERROR: no recipe found in {location}", file=stderr)
        exit(-666)
    print(f"found {len(builder.recipes)} in the given source folder")
    # for rep in builder.recipes:
    #     print(f" - {rep.to_str()}")
    # error_count = builder.build_all(args.force)
    # if error_count > 0:
    #     exit(-666)


def add_build_parameters(sub_parsers):
    """
    Definition of build parameters.
    :param sub_parsers: The parent parser.
    """
    from depmanager.api.internal.common import add_common_arguments

    build_parser = sub_parsers.add_parser("build")
    build_parser.description = "Tool to build a package from source"
    add_common_arguments(build_parser)  # add -v
    build_parser.add_argument(
        "location",
        type=str,
        help="The location of sources. Must contain a pythonclass derived from Recipe.",
    )
    build_parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Recursive search for recipes. allow to search in the <location> and all it subdirectories.",
    )
    build_parser.add_argument(
        "--recursive-depth",
        "-d",
        type=int,
        default=0,
        help="Recursive search for recipes with fixed depth. Allow to search in the <location> and depth sub-folders.",
    )
    build_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force build, even if the dependency already exists in the database.",
    )
    build_parser.add_argument(
        "--cross-c", type=str, default="", help="Define the cross compiler for C."
    )
    build_parser.add_argument(
        "--cross-cxx", type=str, default="", help="Define the cross compiler for C++."
    )
    build_parser.add_argument(
        "--cross-arch", type=str, default="", help="Define the cross archi."
    )
    build_parser.add_argument(
        "--cross-os", type=str, default="", help="Define the cross OS."
    )
    build_parser.add_argument(
        "--single-thread",
        "-s",
        action="store_true",
        default="",
        help="Force the use of single thread.",
    )
    build_parser.set_defaults(func=build)
