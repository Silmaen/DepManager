"""
Add the command for getting information.
"""
possible_info = ["basedir", "cmakedir", "version"]


class InfoCommand:
    """
    Class managing the information command.
    """

    def __init__(self, system=None):
        from depmanager.api.local import LocalManager
        self.local_instance = LocalManager(system)

    def basedir(self):
        """
        Print the actual base dir in the terminal.
        """
        print(self.local_instance.get_base_path())

    def cmakedir(self):
        """
        Print the actual cmake dir in the terminal.
        """
        print(self.local_instance.get_cmake_dir())

    def version(self):
        """
        Print the actual version of the program.
        """
        print(f"depmanager version {self.local_instance.get_version()}.")


def info(args, system=None):
    """
    Info's entrypoint.
    :param args: Command Line Arguments.
    :param system: The local system
    """
    if args.what not in possible_info:
        return
    getattr(InfoCommand(system), args.what)()


def add_info_parameters(sub_parsers):
    """
    Definition of info parameters.
    :param sub_parsers: The parent parser.
    """
    info_parser = sub_parsers.add_parser("info")
    info_parser.description = "Tool to search for dependency in the library"
    info_parser.add_argument(
            "what",
            type=str,
            choices=possible_info,
            help="The information you want about the program")
    info_parser.set_defaults(func=info)
