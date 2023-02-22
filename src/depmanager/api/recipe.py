class Recipe:
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
        pass

    def configure(self):
        pass

    def install(self):
        pass
