# douyin-video-skill — Agent Skills distilled from Douyin videos

> Turn a Douyin (抖音) creator's video into a reusable Agent Skill. The first skill, **`viral-topic-picking`**, helps you pick and score short-video topics with the "four brain questions" method.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-SKILL.md-orange)](https://agentskills.io)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-skill-d97757)](https://code.claude.com/docs/en/skills)
[![Install with npx skills](https://img.shields.io/badge/npx%20skills-add-black)](https://github.com/vercel-labs/skills)

[English](README.md) · [中文](README_zh.md)

`douyin-video-skill` collects **Agent Skills** built from the full transcripts of useful Douyin videos. Each skill turns a creator's method into steps an AI agent can follow, such as Claude Code, Codex or Cursor. The original transcript stays in the repo so you can check the agent's advice against the source.

## Skills

| Skill | What it does | Source video |
|---|---|---|
| [`viral-topic-picking`](skills/viral-topic-picking/SKILL.md) | Generates, scores and fixes **viral short-video topics** (爆款选题) for Douyin, Xiaohongshu (RedNote) and WeChat Channels, using four questions the viewer's brain asks in the first two seconds | 抖音 @人类最强编导《给我两秒就好》([video](https://www.douyin.com/video/7690907639698132081)) |

## Why

A topic sets the ceiling on a short video's views. Most "viral topic" prompts give generic tips. This skill follows one creator's complete method, taken from the **full transcript** (not a summary), and makes the agent score every candidate against it, so you get ranked topics with reasons instead of a list of guesses.

## The four questions

When a viewer scrolls past your video, their brain quickly decides:

1. **Is this about me?** Anchor the audience with a hard-to-measure good trait (thoughtful, capable, mature), then connect to their desire or struggle.
2. **Do I care?** Write about a result they are living with, not just an "important topic".
3. **Is this what I expected?** Break their prediction so they ask "why?".
4. **Can I get it right away?** Not too easy, not too hard: the sweet spot of effort.

The skill also covers how to **build** topics (dig down one need; lift different cases to one shared feeling) and how to **find** them in hot events through role, behavior and event angles.

## Install

With the open-source [`skills`](https://github.com/vercel-labs/skills) CLI, which installs into Claude Code, Codex, Cursor and other agents:

```bash
npx skills add liush2yuxjtu/douyin-video-skill --skill viral-topic-picking -g -y
```

Or as a Claude Code plugin: `/plugin marketplace add liush2yuxjtu/douyin-video-skill` then `/plugin install douyin-video-skill@douyin-video-skill`.

Or copy it by hand into Claude Code ([official docs](https://code.claude.com/docs/en/skills)):

```bash
git clone https://github.com/liush2yuxjtu/douyin-video-skill
mkdir -p ~/.claude/skills
cp -r douyin-video-skill/skills/viral-topic-picking ~/.claude/skills/
```

The skill follows the open [Agent Skills](https://agentskills.io) format (`SKILL.md` with `name` and `description` frontmatter), so any agent that supports it can load it.

## Usage

Ask your agent in plain language, for example:

- "帮我想个选题" / "Help me come up with a topic for my career account"
- "这个选题能火吗：为什么年轻人越活越累" / "Will this topic work?"
- "从这个热点找选题" / "Find topics in this trending story"

The agent will:

1. Ask for (or infer) your account positioning, audience and material.
2. Draft 5 to 10 candidate titles or opening lines.
3. Score each one 0 to 2 on all four questions, with a one-line reason.
4. Return the top 3, each with an opening hook such as `给我两秒，你是不是 X，但是 Y`.
5. Point out the weakest question and how to fix it.

**Example** (from `SKILL.md`):

> Input: a workplace account; material: "a coworker took credit for my work".
> Output: 「为什么最能干的那个人，总是最后一个被看见」 ("Why the most capable person is always the last to be noticed"). About me: capable people. Care: losing credit for your effort. Unexpected: capable yet unseen. Easy: one sentence.

## Repo layout

```
skills/
  viral-topic-picking/
    SKILL.md                    # the method and step-by-step instructions
    references/transcript.md    # full timestamped transcript of the source video
  verify-skill/                 # local checks (no CI): bash skills/verify-skill/verify.sh
.claude-plugin/                 # Claude Code plugin marketplace manifest
ATTRIBUTION.md                  # source & copyright notice
LICENSE
README.md / README_zh.md
```

## Source and credit

> **Attribution:** `viral-topic-picking` quotes the full subtitles of 《给我两秒就好》 by Douyin creator **@人类最强编导** ([video](https://www.douyin.com/video/7690907639698132081)) for learning and reference only. Copyright belongs to the original author. See [ATTRIBUTION.md](ATTRIBUTION.md); removal requests via [issues](https://github.com/liush2yuxjtu/douyin-video-skill/issues).

The method belongs to its creator, 抖音 @人类最强编导. The video had no official subtitles, so the transcript was made with `faster-whisper` (`medium`) and may contain a few recognition errors, which are noted at the top of `transcript.md`. This repo is an unofficial study note and is **not affiliated with Douyin, ByteDance or the creator**. If you are the creator and want anything changed or removed, please open an [issue](https://github.com/liush2yuxjtu/douyin-video-skill/issues).

## Roadmap

- [ ] More skills distilled from other Douyin creator videos (hooks, scripts, editing rhythm)
- [ ] A worked example for each skill with real input and output
- [x] Douyin video reader skill now lives in its own repo: [douyin-read-skill](https://github.com/liush2yuxjtu/douyin-read-skill)

## Contributing

To add a skill from another video:

1. Create `skills/<skill-name>/SKILL.md` with `name` and `description` frontmatter. The description should say when the agent should use it.
2. Put the full transcript in `skills/<skill-name>/references/transcript.md`, with the source URL, author, publish date and how the transcript was made.
3. Credit the creator and do not add anything the video does not say.

## License

[MIT](LICENSE) for the skill files in this repo. The source video and its ideas belong to their creator.
