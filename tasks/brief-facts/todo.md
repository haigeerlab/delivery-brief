# Todo: brief-facts

- [x] Task 0：提交 Plan 与 todo — 2026-11-19 用户批准 Plan（「批准」），本提交记录批准标记。
- [x] Task 1：插件骨架 — marketplace、plugin.json（版本 0.0.0，M1 发版时定）、README「开发中」、.gitignore；`claude plugin validate .` 与插件目录均通过（README 缺安装行只是建议，M1 补）。
- [x] Task 2：显式提交段的事实 — `facts_git.py`（-z 解析、重命名、二进制、根提交用空树）与 `brief_facts.py`（`--range`、退出码 2／3／4、一行中文错误）；`test_range.py` 7 例，实现前因脚本不存在全部报错，实现后通过（Homebrew 3.10 与系统 3.9.6 各一次），每例比对工作区与 ref 不变。
- [x] Task 3：spec-guard 文件解析 — `facts_specguard.py`：能力图行与 Build order、Spec 批准标记与 AC（含续行、跳过围栏）、todo 项与 gate／report／延期、用法草案里程碑与入口（写坏的草案进 warnings）；`test_specguard.py` 9 例，实现前模块不存在报错，实现后 16 例全过（两个 Python 版本）。
- [x] Task 4：模块范围推断 — `brief_facts.py --module`：起点、终点按 Spec 假设 4；`range.basis` 写起止提交与规则，另给 `laterModuleCommits`（终点之后仍改模块文件的提交）与 `openItemsAtHead`，有则进 warnings；混入别的模块文件的提交进 warnings；模块 id 非 kebab-case 退出 2，没有能力图、模块不在能力图上、没有提交退出 3。`test_module_range.py` 9 例，实现前 9 例失败，实现后 26 例全过（两个 Python 版本）。变异（草稿副本，终点改成「最后一次改 todo」）→ 4 例失败。范围内修正：spec-guard 的 map-extra-columns 的成功标准没有 AC 编号，实测读出 0 条，改为按条目顺序列出并标 `acsNumbered: false`、进 warnings（+1 例）。偏离 Spec 的补充：`laterModuleCommits`、`openItemsAtHead`、`acsNumbered` 三个字段是 Spec 没列的新增字段，只增不改，用来如实说出推断的局限（中途 gate 与发版收尾分不开）。
- [ ] Task 5：链接基址
- [ ] Task 6：文档
- [ ] Checkpoint 1（report）：完整检查与实测
- [ ] Checkpoint 2（gate）：最终验收
