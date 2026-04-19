# DepManager — Developer Documentation

Documentation for people working *on* DepManager. End-user documentation lives
in the top-level [`README.md`](../README.md); this folder covers the internals
contributors need.

## Table of Contents

- [Architecture](architecture.md) — layer structure, class relationships, and
  the lifecycles that back the CLI (`pack pull`, `build`, CMake integration).
- [Contributing](contributing.md) — local setup, running tests, coding
  conventions, release checklist.
- [Recipe authoring](recipe-authoring.md) — writing a build recipe for the
  `depmanager build` command.
- [Extending remotes](extending-remotes.md) — implementing a new remote
  backend (alongside the built-in FTP / Folder / HTTP server variants).

## Diagrams

All diagrams use [Mermaid](https://mermaid.js.org/); GitHub renders them
natively. If you add a diagram, use a fenced ```mermaid block rather than an
image — this keeps the diagram editable in-tree.
