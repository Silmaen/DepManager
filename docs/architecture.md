# Architecture

This document describes DepManager's internal structure. For an end-user
overview, see the top-level [`README.md`](../README.md).

## Layered structure

DepManager is organised in three layers. Callers only ever reach down by one
level: `command/` uses `api/`, and `api/` uses `api/internal/`. Nothing in
`api/internal/` should reach back up.

```mermaid
flowchart TB
    CLI["`**CLI**
    depmanager / dmgr entry points
    manager.py`"]
    CMD["`**command/**
    argparse handlers
    build / get / info / load / pack / remote / toolset`"]
    API["`**api/**
    public API
    Builder · PackageManager · RemotesManager · ToolsetsManager · LocalManager`"]
    INT["`**api/internal/**
    core implementation
    LocalSystem · databases · Dependency · Machine · recipes · crypto`"]
    DISK[("~/.edm/
    config.yaml · data/ · tmp/")]
    REMOTES[(remote backends
    FTP · Folder · HTTP server)]

    CLI --> CMD --> API --> INT
    INT --> DISK
    INT --> REMOTES
```

`manager.py` composes the CLI by registering each subcommand's
`add_*_parameters()` function, then dispatches to the matching handler with a
parsed `argparse.Namespace` and a ready `LocalManager`.

## Core collaborators

```mermaid
classDiagram
    class LocalSystem {
        config.yaml
        local_database
        remote_database: dict
        toolsets
        temp_path
        password_manager
    }
    class LocalDatabase {
        base_path: Path
        dependencies: list~Dependency~
        query(props)
        reload()
        delete(query)
        pack(query, dest)
    }
    class RemoteDatabase {
        <<abstract>>
        destination
        query(props)
        push(dep, file)
        pull(dep, dest)
        connect()*
        get_file()*
        send_file()*
    }
    class RemoteDatabaseFolder
    class RemoteDatabaseFtp
    class RemoteDatabaseServer
    class Dependency {
        properties: Props
        base_path
        source
        match(other)
        has_dependency()
        get_dependency_list()
    }
    class Props {
        name · version
        os · arch · kind · abi · glibc
        build_date
        dependencies: list~dict~
        match(other)
        hash()
    }
    class Machine {
        os · arch · default_abi · glibc
        __introspection()
    }
    class PackageManager {
        query(q, remote)
        add_from_location(path)
        add_from_remote(dep, remote)
        add_to_remote(dep, remote)
    }
    class Builder {
        recipes
        build()
    }
    class Recipe {
        <<abstract>>
        name · version · kind
        source()*
        configure()*
        install()*
        clean()*
    }

    LocalSystem "1" o-- "1" LocalDatabase
    LocalSystem "1" o-- "*" RemoteDatabase
    LocalSystem "1" o-- "1" Machine
    RemoteDatabase <|-- RemoteDatabaseFolder
    RemoteDatabase <|-- RemoteDatabaseFtp
    RemoteDatabase <|-- RemoteDatabaseServer
    LocalDatabase --> Dependency
    Dependency --> Props
    PackageManager ..> LocalSystem
    Builder --> Recipe
```

### Responsibilities

- **`LocalSystem`** (`api/internal/system.py`) is the session-scoped singleton.
  Everything — databases, toolsets, temp paths, credentials — is reached
  through it. This is also where file locking for concurrent `depmanager`
  invocations lives.
- **Databases** (`api/internal/database_*`) share the `__DataBase` matching
  contract. `query` accepts a dict, string, `Props`, or `Dependency` and
  returns a list of `Dependency`. Remote variants add `push`/`pull` over the
  transport they implement (FTP, filesystem copy, HTTP).
- **`Props`** is the matching primitive. Wildcards use `fnmatch`; version
  comparison is numeric-aware (`1.10` > `1.2`) via `safe_to_int`; glibc has
  three matching modes (`=X.Y` exact, `X.Y` "this host can run X.Y-built
  packages", `any`/`*`/empty wildcard).
- **`Dependency`** wraps `Props` with filesystem awareness (base path,
  `cmake_config_path` discovered by globbing `*onfig.cmake`).
- **`Machine`** introspects `platform.*` once on first use. Unknown OS or arch
  calls `exit(666)` — see [contributing](contributing.md) if you're adding a
  platform.

## Package metadata format

Each package on disk lives in a directory under `~/.edm/data/` containing:

- `info.yaml` — `Props` serialised as YAML. This is the authoritative metadata
  file since the move from the legacy `edp.info` format (still read on load
  and upgraded on first access).
- `description.md` *(optional)* — free-form package description.
- The actual CMake-installed tree (include/, lib/, share/cmake/…).

Archives (`.tgz` / `.zip`) used for transport mirror this layout.

## Sequence: `depmanager pack pull`

```mermaid
sequenceDiagram
    actor User
    participant CLI as manager.py
    participant PM as PackageManager
    participant Sys as LocalSystem
    participant Remote as RemoteDatabase
    participant Local as LocalDatabase

    User->>CLI: depmanager pack pull libfoo/1.2 -n srv
    CLI->>PM: add_from_remote(dep, "srv")
    PM->>Sys: remote_database["srv"]
    PM->>Remote: query(dep)
    Remote-->>PM: [matched Dependency]
    PM->>Remote: pull(dep, tmp)
    Remote-->>PM: archive filename
    PM->>PM: add_from_location(archive)
    PM->>Local: extract & register
    alt package has transitive deps
        loop for each sub_dep (dict)
            PM->>Local: query(sub_dep)
            alt sub_dep missing locally
                PM->>Remote: query(sub_dep)
                Remote-->>PM: [sub Dependency]
                PM->>PM: add_from_remote(sub, srv)
            end
        end
    end
```

The transitive loop resolves dicts coming out of
`Dependency.get_dependency_list()` to full `Dependency` objects via
`remote.query()` **before** recursing — passing the raw dict would crash the
recursive call on `dep.properties.hash()`.

## Sequence: `depmanager build`

```mermaid
sequenceDiagram
    actor User
    participant CLI as manager.py
    participant B as Builder
    participant R as Recipe
    participant RB as RecipeBuilder
    participant PM as PackageManager

    User->>CLI: depmanager build path/to/recipes
    CLI->>B: build(path)
    B->>B: find_recipes(path)
    loop topological order
        B->>R: source()
        B->>RB: configure()
        RB->>RB: cmake configure
        RB->>RB: cmake build
        B->>R: install()
        B->>PM: add_from_location(install_dir)
        B->>R: clean()
    end
```

## Configuration file (`depmanager.yml`)

`ConfigFile` parses project-level YAML used by the CMake integration. The two
recognised top-level keys are `remote` (server info + pull policy) and
`packages` (what the project wants loaded). See the end-user README for field
definitions.

## Data on disk

```mermaid
flowchart LR
    subgraph HOME["~/.edm/ or $DEPMANAGER_HOME"]
        CFG["config.yaml"]
        DATA["data/"]
        TMP["tmp/"]
    end
    subgraph DATA
        PKG1["libfoo-1.2/
        info.yaml
        description.md
        include/, lib/, share/cmake/..."]
        PKG2["libbar-2.0/
        info.yaml
        ..."]
    end

    TMP -. "archives during push/pull
    recipe build trees" .-> DATA
```

`DEPMANAGER_HOME` overrides `~/.edm/` — used by the test suite
(`tmp_edm_home` fixture) to keep tests isolated.
