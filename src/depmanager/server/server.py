"""
Simple Server object for artifact management
"""
import platform
from pathlib import Path
from sys import stderr


class Server:
    """
    Simple artifact management server
    """

    def __init__(self, config_file: str = ""):
        self.port = 7456
        self.data_dir = Path()
        self.config = {}
        self.config_file = None
        if config_file not in ["", None]:
            self.config_file = Path(config_file).absolute()

        if self.config_file is None:
            self.__set_default_config()

        self.__load_config()
        self.library_file = self.data_dir / "content.pak"
        self.socket = None
        self.running = False

    def __set_default_config(self):
        self.port = 7456
        if platform.system() == "Windows":
            self.config_file = Path("C:/ProgramData/edm/edmserver.conf")
            self.data_dir = Path("C:/ProgramData/edm/data")
        else:
            self.config_file = Path("/etc/edm/edmserver.conf")
            self.data_dir = Path("/var/data/edm")
        if not self.config_file.exists():
            # save defaults
            self.__save_config()

    def __load_config(self):
        # save all the file content into a dictionary
        try:
            import json
            with open(self.config_file, "r") as fp:
                self.config = json.load(fp)
            # extract specific values from the file
            if "port" in self.config.keys():
                self.port = self.config["port"]
            if "data_dir" in self.config.keys():
                self.data_dir = Path(self.config["data_dir"])
            #
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except Exception as err:
            print(F"ERROR while loading config file {self.config_file}: {err}", file=stderr)
            exit(-666)

    def __save_config(self):
        try:
            # apply internal values to config file
            self.config["port"] = self.port
            self.config["data_dir"] = str(self.data_dir)
            # Write the config file
            import json
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as fp:
                fp.write(json.dumps(self.config, indent=4))
        except Exception as err:
            print(F"ERROR while saving config file {self.config_file}: {err}", file=stderr)
            exit(-666)

    def __check_local(self):
        if not self.library_file.exists():
            self.library_file.touch()

    def run(self):
        """
        Run the server
        """
        import socket
        from depmanager.server.process import client_connexion
        self.__check_local()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('', self.port))
        print(f"Starting server on port {self.port}")
        self.running = True
        while self.running:
            print(F"Listening...")
            self.socket.listen()
            conn, addr = self.socket.accept()
            cli = client_connexion(conn, addr, self)
            cli.run()

    def stop_request(self):
        """
        Request server to stop
        """
        self.running = False

    def search(self, query: dict):
        """
        Do a search query in the server
        :param query: the search query
        :return: The list of deps
        """
        result = []
        all_dep = self.__get_all_deps()
        for dep in all_dep:
            if dep.match(query=query):
                result.append(dep)
        return result

    def __get_all_deps(self):
        from depmanager.internal.dependency import Dependency
        with open(self.library_file, "r") as fp:
            lines = fp.readlines()
        result = []
        for line in lines:
            dep = Dependency()
            dep.from_str(line.strip())
            dep.location = self.data_dir / (dep.hash() + ".tgz")
            result.append(dep)
        return result
