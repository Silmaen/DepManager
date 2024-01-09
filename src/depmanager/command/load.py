"""
The load subcommand
"""
from pathlib import Path
from sys import stderr

from depmanager.api.load import load_environment


def load(args, system=None):
    """
    Load entrypoint.
    :param args: The command line arguments.
    :param system: The local system.
    """
    try:
        # check arguments.
        arg_check = True
        config = Path()
        if args.config in ["", None]:
            print(f"Error in loading environment: Config path is empty.", file=stderr)
            arg_check = False
        else:
            config = Path(args.config).resolve()
            if not config.exists():
                print(
                    f"Error in loading environment: Config path does not exists.",
                    file=stderr,
                )
                arg_check = False
            if config.is_dir():
                if (config / "depmanager.yml").exists():
                    config = config / "depmanager.yml"
                else:
                    print(
                        f"Error in loading environment: Config path is a folder not containing 'depmanager.yml.",
                        file=stderr,
                    )
                    arg_check = False
        if args.kind not in ["static", "shared"]:
            print(
                f"Error in loading environment: default kind must be 'static' or 'shared'.",
                file=stderr,
            )
            arg_check = False
        if args.os not in ["Linux", "Windows"]:
            print(
                f"Error in loading environment: os unsupported, valid are 'Linux', 'Windows'.",
                file=stderr,
            )
            arg_check = False
        if args.arch not in ["x86_64", "aarch64"]:
            print(
                f"Error in loading environment: arch unsupported, valid are 'x86_64', 'aarch64'.",
                file=stderr,
            )
            arg_check = False
        if args.compiler not in ["gnu", "msvc"]:
            print(
                f"Error in loading environment: compiler unsupported, valid are 'gnu', 'msvc'.",
                file=stderr,
            )
            arg_check = False
        if not arg_check:
            exit(22)
        err_code, result = load_environment(
            system, config, args.kind, args.os, args.arch, args.compiler, args.glibc
        )
        # finding everything
        print(result)
        return err_code
    except Exception as err:
        print(f"Error in loading environment: {err}", file=stderr)
        exit(23)


def add_load_parameters(sub_parsers):
    """
    Defines the get arguments
    :param sub_parsers: the parser
    """
    from depmanager.api.internal.common import add_common_arguments

    load_parser = sub_parsers.add_parser("load")
    load_parser.description = "Tool to load cmake config based on config file."

    load_parser.set_defaults(func=load)
    add_common_arguments(load_parser)  # add -v
    load_parser.add_argument(
        "--config",
        type=str,
        help="Path to the YAML config file.",
        default="",
    )
    load_parser.add_argument(
        "--kind",
        "-k",
        type=str,
        choices=["static", "shared", "header", "any", "*"],
        help="Library's kind to search (* for any)",
        default="",
    )
    load_parser.add_argument(
        "--os",
        "-o",
        type=str,
        choices=["Linux", "Windows"],
        help="Operating system of the packet to search, use * as wildcard",
        default="",
    )
    load_parser.add_argument(
        "--arch",
        "-a",
        type=str,
        choices=["x86_64", "aarch64"],
        help="CPU architecture of the packet to search, use * as wildcard",
        default="",
    )
    load_parser.add_argument(
        "--compiler",
        "-c",
        type=str,
        choices=["gnu", "msvc"],
        help="Compiler of the packet to search, use * as wildcard",
        default="",
    )
    load_parser.add_argument(
        "--glibc",
        "-g",
        type=str,
        help="Minimal version of glibc, use * as wildcard",
        default="*",
    )
