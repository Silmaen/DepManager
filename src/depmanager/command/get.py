"""
The get subcommand
"""


def get(args):
    """
    Entrypoint for the get subcommand
    :param args: the command line arguments
    """
    from depmanager.internal.common import query_argument_to_dict
    from depmanager.api.package import PackageManager
    local = PackageManager()
    deps = local.query(query_argument_to_dict(args))
    print(deps[0].get_cmake_config_dir())


def get_arguments(sub_parsers):
    """
    Defines the get arguments
    :param sub_parsers: the parser
    """
    from depmanager.internal.common import add_query_arguments
    get_parser = sub_parsers.add_parser("get")
    get_parser.description = "Tool to get cmake config path for dependency in the library"
    add_query_arguments(get_parser)
    get_parser.set_defaults(func=get)
