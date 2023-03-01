"""
Common helper function
"""
from argparse import ArgumentParser
from pathlib import Path


class LocalConfiguration:
    def __init__(self):
        self.base_path = Path.home() / ".edm"
        self.file = self.base_path / "config.ini"
        self.data_path = self.base_path / "data"

        # default values
        self.config = {

        }
        if self.file.exists():
            self.load_config()
        else:
            self.save_config()
        self.check_missing()

    def save_config(self):
        """
        Save the configuration
        """
        import json
        with open(self.file, "w") as fp:
            fp.write(json.dumps(self.config, indent=4))

    def load_config(self):
        """
        Load the configuration
        """
        import json
        with open(self.file, "r") as fp:
            self.config = json.load(fp)

    def check_missing(self):
        """
        Search for all required field in data and add them
        """
        required = {
            "remotes": {}
        }
        modified = False
        for req, default in required.items():
            if req not in self.config.keys():
                self.config[req] = default
                modified = True
        if modified:
            self.save_config()

    def hash_path(self, name: str, version: str, os: str, arch: str, lib_type: str, compiler: str):
        """
        Get the hash for path determination
        :param name:
        :param version:
        :param os:
        :param arch:
        :param lib_type:
        :param compiler:
        :return:
        """
        from hashlib import sha1
        hash_ = sha1()
        hash_.update(
            name.encode() + version.encode() + os.encode() + arch.encode() + lib_type.encode() + compiler.encode())
        return self.data_path / str(hash_.hexdigest())


def add_common_arguments(parser: ArgumentParser):
    """
    Add the common option to the parser.
    :param parser: Where to add options.
    """
    parser.add_argument(
        "--verbose", "-v",
        action="count",
        default=0,
        help="The verbosity level"
    )


def add_query_arguments(parser: ArgumentParser):
    """
    Add all arguments related to query.
    :param parser: the parser for arguments.
    """
    parser.add_argument(
        "--predicate", "-p",
        type=str,
        help="Name/Version of the packet to search, use * as wildcard",
        default="*/*"
    )
    parser.add_argument(
        "--type", "-t",
        type=str,
        choices=["static", "shared", "header", "*"],
        help="Library type of the packet to search (* for any)",
        default="*"
    )
    parser.add_argument(
        "--os", "-o",
        type=str,
        help="Operating system of the packet to search, use * as wildcard",
        default="*"
    )
    parser.add_argument(
        "--arch", "-a",
        type=str,
        help="CPU architecture of the packet to search, use * as wildcard",
        default="*"
    )
    parser.add_argument(
        "--compiler", "-c",
        type=str,
        help="Compiler of the packet to search, use * as wildcard",
        default="*"
    )


def query_argument_to_dict(args):
    """
    Convert input argument into query dict.
    :param args: Input arguments.
    :return: Query dict.
    """
    if not "/" in args.predicate:
        return {}
    name, version = args.predicate.split("/", 1)
    return {
        "name": name,
        "version": version,
        "os": args.os,
        "arch": args.arch,
        "lib_type": args.type,
        "compiler": args.compiler
    }
