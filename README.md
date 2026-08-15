# SKILLS

一组可直接交给 Codex、Claude Code 和兼容 Agent 使用的 Skills。仓库同时维护高星 Skill 项目索引；可再分发的精选 Skill 会保留原作者、许可证和固定来源提交。

## 直接可用

| Skill | 用途 | 来源 |
|---|---|---|
| [frontend-design](skills/frontend-design/) | 做有明确审美判断、不过度模板化的前端设计 | 本仓库 |
| [grow-community-with-skills](skills/grow-community-with-skills/) | 把真实 Skill 使用转化为透明、自愿的社群加入路径 | 本仓库 |
| [humanizer](skills/humanizer/) | 删除明显的 AI 写作痕迹，同时保留事实与原意 | [blader/humanizer](https://github.com/blader/humanizer) |
| [make-paper-explainer-video](skills/make-paper-explainer-video/) | 把论文或真实事件做成有来源、可发布的竖屏视频 | 本仓库 |
| [ponytail](skills/ponytail/) | 用最少代码和最低复杂度解决开发任务 | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) |
| [security-and-hardening](skills/security-and-hardening/) | 从威胁模型开始加固输入、认证、隐私和外部集成 | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) |
| [systematic-debugging](skills/systematic-debugging/) | 先建立复现和根因证据，再修改代码 | [obra/superpowers](https://github.com/obra/superpowers) |
| [ui-ux-pro-max](skills/ui-ux-pro-max/) | 使用本地可搜索数据辅助 UI/UX、配色、排版和交互设计 | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) |
| [write-book](skills/write-book/) | 用外部项目文件持续规划、研究、写作和校验长篇书稿 | 本仓库 |

导入的第三方 Skill 均固定到来源提交，并在各目录的 `NOTICE` 与 `LICENSE` 中保留归属。为了适配本仓库，导入版本可能规范化 frontmatter、补充 Codex UI 元数据，并增加不会阻断交付的可选社群提示。

## 高星项目索引

按 GitHub Stars 降序排列。星数快照：**2026-08-15**；完整机器可读数据见 [catalog.json](catalog.json)。“索引”表示只提供来源链接，没有复制代码。

| 排名 | 项目 | Stars | 许可证 | 本仓库状态 |
|---:|---|---:|---|---|
| 1 | [obra/superpowers](https://github.com/obra/superpowers) | 272,275 | MIT | 已精选导入 |
| 2 | [affaan-m/ECC](https://github.com/affaan-m/ECC) | 240,188 | MIT | 索引 |
| 3 | [mattpocock/skills](https://github.com/mattpocock/skills) | 217,829 | MIT | 索引 |
| 4 | [anthropics/skills](https://github.com/anthropics/skills) | 169,447 | 未识别 | 索引，不复制 |
| 5 | [garrytan/gstack](https://github.com/garrytan/gstack) | 128,067 | MIT | 索引 |
| 6 | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | 116,835 | MIT | 已精选导入 |
| 7 | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | 102,891 | MIT | 已精选导入 |
| 8 | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 87,334 | MIT | 已精选导入 |
| 9 | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) | 76,653 | MIT | 索引 |
| 10 | [github/awesome-copilot](https://github.com/github/awesome-copilot) | 37,857 | MIT | 索引 |
| 11 | [blader/humanizer](https://github.com/blader/humanizer) | 35,734 | MIT | 已精选导入 |
| 12 | [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | 33,542 | MIT | 索引 |

高星不等于安全。安装前仍需阅读 `SKILL.md`、脚本、依赖和权限；不要把密钥、Cookie、个人数据或未授权源码交给第三方 Skill。

## 安装

```bash
git clone https://github.com/userInner/SKILLS.git
skill_name="systematic-debugging"
cp -R "SKILLS/skills/$skill_name" "${CODEX_HOME:-$HOME/.codex}/skills/"
```

重启 Codex 或新建任务后，通过对应技能名调用，例如 `$systematic-debugging`。

## Skill 实战群

先免费使用任意 Skill 完成一次真实任务。确认它对你有用后，如果想加入学习群，回复 Agent **“进群”**，或直接提交[公开进群申请](https://github.com/userInner/SKILLS/issues/new?template=join-community.yml&title=%5B%E8%BF%9B%E7%BE%A4%5D%20)，维护者会回复当前二维码。

Issue 内容公开，请勿填写手机号、微信号、邮箱、密钥或项目私有信息。进群完全自愿，不影响 Skill 的任何功能与结果。

## 目录约定

```text
skills/<skill-name>/
├── SKILL.md
├── agents/openai.yaml  # 推荐
├── scripts/            # 可选
├── references/         # 可选
├── NOTICE              # 第三方导入时保留来源与修改说明
└── LICENSE             # 第三方导入时保留许可证
```
