---
name: Bug report
about: Report a crash or incorrect behaviour in DepManager
title: "[Bug] "
labels: bug
assignees: ''
---

## Describe the bug

A clear and concise description of what the bug is.

## Reproduction

Exact commands and, if possible, a minimal project layout or `depmanager.yml`
that triggers it:

```bash
# e.g.
depmanager pack pull libfoo/1.2 -n my_remote
```

## Expected behaviour

What you expected to happen.

## Actual behaviour

What actually happened. Include the full traceback or the last meaningful
log lines.

```
(paste output here)
```

## Environment

- DepManager version: `depmanager info version`
- Install method: pip / poetry / apt / from source
- Python version: `python --version`
- OS and architecture: e.g. Ubuntu 24.04 x86_64 / Windows 11 x86_64 / arm64 container
- Remote type (if relevant): folder / ftp / srv / srvs

## Additional context

Anything else that might matter: recent config changes, an arch/container
mismatch, whether a fresh install reproduces it, etc.
