"""
Tools for building packages.
"""
import platform
from shutil import rmtree
from pathlib import Path
from sys import stderr
from depmanager.api.internal.system import LocalSystem, Props


def try_run(cmd):
    """
    Safe run of commands.
    :param cmd: Command to run.
    """
    from subprocess import run
    try:
        ret = run(cmd, shell=True)
        if ret.returncode != 0:
            print(F"ERROR '{cmd}' \n bad exit code ({ret.returncode})", file=stderr)
            exit(-666)
    except Exception as err:
        print(F"ERROR '{cmd}' \n exception during run {err}", file=stderr)
        exit(-666)


class Builder:
    """
    Manager for building packages.
    """

    def __init__(self,
                 source: Path,
                 temp: Path = None,
                 local: LocalSystem = None):
        from importlib.util import spec_from_file_location, module_from_spec
        from inspect import getmembers, isclass
        from depmanager.api.recipe import Recipe
        self.generator = ""
        if local is None:
            self.local = LocalSystem()
        else:
            self.local = local
        self.source_path = source
        if temp is None:
            self.temp = self.local.temp_path / "builder"
        else:
            self.temp = temp
        rmtree(self.temp, ignore_errors=True)
        self.temp.mkdir(parents=True)
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
        for key, val in rec.cache_variables.items():
            out += F" -D{key}={val}"
        return out

    def build_all(self):
        """
        Do the build of recipes.
        """
        for rec in self.recipes:
            arch = platform.machine().replace("AMD", "x86_")
            os = platform.system()
            compiler = "gnu"
            rec.source()
            #
            #
            # configure
            rec.configure()
            cmd = F"cmake -S {self._get_source_dir(rec)} -B {self.temp / 'build'} -G \"{self._get_generator(rec)}\" {self._get_options_str(rec)}"
            try_run(cmd)
            #
            #
            # build & install
            for conf in rec.config:
                cmd = F"cmake --build {self.temp / 'build'} --target install --config {conf}"
                try_run(cmd)
            #
            #
            # create the info file
            rec.install()
            p = Props({
                "name"    : rec.name,
                "version" : rec.version,
                "os"      : os,
                "arch"    : arch,
                "kind"    : rec.kind,
                "compiler": compiler
            })
            p.to_edp_file(self.temp / 'install' / "edp.info")
            # copy to repository
            self.local.import_folder(self.temp / 'install')
            # clean Temp
            rmtree(self.temp)
