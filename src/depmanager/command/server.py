"""
Management of the package server
"""


def server(args):
    """
    Entry point for server command.
    :param args: Command Line Arguments.
    """
    from depmanager.server.server import Server
    if args.config not in ["", None]:
        srv = Server(args.config)
    else:
        srv = Server()
    if args.command == "start":
        srv.run()


def add_server_parameters(sub_parsers):
    """
    Definition of server parameters.
    :param sub_parsers: The parent parser.
    """
    server_parser = sub_parsers.add_parser("server")
    server_parser.description = "Server side for dependency in the library"
    server_parser.add_argument(
        "command",
        type=str,
        choices=["start"],
        help="The command")
    server_parser.add_argument(
        "--config", "-c",
        type=str,
        default="",
        help="Path to config file"
    )
    server_parser.set_defaults(func=server)


