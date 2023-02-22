"""
Processing request
"""


class client_connexion:
    """
    Connexion client
    """
    commands = ["search"]

    def __init__(self, conn, addr, server):
        self.conn = conn
        self.addr = addr
        self.server = server
        self.accepted = False

    def search(self, arg_n):
        """
        Search for packages
        :param arg_n: arguments
        """
        query = {}
        args = arg_n.split()
        for arg in args:
            key, val = arg.split("=", 1)
            query[key.strip()] = val.strip()
        print(f"Query: {query}")
        results = self.server.search(query)
        if len(results) == 0:
            print("No Results found!")
            self.conn.send(b"No Results Found")
        for r in results:
            print(r.get_as_str())
            self.conn.send(r.get_as_str().encode())
        self.conn.send(b"END")

    def run(self):
        """
        Process the client connexion
        """
        print(F"Connection from {self.addr}")
        while True:
            data = self.conn.recv(512)
            if not data:
                break
            # Ping request
            if data == b"coucou":
                self.conn.send(b"coucou")
                self.accepted = True
                print(F"Reply wellcome to {self.addr}")
                continue
            if not self.accepted:
                # Kick all bad client
                break
            # Quit request
            if data == b"quit":
                print(f"Quit instruction")
                self.server.stop_request()
                continue
            cmd, arg_n = data.decode().split(" ", 1)
            known = False
            for t_cmd in self.commands:
                if t_cmd == cmd:
                    getattr(self, cmd)(arg_n)
                    known = True
                    break
            # unknown request
            if not known:
                print(f"Receive Unknown request from {self.addr}: {data}")
