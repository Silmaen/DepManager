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

    def to_str(self):
        """
        Get string representing recipe.
        :return: String.
        """
        return f"{self.name}/{self.version} on {self.os}/{self.arch} as {self.kind} from {self.source_dir}"

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
