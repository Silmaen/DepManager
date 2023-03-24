"""
Build command.
"""

from sys import stderr
from pathlib import Path


def build(args, system=None):
    """
    Entry point for build command.
    :param args: Command Line Arguments.
    :param system: The local system.
    """
    from depmanager.api.builder import Builder
    location = Path(args.location).resolve()
    if not location.exists():
        print(f"ERROR location {location} does not exists.", file=stderr)
        exit(-666)
    if not location.is_dir():
        print(f"ERROR location {location} must be a folder.", file=stderr)
        exit(-666)
    builder = Builder(location, local=system)
    if not builder.has_recipes():
        print(f"ERROR: no recipe found in {location}", file=stderr)
        exit(-666)
    print(f"found {len(builder.recipes)} in the given source folder")
    for rep in builder.recipes:
        print(f" - {rep.to_str()}")
    builder.build_all(args.force)


def add_build_parameters(sub_parsers):
    """
    Definition of build parameters.
    :param sub_parsers: The parent parser.
    """
    build_parser = sub_parsers.add_parser("build")
    build_parser.description = "Tool to build a package from source"
    build_parser.add_argument(
            "location",
            type=str,
            help="The location of sources. Must contain a pythonclass derived from Recipe.")
    build_parser.add_argument(
            "--force", "-f",
            action="store_true",
            help="Force build even if the dependency already exists in the database."
    )
    build_parser.set_defaults(func=build)
