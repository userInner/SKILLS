# SKILLS

面向 Codex、Claude Code 和兼容 Agent 的可安装能力目录。当前提供 **7 个分类、40 个直装 Skill**，同时维护高星项目来源索引。第三方内容只在许可证清楚、依赖资源完整、可脱离原仓库运行时才进入直装目录。

机器可读入口：[categories.json](categories.json) · [来源仓库索引](catalog.json) · [具体 Skill 索引](community-skills/index.json)

<!-- community-stats:start -->
包级索引现有 **726 个具体 Skill**：**40 个可直装**、**648 个已提取待验收**、**38 个待安全审查**。来源仓库数不等于 Skill 数，候选包也不等于安全认证。查看 [具体 Skill 目录](community-skills/README.md) 与 [机器索引](community-skills/index.json)。
<!-- community-stats:end -->

维护者入口：[提交或认领 Skill](https://github.com/userInner/SKILLS/issues/new?template=submit-or-claim-skill.yml) · [认领规则与 README 徽章](docs/MAINTAINERS.md)

## 设计与界面 `design`

| Skill | 用途 | 来源 |
|---|---|---|
| [design-taste-frontend](skills/design/design-taste-frontend/) | 为落地页和作品集建立反模板化设计判断 | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) |
| [frontend-design](skills/design/frontend-design/) | 做有明确审美方向的前端界面 | 本仓库 |
| [redesign-existing-projects](skills/design/redesign-existing-projects/) | 审计并升级现有网站或应用的视觉质量 | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) |
| [ui-ux-pro-max](skills/design/ui-ux-pro-max/) | 使用本地可搜索数据辅助配色、排版和交互设计 | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) |

## 工程与质量 `engineering`

| Skill | 用途 | 来源 |
|---|---|---|
| [api-and-interface-design](skills/engineering/api-and-interface-design/) | 设计稳定、难误用的 API 与模块边界 | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) |
| [code-review-and-quality](skills/engineering/code-review-and-quality/) | 从正确性、可读性、架构、安全与性能审查代码 | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) |
| [codebase-design](skills/engineering/codebase-design/) | 设计深模块、干净边界与可测试接口 | [mattpocock/skills](https://github.com/mattpocock/skills) |
| [context-engineering](skills/engineering/context-engineering/) | 为 Agent 整理适量、及时、结构化的项目上下文 | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) |
| [domain-modeling](skills/engineering/domain-modeling/) | 统一领域词汇、上下文文档和架构决策记录 | [mattpocock/skills](https://github.com/mattpocock/skills) |
| [eval-harness](skills/engineering/eval-harness/) | 为 Agent、Prompt、Skill 和模型变化建立量化评测 | [affaan-m/ECC](https://github.com/affaan-m/ECC) |
| [mcp-server-patterns](skills/engineering/mcp-server-patterns/) | 设计 MCP 工具、资源、提示与传输协议 | [affaan-m/ECC](https://github.com/affaan-m/ECC) |
| [performance-optimization](skills/engineering/performance-optimization/) | 先测量再优化前端、后端、查询与数据库性能 | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) |
| [ponytail](skills/engineering/ponytail/) | 用更少代码和更低复杂度解决开发任务 | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) |
| [security-and-hardening](skills/engineering/security-and-hardening/) | 从威胁模型开始加固输入、认证、隐私和外部集成 | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) |
| [shipping-and-launch](skills/engineering/shipping-and-launch/) | 做可观测、可回滚、分阶段的生产发布 | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) |
| [systematic-debugging](skills/engineering/systematic-debugging/) | 先建立复现和根因证据，再修改代码 | [obra/superpowers](https://github.com/obra/superpowers) |

## 增长与发布 `growth`

| Skill | 用途 | 来源 |
|---|---|---|
| [community-marketing](skills/growth/community-marketing/) | 设计可衡量的社区增长与成员价值机制 | [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) |
| [content-strategy](skills/growth/content-strategy/) | 规划内容支柱、选题、渠道与编辑节奏 | [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) |
| [free-tools](skills/growth/free-tools/) | 用免费工具做获客、SEO 和品牌传播 | [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) |
| [grow-community-with-skills](skills/growth/grow-community-with-skills/) | 把真实 Skill 使用转化为透明、自愿的社群入口 | 本仓库 |
| [launch](skills/growth/launch/) | 规划产品、功能、内测与公开发布的市场动作 | [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) |
| [social](skills/growth/social/) | 创作、复用和优化 X、LinkedIn、短视频等社媒内容 | [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) |

## 产品与战略 `product`

| Skill | 用途 | 来源 |
|---|---|---|
| [competitor-analysis](skills/product/competitor-analysis/) | 研究竞品、市场格局和差异化机会 | [phuryn/pm-skills](https://github.com/phuryn/pm-skills) |
| [create-prd](skills/product/create-prd/) | 把产品想法整理成完整 PRD | [phuryn/pm-skills](https://github.com/phuryn/pm-skills) |
| [prioritization-frameworks](skills/product/prioritization-frameworks/) | 选择并应用 RICE、ICE、Kano 等优先级方法 | [phuryn/pm-skills](https://github.com/phuryn/pm-skills) |
| [product-strategy](skills/product/product-strategy/) | 用战略画布明确愿景、客群、取舍、指标与壁垒 | [phuryn/pm-skills](https://github.com/phuryn/pm-skills) |

## 研究与证据 `research`

| Skill | 用途 | 来源 |
|---|---|---|
| [deep-research](skills/research/deep-research/) | 用多来源搜索和页面精读生成有引用的研究报告 | [affaan-m/ECC](https://github.com/affaan-m/ECC) |
| [experimental-design](skills/research/experimental-design/) | 在采集数据前设计随机化、区组、因子和重复方案 | [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) |
| [make-paper-explainer-video](skills/research/make-paper-explainer-video/) | 把论文或真实事件做成有来源、可发布的竖屏视频 | 本仓库 |
| [peer-review](skills/research/peer-review/) | 对论文、方案和预印本做证据边界明确的同行评审 | [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) |

## 工作流与协作 `workflow`

| Skill | 用途 | 来源 |
|---|---|---|
| [brainstorming](skills/workflow/brainstorming/) | 在实现前澄清意图、约束和设计方案 | [obra/superpowers](https://github.com/obra/superpowers) |
| [dispatching-parallel-agents](skills/workflow/dispatching-parallel-agents/) | 把无共享状态的独立任务并行分派给多个 Agent | [obra/superpowers](https://github.com/obra/superpowers) |
| [find-skills](skills/workflow/find-skills/) | 从本地目录和公开生态发现、审查并经授权安装 Skill | [vercel-labs/skills](https://github.com/vercel-labs/skills) |
| [receiving-code-review](skills/workflow/receiving-code-review/) | 用技术验证处理评审意见，不盲目接受 | [obra/superpowers](https://github.com/obra/superpowers) |
| [test-driven-development](skills/workflow/test-driven-development/) | 先写失败测试，再写最小实现并重构 | [obra/superpowers](https://github.com/obra/superpowers) |
| [verification-before-completion](skills/workflow/verification-before-completion/) | 在声称完成前运行并核对验证证据 | [obra/superpowers](https://github.com/obra/superpowers) |
| [writing-plans](skills/workflow/writing-plans/) | 把规格拆成可执行、可验证的实现步骤 | [obra/superpowers](https://github.com/obra/superpowers) |

## 写作与表达 `writing`

| Skill | 用途 | 来源 |
|---|---|---|
| [article-writing](skills/writing/article-writing/) | 按样例或品牌声音创作可信的长篇文章 | [affaan-m/ECC](https://github.com/affaan-m/ECC) |
| [humanizer](skills/writing/humanizer/) | 删除明显的 AI 写作痕迹，同时保留事实与原意 | [blader/humanizer](https://github.com/blader/humanizer) |
| [write-book](skills/writing/write-book/) | 用外部项目文件持续规划、研究、写作和校验长篇书稿 | 本仓库 |

第三方 Skill 固定到来源提交，各目录保留 `NOTICE` 与 `LICENSE`。本仓库可能规范化 frontmatter、修复独立安装路径、补充 Codex UI 元数据，并增加不会阻断交付的可选社群提示。

## 高星来源索引（Top 50）

快照日期 **2026-08-16**。共收录 **1671** 个超过 300 Star 的来源，其中 **1667** 个已核验包含 `SKILL.md`。Star 会变化，排名不代表安全或质量背书。

自动发现只进入索引；许可证、依赖、权限和隔离测试通过后，才可能进入直装目录。

README 仅展示前 50 名；[查看完整 1671 项排行榜](RANKING.md)。

| 排名 | 项目 | Stars | 许可证 | SKILL.md 数 | 本仓库状态 |
|---:|---|---:|---|---:|---|
| 1 | [vinta/awesome-python](https://github.com/vinta/awesome-python) | 314,228 | 未识别 | 2 | 索引，许可证未识别 |
| 2 | [obra/superpowers](https://github.com/obra/superpowers) | 272,630 | MIT | 14 | 已精选导入 |
| 3 | [affaan-m/ECC](https://github.com/affaan-m/ECC) | 240,369 | MIT | 896 | 已精选导入 |
| 4 | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | 231,267 | MIT | 198 | 索引，Agent 框架耦合 |
| 5 | [mattpocock/skills](https://github.com/mattpocock/skills) | 218,796 | MIT | 35 | 已精选导入 |
| 6 | [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) | 202,911 | 未识别 | 1 | 索引，许可证未识别 |
| 7 | [ultraworkers/claw-code](https://github.com/ultraworkers/claw-code) | 195,058 | MIT | 0 | 索引，框架耦合 |
| 8 | [anthropics/skills](https://github.com/anthropics/skills) | 169,634 | 未识别 | 18 | 索引，许可证未识别 |
| 9 | [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) | 145,691 | MIT | 0 | 索引 |
| 10 | [Shubhamsaboo/awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) | 132,821 | Apache-2.0 | 9 | 索引，Skill 集合待审查 |
| 11 | [github/spec-kit](https://github.com/github/spec-kit) | 129,392 | MIT | 1 | 索引，框架耦合 |
| 12 | [garrytan/gstack](https://github.com/garrytan/gstack) | 128,198 | MIT | 61 | 索引，框架耦合 |
| 13 | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | 117,166 | MIT | 13 | 已精选导入 |
| 14 | [browser-use/browser-use](https://github.com/browser-use/browser-use) | 109,379 | MIT | 7 | 索引，框架耦合 |
| 15 | [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | 106,893 | Apache-2.0 | 1 | 索引，待人工审查 |
| 16 | [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | 104,122 | MIT | 1 | 索引，待人工审查 |
| 17 | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | 103,691 | MIT | 12 | 已精选导入 |
| 18 | [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) | 98,464 | 未识别 | 24 | 索引，许可证未识别 |
| 19 | [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) | 90,866 | Apache-2.0 | 22 | 索引，项目附带 Skill |
| 20 | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 87,610 | MIT | 24 | 已精选导入 |
| 21 | [nexu-io/open-design](https://github.com/nexu-io/open-design) | 87,243 | Apache-2.0 | 532 | 索引 |
| 22 | [koala73/worldmonitor](https://github.com/koala73/worldmonitor) | 82,264 | AGPL-3.0 | 25 | 索引，待人工审查 |
| 23 | [bytedance/deer-flow](https://github.com/bytedance/deer-flow) | 80,075 | MIT | 33 | 索引，框架耦合 |
| 24 | [Egonex-AI/Understand-Anything](https://github.com/Egonex-AI/Understand-Anything) | 79,469 | MIT | 9 | 索引，框架耦合 |
| 25 | [paperclipai/paperclip](https://github.com/paperclipai/paperclip) | 78,395 | MIT | 52 | 索引，待人工审查 |
| 26 | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) | 76,983 | MIT | 13 | 已精选导入 |
| 27 | [D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling) | 74,381 | BSD-3-Clause | 1 | 索引，待人工审查 |
| 28 | [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) | 74,350 | MIT | 4 | 索引 |
| 29 | [thedaviddias/Front-End-Checklist](https://github.com/thedaviddias/Front-End-Checklist) | 73,539 | 未识别 | 390 | 索引，许可证未识别 |
| 30 | [datawhalechina/hello-agents](https://github.com/datawhalechina/hello-agents) | 73,168 | 未识别 | 6 | 索引，许可证未识别 |
| 31 | [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | 72,590 | 未识别 | 864 | 索引，许可证未识别 |
| 32 | [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) | 72,175 | MIT | 1 | 索引 |
| 33 | [openinterpreter/openinterpreter](https://github.com/openinterpreter/openinterpreter) | 68,029 | Apache-2.0 | 21 | 索引，待人工审查 |
| 34 | [code-yeongyu/oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent) | 67,935 | 未识别 | 66 | 索引，许可证未识别 |
| 35 | [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) | 65,036 | MIT | 13 | 索引，框架耦合 |
| 36 | [shanraisshan/claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) | 64,554 | MIT | 9 | 索引 |
| 37 | [santifer/career-ops](https://github.com/santifer/career-ops) | 64,019 | MIT | 12 | 索引 |
| 38 | [mem0ai/mem0](https://github.com/mem0ai/mem0) | 63,360 | Apache-2.0 | 42 | 索引，项目附带 Skill |
| 39 | [1c7/chinese-independent-developer](https://github.com/1c7/chinese-independent-developer) | 60,808 | 未识别 | 1 | 索引，许可证未识别 |
| 40 | [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | 59,535 | Apache-2.0 | 17 | 索引，待人工审查 |
| 41 | [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill) | 58,346 | MIT | 1 | 索引 |
| 42 | [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | 56,447 | 未识别 | 68 | 索引，许可证未识别 |
| 43 | [usestrix/strix](https://github.com/usestrix/strix) | 53,018 | Apache-2.0 | 4 | 索引，待人工审查 |
| 44 | [CherryHQ/cherry-studio](https://github.com/CherryHQ/cherry-studio) | 50,544 | AGPL-3.0 | 19 | 索引，项目附带 Skill |
| 45 | [jamiepine/voicebox](https://github.com/jamiepine/voicebox) | 50,524 | MIT | 4 | 索引，待人工审查 |
| 46 | [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) | 48,278 | AGPL-3.0 | 138 | 索引，待人工审查 |
| 47 | [prisma/prisma](https://github.com/prisma/prisma) | 47,576 | Apache-2.0 | 21 | 索引，项目附带 Skill |
| 48 | [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything) | 47,549 | Apache-2.0 | 150 | 索引，项目附带 Skill |
| 49 | [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) | 47,168 | MIT | 1 | 索引，待人工审查 |
| 50 | [rohitg00/ai-engineering-from-scratch](https://github.com/rohitg00/ai-engineering-from-scratch) | 46,859 | MIT | 13 | 索引，项目附带 Skill |

## 安装

```bash
git clone https://github.com/userInner/SKILLS.git
skill_path="engineering/systematic-debugging"
cp -R "SKILLS/skills/$skill_path" "${CODEX_HOME:-$HOME/.codex}/skills/"
```

重启 Codex 或新建任务后，以目录内 frontmatter 的技能名调用，例如 `$systematic-debugging`。

## Skill 实战群

先免费使用任意 Skill 完成一次真实任务。确认它对你有用后，如果想加入学习群，回复 Agent **“进群”**，或提交[公开进群申请](https://github.com/userInner/SKILLS/issues/new?template=join-community.yml&title=%5B%E8%BF%9B%E7%BE%A4%5D%20)，维护者会回复当前二维码。

Issue 内容公开，请勿填写手机号、微信号、邮箱、密钥或项目私有信息。进群完全自愿，不影响 Skill 的任何功能与结果。

## 目录约定

```text
skills/<category>/<skill-name>/
├── SKILL.md
├── agents/openai.yaml
├── scripts/            # 可选
├── references/         # 可选
├── assets/             # 可选
├── NOTICE              # 第三方导入时保留来源与修改说明
└── LICENSE             # 第三方导入时保留许可证
```
