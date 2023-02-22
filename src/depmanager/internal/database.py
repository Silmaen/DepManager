"""
Managing the local database
"""
from pathlib import Path


class DataBase:
    def __init__(self):
        from .common import LocalConfiguration
        self.config = LocalConfiguration()
        if not self.config.data_path.exists():
            self.config.data_path.mkdir(parents=True, exist_ok=True)

    def search(self, query: dict):
        result = []
        all_dep = self.__get_all_deps()
        for dep in all_dep:
            if dep.match(query=query):
                result.append(dep)
        return result

    def count_deps(self):
        return len(self.__get_all_deps())

    def add(self, path: Path):
        from .recipe import Recipe
        rec = Recipe(self, path)
        rec.add_to_database()

    def __get_all_deps(self):
        """
        Look into the local database for all the deps
        :return: list of all deps
        """
        from .dependency import Dependency
        result = []
        for dep_dir in self.config.data_path.iterdir():
            dep = Dependency()
            dep.from_path(dep_dir)
            if dep.is_valid():
                result.append(dep)
        return result
