# SKILLS

可复用的 Codex Skills 集合。

## 目录约定

所有可安装技能放在 `skills/<skill-name>/` 下，每个技能保持独立、标准的 Codex 结构：

```text
skills/
└── <skill-name>/
    ├── SKILL.md
    ├── agents/openai.yaml  # 推荐
    ├── scripts/           # 可选
    └── references/        # 可选
```

## 已收录技能

- [frontend-design](skills/frontend-design/)：为新界面或现有界面重塑提供有辨识度、非模板化的视觉设计指导。
- [make-paper-explainer-video](skills/make-paper-explainer-video/)：从论文核验、数据解读到配音剪辑，制作有来源、有局限说明的竖屏论文解读视频。
- [write-book](skills/write-book/)：使用分层上下文持续规划、研究、起草和修订小说或非虚构书稿。

## 安装单个技能

```bash
git clone https://github.com/userInner/SKILLS.git
skill_name="frontend-design"
cp -R "SKILLS/skills/$skill_name" "${CODEX_HOME:-$HOME/.codex}/skills/"
```

重启 Codex 或新建任务后，通过对应的技能名调用；例如 `$frontend-design`。
