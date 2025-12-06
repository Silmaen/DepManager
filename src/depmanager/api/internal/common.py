"""
Common helper function.
"""

from argparse import ArgumentParser

client_api = "2.1.0"


def add_common_arguments(parser: ArgumentParser):
    """
    Add the common option to the parser.
    :param parser: Where to add options.
    """
    parser.add_argument(
        "--verbose", "-v", action="count", default=0, help="The verbosity level"
    )
    parser.add_argument(
        "--quiet", action="store_true", default=False, help="Only error messages"
    )
    parser.add_argument("--raw", action="store_true", default=False, help="Raw output")


def add_remote_selection_arguments(parser: ArgumentParser):
    """
    Add the common option to the parser.
    :param parser: Where to add options.
    """
    parser.add_argument("--name", "-n", type=str, help="Name of the remote.")
    parser.add_argument(
        "--default",
        "-d",
        action="store_true",
        help="If the new remote should become the default.",
    )


def add_query_arguments(parser: ArgumentParser):
    """
    Add arguments related to query.
    :param parser: The parser for arguments.
    """
    parser.add_argument(
        "--predicate",
        "-p",
        type=str,
        help="Name/Version of the packet to search, use * as wildcard",
        default="*/*",
    )
    parser.add_argument(
        "--kind",
        "-k",
        type=str,
        choices=["static", "shared", "header", "any", "*"],
        help="Library's kind to search (* for any)",
        default="*",
    )
    parser.add_argument(
        "--os",
        "-o",
        type=str,
        help="Operating system of the packet to search, use * as wildcard",
        default="*",
    )
    parser.add_argument(
        "--arch",
        "-a",
        type=str,
        help="CPU architecture of the packet to search, use * as wildcard",
        default="*",
    )
    parser.add_argument(
        "--abi",
        "-b",
        type=str,
        help="Abi of the packet to search, use * as wildcard",
        default="*",
    )
    parser.add_argument(
        "--glibc",
        "-g",
        type=str,
        help="Minimal version of glibc, use * as wildcard",
        default="*",
    )
    parser.add_argument(
        "--build-date",
        type=str,
        help="Minimal build date, use * as wildcard",
        default="*",
    )
    parser.add_argument(
        "--transitive",
        "-t",
        action="store_true",
        help="Transitive query",
        default=False,
    )
    parser.add_argument(
        "--latest",
        "-l",
        action="store_true",
        help="Get only the latest version",
        default=False,
    )


def query_argument_to_dict(args):
    """
    Convert input argument into query dict.
    :param args: Input arguments.
    :return: Query dict.
    """
    if not "/" in args.predicate:
        name = args.predicate
        version = "*"
    else:
        name, version = args.predicate.split("/", 1)
    return {
        "name": name,
        "version": version,
        "os": args.os,
        "arch": args.arch,
        "kind": args.kind,
        "abi": args.abi,
        "glibc": args.glibc,
        "build_date": args.build_date,
        "transitive": args.transitive,
        "latest": args.latest,
    }


def pretty_size_print(raw_size):
    """
    Pretty print of sizes with units
    :param raw_size:
    :return:
    """
    for unite in ["B", "KB", "MB", "GB", "TB"]:
        if raw_size < 1024.0:
            break
        raw_size /= 1024.0
    return f"{raw_size:.2f} {unite}"
