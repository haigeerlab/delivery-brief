# Plan: milestone-brief

<!-- spec-guard: review pending -->

依据 [`spec/milestone-brief.md`](../../spec/milestone-brief.md)（2026-11-19 用户在本会话批准：「批准；Q1 A；Q2 A」）。
分支 `main`，串行，在本会话做。本模块完成即 M3 与整个能力图，版本 0.3.0。

## Overview

按「事实 → 检查 → 渲染 → 命令与规则」的顺序做，每块先写失败的测试：先让 `brief_facts.py --milestone` 给出范围并集、`milestone` 与
`codeMap`；再让检查脚本和渲染脚本认出里程碑页（七节）且模块页一字不变；然后写命令文件与讲解规则。之后对本仓库 M1 真实生成一次里程碑页。
最后做 M3 发版准备，在本机升级前停下问你；升级后你在新会话端到端跑一次，最终验收时逐项问推送、打标签，再按停点问 M3。

## Architecture Decisions

1. **参数**：`--milestone <M>` 与 `--module`、`--range` 三选一；`--draft <路径>` 只和 `--milestone` 一起用。里程碑编号要像 `M1`（字母 M 加数字），
   否则退出 2。
2. **读草案在 `facts_specguard.py`**：新函数 `milestone_row(drafts, milestone)` 返回 `{file, milestone, usages: [{id, title}], modules, confirmed}`；
   典型用法的标题取 `### U1: <标题>`；`confirmed` 看草案里有没有 `<!-- spec-guard: milestone <M> confirmed` 开头的行（不跳过注释，这一行就是注释）。
3. **范围并集在 `brief_facts.py`**：对每个模块调用现有的 `infer_module_range`（每个模块的 warnings 加上「模块 <id>：」前缀）；用
   `git rev-list --reverse --topo-order HEAD` 的位置比先后：起点取位置最小的模块起点的父提交，终点取位置最大的模块终点。
   模块不在能力图上或没有提交时不中断，该模块状态记 `missing`、进 warnings；全部模块都 `missing` 时退出 3。
   顶层 `module` 为 `null`，`usageDraft` 为 `null`，新增 `milestone`。`range.source` 为 `inferred-spec-guard-milestone`，`range.basis` 为 `null`（各模块的依据在 `milestone.modules[].range.basis`）。
4. **`codeMap` 在 `facts_git.py` 与 `brief_facts.py`**：`git ls-tree -r --name-only <终点>` 列出终点的所有文件；按路径前两段归组（三段以上取前两段目录，
   两段取第一段目录，根下文件归 `.`）；每组数新增（`A`、`R`、`C`）、修改（`M`、`T`）、未改的文件数，另数删除（`D`，终点上已不存在）。按路径排序输出。
   只在 `--milestone` 时生成，模块页的 facts 不变。
5. **检查脚本按 facts 选规则**：有 `milestone` 时用里程碑页的七节 `MILESTONE_SECTIONS`，否则用原来的六节，原来的规则代码不动。里程碑页规则：
   - 「这一站做成了什么」要有一张表，`milestone.usages` 的每个编号各占一行且带证据；
   - 「沿典型用法走一遍」是有序列表 3～10 项，每项带引用、写出 `milestone.modules` 里的一个模块 id；
   - 「跨模块约定」每项至少两处引用且是两个不同文件，或者整节只写「没有新约定」；
   - 「需要你判断的」沿用模块页的规则；「代码地图」「各模块讲解」「附录」由脚本生成，写了表格或列表给提醒；
   - 引用、实跑输出、提交号白名单（加上各模块的起止提交）沿用。
6. **渲染**：有 `milestone` 时页头写「<M> 里程碑讲解」、典型用法、模块数、范围，标「进行中」或「已确认」；「代码地图」一节在 agent 的说明之后插入
   脚本画的表（目录、新增、修改、未改、删除，按改动数着色，有改动的行在前、没改的折叠）；「各模块讲解」一节插入模块表：模块、职责、范围、状态、讲解页
   （输出目录里有 `<id>.html` 就用相对链接，没有写「还没生成」与 `/delivery-brief:brief <id>`）。没有 `milestone` 时走原来的代码路径，模块页逐字不变。
7. **命令文件**：第 1 步认 `--milestone`（`NAME=milestone-<M>`）；给了 `--cross-check` 就说明「里程碑页暂不支持交叉核对」照常生成（Q2 A）；
   不做截图；第 3 步按里程碑页的读取策略：先读各模块 Spec 的成功标准与已有的模块页源文件（`<id>.md`），再读模块之间接口处的代码。
8. **讲解规则**：新增「里程碑页」一节，写七节各写什么、走一遍怎么选用法、约定怎么认定、证据规则同模块页。

## Task List

### Task 0：提交 Plan 与 todo

### Task 1：读里程碑行（AC1 的草案部分）

- 文件：`scripts/facts_specguard.py`、`tests/test_specguard.py`。
- 用例：读出用法编号与标题、模块列表、`confirmed` 真与假；里程碑不存在返回 `None`；草案缺 Milestones 表进 warnings。
- 验证：先红后绿。

### Task 2：`--milestone` 的范围与 `milestone` 字段（AC1）

- 文件：`scripts/brief_facts.py`、`tests/test_milestone.py`（新）。
- 用例（夹具：能力图三个模块，草案 M1 = alpha、beta，M2 = gamma；alpha、beta 都做完，gamma 进行中）：
  - `--milestone M1` 的 base 是 alpha 起点的父提交、head 是 beta 的终点；提交与文件是这一段的；`milestone.modules` 两项状态 `done`；未确认时进 warnings。
  - 草案加确认行后 `confirmed: true`、不再有这条 warning。
  - `--milestone M2`：gamma 进行中，页头要的 `range.inProgress` 为真，warnings 带「模块 gamma：」。
  - 多份草案不给 `--draft` 退出 2；`--draft` 指错、里程碑不存在退出 3；`--milestone m1` 退出 2；都是一行中文。
  - 运行前后夹具仓库不变（沿用快照）。
- 验证：先红后绿。

### Task 3：`codeMap` 与字段文档（AC1、AC2）

- 文件：`scripts/facts_git.py`、`scripts/brief_facts.py`、`docs/facts-schema.md`、`tests/test_milestone.py`、`tests/test_schema_doc.py`。
- 用例：新增、修改、未改、删除各自计数正确（夹具里各造一个）；根下文件归 `.`；`--module` 的 facts 里没有 `codeMap` 与 `milestone`。
  字段文档测试加一次 `--milestone` 运行，三次运行的字段并集与文档对得上。
- 验证：先红后绿。

### Task 4：检查里程碑页（AC3）

- 文件：`scripts/check_brief.py`、`tests/test_check.py`。
- 用例：合格的里程碑页 0 错误 0 提醒；缺节、顺序错、某个用法没有一行、用法那行没证据、走一遍 2 项或 11 项、某步没引用或没写模块 id、
  约定只有一处引用或两处同一文件，都报错；「没有新约定」通过；模块页的全部旧用例照常通过。
- 验证：先红后绿。

### Task 5：渲染里程碑页（AC4）

- 文件：`scripts/render_brief.py`、`tests/test_render.py`。
- 用例：页头写里程碑、用法、模块数；进行中与已确认的标签；代码地图的数字与 `codeMap` 一致、未改的目录在折叠里；模块表里存在的模块页是相对链接、
  不存在的写「还没生成」和命令；模块页两次渲染与改前的期望一致（除生成时间）。另用改前、改后的渲染脚本渲染同一份真实模块讲解，逐字比对。
- UI 自验：在浏览器里打开一个夹具生成的里程碑页（桌面与手机宽度）。
- 验证：先红后绿。

### Task 6：命令文件与讲解规则（AC5）

- 文件：`commands/brief.md`、`references/brief-rules.md`、`tests/test_rules_doc.py`。
- 用例：参数提示有 `--milestone` 与 `--draft`，命令里用到的参数都在 `brief_facts.py --help` 里；命令写明暂不支持交叉核对、不截图、缺的模块页只标出；
  规则里的里程碑页模板七节与检查脚本的 `MILESTONE_SECTIONS` 一致。
- 验证：先红后绿。

### Checkpoint 1（report）：完整检查

- 两个 Python 版本全部测试；`claude plugin validate .`。结果记进 todo。

### Task 7：真实生成一次（AC6）

- 对本仓库 `--milestone M1`（三个模块，diff 约 24 万字节，会到规模停点；本次由我手工执行，按 Plan 授权继续，记录这一点）照命令文件做：
  记录读了哪些文件、检查几次、错误是什么；浏览器自验（桌面与手机宽度，代码地图、模块表链接能点开 brief-facts 模块页）；本仓库运行前后不变。

### Task 8：M3 发版准备（AC7 的文件部分）

- README「用法」加 `--milestone`、`--draft` 与一段里程碑页说明；能力图全部完成后的收尾：「后续计划」改为当前状态与已知局限。`plugin.json` 0.3.0。
  `claude plugin validate .`。

### Checkpoint 2（gate）：本机升级插件

- 停下问你；升级后读回版本与提交号，逐文件比对缓存。

### Task 9：端到端一次（AC7 的运行部分）

- 你在新会话运行 `/delivery-brief:brief --milestone M1 --project ~/Documents/haigeerlab/delivery-brief`；我核对产物与本仓库不变。

### Checkpoint 3（gate）：最终验收与发版授权

- 呈现 AC1–AC7 的证据、改动表、提交表、偏离、拟回告原文、能力图完成后的收尾文档建议；逐项问推送 `main`、打 `v0.3.0`。通过后按停点问 M3。

## Files likely touched

- 新增：`plugins/delivery-brief/tests/test_milestone.py`。
- 修改：`scripts/{brief_facts,facts_specguard,facts_git,check_brief,render_brief}.py`、`commands/brief.md`、`references/brief-rules.md`、
  `docs/facts-schema.md`、`tests/{test_specguard,test_schema_doc,test_check,test_render,test_rules_doc}.py`、`README.md`、`plugin.json`。
- 记录：本 Plan、`tasks/milestone-brief/todo.md`。
- 新增依赖、锁文件：无。

## 风险

- **模块页被改坏**：检查与渲染都要分支。缓解：原代码路径不动、只在有 `milestone` 时走新路径；改前改后逐字比对真实模块讲解。
- **范围并集包住别的模块的提交**：两个模块之间夹着别的里程碑的提交时，并集会把它们算进来。缓解：`milestone.modules[].range` 留每个模块自己的范围，
  夹在中间、属于别的模块的提交进 warnings（沿用混入提交的识别），文档写明。
- **里程碑范围大，读不完**：读取策略先读 Spec 成功标准与已有模块页；规模停点照旧。
- **「跨模块约定」难以机械判断**：检查只管证据形状（两处、两个文件），是否真是新约定由人判断；规则里写明。

## 预先声明

- Public paths: 无
- Dependencies: 无
- Configs: 无
- Patches: 无
