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
