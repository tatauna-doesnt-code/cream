# Pre-publication audit â€” 2026-10-30

Repository snapshot: 98b34387197e42c65af11b695cc2f037a066e79a. Visibility remains private.

## Scope and limits

Reviewed all 32 reachable commits on the sole main branch, 32 complete trees and
179 unique historical text blobs; all 16 published CREAM-plugin.zip archives;
and available logs for 15 workflow jobs (latest attempts only).
Credential access for private release downloads stayed in memory and was not logged.
Patterns covered GitHub/API/private/AWS keys and personal absolute paths. File
names were checked for saved settings/credentials, real spreadsheets and SPP files.
No matching credentials or obvious private-data files were found. The CSV is a sample.
This is a bounded pattern/content review, not a guarantee against unsupported,
obfuscated or binary-embedded secrets; earlier rerun-attempt logs were not scanned.
GitHub-native secret scanning should still be enabled when available.

## Cleanup findings

### Personal path in historical UI source

Four historical UI module blob versions contain a developer-specific absolute output path.
The actual private path is intentionally not repeated here. The current code uses
the current Windows user's locations.

| Blob | Representative commit |
| --- | --- |
| 3db447641d31e91dfe06561e3c65d37b28e16804 | 8d8391e612b7b685fe1e1bd7cfa75d4db4d9bfc9 |
| 8b028f95704e59b381bf31a569e9f3d997e4fc5a | d1fae9581558e1bb5b707e00f8e7a435e8c02994 |
| 062d6925dca082bc75df4ee76df0227b2332fd94 | 623483217e1b713aadb4c07f7945d604f2f517f5 |
| 8b625b8d41d047c362bf170e8db48a1250da430a | ad61fb96f4a6ef0202bcf337b6ff9d5797c9da70 and seven other trees |

Release ZIPs v1.1.0, v1.1.1, v1.1.2, v1.2.1 and v1.3.0 contain this type of path.
Cleaning Git history does not clean uploaded release ZIPs.

### Bornie artwork in history and v1.9.4

The former wordmark is blob c8479c1bb773400c1ea16b3e40f2b15f58c40dd3,
the historical logo asset. The v1.9.4 ZIP also contains it. Its source font
archive has a personal-use license; rendering an image did not resolve usage rights.
The new source removes the bitmap/renderer and uses OFL-licensed Righteous.
No Bornie OTF was found in the repository or release archives.

## Decision before public visibility

Recommended: privately back up and purge the personal path and Bornie bitmap from
all intended public Git refs, then remove/replace affected release assets and rescan.
Alternatively publish a clean new repository from the GPL/Righteous source and
retain this history privately. Either choice needs the owner's approval:
no history rewrite, force push, tag rewrite, release deletion or visibility change
has been performed. Old caches/forks may need separate handling after any rewrite.

## Live settings and prepared protections

Actions: GitHub-owned actions plus this owner's actions only, full SHA pinning required.
Read-only token defaults and disabled Actions PR approval were already configured.
Dependency graph, Dependabot alerts and Dependabot security-fix PRs were enabled.
Automatically deleting merged PR branches was enabled.
Private fork PR workflows remain disabled to avoid expanding private-source access.

An admin plan/helper, read-only PR CI, pinned workflows, CodeQL (public-only),
Dependabot action updates, contribution/security policies and issue forms are included.
Ruleset enforcement, public-fork approval policy, secret scanning/push protection,
private vulnerability reporting and public CodeQL need verification when the repository
is public or on a plan that supports them. See github-settings-plan.md for desired values.

## Verified live administration changes

On 2026-10-30 the browser confirmed ruleset CREAM main protection, ID 26240731,
was created with Active status, targeting main, no bypass actors, pull requests,
zero mandatory approvals, resolved conversations, up-to-date branches, GitHub Actions
Test and package, deletion restriction and force-push blocking. GitHub explicitly
states this private repository's plan does not enforce it yet. Recheck enforcement
before relying on it after publication or a plan change.

The public-fork all-contributor approval setting, private vulnerability reporting,
secret scanning and push protection are not currently exposed on this private
personal repository's available settings page. They remain post-publication tasks.
CodeQL is included but intentionally skips private repositories on this plan.
Dependency graph and Dependabot alerts/security updates are verified On. Malware
alerts did not become enabled and are not claimed as configured.
