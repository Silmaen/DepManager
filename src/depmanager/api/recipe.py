"""
Base recipe for building package.
"""
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
    settings = {"os":"", "arch":"", "compiler":"", "install_path":Path()}

    def __init__(self, possible: bool=True):
        self.possible = possible

    def to_str(self):
        """
        Get string representing recipe.
        :return: String.
        """
        os = "any"
        if len(self.settings["os"]) > 0:
            os =self.settings["os"]
        arch = "any"
        if len(self.settings["arch"]) > 0:
            arch = self.settings["arch"]
        return f"{self.name}/{self.version} on {os}/{arch} as {self.kind} from {self.source_dir}"

    def define(self,os, arch, compiler, install_path):
        """
        Actualize parameters
        :param os:
        :param arch:
        :param compiler:
        :param install_path:
        """
        self.settings["os"] = os
        self.settings["arch"] = arch
        self.settings["compiler"] = compiler
        self.settings["install_path"] = install_path

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
