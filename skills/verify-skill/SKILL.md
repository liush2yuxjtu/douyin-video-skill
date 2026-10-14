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

### 手机文字显示检查 / Mobile text-display checks
`verify/verify.mjs` 先跑这部分（`TEXT_ONLY=1` 只跑它，不上传）：iPhone SE 375×667、iPhone 14 390×844、Pixel 7 412×915、小屏安卓 360×740 × 竖屏/横屏 × 空闲/录制中布局 × 每个脚本的每一句：
- 无横向溢出：`scrollWidth <= clientWidth`
- 字幕 `#cur` 完整在视口内，且文字区域 `elementFromPoint` 命中的是字幕自身（没被按钮/控制栏遮挡）
- 字号在 16–72px；字幕框不裁切：`scrollHeight <= clientHeight`
- 中文非豆腐块：canvas `measureText` 宽度与缺字字形对比（box 上需装 Noto Sans CJK，避免误报）
- 截图存 `verify/artifacts/`（`ART=` 可改）。用户反馈“手机上字显示不对”时，先跑这部分确认能复现（应 FAIL），修完再跑到 ALL PASS。

## 克隆配音校验 / Voiceover (voice-clone) verify
Script: [`verify_voiceover.py`](verify_voiceover.py). Needs `ffmpeg`, `numpy`, `faster-whisper` (CPU, `compute_type=float32`; audio decoded via ffmpeg → float32 numpy, no torchaudio).
需要 `ffmpeg`、`numpy`、`faster-whisper`（CPU、float32；用 ffmpeg 解码成 numpy 送入）。

```bash
python3 skills/verify-skill/verify_voiceover.py \
  --full vo_full.wav --clips final/ --lines lines.txt --ref ref_real.wav \
  --nouns 杜威,默顿,波利亚,置换        # 专有名词常被 ASR 识错，相似度计算时忽略
```
`--clips` = one wav per sentence, sorted by filename in line order; `--lines` = script, one sentence per line.
`--clips` 每句一个 wav（按文件名排序 = 台词顺序）；`--lines` 每行一句。

Checks / 检查项 (PASS / WARN / FAIL table, exit 1 on any FAIL):
1. **Text** — per sentence + full file, char similarity (digits → 汉字, punctuation stripped, `--nouns` removed): `<0.80` FAIL, `<0.90` WARN. Proper nouns and homophones (长→找, 教程→叫常) are often ASR errors, so listen to WARNs before regenerating; a repeated mis-hear of a common word (e.g. 先→卸) is more likely a real slip.
   逐句 + 全文字符相似度；WARN 先人工听，常见词被反复识错更可能是真读错。
2. **Pitch** — median f0 of the voiceover vs the real-voice reference within ±10% (catches the "announcer" pitch-up: old clone 164 Hz vs real 116 Hz).
   音高中位数与真人参考相差 ≤10%（播音腔会整体偏高）。
3. **Rate** — chars/s over speech within the reference's per-segment range ±20%.
   语速（字/秒）在真人参考范围 ±20% 内。
4. **Gaps / junk** — max silence in full file ≤1.5s; per clip: duration ≤ chars/2 + 2.5s and inner silence ≤1.0s. Catches the TTS reading the **style prompt aloud** (seen on very short lines like 「下期见。」) and long dead air.
   全文最长静音 ≤1.5s；单句时长与内部静音上限——可抓到 TTS 把风格提示词念出来、长空白。
5. **Level** — true peak ≤ −1 dBFS, integrated −14 ± 1.5 LUFS; a raw clip at 0 dBFS is a WARN (source take may be clipped, prefer regenerating).
   真峰值 ≤ −1 dBFS，响度 −14±1.5 LUFS；单句原始峰值 0 dBFS 给 WARN。

6. **Prosody (phrasing + intonation)** — needs `jieba` (else WARN-skip; `--no-prosody` to turn off). Full-file word timestamps are aligned to the script; each energy pause (≥0.08s, −30 dB) is snapped (±1 char, ASR jitter) to a script boundary: sentence end / comma / jieba word boundary / inside a word.
   韵律（断句 + 语调）：需要 `jieba`。把每个停顿对齐到台词边界：句末 / 逗号 / 词边界 / 词内。
   - **FAIL run-on**: fewer than 30% of commas get a pause (`--min-comma-pause`) — sounds breathless/odd. 逗号处几乎不停顿 = 一口气念完，听感断句怪。
   - **FAIL mid-phrase break**: any pause ≥0.15s not at punctuation (`--max-midphrase`), e.g. `可能是|三个月前`. 非标点处停顿 ≥0.15s。
   - **FAIL inverted hierarchy**: a non-sentence-end pause ≥0.9× the mean sentence-end pause (comma pauses must be clearly shorter than full stops). 逗号停顿不应接近句末停顿。
   - **WARN flat intonation**: mean per-sentence f0 range < 7 semitones (`--min-f0-range`); phrase-final moves are printed (clear falls ≈ assertive/"good tone"). 每句音高范围 <7 半音给 WARN。
   Calibrated on a human listening test (3 style samples): run-on A and mid-phrase-break B were judged 「断句太奇怪」, C 「连贯」; B (13 st range, −3.5 st final falls) 「语气语调好」. The metrics reproduce all three. Root cause there was the TTS take itself (raw takes already had 0/9 comma pauses, or 1.2 s mid-sentence gaps and `可能是|三个月前`); silence-shortening only acts on <−32 dB gaps, so it cannot splice voiced audio, but it flattens pause contrast — re-take bad sentences instead of over-trimming.
   以 3 个风格样本的人工听感校准：A（一口气）和 B（词中断）被评「断句怪」，C「连贯」，B「语气语调好」，指标全部复现。根因是 TTS 原始 take，而非剪静音/变速；坏句应重生成。

### Clone reference rule / 克隆参考音规则
- Use **20–30 s of natural, continuous speech** from the real speaker, same phone/room, normal pace. Record it with the teleprompter scripts `chat20` (casual chat) and `voice-sample` (clean read); trim only leading/trailing silence, light normalization, no EQ/reverb.
  用真人 **20–30 秒自然连续说话**（同一手机、同一房间、正常语速），用提词器脚本 `chat20` / `voice-sample` 录制；只裁首尾静音、轻度归一化，不加 EQ/混响。
- A test clip like 「喂喂喂…」 **fails**: it carries timbre but no tones/prosody, so the model falls back to a polished announcer delivery (uncanny, pitch too high). Do not compensate with fake reverb or dashes/ellipses in the text — they add dead air.
  「喂喂喂」式参考音会失败：只有音色没有声调与语调，模型退回播音腔。不要用假混响或在文本里加破折号/省略号来补救。
- Keep the original script text; style prompt casual (「像平时跟朋友聊天一样随口说……不要播音腔」); 2 takes per bad sentence, pick by this script.
  文本保持原稿；风格提示要口语化；问题句各生成 2 条，用本脚本挑选。

`verify.sh` only byte-compiles this script (no audio needed); set `VO_DIR=<dir with vo_full.wav, final/, ref_real.wav, lines.txt>` to also run it (skipped if `faster-whisper` is missing).
`verify.sh` 默认只做语法检查；设置 `VO_DIR=` 才会真正跑配音校验（缺依赖则 SKIP）。
