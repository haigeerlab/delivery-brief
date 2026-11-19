# Todo: milestone-brief

- [x] Task 0：提交 Plan 与 todo — 2026-11-19 用户批准 Plan（「批准」）。
- [x] Task 1：读里程碑行 — `facts_specguard.milestone_row(text, M)`：Milestones 表这一行的用法（编号与 `### U1: 标题`）、模块、`confirmed`（有 `<!-- spec-guard: milestone M confirmed` 行）；没有这一行或没有表返回 `None`。`test_specguard.py` 新增 3 例，实现前报错，实现后全过。
- [x] Task 2：`--milestone` 的范围与 `milestone` 字段 — `brief_facts.py`：`--milestone`（`M\d+`，与 `--module`、`--range` 三选一）、`--draft`（只能和 `--milestone` 一起）；`_draft_for` 选草案（一份不用指定、多份不指定退出 2 并列出、指错退出 3）；`milestone_facts` 对每个模块调 `infer_module_range`（warnings 加「模块 <id>：」），推断不出的记 `missing`，全部推断不出退出 3；按 `rev-list` 顺序取最早起点的父提交与最晚终点；未确认进 warnings；范围里改了这一站以外模块文件的提交进 warnings；`milestone` 字段只在 `--milestone` 时出现。新增 `test_milestone.py` 10 例，实现前 8 例失败（另 2 例参数错误本来就退出 2），实现后全过；模块范围的旧测试照常通过。
- [ ] Task 3：`codeMap` 与字段文档
- [ ] Task 4：检查里程碑页
- [ ] Task 5：渲染里程碑页
- [ ] Task 6：命令文件与讲解规则
- [ ] Checkpoint 1（report）：完整检查
- [ ] Task 7：真实生成一次
- [ ] Task 8：M3 发版准备
- [ ] Checkpoint 2（gate）：本机升级插件
- [ ] Task 9：端到端一次
- [ ] Checkpoint 3（gate）：最终验收与发版授权
