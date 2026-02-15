# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DepManager is a Python dependency manager for C++ projects that integrates with CMake. It manages pre-built C++ packages through local caches and remote repositories (FTP, folder, HTTP/HTTPS servers), and can build packages from Python recipe definitions.

CLI entry points: `depmanager` and `dmgr` (alias), both invoke `depmanager:main`.

## Build & Install

```bash
# Development install (editable)
pip install -e .

# Build distributable package
python -m build
```

Build system: setuptools via `pyproject.toml`. Python >= 3.9 required.

## Testing

No test infrastructure exists yet. The `test/` directory is empty.

## Code Style

- Black formatter, 88 char line limit
- PEP 8, snake_case variables, PascalCase classes
- reST docstrings
- Type hints preferred for all functions

## Project Conventions

- Use `pathlib.Path` instead of `os.path`
- Use `depmanager.api.internal.messaging.log` for logging (`log.debug()`, `log.info()`, `log.warn()`, `log.error()`, `log.fatal()`)
- Use `rich` for progress bars (SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn)
- Use `PasswordManager` for credential storage; never store plaintext credentials
- Return `False` or `None` on failure; only raise exceptions for critical errors
- Strict file permissions (0o600) for sensitive files

## Architecture

### Layer Structure

```
command/     CLI handlers (argparse dispatch via manager.py)
   ↓
api/         Public API (Builder, PackageManager, RemotesManager, ToolsetsManager, LocalManager)
   ↓
api/internal/  Core implementation
```

`manager.py` registers subcommands via `add_*_parameters()` functions from each `command/` module. Each command handler receives parsed args and a `LocalManager` instance.

### Key Internal Components

- **`LocalSystem`** (`api/internal/system.py`): Central singleton managing config (`~/.edm/config.yaml`), local database, remote databases, toolsets, file locking, and password encryption. All other components access system state through this.

- **Database hierarchy**: Abstract `__DataBase` → `LocalDatabase` (filesystem), `RemoteDatabaseFolder`, `RemoteDatabaseFtp`, `RemoteDatabaseServer`. All implement query/push/pull via `Props` matching.

- **`Props` / `Dependency`** (`api/internal/dependency.py`): Package metadata (name, version, os, arch, abi, glibc, build_date). `Props` handles matching with fnmatch wildcards and version comparison.

- **`Machine`** (`api/internal/machine.py`): Platform introspection — detects OS, architecture, ABI (gnu/llvm/msvc), glibc version.

- **Recipe system**: `Recipe` base class (`api/recipe.py`) → discovered by `find_recipes()` → built by `RecipeBuilder` (`api/internal/recipe_builder.py`) → orchestrated by `Builder` (`api/builder.py`). Lifecycle: source → configure → cmake build → install → clean.

- **`ConfigFile`** (`api/internal/config_file.py`): Handles YAML project config files (`depmanager.yml`) for automated CMake loading.

### CMake Integration

`cmake/DepManager.cmake` provides `dm_find_package()`, `dm_load_package()`, and `dm_load_environment()`. These call the `depmanager` CLI to resolve packages and set up CMake paths.

### Data Storage

All data lives under `~/.edm/` (overridable via `DEPMANAGER_HOME` env var):
- `config.yaml` — remotes, toolsets, paths
- `data/` — local package cache
- `tmp/` — build temporaries

Package metadata format: `edp.info` (YAML) inside each package directory or archive.

### Import Style

Internal modules use relative imports without the package prefix (e.g., `from api.internal.system import LocalSystem` rather than `from depmanager.api.internal.system import LocalSystem`). The `api/internal/` modules use full qualified imports (`from depmanager.api.internal.messaging import log`).
