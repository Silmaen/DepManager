"""
Manage the remotes
"""
from sys import stderr

possible_remote = ["list", "add", "del", "sync", "info"]


class RemoteCommand:
    """
    Managing remotes
    """

    def __init__(self, verbosity=0, system=None):
        from depmanager.api.remotes import RemotesManager

        self.remote_instance = RemotesManager(system, verbosity)
        self.verbosity = verbosity

    def list(self):
        """
        Lists the defined remotes.
        """
        remotes = self.remote_instance.get_remote_list()
        for key, value in remotes.items():
            default = [" ", "*"][value.default]
            if self.verbosity == 0:
                print(f" {default} {key}")
            else:
                status = ["OFFLINE", "ONLINE "][value.valid_shape]
                print(
                    f" {default} [ {status} ] {key} - {value.kind}, {value.destination}"
                )

    def add(
        self,
        name: str,
        url: str,
        default: bool = False,
        login: str = "",
        passwd: str = "",
    ):
        """
        Add a remote to the list or modify the existing one.
        :param name: Remote's name.
        :param url: Remote's url
        :param default: If this remote should become the new default
        :param login: Credential to use for connexion.
        :param passwd: Password for connexion.
        """
        if type(name) is not str or name in ["", None]:
            print(
                f"ERROR please give a name for adding/modifying a remote.", file=stderr
            )
            exit(-666)
        if url in [None, ""]:
            print(
                f"ERROR please give an url for adding/modifying a remote.", file=stderr
            )
            exit(-666)
        if "://" not in url:
            print(f"ERROR '{url}' is not a valid url.", file=stderr)
            print(
                f"  Valid input are in the form: <kind>://<url>/<folder>.", file=stderr
            )
            exit(-666)
        kind, pure_url = url.split("://", 1)
        if ":" in pure_url:
            pure_url, port = pure_url.rsplit(":", 1)
            port = int(port)
        else:
            port = -1
        if kind not in self.remote_instance.get_supported_remotes():
            print(f"ERROR '{kind}' is not a valid type of url.", file=stderr)
            print(
                f"  Valid types are {self.remote_instance.get_supported_remotes()}.",
                file=stderr,
            )
            exit(-666)
        self.remote_instance.add_remote(
            name, pure_url, port, default, kind, login, passwd
        )

    def delete(self, name: str):
        """
        Remove a remote from the list.
        :param name: Remote's name.
        """
        if type(name) is not str or name in ["", None]:
            print(f"ERROR please give a name for removing a remote.", file=stderr)
            exit(-666)
        self.remote_instance.remove_remote(name)

    def sync(
        self,
        name: str,
        default: bool = False,
        pull_newer: bool = True,
        push_newer: bool = True,
        dry_run: bool = False,
    ):
        """
        Synchronize local with given remote (push/pull with server all newer package).
        :param name: Remote's name.
        :param default: If using default remote
        :param pull_newer: Pull images if newer version exists
        :param push_newer: Push images if newer version exists
        :param dry_run: Do checks but no transfer.
        """
        self.remote_instance.sync_remote(name, default, pull_newer, push_newer, dry_run)

    def info(self, name: str, default: bool = False):
        """
        Print info of the designated remote.
        :param name: Remote's name.
        :param default: If using default remote
        """
        remote_srv = self.remote_instance.get_safe_remote(name, default)
        name = self.remote_instance.get_safe_remote_name(name, default)
        if remote_srv is None:
            print(
                f"ERROR the information provided does not designate a remote.",
                file=stderr,
            )
            exit(-666)
        version = remote_srv.get_server_version()
        r_type = remote_srv.get_server_type()
        print(f"Remote server: {name}, type: {r_type}, version: {version}.")


def remote(args, system=None):
    """
    Remote entrypoint.
    :param args: Command Line Arguments.
    :param system: The local system
    """
    if args.what not in possible_remote:
        return
    rem = RemoteCommand(args.verbose, system)
    if args.what == "list":
        rem.list()
    elif args.what == "add":
        rem.add(args.name, args.url, args.default, args.login, args.passwd)
    elif args.what == "del":
        rem.delete(args.name)
    elif args.what == "sync":
        dry_run = False
        do_pull = True
        do_push = True
        if args.push_only:
            do_pull = False
        if args.pull_only:
            do_push = False
        if args.dry_run:
            dry_run = True
        if not (do_push or do_pull):
            print("ERROR: push-only & pull-only are mutually exclusive.", file=stderr)
            exit(1)
        rem.sync(args.name, args.default, do_pull, do_push, dry_run)
    elif args.what == "info":
        rem.info(args.name, args.default)


def add_remote_parameters(sub_parsers):
    """
    Definition of remote parameters.
    :param sub_parsers: The parent parser.
    """
    from depmanager.api.internal.common import (
        add_common_arguments,
        add_remote_selection_arguments,
    )

    info_parser = sub_parsers.add_parser("remote")
    info_parser.description = "Tool to search for dependency in the library"
    info_parser.add_argument(
        "what",
        type=str,
        choices=possible_remote,
        help="The information you want about the program",
    )
    add_common_arguments(info_parser)  # add -v
    add_remote_selection_arguments(info_parser)  # add -n, -d
    info_parser.add_argument("--url", "-u", type=str, help="URL of the remote.")
    info_parser.add_argument(
        "--login", "-l", type=str, default="", help="Login to use."
    )
    info_parser.add_argument("--passwd", "-p", type=str, default="", help="Password.")
    info_parser.add_argument(
        "--push-only",
        action="store_true",
        default=False,
        help="Do only the push actions in sync.",
    )
    info_parser.add_argument(
        "--pull-only",
        action="store_true",
        default=False,
        help="Do only the pull actions in sync.",
    )
    info_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="During sync, do the checks, but no transfer.",
    )
    info_parser.set_defaults(func=remote)
