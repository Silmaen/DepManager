"""
Tools for building packages.
"""
from pathlib import Path
from shutil import rmtree
from sys import stderr

from depmanager.api.internal.dependency import version_lt
from depmanager.api.internal.machine import Machine
from depmanager.api.internal.recipe_builder import RecipeBuilder
from depmanager.api.internal.system import LocalSystem
from depmanager.api.local import LocalManager
from depmanager.api.package import PackageManager
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
                    recipes.append(obj(path=file.parent))
                    file_has_recipe = True
            if file_has_recipe:
                idx += 1
        except Exception as err:
            print(
                f"Exception during analysis of file {file}: {err}",
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
        self.pacman = PackageManager(self.local, verbosity=self.local.verbosity)
        self.source_path = source
        if temp is None:
            self.temp = self.local.temp_path / "builder"
        else:
            self.temp = temp
        if self.local.verbosity > 0:
            print(f"Recipes search ..")
        self.recipes = find_recipes(self.source_path, depth)
        self.server_name = server_name
        self.dry_run = dry_run
        self.skip_pull = skip_pull
        self.skip_push = skip_push
        self.forced = forced

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
                    dep_satisfied = True
                    for dep in rec.dependencies:
                        if not self._find_recipe(new_recipe, dep):
                            dep_satisfied = False
                    if dep_satisfied:
                        stalled = False
                        new_recipe.append(rec)
        # add unresolved dependency recipes
        for rec in self.recipes:
            if rec in new_recipe:  # add recipe only once
                continue
            new_recipe.append(rec)
        # replace the list
        self.recipes = new_recipe

    def build_all(
        self,
    ):
        """
        Do the build of recipes.
        :return:
        """
        rmtree(self.temp, ignore_errors=True)
        self.temp.mkdir(parents=True, exist_ok=True)

        mac = Machine(True)
        self.reorder_recipes()

        error = 0
        for rec in self.recipes:
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
            #
            # do a local query
            local_query = self.pacman.query(
                {
                    "name": rec.name,
                    "version": rec.version,
                    "os": os,
                    "arch": arch,
                    "kind": rec.kind,
                    "compiler": compiler,
                    "glibc": glibc,
                },
            )
            if len(local_query) > 0 and not self.forced:
                print(f"Package {rec.to_str()}: already build, skipping.")
                continue
            #
            # remote check and pull
            do_pull = False
            if (
                len(local_query) == 0
                and self.server_name in self.local.remote_database.keys()
                and not self.skip_pull
            ):
                pull_query = self.pacman.query(
                    {
                        "name": rec.name,
                        "version": rec.version,
                        "os": os,
                        "arch": arch,
                        "kind": rec.kind,
                        "compiler": compiler,
                        "glibc": glibc,
                    },
                    self.server_name,
                )
                if len(pull_query) > 0:
                    # do pull !
                    do_pull = True
                    if not self.dry_run:
                        print(f"Package {rec.to_str()}: found on remote, pull it.")
                        self.pacman.add_from_remote(pull_query[0], self.server_name)

            #
            # local check and build
            do_build = False
            do_skip = False
            if self.dry_run:
                if len(local_query) > 0 or do_pull:
                    do_build = False
                    do_skip = True
                else:
                    do_build = True
            else:
                if self.temp.exists():
                    rmtree(self.temp, ignore_errors=True)
                self.temp.mkdir(parents=True, exist_ok=True)
                rec_build = RecipeBuilder(rec, self.temp, self.local, self.cross_info)
                if not rec_build.has_recipes():
                    print("Something gone wrong with the recipe!", file=stderr)
                    continue
                if not rec_build.build(self.forced):
                    error += 1
                rmtree(self.temp, ignore_errors=True)
            #
            # remote push
            do_push = False
            if (
                self.server_name in self.local.remote_database.keys()
                and not self.skip_push
            ):
                if do_build:
                    do_push = True
                if not self.dry_run:
                    local_query = self.pacman.query(
                        {
                            "name": rec.name,
                            "version": rec.version,
                            "os": os,
                            "arch": arch,
                            "kind": rec.kind,
                            "compiler": compiler,
                            "glibc": glibc,
                        },
                    )
                    if len(local_query) == 0:
                        print(
                            f"Package {rec.to_str()}: not found locally after build.",
                            file=stderr,
                        )
                        error += 1
                    else:
                        push_query = self.pacman.query(
                            {
                                "name": rec.name,
                                "version": rec.version,
                                "os": os,
                                "arch": arch,
                                "kind": rec.kind,
                                "compiler": compiler,
                                "glibc": glibc,
                            },
                            self.server_name,
                        )

                        if len(push_query) > 0:
                            print(
                                f"Package {rec.to_str()}: already exists on remote remote {self.server_name}."
                            )
                            if not self.forced:
                                do_push = False
                            else:
                                # to 'force' push, start by deleting the package
                                self.pacman.remove_package(
                                    push_query[0], self.server_name
                                )
                        if do_push:
                            print(
                                f"Package {rec.to_str()}: push to remote {self.server_name}."
                            )
                            self.pacman.add_to_remote(local_query[0], self.server_name)
            if self.dry_run:
                print(
                    f"Package {rec.to_str()} - action:{['',' pull'][do_pull]}{['',' skip'][do_skip]}{['',' build'][do_build]}{['',' push'][do_push]}."
                )
        return error
