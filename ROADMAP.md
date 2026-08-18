# Roadmap

SKILLS 的路线图围绕一个目标：让 Agent Skill 从“能找到”走向“能理解来源、能审查、能复现、再决定是否安装”。时间仅表示方向，不是交付承诺。

## 已完成

- [x] 每日更新超过 300 Star 的公开 Skill 来源索引
- [x] 把来源仓库拆分为具体 Skill 包，而不是只统计仓库数量
- [x] 区分 `direct`、`extracted` 与 `needs-review`，避免把候选包宣传成安全认证
- [x] 固定来源 Commit，记录包内容摘要、许可证与提取信息
- [x] 生成 Registry v1 与只新增的核验证据
- [x] 为 40 个精选 Skill 提供可独立安装的目录结构

## 近期：安装体验与兼容性

- [ ] 提供带摘要预览、冲突检测和撤销提示的一键安装器
- [ ] 建立 Codex、Claude Code 与其他 Agent 的兼容性矩阵
- [ ] 为精选 Skill 增加最小冒烟测试与真实任务示例
- [ ] 在网站中按用途、权限、依赖和验证状态筛选

## 中期：维护者与社区审查

- [ ] 完善源仓库维护者认领与元数据纠错流程
- [ ] 展示可复现的社区试用报告，而不是只收集点赞
- [ ] 增加 Skill 版本变化、依赖变化和风险规则变化的差异视图
- [ ] 为失效、归档或许可证变化建立清晰的下架记录

## 长期：开放 Registry

- [ ] 提供稳定的 Registry 查询 API 和版本化 Schema
- [ ] 研究签名清单与可验证发布制品
- [ ] 记录真实隔离环境中的运行证据，同时明确环境与权限边界
- [ ] 让其他目录、安装器和 Agent 客户端可以复用同一份开放数据

## 参与路线图

如果你愿意试用，请提交一条[体验反馈](https://github.com/userInner/SKILLS/issues/new?template=product-feedback.yml)，写清 Agent、操作系统、Skill、任务和结果。具体、可复现的失败报告比一句“不错”更有价值。

想提交或认领公开 Skill，请使用[提交表单](https://github.com/userInner/SKILLS/issues/new?template=submit-or-claim-skill.yml)。
