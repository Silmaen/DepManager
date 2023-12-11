"""
Remote FTP database
"""
from datetime import datetime
from pathlib import Path
from sys import stderr

from depmanager.api.internal.database_common import __RemoteDatabase
from depmanager.api.internal.dependency import Dependency
from requests import get as http_get, post as http_post
from requests.auth import HTTPBasicAuth
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor


class RemoteDatabaseServer(__RemoteDatabase):
    """
    Remote database using server protocol.
    """

    def __init__(
        self,
        destination: str,
        port: int = -1,
        secure: bool = False,
        default: bool = False,
        user: str = "",
        cred: str = "",
        verbosity: int = 0,
    ):
        self.port = port
        if self.port == -1:
            if secure:
                self.port = 443
            else:
                self.port = 80
        self.secure = secure
        self.kind = ["srv", "srvs"][secure]
        true_destination = f"http{['', 's'][secure]}://{destination}"
        if secure:
            if self.port != 443:
                true_destination += f":{self.port}"
        else:
            if self.port != 80:
                true_destination += f":{self.port}"
        super().__init__(
            destination=true_destination,
            default=default,
            user=user,
            cred=cred,
            kind=self.kind,
            verbosity=verbosity,
        )
        self.remote_type = "Dependency Server"

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
            if self.verbosity > 3:
                print("Query dep list from remote.")
            basic = HTTPBasicAuth(self.user, self.cred)
            resp = http_get(f"{self.destination}/api", auth=basic)
            if resp.status_code != 200:
                self.valid_shape = False
                print(
                    f"ERROR connecting to server: {self.destination}: {resp.status_code}: {resp.reason}",
                    file=stderr,
                )
                print(f"  Response from server:\n{resp.text}", file=stderr)
                return
            data = resp.text.splitlines(keepends=False)
            self.deps_from_strings(data)
        except Exception as err:
            print(
                f"ERROR Exception during server connexion: {self.destination}: {err}",
                file=stderr,
            )
            return

    @staticmethod
    def dep_to_code(dep: Dependency):
        """

        :param dep:
        :return:
        """
        data = {}
        if dep.properties.name not in ["", None]:
            data["name"] = dep.properties.name
        if dep.properties.version not in ["", None]:
            data["version"] = dep.properties.version
        data["glibc"] = ""
        if dep.properties.glibc not in ["", None]:
            data["glibc"] = dep.properties.glibc
        if dep.properties.build_date not in ["", None]:
            data["build_date"] = dep.properties.build_date.isoformat()
        # os
        if dep.properties.os.lower() == "windows":
            data["os"] = "w"
        if dep.properties.os.lower() == "linux":
            data["os"] = "l"
        if dep.properties.os.lower() == "any":
            data["os"] = "a"
        # arch
        if dep.properties.arch.lower() == "x86_64":
            data["arch"] = "x"
        if dep.properties.arch.lower() == "aarch64":
            data["arch"] = "a"
        if dep.properties.arch.lower() == "any":
            data["arch"] = "y"
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
        if dep.properties.compiler.lower() == "any":
            data["compiler"] = "a"
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
            resp = http_post(f"{self.destination}/api", auth=basic, data=post_data)

            if resp.status_code != 200:
                self.valid_shape = False
                print(
                    f"ERROR connecting to server: {self.destination}: {resp.status_code}: {resp.reason}",
                    file=stderr,
                )
                print(f"      Server Data: {resp.text}", file=stderr)
                return
            data = resp.text.strip()
            filename = data.rsplit("/", 1)[-1]
            if filename.startswith(dep.properties.name):
                filename = filename.replace(dep.properties.name, "")
            file_name = destination / filename
            resp = http_get(f"{self.destination}{data}", auth=basic)
            if resp.status_code != 200:
                self.valid_shape = False
                server_error = f"{self.destination}: {resp.status_code}: {resp.reason}"
                print(
                    f"ERROR retrieving file {data} from server {server_error}, see error.log",
                    file=stderr,
                )
                with open("error.log", "ab") as fp:
                    fp.write(f"---- ERROR: {datetime.now()} ---- \n".encode("utf8"))
                    fp.write(resp.content)
                return
            with open(file_name, "wb") as fp:
                fp.write(resp.content)
            return filename
        except Exception as err:
            print(
                f"ERROR Exception during server pull: {self.destination}: {err}",
                file=stderr,
            )
            return

    def create_callback(self, encoder):
        """
        Create a callback for the given encoder.
        :param encoder: The encoder.
        :return: A monitor call back.
        """
        from depmanager.api.internal.common import pretty_size_print

        encoder_len = encoder.len
        if self.verbosity > 0:
            print(
                f"[{pretty_size_print(0)} of {pretty_size_print(encoder_len)}]                    ",
                flush=True,
                end="\r",
            )

        def callback(monitor):
            """
            The callback function.
            :param monitor: The monitor
            """
            if self.verbosity > 0:
                print(
                    f"[{pretty_size_print(monitor.bytes_read)} of {pretty_size_print(encoder_len)}]                    ",
                    flush=True,
                    end="\r",
                )

        return callback

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
            print(
                f"WARNING: Cannot push dependency {dep.properties.name}: already on server.",
                file=stderr,
            )
            return
        #
        try:
            basic = HTTPBasicAuth(self.user, self.cred)
            post_data = {"action": "push"} | self.dep_to_code(dep)
            post_data["package"] = (
                file.name,
                open(file, "rb"),
                "application/octet-stream",
            )
            encoder = MultipartEncoder(fields=post_data)
            if file.stat().st_size < 1:
                monitor = MultipartEncoderMonitor(encoder)
                headers = {"Content-Type": monitor.content_type}
                resp = http_post(
                    f"{self.destination}/api", auth=basic, data=monitor, headers=headers
                )
            else:
                monitor = MultipartEncoderMonitor(
                    encoder, callback=self.create_callback(encoder)
                )
                headers = {"Content-Type": monitor.content_type}
                resp = http_post(
                    f"{self.destination}/upload",
                    auth=basic,
                    data=monitor,
                    headers=headers,
                )
                if self.verbosity > 0:
                    print()

            if resp.status_code == 201:
                print(
                    f"WARNING coming from server: {self.destination}: {resp.status_code}: {resp.reason}",
                    file=stderr,
                )
                print(f"response: {resp.content.decode('utf8')}", file=stderr)
                return
            if resp.status_code != 200:
                self.valid_shape = False
                print(
                    f"ERROR connecting to server: {self.destination}: {resp.status_code}: {resp.reason}, see error.log",
                    file=stderr,
                )
                with open("error.log", "ab") as fp:
                    fp.write(f"---- ERROR: {datetime.now()} ---- \n".encode("utf8"))
                    fp.write(resp.content)
                return
        except Exception as err:
            print(
                f"ERROR Exception during server push: {self.destination}: {err}",
                file=stderr,
            )
            return

    def delete(self, dep: Dependency):
        """
        Suppress the dependency from the server
        :param dep: Dependency information.
        :return: True if success.
        """
        if not self.valid_shape:
            return
        result = self.query(dep)
        if len(result) == 0:
            print(
                f"WARNING: Cannot suppress dependency {dep.properties.name}: not on server.",
                file=stderr,
            )
            return
        if len(result) > 1:
            print(
                f"WARNING: Cannot suppress dependency {dep.properties.name}: multiple dependencies match on server.",
                file=stderr,
            )
            return
        try:
            basic = HTTPBasicAuth(self.user, self.cred)
            post_data = {"action": "delete"} | self.dep_to_code(dep)
            resp = http_post(f"{self.destination}/api", auth=basic, data=post_data)

            if resp.status_code != 200:
                self.valid_shape = False
                print(
                    f"ERROR connecting to server: {self.destination}: {resp.status_code}: {resp.reason}",
                    file=stderr,
                )
                print(f"      Server Data: {resp.text}", file=stderr)
                return False
            return True
        except Exception as err:
            print(
                f"ERROR Exception during server pull: {self.destination}: {err}",
                file=stderr,
            )
            return False

    def get_file(self, distant_name: str, destination: Path):
        """
        Download a file.
        TO IMPLEMENT IN DERIVED CLASS.
        :param distant_name: Name in the distant location.
        :param destination: Destination path.
        """
        self.valid_shape = False
        print(
            f"WARNING: RemoteDatabaseServer::get_file({distant_name},{destination}) not implemented.",
            file=stderr,
        )

    def send_file(self, source: Path, distant_name: str):
        """
        Upload a file.
        TO IMPLEMENT IN DERIVED CLASS.
        :param source: File to upload.
        :param distant_name: Name in the distant location.
        """
        self.valid_shape = False
        print(
            f"WARNING: RemoteDatabaseServer::send_file({source}, {distant_name}) not implemented.",
            file=stderr,
        )

    def suppress(self, dep: Dependency) -> bool:
        """
        Suppress the dependency from the server
        TO IMPLEMENT IN DERIVED CLASS.
        :param dep: Dependency information.
        :return: True if success.
        """
        self.valid_shape = False
        print(
            f"WARNING: RemoteDatabaseServer::suppress({dep}) not implemented.",
            file=stderr,
        )

    def get_server_version(self):
        """
        Get the version running on the server.
        :return: Server's version number.
        """
        try:
            basic = HTTPBasicAuth(self.user, self.cred)
            post_data = {"action": "version"}
            resp = http_post(f"{self.destination}/api", auth=basic, data=post_data)

            if resp.status_code != 200:
                self.valid_shape = False
                print(
                    f"ERROR connecting to server: {self.destination}: {resp.status_code}: {resp.reason}",
                    file=stderr,
                )
                print(f"      Server Data: {resp.text}", file=stderr)
                return "unknown"
            data = resp.text.strip().split("version:")[-1].strip()
            return data
        except Exception as err:
            print(
                f"ERROR Exception during server pull: {self.destination}: {err}",
                file=stderr,
            )
            return "unknown"
