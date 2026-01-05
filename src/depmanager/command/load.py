"""
The load subcommand
"""

from pathlib import Path

from api.internal.messaging import log, message, set_logging_level
from api.load import load_environment


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
            log.error(f"Loading environment: Config path is empty.")
            arg_check = False
        else:
            config = Path(args.config).resolve()
            if not config.exists():
                log.error(f"Loading environment: Config path does not exists.")
                arg_check = False
            if config.is_dir():
                if (config / "depmanager.yml").exists():
                    config = config / "depmanager.yml"
                else:
                    log.error(
                        f"Loading environment: Config path is a folder not containing 'depmanager.yml."
                    )
                    arg_check = False
        if args.kind not in ["static", "shared"]:
            log.error(
                f"Loading environment: default kind must be 'static' or 'shared'."
            )
            arg_check = False
        if args.os not in ["Linux", "Windows"]:
            log.error(
                f"Loading environment: os unsupported, valid are 'Linux', 'Windows'."
            )
            arg_check = False
        if args.arch not in ["x86_64", "aarch64"]:
            log.error(
                f"Loading environment: arch unsupported, valid are 'x86_64', 'aarch64'."
            )
            arg_check = False
        if args.abi not in ["gnu", "llvm", "msvc"]:
            log.error(
                f"Loading environment: abi unsupported, valid are 'gnu', 'llvm', 'msvc'."
            )
            arg_check = False
        if not arg_check:
            exit(22)
        if args.info:
            set_logging_level(3)
        err_code, result = load_environment(
            system,
            config,
            args.kind,
            args.os,
            args.arch,
            args.abi,
            args.glibc,
        )
        # finding everything
        if not args.info:
            message(f"{result}")
        return err_code
    except Exception as err:
        log.fatal(f"Loading environment: {err}")
        exit(23)


def add_load_parameters(sub_parsers):
    """
    Defines the get arguments
    :param sub_parsers: the parser
    """
    from api.internal.common import add_common_arguments

    load_parser = sub_parsers.add_parser("load")
    load_parser.description = "Tool to load cmake config based on config file."

    load_parser.set_defaults(func=load)
    add_common_arguments(load_parser)  # add -v
    load_parser.add_argument(
        "--info", action="store_true", default=False, help="Print info messages"
    )
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
        "--abi",
        "-b",
        type=str,
        choices=["gnu", "llvm", "msvc"],
        help="Abi of the packet to search, use * as wildcard",
        default="",
    )
    load_parser.add_argument(
        "--glibc",
        "-g",
        type=str,
        help="Minimal version of glibc, use * as wildcard",
        default="*",
    )
