"""
Remote FTP database
"""

from datetime import datetime
from pathlib import Path

from api.internal.common import client_api
from api.internal.database_common import __RemoteDatabase
from api.internal.dependency import Dependency, version_lt
from api.internal.messaging import log
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
        )
        self.remote_type = "Dependency Server"
        self.server_api_version = "1.0.0"
        self.api_url = "/api"
        self.upload_url = "/upload"
        self.version = "1.0"
        self.connected = False

    def connect(self):
        """
        Initialize the connection to remote host.
        TO IMPLEMENT IN DERIVED CLASS.
        """
        if self.connected:
            return
        basic = HTTPBasicAuth(self.user, self.cred)
        try:
            resp = http_post(
                f"{self.destination}{self.api_url}",
                auth=basic,
                data={"action": "version"},
            )
        except Exception as err:
            log.warn(f"Exception during server connexion: {self.destination}: {err}")
            self.valid_shape = False
            self.connected = False
            return

        if resp.status_code != 200:
            self.valid_shape = False
            return
        try:
            self.server_api_version = "1.0.0"
            for line in resp.text.splitlines(keepends=False):
                if line.startswith("version"):
                    self.version = line.strip().split("version:")[-1].strip()
                elif line.startswith("api_version:"):
                    self.server_api_version = (
                        line.strip().split("api_version:")[-1].strip()
                    )

            log.debug(
                f"Connected to server {self.destination} version {self.version} API: {self.server_api_version}"
            )
            self.valid_shape = True
        except Exception as err:
            log.fata(f"Exception during server connexion: {self.destination}: {err}")
            self.valid_shape = False
        self.connected = True

    def get_dep_list(self):
        """
        Get a list of string describing dependency from the server.
        """
        self.connect()
        if not self.valid_shape:
            return
        try:
            log.debug("Query dep list from remote.")
            basic = HTTPBasicAuth(self.user, self.cred)
            headers = {
                "X-API-Version": client_api,
            }
            resp = http_get(
                f"{self.destination}{self.api_url}", auth=basic, headers=headers
            )
            if resp.status_code != 200:
                self.valid_shape = False
                log.error(
                    f"connecting to server: {self.destination}: {resp.status_code}: {resp.reason}"
                )
                log.error(f"  Response from server:\n{resp.text}")
                return
            data = resp.text.splitlines(keepends=False)
            self.deps_from_strings(data)
        except Exception as err:
            log.error(f"Exception during server connexion: {self.destination}: {err}")
            return

    def dep_to_code(self, dep: Dependency):
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
        # abi
        if self.server_api_version == "1.0.0":
            if dep.properties.abi.lower() == "gnu":
                data["abi"] = "g"
            elif dep.properties.abi.lower() == "msvc":
                data["abi"] = "m"
            elif dep.properties.abi.lower() == "any":
                data["abi"] = "a"
            else:
                log.warn(f"WARNING: Unsupported ABI type {dep.properties.abi}.")
        else:
            if dep.properties.abi.lower() == "gnu":
                data["abi"] = "g"
            elif dep.properties.abi.lower() == "llvm":
                data["abi"] = "l"
            elif dep.properties.abi.lower() == "msvc":
                data["abi"] = "m"
            elif dep.properties.abi.lower() == "any":
                data["abi"] = "a"
            else:
                log.warn(f"WARNING: Unsupported ABI type {dep.properties.abi}.")
        if version_lt("2.0.0", self.server_api_version):
            data["dependencies"] = f"{dep.properties.dependencies}"
            if dep.description not in ["", None]:
                data["description"] = f"{dep.description}"
        return data

    def pull(self, dep: Dependency, destination: Path):
        """
        Pull a dependency from remote.
        :param dep: Dependency information.
        :param destination: Destination directory
        """
        from rich.progress import (
            Progress,
            SpinnerColumn,
            BarColumn,
            TextColumn,
            DownloadColumn,
            TransferSpeedColumn,
        )

        self.connect()
        if not self.valid_shape:
            return
        if destination.exists() and not destination.is_dir():
            return
        deps = self.query(dep)
        if len(deps) != 1:
            return
        # get the download url:
        try:
            basic = HTTPBasicAuth(self.user, self.cred)
            post_data = {"action": "pull"} | self.dep_to_code(dep)
            resp = http_post(
                f"{self.destination}{self.api_url}", auth=basic, data=post_data
            )
            if resp.status_code != 200:
                self.valid_shape = False
                log.error(
                    f"connecting to server: {self.destination}: {resp.status_code}: {resp.reason}"
                )
                log.error(f"      Server Data: {resp.text}")
                return
            data = resp.text.strip()
            filename = data.rsplit("/", 1)[-1]
            if filename.startswith(dep.properties.name):
                filename = filename.replace(dep.properties.name, "")
            file_name = destination / filename

            headers = {
                "X-API-Version": client_api,
            }
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
            ) as progress:
                resp = http_get(
                    f"{self.destination}{data}", auth=basic, headers=headers
                )
                if resp.status_code != 200:
                    self.valid_shape = False
                    server_error = (
                        f"{self.destination}: {resp.status_code}: {resp.reason}"
                    )
                    log.error(
                        f"retrieving file {data} from server {server_error}, see error.log"
                    )
                    with open("error.log", "ab") as fp:
                        fp.write(f"---- ERROR: {datetime.now()} ---- \n".encode("utf8"))
                        fp.write(resp.content)
                    return
                total_size = int(resp.headers.get("content-length", 0))
                task = progress.add_task(f"Downloading {filename}", total=total_size)

                with open(file_name, "wb") as fp:
                    for chunk in resp.iter_content(chunk_size=1024):
                        fp.write(chunk)
                        progress.update(task, advance=len(chunk))
            return
        except Exception as err:
            log.error(f"Exception during server pull: {self.destination}: {err}")
            return

    def create_callback(self, progress, task):
        """
        Create a callback for the given encoder.
        :param progress: Progress object.
        :param task: Task identifier.
        :return: A monitor callback.
        """

        def callback(monitor):
            """
            The callback function.
            :param monitor: The monitor
            """
            progress.update(task, completed=monitor.bytes_read)

        return callback

    def push(self, dep: Dependency, file: Path, force: bool = False):
        """
        Push a dependency to the remote.
        :param dep: Dependency's description.
        :param file: Dependency archive file.
        :param force: If true, re-upload a file that already exists.
        """
        from rich.progress import (
            Progress,
            SpinnerColumn,
            TextColumn,
            BarColumn,
            DownloadColumn,
            TransferSpeedColumn,
        )

        self.connect()
        if not self.valid_shape:
            return
        if not file.exists():
            return
        result = self.query(dep)
        if len(result) != 0 and not force:
            log.warn(
                f"WARNING: Cannot push dependency {dep.properties.name}: already on server."
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
            log.debug(f"Pushing data {post_data}")
            encoder = MultipartEncoder(fields=post_data)
            dest_url = f"{self.destination}{self.api_url}"

            file_size = file.stat().st_size

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
            ) as progress:
                task = progress.add_task(f"Uploading {file.name}", total=encoder.len)

                if file_size < 1:
                    monitor = MultipartEncoderMonitor(encoder)
                    headers = {"Content-Type": monitor.content_type}
                    resp = http_post(
                        dest_url,
                        auth=basic,
                        data=monitor,
                        headers=headers,
                    )
                else:
                    monitor = MultipartEncoderMonitor(
                        encoder, callback=self.create_callback(progress, task)
                    )
                    headers = {
                        "Content-Type": monitor.content_type,
                        "X-API-Version": client_api,
                    }
                    dest_url = f"{self.destination}{self.upload_url}"
                    resp = http_post(
                        dest_url,
                        auth=basic,
                        data=monitor,
                        headers=headers,
                    )

            if resp.status_code == 201:
                log.warn(
                    f"WARNING coming from server: {dest_url}: {resp.status_code}: {resp.reason}"
                )
                log.warn(f"response: {resp.content.decode('utf8')}")
                return
            if resp.status_code != 200:
                self.valid_shape = False
                log.error(
                    f"connecting to server: {dest_url}: {resp.status_code}: {resp.reason}, see error.log"
                )
                with open("error.log", "ab") as fp:
                    fp.write(f"---- ERROR: {datetime.now()} ---- \n".encode("utf8"))
                    fp.write(resp.content)
                    fp.write("\n".encode("utf8"))
                    fp.write(str(post_data).encode("utf8"))
                    fp.write("\n".encode("utf8"))
                return
        except Exception as err:
            log.error(f"Exception during server push: {self.destination}: {err}")
            return
        # Actualization the list
        self.get_dep_list()

    def delete(self, dep: Dependency):
        """
        Suppress the dependency from the server
        :param dep: Dependency information.
        :return: True if success.
        """
        self.connect()
        if not self.valid_shape:
            return False
        result = self.query(dep)
        if len(result) == 0:
            log.warn(
                f"WARNING: Cannot suppress dependency {dep.properties.name}: not on server."
            )
            return False
        if len(result) > 1:
            log.warn(
                f"WARNING: Cannot suppress dependency {dep.properties.name}: multiple dependencies match on server."
            )
            return False
        try:
            basic = HTTPBasicAuth(self.user, self.cred)
            post_data = {"action": "delete"} | self.dep_to_code(dep)
            resp = http_post(
                f"{self.destination}{self.api_url}", auth=basic, data=post_data
            )

            if resp.status_code != 200:
                self.valid_shape = False
                log.error(
                    f"connecting to server: {self.destination}: {resp.status_code}: {resp.reason}"
                )
                log.error(f"      Server Data: {resp.text}")
                return False
            return True
        except Exception as err:
            log.error(f"Exception during server pull: {self.destination}: {err}")
            return False

    def get_file(self, distant_name: str, destination: Path):
        """
        Download a file.
        TO IMPLEMENT IN DERIVED CLASS.
        :param distant_name: Name in the distant location.
        :param destination: Destination path.
        """
        self.valid_shape = False
        log.warn(
            f"WARNING: RemoteDatabaseServer::get_file({distant_name},{destination}) not implemented."
        )

    def send_file(self, source: Path, distant_name: str):
        """
        Upload a file.
        TO IMPLEMENT IN DERIVED CLASS.
        :param source: File to upload.
        :param distant_name: Name in the distant location.
        """
        self.valid_shape = False
        log.warn(
            f"WARNING: RemoteDatabaseServer::send_file({source}, {distant_name}) not implemented."
        )

    def suppress(self, dep: Dependency) -> bool:
        """
        Suppress the dependency from the server
        TO IMPLEMENT IN DERIVED CLASS.
        :param dep: Dependency information.
        :return: True if success.
        """
        self.valid_shape = False
        log.warn(f"WARNING: RemoteDatabaseServer::suppress({dep}) not implemented.")
        return False

    def get_server_version(self):
        """
        Get the version running on the server.
        :return: Server's version number.
        """
        self.connect()
        if not self.valid_shape:
            return "0.0.0"
        return self.version

    def get_remote_info(self) -> dict:
        """
        Get information about the remote.
        :return: Dictionary with remote information.
        """
        self.connect()
        return {
            "destination": str(self.destination),
            "default": self.default,
            "user": self.user,
            "kind": self.kind,
            "remote_type": self.remote_type,
            "version": self.version,
            "api_version": self.server_api_version,
        }
