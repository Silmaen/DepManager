"""

"""
import platform
import shutil
from sys import stderr


def try_run(cmd):
    from subprocess import run
    try:
        ret = run(cmd, shell=True)
        if ret.returncode != 0:
            print(F"ERROR '{cmd}' \n bad exit code ({ret.returncode})", file=stderr)
            exit(-666)
    except Exception as err:
        print(F"ERROR '{cmd}' \n exception during run {err}", file=stderr)
        exit(-666)


class Recipe:
    generator = ""

    def __init__(self, database, recipe_path):
        from pathlib import Path
        import importlib.util
        import inspect
        from depmanager.api import recipe
        self.db = database
        self.temp_dir = Path()
        self.base_path = Path(recipe_path).absolute().parent
        self.recipe_classes = []
        self.config = self.db.config
        spec = importlib.util.spec_from_file_location(self.base_path.name, recipe_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for name, obj in inspect.getmembers(mod):
            if inspect.isclass(obj) and name != "Recipe" and issubclass(obj, recipe.Recipe):
                self.recipe_classes.append(obj())

    def _get_source_dir(self, rec):
        from pathlib import Path
        source_dir = Path(rec.source_dir)
        if not source_dir.is_absolute():
            source_dir = self.base_path / source_dir
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
        out = F"-DCMAKE_INSTALL_PREFIX={self.temp_dir / 'install'}"
        out += F" -DBUILD_SHARED_LIBS={['OFF', 'ON'][rec.lib_type.lower() == 'shared']}"
        for key, val in rec.cache_variables.items():
            out += F" -D{key}={val}"
        return out

    def add_to_database(self):
        from pathlib import Path
        from tempfile import mktemp
        if len(self.recipe_classes) == 0:
            print("WARNING: no recipes found in the given path")
            return

        for rec in self.recipe_classes:
            self.temp_dir = Path(mktemp())
            arch = platform.machine().replace("AMD", "x86_")
            os = platform.system()
            compiler = "gnu"
            rec.source()
            #
            #
            # configure
            rec.configure()
            cmd = F"cmake -S {self._get_source_dir(rec)} -B {self.temp_dir / 'build'} -G \"{self._get_generator(rec)}\" {self._get_options_str(rec)}"
            try_run(cmd)
            #
            #
            # build & install
            for conf in rec.config:
                cmd = F"cmake --build {self.temp_dir / 'build'} --target install --config {conf}"
                try_run(cmd)
            #
            #
            # create the info file
            rec.install()
            with open(self.temp_dir / 'install' / "edp.info", "w") as fp:
                fp.write(F"name {rec.name}\n")
                fp.write(F"version {rec.version}\n")
                fp.write(F"os {os}\n")
                fp.write(F"arch {arch}\n")
                fp.write(F"lib_type {rec.lib_type}\n")
                fp.write(F"compiler {compiler}\n")
            # copy to repository
            destination = self.config.hash_path(
                name=rec.name,
                version=rec.version,
                os=os,
                arch=arch,
                lib_type=rec.lib_type,
                compiler=compiler
            )
            shutil.copytree(self.temp_dir / 'install', destination)
            # clean Temp
            shutil.rmtree(self.temp_dir)
