# Todo: milestone-brief

- [x] Task 0：提交 Plan 与 todo — 2026-11-19 用户批准 Plan（「批准」）。
- [x] Task 1：读里程碑行 — `facts_specguard.milestone_row(text, M)`：Milestones 表这一行的用法（编号与 `### U1: 标题`）、模块、`confirmed`（有 `<!-- spec-guard: milestone M confirmed` 行）；没有这一行或没有表返回 `None`。`test_specguard.py` 新增 3 例，实现前报错，实现后全过。
- [x] Task 2：`--milestone` 的范围与 `milestone` 字段 — `brief_facts.py`：`--milestone`（`M\d+`，与 `--module`、`--range` 三选一）、`--draft`（只能和 `--milestone` 一起）；`_draft_for` 选草案（一份不用指定、多份不指定退出 2 并列出、指错退出 3）；`milestone_facts` 对每个模块调 `infer_module_range`（warnings 加「模块 <id>：」），推断不出的记 `missing`，全部推断不出退出 3；按 `rev-list` 顺序取最早起点的父提交与最晚终点；未确认进 warnings；范围里改了这一站以外模块文件的提交进 warnings；`milestone` 字段只在 `--milestone` 时出现。新增 `test_milestone.py` 10 例，实现前 8 例失败（另 2 例参数错误本来就退出 2），实现后全过；模块范围的旧测试照常通过。
- [x] Task 3：`codeMap` 与字段文档 — `facts_git.list_files`；`brief_facts.code_map`：终点上的文件按前两层目录归组（一层目录取这一层、根下为 `.`），数新增（A／R／C）、修改（M／T）、未改、删除；只在 `--milestone` 时输出，`milestone` 也一样。`docs/facts-schema.md`：用法与退出码、「里程碑范围怎么推断」与已知局限、`range.source`／`inProgress`／`basis` 的里程碑取值、`milestone` 与 `codeMap` 字段表（模块的 `range.basis` 写一行「结构同 `range.basis`」）。`test_milestone.py` 新增 2 例（四种计数与根目录、模块 facts 没有这两个键），实现前 1 例报错；`test_schema_doc.py` 加一次 `--milestone` 运行，与文档两向比对通过。
- [x] Task 4：检查里程碑页 — `check_brief.py`：facts 有 `milestone` 时走 `run_milestone`（七节 `MILESTONE_SECTIONS`），原来的六节路径不动，`check_sections` 只加了参数。规则：用法表每个 `U<n>` 一行且有证据；走一遍是 3～10 步的有序列表，每步有引用且正文写出这一站的模块 id；约定每条引用两个不同文件，或只写「没有新约定」；代码地图、各模块讲解、附录里写表格或列表给提醒；提交号白名单加上各模块依据里的提交；截图块在里程碑页一律报错。`test_check.py` 新增 7 例，实现前全部失败，实现后 30 例全过（含模块页旧用例）。
- [ ] Task 5：渲染里程碑页
- [ ] Task 6：命令文件与讲解规则
- [ ] Checkpoint 1（report）：完整检查
- [ ] Task 7：真实生成一次
- [ ] Task 8：M3 发版准备
- [ ] Checkpoint 2（gate）：本机升级插件
- [ ] Task 9：端到端一次
- [ ] Checkpoint 3（gate）：最终验收与发版授权
