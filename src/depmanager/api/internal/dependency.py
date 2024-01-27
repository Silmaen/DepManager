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
base_date = datetime.fromisoformat("2000-01-01T00:00:00+00:00")


def safe_to_int(vers: str):
    """
    Safely convert a string to int taking only the fist digit characters.
    :param vers: The string to convert
    :return: Corresponding int.
    """
    from re import match

    crr = match(r"^\D*(\d+)", vers)
    if crr:
        return int(crr.group(1))
    else:
        return 0


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
        return safe_to_int(vers_aa[i]) < safe_to_int(vers_bb[i])
    return len(vers_aa) < len(vers_bb)


def read_date(the_date: str):
    """
    :param the_date:
    :return:
    """
    try:
        if "T" not in the_date:  # not dte/hour separator: assume not a date
            return datetime.fromisoformat("2000-01-01T00:00:00+00:00")
        date, time = the_date.split("T", 1)
        if "-" not in date:
            if len(date) == 8:
                date = date[0:4] + "-" + date[4:6] + "-" + date[6:]
            elif len(date) == 6:
                date = "20" + date[0:2] + "-" + date[2:4] + "-" + date[4:]
            else:  # assume not a real date
                return datetime.fromisoformat("2000-01-01T00:00:00+00:00")
        else:
            if len(date) == 8:
                date = "20" + date
            if len(date) != 10:  # not real date
                return datetime.fromisoformat("2000-01-01T00:00:00+00:00")
        tz_str = "00:00"
        if "+" in time:
            time, tz_str = time.split("+", 1)
        if "." in time:
            time, _ = time.split(".", 1)
        elif time.endswith("Z"):
            time = time.replace("Z", "")
        if ":" not in time:
            if len(time) == 4:
                time = time[0:2] + ":" + time[2:] + ":00"
            elif len(time) == 6:
                time = time[0:2] + ":" + time[2:4] + ":" + time[4:]
        else:
            if len(time) == 5:
                time += ":00"
            if len(time) != 8:
                time = "00:00:00"
        if ":" not in tz_str:
            if len(tz_str) != 4:
                tz_str = "00:00"
            else:
                tz_str = tz_str[0:2] + ":" + tz_str[2:]
        return datetime.fromisoformat(date + "T" + time + "+" + tz_str)
    except Exception as err:
        print(f"*** Exception during date '{the_date}' decoding: {err}", file=stderr)
        return datetime.fromisoformat("2000-01-01T00:00:00+00:00")


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
    build_date = base_date
    glibc = ""

    def __init__(self, data=None, query: bool = False):
        self.name = "*"
        self.version = "*"
        self.os = mac.os
        self.arch = mac.arch
        self.kind = default_kind
        self.compiler = mac.default_compiler
        self.query = query
        self.build_date = base_date
        self.glibc = ""
        if type(data) is str:
            self.from_str(data)
        elif type(data) is dict:
            self.from_dict(data)

    def __eq__(self, other):
        return (
            self.name == other.name
            and self.version == other.version
            and self.build_date == other.build_date
            and self.os == other.os
            and self.glibc == other.glibc
            and self.arch == other.arch
            and self.kind == other.kind
            and self.compiler == other.compiler
        )

    def __lt__(self, other):
        if self.name != other.name:
            return self.name < other.name
        if self.version != other.version:
            return version_lt(self.version, other.version)
        if self.build_date != other.build_date:
            return self.build_date < other.build_date
        if self.os != other.os:
            return self.os < other.os
        if self.glibc != other.glibc:
            return version_lt(self.glibc, other.glibc)
        if self.arch != other.arch:
            return self.arch < other.arch
        if self.kind != other.kind:
            return self.kind < other.kind
        if self.compiler != other.compiler:
            return self.compiler < other.compiler

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
            self.glibc = "*"
            self.build_date = "*"
        else:
            self.os = mac.os
            self.arch = mac.arch
            self.kind = default_kind
            self.compiler = mac.default_compiler
            self.glibc = mac.glibc
            self.build_date = base_date
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
            "name": self.name,
            "version": self.version,
            "os": self.os,
            "arch": self.arch,
            "kind": self.kind,
            "compiler": self.compiler,
            "glibc": self.glibc,
            "build_date": self.build_date,
        }

    def match(self, other):
        """
        Check similarity between props.
        :param other: The other props to compare.
        :return: True if regexp match.
        """
        from fnmatch import translate
        from re import compile

        for attr in [
            "name",
            "version",
            "os",
            "arch",
            "kind",
            "compiler",
            "glibc",
        ]:
            str_other = f"{getattr(other, attr)}"
            str_self = f"{getattr(self, attr)}"
            if attr == "glibc":
                if str_other in ["any", "*", ""]:
                    continue
                if str_other.startswith("="):
                    str_other = str_other.replace("=", "")
                    if str_other != str_self:
                        return False
                    continue
                else:
                    if version_lt(str_other, str_self):
                        return False
                    continue

            if attr not in ["name", "version", "glibc"] and (
                str_other in ["any", "*", ""] or str_self in ["any", "*", ""]
            ):
                continue
            if not compile(translate(str_other)).match(str_self):
                return False
        return True

    def hash(self):
        """
        Get a hash for dependency info.
        :return: The hash as string.
        """
        from hashlib import sha1

        hash_ = sha1()
        glob = (
            self.name
            + self.version
            + self.os
            + self.arch
            + self.kind
            + self.compiler
            + self.glibc
        )
        hash_.update(glob.encode())
        return str(hash_.hexdigest())

    def get_as_str(self):
        """
        Get a human-readable string.
        :return: A string.
        """
        base_info = f"{self.arch}, {self.kind}, {self.os}, {self.compiler}"
        if type(self.build_date) is datetime:
            date = self.build_date.isoformat()
        else:
            date = f"{self.build_date}"
        output = f"{self.name}/{self.version} ({date}) [{base_info}"
        if self.glibc not in ["", None]:
            output += f", {self.glibc}"
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
                print(
                    f"WARNING: Bad Line format: '{data}': '{name}' '{version}' '{date}' {items}",
                    file=stderr,
                )
                return
        except Exception as err:
            print(f"ERROR: bad line format '{data}' ({err})", file=stderr)
            return
        self.name = name
        self.version = version
        if date not in [None, ""]:
            self.build_date = read_date(date)
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
            if key not in [
                "name",
                "version",
                "os",
                "arch",
                "kind",
                "compiler",
                "glibc",
                "build_date",
            ] or val in [None, ""]:
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
                self.build_date = read_date(val)

    def to_edp_file(self, file: Path):
        """
        Write data into edp file.
        :param file: Filename to write.
        """
        file.parent.mkdir(parents=True, exist_ok=True)
        with open(file, "w") as fp:
            fp.write(f"name = {self.name}\n")
            fp.write(f"version = {self.version}\n")
            fp.write(f"os = {self.os}\n")
            fp.write(f"arch = {self.arch}\n")
            fp.write(f"kind = {self.kind}\n")
            fp.write(f"compiler = {self.compiler}\n")
            fp.write(f"glibc = {self.glibc}\n")
            fp.write(f"build_date = {self.build_date.isoformat()}\n")


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
            if (
                not self.base_path.exists()
                or not (self.base_path / "edp.info").exists()
            ):
                self.base_path = None
                return
            self.read_edp_file()
            search = list(
                set([folder.parent for folder in self.base_path.rglob("*onfig.cmake")])
            )
            self.cmake_config_path = ";".join([str(s) for s in search])
        elif type(data) in [str, dict]:
            self.properties = Props(data)
        self.valid = True

    def __eq__(self, other):
        return self.properties == other.properties

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
        Returns where this dependency has been found (local or remote name).
        :return: Name of the source.
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
        if type(other) is Props:
            return self.properties.match(other)
        elif type(other) is Dependency:
            return self.properties.match(other.properties)
        elif type(other) in [str, dict]:
            q = Props(other)
            return self.properties.match(q)
        else:
            return False

    def is_platform_dependent(self):
        """
        Check platform dependency.
        :return: True if dependent on a platform
        """
        if self.properties.kind in ["header", "any"]:
            return False
        return True

    def has_build_date(self):
        """
        Check if build_date defined.
        :return: True if build_date defined.
        """
        return self.properties.build_date != base_date

    def has_glibc(self):
        """
        Check glibc defined.
        :return: True if defined or irrelevant.
        """
        return self.properties.os != "Linux" or self.properties.glibc not in ["", None]

    def libc_compatible(self, system_libc_version: str = ""):
        """
        Check the compatibility of this props with the given system libc version.
        :param system_libc_version: Reference version to check.
        :return: True if compatible.
        """
        if system_libc_version in ["", None]:
            return True
        return not self.has_glibc() or version_lt(
            self.properties.version, system_libc_version
        )

    def is_newer(self, reference: datetime):
        """
        Check if this dependency newer that reference date.
        :param reference: The reference date.
        :return: True if newer.
        """
        if not self.has_build_date():  # cannot be newer if no build date
            return False
        return self.properties.build_date > reference

    def check_newest(self, other):
        """
        Check this Dependency newer than a reference.
        :param other: The reference to check.
        :return: True if newer.
        """
        if type(other) is Props:
            prop = other
        elif type(other) is Dependency:
            prop = other.properties
        elif type(other) in [str, dict]:
            prop = Props(other)
        else:
            print("ERROR: Bad reference for check newer.", file=stderr)
            return False
        # must have same name, os kind, etc.
        if prop.name != self.properties.name:
            return False
        if prop.kind == "header":
            if self.properties.kind != "header":
                return False
        else:
            if (
                prop.os != self.properties.os
                or prop.arch != self.properties.arch
                or prop.kind != self.properties.kind
            ):
                return False
            if prop.os == "Linux" and prop.glibc not in ["", None]:
                if not self.has_glibc() or not self.libc_compatible(prop.glibc):
                    return False
        # version check.
        if prop.version == self.properties.version:
            # check the build date!
            if self.has_build_date():
                if prop.build_date != base_date:
                    return self.is_newer(prop.build_date)
            else:
                return False
        elif version_lt(self.properties.version, prop.version):
            return False
        return True

    def get_generic_query(self):
        """
        Construct generic query for searching dependencies similar to this one.
        :return: Generic query.
        """
        query = {
            "name": self.properties.name,
            "kind": self.properties.kind,
        }
        if self.is_platform_dependent():
            query["os"] = self.properties.os
            query["arch"] = self.properties.arch
            query["compiler"] = self.properties.compiler
            if self.has_glibc():
                query["glibc"] = self.properties.glibc
        return query

    def version_greater(self, other_version):
        """
        Compare Version number
        :param other_version:
        :return: True if self greater than other version
        """
        if type(other_version) is str:
            compare = other_version
        elif type(other_version) is Props:
            compare = other_version.version
        elif type(other_version) is Dependency:
            compare = other_version.properties.version
        else:
            compare = str(other_version)
        if compare == "":
            return True
        if self.properties.version != compare:
            return version_lt(compare, self.properties.version)
        return False

    def has_minimal_version(self, version: str):
        """
        Check version at least the reference.
        :param version: Reference version.
        :return: True if newer or equal
        """
        if not type(version) is not str:
            return False
        if version in ["", None]:
            return False
        return not version_lt(self.properties.version, version)
