<!-- Sync note: this page mirrors README.md section for section; English is authoritative. Update both in the same commit. -->
# Econ Slides Skill（经济学 Beamer 学术幻灯片）

**把你的经济学论文变成一套专业的 Beamer 演讲——拿到顶级研讨会上也不丢人的那种。**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-ready-8A2BE2.svg)](#安装)
[![Codex](https://img.shields.io/badge/Codex-ready-brightgreen.svg)](#安装)
[![en](https://img.shields.io/badge/lang-English-red.svg)](./README.md)
[![中文](https://img.shields.io/badge/语言-中文-yellow.svg)](./README.zh-CN.md)

*中英文如有出入，以[英文版](./README.md)为准。*

| 核心结论页 | 主结果表格页 |
|---|---|
| ![AI 生成 Beamer 演讲中的核心结论页：主结果、一个支撑性的异质性模式和由此得出的含义](docs/images/sample-punchline.png) | ![主结果页：Table 2 中四个精确估计值、一个高亮单元格和一句简洁的经济学解读](docs/images/sample-mainresult.png) |

*这两页由本技能对一篇演示论文冷启动生成——完整的[示例幻灯片（PDF）](docs/sample-talk/conference-30min.pdf)与[演讲讲稿（PDF）](docs/sample-talk/script.pdf)。*

`econ-slides` 是一个面向 Claude Code 和 Codex 的 Agent Skill（智能体技能）。AI 生成的幻灯片通常败在两处：版面凌乱，演讲没有论证主线。本技能同时解决这两个问题：它汇集多位知名经济学家的演讲方法论，把论文自身的逻辑依赖结构转化为一场演讲，并在交付前通过编译、测量渲染后的版面几何、逐页目检来验证结果。

*为经济学而生，也适用于任何以证据、模型与回归表为基础的研究报告。*

> **初次接触 Claude Code 或 Codex？** 它们是在你自己电脑上运行的 AI 智能体，可配合你现有的 Claude 或 ChatGPT 订阅使用，几分钟即可完成安装（[Claude Code](https://docs.anthropic.com/en/docs/claude-code) · [Codex](https://openai.com/index/codex/)）。装好任意一个之后，econ-slides 只需粘贴一段话即可安装。

## 它能做什么

- **论文 → 演讲。** 给它一份稿件和一个 15 到 90 分钟的总时长，它会构建一条带领听众走完全程的最短路径：问题、答案、必要的实证或理论铺垫、证据或命题、解读、含义。顺序和每页的结构始终取决于论文本身。
- **演讲讲稿。** 生成可打印的排练讲稿：逐页对应幻灯片标题、从开场到正文全程计时、与真实的视觉分步展示同步，并附有备用的问答应对模块。默认为提问保留总时长的 20–25%，绝不为凑时长注水。
- **评论人（discussant）幻灯片。** 作为一等公民对待、而非附带功能：一份面向听众校准的论文摘要，加上最有分量的几条点评（每条自带标题），每条都落在具体建议上——遵循达拉斯联储与 ASHEcon 的评论人规范。
- **修改现有幻灯片。** 增加主题页、附录、讨论内容或整体打磨，同时把已编译的目标幻灯片当作设计契约：工作流会逆向识别并保留其 Beamer 风格，而不是套用本技能自带的主题。
- **改编演讲场合。** 同一篇论文的 15 分钟版和 90 分钟版是两场不同的演讲，不是同一套幻灯片讲快讲慢。本技能以完整的论证单元为单位进行保留、压缩、移动、删减或深化，而不是把每页等比缩放。

## 为什么这些幻灯片值得信任

1. **体裁忠实。** 论文转演讲的请求始终是作者报告。证据审核只用于校准措辞和一个关键局限，不会悄悄把开场、标题页和结论变成一份审稿报告。
2. **论断与数值可溯源。** 起草大纲之前，技能会将行文与处理分配规则、图表、表注、单位和代数逐一核对。每个待用的标题论断被归类为"有支撑、描述性、有冲突、排除"之一；每个量级都追溯到其所在表格和页码。讲稿不可能把"相关"说成"提高"。
3. **渲染行数纪律。** 只要表意允许，标题和要点会改写到渲染后单行以内。确实无法压缩且可读的换行以 PDF 实际效果为准判断，而不是机械否决；整页缩字号永远不是第一选择。
4. **图表优先用原件。** 优先复用或裁剪清晰的原文图表；其次使用幻灯片原生表格、公式或简洁文字。只有必要时才基于可追溯的输入重建或新建图形，并逐一目检。回归表会精简到演讲真正需要的行和列。
5. **真实的验证闭环。** `compile_deck.py` 负责编译并分诊错误；`check_deck.py` 拦截客观缺陷——超出页边、严重溢出、失效链接、导航元素碰撞——同时把换行、密度、分栏、强调和留白列为人工复核项。对局部修改，其基线模式能区分"继承的旧问题"与"新引入的客观退化"，且不豁免视觉比对。`check_script.py` 审核标题顺序、总时长、问答分离、口语风格和真实的点击同步。两份 PDF 都要经过逐页目检。

## 效果展示

页面顶部的两页幻灯片来自交错推行（staggered-rollout）[示例演讲](docs/sample-talk/)，按 30 分钟总时长构建；其配套讲稿约 22.5 分钟，为提问留出约四分之一的时间。

**[浏览完整的示例基准 →](docs/sample-talk/)**：包含幻灯片与讲稿的 PDF 和 LaTeX 源文件，以及一份结构规划。它使用来自 [econ-paper-review-skill](https://github.com/hanlulong/econ-paper-review-skill) 的虚构演示论文；来源说明见示例的 [README](docs/sample-talk/README.md)。

本框架还在多篇实质不同的实证与理论论文上做过本地审核。第三方论文及其衍生的测试幻灯片保持私密，不随技能发布。

## 安装

需要 Python 3.10+、带 XeLaTeX 的 TeX 发行版（TeX Live / MacTeX / MiKTeX），以及 PyMuPDF（`python3 -m pip install --user pymupdf`；若你的 Python 受系统管理限制，请装入虚拟环境）。

将以下内容粘贴到 Claude Code 或 Codex（安装指令面向智能体，请保持英文原文）：

```text
Help me install the econ-slides skill from
https://github.com/hanlulong/econ-slides-skill: clone it, then link the
folder as an Agent Skill — into ~/.claude/skills/econ-slides for Claude Code
and ~/.agents/skills/econ-slides for Codex (whichever of the two I use).
Verify python3 and xelatex are available and pymupdf is installed (use
--user or a venv if pip is externally managed), then confirm the skill
loads.
```

<details>
<summary>手动安装</summary>

macOS / Linux：

```bash
git clone https://github.com/hanlulong/econ-slides-skill.git
python3 -m pip install --user pymupdf   # 若 pip 受系统管理限制，请装入虚拟环境

# Claude Code（全局技能目录）
ln -s "$(pwd)/econ-slides-skill" ~/.claude/skills/econ-slides

# Codex（共享的 agent-skills 目录）
mkdir -p ~/.agents/skills
ln -s "$(pwd)/econ-slides-skill" ~/.agents/skills/econ-slides
```

Windows（PowerShell——使用 `python` 而非 `python3`）：

```powershell
git clone https://github.com/hanlulong/econ-slides-skill.git
python -m pip install --user pymupdf
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\econ-slides" -Target "$PWD\econ-slides-skill"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills" | Out-Null
New-Item -ItemType Junction -Path "$env:USERPROFILE\.agents\skills\econ-slides" -Target "$PWD\econ-slides-skill"
```

两个客户端读取同一份 `SKILL.md`；任何能读取它的智能体都能使用本技能。脚本为纯 Python（全程 pathlib，TeX 路径使用 `os.pathsep`），可在 macOS、Windows 和 Linux 上运行；`tests/run-tests.sh` 需要 bash（Windows 上可用 Git Bash 或 WSL）。

</details>

## 使用

把论文（PDF，如有 LaTeX 源文件一并放入）放进工作目录，然后提出请求（中文提问同样有效；示例为英文原文）：

```text
Use the econ-slides skill to make a 30-minute total-session conference talk
from this empirical paper, reserving 20–25% for questions.
Use the econ-slides skill to prepare exactly 20 minutes of speaking; the
organizer schedules questions separately.
Use the econ-slides skill to make a 60-minute pure-theory seminar talk.
Use the econ-slides skill to make the talk and a printable speaker script.
Use the econ-slides skill to build my discussion of the attached paper for a 15-minute total session.
Use the econ-slides skill to turn my 90-minute seminar deck into a 30-minute
total-session version for SED while preserving its Beamer style.
Use the econ-slides skill to add slides on the mechanism and a linked appendix
to my existing deck without restyling it.
```

技能会在动笔之前先给你看"论断—证据台账"和幻灯片规划，然后交付幻灯片的 `.tex`/PDF、可选的讲稿 `.tex`/PDF，以及一份说明——每个标题论断和数值分别来自论文的哪张表、哪一页。

## 主题

三套内置外观加一个通用适配器，同一套语义接口——成稿的幻灯片只需改一行 `\usepackage` 即可切换主题：

| 主题 | 外观 | 适用场合 |
|---|---|---|
| `econ-slides-house`（默认） | 无装饰、居中的信息式/对象式标题、Palatino 数学字体、Okabe–Ito 色板 | 研究报告 |
| `econ-slides-clean` | 近乎黑白、左对齐标题配细分隔线 | 不留任何视觉风格印记的场合 |
| `econ-slides-boxed` | 深蓝标题栏、结构化区块 | 论文评论、政策场合 |
| `econ-slides-compat` | **你喜欢的任何 Beamer 标准主题** | Madrid、metropolis、CambridgeUS、机构主题 |

想用标准主题新建幻灯片？先 `\usetheme{Madrid}` 再 `\usepackage{econ-slides-compat}`，即可保留原有外观并获得语义接口。修改机构或个人的现有幻灯片？保留其原有导言区、编译引擎、宏、间距和视觉语言。详见 [themes/README.md](themes/README.md)。

## 仓库结构

```
SKILL.md                 工作流：接收 → 精读 → 规划 → 起草 → 验证 → 交付
references/
  talk-structures.md     可调整的听众路径与 15–90 分钟时间预算
  discussant.md          论文评论体裁：骨架、时间预算、语气规则
  slide-rules.md         渲染版面规范：标题、间距、数学、颜色
  beamer-layout-mechanics.md
                         源码修改如何改变编译后的版面
  existing-deck-workflow.md
                         在不改变风格的前提下增补、打磨、评论或改编
  exhibit-surgery.md     回归表 → 幻灯片表格；图形；数值溯源
  source-integrity.md    论断↔证据台账；识别策略、模型与政策核查
  speaker-script.md      计时、口语表达、点击同步、问答与可打印质检
  style-guide.md         主题、文件工程、构建与交付规范
themes/                  三套内置外观 + 标准主题兼容适配器
templates/               可选的实证、理论、评论与讲稿起点模板
scripts/
  compile_deck.py        XeLaTeX 编译循环与错误分诊
  check_deck.py          渲染版面审核：硬性拦截项 + 评分
  check_script.py        幻灯片/讲稿同步、计时、口语风格与点击审核
  crop_figure.py         无独立图形文件时裁剪原文图形
tests/                   跨主题渲染 + 缺陷幻灯片/讲稿反例
```

## 它不做什么

它不会代写论文内容，不会编造材料中不存在的数值，不会承诺论文没有的结果。它也不会把文献综述放上幻灯片——所有演讲方法论文献在这一点上意见一致。

## 相关项目

- [econ-paper-review-skill](https://github.com/hanlulong/econ-paper-review-skill) — 审稿侧的姊妹技能：它评判论文，本技能展示论文
- [econ-writing-skill](https://github.com/hanlulong/econ-writing-skill) — 先把论文写好
- [awesome-ai-for-economists](https://github.com/hanlulong/awesome-ai-for-economists) — 更全面的工具索引

## 致谢

演讲方法规则综合了以下公开指南：[Jesse Shapiro](https://shapiro.scholars.harvard.edu/notes-and-lectures)、Rachael Meager、[Paul Goldsmith-Pinkham](https://paulgp.com/beamer_tips.pdf)、[John Cochrane](https://faculty.wcas.northwestern.edu/mdo738/teaching/cochrane.pdf)、Dick Startz、[Marc Bellemare](https://profiles.shsu.edu/dpg006/present.htm)、Monika Piazzesi、Alex Tabarrok、David Evans、Darren Lubotsky、Donald Davis、Keith Head，以及达拉斯联储和 ASHEcon 的评论人指南。验证方法借鉴了 [beamer-skill](https://github.com/Noi1r/beamer-skill)（PDF 渲染目检）和 [Pedro Sant'Anna 的工作流](https://github.com/pedrohcgs/claude-code-my-workflow)（可执行的质量关卡）；TikZ 定位规则改编自 Scott Cunningham 的 MixtapeTools。实现为原创；公开指南仅作署名链接，未捆绑或复制。

## 许可证

MIT——见 [LICENSE](LICENSE)。

---

如果这个技能帮你省下了研讨会前夜赶幻灯片的恐慌，请为仓库点一颗星，让更多经济学者找到它；如果它做出了难看或不诚实的幻灯片，请开一个 issue。在这里，糟糕的幻灯片就是 bug。
