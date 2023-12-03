"""
Remote Folder database.
"""
from pathlib import Path
from shutil import copyfile

from depmanager.api.internal.database_common import __RemoteDatabase


class RemoteDatabaseFolder(__RemoteDatabase):
    """
    Remote database using ftp protocol.
    """

    def __init__(self, destination: str, default: bool = False, verbosity: int = 0):
        super().__init__(
            destination=Path(destination).resolve(),
            default=default,
            kind="folder",
            verbosity=verbosity,
        )
        self.remote_type = "Folder"
        self.version = "1.0"

    def connect(self):
        """
        Initialize the connection to remote host.
        TO IMPLEMENT IN DERIVED CLASS.
        """
        self.destination.mkdir(parents=True, exist_ok=True)
        if not (self.destination / "deplist.txt").exists():
            self.send_dep_list()
        self.valid_shape = True

    def suppress(self, dep) -> bool:
        """
        Suppress the dependency from the server
        :param dep: Dependency information.
        :return: True if success.
        """
        destination = Path(
            self.destination / f"{dep.properties.name}" / f"{dep.properties.hash()}.tgz"
        )
        try:
            destination.unlink()
        except Exception as err:
            print(
                f"WARNING: unable to suppress file {destination} on FTP server: {err}"
            )
            return False
        return True

    def get_file(self, distant_name: str, destination: Path):
        """
        Download a file.
        TO IMPLEMENT IN DERIVED CLASS.
        :param distant_name: Name in the distant location.
        :param destination: Destination path.
        """
        source = self.destination / distant_name
        if not source.is_file():
            return
        destination.mkdir(parents=True, exist_ok=True)
        copyfile(source, destination / source.name)

    def send_file(self, source: Path, distant_name: str):
        """
        Upload a file.
        TO IMPLEMENT IN DERIVED CLASS.
        :param source: File to upload.
        :param distant_name: Name in the distant location.
        """
        if not source.is_file():
            return
        distant = self.destination / distant_name
        distant.parent.mkdir(parents=True, exist_ok=True)
        copyfile(source, distant)

    def get_server_version(self):
        """
        Returns the server's version
        :return: Server version.
        """
        return self.version
