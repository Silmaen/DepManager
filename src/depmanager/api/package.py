"""
Manager for package.
"""

from pathlib import Path
from shutil import rmtree

from api.internal.messaging import log
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
)


def get_folder_size(folder_path: Path) -> int:
    """
    Calculate total size of all files in a folder recursively.

    :param folder_path: Path to the folder
    :return: Total size in bytes
    """
    total_size = 0
    try:
        for item in folder_path.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size
    except Exception as e:
        from api.internal.messaging import log

        log.warn(f"Error calculating folder size: {e}")
    return total_size


class PackageManager:
    """
    Manager fo package.
    """

    def __init__(self, system=None):
        from api.internal.system import LocalSystem
        from api.local import LocalManager

        if type(system) is LocalSystem:
            self.__sys = system
        elif type(system) is LocalManager:
            self.__sys = system.get_sys()
        else:
            self.__sys = LocalSystem()

    def query(self, query, remote_name: str = "", sort: bool = True):
        """
        Do a query into database.
        :param query: Query's data.
        :param remote_name: Remote's name to search of empty for local.
        :param sort: Sort the result list by name and version.
        :return: List of packages matching the query.
        """
        using_name = "local"
        if remote_name in self.__sys.remote_database:
            using_name = remote_name
        elif remote_name == "default":
            using_name = self.__sys.default_remote

        if type(query) is dict and query.get("transitive", False):
            slist = self.__sys.get_source_list()
        else:
            if using_name not in ["", None]:
                slist = [using_name]
            else:
                slist = []
        db = []
        for s in slist:
            if s == "local":
                ldb = self.__sys.local_database.query(query)
            else:
                ldb = self.__sys.remote_database[s].query(query)
            for dep in ldb:
                dep.source = s
            db += ldb
        if sort:
            db.sort(
                key=lambda x: (
                    x.properties.name,
                    x.properties.version,
                ),
                reverse=False,
            )
            # stable sort to have versions in order
            db.sort(
                key=lambda x: x.properties.version,
                reverse=True,
            )
        return db

    def get_default_remote(self):
        """
        Get the default remote name
        :return:
        """
        return self.__sys.default_remote

    def remote_name(self, args):
        """
        Get remote name based of arguments.
        :param args: Arguments.
        :return: Remote name.
        """
        if args.default:
            return self.__sys.default_remote
        if args.name in self.__sys.remote_database:
            return args.name
        return ""

    def add_from_location(self, source: Path):
        """
        Add a package to the local database
        :param source: Path to the package source
        :return:
        """
        if not source.exists():
            log.warn(f"WARNING: Location {source} does not exists.")
            return
        if source.is_dir():
            if not (source / "edp.info").exists():
                log.warn(f"WARNING: Location {source} does not contains edp.info file.")
                return
            self.__sys.import_folder(source)
            return
        elif source.is_file():
            suffixes = []
            if len(source.suffixes) > 0:
                suffixes = [source.suffixes[-1]]
                if suffixes == [".gz"] and len(source.suffixes) > 1:
                    suffixes = [source.suffixes[-2], source.suffixes[-1]]
            destination_dir = self.__sys.temp_path / "pack"
            if destination_dir.exists():
                rmtree(destination_dir, ignore_errors=True)
            destination_dir.mkdir(parents=True)
            if suffixes == ["zip"]:
                from zipfile import ZipFile

                log.debug(
                    f"PackageManager::add_from_location - Extract ZIP from {source} to {destination_dir}"
                )
                with ZipFile(source) as archive:
                    members = archive.infolist()
                    total = sum(m.file_size for m in members)
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        BarColumn(),
                        DownloadColumn(),
                        TransferSpeedColumn(),
                    ) as progress:
                        task = progress.add_task("Extracting ZIP...", total=total)
                        for member in members:
                            archive.extract(member, destination_dir)
                            progress.update(task, advance=member.file_size)
            elif suffixes in [[".tgz"], [".tar", ".gz"]]:
                import tarfile

                log.debug(
                    f"PackageManager::add_from_location - Extract TGZ from {source} to {destination_dir}"
                )
                try:
                    with tarfile.open(str(source), "r:gz") as archive:
                        members = archive.getmembers()
                        total = sum(m.size for m in members if m.isfile())
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            BarColumn(),
                            DownloadColumn(),
                            TransferSpeedColumn(),
                        ) as progress:
                            task = progress.add_task("Extracting TGZ...", total=total)
                            for member in members:
                                archive.extract(member, destination_dir)
                                if member.isfile():
                                    progress.update(task, advance=member.size)
                except Exception as e:
                    log.warn(f"WARNING: Error extracting {source}: {e}")
                    self.__sys.clear_tmp()
                    return
            else:
                log.warn(f"WARNING: File {source} has unsupported format.")
                self.__sys.clear_tmp()
                return
            if destination_dir is not None:
                if not (destination_dir / "edp.info").exists():
                    log.warn(f"WARNING: Archive does not contains package info.")
                    self.__sys.clear_tmp()
                    return
                self.__sys.import_folder(destination_dir)

    def remove_package(self, pack, remote_name: str = ""):
        """
        Suppress package in local database.
        :param pack: The package to remove.
        :param remote_name: The remote server to use.
        """
        if remote_name == "":
            self.__sys.remove_local(pack)
            return
        if remote_name == "default":
            remote_name = self.__sys.default_remote
        if remote_name not in self.__sys.remote_database:
            log.error(f"no remote named {remote_name} found.")
            return
        remote = self.__sys.remote_database[remote_name]
        remote.delete(pack)

    def add_from_remote(self, dep, remote_name):
        """
        Get a package from remote to local.
        :param dep: The dependency to get.
        :param remote_name: The remote server to use.
        """
        if remote_name == "default":
            remote_name = self.__sys.default_remote
        if remote_name not in self.__sys.remote_database:
            log.error(f"no remote named {remote_name} found.")
            return
        remote = self.__sys.remote_database[remote_name]
        finds = remote.query(dep)
        if len(finds) > 1:
            log.warn("WARNING: more than 1 package matches the request:")
            for find in finds:
                log.warn(f"         {find.properties.get_as_str()}")
            log.warn(
                "         Precise your request, only one package per pull allowed."
            )
            return
        if len(finds) == 0:
            log.error("no package matches the request.")
            return
        depp = finds[0]
        res = remote.pull(dep, self.__sys.temp_path)
        if res is None:
            file = self.__sys.temp_path / f"{dep.properties.hash()}.tgz"
        else:
            file = self.__sys.temp_path / f"{res}"
        self.add_from_location(file)
        if depp.has_dependency():
            log.info("Package has dependencies, trying to get them...")
            for sub_dep in depp.get_dependency_list():
                if len(self.query(sub_dep)) == 0:
                    log.info(
                        f" Getting dependency {sub_dep['name']}/{sub_dep['version']}..."
                    )
                    self.add_from_remote(sub_dep, remote_name)
                else:
                    log.info(
                        f" Dependency {sub_dep['name']}/{sub_dep['version']} already present locally."
                    )

    def add_to_remote(self, dep, remote_name):
        """
        Get a package from local to remote.

        :param dep: The dependency to send.
        :param remote_name: The remote server to use.
        """
        if remote_name == "default":
            remote_name = self.__sys.default_remote
        if remote_name not in self.__sys.remote_database:
            log.error(f"no remote named {remote_name} found.")
            return
        log.info(f"Using remote named {remote_name}.")
        remote = self.__sys.remote_database[remote_name]
        finds = self.__sys.local_database.query(dep)
        if len(finds) > 1:
            log.warn("WARNING: more than 1 package matches the request:")
            for find in finds:
                log.warn(f"         {find.properties.get_as_str()}")
            log.warn(
                "         Precise your request, only one package per push allowed."
            )
            return
        if len(finds) == 0:
            log.error("no package matches the request.")
            return
        depp = finds[0]

        dep_path = self.__sys.temp_path / (Path(depp.get_path()).name + ".tgz")
        log.info(f"Compressing library to file {dep_path}.")

        try:
            folder_path = Path(depp.get_path())
            total_size = get_folder_size(folder_path)

            if total_size > 0:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                ) as progress:
                    task = progress.add_task("Compressing...", total=total_size)

                    def progress_callback(bytes_processed: int) -> None:
                        """
                        Update progress bar with compressed bytes.

                        :param bytes_processed: Number of bytes just processed
                        """
                        progress.advance(task, bytes_processed)

                    self.__sys.local_database.pack(
                        depp,
                        self.__sys.temp_path,
                        "tgz",
                        progress_callback=progress_callback,
                    )
            else:
                # Fallback without progress bar
                self.__sys.local_database.pack(depp, self.__sys.temp_path, "tgz")

        except TypeError:
            # pack() doesn't support progress_callback parameter
            log.debug(
                "Pack method doesn't support progress callback, using without progress bar"
            )
            self.__sys.local_database.pack(depp, self.__sys.temp_path, "tgz")
        except Exception as e:
            log.error(f"Compression failed: {e}")
            return

        log.info(f"Starting upload.")
        remote.push(depp, dep_path)
        if depp.has_dependency():
            log.info("Package has dependencies, trying to push them...")
            for sub_dep in depp.get_dependency_list():
                if len(remote.query(sub_dep)) == 0:
                    log.info(
                        f" Pushing dependency {sub_dep['name']}/{sub_dep['version']}..."
                    )
                    self.add_to_remote(sub_dep, remote_name)
                else:
                    log.info(
                        f" Dependency {sub_dep['name']}/{sub_dep['version']} already present on remote."
                    )
