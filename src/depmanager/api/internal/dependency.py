"""
Dependency object.
"""
import platform
from pathlib import Path
from sys import stderr

kinds = ["shared", "static", "header", "any"]
compilers = ["gnu", "msvc"]
oses = ["Windows", "Linux"]
arches = ["x86_64", "aarch64"]

# TODO: system introspection
default_kind = kinds[0]
default_compiler = compilers[0]


def format_os(os_str: str):
    if os_str not in oses:
        exit(666)
    return os_str


def format_arch(arch_str: str):
    if arch_str == "AMD64":
        arch_str = "x86_64"
    if arch_str not in arches:
        exit(666)
    return arch_str


default_os = format_os(platform.system())
default_arch = format_arch(platform.machine())


class Props:
    """
    Class for the details about items.
    """
    name = "*"
    version = "*"
    os = default_os
    arch = default_arch
    kind = default_kind
    compiler = default_compiler
    query = False

    def __init__(self, data=None, query: bool = False):
        self.name = "*"
        self.version = "*"
        self.os = default_os
        self.arch = default_arch
        self.kind = default_kind
        self.compiler = default_compiler
        self.query = query
        if type(data) == str:
            self.from_str(data)
        elif type(data) == dict:
            self.from_dict(data)

    def __eq__(self, other):
        if type(other) != Props:
            return False
        return self.name == other.name \
            and self.version == other.version \
            and self.os == other.os \
            and self.arch == other.arch \
            and self.kind == other.kind \
            and self.compiler == other.compiler

    def __lt__(self, other):
        if type(other) != Props:
            return False
        if self.name != other.name:
            return self.name < other.name
        if self.version != other.version:
            self_version_item = self.version.split(".")
            other_version_item = other.version.split(".")
            for i in range(min(len(self_version_item), len(other_version_item))):
                if self_version_item[i] != other_version_item[i]:
                    try:
                        return int(self_version_item[i]) > int(other_version_item[i])
                    except:
                        return self_version_item[i] > other_version_item[i]
            return len(self_version_item) > len(other_version_item)
        if self.os != other.os:
            return self.os < other.os
        if self.arch != other.arch:
            return self.arch < other.arch
        if self.kind != other.kind:
            return self.kind < other.kind
        if self.compiler != other.compiler:
            return self.compiler < other.compiler
        return False

    def __le__(self, other):
        return self == other or self < other

    def __gt__(self, other):
        return other < self

    def __ge__(self, other):
        return self == other or self > other

    def from_dict(self, data: dict):
        """
        Create props from a dictionary.
        :param data: The input dictionary.
        """
        self.name = "*"
        if "name" in data:
            self.name = data["name"]
        self.version = "*"
        if "version" in data:
            self.version = data["version"]
        if self.query:
            self.os = "*"
            self.arch = "*"
            self.kind = "*"
            self.compiler = "*"
        else:
            self.os = default_os
            self.arch = default_arch
            self.kind = default_kind
            self.compiler = default_compiler
        if "os" in data:
            self.os = data["os"]
        if "arch" in data:
            self.arch = data["arch"]
        if "kind" in data:
            self.kind = data["kind"]
        if "compiler" in data:
            self.compiler = data["compiler"]

    def to_dict(self):
        """
        Get a dictionary of data.
        :return: Dictionary.
        """
        return {
            "name"    : self.name,
            "version" : self.version,
            "os"      : self.os,
            "arch"    : self.arch,
            "kind"    : self.kind,
            "compiler": self.compiler
        }

    def match(self, other):
        """
        Check similarity between props.
        :param other: The other props to compare.
        :return: True if regexp match.
        """
        from fnmatch import translate
        from re import compile
        for attr in ["name", "version", "os", "arch", "kind", "compiler"]:
            if attr not in ["name", "version"] and (getattr(other, attr) == "any" or getattr(self, attr) == "any"):
                continue
            if not compile(translate(getattr(other, attr))).match(getattr(self, attr)):
                return False
        return True

    def hash(self):
        """
        Get a hash for dependency infos.
        :return: The hash as string.
        """
        from hashlib import sha1
        hash_ = sha1()
        glob = self.name + self.version + self.os + self.arch + self.kind + self.compiler
        hash_.update(glob.encode())
        return str(hash_.hexdigest())

    def get_as_str(self):
        """
        Get a human-readable string.
        :return: A string.
        """
        return F"  {self.name}/{self.version} [{self.arch}, {self.kind}, {self.os}, {self.compiler}]"

    def from_str(self, data: str):
        """
        Do the inverse of get_as_string.
        :param data: The string representing the dependency as in get_as_str.
        """
        idata = data.replace("[", "")
        idata = idata.replace("]", "")
        idata = idata.replace(",", "")
        idata = idata.replace("  ", "")
        idata = idata.replace("/", " ")
        items = idata.split()
        if len(items) != 6:
            print(f"WARNING: Bad Line format: '{data}': {items}", file = stderr)
            return
        self.name = items[0]
        self.version = items[1]
        self.arch = items[2]
        self.kind = items[3]
        self.os = items[4]
        self.compiler = items[5].split("-", 1)[0]

    def from_edp_file(self, file: Path):
        """
        Read edp file for data.
        :param file: The file to read.
        """
        self.query = False
        if not file.exists():
            return
        if not file.is_file():
            return
        with open(file, "r") as fp:
            lines = fp.readlines()
        for line in lines:
            items = [item.strip() for item in line.split("=", 1)]
            if len(items) != 2:
                continue
            key = items[0]
            val = items[1]
            if key not in ["name", "version", "os", "arch", "kind", "compiler"] or val in [None, ""]:
                continue
            if key == "name":
                self.name = val
            if key == "version":
                self.version = val
            if key == "os":
                self.os = val
            if key == "arch":
                self.arch = val
            if key == "kind":
                self.kind = val
            if key == "compiler":
                self.compiler = val

    def to_edp_file(self, file: Path):
        """
        Write data into edp file.
        :param file: Filename to write.
        """
        file.parent.mkdir(parents=True, exist_ok=True)
        with open(file, "w") as fp:
            fp.write(F"name = {self.name}\n")
            fp.write(F"version = {self.version}\n")
            fp.write(F"os = {self.os}\n")
            fp.write(F"arch = {self.arch}\n")
            fp.write(F"kind = {self.kind}\n")
            fp.write(F"compiler = {self.compiler}\n")


class Dependency:
    """
    Class describing an entry of the database.
    """
    properties = Props()
    base_path = None
    valid = False

    def __init__(self, data=None):
        self.properties = Props()
        self.valid = False
        self.base_path = None
        self.cmake_config_path = None
        if isinstance(data, Path):
            self.base_path = Path(data)
            if not self.base_path.exists() or not (self.base_path / "edp.info").exists():
                self.base_path = None
                return
            self.read_edp_file()
            search = list(self.base_path.rglob("*onfig.cmake"))
            if len(search) > 0:
                self.cmake_config_path = ";".join([str(s.parent) for s in search])
        elif type(data) in [str, dict]:
            self.properties = Props(data)
        self.valid = True

    def __lt__(self, other):
        return self.properties < other.properties

    def __le__(self, other):
        return self.properties <= other.properties

    def __gt__(self, other):
        return self.properties > other.properties

    def __ge__(self, other):
        return self.properties >= other.properties

    def write_edp_info(self):
        """
        Save dependency info into file.
        """
        if self.base_path is None:
            return
        file = self.base_path / "edp.info"
        file.unlink(missing_ok=True)
        self.properties.to_edp_file(file)

    def read_edp_file(self):
        """
        Read info from file in path.
        """
        if self.base_path is None:
            return
        file = self.base_path / "edp.info"
        self.properties.from_edp_file(file)

    def get_path(self):
        """
        Compute the relative path of the dependency.
        :return: Relative path.
        """
        if self.base_path is not None:
            return self.base_path
        return f"{self.properties.name}/{self.properties.hash()}"

    def get_cmake_config_dir(self):
        """
        Get the path to the cmake config.
        :return:
        """
        return self.cmake_config_path

    def match(self, other):
        """
        Matching test.
        :param other: The other dependency to compare.
        :return: True if regexp match.
        """
        if type(other) == Props:
            return self.properties.match(other)
        elif type(other) == Dependency:
            return self.properties.match(other.properties)
        elif type(other) in [str, dict]:
            q = Props(other)
            return self.properties.match(q)
        else:
            return False
