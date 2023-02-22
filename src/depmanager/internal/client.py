"""
Client for conecting to server
"""
from sys import stderr


class Client:
    """
    Connector to a remote server
    """
    def __init__(self, url):
        import socket
        from depmanager.internal.database import DataBase
        self.__db = DataBase()
        self.url = url
        if self.url == "":
            print("ERROR no remotes!", file=stderr)
            exit(-666)
        self.stream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.status = "new"

    def connect(self, verbose: bool = False):
        """
        Connect the client to remote
        :param verbose:
        """
        if ":" in self.url:
            url, port = self.url.rsplit(":", 1)
        else:
            url = self.url
            port = 7456
        try:
            self.stream.connect((url, port))
            self.stream.send(b"coucou")
            data = self.stream.recv(32)
            if data != b"coucou":
                self.status = "fail"
            else:
                self.status = "connected"
        except Exception as err:
            self.status = "fail"
            if verbose:
                print(f"WARNING unable to connect to {url}:{port}", file=stderr)
                print(f"   {err}", file=stderr)
        if self.status != "connected":
            self.stream.close()

    def send(self, data: str):
        """
        Send data to the remotes
        :param data: What to send
        """
        if self.status not in ["connected"]:
            print(f"WARNING cannot send data Client not connected", file=stderr)
            return
        self.stream.send(data.encode())

    def received(self, ending: str = ""):
        """
        Received data
        :param ending: message for ending transmission
        :return: set of lines
        """
        if self.status not in ["connected"]:
            print(f"WARNING cannot send data Client not connected", file=stderr)
            return
        lines = []
        while True:
            data = self.stream.recv(512)
            if not data:
                break
            data = data.decode()
            if data == ending:
                break
            lines.append(data)
        return lines

    def search(self, query: dict):
        """
        Do a remote search
        :param query: what to search
        :return: list of dependency in the remote server
        """
        from depmanager.internal.dependency import Dependency
        query_str = "search"
        for key, val in query.items():
            query_str += f" {key}={val}"
        self.send(query_str)
        lines = self.received("END")
        if len(lines) == 0:
            return []
        if lines[0].startswith("No Results"):
            return []
        result = []
        for line in lines:
            dep = Dependency()
            dep.from_str(line)
            result.append(dep)
        return result
