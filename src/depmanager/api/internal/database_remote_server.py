"""
Remote FTP database
"""
import http.client
from base64 import b64encode
from datetime import datetime
from sys import stderr

from depmanager.api.internal.database_common import __RemoteDatabase
from pathlib import Path

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
        self.http = None
        self.secure = secure
        self.kind = ["srv","srvs"][secure]
        super().__init__(destination, default, user, cred)

    def connect(self):
        """
        Initialize the connection to remote host.
        TO IMPLEMENT IN DERIVED CLASS.
        """
        try:
            if self.secure:
                self.http = http.client.HTTPSConnection(self.destination, self.port)
            else:
                self.http = http.client.HTTPConnection(self.destination, self.port)
        except Exception as err:
            self.valid_shape = False
            print(f"ERROR while connecting to depmanager server {self.destination}: {err}.", file=stderr)

    def basic_auth(self):
        """
        Generate basic auth chain
        :return: Basic auth token
        """
        token = b64encode(f"{self.user}:{self.cred}".encode('utf-8')).decode("ascii")
        return f'Basic {token}'

    def get_dep_list(self):
        """
        Get a list of string describing dependency from the server.
        """
        try:
            headers = {'Authorization': self.basic_auth()}
            self.http.request("GET", "/api", headers=headers)
            resp = self.http.getresponse()
            if resp.status != 200:
                self.valid_shape = False
                print(f"ERROR connecting to server: {self.destination}: {resp.status}: {resp.reason}")
                return
            data = resp.read().decode("utf8").splitlines(keepends=False)
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
            key = "###"
            headers = {'Authorization': self.basic_auth(), 'Content-Type': f'multipart/form-data;boundary={key}'}
            post_data = {"action": "pull"} | self.dep_to_code(dep)
            self.http.request("POST", "/api", self.encode_request(post_data, key), headers=headers)
            resp = self.http.getresponse()
            if resp.status != 200:
                self.valid_shape = False
                print(f"ERROR connecting to server: {self.destination}: {resp.status}: {resp.reason}", file=stderr)
                print(f"      Server Data: {resp.read()}", file=stderr)
                return
            data = resp.read().decode("utf8").strip()
            fname = destination / data.rsplit("/",1)[-1]
            self.http.request("GET", data)
            resp = self.http.getresponse()
            if resp.status != 200:
                self.valid_shape = False
                print(f"ERROR retrieving file {data} from server {self.destination}: {resp.status}: {resp.reason}, see error.log", file=stderr)
                with open("error.log", "ab") as fp:
                    fp.write(f"---- ERROR: {datetime.now()} ---- \n".encode('utf8'))
                    fp.write(resp.read())
                return
            with open(fname, "wb") as fp:
                fp.write(resp.read())
        except Exception as err:
            print(f"ERROR Exception during server connexion: {self.destination}: {err}")
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
        try:
            key = "###"
            headers = {'Authorization': self.basic_auth(), 'Content-Type': f'multipart/form-data;boundary={key}'}
            post_data = {"action": "push"} | self.dep_to_code(dep)
            request = self.encode_request(post_data, key).encode()
            request += f'Content-Disposition: form-data; name="package"; filename="{file.name}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()
            with open(file, "rb") as fp:
                request += fp.read()
            request += f'--{key}--\r\n'.encode()
            self.http.request("POST", "/api", request, headers=headers)
            resp = self.http.getresponse()
            if resp.status != 200:
                self.valid_shape = False
                print(f"ERROR connecting to server: {self.destination}: {resp.status}: {resp.reason}, see error.log", file=stderr)
                with open("error.log", "ab") as fp:
                    fp.write(f"---- ERROR: {datetime.now()} ---- \n".encode('utf8'))
                    fp.write(resp.read())
                return
        except Exception as err:
            print(f"ERROR Exception during server connexion: {self.destination}: {err}")
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
