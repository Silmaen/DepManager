"""
Instance of remotes manager.
"""


class RemotesManager:
    """
    Local manager.
    """

    def __init__(self, system=None):
        from depmanager.api.internal.system import LocalSystem
        from depmanager.api.local import LocalManager
        if isinstance(system, LocalSystem):
            self.__sys = system
        elif isinstance(system, LocalManager):
            self.__sys = system.get_sys()
        else:
            self.__sys = LocalSystem()

    def get_remote_list(self):
        """
        Get a list of remotes.
        :return: List of remotes.
        """
        return self.__sys.remote_database

    def get_supported_remotes(self):
        """
        Get lit of supported remote kind.
        :return: Supported remotes.
        """
        return self.__sys.supported_remote

    def get_remote(self, name: str):
        """
        Access to remote with given name.
        :param name: Name of the remote.
        :return: The remote or None.
        """
        if name not in self.__sys.remote_database:
            return None
        return self.__sys.remote_database[name]

    def get_local(self):
        """
        Access to local base.
        :return: The local base.
        """
        return self.__sys.local_database

    def get_temp_dir(self):
        """
        Get temp path
        :return:
        """
        return self.__sys.temp_path

    def get_default_remote(self):
        """
        Access to the default remote.
        :return: The remote or None.
        """
        if self.__sys.default_remote == "":
            return None
        return self.get_remote(self.__sys.default_remote)

    def add_remote(self, name: str, url: str, port: int = -1, default: bool = False,
                   kind: str = "ftp", login: str = "", passwd: str = ""):
        """
        Add a remote to the list.
        :param name: Remote's name.
        :param url: Remote's url.
        :param port: Remote server's port.
        :param default: If this remote should become the new default.
        :param kind: Kind of remote.
        :param login: Credential to use for connexion.
        :param passwd: Password for connexion.
        """
        data = {
            "name"   : name,
            "url"    : url,
            "default": default,
            "kind"   : kind
        }
        if port > 0:
            data["port"] = port
        if login != "":
            data["login"] = login
        if passwd != "":
            data["passwd"] = passwd
        self.__sys.add_remote(data)

    def remove_remote(self, name: str):
        """
        Remove a remote from the list.
        :param name: Remote's name.
        """
        self.__sys.del_remote(name)
