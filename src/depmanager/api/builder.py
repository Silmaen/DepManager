"""
Tools for building packages.
"""
from pathlib import Path
from shutil import rmtree
from sys import stderr

from depmanager.api.internal.recipe_builder import RecipeBuilder
from depmanager.api.internal.system import LocalSystem
from depmanager.api.local import LocalManager
from depmanager.api.recipe import Recipe


def find_recipes(location: Path, depth: int = -1):
    """
    List all recipes in the given location.
    :param location: Starting location.
    :param depth: Folder's depth of search, negative means infinite.
    :return: List of recipes
    """
    from importlib.util import spec_from_file_location, module_from_spec
    from inspect import getmembers, isclass

    recipes = []

    all_py = []

    def search_rep(rep: Path, dep: int):
        """
        Recursive search function, a bit faster than a rglob.
        :param rep: Folder to look.
        :param dep: Current depth of search
        """
        for entry in rep.iterdir():
            if entry.is_file():
                if entry.suffix != ".py":
                    continue
                if "conan" in entry.name:  # skip conan files
                    continue
                if "doxy" in entry.name:  # skip doxygen files
                    continue
                with open(entry, "r") as f:
                    if f.readline().startswith("#!"):  # skip files with a shebang
                        continue
                all_py.append(entry.resolve())
            elif entry.is_dir() and (depth < 0 or dep < depth):
                search_rep(entry, dep + 1)

    search_rep(location, 0)
    print(f"found {len(all_py)} python files")
    idx = 0
    for file in all_py:
        try:
            spec = spec_from_file_location(file.name, file)
            mod = module_from_spec(spec)
            spec.loader.exec_module(mod)
            file_has_recipe = False
            for name, obj in getmembers(mod):
                if isclass(obj) and name != "Recipe" and issubclass(obj, Recipe):
                    recipes.append(obj())
                    file_has_recipe = True
            if file_has_recipe:
                idx += 1
        except Exception as err:
            print(
                f"Exception during analysis of file {file}, module {name} : {err}",
                file=stderr,
            )
            continue
    print(f"found {len(recipes)} recipes in {idx} files")
    return recipes


class Builder:
    """
    Manager for building packages.
    """

    def __init__(
        self,
        source: Path,
        temp: Path = None,
        depth: int = 0,
        local: LocalSystem = None,
        cross_info=None,
    ):
        if cross_info is None:
            cross_info = {}

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
        if self.local.verbosity > 0:
            print(f"Recipes search ..")
        self.recipes = find_recipes(self.source_path, depth)

    def has_recipes(self):
        """
        Check recipes in the list.
        :return: True if contain recipe.
        """
        return len(self.recipes) > 0

    def build_all(self, forced: bool = False):
        """
        Do the build of recipes.
        """
        rmtree(self.temp, ignore_errors=True)
        self.temp.mkdir(parents=True, exist_ok=True)
        error = 0
        for rec in self.recipes:
            if self.temp.exists():
                rmtree(self.temp, ignore_errors=True)
            self.temp.mkdir(parents=True, exist_ok=True)
            rec_build = RecipeBuilder(rec, self.temp, self.local, self.cross_info)
            if not rec_build.has_recipes():
                print("Something gone wrong with the recipe!", file=stderr)
                continue
            if not rec_build.build(forced):
                error += 1
            rmtree(self.temp, ignore_errors=True)
        return error
