"""
Definition of config file.
"""
from pathlib import Path
from sys import stderr

from yaml import full_load


class ConfigFile:
    """
    Class for exception-safe management of a configuration file.
    """

    def __init__(self, file: Path):
        self.data = None
        self.path = file
        if self.path.exists():
            self.load()

    def load(self):
        """
        Try to load the file.
        """
        try:
            with open(self.path, "r") as file:
                self.data = full_load(file)
        except Exception as err:
            print(f"CONFIG FILE: load, {err}", file=stderr)
            self.data = None

    def has_remote(self):
        """
        Check if the configuration has a "remote" section.
        :return: True if a remote section found.
        """
        try:
            if self.data is None:
                return False
            if type(self.data) is not dict:
                return False
            if "remote" not in self.data:
                return False
            return type(self.data["remote"]) is dict
        except Exception as err:
            print(f"CONFIG FILE: has_remote, {err}", file=stderr)
            return False

    def has_packages(self):
        """
        Check if configuration has a "packages" section.
        :return: True if packages section found.
        """
        try:
            if self.data is None:
                return False
            if type(self.data) is not dict:
                return False
            if "packages" not in self.data:
                return False
            return type(self.data["packages"]) is dict
        except Exception as err:
            print(f"CONFIG FILE: has_packages, {err}", file=stderr)
            return False

    def server_to_add(self):
        """
        Get the server information.
        :return: Server information if exists or empty dictionary.
        """
        if not self.has_remote():
            return {}
        remote = self.data["remote"]
        if type(remote) is not dict:
            return {}
        try:
            if "server" not in remote:
                return {}
            if type(remote["server"]) is dict:
                return remote["server"]
            else:
                return {}
        except Exception as err:
            print(f"CONFIG FILE: server_to_add, {err}", file=stderr)
            return {}

    def do_pull(self):
        """
        Is pull authorized?
        :return: True if pull authorized.
        """
        if not self.has_remote():
            return False
        remote = self.data["remote"]
        if "pull-newer" in remote:
            if remote["pull-newer"]:
                return True
        if "pull" in remote:
            if remote["pull"]:
                return True
        return False

    def do_pull_newer(self):
        """
        Is pull newer authorized?
        :return: True if pull newer authorized.
        """
        if not self.has_remote():
            return False
        remote = self.data["remote"]
        if "pull-newer" in remote:
            if remote["pull-newer"]:
                return True
        return False

    def get_packages(self):
        """
        Get the packages dictionary.
        :return: Packages dictionary.
        """
        if not self.has_packages():
            return {}
        return self.data["packages"]
