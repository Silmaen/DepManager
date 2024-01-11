"""
Tools for building packages.
"""
from datetime import datetime
from pathlib import Path
from shutil import rmtree
from sys import stderr

from depmanager.api.internal.system import LocalSystem, Props
from depmanager.api.local import LocalManager

from .internal.machine import Machine


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


class Builder:
    """
    Manager for building packages.
    """

    def __init__(
        self,
        source: Path,
        temp: Path = None,
        local: LocalSystem = None,
        cross_info=None,
    ):
        if cross_info is None:
            cross_info = {}
        from importlib.util import spec_from_file_location, module_from_spec
        from inspect import getmembers, isclass
        from depmanager.api.recipe import Recipe

        self.cross_info = cross_info
        self.generator = ""
        if type(local) is LocalSystem:
            self.local = local
        elif type(local) is LocalManager:
            self.local = local.get_sys()
        else:
            self.local = LocalSystem()
        self.source_path = source
        if temp is None:
            self.temp = self.local.temp_path / "builder"
        else:
            self.temp = temp
        rmtree(self.temp, ignore_errors=True)
        self.temp.mkdir(parents=True, exist_ok=True)
        self.recipes = []
        for file in self.source_path.iterdir():
            if not file.is_file():
                continue
            if file.suffix != ".py":
                continue
            spec = spec_from_file_location(file.name, file)
            mod = module_from_spec(spec)
            spec.loader.exec_module(mod)
            for name, obj in getmembers(mod):
                if isclass(obj) and name != "Recipe" and issubclass(obj, Recipe):
                    self.recipes.append(obj())

    def has_recipes(self):
        """
        Check recipes in the list.
        :return: True if contain recipe.
        """
        return len(self.recipes) > 0

    def _get_source_dir(self, rec):
        from pathlib import Path

        source_dir = Path(rec.source_dir)
        if not source_dir.is_absolute():
            source_dir = self.source_path / source_dir
        if not source_dir.exists():
            print(f"ERROR: could not find source dir {source_dir}", file=stderr)
            exit(-666)
        if not (source_dir / "CMakeLists.txt").exists():
            print(
                f"ERROR: could not find CMakeLists.txt in dir {source_dir}", file=stderr
            )
            exit(-666)
        return source_dir

    def _get_generator(self, rec):
        if self.generator not in ["", None]:
            return self.generator
        if len(rec.config) > 1:
            return "Ninja Multi-Config"
        return "Ninja"

    def _get_options_str(self, rec):
        out = f"-DCMAKE_INSTALL_PREFIX={self.temp / 'install'}"
        out += f" -DBUILD_SHARED_LIBS={['OFF', 'ON'][rec.kind.lower() == 'shared']}"
        if "C_COMPILER" in self.cross_info:
            out += f" -DCMAKE_C_COMPILER={self.cross_info['C_COMPILER']}"
        if "CXX_COMPILER" in self.cross_info:
            out += f" -DCMAKE_CXX_COMPILER={self.cross_info['CXX_COMPILER']}"
        if rec.settings["os"].lower() in ["linux"]:
            out += " -DCMAKE_SKIP_INSTALL_RPATH=ON -DCMAKE_POSITION_INDEPENDENT_CODE=ON"
        for key, val in rec.cache_variables.items():
            out += f" -D{key}={val}"
        return out

    def build_all(self, forced: bool = False):
        """
        Do the build of recipes.
        """
        mac = Machine(True)
        creation_date = datetime.now(tz=datetime.now().astimezone().tzinfo).replace(
            microsecond=0
        )
        error = 0
        for rec in self.recipes:
            #
            #
            glibc = ""
            if rec.kind == "header":
                arch = "any"
                os = "any"
                compiler = "any"
            else:
                if "CROSS_ARCH" in self.cross_info:
                    arch = self.cross_info["CROSS_ARCH"]
                else:
                    arch = mac.arch
                if "CROSS_OS" in self.cross_info:
                    os = self.cross_info["CROSS_OS"]
                else:
                    os = mac.os
                compiler = mac.default_compiler
                glibc = mac.glibc

            rec.define(os, arch, compiler, self.temp / "install", glibc, creation_date)

            #
            #
            # Check for existing
            if self.local.verbosity > 2:
                print(f"package {rec.to_str()}: Checking existing...")
            p = Props(
                {
                    "name": rec.name,
                    "version": rec.version,
                    "os": os,
                    "arch": arch,
                    "kind": rec.kind,
                    "compiler": compiler,
                    "glibc": glibc,
                }
            )
            search = self.local.local_database.query(p)
            if len(search) > 0:
                if forced:
                    print(
                        f"REMARK: library {p.get_as_str()} already exists, overriding it."
                    )
                else:
                    print(
                        f"REMARK: library {p.get_as_str()} already exists, skipping it."
                    )
                    continue
            p.build_date = creation_date
            rec.source()

            #
            #
            # check dependencies+
            if self.local.verbosity > 2:
                print(f"package {rec.to_str()}: Checking dependencies...")
            if type(rec.dependencies) is not list:
                print(
                    f"ERROR: package {rec.to_str()}: dependencies must be a list.",
                    file=stderr,
                )
                error += 1
                continue
            ok = True
            dep_list = []
            for dep in rec.dependencies:
                if type(dep) is not dict:
                    ok = False
                    print(
                        f"ERROR: package {rec.to_str()}: dependencies must be a list of dict.",
                        file=stderr,
                    )
                    break
                if "name" not in dep:
                    print(
                        f"ERROR: package {rec.to_str()}: dependencies {dep} must be a contain a name.",
                        file=stderr,
                    )
                    ok = False
                    break
                if "os" not in dep:
                    dep["os"] = os
                if "arch" not in dep:
                    dep["arch"] = arch
                result = self.local.local_database.query(dep)
                if len(result) == 0:
                    print(
                        f"ERROR: package {rec.to_str()}: dependency {dep['name']} Not found:\n{dep}",
                        file=stderr,
                    )
                    ok = False
                    break
                dep_list.append(
                    str(result[0].get_cmake_config_dir()).replace("\\", "/")
                )
            if not ok:
                continue

            #
            #
            # configure
            if self.local.verbosity > 2:
                print(f"package {rec.to_str()}: Configure...")
            if rec.kind not in ["shared", "static"]:
                rec.config = ["Release"]
            rec.configure()
            cmd = f'cmake -S {self._get_source_dir(rec)} -B {self.temp / "build"}'
            cmd += f' -G "{self._get_generator(rec)}"'
            if len(dep_list) != 0:
                cmd += ' -DCMAKE_PREFIX_PATH="' + ";".join(dep_list) + '"'
            cmd += f" {self._get_options_str(rec)}"
            if not try_run(cmd):
                if self.local.verbosity > 0:
                    print(
                        f"ERROR: package {rec.to_str()}: Configuration fail.",
                        file=stderr,
                    )
                error += 1
                continue
            #
            #
            # build & install
            if self.local.verbosity > 2:
                print(f"package {rec.to_str()}: Build and install...")
            has_fail = False
            for conf in rec.config:
                if self.local.verbosity > 2:
                    print(f"package {rec.to_str()}: Build config {conf}...")
                cmd = f"cmake --build {self.temp / 'build'} --target install --config {conf}"
                if self.cross_info["SINGLE_THREAD"]:
                    cmd += f" -j 1"
                if not try_run(cmd):
                    print(
                        f"ERROR: package {rec.to_str()}, ({conf}): install Fail.",
                        file=stderr,
                    )
                    has_fail = True
                    break
            if has_fail:
                error += 1
                continue
            #
            #
            # create the info file
            if self.local.verbosity > 2:
                print(f"package {rec.to_str()}: Create package...")
            rec.install()
            p.to_edp_file(self.temp / "install" / "edp.info")
            # copy to repository
            self.local.import_folder(self.temp / "install")
            # clean Temp
            rec.clean()
            rmtree(self.temp, ignore_errors=True)
        return error
