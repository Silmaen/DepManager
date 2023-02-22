"""
Manage the database
"""
from pathlib import Path


class DataBase:

    def __init__(self):
        from depmanager.internal.database import DataBase
        self.__db = DataBase()
        self.__config = self.__db.config

    # =============== INFORMATIONS =====================
    def get_local_path(self):
        """
        Access to the local databasePath
        :return: the local path
        """
        return self.__config.base_path

    def get_dependency_count(self):
        return self.__db.count_deps()

    # ================== SEARCH ========================
    def search(self,
               name: str = "*",
               version: str = "*",
               os: str = "*",
               arch: str = "*",
               lib_type: str = "*",
               compiler: str = "*"):
        query = {
            "name":     name,
            "version":  version,
            "os":       os,
            "arch":     arch,
            "lib_type": lib_type,
            "compiler": compiler,
        }
        return self.__db.search(query)

    # =============== MODIFICATIONS ====================
    def add(self, location: Path):
        return self.__db.add(location)
