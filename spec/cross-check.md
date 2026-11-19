# Spec: cross-check

<!-- spec-guard: review approved 668ed38ced72 -->

## 目标

`/delivery-brief:brief <模块 id> --cross-check`：讲解源文件检查通过后，交给另一个模型（经 delegate 插件，只读）逐条核对说法与代码是否相符、
找出漏掉的事实；生成讲解的 agent 再把每条发现回到代码核实，成立的改进讲解，页面附录记下核对记录。默认关。

为什么要它：module-brief 的验收说明单次生成不保证属实、也不保证完整——样张初稿的 3 处失真是 Codex 交叉核对查出来的；
module-brief 的真实生成和样张相比又漏了 3 条「需要你判断的」。检查脚本只能管结构和引用，叙述对不对要另一双眼睛。

本模块是 M1 的最后一个模块，所以也负责 **M1 发版**：README 写全、补 LICENSE、版本 0.1.0、安装后端到端跑一次斜杠命令；
建远端仓库、推送、打标签每一步都先问用户。

对外接口与用法草案 `spec/usage/delivery-brief.md` 一致：入口表 `--cross-check` 一行（M1），U1 的「想更放心时加 `--cross-check`，页脚多一行核对记录」。
与草案的差异：核对记录放在附录的折叠块里，页脚只有一行摘要（草案写「页脚多一行」，现在是页脚一行加附录明细）。

给谁用：想让讲解先被另一个模型核过再看的用户。

## 假设

1. **只经 delegate 的对外入口**：调用 `/delegate:review`（delegate `interface.json` 的 `review.command`，接口 1.x），不直接调它的内部脚本，
   也不直接调 `codex`。可用技能里没有 `delegate:review` 时，说明「没装 delegate，跳过交叉核对」，照常渲染。
2. **后端用 delegate 的默认值**（目前是 Codex，另一个额度池）；本插件不指定模型，见待定问题 Q1。
3. **审查材料由脚本准备**：新脚本 `crosscheck_material.py --facts <facts> --source <brief.md> --out <目录>` 在讲解输出目录旁建一个临时 git 仓库，放入：
   讲解源文件、facts、本次范围的 diff、被引用的文件（终点提交上的版本）。delegate 的 Codex 审查把文件内容直接内联，上限 1 MiB；
   材料超过约 900 KB 时，被引用的大文件只放引用行前后各 40 行，并在材料说明里写明截取了哪些。仍然超限时报错退出，不让审查方看不全还当全看了。
4. **不把结论喂给审查方**：给审查方的任务是固定模板（`references/cross-check-prompt.md`）：只说读者是谁、讲解要回答什么、请核对什么、
   请找漏掉的什么；不附生成方自己的评价，也不告诉它哪些地方可能有问题。
5. **审查结论不等于事实**：每条发现，生成讲解的 agent 都要回到代码（或在导出临时目录里实跑）核实，标成
   `confirmed`（成立，已改讲解）、`rejected`（不成立，写明证据）或 `unverified`（核实不了，写明原因）。只改 `confirmed` 的。
   改完重新跑检查脚本（这一次检查不计入 module-brief 的三次）。
6. **核对记录**写成 `<名字>.crosscheck.json`：`backend`、`model`（delegate 报告里有就写，没有写 `unknown`）、`reportPath`、`coverage`
   （审查了几个文件、没审查几个）、`findings[]`（`title`、`verdict`、`note`）。渲染脚本加可选参数 `--cross-check <json>`：附录里加一个
   「交叉核对记录」折叠块，页脚加一行摘要（几条发现、几条成立已改、几条不成立、几条没核实）。JSON 写坏时渲染脚本退出 2。
7. **失败照实记**：delegate 报错、超限、部分覆盖（`unreviewed` 非空）、输出为空时，核对记录写 `status: incomplete` 和原因，页面照常渲染，
   页脚写「交叉核对没有完成：原因」。不把 delegate 退出 0 当成「核对通过」。
8. **花费**：一次核对约 10～25 万输入 token，随材料大小（样张那次实测 10.3 万；usage-draft 讲解 26 个文件、约 58 万字节材料实测 22.4 万），花在 delegate 后端的额度上。用户写了 `--cross-check` 就算同意，不再另问；
   命令开始前的规模报告里加一句预计花费。
9. **M1 发版**（本模块的最后一段）：README 从用法草案展开写全（安装、命令、输出位置、示例截图）；补 MIT LICENSE；两份清单版本 0.1.0；
   按插件安装方式在本机装上，端到端跑一次 `/delivery-brief:brief`（不加和加 `--cross-check` 各一次）；然后依次问用户：建远端仓库（公开的 `haigeerlab/delivery-brief`）、推送、打 `v0.1.0` 标签。
   发版后经 agent-relay 告诉 ecosystem-lead：版本、标签对应的提交、安装情况、改了什么。

## 命令

```text
python3 -B -m unittest discover -s plugins/delivery-brief/tests
python3 -B plugins/delivery-brief/scripts/crosscheck_material.py --facts <facts.json> --source <brief.md> --out <目录>
python3 -B plugins/delivery-brief/scripts/render_brief.py --facts <facts.json> --source <brief.md> --out <brief.html> --cross-check <crosscheck.json>
/delivery-brief:brief usage-draft --project <spec-guard 克隆> --cross-check
claude plugin validate .
```

## 项目结构

```text
plugins/delivery-brief/scripts/crosscheck_material.py   # 准备审查材料（新）
plugins/delivery-brief/references/cross-check-prompt.md # 给审查方的固定任务模板（新）
plugins/delivery-brief/scripts/render_brief.py          # 加 --cross-check
plugins/delivery-brief/commands/brief.md                # 加 --cross-check 一步
plugins/delivery-brief/tests/                           # 材料脚本、渲染核对记录的测试
README.md、LICENSE、两份清单                             # M1 发版
```

## 测试策略

- 材料脚本先写测试：被引用的文件按终点提交导出（不是工作区）；diff 范围正确；超限时退回引用窗口并写进说明；仍超限退出非 0；
  不写被讲解项目（快照比对）；生成的材料目录是一个干净提交的 git 仓库。
- 渲染：有 `--cross-check` 时附录有记录、页脚有摘要；`incomplete` 时页脚写没有完成与原因；JSON 写坏退出 2；不给参数时页面与之前相同（除生成时间）。
- 规则一致性：命令文件里的新参数在脚本 `--help` 里；任务模板里没有生成方的结论（不含「需要你判断的」原文）。
- 真实运行：对 module-brief 那份 usage-draft 讲解加 `--cross-check` 跑一次，记录发现条数、成立几条、和样张对照时漏掉的 3 条是否被找回；记录花费。
- 发版：安装后端到端两次（不加、加 `--cross-check`），浏览器自验成品。

## 边界

- Always：只经 `/delegate:review`；审查只读；每条发现先核实再改；失败照实记；默认关。
- Ask first：建远端仓库、推送、打标签、装插件到全局（本机安装算改全局配置）；在 delegate 默认值之外指定后端或模型。
- Never：直接调 `codex` 或 delegate 的内部脚本；把审查方的话不经核实写进讲解；把 delegate 退出 0 当成核对通过；
  把生成方的自我评价放进审查材料。

## 成功标准

- AC1：不给 `--cross-check` 时，流程与产物和 module-brief 相同（渲染结果除生成时间外逐字相同，测试守护）。
- AC2：`crosscheck_material.py` 按假设 3 准备材料：被引用文件取终点提交上的版本、带范围 diff、超限时退回引用窗口并说明、仍超限退出非 0；
  被讲解项目不变。
- AC3：命令文件写明 `--cross-check` 的流程：没装 delegate 时跳过并说明；调用 `/delegate:review` 的参数；逐条核实与 `verdict`；改后复检；
  失败照实记。
- AC4：`render_brief.py --cross-check` 渲染核对记录与页脚摘要；`incomplete` 写明原因；JSON 写坏退出 2。
- AC5：`references/cross-check-prompt.md` 是固定模板，不含生成方结论；测试守护。
- AC6：对 usage-draft 讲解真实跑一次 `--cross-check`，核对记录完整，结果（发现数、成立数、是否找回漏掉的 3 条、花费）写进验收材料。
- AC7：M1 发版准备：README 写全、LICENSE、版本 0.1.0、`claude plugin validate .` 与目录检查（`--profile directory`）通过；本机安装后端到端两次成功。
- AC8：建远端、推送、打标签都在用户分别同意后才做；发版后回告 ecosystem-lead。

## 文档建议

- README 本次写全（M1 发版），从用法草案展开：安装、`/delivery-brief:brief` 的两种参数、`--cross-check`、`--no-open`、输出位置、
  范围推断与已知局限（链接 `docs/facts-schema.md`）、一张讲解页截图。

## 待定问题

- 无。2026-11-19 用户定为「批准；Q1 A；Q2 A」：交叉核对只用 delegate 的默认后端，本插件不传后端和模型（假设 2）；
  远端仓库为公开的 `haigeerlab/delivery-brief`（假设 9；建仓、推送、打标签仍逐步先问）。

## 变更记录

- 2026-11-19：假设 8 的预计花费由「约 10 万」改为「约 10～25 万」，依据 Task 4 实测 22.4 万输入 token；随最终验收交审。
