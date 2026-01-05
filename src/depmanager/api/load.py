"""
Function for loading a full environment
"""

from pathlib import Path

from api.internal.config_file import ConfigFile
from api.internal.messaging import log
from api.internal.system import LocalSystem
from api.local import LocalManager
from api.package import PackageManager


def load_environment(
    system, config: Path, kind: str, os: str, arch: str, abi: str, glibc: str
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

    log.info(f"Loading environment from {config} for {os}-{arch}-{abi} ({kind})")
    pacman = PackageManager(internal_system)
    conf = ConfigFile(config)
    # treat server section:
    srv = conf.server_to_add()
    log.debug("**Server actions...")
    if srv != {}:
        if "default" not in srv:
            srv["default"] = False
        if "name" in srv:
            if srv["name"] not in internal_system.remote_database:
                log.info(f"Adding remote {srv['name']} ({srv})")
                internal_system.add_remote(srv)
            else:
                log.info(f"Remote {srv['name']} already present.")

    log.debug("**Package actions...")
    # treat packages section.
    packs = conf.get_packages()
    if len(packs) == 0:
        log.debug("No packages found.")
    output = ""
    err_code = 0
    queries = []
    for pack, constrains in packs.items():
        res = pacman.query({"name": pack})
        not_header = False
        if len(res) > 0:
            if res[0].is_platform_dependent():
                not_header = True
        # build queries
        if not_header:
            query = {"name": pack, "os": os, "arch": arch, "abi": abi, "kind": kind}
            if glibc not in ["", None]:
                query["glibc"] = glibc
        else:
            query = {"name": pack}
        is_optional = False
        to_skip = False
        if constrains is not None and type(constrains) is dict:
            if "optional" in constrains:
                is_optional = constrains["optional"]
            if "version" in constrains:
                query["version"] = constrains["version"]
            if "kind" in constrains:
                query["kind"] = constrains["kind"]
            for key in ["os", "arch", "abi"]:
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
                    if key == "abi" and abi not in restrained:
                        to_skip = True
        if to_skip:
            continue
        queries.append({"query": query, "optional": is_optional})

    log.debug("**Resolving packages...")
    found_queries = []
    for item in queries:
        query = item["query"]
        is_optional = item["optional"]
        remote_matches = pacman.query(query | {"transitive": True})
        if len(remote_matches) > 0:
            found_queries.append(query)
            log.debug(
                f"V Found {query['name']}/{query['version']} on {remote_matches[0].source}"
            )
            sub_dep = remote_matches[0].get_dependency_list()
            if len(sub_dep) > 0:
                for d in sub_dep:
                    sub_query = {
                        "name": d["name"],
                        "os": d["os"],
                        "arch": d["arch"],
                        "abi": d["abi"],
                        "kind": d["kind"],
                    }
                    if "version" in d:
                        sub_query["version"] = d["version"]
                    if glibc not in ["", None]:
                        sub_query["glibc"] = glibc
                    sub_matches = pacman.query(sub_query | {"transitive": True})
                    if len(sub_matches) == 0:
                        log.error(
                            f"  X Missing dependency {d['name']}/{d['version']} for package {query['name']}/{query['version']}"
                        )
                        log.error(f"{sub_query}")
                        err_code = 1
                    else:
                        log.debug(
                            f"  V Found dependency {d['name']}/{d['version']} for package {query['name']}/{query['version']}"
                        )
                        found_queries.append(sub_query)
            else:
                log.debug(
                    f"  No dependencies for package {query['name']}/{query['version']}"
                )
        else:
            if is_optional:
                log.debug(
                    f"⊘ Skipping optional package {query['name']}/{query['version']}"
                )
            else:
                log.error(
                    f"X Missing required package {query['name']}/{query['version']}"
                )
                log.error(f"{query}")
                err_code = 1
    if err_code != 0:
        return err_code, output

    # check found queries
    log.debug(f"**Checking {len(found_queries)} packages...")
    unique_queries = []
    for q in found_queries:
        name = q["name"]
        insert = True
        for q2 in unique_queries:
            if q2["name"] != q["name"]:
                continue
            if q2["version"] != q["version"]:
                log.error(
                    f"X Conflicting versions for package {name}: {q2['version']} vs. {q['version']}"
                )
                err_code = 1
                insert = False
                continue
            if q2["kind"] != q["kind"]:
                log.error(
                    f"X Conflicting kinds for package {name}: {q2['kind']} vs. {q['kind']}"
                )
                err_code = 1
                insert = False
                continue
        if insert:
            unique_queries.append(q)
    if err_code != 0:
        return err_code, output

    # get list of packages
    log.debug(f"**getting {len(unique_queries)} packages...")
    packages = []
    for q in unique_queries:
        log.info(f"getting package {q['name']}...")
        result = pacman.query(q | {"transitive": True})
        if len(result) == 0:
            log.error(f"X Could not find package {q['name']} after resolution.")
            err_code = 1
            continue
        if result[0].source != "local":
            log.debug(f"V Adding package {q['name']} from remote...")
            pacman.add_from_remote(result[0], result[0].source)
        result = pacman.query(q)
        if len(result) == 0:
            log.error(f"X Could not find package {q['name']} after addition.")
            err_code = 1
            continue
        packages.append(result[0])

    # create list of dir
    for package in packages:
        output += f"{package.get_cmake_config_dir()};"
    output = output.replace(";;", ";")
    output = output.rstrip(";")

    return err_code, output
