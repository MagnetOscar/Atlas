# Atlas engineering guide

Read [docs/development.md](docs/development.md), [docs/releasing.md](docs/releasing.md), [AICACHE.md](AICACHE.md), and the nearest scoped guide.

## Scope and compatibility

- Current task (2026-11-19): adjust the automatic release workflow to upload only the theme ZIP, place SHA256/source/verification links in the description and link optional components separately. No runtime, dependency, saved-setting, manifest-version or production changes; do not trigger a release or rebuild a theme ZIP for this task.
- Use Atlas for current project names. Retain copyrights/notices, vendored bytes, upstream links/history and fork baseline 0332d5f7c73f7994ba21c01e4b739d04835120b1.
- Preserve legacy Enhanced configuration, plugin IDs/paths, dependency names and per-node authentication; do not blindly rename compatibility identifiers or third-party source.
- Preserve accepted UI and data semantics. Further UI changes require explicit authorization and an additive contract under [the UI SOP](docs/ui-contract-sop.md).
- Repository maintenance does not authorize server writes/probes. Retain existing Komari attachment scheduling and endpoints without new daemons/listeners.

## Workflow

- Authoritative branch: personal/main. Upstream is read-only. Isolate work from dirty user worktrees and deliver a pushed commit plus reviewable diff.
- Keep unfinished work in a Draft PR. Preflight the final edited tree before Ready; return to Draft before further edits. Retain required lint-and-build/screenshots checks, branch protection and genuine failure notifications.
- Inspect CI commands/lockfiles first. Use non-mutating lint. Runtime/UI edits require complete affected suites and build/package checks; no weakened assertions or blind snapshot regeneration. Windows checks do not replace Linux fixture coverage.
- Documentation-only changes require links, scope and git diff --check, without rebuilding or repeating local runtime/native tests. Workflow edits additionally require YAML and edited shell/package-contract checks, without creating a test Release.
- Record actual checks and gaps. Avoid redundant tests/backups. Never publish credentials or private deployment evidence.

## Packaging and licensing

- komari-theme.json.version is the only version source. Native package: komari-theme-Atlas-build-<short-sha>.zip, containing only komari-theme.json, preview.png, dist/. Preview source remains docs/preview.png.
- Theme Releases have one manually uploaded theme ZIP. Put SHA256 and source/verification links in their descriptions; GitHub automatic source archives remain visible.
- Components use a separate archive download page with original versions, bytes, licenses and source commits. Never mix Plugin/Helper/TcpQuality/rootfs/installers into a theme ZIP.
- Do not move software tags or replace theme ZIPs. The 2026-11-19 user request explicitly permits removing JSON/checksum attachments and relocating components once replacement links exist.
- Preserve MIT notices and the separate pinned TcpQuality GPL-3.0-only source/license.

## Architecture

Follow Component -> Composable -> Service -> RequestManager / CacheService -> API / RPC and [src/AGENTS.md](src/AGENTS.md). Preserve public monitoring, authorized sensitive actions, reactive references, live updates, request/cache behavior and unknown saved fields.

Do not reintroduce Naive UI, UnoCSS, SCSS or extra icon component libraries. Runtime resource paths and defaults are contracts.

[Historical task policy](https://github.com/MagnetOscar/Atlas/blob/e0039b2f323114977fc1e94de054bd90f4f3e3b7/AGENTS.md) remains available in Git history.
