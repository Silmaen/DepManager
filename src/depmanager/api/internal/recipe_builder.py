"""
Tools for building single recipe.
"""
from datetime import datetime
from os import access, R_OK, W_OK
from pathlib import Path
from sys import stderr

from depmanager.api.internal.machine import Machine
from depmanager.api.internal.system import LocalSystem, Props
from depmanager.api.local import LocalManager
from depmanager.api.recipe import Recipe


def try_run(cmd):
    """
    Safe run of commands.
    :param cmd: Command to run.
    """
    from subprocess import run

    try:
        ret = run(cmd, shell=True, bufsize=0)
        if ret.returncode != 0:
            print(f"ERROR '{cmd}' \n bad exit code ({ret.returncode})", file=stderr)
            return False
    except Exception as err:
        print(f"ERROR '{cmd}' \n exception during run {err}", file=stderr)
        return False
    return True


class RecipeBuilder:
    """
    Class handling the build of a single recipe
    """

    def __init__(
        self,
        recipe,
        temp: Path,
        local=None,
        cross_info=None,
    ):
        # manage cross Info
        self.generator = None
        if cross_info is None:
            cross_info = {}
        self.cross_info = cross_info
        # manage the recipe
        self.recipe = None
        if isinstance(recipe, Recipe):
            self.recipe = recipe
        #
        if type(local) is LocalSystem:
            self.local = local
        elif type(local) is LocalManager:
            self.local = local.get_sys()
        else:
            self.local = LocalSystem()
        self.temp = temp

        self.creation_date = None
        self.os = None
        self.arch = None
        self.os = None
        self.compiler = None

    def has_recipes(self):
        """
        Check if the builder has a recipe objet.
        """
        return self.recipe is not None and isinstance(self.recipe, Recipe)

    def _get_source_dir(self):
        from pathlib import Path

        if self.recipe.path is None:
            print(
                "warning: it may be better to setup recipe path for automated builder."
            )
            source_dir = Path(self.recipe.source_dir).resolve()
        else:
            source_dir = (
                Path(self.recipe.path) / Path(self.recipe.source_dir)
            ).resolve()
        if not source_dir.exists():
            print(
                f"Cannot build {self.recipe.to_str()}: could not find source dir {source_dir}",
                file=stderr,
            )
            return None
        if not (source_dir / "CMakeLists.txt").exists():
            print(
                f"Cannot build {self.recipe.to_str()}: could not find CMakeLists.txt in dir {source_dir}",
                file=stderr,
            )
            return None
        if not access(source_dir, R_OK | W_OK):
            if self.local.verbosity > 0:
                print(
                    f"Cannot build {self.recipe.to_str()}: source directory {source_dir} not enough permissions",
                    file=stderr,
                )
            return None
        return source_dir

    def _get_generator(self):
        if self.generator not in ["", None]:
            return f" -G {self.generator}"
        if len(self.recipe.config) > 1:
            return " -G Ninja Multi-Config"
        if len(self.recipe.config) == 1:
            return " -G Ninja"
        return ""

    def _get_configs(self):
        if len(self.recipe.config) > 1:
            return f" -DCMAKE_CONFIGURATION_TYPES={';'.join(self.recipe.config)}"
        if len(self.recipe.config) == 1:
            return f" -DCMAKE_BUILD_TYPE={self.recipe.config[0]}"
        return ""

    def _get_options_str(self):
        out = f" -DCMAKE_INSTALL_PREFIX={self.temp / 'install'}"
        out += f" -DBUILD_SHARED_LIBS={['OFF', 'ON'][self.recipe.kind.lower() == 'shared']}"
        if "C_COMPILER" in self.cross_info:
            out += f" -DCMAKE_C_COMPILER={self.cross_info['C_COMPILER']}"
        if "CXX_COMPILER" in self.cross_info:
            out += f" -DCMAKE_CXX_COMPILER={self.cross_info['CXX_COMPILER']}"
        if self.recipe.settings["os"].lower() in ["linux"]:
            out += " -DCMAKE_SKIP_INSTALL_RPATH=ON -DCMAKE_POSITION_INDEPENDENT_CODE=ON"
        for key, val in self.recipe.cache_variables.items():
            out += f" -D{key}={val}"
        return out

    def _make_define(self):
        mac = Machine(True)
        self.creation_date = datetime.now(
            tz=datetime.now().astimezone().tzinfo
        ).replace(microsecond=0)
        self.glibc = ""
        if self.recipe.kind == "header":
            self.arch = "any"
            self.os = "any"
            self.compiler = "any"
        else:
            if "CROSS_ARCH" in self.cross_info:
                self.arch = self.cross_info["CROSS_ARCH"]
            else:
                self.arch = mac.arch
            if "CROSS_OS" in self.cross_info:
                self.os = self.cross_info["CROSS_OS"]
            else:
                self.os = mac.os
            self.compiler = mac.default_compiler
            self.glibc = mac.glibc
        self.recipe.define(
            self.os,
            self.arch,
            self.compiler,
            self.temp / "install",
            self.glibc,
            self.creation_date,
        )

    def _check_dependencies(self):
        if self.local.verbosity > 2:
            print(f"package {self.recipe.to_str()}: Checking dependencies...")
        if type(self.recipe.dependencies) is not list:
            print(
                f"ERROR: package {self.recipe.to_str()}: dependencies must be a list.",
                file=stderr,
            )
            self.recipe.clean()
            return False
        ok = True
        dep_list = []
        for dep in self.recipe.dependencies:
            if type(dep) is not dict:
                ok = False
                print(
                    f"ERROR: package {self.recipe.to_str()}: dependencies must be a list of dict.",
                    file=stderr,
                )
                break
            if "name" not in dep:
                print(
                    f"ERROR: package {self.recipe.to_str()}: dependencies {dep} must be a contain a name.",
                    file=stderr,
                )
                ok = False
                break
            if "os" not in dep:
                dep["os"] = self.os
            if "arch" not in dep:
                dep["arch"] = self.arch
            result = self.local.local_database.query(dep)
            if len(result) == 0:
                print(
                    f"ERROR: package {self.recipe.to_str()}: dependency {dep['name']} Not found:\n{dep}",
                    file=stderr,
                )
                ok = False
                break
            dep_list.append(str(result[0].get_cmake_config_dir()).replace("\\", "/"))
        return ok, dep_list

    def build(self, forced: bool = False):
        """
        Do the build of recipes.
        """
        # check output folder
        if not self.temp.exists():
            if self.local.verbosity > 0:
                print(
                    f"Cannot build {self.recipe.to_str()}: temp directory {self.temp} does not exists",
                    file=stderr,
                )
            return False
        # check read write permissions
        if not access(self.temp, R_OK | W_OK):
            if self.local.verbosity > 0:
                print(
                    f"Cannot build {self.recipe.to_str()}: temp directory {self.temp} does not have enough permissions",
                    file=stderr,
                )
            return False

        self._make_define()

        #
        # Check for existing
        if self.local.verbosity > 2:
            print(f"package {self.recipe.to_str()}: Checking existing...")
        p = Props(
            {
                "name": self.recipe.name,
                "version": self.recipe.version,
                "os": self.os,
                "arch": self.arch,
                "kind": self.recipe.kind,
                "compiler": self.compiler,
                "glibc": self.glibc,
            }
        )
        search = self.local.local_database.query(p)
        if len(search) > 0:
            if forced:
                print(f"package {self.recipe.to_str()}: already exists, overriding it.")
            else:
                print(f"package {self.recipe.to_str()}: already exists, skipping it.")
                return True
        p.build_date = self.creation_date

        #
        #
        # getting the sources
        source_dir = self._get_source_dir()
        if source_dir is None:
            return False
        self.recipe.source()

        #
        #
        # check dependencies+
        ok, dep_list = self._check_dependencies()
        if not ok:
            self.recipe.clean()
            return False

        #
        #
        # configure
        if self.local.verbosity > 2:
            print(f"package {self.recipe.to_str()}: Configure...")
        if self.recipe.kind not in ["shared", "static"]:
            self.recipe.config = ["Release"]
        self.recipe.configure()
        cmd = f'cmake -S {self._get_source_dir()} -B {self.temp / "build"}'
        cmd += self._get_generator()
        cmd += self._get_configs()
        if len(dep_list) != 0:
            cmd += f' -DCMAKE_PREFIX_PATH="{";".join(dep_list)}"'
        cmd += self._get_options_str()
        if not try_run(cmd):
            if self.local.verbosity > 0:
                print(
                    f"ERROR: package {self.recipe.to_str()}: Configuration fail.",
                    file=stderr,
                )
            self.recipe.clean()
            return False
        #
        #
        # build & install
        if self.local.verbosity > 2:
            print(f"package {self.recipe.to_str()}: Build and install...")
        has_fail = False
        for conf in self.recipe.config:
            if self.local.verbosity > 2:
                print(f"package {self.recipe.to_str()}: Build config {conf}...")
            cmd = f"cmake --build {self.temp / 'build'} --target install"
            if len(self.recipe.config):
                cmd += f" --config {conf}"
            if self.cross_info["SINGLE_THREAD"]:
                cmd += f" -j 1"
            if not try_run(cmd):
                print(
                    f"ERROR: package {self.recipe.to_str()}, ({conf}): install Fail.",
                    file=stderr,
                )
                has_fail = True
                break
        if has_fail:
            self.recipe.clean()
            return False
        #
        #
        # create the info file
        if self.local.verbosity > 2:
            print(f"package {self.recipe.to_str()}: Create package...")
        self.recipe.install()
        p.to_edp_file(self.temp / "install" / "edp.info")
        # copy to repository
        self.local.import_folder(self.temp / "install")
        # clean Temp
        self.recipe.clean()
        return True
