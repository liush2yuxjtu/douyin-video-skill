# douyin-video-skill — 把抖音视频变成 Agent Skill

> 把抖音博主的干货视频做成可复用的 Agent Skill。第一个 skill **`viral-topic-picking`**（爆款选题）用"脑科学四问"帮你造选题、找选题、给选题打分。

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-SKILL.md-orange)](https://agentskills.io)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-skill-d97757)](https://code.claude.com/docs/en/skills)
[![Install with npx skills](https://img.shields.io/badge/npx%20skills-add-black)](https://github.com/vercel-labs/skills)

[English](README.md) · [中文](README_zh.md)

`douyin-video-skill` 收集从抖音干货视频**完整字幕**整理出来的 **Agent Skill**。每个 skill 把博主的方法写成 AI agent（Claude Code、Codex、Cursor 等）能照着执行的步骤，原始字幕也放在仓库里，方便对照原文核对 agent 的建议。

## Skills

| Skill | 作用 | 来源视频 |
|---|---|---|
| [`viral-topic-picking`](skills/viral-topic-picking/SKILL.md) | 给抖音、小红书、视频号做**爆款选题**：生成候选、按"脑科学四问"打分、指出最弱的一问并给出改法 | 抖音 @人类最强编导《给我两秒就好》（[视频](https://www.douyin.com/video/7690907639698132081)） |

## 为什么做这个

选题决定一条视频的流量上限。常见的"爆款选题" prompt 只给泛泛的技巧；这个 skill 照着一位编导的完整方法走（来自**全文字幕**，不是摘要），并让 agent 用同一套标准给每个候选打分，所以你拿到的是带理由的排名，而不是一堆猜测。

## 脑科学四问

用户刷到你的视频时，大脑会先快速判断：

1. **和我有关吗？**（用户认领）用一个难以量化的好特质（有想法、能干、成熟）锚定人群，再连接他的欲望或困境。
2. **我在乎吗？**（兴趣强度）写用户正在承受的结果，而不只是一个"重要的话题"。
3. **和我想的一样吗？**（预期违背）打断他原来的判断，让他想问"为什么"。
4. **我能马上看懂吗？**（合意难度）不太简单也不太难，落在认知甜蜜点上。

skill 里还写了怎么**造**选题（沿一个需求往下挖；从不同现象提炼相同本质），以及怎么从热点里按角色、行为、事件三个角度**找**选题。

## 安装

用开源的 [`skills`](https://github.com/vercel-labs/skills) 命令行（可安装到 Claude Code、Codex、Cursor 等 agent）：

```bash
npx skills add liush2yuxjtu/douyin-video-skill --skill viral-topic-picking -g -y
```

或者手动复制到 Claude Code（[官方文档](https://code.claude.com/docs/en/skills)）：

```bash
git clone https://github.com/liush2yuxjtu/douyin-video-skill
mkdir -p ~/.claude/skills
cp -r douyin-video-skill/skills/viral-topic-picking ~/.claude/skills/
```

skill 遵循开放的 [Agent Skills](https://agentskills.io) 格式（`SKILL.md` 带 `name` 和 `description` frontmatter），支持这个格式的 agent 都能加载。

也可作为 Claude Code 插件安装：`/plugin marketplace add liush2yuxjtu/douyin-video-skill`，再 `/plugin install douyin-video-skill@douyin-video-skill`。

本地校验（无 CI）：`bash skills/verify-skill/verify.sh`。

## 使用

直接用自然语言问 agent，例如：

- "帮我想个选题"
- "这个选题能火吗：为什么年轻人越活越累"
- "从这个热点找选题"

agent 会：

1. 先问清楚或推断你的账号定位、目标人群和手上的素材。
2. 产出 5 到 10 个候选选题，每个写成一句标题或开头。
3. 每个候选按四问打分（每项 0 到 2 分），附一句理由。
4. 给出排名前 3 的选题，每个配一句开头钩子，比如 `给我两秒，你是不是 X，但是 Y`。
5. 指出最弱的一问，以及具体怎么改。

**示例**（来自 `SKILL.md`）：

> 输入：职场号，素材是"同事抢功"。
> 输出：「为什么最能干的那个人，总是最后一个被看见」。认领：能干的人；在乎：付出被吞的损失；违背：能干却不被看见；合意难度：一句话就能懂。

## 目录结构

```
skills/
  viral-topic-picking/
    SKILL.md                    # 方法和执行步骤
    references/transcript.md    # 来源视频带时间戳的全文字幕
  verify-skill/                 # 本地校验（无 CI）：bash skills/verify-skill/verify.sh
.claude-plugin/                 # Claude Code 插件市场清单
ATTRIBUTION.md                  # 出处与版权声明
LICENSE
README.md / README_zh.md
```

## 来源与致谢

> **引用声明：** `viral-topic-picking` 引用了抖音 **@人类最强编导**《给我两秒就好》（[视频](https://www.douyin.com/video/7690907639698132081)）的完整字幕，仅供学习与参考，版权归原作者所有。详见 [ATTRIBUTION.md](ATTRIBUTION.md)；如需删除请提 [issue](https://github.com/liush2yuxjtu/douyin-video-skill/issues)。

方法归原作者抖音 @人类最强编导 所有。视频没有官方字幕，字幕用 `faster-whisper`（`medium`）转写，可能有少量识别错误，已在 `transcript.md` 开头注明。本仓库是非官方的学习笔记，**与抖音、字节跳动及原作者无关**。如果你是原作者，希望修改或删除任何内容，请提 [issue](https://github.com/liush2yuxjtu/douyin-video-skill/issues)。

## 路线图

- [ ] 从更多抖音干货视频整理新 skill（开头钩子、脚本结构、剪辑节奏）
- [ ] 每个 skill 配一个真实输入输出的完整示例
- [x] 抖音视频读取 skill 已独立成仓库：[douyin-read-skill](https://github.com/liush2yuxjtu/douyin-read-skill)

## 贡献

从另一个视频新增 skill：

1. 新建 `skills/<skill-name>/SKILL.md`，写好 `name` 和 `description` frontmatter，description 要说明 agent 什么时候该用它。
2. 把全文字幕放到 `skills/<skill-name>/references/transcript.md`，注明来源链接、作者、发布日期和字幕获取方式。
3. 注明原作者，不要加视频里没说过的内容。

## 许可证

本仓库的 skill 文件采用 [MIT](LICENSE)。来源视频及其观点归原作者所有。
