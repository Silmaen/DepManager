# Security Policy

## Supported versions

Only the latest minor release line receives security fixes. Older versions
are maintained on a best-effort basis.

| Version | Supported |
|---------|-----------|
| 0.5.x   | Yes       |
| < 0.5   | No        |

## Reporting a vulnerability

**Please do not open a public GitHub issue for security reports.**

Report privately by emailing the maintainer (<genteur.slayer@laposte.net>) with:

- A description of the vulnerability and its impact.
- Steps to reproduce, including the DepManager version and host OS.
- Any proof-of-concept or suggested fix, if available.

You should receive an acknowledgement within a few working days. Once the
issue is confirmed, we will coordinate a fix and a disclosure timeline with
you before publishing any advisory.

## Scope

DepManager handles credentials for remote package servers (FTP / HTTP). The
following categories are in scope for reports:

- Plaintext leakage of credentials (in logs, config files, temp files).
- Bypass of the encrypted credentials store (`PasswordManager`).
- Arbitrary code execution via malicious recipes or package metadata.
- Path traversal or overwrite attacks via remote-supplied archives.

Out of scope:

- Bugs that require local root access or an already-compromised host.
- Issues in the CMake user code that *uses* DepManager output.
- Denial of service against a remote you explicitly configured.
