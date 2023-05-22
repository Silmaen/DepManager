"""
Remote Folder database.
"""
from shutil import copyfile

from depmanager.api.internal.database_common import __RemoteDatabase
from pathlib import Path


class RemoteDatabaseFolder(__RemoteDatabase):
    """
    Remote database using ftp protocol.
    """

    def __init__(self, destination: str, default: bool = False, verbosity:int  = 0):
        super().__init__(destination=Path(destination).resolve(), default=default, kind="folder", verbosity=verbosity)


    def connect(self):
        """
        Initialize the connection to remote host.
        TO IMPLEMENT IN DERIVED CLASS.
        """
        self.destination.mkdir(parents=True, exist_ok=True)
        if not (self.destination / "deplist.txt").exists():
            self.send_dep_list()
        self.valid_shape = True

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
