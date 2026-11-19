# Todo: brief-facts

- [x] Task 0：提交 Plan 与 todo — 2026-11-19 用户批准 Plan（「批准」），本提交记录批准标记。
- [x] Task 1：插件骨架 — marketplace、plugin.json（版本 0.0.0，M1 发版时定）、README「开发中」、.gitignore；`claude plugin validate .` 与插件目录均通过（README 缺安装行只是建议，M1 补）。
- [x] Task 2：显式提交段的事实 — `facts_git.py`（-z 解析、重命名、二进制、根提交用空树）与 `brief_facts.py`（`--range`、退出码 2／3／4、一行中文错误）；`test_range.py` 7 例，实现前因脚本不存在全部报错，实现后通过（Homebrew 3.10 与系统 3.9.6 各一次），每例比对工作区与 ref 不变。
- [ ] Task 3：spec-guard 文件解析
- [ ] Task 4：模块范围推断
- [ ] Task 5：链接基址
- [ ] Task 6：文档
- [ ] Checkpoint 1（report）：完整检查与实测
- [ ] Checkpoint 2（gate）：最终验收
