# DepManager

[![PyPI](https://img.shields.io/pypi/v/depmanager)](https://pypi.org/project/depmanager)
[![Download](https://static.pepy.tech/badge/depmanager)](https://pepy.tech/project/depmanager)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Depmanager is a minimalistic tool to manage dependencies (also known as third-party
libraries) of a C++ Project. It works closely with cmake tool.

It allows to store dependencies in a distant repository to share builds with other and
have a local cache project-independent.

## Installation

Depmanager is written in python so in the following we assume you have a
working python installation designated as `<python>` with `pip` installed.

### pip

On systems that only rely on pip (in venv, for example)
To install dep manager simply use `<python> -m pip  install depmanager`

See the page on Pypi: [depmanager](https://pypi.org/project/depmanager/).

### From source

Prerequisite: python module 'build' install it with `<python> -m pip install build`

Clone the GitHub repository.

For a package installation, in the source root do:

```powershell
<python> -m build
<python> -m pip install dist/depmanager-x.y.z-py3-none-any.whl
```

For a non-packaged installation, in the source root do:

```bash
<python> -m pip install .
```

for a development installation, in the source root do (python files will be symlinked to source):

```bash
<python> -m pip install -e .
```

In this second case the actual source are directly used by your python installation or your venv.

### ubuntu

In ubuntu, it is not recommended to use pip for python modules because the system also comes with its bundled python
modules. DepManager is not bundled with the Ubuntu packages. To install DepManager, with limited impact on your system:

```bash
sudo apt install python3 python3-yaml python3-requests-toolbelt python3-cryptography python3-pip
sudo pip install depmanager --no-deps --break-system-packages
```

## Setup

The first time you run depmanager, it will create its local data folder in your home folder. You can override this
by setting the environment variable `DEPMANAGER_HOME` to the desired path.
The local data folder `.edm` contains :

* `config.ini` the configuration file (old config file)
* `config.yaml` The configuration file
* `data/` the local cache of packages
* `tmp/` the temporary folder for building packages

## Commandline use

### Get help

For any command or sub-command adding `--help` or `-h` to get help
on parameters or usage.

### Generalities

In the base command you can find:

| command | subcommands                | description                        |
|---------|----------------------------|------------------------------------|
| info    | basedir, cmakedir, version | info on local instance             |
| get     |                            | Get the config package             |
| pack    | pull, push, add, rm, ls    | Manage packages                    |
| remote  | list, ls, add, rm, info    | Manage the list of distant servers |
| build   |                            | Build a new package                |
| toolset | list, ls, add, rm          | Manage toolsets                    |

In the following, `<query>` designate something representing the dependency's description.
The syntax reads:  `--predicate(-p) <name>:<version> --type(-t)
<type> --os(-o) <os> --arch(-a) <arch> --abi(-c) <abi> --glibc <glibc>`

Valid values for `type`: `shared`, `static`, `header`.

Valid values for `os` : `Windows`, `Linux` (default: host os)

Valid values for `arch` : `x86_64`, `aarch64` (default: host arch)

Valid values for `abi` : `gnu`, `llvm` or `msvc` (default: `gnu`)
Note: clang compiler stands for `gnu` if using libstdc++ or `llvm` when using libc++ while clang-cl stands for `msvc`.

Valid values for `glibc` are only needed for linux. By giving, a value the system will look at
package with compatible version will be search (i.e. wit a version number lower or equal).
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

#### ls

`depmanager pack ls <query> [--transitive(-t)] <remote>` Simply do a search in the given remote (in local if
nothing given) and print the result.

The `--transitive(-t)` flag will allow to use transitive query, meaning to search for local then remote.

#### add, rm

`depmanager pack add <location>` Will add a package to the local database. `<location>` can be a
folder, then it must contain a properly formatted `edp.info` file. Or an archive (.zip, .tgz or .tar.gz
file format allowed). The uncompressed archive must contain a properly formatted `edp.info` file.

`depmanager pack rm <query> <remote> [-r]` Will remove from local cache all package matching the query.

The `-r` option allows operation on multiple packages (local only), else the command will return an error if multiple
package matches the query.

#### push, pull

`depmanager pack [push|pull] <query> <remote> [--force(-f)] [-r]` will synchronize Local cache with the remote.
The `query` must be precise enough to match one and only one package. `remote` must be valid.

`push` will look for the package in local cache that match the query and send it to the given remote.

`pull` will look for the package in given remote that match the query and bring it to the local cache.

If `--force` is given, The transfer occurs even if the package already exists in the destination.

The `-r` option allows operation on multiple packages. If multiple versions, only the highest one will be used.

#### clean

`depmanager pack clean [--full(-f)]` Will clean the local repository by removing old packages, only the newest
version of each package is kept.

The `[--full(-f)]` option will make the clean operation applies to all package, thus emptying the local database.

### remote

Manage the list of remote servers
subcommands:

* `list` or `ls` lists the defined remote server.
* `add` adds a new remote to the list.
    * `--name(-n) <name> --url(-u) <proto>://<url[:port]> [--default(-d)]`.
    * Mandatory. If name already exists it will modify the existing one.
    * Allowed proto are:
        * `ftp` supports login
        * `folder` a folder of your computer (mostly for debug or testing)
        * `srv` a dedicated server see [GitHub](https://github.com/Silmaen/DepManagerServer)
        * `srvs` a dedicated server with secure connexion see [GitHub](https://github.com/Silmaen/DepManagerServer)
    * Login can be defined with: `--login(-l) <login> --passwd(-p) <passwd>`.
* `rm <remote>` remove the designated remote if exists.
* `sync <remote> [--push-only|--pull-only] [--dry-run]` push to remote all local package that does not already
  exist on remote. Pull local package that have a newer version on the remote. If no remote given, it will use the
  default one.
* `info <remote>` gets information from the remote: type and version.

### toolset

Manage the toolset list.

* `list` or `ls` for listing the toolsets.
* `add` add a new toolset to the list
    * `--name(-n) <name> --compiler(-c) <compiler_path> [--abi(-b) <abi>`
* `rm --name(-n) <name>` remove a toolset

### build

`depmanager build [OPTIONS] <location>` will search for recipe in the given location and build them.

See the section [Create you own package](#create-your-own-package) for more details.

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
else ()
    execute_process(COMMAND ${EDEPMANAGER} info cmakedir
            OUTPUT_VARIABLE depmanager_path)
    string(STRIP ${depmanager_path} depmanager_path)
    list(PREPEND CMAKE_MODULE_PATH ${depmanager_path})
    include(DepManager)
endif ()
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
        [ABI target_abi]
        [GLIBC target_glibc]
) 
```

If `QUIET` set, only errors are written.

`path` is the path to the configuration file, either directly a configuration file name,
or a directory containing a file named `depmanager.yml`. By default, it will look at the
project root. See the next paragraph for more information about configuration file.

`kind` is used to force library kind (`shared`, `static`, `header`). By default, it uses
the value from `BUILD_SHARED_LIBS`.

`target_arch`, `target_os`, `target_abi`, `target_glibc` are used in the query. If not set, default
values are `CMAKE_SYSTEM_PROCESSOR`, `CMAKE_SYSTEM_NAME` and `CMAKE_CXX_COMPILER_ID`

The cmake function will update the CMAKE variable for the search of package.

After call this command, the cmake user has to call for needed `find_package`.

#### Configuration file

The configuration file is a YAML file. Here is an example with explication in comment.

```yaml
remote:
  # If server is defined, depmanager will add this server to its
  # database (if not already there)
  server:
    # Same parameter as command-line (also the required)
    name: "my_server"
    kind: "srvs"
    url: "https://packages.example.net"
    login: "foo"
    passwd: "bar"
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
    # use this only for the (same for arch, and abi)
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
        [ABI target_abi]
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

`target_arch`, `target_os`, `target_abi` `target_glibc` are used in the query. If not set, default
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
        [ABI target_abi]
        [GLIBC target_glibc]
)
```

After call this command, the cmake user has to call for needed `find_package`.

## Create your own package

Depmanager allow you to create your own packages by defining recipes. Then run
`depmanager build <location of recipes> [OPTIONS]`
The program will then build and add dependencies to the local cache.

The location can contain as many recipe in any number of files.

The search behavior can bve set as recursive with option `--recursive,-r`. As sometimes, sources also contains python
files that may fail to load, the depth of recursion can be restrained using `--recursive-depth <n>`.

By default, a package will not be build if already exists in the local cache. You can force the rebuild with the
option `--force,-f`.

By default, the builder will use all the cpu cores, but `--single-thred,-s` will force to use only one core.

Cross-compilation can be used by giving the tools at command
line: `--cross-c <C_COMPILER> --cross-cxx <CXX_COMPILER> --cross-arch <TARGET_ARCH> --cross-os <TARGET_OS>`

A defined toolset can be used by giving its name: `--toolset,-t <TOOLSET_NAME>`.

It is also possible to give a remote name `-n <remote_name>` or set to default remote `-d`. This way,
The builder will look into remote to see if a package already exists and pull it instead of building it.
Also, after a successful build, it will automatically push to the remote. Use either `--no-pull`and `--no-push`
option to skip these steps.

A `--dry-run` option will do all the checks and print the results but no pull, build and push action will be done.

### The recipe

During build, Depmanager will look in all `.py` file for class that inherits from
depmanager.api.recipe.Recipe.

As for dependency usage, build also rely on cmake for building.

The builder will use the provided recipe in the following workflow:

* Init recipe
* Call `recipe.source()`
* Check for dependencies
* Call `recipe.make_description()`
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

Note: if any step fails, the process stops and calls `recipe.clean()` before exiting.

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

As many python file may exist in the source you want to build, python file using shebang will be ignored to avoid errors
when parsing them. Do not add shebang in your recipe files.

#### Recipe attributes

A recipe can define the following attributes:

* `name` (str): the package name
* `version` (str): the package version
* `source_dir` (str): the folder where to find the sources (and CMakeLists.txt)
* `cache_variables` (dict): dictionary of cmake cache variables to set prior to configure
  example:
    ```python
    cache_variables = {
        'BUILD_SHARED_LIBS': 'ON',
        'BUILD_TESTS': 'OFF'
    }
    ```
* `config` (list of str): list of build configurations to build
  default:
    ```python
    config = ['Debug', 'Release']
    ```
* `kind` (str): the library kind: `shared`, `static`, `header`
* `public_dependencies` (list of dict): list of public dependencies with keys'
* `dependencies` (list of dict): list of dependencies with keys:
    * `name` (str): dependency name
    * `version` (str): dependency version requirement
    * `kind` (str): dependency kind requirement
    * `os` (str): dependency os requirement
    * `arch` (str): dependency architecture requirement
    * `abi` (str): dependency abi requirement
      example:
    ```python
    dependencies = [
        {'name': 'fmt', 'version': '>=10.0.0', 'kind': 'shared'},
        {'name': 'spdlog', 'version': '1.12.0'}
    ]
    ```
* `description` (str): description of the package in Markdown format
* `settings` (dict): dictionary of settings to store in the package
  default:
    ```python
    settings = {
        'os': '',
        'arch': '',
        'abi': '',
        'install_path': Path()
    }
    ```
    * `os` (str): target os: `Linux`, `Windows`
    * `arch` (str): target architecture: `x86_64`, `aarch64`
    * `abi` (str): target abi: `gnu`, `llvm`, `msvc`
    * `install_path` (Path): path to install the package (by default, depmanager will use its own layout)

#### Recipe methods

A recipe can override the following methods (by default, they do nothing):

* `source(self)`: method called to get the sources.

  by default, it does nothing, thus assuming the sources are already in place in `source_dir`.
  this method can de used to dynamically modify or download the sources prior to build.

* `make_description(self)`: method called to generate the description

  by default, description is only the given property string; but with this method, the property text can be filled
  dynamically.

* `configure(self)`: method called prior to cmake configure. By default, do nothing.

  In this method, the recipe can modify the cmake options by using `self.cache_variable` dictionary.

  example:
   ```python
   def configure(self):
       # force shared build
       self.cache_variable['BUILD_SHARED_LIBS'] = 'ON'
       # disable tests
       self.cache_variable['BUILD_TESTS'] = 'OFF'
   ```

* `install(self)`: method called after cmake install. By default, do nothing.

  This method can be used to move files around after installation.
  Tycally if the recipe has custom installation rules.

* `clean(self)`: method called at the end of the build process. By default,

  do nothing. This method can be used to clean temporary files created
  during the build process. this method is called even in case of failing build.

## Roadmap

The First in the roadmap is to use this tool in C++ project to get feedback.

Among things:

* version 1.0.x
    * [ ] Creation of a frontend application.
        * [ ] Can view, edit, suppress local package.
        * [ ] Can add, remove, explore remotes.
        * [ ] Can push, pull packages.
* version 0.6.x
    * [ ] Add recipe library
        * [ ] Possibility to store the recipes in remote
        * [ ] Auto build recipe if neither local nor remote found.
    * [ ] Add more cmake commands
        * [ ] Check for package updates
        * [ ] Manage Remotes
        * [ ] Manage Toolsets
* version 0.5.2 -- 2026-01-05
    * [X] Add more logs during cmake call
    * [X] Bugfixes
        * [X] Fix issue with some special characters in package description.
        * [X] Fix issue with some special characters in cmake cache variable.
    * [X] better packaging
* version 0.5.1 -- 2025-12-06
    * [X] Bugfixes
        * [X] Fix dm_load_package that was still using old compiler options.
        * [X] Fix creation of folder .edm in new installations.
        * [X] Fix untar extraction during pull
        * [X] Fix messaging of folders
* version 0.5.0 -- 2025-11-18
    * [X] Prettier output for commandline
    * [X] Add DEPMANAGER_HOME environment variable to override to classical search in HOME.
    * [X] Add concept of package dependencies
        * [X] Add dependency list in built packages.
            * [X] Construct dependency based on build.
            * [X] Use dependency list in query search
        * [X] Allow push/pull package with dependencies.
        * [X] Dependency checks during load.
        * [X] Recursive load of package.
    * [X] Management of package description in Markdown format.
        * [X] Allow to write description in recipe.
        * [X] Display description in commandline.
        * [X] Store description in package.
* version 0.4.2 -- 2025-10-26
    * [X] allow to introduce a missing CMakelists.txt file in recipe source step.
* version 0.4.1 -- 2025-07-01
    * [X] Bugfixes
        * [X] Fix toolset management command.
        * [X] Better Handling of llvm abi in recipe builder.
* version 0.4.0 -- 2025-06-16
    * [X] Add concept of toolset.
        * [X] Tool set defines arch, os and compilers; stored in config.ini; with a default one.
        * [X] Add concept of ABi for the compilers.
        * [X] Use toolset in build.
        * [X] Use toolset in queries.
    * [X] bugfixes
        * [X] Better local database reload
        * [X] Refactor builder in case of multiple build (pull, build, push)
    * [X] misc
        * [X] Add alias `rm` and `ls`
* version 0.3.4 -- 2024-05-08
    * [X] bugfix: deepcopy in push command (for multiple push)
    * [X] bugfix: quotes in Cmake invocation command
    * [X] Add more verbose output in cleaning command
* version 0.3.3 -- 2024-01-27
    * [X] Improved Builder Configurations management
    * [X] Operation on multiple package
        * [X] add a 'clean' command
            * [X] basic mode: keep only the newest packages
            * [X] full mode: delete everything.
        * [X] allow local deletion of multiple packages
        * [X] allow push/pull of multiple packages
* version 0.3.2 -- 2024-01-19
    * [X] Better management of push in auto-build
    * [X] Bugfixes in the use of CMake
    * [X] manage dependency in the list of Recipes
* version 0.3.1 -- 2024-01-16
    * [X] Allow to externally control the build system
        * [X] Allow to build a package by giving a single recipe
        * [X] Allow to pull packages prior to build if exists on a remote
        * [X] Allow to push (force) to remote after build
    * [X] Helper functions to find recipes in filesystem
        * [X] Allow recursive search
* version 0.3.0 -- 2024-01-12
    * [X] CMake integration improvement
        * [X] Simplify integration with cmake
        * [X] Python auto generate the Module dir for cmake
        * [X] Allow to load package by batch
            * [X] use YAML config file.
* version 0.2.1 -- 2023-12-31
    * [X] Bugfix: allow more date format and don't break if bad format.
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
