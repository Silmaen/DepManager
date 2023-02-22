"""
Module for adding new library
"""


def add(args):
    from depmanager.api.database import DataBase
    from pathlib import Path
    db = DataBase()
    location = Path(args.recipe)
    if not location.exists():
        print(F"ERROR: not able to find '{location}'")
        exit(-666)
    scripts = []
    if location.is_file():
        if location.suffix != ".py":
            print(F"ERROR: file '{location}' is not a python file")
            exit(-666)
        scripts.append(location)
    if location.is_dir():
        for file in location.iterdir():
            if file.is_file() and file.suffix == ".py":
                scripts.append(file)
    for script in scripts:
        db.add(script)


def add_arguments(sub_parsers):
    search_parser = sub_parsers.add_parser("add")
    search_parser.description = "Tool to search for dependency in the library"
    search_parser.add_argument(
        "recipe",
        type=str,
        help="The path of the package recipe")
    search_parser.set_defaults(func=add)
