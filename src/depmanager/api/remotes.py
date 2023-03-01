"""
Instance of remotes manager
"""


class RemotesManager:
    """
    Local manager.
    """
    def __init__(self):
        from depmanager.internal.remote import Remotes
        self.__remotes = Remotes()

    def get_remote_list(self):
        """
        Get a list of remotes.
        :return: List of remotes
        """
        return self.__remotes.get_remotes()

    def is_remote_online(self, name: str):
        """
        Check if the given remote is online.
        :param name: Remote's name
        :return: True if remote respond.
        """
        return self.__remotes.is_online(name)

    def add_remote(self, name: str, url: str, default: bool = False):
        """
        Add a remote to the list.
        :param name: Remote's name.
        :param url: Remote's url
        :param default: If this remote should become the new default
        """
        self.__remotes.add(name, url, default)

    def remove_remote(self, name: str):
        """
        Remove a remote from the list.
        :param name: Remote's name.
        """
        self.__remotes.remove(name)

