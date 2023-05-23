# DepManager

Depmanager is a minimalistic tool to manage dependencies (also known as third-party 
libraries) of a C++ Project. It works closely with cmake tool.

It allow to store dependencies in a distant repository to share builds with other and
have a local cache project-independent.

## Installation

Depmanager is written in python so in the following we assume you have a 
working python installation designated as `<python>` with `pip` installed.

### pip

To install dep manager simply use `<python> -m pip  install depmanager`

### From source

Prerequisite: python module 'build' install it with `<python> -m pip install build`

Clone the github repository.

In the source root do:
```powershell
<python> -m build
<python> -m pip install dist/depmanager-x.y.z-py3-none-any.whl
```

## Commandline use

### Get help

For any command or sub-command adding `--help` or `-h` to get help 
on parameters or usage.

### Generalities

In the base commande you can find:

| command | subcommands                 | description                        |
|---------|-----------------------------|------------------------------------|
| info    | basedir, cmakedir, version  | info on local instance             |
| get     |                             | Get the config package             |
| pack    | pull, push, add, del, query | Manage packages                    |
| remote  | list, add, del              | Manage the list of distant servers |
| build   |                             | Build a new package                |

In the following we will desigate `<query>` as something representing the description
of a dependency. The syntax reads:  `--predicate(-p) <name>:<version> --type(-t)
 <type> --os(-o) <os> --arch(-a) <arch> --compiler(-c) <compiler>`

Valid values for `type`: `shared`, `static`, `header`.

Valid values for `os` : `Windows`, `Linux` (default: host os)

Valid values for `arch` : `x86_64`, `aarch64` (default: host arch)

Valid values for `comiler` : `gnu`, `msvc` (default: `gnu`)
Note: clang compiler stands for `gnu` while clang-cl stands for `msvc`.

Also, we will designate `<remote>` as a description a remote server, syntax reads: `[-n <name>|-d]`.
If nothing given, we assume 'local'. If `-d` given, use the default remote, else use the remote by
its name.

If the name does not exist, it will fall back to default then to local.

## Base commands

### info

subcommands:
 * `version` gives the version of the local manager.
 * `basedir` gives the path to the local data of the manager
 * `cmakedir` gives the path to add to `CMAKE_MODULE_PATH` before include `ExternalDependencyManager`

### get

`depmanager get <query>`

Get path to cmake config of the 'best' package given the query information.

The command will only search in the local cache. This does not intent for human use but more for
cmake integration.

### pack

Actions on packages.

#### query

`depmanager pack query <query> <remote>` Simply do a search in the given remote (in local if 
nothing given) and print the result.

#### add, del

`depmanager pack add <location>` Will add a package to the local database. `<location>` can be a
folder, then it must contain a properly formatted `edp.info` file. Or an archive (.zip, .tgz or .tar.gz
file format allowed). The uncompressed archive must contain a properly formatted `edp.info` file.

`depmanager pack del <query>` Will remove from local cache all package matching the query

#### push, pull

`depmanager pack [push|pull] <query> <remote> [--force(-f)]` will synchronize Local cache with the remote.
The `query` must be precise enough to match one and only one package. `remote` must be valid.

`push` will look for the package in local cache that match the query and send it to the given remote.

`pull` will look for the package in given remote that match the query and bring it to the local cache.

If `--force` is given, The transfert occurs even if the package already exists in the destination.

### remote

Manage the list of remote servers
subcommands:
 * `list` lists the defined remote server.
 * `add` adds a new remote to the list.
   * `--name(-n) <name> --url(-u) <proto>://<url[:port]> [--default(-d)]`.
   * Name is mandatory. if the name already exist it will modify the existing one.
   * Allowed proto are:
     * `ftp` supports login
     * `folder` a folder of your computer (mostly for debug or testing)
     * `srv` a dedicated server see [github](https://github.com/Silmaen/DepManagerServer)
     * `srvs` a dedicated server with secure connexion see [github](https://github.com/Silmaen/DepManagerServer)
   * Login can be defined with: `--login(-l) <login> --passwd(-p) <passwd>`.
 * `del <remote>` remove the designated remote if exists.
 * `sync <remote>` push to remote all local package that does not already exist on remote.

### build

`depmanager build <location>` will search for recipe in the given location and build them.

## Using package with cmake

### Include depmanager to cmake

To initialize depmanager into cmake you need to add to `CMAKE_MODULE_PATH` the path
to the cmake folder of this installation.

Here is a small cmake code snippet to initialize depmanager in cmake.

```cmake
# add HINTS or PATH to find the executable if not in the PATH
find_program(EDEPMANAGER depmanager) 
if (${EDEPMANAGER} STREQUAL EDEPMANAGER-NOTFOUND)
    message(FATAL_ERROR "Dependency manager not found.")
else()
    execute_process(COMMAND ${EDEPMANAGER} info cmakedir
            OUTPUT_VARIABLE depmanager_path)
    string(STRIP ${depmanager_path} depmanager_path)
    list(PREPEND CMAKE_MODULE_PATH ${depmanager_path})
    include(DepManager)
endif()
```

### Find packages

With depmanager initialized in cmake, it provide an alternative to classical `find_package`
of cmake by `dm_find_package`

```cmake
dm_find_package(
   package
   [QUIET] [TRACE] [REQUIRED]
   [VERSION version]
   [KIND kind]
   [ARCH target_arch]
   [OS target_os]
   [COMPILER target_compiler]
)
```
`package` is the package name to find.

`version` is the exact version to match (wildcard are allowed). By default, find the
latest one.

`kind` is used to force library kind (`shared`, `static`, `header`). By default it return
the first found.

If `REQUIRED` set, the function will give an error if no package found. 
(same as original `find_package`)

If `QUIET` set, only errors are written. (same as original `find_package`). In opposition,
if `TRACE` set, many more debug message displayed.

`target_arch`, `target_os`, `target_compiler` are used in the query. If not set, default
values are `CMAKE_SYSTEM_PROCESSOR`, `CMAKE_SYSTEM_NAME` and `CMAKE_CXX_COMPILER_ID`

**LIMITATION:** it require the library name is the package name. So no multi lib or lib with different name.

### Load package

This command is similar to the previous one, but does not directly do a cmake's `find_package`. 
It only adds to the `CMAKE_PREFIX_PATH` list the folders of given package.

```cmake
dm_load_package(
   package
   [QUIET] [TRACE]
   [VERSION version]
   [KIND kind]
   [ARCH target_arch]
   [OS target_os]
   [COMPILER target_compiler]
)
```

After call this command, the cmake user has to call for needed `find_package`.

## Create you own package

Depmanager allow you to create your own packages by defining recipes. Then run 
`depmanager build <location of recipes>`
The program will then build and add dependencies to the local cache.

The location can contain as many recipe in any number of files.

### The recipe

During build, Depmanager will look in all `.py` file for class that inherits from
depmanager.api.recipe.Recipe.

As for dependency usage, build also rely on cmake for building.

The builder will use the provided recipe in the following workflow:

 * Init recipe
 * Call `recipe.source()`
 * Call `recipe.configure()`
 * Initialize options based on recipe data
 * Run cmake configure
 * For all configuration (mostly 'Debug', 'Release')
   * build target `install`
 * Call `recipe.install()`
 * Generate edp.info file
 * Import into local cache
 * Clean Temporary

Here is a small example

```python
"""
Small recipe example
"""
from depmanager.api.recipe import Recipe

class MyAwesomeLib(Recipe):
    """
    Awesome lib
    """
    name = "awesome_lib"  # lib name
    version = "0.0.1.foo" # lib version
    source_dir = "src"    # where to fine the sources (especially) the CmakeList.txt
    kind = "static"       # the lib's kind

class AnotherAwesomeLib(MyAwesomeLib):
    """
    Shared version of previous one
    """
    kind = "shared"
```

## Roadmap

First of all in the roadmap is to use this tool in C++ project to get feedback.

Among things:

* version 0.2.0
  * [ ] Do query across multiple source (local then remote)
  * [ ] Add a sorting order for remotes
  * [ ] Auto-pull if not in local
    * [ ] Auto build recipe if neither local or remote found
* version 0.1.2
  * [X] Add possibility to force os, arch and compiler for cross compiling
  * [X] Adapt build system to search dependency in the forced environment.
* version 0.1.1
  * [X] Add remote Type of 'srv': a dedicated dependency server
  * [X] Add remote Type of 'srvs': a dedicated dependency server with secure connexion
