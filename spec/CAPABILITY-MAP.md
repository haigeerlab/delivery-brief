# Capability Map: delivery-brief（交付讲解）

## 目标

AI 交付一个模块或一个里程碑后，用一个命令按需调出一个本机网页，让懂技术的程序员（主要是用户本人）几分钟看懂这次代码造了什么、
为什么这样造、怎么串起来、哪里要人判断（总账 S90）。形式以定稿样张为准；讲解只摆事实，不给代码质量打分，不进被讲解项目的仓库。

<!-- 这一段是 Proposal 审查的目标指纹底本（`spec-digest.py` 计算）。
     改写目标会让已发布的 Proposal 被判为过期，所以改了先人工审阅；追加模块不需要改这里。
     标题必须是 `## 目标`（或 `## Goal`）—— 指纹脚本按标题定位这一节。 -->

## 模块

| Module id | Responsibility | Depends on |
|---|---|---|
| brief-facts | 插件骨架与事实收集脚本：把「模块 id／里程碑／任意提交段」解析成提交范围（spec-guard 项目按其文件约定推断并标明来源，可用显式提交段覆盖），收集提交、逐文件增删、Spec 的 AC、todo 勾选、用法草案归属、代码链接基址与规模估算，输出 JSON；只读，不调用模型 | — |
| module-brief | 模块讲解页：`/delivery-brief:brief <模块 id 或 base..head>` 读 brief-facts 的输出与代码，按讲解规则（六问、证据只引用测试断言／代码行／实跑输出、按《技术图表选型指南》选图）写单文件 HTML 到 `~/.claude/delivery-brief/<项目>/`；生成前报规模；生成后结构校验脚本检查必备各节、链接落在范围内的提交上 | brief-facts |
| cross-check | `--cross-check`：生成后经 delegate 插件做只读事实核对（不带结论喂给审查方），把核实成立的问题改进讲解页并在页脚记下；没装 delegate 时说明后跳过；默认关 | module-brief |
| ui-screenshots | 有界面改动的模块：按项目的启动方式起开发服务器，给清单里的页面截图嵌进讲解页；起不来或没有界面时写明「截图未生成」及原因，不让生成失败 | module-brief |
| milestone-brief | 里程碑讲解页：`--milestone <M>` 读用法草案的里程碑，出代码地图（标出这一站新增与改动）、沿典型用法走一遍的完整链路、新出现的跨模块约定，并链接各模块页；缺的模块页标出或先生成 | module-brief |

Build order: brief-facts → module-brief → cross-check → ui-screenshots → milestone-brief

<!-- Spec Guard 按严格串行推进。为兼容上游格式，逗号分组会按左到右顺序展开为单模块步骤，不代表并行授权。 -->

---

## 审阅记录

<!-- 第一次审能力图时的自查清单：勾不勾都行，spec-guard 的工具不读也不校验这一节；能力图是否批准以对话里用户的答复为准。 -->

- [ ] 模块边界确认（砍掉或替换一个模块，不需要重写其他模块的需求）
- [ ] 依赖方向单向无环（互相依赖 = 它们本来就是一个模块）
- [ ] module id 已定稿（kebab-case，之后绝不改名 —— 同一个 id 同时是
      `spec/<id>.md`、`tasks/<id>/`、`.agent/state.json` 的 `activeModule` 和 Proposal 中的模块名，
      已发布的 Proposal 改不动）
- [ ] 构建顺序符合依赖拓扑

审阅人：
日期：
