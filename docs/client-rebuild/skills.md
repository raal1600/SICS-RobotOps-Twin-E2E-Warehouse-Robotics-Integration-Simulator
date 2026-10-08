# Installed skills

All four complete skill directories are installed under project `.agents/skills`.
Pinned sources and file checksums are in [skill-manifest.json](skill-manifest.json).
Read each upstream README and skill before installation; used the reviewed built-in
skill-installer with `--repo`, pinned `--ref`, `--path`, `--dest .agents/skills`, and
`--method download`. No customized install existed. No collection-wide install.

| Skill | Source / commit | Installed directory | Usable check and application |
|---|---|---|---|
| Impeccable 4.5.0 | [pbakaus/impeccable](https://github.com/pbakaus/impeccable), `778c8a7b71ccd5bfe3ca6ac68c15d9d872d0f87d` | `.agents/skills/impeccable` | `scripts/impeccable.cmd context --target apps/erp_ui/index.html` passed; operate/distill/harden/craft-floor guidance read and used for task hierarchy, progressive detail, plain language and focus/state review |
| Web Design Guidelines 1.0.0 | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills), `063bee94c3f4df8453406c830b0a7df0f2860278` | `.agents/skills/web-design-guidelines` | Current `vercel-labs/web-interface-guidelines/main/command.md` fetched and read; semantic navigation, skip link, keyboard tabs, URL state and error checks |
| UI/UX Pro Max | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill), `477bcb28c9812b385cb51a4605ddf30d7b2266e2` | `.agents/skills/ui-ux-pro-max` | Python search passes with complete data/scripts/references; `focus not obscured --domain ux` returned specific AA/AAA distinctions applied to removing sticky overlays |
| OpenAI Playwright | [openai/skills](https://github.com/openai/skills/tree/main/skills/.curated/playwright), `49f948faa9258a0c61caceaf225e179651397431` | `.agents/skills/playwright` | Reviewed wrapper, CLI help, actual app open and snapshot passed; browser evidence and reusable Python Playwright regression framework |

## Runtime and review details

Windows PowerShell 5.1; Node 20.17.0, npm/npx available, Git Bash installed. Existing
Python 3.13 virtual environment and Playwright 1.63.0 retained. Impeccable's npm shim
requires newer Node, so use the official Windows engine 0.1.11 with its shipped launcher.
The 17,096,584-byte release binary was verified against its SHA-256 sidecar:
`605b5b442d2a65d270ef989de13371444849526249f511d397ca7424c184db49`.
It is stored in ignored `artifacts/client-rebuild/tooling/impeccable.exe`, selected via
`IMPECCABLE_BIN`; no unreviewed installer/hook or global engine cache was used.

UI/UX Pro Max's reviewed scripts use Python standard library/local CSV files. No OS
install is required. The complete upstream skill package was copied with supporting
files; its example command paths were adapted from the Claude package to the verified
Codex `.agents/skills` path. This local adaptation is documented in the manifest.
The generated design-system search suggested a marketing page; it was rejected as a
poor fit. A narrower product query returned no match. Existing product conventions
and the verified focus guidance were used, with no generated competing design files.

Playwright CLI `@playwright/cli@0.1.22` and axe-core `4.14.0` were installed in ignored
tooling artifacts using `--ignore-scripts --no-audit --no-fund`. Reviewed metadata:
CLI depends on official Playwright/Playwright Core `1.64.0-alpha-1790635538000`; axe
has no runtime dependencies. CLI entry point delegates to Playwright core. Update
notifier disabled during use. Existing Python E2E continues to use pinned 1.63.0.
The first CLI open failed because only Chromium headless-shell was installed; using
the observed `chrome-headless-shell.exe` in the CLI config fixed it. No browser security
control was disabled. CLI help/open/snapshot verified; this was not a framework replacement.

## Activation and hooks

All installed SKILL.md files and relevant references were explicitly read and used
in this session. Automatic discovery is **pending verification in a new session
launched inside this repository** (the current harness started at the user directory).
Official [Codex skill locations](https://learn.chatgpt.com/docs/build-skills) document
repository `.agents/skills` support and reloading if discovery does not occur.

Impeccable automatic hooks are **not installed, not approved, and not claimed active**.
Upstream allows `--no-hooks`; manual-copy installation was used. Its context command
requests a manual detector pass at the finish. It was run; findings and static-path limitations are reviewed in verification.md. All installed file hashes were verified again in artifacts/client-rebuild/skill-verification.json.
No security prompt was approved on the user's behalf.
