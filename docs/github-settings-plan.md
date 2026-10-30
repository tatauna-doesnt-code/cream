# Repository administration plan

These are **desired settings**, not a claim that they have been applied.
The connected GitHub tools can edit source/PRs, but do not expose administration
mutations. The current private repository also returns a plan restriction for rulesets.
No visibility change is performed by this plan or its helper script.

## Main branch

Create an active branch ruleset targeting `refs/heads/main`:

- Require a pull request, with **zero mandatory approvals** while the project has
  a single maintainer. Require resolved review conversations.
- Require the GitHub Actions **Test and package** check, and an up-to-date branch.
- Block branch deletion and force pushes. No broad bypass actors.
- Do not enable a merge queue or require another person's approval.

The ruleset can be enabled on GitHub Free once the repository is public. Keep it
private until history cleanup is decided; alternatively upgrade the plan first.
After protection is active, source changes must be published through PRs.

## Actions

- Default token permissions: read-only contents/packages.
- Disable Actions approving pull requests.
- Allow GitHub-owned actions only (all current workflows use those).
- Require approval for workflow runs from all outside contributors.
- Keep hosted runners; no self-hosted runner for public PRs.
- Publishing stays a separate main-only job with contents:write; PR CI is read-only.

Workflows pin action commit SHAs. Dependabot proposes action updates monthly.

## Security/community

- Enable Dependabot alerts, secret scanning and push protection where available.
- Enable private vulnerability reporting after publication.
- CodeQL workflow runs on public-repository pushes/PRs and weekly. It deliberately
  skips the current private repository where the required product is unavailable.
- Keep Issues on. Bug/feature templates, CONTRIBUTING.md and SECURITY.md are included.
- Delete merged branches automatically.

`scripts/configure_github.ps1` applies and reads back settings using a separately
supplied administration token. It does not read CREAM's update token, change visibility,
rewrite history, delete releases or upload secrets. Run it only from a trusted checkout.
It reports unsupported/forbidden settings individually, rather than claiming success.

Use a fine-grained token limited to this repository with Administration and Actions
read/write and Vulnerability alerts read/write, plus metadata/contents read as required
by GitHub. Pass it at the secure prompt; never paste it into an issue or this chat.
The script may need rerunning after the repository becomes public.
