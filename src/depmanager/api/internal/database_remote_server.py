"""
Remote FTP database
"""
from datetime import datetime
from sys import stderr
from pathlib import Path
from requests.auth import HTTPBasicAuth
from requests import get as httpget, post as httppost
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

from depmanager.api.internal.database_common import __RemoteDatabase
from depmanager.api.internal.dependency import Dependency


class RemoteDatabaseServer(__RemoteDatabase):
    """
    Remote database using server protocol.
    """

    def __init__(self, destination: str, port: int = -1, secure: bool = False, default: bool = False, user: str = "", cred: str = ""):
        self.port = port
        if self.port == -1:
            if secure:
                self.port = 443
            else:
                self.port = 80
        self.secure = secure
        self.kind = ["srv","srvs"][secure]
        true_destination = f"http{['','s'][secure]}://{destination}"
        if secure:
            if self.port != 443:
                true_destination += f":{self.port}"
        else:
            if self.port != 80:
                true_destination += f":{self.port}"
        super().__init__(destination=true_destination, default=default, user=user, cred=cred, kind = self.kind)

    def connect(self):
        """
        Initialize the connection to remote host.
        TO IMPLEMENT IN DERIVED CLASS.
        """
        pass

    def get_dep_list(self):
        """
        Get a list of string describing dependency from the server.
        """
        try:
            basic = HTTPBasicAuth(self.user, self.cred)
            resp = httpget(f"{self.destination}/api", auth=basic)
            if resp.status_code != 200:
                self.valid_shape = False
                print(f"ERROR connecting to server: {self.destination}: {resp.status_code}: {resp.reason}")
                return
            data = resp.text.splitlines(keepends=False)
            self.deps_from_strings(data)
        except Exception as err:
            print(f"ERROR Exception during server connexion: {self.destination}: {err}")
            return

    def encode_request(self, req: dict, key):
        """
        encode the post request
        :param req:
        :param key:
        :return:
        """
        data = ""
        for r, q in req.items():
            data += f'--{key}\r\nContent-Disposition: form-data; name="{r}"\r\n\r\n{q}\r\n'
        # end of data body
        data += f'--{key}--\r\n'
        return data

    def dep_to_code(self, dep: Dependency):
        data = {}
        if dep.properties.name not in ["", None]:
            data["name"] = dep.properties.name
        if dep.properties.version not in ["", None]:
            data["version"] = dep.properties.version
        # os
        if dep.properties.os.lower() == "windows":
            data["os"] = "w"
        if dep.properties.os.lower() == "linux":
            data["os"] = "l"
        # arch
        if dep.properties.arch.lower() == "x86_64":
            data["arch"] = "x"
        if dep.properties.arch.lower() == "aarch64":
            data["arch"] = "a"
        # kind
        if dep.properties.kind.lower() == "shared":
            data["kind"] = "r"
        if dep.properties.kind.lower() == "static":
            data["kind"] = "t"
        if dep.properties.kind.lower() == "header":
            data["kind"] = "h"
        if dep.properties.kind.lower() == "any":
            data["kind"] = "a"
        # compiler
        if dep.properties.compiler.lower() == "gnu":
            data["compiler"] = "g"
        if dep.properties.compiler.lower() == "msvc":
            data["compiler"] = "m"
        return data

    def pull(self, dep: Dependency, destination: Path):
        """
        Pull a dependency from remote.
        :param dep: Dependency information.
        :param destination: Destination directory
        """
        if destination.exists() and not destination.is_dir():
            return
        deps = self.query(dep)
        if len(deps) != 1:
            return
        # get the download url:
        try:
            basic = HTTPBasicAuth(self.user, self.cred)
            post_data = {"action": "pull"} | self.dep_to_code(dep)
            resp = httppost(f"{self.destination}/api", auth=basic, data=post_data)

            if resp.status_code != 200:
                self.valid_shape = False
                print(f"ERROR connecting to server: {self.destination}: {resp.status_code}: {resp.reason}", file=stderr)
                print(f"      Server Data: {resp.text}", file=stderr)
                return
            data = resp.text.strip()
            filename = data.rsplit("/",1)[-1]
            if filename.startswith(dep.properties.name):
                filename = filename.replace(dep.properties.name, "")
            fname = destination / filename
            resp = httpget(f"{self.destination}{data}", auth=basic)
            if resp.status_code != 200:
                self.valid_shape = False
                print(f"ERROR retrieving file {data} from server {self.destination}: {resp.status_code}: {resp.reason}, see error.log", file=stderr)
                with open("error.log", "ab") as fp:
                    fp.write(f"---- ERROR: {datetime.now()} ---- \n".encode('utf8'))
                    fp.write(resp.content)
                return
            with open(fname, "wb") as fp:
                fp.write(resp.content)
        except Exception as err:
            print(f"ERROR Exception during server pull: {self.destination}: {err}")
            return

    def push(self, dep: Dependency, file: Path, force: bool = False):
        """
        Push a dependency to the remote.
        :param dep: Dependency's description.
        :param file: Dependency archive file.
        :param force: If true re-upload a file that already exists.
        """
        if not self.valid_shape:
            return
        if not file.exists():
            return
        result = self.query(dep)
        if len(result) != 0 and not force:
            print(f"WARNING: Cannot push dependency {dep.properties.name}: already on server.", file=stderr)
            return
        #
        try:
            if file.stat().st_size < 1024 * 1024 * 50:
                basic = HTTPBasicAuth(self.user, self.cred)
                post_data = {"action": "push"} | self.dep_to_code(dep)
                post_data["package"] = (file.name, open(file, "rb"), "application/octet-stream")
                encoder = MultipartEncoder(fields=post_data)
                monitor = MultipartEncoderMonitor(encoder)
                headers = {"Content-Type": monitor.content_type}
                resp = httppost(f"{self.destination}/api", auth=basic, data=monitor, headers=headers)
                if resp.status_code != 200:
                    self.valid_shape = False
                    print(f"ERROR connecting to server: {self.destination}: {resp.status_code}: {resp.reason}, see error.log", file=stderr)
                    with open("error.log", "ab") as fp:
                        fp.write(f"---- ERROR: {datetime.now()} ---- \n".encode('utf8'))
                        fp.write(resp.content)
                    return
            else:
                print("Large file upload detected")
                basic = HTTPBasicAuth(self.user, self.cred)
                post_data = {"action": "push"} | self.dep_to_code(dep)
                post_data["package"] = (file.name, open(file, "rb"), "application/octet-stream")
                encoder = MultipartEncoder(fields=post_data)
                monitor = MultipartEncoderMonitor(encoder)
                headers = {"Content-Type": monitor.content_type}
                resp = httppost(f"{self.destination}/upload", auth=basic, data=monitor, headers=headers)
                if resp.status_code != 200:
                    self.valid_shape = False
                    print(
                        f"ERROR connecting to server: {self.destination}: {resp.status_code}: {resp.reason}, see error.log",
                        file=stderr)
                    with open("error.log", "ab") as fp:
                        fp.write(f"---- ERROR: {datetime.now()} ---- \n".encode('utf8'))
                        fp.write(resp.content)
                    return
        except Exception as err:
            print(f"ERROR Exception during server push: {self.destination}: {err}")
            return

    def get_file(self, distant_name: str, destination: Path):
        """
        Download a file.
        TO IMPLEMENT IN DERIVED CLASS.
        :param distant_name: Name in the distant location.
        :param destination: Destination path.
        """
        self.valid_shape = False
        print(f"WARNING: __RemoteDatabase::get_file({distant_name},{destination}) not implemented.", file=stderr)

    def send_file(self, source: Path, distant_name: str):
        """
        Upload a file.
        TO IMPLEMENT IN DERIVED CLASS.
        :param source: File to upload.
        :param distant_name: Name in the distant location.
        """
        self.valid_shape = False
        print(f"WARNING: __RemoteDatabase::send_file({source}, {distant_name}) not implemented.", file=stderr)
