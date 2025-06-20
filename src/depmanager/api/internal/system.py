"""
Everything needed for database.
"""

from pathlib import Path
from shutil import rmtree
from sys import stderr

from depmanager.api.internal.data_locking import Locker
from depmanager.api.internal.database_local import LocalDatabase
from depmanager.api.internal.database_remote_folder import RemoteDatabaseFolder
from depmanager.api.internal.database_remote_ftp import RemoteDatabaseFtp
from depmanager.api.internal.database_remote_server import RemoteDatabaseServer
from depmanager.api.internal.dependency import Props
from depmanager.api.internal.toolset import Toolset


class LocalSystem:
    """
    System manager.
    """

    supported_remote = ["srv", "srvs", "ftp", "folder"]

    def __init__(self, config_file: Path = None, verbosity: int = 0):
        self.config = {}
        self.verbosity = verbosity
        if config_file is None:
            self.base_path = Path.home() / ".edm"
            self.file = self.base_path / "config.ini"
            self.data_path = self.base_path / "data"
            self.temp_path = self.base_path / "tmp"
        else:
            self.file = config_file
            self.base_path = self.file.parent
            self.data_path = self.base_path / "data"
            self.temp_path = self.base_path / "tmp"
        #
        # request data lock
        self.locker = Locker(base_path=self.base_path, verbosity=verbosity)
        if not self.locker.request_lock():
            print(f"Locking system reach deadlock - exit.", file=stderr)
            exit(1)
        self.released = False
        # in case of first initialization
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)
        #
        # this instance has now exclusive (hope)
        #
        self.read_config_file()
        #
        # Manage databases
        #
        self.local_database = LocalDatabase(self.data_path, verbosity=self.verbosity)
        self.remote_database = {}
        self.default_remote = ""
        if "remotes" not in self.config.keys():
            self.config["remotes"] = {}
        for name, info in self.config["remotes"].items():
            if "url" not in info:
                print(f"Missing urls in remote.", file=stderr)
                continue
            url = info["url"]
            if "kind" in info:
                kind = info["kind"]
            else:
                kind = self.supported_remote[0]
            if kind not in self.supported_remote:
                print(f"Unsupported kind: {kind}.", file=stderr)
                continue
            if "login" in info:
                login = info["login"]
            else:
                login = ""
            if "passwd" in info:
                passwd = info["passwd"]
            else:
                passwd = ""
            default = False
            if "default" in info:
                default = info["default"]
            if default:
                self.default_remote = name
            if kind == "srv":
                if "port" in info:
                    port = info["port"]
                else:
                    port = -1
                self.remote_database[name] = RemoteDatabaseServer(
                    url, port, False, default, login, passwd, verbosity=self.verbosity
                )
            if kind == "srvs":
                if "port" in info:
                    port = info["port"]
                else:
                    port = -1
                self.remote_database[name] = RemoteDatabaseServer(
                    url, port, True, default, login, passwd, verbosity=self.verbosity
                )
            elif kind == "ftp":
                if "port" in info:
                    port = info["port"]
                else:
                    port = 21
                self.remote_database[name] = RemoteDatabaseFtp(
                    url, port, default, login, passwd, verbosity=self.verbosity
                )
            elif kind == "folder":
                self.remote_database[name] = RemoteDatabaseFolder(
                    url, default, verbosity=self.verbosity
                )
        #
        # Manage toolsets
        #
        self.toolsets = {}
        self.default_toolset = ""
        if "toolsets" not in self.config.keys():
            self.config["toolsets"] = {}
        for name, info in self.config["toolsets"].items():
            self.toolsets[name] = Toolset(name)
            self.toolsets[name].from_dict(info)
            if self.toolsets[name].default:
                self.default_toolset = name
        if self.default_toolset == "":
            for name, info in self.config["toolsets"].items():
                self.default_toolset = name
                self.toolsets[name].default = True
        #
        self.write_config_file()

    def __del__(self):
        if not self.released:
            self.release()

    def release(self):
        """
        Release the lock on the data
        """
        self.locker.release_lock()
        self.released = True

    def get_source_list(self):
        """
        Get the list of source starting from local, then default remote then other remotes
        :return: List of sources
        """
        slist = ["local"]
        if self.default_remote not in ["", None]:
            slist.append(self.default_remote)
        for rem in self.remote_database.keys():
            if rem == self.default_remote:
                continue
            slist.append(rem)
        return slist

    def read_config_file(self):
        """
        Read configuration file.
        """
        import json

        if not self.file.exists():
            return
        with open(self.file, "r") as fp:
            self.config = json.load(fp)
        if "base_path" in self.config.keys():
            self.base_path = Path(self.config["base_path"]).resolve()
            self.data_path = self.base_path / "data"
            self.temp_path = self.base_path / "tmp"
        if "data_path" in self.config.keys():
            self.base_path = Path(self.config["data_path"]).resolve()
        if "temp_path" in self.config.keys():
            self.base_path = Path(self.config["temp_path"]).resolve()

    def write_config_file(self):
        """
        Write actual configuration to file.
        """
        import json

        # create all directories if not exists
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.file, "w") as fp:
                fp.write(json.dumps(self.config, indent=2))
        except Exception as err:
            print(f"Exception during config writing: {err}", file=stderr)

    def clear_tmp(self):
        """
        Empty the Temp dir.
        """
        from shutil import rmtree

        rmtree(self.temp_path, ignore_errors=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)

    def add_remote(self, data):
        """
        Add remote or modify existing one.
        :param data: All remote data.
        :return: True if remote added.
        """
        # checking keys
        if (
            "name" not in data
            or "url" not in data
            or "default" not in data
            or "kind" not in data
        ):
            if self.verbosity > 3:
                print("ERROR: cannot add remote: missing required fields")
            return False
        name = data["name"]
        url = data["url"]
        default = data["default"]
        kind = data["kind"]
        # checking type
        if (
            type(default) is not bool
            or type(name) is not str
            or type(url) is not str
            or kind not in self.supported_remote
        ):
            if self.verbosity > 3:
                print("ERROR: cannot add remote: wrong type in required fields")
            return False
        if name in [None, ""]:
            if self.verbosity > 3:
                print("ERROR: cannot add remote: empty name")
            return False
        if "://" in url:
            url = str(url).split("://")[-1]
        if url in [None, ""]:
            if self.verbosity > 3:
                print("ERROR: cannot add remote: empty url")
            return False
        if default and self.default_remote != "":
            self.remote_database[self.default_remote].default = False
            self.config["remotes"][self.default_remote]["default"] = False
        if self.default_remote == "":
            default = True
        if default:
            self.default_remote = name
        if kind in ["srv", "srvs"]:
            if "port" in data:
                port = data["port"]
            else:
                if kind == "srvs":
                    port = 443
                else:
                    port = 80
            if "login" in data:
                login = data["login"]
            else:
                login = ""
            if "passwd" in data:
                passwd = data["passwd"]
            else:
                passwd = ""
            self.remote_database[name] = RemoteDatabaseServer(
                destination=url,
                port=port,
                secure=kind == "srvs",
                default=default,
                user=login,
                cred=passwd,
            )
            if not self.remote_database[name].valid_shape:
                print("Error: cannot add the remote!", file=stderr)
                return False
            self.config["remotes"][name] = {
                "url": url,
                "port": port,
                "default": default,
                "kind": kind,
            }
            if ("port" != 80 and kind == "srv") or ("port" != 443 and kind == "srvs"):
                self.config["remotes"][name]["port"] = port
            if "login" != "":
                self.config["remotes"][name]["login"] = login
            if "passwd" != "":
                self.config["remotes"][name]["passwd"] = passwd
            self.write_config_file()
            return True
        if kind == "ftp":
            if "port" in data:
                port = data["port"]
            else:
                port = 21
            if "login" in data:
                login = data["login"]
            else:
                login = ""
            if "passwd" in data:
                passwd = data["passwd"]
            else:
                passwd = ""
            self.remote_database[name] = RemoteDatabaseFtp(
                url, port, default, login, passwd
            )
            self.config["remotes"][name] = {
                "url": url,
                "port": port,
                "default": default,
                "kind": kind,
            }
            if "port" != 21:
                self.config["remotes"][name]["port"] = port
            if "login" != "":
                self.config["remotes"][name]["login"] = login
            if "passwd" != "":
                self.config["remotes"][name]["passwd"] = passwd
            self.write_config_file()
            return True
        if kind == "folder":
            self.remote_database[name] = RemoteDatabaseFolder(url, default)
            self.config["remotes"][name] = {
                "url": url,
                "default": default,
                "kind": kind,
            }
            self.write_config_file()
            return True
        return False

    def del_remote(self, name: str):
        """
        Delete a remote.
        :param name: Remote's name.
        :return: True if success.
        """
        if name not in self.remote_database:
            return False
        self.config["remotes"].pop(name)
        self.remote_database.pop(name)
        if name == self.default_remote:
            self.default_remote = ""
            if len(self.config["remotes"]) != 0:
                self.default_remote = list(self.config["remotes"].keys())[0]
                self.config["remotes"][self.default_remote]["default"] = True
                self.remote_database[self.default_remote].default = True
        self.write_config_file()
        return True

    def import_folder(self, source: Path):
        """
        Import package to database.
        :param source: Package initial folder.
        """
        from shutil import copytree

        p = Props()
        p.from_edp_file(source / "edp.info")
        destination_folder = self.local_database.base_path / f"{p.name}{p.hash()}"
        rmtree(destination_folder, ignore_errors=True)
        copytree(source, destination_folder)
        self.clear_tmp()
        self.local_database.reload()

    def remove_local(self, pack):
        """
        Remove from local database.
        :param pack: Package's query to remove.
        """
        self.local_database.delete(pack)

    def add_toolset(self, name: str, info: dict, default: bool = False):
        """
        Add a new toolset to the system.
        :param name: The Toolset's name.
        :param info: The toolset's internal information.
        :param default: If that toolset is the default one.
        """
        if name not in self.toolsets:
            self.toolsets[name] = Toolset(name)
            self.toolsets[name].from_dict(info)
            if default or self.default_toolset in [None, ""]:
                if self.default_toolset not in [None, ""]:
                    self.toolsets[self.default_toolset].default = False
                    self.config["toolsets"][self.default_toolset] = self.toolsets[
                        self.default_toolset
                    ].to_dict()
                self.default_toolset = name
                self.toolsets[name].default = True
            self.config["toolsets"][name] = self.toolsets[name].to_dict()
        else:
            if self.verbosity > 0:
                print("WARNING: cannot add toolset: already exists.")
        self.write_config_file()
        return True

    def del_toolset(self, name: str = ""):
        """
        Remove the toolset with the given name.
        :param name: Name of the toolset to remove.
        """
        if name in [None, str]:
            if self.verbosity > 0:
                print("WARNING: Empty toolset name.")
            return False
        if name not in self.toolsets:
            if self.verbosity > 0:
                print(
                    f"WARNING: no toolset {name} found in database: {list(self.toolsets.keys())}."
                )
            return False
        self.toolsets.pop(name)
        self.config["toolsets"].pop(name)
        if name == self.default_toolset:
            if len(self.toolsets) == 0:
                self.default_toolset = ""
            else:
                self.default_toolset = list(self.toolsets.keys())[0]
                self.config["toolsets"][self.default_toolset]["default"] = True
                self.toolsets[self.default_toolset].default = True
        self.write_config_file()
        return True

    def get_toolset(self, name: str = ""):
        """
        Get the toolset with given name.
        :param name: Name of the toolset, empty for default one.
        :return: Tool set.
        """
        if len(self.toolsets) == 0:
            return None
        if name in [None, ""]:
            self.toolsets[self.default_toolset]
        if name in self.toolsets:
            return self.toolsets[name]
        return None

    #
