# Todo: milestone-brief

- [x] Task 0：提交 Plan 与 todo — 2026-11-19 用户批准 Plan（「批准」）。
- [x] Task 1：读里程碑行 — `facts_specguard.milestone_row(text, M)`：Milestones 表这一行的用法（编号与 `### U1: 标题`）、模块、`confirmed`（有 `<!-- spec-guard: milestone M confirmed` 行）；没有这一行或没有表返回 `None`。`test_specguard.py` 新增 3 例，实现前报错，实现后全过。
- [x] Task 2：`--milestone` 的范围与 `milestone` 字段 — `brief_facts.py`：`--milestone`（`M\d+`，与 `--module`、`--range` 三选一）、`--draft`（只能和 `--milestone` 一起）；`_draft_for` 选草案（一份不用指定、多份不指定退出 2 并列出、指错退出 3）；`milestone_facts` 对每个模块调 `infer_module_range`（warnings 加「模块 <id>：」），推断不出的记 `missing`，全部推断不出退出 3；按 `rev-list` 顺序取最早起点的父提交与最晚终点；未确认进 warnings；范围里改了这一站以外模块文件的提交进 warnings；`milestone` 字段只在 `--milestone` 时出现。新增 `test_milestone.py` 10 例，实现前 8 例失败（另 2 例参数错误本来就退出 2），实现后全过；模块范围的旧测试照常通过。
- [x] Task 3：`codeMap` 与字段文档 — `facts_git.list_files`；`brief_facts.code_map`：终点上的文件按前两层目录归组（一层目录取这一层、根下为 `.`），数新增（A／R／C）、修改（M／T）、未改、删除；只在 `--milestone` 时输出，`milestone` 也一样。`docs/facts-schema.md`：用法与退出码、「里程碑范围怎么推断」与已知局限、`range.source`／`inProgress`／`basis` 的里程碑取值、`milestone` 与 `codeMap` 字段表（模块的 `range.basis` 写一行「结构同 `range.basis`」）。`test_milestone.py` 新增 2 例（四种计数与根目录、模块 facts 没有这两个键），实现前 1 例报错；`test_schema_doc.py` 加一次 `--milestone` 运行，与文档两向比对通过。
- [x] Task 4：检查里程碑页 — `check_brief.py`：facts 有 `milestone` 时走 `run_milestone`（七节 `MILESTONE_SECTIONS`），原来的六节路径不动，`check_sections` 只加了参数。规则：用法表每个 `U<n>` 一行且有证据；走一遍是 3～10 步的有序列表，每步有引用且正文写出这一站的模块 id；约定每条引用两个不同文件，或只写「没有新约定」；代码地图、各模块讲解、附录里写表格或列表给提醒；提交号白名单加上各模块依据里的提交；截图块在里程碑页一律报错。`test_check.py` 新增 7 例，实现前全部失败，实现后 30 例全过（含模块页旧用例）。
- [x] Task 5：渲染里程碑页 — `render_brief.py`：facts 有 `milestone` 时用七节锚点与目录；页头写「里程碑讲解」、编号、典型用法与标题、模块数，标进行中／已确认／还没确认；「代码地图」节在 agent 的说明后插入脚本画的表（有改动的按改动数排在前，没改动的折叠），「各模块讲解」节插入模块表（输出目录里有 `<id>.html` 就相对链接，没有写「还没生成」与生成命令），两节里的占位文字「（由脚本生成）」不显示。模块页走原来的代码路径。`test_render.py` 新增 4 例，实现前 2 失败 2 报错，实现后 27 例全过。
  - 改前（`d30b73a`）改后渲染两份真实模块讲解（brief-facts 带交叉核对、next-shadcn 带截图），去掉生成时间后都逐字相同。
  - UI 自验：用本仓库 M1 的真实 facts（三个模块都已完成、M1 已确认、11 组目录）配一份简短源文件渲染，本机静态服务打开：页头「M1 · 典型用法 U1 模块交付后看讲解 · 3 个模块」「已确认」；目录 7 项；代码地图 11 行、新增着色；模块表里 brief-facts 链到 `brief-facts.html`，另两个写「还没生成」；桌面与手机宽度都无横向溢出。手机宽度下模块 id 与范围被挤成一字一行、职责里的反引号原样显示，改为这几列不换行、职责按行内格式渲染后复验正常。
- [x] Task 6：命令文件与讲解规则 — `commands/brief.md`：参数提示加 `--milestone <M> [--draft <草案>]`；第 1 步认 `--milestone`；新增「里程碑页」小节（`NAME=milestone-$M`、报告多说用法与模块状态、按里程碑读取策略先读成功标准再读已有模块页源文件、缺模块页只标出、给了 `--cross-check` 说明暂不支持并跳过 4.5、不截图跳过 4.6）。`references/brief-rules.md`：新增「里程碑页」一节（读者与目标、读取策略、七节模板、每节写法：用法表、代码地图只写怎么读、走一遍 3～10 步写出模块 id、约定引用两个不同文件或写「没有新约定」）。`test_rules_doc.py` 新增 2 例（规则里的七节模板与 `MILESTONE_SECTIONS` 一致、命令流程要素与参数在 `--help` 里），实现前 1 失败 1 报错，实现后 14 例全过。
- [ ] Checkpoint 1（report）：完整检查
- [ ] Task 7：真实生成一次
- [ ] Task 8：M3 发版准备
- [ ] Checkpoint 2（gate）：本机升级插件
- [ ] Task 9：端到端一次
- [ ] Checkpoint 3（gate）：最终验收与发版授权
