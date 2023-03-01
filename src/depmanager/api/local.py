"""
Local instance of manager
"""
from pathlib import Path


class LocalManager:
    """
    Local manager.
    """
    def __init__(self):
        from depmanager.internal.database import DataBase
        self.__db = DataBase()
        self.root_path = Path(__file__).resolve().parent.parent

    def get_base_path(self):
        """
        Get the base folder of local data.
        :return: The base path.
        """
        return self.__db.config.base_path

    def get_cmake_dir(self):
        """
        Get the path to cmake additional functions.
        :return: Path to cmake functions.
        """
        return self.root_path / "cmake"

    def query_package(self, query):
        """

        :param query:
        :return:
        """
