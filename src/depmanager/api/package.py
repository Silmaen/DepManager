"""
Manager for package
"""


class PackageManager:
    """
    Manager fo package
    """
    def __init__(self):
        from depmanager.internal.database import DataBase
        self.__db = DataBase()

    def query(self, query):
        """
        Do a query into lo
        :param query:
        :return:
        """
        return self.__db.search(query)
