"""
Description of a dependency
"""
from pathlib import Path


def valid_str(bob):
    """
    Check for valid string.
    :param bob: String to check.
    :return: True if Valid
    """
    if bob in [None, ""]:
        return False
    if "*" in bob:
        return False
    if "?" in bob:
        return False
    if "[" in bob:
        return False
    if "]" in bob:
        return False
    return True


class Dependency:
    """
    Object describing the dependency
    """
    name = ""
    version = ""
    os = ""
    arch = ""
    lib_type = ""  # Possible 'shared', 'static', 'header'
    compiler = ""
    location = Path()

    def __repr__(self):
        return F"{self.name}/{self.version}"

    def hash(self):
        """
        Get a hash for dependency infos
        :return: The hash as string
        """
        from hashlib import sha1
        hash_ = sha1()
        glob = self.name + self.version + self.os + self.arch + self.lib_type + self.compiler
        hash_.update(glob.encode())
        return str(hash_.hexdigest())

    def is_valid(self):
        """
        Check for dependency validity.
        :return: True if everything OK.
        """
        if self.location == Path():
            return False
        if not self.location.exists():
            return False
        if self.lib_type not in ['shared', 'static', 'header']:
            return False
        return valid_str(self.arch) and \
            valid_str(self.name) and \
            valid_str(self.compiler) and \
            valid_str(self.version) and \
            valid_str(self.os)

    def from_path(self, path: Path):
        """
        Read given path for setting this dependency.
        :param path: Path to check.
        """
        if not path.exists():
            return
        if not (path / "edp.info").exists():
            return
        self.location = path
        with open(self.location / "edp.info", "r") as fp:
            lines = fp.readlines()
        for line in lines:
            items = line.split()
            if len(items) != 2:
                continue
            key = items[0]
            val = items[1]
            if key not in ["name", "version", "os", "arch", "lib_type", "compiler"] or val in [None, ""]:
                continue
            if key == "name":
                self.name = val
            if key == "version":
                self.version = val
            if key == "os":
                self.os = val
            if key == "arch":
                self.arch = val
            if key == "lib_type":
                self.lib_type = val
            if key == "compiler":
                self.compiler = val

    def save_info(self):
        """
        Save infos into file.
        """
        if self.location == Path():
            return
        if not self.location.exists():
            return
        with open(self.location / "edp.info", "w") as fp:
            fp.write(F"name {self.name}")
            fp.write(F"version {self.version}")
            fp.write(F"os {self.os}")
            fp.write(F"arch {self.arch}")
            fp.write(F"lib_type {self.lib_type}")
            fp.write(F"compiler {self.compiler}")

    def match(self, query: dict):
        """
        Match dependency with the given query.
        :param query: The Details to look.
        :return: True if positive match.
        """
        from fnmatch import translate
        from re import compile
        for attr in ["name", "version", "os", "arch", "lib_type", "compiler"]:
            if attr in query.keys():
                if not compile(translate(query[attr])).match(getattr(self, attr)):
                    return False
        return True

    def get_cmake_config_dir(self):
        """
        Get the path to the cmake config files for find package
        :return: Cmake config path
        """
        if not self.is_valid():
            return Path()
        lst = list(self.location.rglob("*config.cmake"))
        if len(lst) == 0:
            return Path()
        return lst[0].parent

    def get_as_str(self):
        """
        Get a human-readable string
        :return: A string
        """
        return F"  {self.name}/{self.version} [{self.arch}, {self.lib_type}, {self.os}, {self.compiler}]"

    def from_str(self, data: str):
        """
        Do the inverse of get_as_string
        :param data: the string representing the dependency as in get_as_str
        """
        idata = data.replace("[", "")
        idata = idata.replace("]", "")
        idata = idata.replace(",", "")
        idata = idata.replace("  ", "")
        idata = idata.replace("/", " ")
        items = idata.split()
        if len(items) != 6:
            print(f"Warning bdly formed string {data}")
            return
        self.name = items[0]
        self.version = items[1]
        self.arch = items[2]
        self.lib_type = items[3]
        self.os = items[4]
        self.compiler = items[5]
