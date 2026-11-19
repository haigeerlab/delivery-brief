# Plan: cross-check

<!-- spec-guard: review approved -->

依据 [`spec/cross-check.md`](../../spec/cross-check.md)（2026-11-19 用户在本会话批准：「批准；Q1 A；Q2 A」，提交 `3bb39dd`）。
分支 `main`，串行，在本会话做。本模块完成即 M1，版本 0.1.0。

## Overview

先做两个确定性部分（审查材料脚本、渲染核对记录），各自先写失败的测试；再写给审查方的固定模板与命令文件里的 `--cross-check` 一步；
然后对 module-brief 生成的 usage-draft 讲解真实跑一次交叉核对。之后做 M1 发版准备（README、LICENSE、0.1.0），在本机安装前停下问你；
装好后由你在新会话里端到端跑两次，我核对产物；最后验收，并逐项问你建远端、推送、打标签。

## Architecture Decisions

1. **材料是一个独立的临时 git 仓库**：`crosscheck_material.py` 在 `<输出目录>/.crosscheck-<名字>/` 建仓库，放 `brief.md`、`facts.json`、
   `range.diff`、`MATERIAL.md`（说明每个文件是什么、哪些被截取）与 `source/<路径>`（被引用文件在终点提交上的版本），提交一次。
   delegate 的 `--repo` 指向它、`--paths` 列出这几项。材料目录每次重建，跑完由命令删除。
2. **大小控制在脚本里**：按 UTF-8 字节统计全部材料；超过 900 KB 时，从最大的被引用文件开始换成「引用行前后各 40 行」的窗口，
   直到不超；仍超限退出 3 并列出各项大小。阈值是参数，测试用小阈值覆盖截取与超限两条路。
3. **核对记录的格式由渲染脚本校验**：`crosscheck.json` 必须有 `status`（`complete`／`incomplete`）、`backend`、`model`、`reportPath`、
   `coverage`（`reviewed`、`unreviewed` 两个整数）、`findings[]`（`title`、`verdict` ∈ confirmed／rejected／unverified、`note`），
   `incomplete` 时另有 `reason`。缺字段或取值不对退出 2 并点名字段。
4. **不加参数时零影响**：渲染时没有 `--cross-check` 就不输出任何核对相关的标记；测试比对两次渲染（去掉生成时间）逐字相同，并且与
   不认识这个参数的旧逻辑的输出相同（用固定夹具的期望片段守护）。
5. **给审查方的模板放在 `references/cross-check-prompt.md`**：命令只替换其中的读者与范围占位；测试守住模板里没有「需要你判断的」等
   生成方结论用语、没有「可能有问题」之类的引导。
6. **调用 delegate 由命令文件规定**：用 Skill 调 `delegate:review`，参数 `--repo <材料目录> --paths brief.md --paths facts.json --paths range.diff
   --paths MATERIAL.md --paths source`，任务为模板全文；读 delegate 输出里的报告 JSON（`findings`、`unreviewed`、`execution_status`、`observed_models`）。
   不传后端与模型（Q1 A）。

## Task List

### Task 0：提交 Plan 与 todo

- 验证：verify-artifacts 0 失败。

### Task 1：审查材料脚本（AC2）

- 文件：`scripts/crosscheck_material.py`、`tests/test_material.py`。
- 用例：被引用文件取终点提交版本（工作区改过也不受影响）；`range.diff` 与 `git diff base head` 一致；`MATERIAL.md` 列出全部文件；
  超阈值时最大的文件换成窗口并在说明里写明；仍超限退出 3 并列大小；材料目录是干净的单提交仓库；被讲解项目不变；重复运行会重建目录。
- 验证：先红后绿。

### Task 2：渲染核对记录（AC1、AC4）

- 文件：`scripts/render_brief.py`、`tests/test_render.py`。
- 用例：`complete` 时附录有「交叉核对记录」折叠块、逐条显示结论与说明，页脚一行摘要（发现数、成立已改、不成立、没核实）；
  `incomplete` 时页脚写「交叉核对没有完成：原因」；缺字段、`verdict` 取值不对时退出 2 并点名；不给参数时没有任何核对标记且两次渲染去掉时间后逐字相同。
- 验证：先红后绿。

### Task 3：审查模板与命令文件（AC3、AC5）

- 文件：`references/cross-check-prompt.md`、`commands/brief.md`（新增第 4.5 步与 `--cross-check` 参数说明）、`tests/test_rules_doc.py`。
- 内容：没装 delegate 时跳过并说明；准备材料、调用 `delegate:review`、读报告；逐条回到代码核实并标 `verdict`；只改 `confirmed`；复检；
  写 `crosscheck.json`；失败照实记；删除材料目录；规模报告里加预计花费一句。
- 验证：新参数在脚本 `--help` 里；模板不含生成方结论用语（测试）。

### Checkpoint 1（report）：完整检查

- 两个 Python 版本跑全部测试；`claude plugin validate .`。

### Task 4：真实交叉核对一次（AC6）

- 对 `~/.claude/delivery-brief/sgclone/usage-draft.md`（module-brief 的第 2 次生成）照命令文件第 4.5 步跑：建材料、`/delegate:review`、逐条核实、改讲解、复检、渲染。
- 记录：发现条数、`confirmed`／`rejected`／`unverified` 各几条、和样张对照时漏掉的 3 条（没有 python3 时静默跳过、草案目录不可读时预览抛错、
  add-module 后忘归里程碑不被拦）找回了几条、delegate 报告的花费。浏览器自验核对记录的显示。

### Task 5：M1 发版准备（AC7 的文件部分）

- 文件：`README.md`（从用法草案展开：安装、两种参数、`--cross-check`、`--no-open`、输出位置、范围推断与已知局限、一张讲解页截图）、
  `LICENSE`（MIT）、`plugins/delivery-brief/.claude-plugin/plugin.json`（0.1.0、license 字段）、README 截图文件。
- 验证：`claude plugin validate .` 与 `claude plugin validate plugins/delivery-brief --profile directory` 都通过。

### Checkpoint 2（gate）：本机安装插件

- 停下问你：用 `claude plugin marketplace add <本仓库路径>` 与 `claude plugin install delivery-brief@delivery-brief-marketplace` 装到本机
  （这会改 Claude Code 的全局插件配置）。你同意后我执行并读回安装状态。

### Task 6：端到端两次（AC7 的运行部分）

- 新装的插件要新会话才加载，所以请你在本仓库目录开一个新会话，依次输入两条命令：`/delivery-brief:brief brief-facts`、
  `/delivery-brief:brief brief-facts --cross-check`。我核对两次的产物（检查脚本、页面自验、核对记录）。

### Checkpoint 3（gate）：最终验收与发版授权

- 呈现 AC1–AC8 证据、改动表、提交表、偏离计划处、拟回告原文。
- 同一停点分三项问你，各自单独回答：**建远端仓库**（`gh repo create haigeerlab/delivery-brief --public`，并把本仓库设为 origin）；
  **推送** `main`；**打标签** `v0.1.0` 并推送标签。只做你同意的那几项。

### 发版（按 Checkpoint 3 的授权）

- 依次执行已同意的项并读回结果（远端可见、`main` 与标签指向的提交）；把本机安装的来源改为远端前先问你；回告 ecosystem-lead：
  版本、标签对应的提交、安装情况、改了什么。任一步失败就停下说明。

## Files likely touched

- 新增：`plugins/delivery-brief/scripts/crosscheck_material.py`、`plugins/delivery-brief/references/cross-check-prompt.md`、
  `plugins/delivery-brief/tests/test_material.py`、`LICENSE`、README 截图（`docs/images/`）。
- 修改：`plugins/delivery-brief/scripts/render_brief.py`、`plugins/delivery-brief/commands/brief.md`、`plugins/delivery-brief/tests/{test_render,test_rules_doc}.py`、
  `README.md`、`plugins/delivery-brief/.claude-plugin/plugin.json`。
- 记录：本 Plan、`tasks/cross-check/todo.md`。
- 仓库外：讲解与材料写在 `~/.claude/delivery-brief/`；Checkpoint 2 后改 Claude Code 全局插件配置；Checkpoint 3 后在 GitHub 建仓库。
- 新增依赖、锁文件：无。

## 风险

- **delegate 报告格式变化**：只读报告里 `findings`、`unreviewed`、`execution_status`、`observed_models` 几个字段；读不到就记 `incomplete`，不猜。
- **花费**：Task 4 一次约 10 万输入 token，花在 Codex 额度上；你在 Task 6 的第二条命令再花一次。
- **端到端要新会话**：本会话不会加载新装的插件，所以 Task 6 需要你动手；两条命令的产物我来核对。
- **公开仓库**：建成公开后，仓库里的 Spec、Plan、todo 都公开可见；里面有其他插件的名字（spec-guard、delegate 等公开插件）和本机路径片段
  （例如 scratchpad 路径），Checkpoint 3 前我扫一遍并列给你，要删的先删。

## 预先声明

- Public paths: 无
- Dependencies: 无
- Configs: 无
- Patches: 无
