"""
Dependency object.
"""

import datetime
from pathlib import Path

from api.internal.messaging import log

from .machine import Machine

kinds = ["shared", "static", "header", "any"]

default_kind = kinds[0]
mac = Machine(True)
base_date = datetime.datetime.fromisoformat("2000-01-01T00:00:00+00:00")


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
        normalized_date = the_date.strip().replace(" ", "T")
        if "T" not in normalized_date:  # not dte/hour separator: assume not a date
            return datetime.datetime.fromisoformat("2000-01-01T00:00:00+00:00")
        date, time = normalized_date.split("T", 1)
        if "-" not in date:
            if len(date) == 8:
                date = date[0:4] + "-" + date[4:6] + "-" + date[6:]
            elif len(date) == 6:
                date = "20" + date[0:2] + "-" + date[2:4] + "-" + date[4:]
            else:  # assume not a real date
                return datetime.datetime.fromisoformat("2000-01-01T00:00:00+00:00")
        else:
            if len(date) == 8:
                date = "20" + date
            if len(date) != 10:  # not real date
                return datetime.datetime.fromisoformat("2000-01-01T00:00:00+00:00")
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
        return datetime.datetime.fromisoformat(date + "T" + time + "+" + tz_str)
    except Exception as err:
        log.fatal(f"*** Exception during date '{the_date}' decoding: {err}")
        return datetime.datetime.fromisoformat("2000-01-01T00:00:00+00:00")


class Props:
    """
    Class for the details about items.
    """

    def __init__(self, data=None, query: bool = False):
        self.name = "*"
        self.version = "*"
        self.query = query
        self.dependencies = []
        if self.query:
            self.os = "*"
            self.arch = "*"
            self.kind = "*"
            self.abi = "*"
            self.glibc = "*"
            self.build_date = "*"
        else:
            self.os = mac.os
            self.arch = mac.arch
            self.kind = default_kind
            self.abi = mac.default_abi
            self.glibc = mac.glibc
            self.build_date = base_date

        if type(data) is str:
            self.from_str(data)
        elif type(data) is dict:
            self.from_dict(data)
        elif type(data) is Path:
            self.from_yaml_file(data)

    def __eq__(self, other):
        return (
            self.name == other.name
            and self.version == other.version
            and self.build_date == other.build_date
            and self.os == other.os
            and self.glibc == other.glibc
            and self.arch == other.arch
            and self.kind == other.kind
            and self.abi == other.abi
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
        if self.abi != other.abi:
            return self.abi < other.abi

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
            self.abi = "*"
            self.glibc = "*"
            self.build_date = "*"
        else:
            self.os = mac.os
            self.arch = mac.arch
            self.kind = default_kind
            self.abi = mac.default_abi
            self.glibc = mac.glibc
            self.build_date = base_date
        if "os" in data:
            self.os = data["os"]
        if "arch" in data:
            self.arch = data["arch"]
        if "kind" in data:
            self.kind = data["kind"]
        if "abi" in data:
            self.abi = data["abi"]
        if "glibc" in data:
            self.glibc = data["glibc"]
        if "build_date" in data and isinstance(data["build_date"], str):
            self.build_date = read_date(data["build_date"])
        elif "build_date" in data and isinstance(data["build_date"], datetime.datetime):
            self.build_date = data["build_date"]
        else:
            self.build_date = base_date
        if "dependencies" in data:
            self.dependencies = data["dependencies"]
        # read deprecated component
        if "compiler" in data:
            self.abi = data["compiler"]

    def to_dict(self):
        """
        Get a dictionary of data.
        :return: Dictionary.
        """
        dict_out = {
            "name": self.name,
            "version": self.version,
            "os": self.os,
            "arch": self.arch,
            "kind": self.kind,
            "abi": self.abi,
            "build_date": self.build_date,
            "dependencies": self.dependencies,
        }
        if self.has_glibc():
            dict_out["glibc"] = self.glibc
        return dict_out

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
            "abi",
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
            + self.abi
            + self.glibc
        )
        hash_.update(glob.encode())
        return str(hash_.hexdigest())

    def get_as_str(self):
        """
        Get a human-readable string.
        :return: A string.
        """
        base_info = f"{self.arch}, {self.kind}, {self.os}, {self.abi}"
        if type(self.build_date) is datetime.datetime:
            date = self.build_date.isoformat()
        else:
            date = f"{self.build_date}"
        output = f"{self.name}/{self.version} ({date}) [{base_info}"
        if self.kind != "header" and self.glibc not in ["", None]:
            output += f", {self.glibc}"
        output += "]"
        return output

    def has_glibc(self):
        """
        Check glibc defined.
        :return: True if defined or irrelevant.
        """
        return (
            self.os == "Linux"
            and self.glibc not in ["", None]
            and self.kind != "header"
        )

    def from_str(self, data: str):
        """
        Do the inverse of get_as_string.
        :param data: The string representing the dependency as in get_as_str.
        """

        try:
            dep_data = None
            if "|" in data:
                data, dep_data = data.split("|", 1)
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
                log.warn(
                    f"Bad Line format: '{data}': '{name}' '{version}' '{date}' {items}"
                )
                return
            if dep_data is not None:
                try:
                    dep_data = dep_data.replace("deps:", "").strip()
                    if len(dep_data) == 0:
                        self.dependencies = []
                    else:
                        self.dependencies = eval(dep_data)
                except Exception as err:
                    log.warn(f"Invalid dependencies format: {err} in {dep_data}")
                    self.dependencies = []
        except Exception as err:
            log.fatal(f"bad line format '{data}' ({err})")
            return
        self.name = name
        self.version = version
        if date not in [None, ""]:
            self.build_date = read_date(date)
        self.arch = items[0]
        self.kind = items[1]
        self.os = items[2]
        self.abi = items[3].split("-", 1)[0]
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
                "abi",
                "glibc",
                "build_date",
                # deprecated:
                "compiler",
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
            if key == "abi":
                self.abi = val
            if key == "glibc":
                self.glibc = val
            if key == "build_date":
                self.build_date = read_date(val)
            # deprecated keys
            if key == "compiler":
                self.abi = val

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
            fp.write(f"abi = {self.abi}\n")
            if self.has_glibc():
                fp.write(f"glibc = {self.glibc}\n")
            fp.write(f"build_date = {self.build_date.isoformat()}\n")

    def from_yaml_file(self, file: Path):
        """
        Read data from a YAML file.
        :param file: The file to read.
        """
        import yaml

        if not file.exists():
            return
        if not file.is_file():
            return
        with open(file) as fp:
            data = yaml.safe_load(fp)
        self.from_dict(data)

    def to_yaml_file(self, file: Path):
        """
        Write data into a YAML file.
        :param file: Filename to write.
        """
        import yaml

        file.parent.mkdir(parents=True, exist_ok=True)
        with open(file, "w") as fp:
            yaml.dump(self.to_dict(), fp)


class Dependency:
    """
    Class describing an entry of the database.
    """

    def __init__(self, data=None, source=None):
        self.properties = Props()
        self.valid = False
        self.base_path = None
        self.cmake_config_path = None
        self.source = source
        self.description = ""
        if isinstance(data, Path):
            self.base_path = Path(data)
            if not self.base_path.exists() or (
                not (self.base_path / "edp.info").exists()
                and not (self.base_path / "info.yaml").exists()
            ):
                log.warn(
                    f"Dependency at {self.base_path} does not contains edp.info or info.yaml file."
                )
                self.base_path = None
                return
            if not (self.base_path / "info.yaml").exists():
                log.warn(
                    f"Dependency at {self.base_path}: Old format detected, upgrading..."
                )
                self.read_file_info()
                self.write_file_info()
            if not (self.base_path / "info.yaml").exists():
                log.error(
                    f"Dependency at {self.base_path}: Cannot read info.yaml file after upgrade."
                )
                self.base_path = None
                return
            self.read_file_info()
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

    def write_file_info(self):
        """
        Save dependency info into file.
        """
        if self.base_path is None:
            return
        file = self.base_path / "edp.info"
        file.unlink(missing_ok=True)
        file = self.base_path / "info.yaml"
        self.properties.to_yaml_file(file)
        if self.description not in [None, ""]:
            desc_file = self.base_path / "description.md"
            with open(desc_file, "w") as fp:
                fp.write(self.description)

    def read_file_info(self):
        """
        Read info from file in path.
        """
        if self.base_path is None:
            return
        file = self.base_path / "info.yaml"
        if file.exists():
            self.properties.from_yaml_file(file)
        else:
            log.warn(
                f"Dependency at {self.base_path}: Old format detected reading old edp.info file..."
            )
            file = self.base_path / "edp.info"
            self.properties.from_edp_file(file)
        desc_file = self.base_path / "description.md"
        if desc_file.exists():
            with open(desc_file) as fp:
                self.description = fp.read()

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
        return self.properties.has_glibc()

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
            log.error("ERROR: Bad reference for check newer.")
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
            query["abi"] = self.properties.abi
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

    def has_dependency(self):
        """
        Check if this dependency has dependencies.
        :return: True if has dependencies.
        """
        return len(self.properties.dependencies) > 0

    def get_dependency_list(self):
        """
        Get the list of dependencies as strings.
        :return: List of dependencies.
        """
        return self.properties.dependencies

    def get_detailed_info(self):
        """
        Get detailed information about this dependency.
        :return: Dictionary with detailed info.
        """
        if self.description in ["", None]:
            return "No description available."
        return self.description
