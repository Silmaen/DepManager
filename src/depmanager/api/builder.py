"""
Tools for building packages.
"""
import platform
from shutil import rmtree
from pathlib import Path
from sys import stderr
from depmanager.api.internal.system import LocalSystem, Props
from depmanager.api.local import LocalManager


def try_run(cmd):
    """
    Safe run of commands.
    :param cmd: Command to run.
    """
    from subprocess import run
    try:
        ret = run(cmd, shell=True, bufsize=0)
        if ret.returncode != 0:
            print(F"ERROR '{cmd}' \n bad exit code ({ret.returncode})", file=stderr)
            return False
    except Exception as err:
        print(F"ERROR '{cmd}' \n exception during run {err}", file=stderr)
        return False
    return True


class Builder:
    """
    Manager for building packages.
    """

    def __init__(self,
                 source: Path,
                 temp: Path = None,
                 local: LocalSystem = None,
                 cross_info=None):
        if cross_info is None:
            cross_info = {}
        from importlib.util import spec_from_file_location, module_from_spec
        from inspect import getmembers, isclass
        from depmanager.api.recipe import Recipe
        self.cross_info = cross_info
        self.generator = ""
        if isinstance(local, LocalSystem):
            self.local = local
        elif isinstance(local, LocalManager):
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
            print(F"ERROR: could not find source dir {source_dir}", file=stderr)
            exit(-666)
        if not (source_dir / "CMakeLists.txt").exists():
            print(F"ERROR: could not find CMakeLists.txt in dir {source_dir}", file=stderr)
            exit(-666)
        return source_dir

    def _get_generator(self, rec):
        if self.generator not in ["", None]:
            return self.generator
        if len(rec.config) > 1:
            return "Ninja Multi-Config"
        return "Ninja"

    def _get_options_str(self, rec):
        out = F"-DCMAKE_INSTALL_PREFIX={self.temp / 'install'}"
        out += F" -DBUILD_SHARED_LIBS={['OFF', 'ON'][rec.kind.lower() == 'shared']}"
        if "C_COMPILER" in self.cross_info:
            out += F" -DCMAKE_C_COMPILER={self.cross_info['C_COMPILER']}"
        if "CXX_COMPILER" in self.cross_info:
            out += F" -DCMAKE_CXX_COMPILER={self.cross_info['CXX_COMPILER']}"
        if rec.settings["os"].lower() in ["linux"]:
            out += " -DCMAKE_SKIP_INSTALL_RPATH=ON -DCMAKE_POSITION_INDEPENDENT_CODE=ON"
        for key, val in rec.cache_variables.items():
            out += F" -D{key}={val}"
        return out

    def build_all(self, forced:bool = False):
        """
        Do the build of recipes.
        """
        for rec in self.recipes:
            #
            #
            if rec.kind == "header":
                arch = "any"
                os = "any"
                compiler = "any"
            else:
                if "CROSS_ARCH" in self.cross_info:
                    arch = self.cross_info["CROSS_ARCH"]
                else:
                    arch = platform.machine().replace("AMD", "x86_")
                if "CROSS_OS" in self.cross_info:
                    os = self.cross_info["CROSS_OS"]
                else:
                    os = platform.system()
                compiler = "gnu"

            rec.define(os, arch, compiler, self.temp / 'install')

            #
            #
            # Check for existing
            p = Props({
                "name"    : rec.name,
                "version" : rec.version,
                "os"      : os,
                "arch"    : arch,
                "kind"    : rec.kind,
                "compiler": compiler
            })
            search = self.local.local_database.query(p)
            if len(search) > 0:
                if forced:
                    print(f"REMARK: library {p.get_as_str()} already exists, overriding it.")
                else:
                    print(f"REMARK: library {p.get_as_str()} already exists, skipping it.")
                    continue
            rec.source()

            #
            #
            # check dependencies
            if type(rec.dependencies) != list:
                print(f"ERROR: dependencies of {rec.to_str()} must be a list.", file=stderr)
                continue
            ok = True
            dep_list = []
            for dep in rec.dependencies:
                if type(dep) != dict:
                    ok = False
                    print(f"ERROR: dependencies of {rec.to_str()} must be a list of dict.", file=stderr)
                    break
                if "name" not in dep:
                    print(f"ERROR: dependencies of {rec.to_str()}\n{dep} must be a contain a name.", file=stderr)
                    ok = False
                    break
                if "os" not in dep:
                    dep["os"] = os
                if "arch" not in dep:
                    dep["arch"] = arch
                result = self.local.local_database.query(dep)
                if len(result) == 0:
                    print(f"ERROR: dependencies of {rec.to_str()}, {dep['name']} Not found:\n{dep}", file=stderr)
                    ok = False
                    break
                dep_list.append(str(result[0].get_cmake_config_dir()).replace("\\", "/"))
            if not ok:
                continue

            #
            #
            # configure
            rec.configure()
            cmd = F'cmake -S {self._get_source_dir(rec)} -B {self.temp / "build"}'
            cmd += F' -G "{self._get_generator(rec)}"'
            if len(dep_list) != 0:
                cmd += ' -DCMAKE_PREFIX_PATH="' + ";".join(dep_list) + '"'
            cmd += F' {self._get_options_str(rec)}'
            cont = try_run(cmd)

            #
            #
            # build & install
            if cont:
                for conf in rec.config:
                    cmd = F"cmake --build {self.temp / 'build'} --target install --config {conf}"
                    cont = try_run(cmd)
                    if not cont:
                        break

            #
            #
            # create the info file
            if cont:
                rec.install()
                p.to_edp_file(self.temp / 'install' / "edp.info")
                # copy to repository
                self.local.import_folder(self.temp / 'install')
            # clean Temp
            rec.clean()
            rmtree(self.temp)
            if not cont:
                exit(-666)
