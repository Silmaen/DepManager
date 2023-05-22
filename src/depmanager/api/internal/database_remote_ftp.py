"""
Remote FTP database
"""
import ftplib
from sys import stderr

from depmanager.api.internal.database_common import __RemoteDatabase
from pathlib import Path


class RemoteDatabaseFtp(__RemoteDatabase):
    """
    Remote database using ftp protocol.
    """

    def __init__(self, destination: str, port: int = 21, default: bool = False, user: str = "", cred: str = "", verbosity:int  = 0):
        self.port = port
        self.ftp = ftplib.FTP()
        super().__init__(destination=destination, default=default, user=user, cred=cred, kind="ftp", verbosity=verbosity)

    def connect(self):
        """
        Initialize the connection to remote host.
        TO IMPLEMENT IN DERIVED CLASS.
        """
        url = self.destination
        path = ""
        if "/" in url:
            url, path = url.split("/", 1)
        try:
            self.ftp.connect(url, self.port)
            self.ftp.login(self.user, self.cred)
            if path != "":
                self.ftp.cwd(f"/{path}")
            self.valid_shape = True
        except Exception as err:
            self.valid_shape = False
            print(f"ERROR while connecting to ftp server {self.destination}: {err}.", file=stderr)

    def get_file(self, distant_name: str, destination: Path):
        """
        Download a file.
        TO IMPLEMENT IN DERIVED CLASS.
        :param distant_name: Name in the distant location.
        :param destination: Destination path.
        """
        file_name = Path(distant_name).name
        try:
            with open(destination / file_name, "wb") as handler:
                self.ftp.retrbinary(f"RETR {distant_name}", handler.write)
        except Exception as err:
            print(f"WARNING: error getting {distant_name} from FTP {self.destination}: {err}")

    def send_file(self, source: Path, distant_name: str):
        """
        Upload a file.
        TO IMPLEMENT IN DERIVED CLASS.
        :param source: File to upload.
        :param distant_name: Name in the distant location.
        """
        if "/" in distant_name:
            items = distant_name.split("/")
            items = items[:-1]
            cur_dir = ""
            for sub in items:
                candidate = f"{sub}"
                if cur_dir != "":
                    candidate = f"{cur_dir}/{candidate}"
                if sub not in self.ftp.nlst(cur_dir):
                    self.ftp.mkd(candidate)
                cur_dir = candidate
        try:
            with open(source, "rb") as handler:
                self.ftp.storbinary(f"STOR {distant_name}", handler)
        except Exception as err:
            print(f"WARNING: error sending {distant_name} to FTP {self.destination}: {err}")
