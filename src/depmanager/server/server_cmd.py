"""
Management of the package server
"""


def server(args):
    from depmanager.server.server import Server
    if args.config not in ["", None]:
        srv = Server(args.config)
    else:
        srv = Server()
    if args.command == "start":
        srv.run()


def server_arguments(sub_parsers):
    search_parser = sub_parsers.add_parser("server")
    search_parser.description = "Server side for dependency in the library"
    search_parser.add_argument(
        "command",
        type=str,
        choices=["start"],
        help="The command")
    search_parser.add_argument(
        "--config", "-c",
        type=str,
        default="",
        help="Path to config file"
    )
    search_parser.set_defaults(func=server)


