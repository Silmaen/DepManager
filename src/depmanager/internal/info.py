"""
Getting information
"""

possible_info = ["basedir", "cache", "remotes", "cmakedir"]


def info(args):
    if args.what not in possible_info:
        return
    getattr(Info(), args.what)()



def info_arguments(sub_parsers):
    search_parser = sub_parsers.add_parser("info")
    search_parser.description = "Tool to search for dependency in the library"
    search_parser.add_argument(
        "what",
        type=str,
        choices=possible_info,
        help="The information you want about the program")
    search_parser.set_defaults(func=info)


class Info:
    """
    Class managing the 'info' command
    """

    def basedir(self):
        print(self.__db.config.base_path)

    def remotes(self):
        print("Not Yet implemented")

    def cache(self):
        print(F"Found {self.__db.count_deps()} dependencies in local cache")

    def cmakedir(self):
        from pathlib import Path
        print(Path(__file__).parent.parent / "cmake")

    def __init__(self):
        from depmanager.internal.database import DataBase
        self.__db = DataBase()
