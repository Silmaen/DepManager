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
        if type(system) is LocalSystem:
            self.__sys = system
        elif type(system) is LocalManager:
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
        if default or type(name) is not str or name in ["", None]:
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
        if default or type(name) is not str or name in ["", None]:
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

    def add_remote(
        self,
        name: str,
        url: str,
        port: int = -1,
        default: bool = False,
        kind: str = "ftp",
        login: str = "",
        passwd: str = "",
    ):
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
        data = {"name": name, "url": url, "default": default, "kind": kind}
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

    def sync_remote(
        self,
        name: str,
        default: bool = False,
        pull_newer: bool = True,
        push_newer: bool = True,
        dry_run: bool = False,
    ):
        """
        Synchronize with given remote (push/pull with server all newer package).
        :param name: Remote's name.
        :param default: If using default remote
        :param pull_newer: Pull images if newer version exists
        :param push_newer: Push images if newer version exists
        :param dry_run: Do checks but no transfer.
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
            print(
                f"ERROR remote {name}({default}) -> {remote_db_name} not found.",
                file=stderr,
            )
            exit(-666)
        all_local = local_db.query()
        if self.verbosity > 0:
            print(f"Syncing with server: {remote_db_name}")

        # Compare local and remote
        for single_local in all_local:
            query_remote = single_local.get_generic_query()
            is_up_to_date = False
            just_pulled = False
            do_pull = True
            if self.verbosity > 1:
                print(f"Check Local Package: {single_local.properties.get_as_str()}")
            #
            # check locally if there is already a newer version
            #
            if pull_newer:
                loc_dep_list = local_db.query(query_remote)
                highest_version = ""
                for dep in loc_dep_list:
                    if dep.version_greater(highest_version):
                        highest_version = dep.properties.version
                if not single_local.has_minimal_version(highest_version):
                    do_pull = False

            #
            # pull newer version of packages
            #
            if pull_newer and do_pull:
                if self.verbosity > 3:
                    print(f"Query to remote: {query_remote}")
                remote_dep_list = remote_db.query(query_remote)
                if len(remote_dep_list) == 0:
                    if self.verbosity > 3:
                        print(f"No Similar Package found on remote.")
                else:
                    if self.verbosity > 3:
                        print(
                            f"found {len(remote_dep_list)} similar package{['','s'][len(remote_dep_list)>0]}"
                        )
                    # filter to remove older version
                    highest_version = ""
                    for dep in remote_dep_list:
                        if dep.version_greater(highest_version):
                            highest_version = dep.properties.version
                    if self.verbosity > 3:
                        print(f"Highest version found: {highest_version}.")
                    if highest_version == "":
                        if self.verbosity > 3:
                            print(f"Remote has only lower version in database.")
                    else:
                        # get list of newest
                        filtered_list = []
                        for dep in remote_dep_list:
                            if dep.properties.version == highest_version:
                                filtered_list.append(dep)
                        filtered_list = sorted(
                            filtered_list,
                            key=lambda item: item.properties.build_date,
                            reverse=True,
                        )
                        if self.verbosity > 3:
                            print(
                                f"After version filter, remains {len(filtered_list)}."
                            )
                        if len(filtered_list) == 0:
                            if self.verbosity > 3:
                                print(f"remote contains only older versions.")
                        else:
                            if highest_version == single_local.properties.version:
                                # same version, look at build date
                                if (
                                    filtered_list[0].properties.build_date
                                    == single_local.properties.build_date
                                ):
                                    # up-to-date
                                    if self.verbosity > 1:
                                        print(
                                            f" ---- Local Package is already up to date."
                                        )
                                    is_up_to_date = True
                                elif (
                                    filtered_list[0].properties.build_date
                                    > single_local.properties.build_date
                                ):
                                    if self.verbosity > 3:
                                        print(
                                            f"suppress [local] {single_local.properties.get_as_str()}"
                                        )
                                        print(
                                            f"pull    [{remote_db_name}] {filtered_list[0].properties.get_as_str()}"
                                        )
                                    elif self.verbosity > 1:
                                        print(
                                            f" <-X- newer build date found on server PULL and replace local."
                                        )
                                    elif self.verbosity > 0:
                                        print(
                                            f" <-X- [{single_local.properties.get_as_str()}] force-pull from server: ",
                                            end="",
                                        )
                                    just_pulled = True
                                    if not dry_run:
                                        pkg_mgr.remove_package(single_local)
                                        pkg_mgr.add_from_remote(
                                            filtered_list[0], remote_db_name
                                        )
                                    else:
                                        if self.verbosity == 1:
                                            print()
                                else:
                                    if self.verbosity > 3:
                                        print(
                                            f"suppress [{remote_db_name}] {filtered_list[0].properties.get_as_str()}"
                                        )
                                        print(
                                            f"push    [local] {single_local.properties.get_as_str()}"
                                        )
                                    elif self.verbosity > 1:
                                        print(
                                            f" -X-> older build date found on server PUSH and replace on remote."
                                        )
                                    elif self.verbosity > 0:
                                        print(
                                            f" -X-> [{single_local.properties.get_as_str()}] force-push to server."
                                        )
                                    just_pulled = True
                                    if not dry_run:
                                        pkg_mgr.remove_package(
                                            filtered_list[0], remote_db_name
                                        )
                                        pkg_mgr.add_to_remote(
                                            single_local, remote_db_name
                                        )
                            else:
                                # newer version found!
                                if self.verbosity > 3:
                                    print(
                                        f"pull    [{remote_db_name}] {filtered_list[0].properties.get_as_str()}"
                                    )
                                elif self.verbosity > 1:
                                    print(f" <--- Newer version: pull from server.")
                                elif self.verbosity > 0:
                                    print(
                                        f" <--- [{single_local.properties.get_as_str()}] pull from server"
                                    )
                                just_pulled = True
                                if not dry_run:
                                    pkg_mgr.add_from_remote(
                                        filtered_list[0], remote_db_name
                                    )

            #
            # push all not-existing package
            #
            if not push_newer or just_pulled or is_up_to_date:
                continue
            query_for_push = deepcopy(single_local.properties)
            query_for_push.build_date = "*"
            if self.verbosity > 3:
                print(f"Query for push: {query_for_push.get_as_str()}")
            result = remote_db.query(query_for_push)
            if len(result) > 1:
                print(
                    f"ERROR: {single_local.properties.get_as_str()} Too many version date on remote, please correct the remote."
                )
                continue
            to_del = None
            if len(result) > 0:
                to_del = result[0]
                if not single_local.is_newer(to_del.properties.build_date):
                    if self.verbosity > 2:
                        print(f"Newer version on the server, not pushing.")
                    continue
            if self.verbosity > 3:
                if to_del is not None:
                    print(
                        f"suppress [{remote_db_name}] {to_del.properties.get_as_str()}"
                    )
                print(f"push    [local] {single_local.properties.get_as_str()}")
            elif self.verbosity > 1:
                if to_del is not None:
                    print(
                        f" -X-> older build date found on server PUSH and replace on remote."
                    )
                else:
                    print(f" ---> package not found on the server, pushing it.")
            elif self.verbosity > 0:
                if to_del is not None:
                    print(
                        f" -X-> [{single_local.properties.get_as_str()}] force-push to server: "
                    )
                else:
                    print(
                        f" ---> [{single_local.properties.get_as_str()}] push to server: "
                    )
            if not dry_run:
                if to_del is not None:
                    pkg_mgr.remove_package(to_del, remote_db_name)
                pkg_mgr.add_to_remote(single_local, remote_db_name)
        if self.verbosity > 0:
            print("Syncing done.")
