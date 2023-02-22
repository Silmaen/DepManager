"""
manage remotes
"""
import time
from sys import stderr

possible_remote = ["add", "remove", "list", "default", "send"]


def remote(args):
    """
    Entry point for the remote command.
    :param args: command line arguments.
    """
    if args.remote_command not in possible_remote:
        return
    remote_obj = Remotes()
    if args.remote_command == "list":
        remote_obj.list(args.verbose)
        return
    if args.remote_command == "add":
        if args.name in ["", None] or args.url in ["", None]:
            print("ERROR <name> and <url> are required for adding remote", file=stderr)
            exit(-666)
        remote_obj.add(args.name, args.url, args.default)
        return
    if args.remote_command == "remove":
        if args.name in ["", None] or args.url in ["", None]:
            print("ERROR <name> is required for removing remote", file=stderr)
            exit(-666)
        remote_obj.remove(args.name)
        return
    if args.remote_command == "send":
        remote_obj.send(args.message, args.name)
        return

    print("not Yet Implemented")


def remote_arguments(sub_parsers):
    """
    Definition of command line arguments.
    :param sub_parsers: Parser
    """
    remote_parser = sub_parsers.add_parser("remote")
    remote_parser.description = "Tool to search for dependency in the library"
    remote_parser.add_argument(
        "remote_command",
        type=str,
        choices=possible_remote,
        help="The information you want about the program")
    remote_parser.add_argument(
        "--verbose", "-v",
        action="count",
        default=0,
        help="The verbosity level"
    )
    remote_parser.add_argument(
        "--name", "-n",
        type=str,
        default="",
        help="The remote name"
    )
    remote_parser.add_argument(
        "--url", "-u",
        type=str,
        default="",
        help="The remote url"
    )
    remote_parser.add_argument(
        "--message", "-m",
        type=str,
        default="",
        help="The message to the remote"
    )
    remote_parser.add_argument(
        "--default", "-d",
        action="store_true",
        default=False,
        help="If the remote should be the default"
    )
    remote_parser.set_defaults(func=remote)


class Remotes:
    """
    Class managing remotes
    """

    def __init__(self):
        from depmanager.internal.database import DataBase
        self.__db = DataBase()

    def list(self, verbosity: int = 0):
        """
        List the defined remotes
        :param verbosity: Verbosity level
        """
        remotes = {}
        if "remotes" in self.__db.config.config:
            remotes = self.__db.config.config["remotes"]
        for key, value in remotes.items():
            default = [' ', '*'][value['default']]
            if verbosity == 0:
                print(F" {default} {key}")
            else:
                print(F" {default} [ {['OFFLINE', 'ONLINE '][self.is_online(key)]} ] {key} - {value['url']}")

    def add(self, name, url, default: bool = False):
        """
        Add a remote to the list.
        :param name: Remote's name.
        :param url: Remote's url
        :param default: If this remote should become the new default
        """
        if self.is_empty():
            default = True
        elif default:
            for name in self.get_name_list():
                self.__db.config.config["remotes"][name]["default"] = False
        self.__db.config.config["remotes"][name] = {
            "url": url,
            "default": default
        }
        self.save()

    def remove(self, name):
        """
        Remove a remote from the list.
        :param name: Remote's name.
        """
        if not self.exists(name):
            return
        default = self.is_default(name)
        self.__db.config.config["remotes"].pop(name)
        if not default:
            return
        for n in self.get_name_list():
            self.__db.config.config["remotes"][n]["default"] = True
            break
        self.save()

    def send(self, data: str, name: str = ""):
        """
        Send data to the server
        :param data: Data to transfer
        :param name: name of the remote
        """
        from depmanager.internal.client import Client
        if name in ["", None]:
            name = self.get_default_name()
        url = self.get_url(name)
        if url in ["", None]:
            print("WARNING no remotes")
            return
        cli = Client(url)
        cli.connect()
        time.sleep(1)
        cli.send(data)

    def get_default_name(self):
        """
        Get the name of the default remote
        """
        if self.is_empty():
            return ""
        remotes = self.__db.config.config["remotes"]
        return [name for name in remotes.keys() if remotes[name]["default"]][0]

    def save(self):
        """
        Save the config
        """
        self.__db.config.save_config()

    def get_name_list(self):
        """
        Return the list of remotes names
        """
        raw = self.__db.config.config["remotes"].keys()
        default = self.get_default_name()
        return [default] + [name for name in raw if name != default]

    def is_empty(self):
        """
        Returns True if the remote list is empty
        """
        return len(self.__db.config.config["remotes"]) == 0

    def exists(self, name: str):
        """
        Check if a remote name exists
        :param name: the remote name
        :return: True if the remote name exists
        """
        return name in self.get_name_list()

    def is_default(self, name: str):
        """
        Check if the given remote is default.
        :param name: Remote's name to test.
        :return: True if the remote is the default.
        """
        if not self.exists(name):
            return False
        return self.__db.config.config["remotes"][name]["default"]

    def get_url(self, name: str):
        """
        Get the url of a remote.
        :param name: Remote's name.
        :return: The URL of the remote.
        """
        if not self.exists(name):
            return ""
        return self.__db.config.config["remotes"][name]["url"]

    def is_online(self, name: str):
        """
        Check if a remote online
        :param name: Remote's name.
        :return: True if server respond
        """
        from depmanager.internal.client import Client
        url = self.get_url(name)
        if url in [None, ""]:
            print(f"ERROR: cannot check remote '{name}: empty url.", file=stderr)
            return
        cli = Client(url)
        cli.connect()
        return cli.status not in ["fail", "new"]
