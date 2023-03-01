"""
Base recipe for building package
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
    lib_type = "shared"
    generator = ""

    def source(self):
        """
        Method executed when getting the sources
        """
        pass

    def configure(self):
        """
        Method executed before the call to configure cmake
        """
        pass

    def install(self):
        """
        Method executed during installation
        """
        pass
