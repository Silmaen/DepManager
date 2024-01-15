"""
Base recipe for building package.
"""
from datetime import datetime
from pathlib import Path


class Recipe:
    """
    Recipe for package creation.
    """

    name = ""
    version = ""
    source_dir = ""
    cache_variables = {}
    config = ["Debug", "Release"]
    kind = "shared"
    dependencies = []
    settings = {"os": "", "arch": "", "compiler": "", "install_path": Path()}

    def __init__(self, path: Path = None, possible: bool = True):
        self.possible = possible
        self.path = path

    def to_str(self):
        """
        Get string representing recipe.
        :return: String.
        """
        result = f"{self.name}/{self.version}"
        if self.kind in ["static", "shared"]:
            os = "any"
            if len(self.settings["os"]) > 0:
                os = self.settings["os"]
            arch = "any"
            if len(self.settings["arch"]) > 0:
                arch = self.settings["arch"]
            result += f" {os}/{arch}"
            if os == "Linux":
                result += f"/glibc_{self.settings['glibc']}"
        result += f" as {self.kind}"
        return result

    def define(self, os, arch, compiler, install_path, glibc="", creation_date=None):
        """
        Actualize parameters
        :param os:
        :param arch:
        :param compiler:
        :param install_path:
        :param glibc:
        :param creation_date:
        """
        self.settings["os"] = os
        self.settings["arch"] = arch
        self.settings["compiler"] = compiler
        self.settings["install_path"] = install_path
        self.settings["glibc"] = glibc
        if creation_date is None or type(creation_date) is not datetime:
            self.settings["build_date"] = datetime.now(
                tz=datetime.now().astimezone().tzinfo
            ).replace(microsecond=0)
        else:
            self.settings["build_date"] = creation_date

    def source(self):
        """
        Method executed when getting the sources.
        """
        pass

    def configure(self):
        """
        Method executed before the call to configure cmake.
        """
        pass

    def install(self):
        """
        Method executed during installation.
        """
        pass

    def clean(self):
        """
        Method executed at the end.
        """
        pass
