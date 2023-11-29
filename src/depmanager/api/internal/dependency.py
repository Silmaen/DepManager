"""
Dependency object.
"""
from datetime import datetime
from pathlib import Path
from sys import stderr

from .machine import Machine

kinds = ["shared", "static", "header", "any"]

default_kind = kinds[0]
mac = Machine(True)


def version_lt(vers_a: str, vers_b: str) -> bool:
    """
    Compare 2 string describing version number
    :param vers_a:
    :param vers_b:
    :return: True if vers_a is lower than vers_b
    """
    if vers_a == vers_b:
        return False
    vers_aa = vers_a.split(".")
    vers_bb = vers_b.split(".")
    for i in range(min(len(vers_aa), len(vers_bb))):
        if vers_aa[i] == vers_bb[i]:
            continue
        try:
            compare = int(vers_aa[i]) < int(vers_bb[i])
        except:
            compare = vers_aa[i] < vers_bb[i]
        return compare
    return len(vers_aa) < len(vers_bb)


class Props:
    """
    Class for the details about items.
    """
    name = "*"
    version = "*"
    os = mac.os
    arch = mac.arch
    kind = default_kind
    compiler = mac.default_compiler
    query = False
    build_date = datetime(2000, 1, 1)
    glibc = ""

    def __init__(self, data=None, query: bool = False):
        self.name = "*"
        self.version = "*"
        self.os = mac.os
        self.arch = mac.arch
        self.kind = default_kind
        self.compiler = mac.default_compiler
        self.query = query
        self.build_date = datetime(2000, 1, 1)
        self.glibc = ""
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
            and self.compiler == other.compiler \
            and self.glibc == other.glibc \
            and self.build_date == other.build_date

    def __lt__(self, other):
        if type(other) != Props:
            return False
        if self.name != other.name:
            return self.name < other.name
        if self.version != other.version:
            return version_lt(self.version, other.version)
        if self.os != other.os:
            return self.os < other.os
        if self.arch != other.arch:
            return self.arch < other.arch
        if self.kind != other.kind:
            return self.kind < other.kind
        if self.compiler != other.compiler:
            return self.compiler < other.compiler
        if self.glibc != other.glibc:
            return version_lt(self.glibc, other.glibc)
        if self.build_date != other.build_date:
            return self.build_date < other.build_date
        return False

    def __le__(self, other):
        return self == other or self < other

    def __gt__(self, other):
        return other < self

    def __ge__(self, other):
        return self == other or self > other

    def version_greater(self, other_version):
        """
        Compare Version number
        :param other_version:
        :return: True if self greater than other version
        """
        if type(other_version) == str:
            compare = other_version
        elif isinstance(other_version, Props):
            compare = other_version.version
        elif isinstance(other_version, Dependency):
            compare = other_version.properties.version
        else:
            compare = str(other_version)
        if self.version != compare:
            self_version_item = self.version.split(".")
            other_version_item = compare.split(".")
            for i in range(min(len(self_version_item), len(other_version_item))):
                if self_version_item[i] != other_version_item[i]:
                    try:
                        return int(self_version_item[i]) > int(other_version_item[i])
                    except:
                        return self_version_item[i] > other_version_item[i]
            return len(self_version_item) > len(other_version_item)
        return False

    def libc_compatible(self, system_libc_version: str = ""):
        """
        Check the compatibility of this props with the given system libc version.
        :param system_libc_version:
        :return: True if compatible
        """
        if system_libc_version in ["", None]:
            return True
        if self.os != "Linux":
            return True
        return version_lt(self.version, system_libc_version)

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
            self.glibc = "*"
            self.build_date = "*"
        else:
            self.os = mac.os
            self.arch = mac.arch
            self.kind = default_kind
            self.compiler = mac.default_compiler
            self.glibc = mac.glibc
            self.build_date = datetime(2000, 1, 1)
        if "os" in data:
            self.os = data["os"]
        if "arch" in data:
            self.arch = data["arch"]
        if "kind" in data:
            self.kind = data["kind"]
        if "compiler" in data:
            self.compiler = data["compiler"]
        if "glibc" in data:
            self.glibc = data["glibc"]
        if "build_date" in data:
            self.build_date = data["build_date"]

    def to_dict(self):
        """
        Get a dictionary of data.
        :return: Dictionary.
        """
        return {
            "name"      : self.name,
            "version"   : self.version,
            "os"        : self.os,
            "arch"      : self.arch,
            "kind"      : self.kind,
            "compiler"  : self.compiler,
            "glibc"     : self.glibc,
            "build_date": self.build_date
        }

    def match(self, other):
        """
        Check similarity between props.
        :param other: The other props to compare.
        :return: True if regexp match.
        """
        from fnmatch import translate
        from re import compile
        for attr in ["name", "version", "os", "arch", "kind", "compiler", "glibc", "build_date"]:
            str_other = f"{getattr(other, attr)}"
            str_self = f"{getattr(self, attr)}"
            if (attr not in ["name", "version"] and
                    (str_other in ["any", "*", ""] or str_self in ["any", "*", ""])):
                continue
            if not compile(translate(str_other)).match(str_self):
                return False
        return True

    def hash(self):
        """
        Get a hash for dependency infos.
        :return: The hash as string.
        """
        from hashlib import sha1
        hash_ = sha1()
        glob = self.name + self.version + self.os + self.arch + self.kind + self.compiler + self.glibc + str(
                self.build_date)
        hash_.update(glob.encode())
        return str(hash_.hexdigest())

    def get_as_str(self):
        """
        Get a human-readable string.
        :return: A string.
        """

        output = F"{self.name}/{self.version} ({self.build_date.isoformat()}) [{self.arch}, {self.kind}, {self.os}, {self.compiler}"
        if self.glibc not in ["", None]:
            output += F", {self.glibc}"
        output += "]"
        return output

    def from_str(self, data: str):
        """
        Do the inverse of get_as_string.
        :param data: The string representing the dependency as in get_as_str.
        """
        try:
            predicate, idata = data.strip().split(" ", 1)
            predicate.strip()
            idata.strip()
            name, version = predicate.split("/", 1)
            date = ""
            if ")" in idata:
                date, idata = idata.split(")")
                date = date.replace("(", "").strip()
                idata.strip()
            items = idata.replace("[", "").replace("]", "").replace(",", "").split()
            if len(items) not in [4, 5]:
                print(f"WARNING: Bad Line format: '{data}': '{name}' '{version}' '{date}' {items}", file=stderr)
                return
        except Exception as err:
            print(f"ERROR: bad line format '{data}' ({err})", file=stderr)
            return
        self.name = name
        self.version = version
        if date not in [None, ""]:
            self.build_date = datetime.fromisoformat(date)
        self.arch = items[0]
        self.kind = items[1]
        self.os = items[2]
        self.compiler = items[3].split("-", 1)[0]
        if len(items) == 5:
            self.glibc = items[4]
        else:
            self.glibc = ""

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
        with open(file) as fp:
            lines = fp.readlines()
        for line in lines:
            items = [item.strip() for item in line.split("=", 1)]
            if len(items) != 2:
                continue
            key = items[0]
            val = items[1]
            if (key not in ["name", "version", "os", "arch", "kind", "compiler", "glibc", "build_date"] or
                    val in [None, ""]):
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
            if key == "glibc":
                self.glibc = val
            if key == "build_date":
                self.build_date = datetime.fromisoformat(val)

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
            fp.write(F"glibc = {self.glibc}\n")
            fp.write(F"build_date = {self.build_date.isoformat()}\n")


class Dependency:
    """
    Class describing an entry of the database.
    """
    properties = Props()
    base_path = None
    valid = False

    def __init__(self, data=None, source=None):
        self.properties = Props()
        self.valid = False
        self.base_path = None
        self.cmake_config_path = None
        self.source = source
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

    def get_source(self):
        """
        Returns where this dependency has been found (local or remote name)
        :return: Name of the source
        """
        if self.source is None:
            return "local"
        return self.source

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

    def libc_compatible(self, system_libc_version: str = ""):
        """
        Check the compatibility of this props with the given system libc version.
        :param system_libc_version:
        :return: True if compatible
        """
        return self.properties.libc_compatible(system_libc_version)
