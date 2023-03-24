"""
Base recipe for building package.
"""


class Recipe:
    """
    Recipe for package creation.
    """
    name = ""
    version = ""
    os = []
    arch = []
    source_dir = ""
    cache_variables = {}
    config = ["Debug", "Release"]
    kind = "shared"
    generator = ""
    dependencies = []
    settings = {"os":"", "arch":"", "compiler":""}

    def to_str(self):
        """
        Get string representing recipe.
        :return: String.
        """
        os = "any"
        if len(self.os) > 0:
            os = self.os
        arch = "any"
        if len(self.arch) > 0:
            arch = self.arch
        return f"{self.name}/{self.version} on {os}/{arch} as {self.kind} from {self.source_dir}"

    def define(self,os, arch, compiler):
        """
        Actualize parameters
        :param os:
        :param arch:
        :param compiler:
        """
        self.settings["os"] = os
        self.settings["arch"] = arch
        self.settings["compiler"] = compiler

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
