# Docs workflow Node pins — 2026-10-24

Pin both docs builders to the approved Node `22.23.4` target from base
`1fdddacfb92224b2617d41b59e6ac2a9a7fe39e3`.

- `.github/workflows/deploy-site.yml:42`: `20` → `22.23.4`.
- `.github/workflows/docs-site-checks.yml:21`: `20` → `22.23.4`.
- `website/package.json:49–50` accepts Node `>=20.0`.
- Action commit SHAs remain pinned per `AGENTS.md:311–330`.
- Existing workflow triggers, permissions and repository guards remain intact.

The native PR workflow installs website dependencies, regenerates skill docs,
lints diagrams and builds Docusaurus (`docs-site-checks.yml:25–48`). The deploy
job remains upstream-only (`deploy-site.yml:32`); this fork PR grants no
publication or deployment authority.

## Validation and status

Refreshed by normal merge of `main` after the independent fixture correction in
PR2. The docs PR diff remains the two workflow pins and this evidence file.

Local validation command: `git diff --check`. Native PR checks provide the
install/build result; this source document makes no claim about a future run.
No tests are added or removed. No local install, generated output, Python lock
change, installed-runtime replacement or restart belongs to this candidate.

Status: source candidate, unmerged. Review the exact PR head and native checks
before a separate merge decision. Rollback after an approved merge: revert its
actual merge commit.

Local run records: `.claude/artifacts/node-sec-docs-node-pins/` in the canonical
checkout; check and review results belong to the PR and its handoff packet.
