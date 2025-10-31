#!/usr/bin/env python3
"""
Main entrypoint for library manager
"""
from depmanager.api.internal.messaging import set_logging_level


def main():
    """
    Main entrypoint for command-line use of manager
    :return:
    """
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Dependency manager used alongside with cmake")
    sub_parsers = parser.add_subparsers(
        title="Sub Commands", help="Sub command Help", dest="command", required=True
    )
    # ============================= INFO ==============================================
    from depmanager.command.info import add_info_parameters

    add_info_parameters(sub_parsers)
    # ============================ REMOTE =============================================
    from depmanager.command.remote import add_remote_parameters

    add_remote_parameters(sub_parsers)
    # ============================== GET ==============================================
    from depmanager.command.get import add_get_parameters

    add_get_parameters(sub_parsers)
    # ============================= PACK ==============================================
    from depmanager.command.pack import add_pack_parameters

    add_pack_parameters(sub_parsers)
    # ============================ BUILD ==============================================
    from depmanager.command.build import add_build_parameters

    add_build_parameters(sub_parsers)
    # ============================ LOAD ==============================================
    from depmanager.command.load import add_load_parameters

    add_load_parameters(sub_parsers)
    # ============================ TOOLSET ==============================================
    from depmanager.command.toolset import add_toolset_parameters

    add_toolset_parameters(sub_parsers)

    args = parser.parse_args()
    if args.command in ["", None]:
        parser.print_help()
    else:
        from depmanager.api.local import LocalManager

        logging_level = args.verbose + 2
        if args.quiet:
            logging_level = 0
        set_logging_level(logging_level)
        local = LocalManager()
        args.func(args, local)
        local.clean_tmp()


if __name__ == "__main__":
    main()
