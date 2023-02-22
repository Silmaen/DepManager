"""
Managing search command
"""
from sys import stderr


def search(args):
    """
    Treat search command.
    :param args:
    """
    if "/" not in args.predicate:
        print("ERROR: Predicate must be in the form of <name>/<version>, usr *,? as wildcard", file=stderr)
    name, version = args.predicate.split("/", 1)
    query = {
        "name": name,
        "version": version,
        "os":  args.os,
        "arch": args.arch,
        "lib_type": args.type,
        "compiler": args.compiler
    }
    if not args.remote_only or args.root:
        from depmanager.api.database import DataBase
        db = DataBase()
        result = db.search(name=name, version=version, os=args.os, arch=args.arch, lib_type=args.type,compiler=args.compiler)
        if args.root:
            if len(result) == 0:
                return
            if args.best:
                print(result[0].get_cmake_config_dir())
            else:
                for r in result:
                    print(r.get_cmake_config_dir())
            return
        print("Local:")
        if len(result) == 0:
            print(" - No results found -")
            return
        if args.best:
            r = result[0]
            print(r.get_as_str())
        else:
            for r in result:
                print(r.get_as_str())
    if not args.local_only and not args.root:
        from depmanager.internal.remote import Remotes
        from depmanager.internal.client import Client
        remotes = Remotes()
        if remotes.is_empty():
            return
        names = remotes.get_name_list()
        for name in names:
            print(f"{['-','*'][remotes.is_default(name)]}{name} ({remotes.get_url(name)})")
            cli = Client(remotes.get_url(name))
            cli.connect()
            if cli.status not in ["connected"]:
                print(f"  OFFLINE")
                continue
            result = cli.search(query)
            if len(result) == 0:
                print(" - No results found -")
                return
            if args.best:
                r = result[0]
                print(r.get_as_str())
            else:
                for r in result:
                    print(r.get_as_str())


def search_arguments(sub_parsers):
    """
    Defines the Search arguments
    :param sub_parsers: the parser
    """
    search_parser = sub_parsers.add_parser("search")
    search_parser.description = "Tool to search for dependency in the library"
    search_parser.add_argument(
        "--root", "-r",
        action="store_true",
        help="Only get the path to the cmake config",
        default=False
    )
    search_parser.add_argument(
        "--best", "-b",
        action="store_true",
        help="Output only one result that is the best one",
        default=False
    )
    search_parser.add_argument(
        "--predicate", "-p",
        type=str,
        help="Name/Version of the packet to search, use * as wildcard",
        default="*/*"
    )
    search_parser.add_argument(
        "--type", "-t",
        type=str,
        choices=["static", "shared", "header", "*"],
        help="Library type of the packet to search (* for any)",
        default="*"
    )
    search_parser.add_argument(
        "--os", "-o",
        type=str,
        help="Operating system of the packet to search, use * as wildcard",
        default="*"
    )
    search_parser.add_argument(
        "--arch", "-a",
        type=str,
        help="CPU architecture of the packet to search, use * as wildcard",
        default="*"
    )
    search_parser.add_argument(
        "--compiler", "-c",
        type=str,
        help="Compiler of the packet to search, use * as wildcard",
        default="*"
    )
    search_parser.add_argument(
        "--remote-name", "-n",
        type=str,
        help="The name of the remote to search",
        default=""
    )
    search_parser.add_argument(
        "--local-only", "-l",
        action="store_true",
        help="Avoid searching in remotes",
        default=False
    )
    search_parser.add_argument(
        "--remote-only", "-d",
        action="store_true",
        help="Avoid searching in local database",
        default=False
    )
    search_parser.set_defaults(func=search)
