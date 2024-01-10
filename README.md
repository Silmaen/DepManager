# DepManager

[![PyPI](https://img.shields.io/pypi/v/depmanager)](https://pypi.org/project/depmanager)
[![Download](https://static.pepy.tech/badge/depmanager)](https://pepy.tech/project/depmanager)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Depmanager is a minimalistic tool to manage dependencies (also known as third-party
libraries) of a C++ Project. It works closely with cmake tool.

It allow to store dependencies in a distant repository to share builds with other and
have a local cache project-independent.

## Installation

Depmanager is written in python so in the following we assume you have a
working python installation designated as `<python>` with `pip` installed.

### pip

To install dep manager simply use `<python> -m pip  install depmanager`

See the page on Pypi: [depmanager](https://pypi.org/project/depmanager/).

### From source

Prerequisite: python module 'build' install it with `<python> -m pip install build`

Clone the gitHub repository.

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
| remote  | list, add, del, info        | Manage the list of distant servers |
| build   |                             | Build a new package                |

In the following, `<query>` designate something representing the dependency's description.
The syntax reads:  `--predicate(-p) <name>:<version> --type(-t)
<type> --os(-o) <os> --arch(-a) <arch> --compiler(-c) <compiler> --glibc <glibc>`

Valid values for `type`: `shared`, `static`, `header`.

Valid values for `os` : `Windows`, `Linux` (default: host os)

Valid values for `arch` : `x86_64`, `aarch64` (default: host arch)

Valid values for `compiler` : `gnu`, `msvc` (default: `gnu`)
Note: clang compiler stands for `gnu` while clang-cl stands for `msvc`.

Valid values for `glibc` are only needed for linux. By giving, a value the system will look at
package with compatible version will be search (ie. wit a version number lower or equal).
It is still possible to do an exact search by using `=` as first character. (like `--glibc =2.36`)

Also, we will designate `<remote>` as a description a remote server, syntax reads: `[-n <name>|-d]`.
If nothing given, we assume 'local'. If `-d` given, use the default remote, else use the remote by
its name.

If the name does not exist, it will fall back to default then to local.

## Base commands

### info

Subcommands:

* `version` gives the version of the local manager.
* `basedir` gives the path to the local data of the manager
* `cmakedir` gives the path to add to `CMAKE_MODULE_PATH` before include `ExternalDependencyManager`

### get

`depmanager get <query>`

Get path to cmake config of the 'best' package given by the query information.

The command will first search in the local cache, if not found it will search in the default remote. This does not
intent for human use but more for
cmake integration.

### pack

Actions on packages.

#### query

`depmanager pack query <query> [--transitive(-t)] <remote>` Simply do a search in the given remote (in local if
nothing given) and print the result.

The `--transitive(-t)` flag will allow to use transitive query, meaning to search for local then remote.

#### add, del

`depmanager pack add <location>` Will add a package to the local database. `<location>` can be a
folder, then it must contain a properly formatted `edp.info` file. Or an archive (.zip, .tgz or .tar.gz
file format allowed). The uncompressed archive must contain a properly formatted `edp.info` file.

`depmanager pack del <query>` Will remove from local cache all package matching the query.

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
    * Mandatory. If name already exists it will modify the existing one.
    * Allowed proto are:
        * `ftp` supports login
        * `folder` a folder of your computer (mostly for debug or testing)
        * `srv` a dedicated server see [gitHub](https://github.com/Silmaen/DepManagerServer)
        * `srvs` a dedicated server with secure connexion see [gitHub](https://github.com/Silmaen/DepManagerServer)
    * Login can be defined with: `--login(-l) <login> --passwd(-p) <passwd>`.
* `del <remote>` remove the designated remote if exists.
* `sync <remote> [--push-only|--pull-only] [--dry-run]` push to remote all local package that does not already
  exist on remote. Pull local package that have a newer version on the remote. If no remote given, it will use the
  default one.
* `info <remote>` gets information from the remote: type and version.

### build

`depmanager build [OPTIONS] <location>` will search for recipe in the given location and build them.

Some option can be passed to the build system:

* `--single-thread`: on some low-end devices (such as RaspberryPi) single thread build is recommended.
* `--force`, `-f`: Force the build even if the dependency already exists
* `--cross-c`: redefine the C compiler
* `--cross-cxx`: redefine the C++ compiler
* `--cross-arch`: redefine the architecture
* `--cross-os`: redefine the OS

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

### Automated mode

In automated mode, depmanager can automatically set a remote repository, retrieve packages from this repository
and load then in one command.

#### The command

```cmake
dm_load_environment(
   [QUIET]
   [PATH path]
   [KIND kind]
   [ARCH target_arch]
   [OS target_os]
   [COMPILER target_compiler]
   [GLIBC target_glibc]
) 
```

If `QUIET` set, only errors are written.

`path` is the path to the configuration file, either directly a configuration file name,
or a directory containing a file named `depmanager.yml`. By default, it will look at the
project root. See the next paragraph for more information about configuration file.

`kind` is used to force library kind (`shared`, `static`, `header`). By default, it uses
the value from `BUILD_SHARED_LIBS`.

`target_arch`, `target_os`, `target_compiler`, `target_glibc` are used in the query. If not set, default
values are `CMAKE_SYSTEM_PROCESSOR`, `CMAKE_SYSTEM_NAME` and `CMAKE_CXX_COMPILER_ID`

The cmake function will update the CMAKE variable for the search of package.

After call this command, the cmake user has to call for needed `find_package`.

#### Configuration file

The configuration file is a yaml file. Here is an example with explication in comment.

```yaml
remote:
  # If server is defined, depmanager will add this server to its
  # database (if not already there)
  server:
    # Same parameter as command-line (also the required)
    name: "my_server"
    kind: "srvs"
    url: "https://packages.argawaen.net"
    login: "argawaen"
    passwd: "ElorAloric1024*"
  # If package not found locally, do you allow for download?
  pull: true
  # If newer remote package exists, download it? (implies 'pull')
  pull-newer: true
packages:
  # list the needed packages.
  fmt:
    # version 'at least'
    version: ">=10.1.0"
  spdlog:
    # exact version
    version: "1.12.0"
  debugbreak:
    # if not found locally, don't pull, nor error.
    optional: true
  glm:
    version: "0.9.9.9"
    # force the shared version even in static build mode.
    kind: "shared"
  glfw:
    # use this only for the (same for arch, and compiler)
    os: Linux
```

### Manual mode

In manual mode you should load or find each package individually.
You should also manually set the remote and download the package.

#### Find packages

With depmanager initialized in cmake, it provides an alternative to classical `find_package`
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
   [GLIBC target_glibc]
)
```

`package` is the package name to find.

`version` is the exact version to match (wildcard are allowed). By default, find the
latest one.

`kind` is used to force library kind (`shared`, `static`, `header`). By default, it returns
the first found.

If `REQUIRED` set, the function will give an error if no package found.
(same as original `find_package`)

If `QUIET` set, only errors are written. (same as original `find_package`). In opposition,
if `TRACE` set, many more debug message displayed.

`target_arch`, `target_os`, `target_compiler` `target_glibc` are used in the query. If not set, default
values are `CMAKE_SYSTEM_PROCESSOR`, `CMAKE_SYSTEM_NAME` and `CMAKE_CXX_COMPILER_ID`

**LIMITATION:** it requires the library name is the package name. So no multi lib or lib with different name.

#### Load package

This command is similar to the previous one, but does not directly do a cmake's `find_package`.
It only adds to the `CMAKE_PREFIX_PATH` list the folders of given package.

```cmake
dm_load_package(
   package
   [REQUIRED] [TRACE]
   [VERSION version]
   [KIND kind]
   [ARCH target_arch]
   [OS target_os]
   [COMPILER target_compiler]
   [GLIBC target_glibc]
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
* Call `recipe.clean()`
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
    version = "0.0.1.foo"  # lib version
    source_dir = "src"  # where to fine the sources (especially) the CmakeList.txt
    kind = "static"  # the lib's kind


class AnotherAwesomeLib(MyAwesomeLib):
    """
    Shared version of previous one
    """
    kind = "shared"
```

## Roadmap

First of all in the roadmap is to use this tool in C++ project to get feedback.

Among things:

* version 0.7.x
    * [ ] Creation of a frontend application.
        * [ ] Can view, edit, suppress local package.
        * [ ] Can add, remove, explore remotes.
        * [ ] Can push, pull packages.
* version 0.6.x
    * [ ] Add recipe libray
        * [ ] Possibility to store the recipes in remote
        * [ ] Auto build recipe if neither local nor remote found.
* version 0.5.x
    * [ ] Add a sorting order for remotes.
        * [ ] Searching across remotes with final package sorting.
        * [ ] Allow auto-pull best-fitting package
* version 0.4.x
    * [ ] Add concept of toolset.
        * [ ] Tool set defines arch, os and compilers; stored in config.ini; with a default one.
        * [ ] Use toolset in build.
        * [ ] Use toolset in queries.
* version 0.3.x
    * [X] CMake integration improvement
        * [X] Simplify integration with cmake
        * [X] Python auto generate the Module dir for cmake
        * [X] Allow to load package by batch
            * [X] use Yaml config file.
* version 0.2.1 -- 2023-12-31
    * [X] Bufix: allow more date format and don't break if bad format.
* version 0.2.0 -- 2023-12-12
    * WARNING: Some breaking change. Backward compatibility not fully tested.
    * [X] Faster commandline
        * [X] Use remote connexion only if needed
    * [X] Transitive search
        * [X] Query: search in local then remote.
        * [X] get: Auto-pull if not in local.
    * [X] Add new remote command.
        * [X] Get info from remote (type and version)
        * [X] Allow to delete package on remote.
    * [X] Better Package properties
        * [X] Add build Date in package properties.
        * [X] Add build glibc version in package properties if applicable.
        * [X] Better queries on glibc compatible system
        * [X] Use system's glibc in get searches
* version 0.1.4 -- 2023-06-21
    * [X] Allow to sync with remote.
        * [X] Allow to pull local package that have newer version.
        * [X] Allow to push local package newer than remote or not existing in remote.
    * [X] Allow to force push/pull.
    * [X] Bugfix: safe delete
* version 0.1.3 -- 2023-06-12
    * [X] Update internal statuses when using API.
    * [X] omit -d in push/pull command.
    * [X] add progress bar in push/pull command.
    * [X] Allow single thread in build.
* version 0.1.2 -- 2023-05-31
    * [X] Add possibility to force os, arch and compiler for cross compiling.
    * [X] Adapt build system to search dependency in the forced environment.
* version 0.1.1
    * [X] Add remote 'srv' Type: a dedicated dependency server.
    * [X] Add remote 'srvs' Type: a dedicated dependency server with secure connexion.
