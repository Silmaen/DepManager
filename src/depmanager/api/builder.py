"""
Tools for building packages.
"""

from pathlib import Path
from shutil import rmtree

from api.internal.dependency import version_lt
from api.internal.machine import Machine
from api.internal.messaging import log
from api.internal.recipe_builder import RecipeBuilder
from api.internal.system import LocalSystem
from api.local import LocalManager
from api.package import PackageManager
from api.recipe import Recipe


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
                if "setup" in entry.name:  # skip files like setup.py
                    continue
                with open(entry, "r") as f:
                    if f.readline().startswith("#!"):  # skip files with a shebang
                        continue
                all_py.append(entry.resolve())
            elif entry.is_dir() and (depth < 0 or dep < depth):
                search_rep(entry, dep + 1)

    search_rep(location, 0)
    log.info(f"found {len(all_py)} python files")
    idx = 0
    for file in all_py:
        try:
            spec = spec_from_file_location(file.name, file)
            mod = module_from_spec(spec)
            spec.loader.exec_module(mod)
            file_has_recipe = False
            for name, obj in getmembers(mod):
                if isclass(obj) and name != "Recipe" and issubclass(obj, Recipe):
                    recipes.append(obj(path=file.parent))
                    file_has_recipe = True
            if file_has_recipe:
                idx += 1
        except Exception as err:
            log.error(f"Exception during analysis of file {file}: {err}")
            continue
    log.info(f"found {len(recipes)} recipes in {idx} files")
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
        toolset: str = "",
        server_name: str = "",
        dry_run: bool = False,
        skip_pull: bool = False,
        skip_push: bool = False,
        forced: bool = False,
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
        if toolset in [None, ""]:
            self.toolset = None
        else:
            self.toolset = self.local.get_toolset(toolset)
        self.pacman = PackageManager(self.local)
        self.source_path = source
        if temp is None:
            self.temp = self.local.temp_path / "builder"
        else:
            self.temp = temp
        log.info(f"Recipes search ..")
        self.recipes = find_recipes(self.source_path, depth)
        self.server_name = server_name
        self.dry_run = dry_run
        self.skip_pull = skip_pull
        self.skip_push = skip_push
        self.forced = forced

    def query_from_recipe(self, recipe, machine: Machine):
        glibc = ""
        if recipe.kind == "header":
            arch = "any"
            os = "any"
            abi = "any"
        else:
            if "CROSS_ARCH" in self.cross_info:
                arch = self.cross_info["CROSS_ARCH"]
            else:
                arch = machine.arch
            if "CROSS_OS" in self.cross_info:
                os = self.cross_info["CROSS_OS"]
            else:
                os = machine.os
            abi = machine.default_abi
            glibc = machine.glibc
        return {
            "name": recipe.name,
            "version": recipe.version,
            "os": os,
            "arch": arch,
            "kind": recipe.kind,
            "abi": abi,
            "glibc": glibc,
        }

    def has_recipes(self):
        """
        Check recipes in the list.
        :return: True if contain recipe.
        """
        return len(self.recipes) > 0

    def _find_recipe(self, rec_list: list, criteria: dict):
        found = False
        for rec in rec_list:
            if "name" in criteria:
                if rec.name != criteria["name"]:
                    continue
            if "kind" in criteria:
                if rec.kind != criteria["kind"]:
                    continue
            if "version" in criteria:
                if version_lt(rec.version, criteria["version"]):
                    continue
            found = True
            break
        return found

    def reorder_recipes(self):
        """
        Reorder the recipes to take the dependencies into account.
        """
        new_recipe = []
        stalled = False
        while not stalled:
            for rec in self.recipes:
                stalled = True
                if rec in new_recipe:  # add recipe only once
                    continue
                if len(rec.dependencies) == 0:  # no dependency -> just add it!
                    stalled = False
                    new_recipe.append(rec)
                else:
                    unfulfilled_deps = []
                    dependencies = [{"dep": d, "from": d} for d in rec.dependencies]
                    for dep in dependencies:
                        loc = self.pacman.query(dep["dep"])
                        if len(loc) > 0:
                            log.info(
                                f"Found dependency {dep['dep']} in local DB (needed for {dep['from']})."
                            )
                            if loc[0].has_dependency():
                                for sub_dep in loc[0].get_dependency_list():
                                    dependencies.append(
                                        {"dep": sub_dep, "from": dep["dep"]}
                                    )
                            continue
                        if self._find_recipe(new_recipe, dep["dep"]):
                            log.info(
                                f"Found dependency {dep['dep']} in new recipe list (needed for {dep['from']})."
                            )
                            continue
                        log.warn(
                            f"Dependency {dep['dep']} (needed for {dep['from']}) not fulfilled for {rec}."
                        )
                        unfulfilled_deps.append(dep["dep"])
                    if len(unfulfilled_deps) == 0:
                        stalled = False
                        new_recipe.append(rec)
                    else:
                        log.warn(f"Recipe {rec} has unfulfill dependencies !!")
        # add unresolved dependency recipes
        for rec in self.recipes:
            if rec in new_recipe:  # add recipe only once
                continue
            log.warning(f"Added {rec.to_str()} with missing dependency.")
            new_recipe.append(rec)
        # replace the list
        self.recipes = new_recipe

    def build_all(self):
        """
        Do the build of recipes.
        :return:
        """
        rmtree(self.temp, ignore_errors=True)
        self.temp.mkdir(parents=True, exist_ok=True)

        mac = Machine(True, self.toolset)
        #
        # Reorder Recipes
        self.reorder_recipes()
        #
        # Distinguish recipes to build or to pull
        #
        recipe_to_build = []
        if self.skip_pull:
            recipe_to_build = self.recipes
        else:
            for recipe in self.recipes:
                query_result = self.pacman.query(self.query_from_recipe(recipe, mac))
                if len(query_result):
                    log.info(
                        f"Package {recipe.to_str()} found locally for {mac}, no build."
                    )
                    continue
                query_result = self.pacman.query(
                    self.query_from_recipe(recipe, mac), remote_name="default"
                )
                if len(query_result) > 0:
                    log.info(
                        f"Package {recipe.to_str()} found on remote for {mac}, pulling, no build."
                    )
                    if not self.dry_run:
                        self.pacman.add_from_remote(query_result[0], "default")
                    continue
                recipe_to_build.append(recipe)
        nb = len(recipe_to_build)
        if nb == 0:
            log.info("Nothing to build!")
            return 0
        else:
            log.info(f"{nb} recipe{['', 's'][nb > 1]} needs to be build.")
            for recipe in recipe_to_build:
                log.info(f" --- Need to build: {recipe.to_str()} for {mac}...")
        #
        # do the builds
        #
        error = 0
        for recipe in recipe_to_build:
            log.info(f"Building: {recipe.to_str()} for {mac}...")
            if self.dry_run:
                continue
            # clear the static cache variables, in case of previous builds
            recipe.cache_variables.clear()
            # clear the temp directory if not void.
            if self.temp.exists():
                rmtree(self.temp, ignore_errors=True)
            self.temp.mkdir(parents=True, exist_ok=True)
            builder = RecipeBuilder(
                recipe, self.temp, self.local, self.cross_info, self.toolset
            )
            if not builder.has_recipes():
                log.warn("WARNING Something gone wrong with the recipe!")
                continue
            # do the build
            if not builder.build(self.forced):
                error += 1
            # Actualize the local database
            self.local.local_database.reload()
        # clean temp directory when all build finished
        rmtree(self.temp, ignore_errors=True)
        #
        # do the push
        #
        for recipe in recipe_to_build:
            if not self.dry_run:
                packs = self.pacman.query(self.query_from_recipe(recipe, mac))
                if len(packs) == 0:
                    log.error(f"recipe {recipe.to_str()} should be built for {mac}")
                    error += 1
                    continue
                elif len(packs) > 1:
                    log.warn(
                        f"recipe {recipe.to_str()} for {mac} seems to appear more than once"
                    )
                if self.skip_push:
                    log.info(
                        f"SKIP pushing {packs[0].properties.get_as_str()} for {mac} to te remote!"
                    )
                else:
                    log.info(
                        f"Pushing {packs[0].properties.get_as_str()} for {mac} to te remote!"
                    )
                    self.pacman.add_to_remote(packs[0], "default")
            else:
                if self.skip_push:
                    log.info(f"SKIP pushing {recipe.to_str()} for {mac} to te remote!")
                else:
                    log.info(f"Pushing {recipe.to_str()} for {mac} to te remote!")
        return error
