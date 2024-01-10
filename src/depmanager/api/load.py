"""
Function for loading a full environment
"""
from pathlib import Path

from depmanager.api.internal.config_file import ConfigFile
from depmanager.api.internal.system import LocalSystem
from depmanager.api.local import LocalManager
from depmanager.api.package import PackageManager


def load_environment(
    system, config: Path, kind: str, os: str, arch: str, compiler: str, glibc: str
):
    """
    Do work on environment.
    """
    if type(system) is LocalSystem:
        internal_system = system
    elif type(system) is LocalManager:
        internal_system = system.get_sys()
    else:
        internal_system = LocalSystem()
    verbosity = internal_system.verbosity

    pacman = PackageManager(internal_system)
    conf = ConfigFile(config)
    # treat server section:
    srv = conf.server_to_add()
    if verbosity > 2:
        print("**Server actions...")
    if srv != {}:
        if "default" not in srv:
            srv["default"] = False
        if "name" in srv:
            if verbosity > 2:
                print(f"Adding remote {srv['name']} ({srv})")
            if srv["name"] not in internal_system.remote_database:
                internal_system.add_remote(srv)

    if verbosity > 2:
        print("**Package actions...")
    # treat packages section.
    packs = conf.get_packages()
    if verbosity > 2:
        if len(packs) == 0:
            print("No packages found.")
    output = ""
    err_code = 0
    for pack, constrains in packs.items():
        if verbosity > 2:
            print(f"Treat Package {pack}")
        # first query: identify if header-only and if there is something somewhere
        res1 = pacman.query({"name": pack}, transitive=True)
        if len(res1) == 0:
            if verbosity > 2:
                print(f"    Not Found at all!")
            # nothing found!!!
            if constrains is None or type(constrains) is not dict:
                err_code = 1
                continue
            if "optional" not in constrains:
                err_code = 1
                continue
            if not constrains["optional"]:
                err_code = 1
            continue
        platform_dependent = res1[0].is_platform_dependent()
        #
        # generate specific query
        query = {
            "name": pack,
        }
        if platform_dependent:
            query["os"] = os
            query["arch"] = arch
            query["compiler"] = compiler
            query["kind"] = kind
            if glibc not in ["", None]:
                query["glibc"] = glibc
        is_optional = False
        to_skip = False
        if constrains is not None and type(constrains) is dict:
            if "optional" in constrains:
                is_optional = constrains["optional"]
            if "version" in constrains:
                query["version"] = constrains["version"]
            if "kind" in constrains:
                query["kind"] = constrains["kind"]
            for key in ["os", "arch", "compiler"]:
                if key in constrains:
                    restrained = []
                    if type(constrains[key]) is str:
                        restrained = constrains[key].split(",")
                    elif type(constrains[key]) is list:
                        restrained = constrains[key]
                    if key == "os" and os not in restrained:
                        to_skip = True
                    if key == "arch" and arch not in restrained:
                        to_skip = True
                    if key == "compiler" and compiler not in restrained:
                        to_skip = True
        if to_skip:
            if verbosity > 2:
                print(f"    SKIPPING")
            continue
        #
        # search package
        res1 = pacman.query(query, transitive=False)
        new_path = ""
        check_newer = conf.do_pull_newer()
        if len(res1) > 0:
            if verbosity > 2:
                print(f"    FOUND Locally!")
            new_path = res1[0].get_cmake_config_dir()
        else:
            if verbosity > 2:
                print(f"    Not Found locally.")
            if is_optional:
                if verbosity > 2:
                    print(f"    Optional -> SKIP.")
                continue
            if conf.do_pull():
                if verbosity > 2:
                    print(f"    Trying to pull")
                res = pacman.query(query, "default", transitive=False)
                if len(res) == 0:
                    err_code = 1
                    if verbosity > 2:
                        print(f"    Not Found on server!")
                    continue
                pacman.add_from_remote(res[0], "default")
                res = pacman.query(query, transitive=False)
                if len(res) == 0:
                    err_code = 1
                    if verbosity > 2:
                        print(f"    Pull fail!")
                    continue
                new_path = res[0].get_cmake_config_dir()
                check_newer = False
        if check_newer:
            if verbosity > 2:
                print(f"    check newer")
            res = pacman.query(query, "default", transitive=False)
            if len(res) > 0:
                if res[0].is_newer(res1[0].properties.build_date):
                    if verbosity > 2:
                        print(f"    Found newer")
                    pacman.add_from_remote(res[0], "default")
                    res = pacman.query(query, transitive=False)
                    if len(res) == 0:
                        err_code = 1
                        continue
                    new_path = res1[0].get_cmake_config_dir()
        if new_path != "":
            if len(output) == 0:
                output += f"{new_path}"
            else:
                output += f";{new_path}"
        else:
            if verbosity > 2:
                print(f"    ** empty path **")
            err_code = 1

    return err_code, output
