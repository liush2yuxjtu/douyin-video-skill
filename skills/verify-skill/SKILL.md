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

## A-roll 提词录制器端到端验证 / Teleprompter E2E verify
Repo: https://github.com/liush2yuxjtu/aroll-teleprompter · Site: https://aroll-teleprompter.vercel.app/?k=<TP_KEY>&script=<id>（`koubo` / `chat20` / `voice-sample`）

```bash
git clone https://github.com/liush2yuxjtu/aroll-teleprompter && cd aroll-teleprompter
npm ci && npx playwright install chromium
TP_KEY=<key> node verify/verify.mjs        # 可选 BASE=<预览地址>；默认生产地址
```
Headless Chromium with `--use-fake-device-for-media-stream`, mobile (Pixel 7) + desktop (1440×900) viewports, for every script in `public/scripts/index.json`:
标签数量与切换、顶部新手说明、逐句字幕（`#cur` 与 `n / 总数`）、录制约 7s → 等「已自动上传」→ `GET /api/recordings?session=` 为 `complete`、`script` 字段正确、分片 ≥1、`markers.json` 的 `script.id` 正确；
最后只 `DELETE` 本次测试创建的会话（绝不删除真实录音）。通过标准：输出 `RESULT: ALL PASS`、退出码 0。改提词站后必须对生产地址跑通再报告完成。
