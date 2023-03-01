#!/usr/bin/env python3
"""
Main entrypoint for library manager
"""


def main():
    """
    Main entrypoint for command-line use of manager
    :return:
    """
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Dependency manager to be used alongside with cmake"
    )
    # parser.add_argument("--verbose", "-v", action='count', default=0)
    sub_parsers = parser.add_subparsers(
        title="Sub Commands",
        help="Sub command Help",
        dest="command",
        required=True
    )
    # ============================= INFO ==============================================
    from depmanager.command.info import add_info_parameters
    add_info_parameters(sub_parsers)
    # ============================ REMOTE =============================================
    from depmanager.command.remote import add_remote_parameters
    add_remote_parameters(sub_parsers)
    # ============================ SERVER =============================================
    from depmanager.command.server import add_server_parameters
    add_server_parameters(sub_parsers)


    # ===========================================================================
    from depmanager.internal.search import search_arguments
    search_arguments(sub_parsers)
    # ===========================================================================
    from depmanager.internal.info import info_arguments
    info_arguments(sub_parsers)
    # ===========================================================================
    from depmanager.internal.add import add_arguments
    add_arguments(sub_parsers)
    # ===========================================================================
    from depmanager.server.server_cmd import server_arguments
    server_arguments(sub_parsers)
    # ===========================================================================
    from depmanager.internal.remote import remote_arguments
    remote_arguments(sub_parsers)
    # ===========================================================================
    args = parser.parse_args()
    if args.command in ["", None]:
        parser.print_help()
    else:
        args.func(args)


if __name__ == "__main__":
    main()
