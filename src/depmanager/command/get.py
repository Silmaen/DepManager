"""
The get subcommand
"""


def get(args, system=None):
    """
    Get entrypoint.
    :param args: The command line arguments.
    :param system: The local system.
    """
    from depmanager.api.internal.common import query_argument_to_dict
    from depmanager.api.package import PackageManager

    pack_manager = PackageManager(system)
    deps = pack_manager.query(query_argument_to_dict(args), "")
    if len(deps) > 0:
        print(deps[0].get_cmake_config_dir())
        return
    # If not found... search and get from remote.
    rep = pack_manager.query(query_argument_to_dict(args), system.default_remote)
    if len(rep) != 0:
        pack_manager.add_from_remote(rep[0], system.default_remote)
        deps = pack_manager.query(query_argument_to_dict(args), "")
        if len(deps) > 0:
            print(deps[0].get_cmake_config_dir())


def add_get_parameters(sub_parsers):
    """
    Defines the get arguments
    :param sub_parsers: the parser
    """
    from depmanager.api.internal.common import add_query_arguments, add_common_arguments

    get_parser = sub_parsers.add_parser("get")
    get_parser.description = (
        "Tool to get cmake config path for dependency in the library"
    )
    add_common_arguments(get_parser)  # add -v
    add_query_arguments(get_parser)
    get_parser.set_defaults(func=get)
