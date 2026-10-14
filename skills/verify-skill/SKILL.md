---
name: verify-skill
description: Use before committing or pushing changes to this repo (douyin-video-skill) to run the local verification suite (there is no CI) — required files, SKILL.md frontmatter, .claude-plugin JSON, attribution of quoted creator content, broken relative markdown links, and bash -n / shellcheck on scripts. 提交或推送前运行本地校验（本仓库不使用 CI）。
---
# Local verification / 本地校验 (no CI)

This repo intentionally has no GitHub Actions. Run this locally before every push.
本仓库不使用 GitHub Actions，每次推送前请在本地运行。

## Run / 运行
```bash
bash skills/verify-skill/verify.sh
```
Needs `bash`, `python3`; `shellcheck` is used if installed, otherwise skipped. Exit code 0 = all passed.
需要 `bash`、`python3`；装了 `shellcheck` 会自动使用。退出码 0 表示全部通过。

## What it checks / 检查项
1. Required files: `README.md`, `README_zh.md`, `LICENSE`, `.claude-plugin/*.json`; no `.github/workflows`.
2. Every `skills/*/SKILL.md` has frontmatter with `name` (= directory, lowercase-hyphen) and a non-empty `description` (≤1024 chars), plus a body.
3. `.claude-plugin/marketplace.json` and `plugin.json` are valid JSON, names and versions match.
4. Attribution: `ATTRIBUTION.md` exists, mentions the source title, creator and link, and is linked from both READMEs and from every skill that ships a `references/` transcript.
5. Every relative markdown link resolves to an existing file.
6. `bash -n` and `shellcheck -S warning` on every `*.sh`.

When adding a skill from a new video, also add its source to `ATTRIBUTION.md`.
新增来自其他视频的 skill 时，请同步在 `ATTRIBUTION.md` 中补充出处。
