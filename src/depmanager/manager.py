#!/usr/bin/env python3
"""
Main entrypoint for library manager
"""
from api.internal.messaging import set_logging_level, set_raw_output


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
    from command.info import add_info_parameters

    add_info_parameters(sub_parsers)
    # ============================ REMOTE =============================================
    from command.remote import add_remote_parameters

    add_remote_parameters(sub_parsers)
    # ============================== GET ==============================================
    from command.get import add_get_parameters

    add_get_parameters(sub_parsers)
    # ============================= PACK ==============================================
    from command.pack import add_pack_parameters

    add_pack_parameters(sub_parsers)
    # ============================ BUILD ==============================================
    from command.build import add_build_parameters

    add_build_parameters(sub_parsers)
    # ============================ LOAD ==============================================
    from command.load import add_load_parameters

    add_load_parameters(sub_parsers)
    # ============================ TOOLSET ==============================================
    from command.toolset import add_toolset_parameters

    add_toolset_parameters(sub_parsers)

    args = parser.parse_args()
    if args.command in ["", None]:
        parser.print_help()
    else:
        from api.local import LocalManager

        logging_level = args.verbose + 2
        if args.quiet:
            logging_level = 0
        set_logging_level(logging_level)
        set_raw_output(args.raw)
        local = LocalManager()
        ret = args.func(args, local)
        if ret is None:
            ret = 0
        local.clean_tmp()
        return ret


if __name__ == "__main__":
    exit(main())
