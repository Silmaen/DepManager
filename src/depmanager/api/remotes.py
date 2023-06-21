"""
Instance of remotes manager.
"""
from copy import deepcopy
from sys import stderr


class RemotesManager:
    """
    Local manager.
    """

    def __init__(self, system=None, verbosity: int = 0):
        from depmanager.api.internal.system import LocalSystem
        from depmanager.api.local import LocalManager
        self.verbosity = verbosity
        if isinstance(system, LocalSystem):
            self.__sys = system
        elif isinstance(system, LocalManager):
            self.__sys = system.get_sys()
        else:
            self.__sys = LocalSystem(verbosity=verbosity)

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

    def get_safe_remote(self, name, default: bool = False):
        """
        Get remote or default or None (only if no default exists)
        :param name: Remote name
        :param default: to force using default
        :return: the remote
        """
        if default or type(name) != str or name in ["", None]:
            remote = None
        else:
            remote = self.get_remote(name)
        if remote is None:
            return self.get_default_remote()
        return remote

    def get_safe_remote_name(self, name, default: bool = False):
        """
        Get remote or default or None (only if no default exists)
        :param name: Remote name
        :param default: to force using default
        :return: the remote
        """
        if default or type(name) != str or name in ["", None]:
            remote = None
        else:
            remote = name
        if remote is None:
            return self.__sys.default_remote
        return remote

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

    def sync_remote(self, name: str, default: bool = False, pull_newer: bool = True, push_newer: bool = True):
        """
        Synchronize with given remote (push/pull with server all newer package).
        :param name: Remote's name.
        :param default: If using default remote
        :param pull_newer: Pull images if newer version exists
        :param push_newer: Push images if newer version exists
        """
        from depmanager.api.package import PackageManager
        pkg_mgr = PackageManager(self.__sys, self.verbosity)
        local_db = self.__sys.local_database
        remote_db_name = self.get_safe_remote_name(name, default)
        remote_db = self.get_safe_remote(name, default)
        if remote_db is None:
            print(f"ERROR remote {name} not found.", file=stderr)
            exit(-666)
        if remote_db_name in ["", None]:
            print(f"ERROR remote {name}({default}) -> {remote_db_name} not found.", file=stderr)
            exit(-666)
        all_local = local_db.query({
            "name"    : "*",
            "version" : "*",
            "os"      : "*",
            "arch"    : "*",
            "kind"    : "*",
            "compiler": "*"
        })
        # Compare local and remote
        for single_local in all_local:
            props = deepcopy(single_local.properties)
            props_versionless = deepcopy(props)
            props_versionless.version = "*"
            just_pulled = False
            if self.verbosity > 0:
                print(f"Package {single_local.properties.get_as_str()} :", end="")
            # pull newer version of packages
            if pull_newer:
                remote_list = remote_db.query(props_versionless)
                if len(remote_list) > 0:
                    dep_first = remote_list[0]
                    if dep_first.properties.version_greater(props):
                        # Check if new package already on local
                        if len(local_db.query(dep_first)) == 0:
                            if self.verbosity > 0:
                                print(f"==> Pull newer version {dep_first.properties.version}.", end="")
                            else:
                                print(f"Package {dep_first.properties.get_as_str()} : ==> Pull newer version.")
                            pkg_mgr.add_from_remote(dep_first, remote_db_name)
                            just_pulled = True
                    else:
                        if self.verbosity > 0:
                            print(f" No newer version on the server.", end="")
            # push all not-existing package
            if push_newer and not just_pulled:
                if len(remote_db.query(single_local)) > 0:
                    if self.verbosity > 0:
                        print(f" Already on server.", end="")
                else:
                    if self.verbosity > 0:
                        print(f" ==> Push to server.", end="")
                    else:
                        print(f"Package {single_local.properties.get_as_str()} : ==> Push to server.")
                    pkg_mgr.add_to_remote(single_local, remote_db_name)
            if self.verbosity > 0:
                print()
