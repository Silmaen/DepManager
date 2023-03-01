"""
Manage the remotes
"""

possible_remote = ["list", "add", "del"]


class RemoteCommand:
    """
    Managing remotes
    """

    def __init__(self, verbosity=0):
        from depmanager.api.remotes import RemotesManager
        self.remote_instance = RemotesManager()
        self.verbosity = verbosity

    def list(self):
        """
        Lists the defined remotes.
        """
        remotes = self.remote_instance.get_remote_list()
        for key, value in remotes.items():
            default = [' ', '*'][value['default']]
            if self.verbosity == 0:
                print(F" {default} {key}")
            else:
                print(F" {default} [ {['OFFLINE', 'ONLINE '][self.remote_instance.is_remote_online(key)]} ] {key} - {value['url']}")

    def add(self, name: str, url: str, default: bool = False):
        """
        Add a remote to the list.
        :param name: Remote's name.
        :param url: Remote's url
        :param default: If this remote should become the new default
        """
        self.remote_instance.add_remote(name, url, default)

    def delete(self, name: str):
        """
        Remove a remote from the list.
        :param name: Remote's name.
        """
        self.remote_instance.remove_remote(name)


def remote(args):
    """
    Entry point for remote command.
    :param args: Command Line Arguments.
    """
    if args.what not in possible_remote:
        return
    rem = RemoteCommand(args.verbosity)
    if args.what == "list":
        rem.list()
    elif args.what == "add":
        rem.add(args.name, args.url, args.default)
    elif args.what == "del":
        rem.delete(args.name)


def add_remote_parameters(sub_parsers):
    """
    Definition of remote parameters.
    :param sub_parsers: The parent parser.
    """
    info_parser = sub_parsers.add_parser("remote")
    info_parser.description = "Tool to search for dependency in the library"
    info_parser.add_argument(
        "what",
        type=str,
        choices=possible_remote,
        help="The information you want about the program")
    info_parser.add_argument(
        "--name", "-n",
        type=str,
        help="Name of the remote"
    )
    info_parser.add_argument(
        "--url", "-u",
        type=str,
        help="URL of the remote"
    )
    info_parser.add_argument(
        "--default", "-d",
        action="store_true",
        help="If the new remote should be the default"
    )
    info_parser.set_defaults(func=remote)
