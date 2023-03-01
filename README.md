# DepManager

Dependency manager.

## Base command

In the base commande you can find:

| command | subcommands                 | description                        |
|---------|-----------------------------|------------------------------------|
| info    | basedir, cmakedir, version  | info on local instance             |
| get     |                             | Get the config package             |
| pack    | pull, push, add, del, query | Manage packages                    |
| remote  | list, add, del              | Manage the list of distant servers |
| server  | start                       | Manage the repository server       |

### info

subcommands:
 * `version` gives the version of the local manager.
 * `basedir` gives the path to the local data of the manager
 * `cmakedir` gives the path to add to `CMAKE_MODULE_PATH` before include `ExternalDependencyManager`

### get

Get the path to cmake config of the 'best' package given the query information.

Query are written in the format: `--predicate(-p) <name>:<version> --type(-t)
 <type> --os(-o) <os> --arch(-a) <arch> --compiler(-c) <compiler>`

Valid values for `type`: `shared`, `static`, `header`.

Valid values for `os` : `Windows`, `Linux` (default: host os)

Valid values for `arch` : `x86_64`, `aarch64` (default: host arch)

Valid values for `comiler` : `gnu`, `msvc` (default: `gnu`)
Note: clang compiler stands for `gnu` while clang-cl stands for `msvc`. 


### pack

### remote

Manage the list of remote servers
subcommands:
 * `list` lists the defined remote server.
 * `add` adds a new remote to the list
   * `--name(-n) <name> --url(-u) <url[:port]> [--default(-d)]`
 * `del` remove the remote named `name` from the list if exists
   * `--name(-n) <name>`

### server

subcommands:
 * `start`  starts the server and listen to connexion