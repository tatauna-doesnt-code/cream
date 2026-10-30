# Contributing to CREAM

Discuss substantial behavior changes in an issue first. Keep pull requests focused
and describe the problem, resulting behavior and validation. New contributions are
accepted under GPL-3.0-only; submit only code and assets you have permission to share.

Run `python -m unittest discover -s tests -p 'test_*.py'` and
`python scripts/build_release.py` (Pillow is needed for development tests).
The scripts/check_* Qt integration checks additionally require Painter's SDK runtime.
Do not include real backer data, credentials, SPP projects or machine-specific paths.

CI tests pull requests with read-only permissions. Publishing is a separate workflow
on main. Changes to publishing, updater/bootstrap code or dependencies need careful
review. Report vulnerabilities privately as described in SECURITY.md.

## Iterate locally

No commit or push is needed to test a change. Edit your checkout, run Dev.cmd, then
use Settings → Check for updates → Apply and reopen CREAM. A same-version local
build is supported. Some edits require a Painter restart; the reload policy explains
which. See [docs/development.md](docs/development.md).
