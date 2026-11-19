# Todo: ui-screenshots

- [x] Task 0：提交 Plan 与 todo — 2026-11-19 用户批准 Plan（「批准」）。
- [x] Task 1：截图块的解析与检查 — `brief_markdown.screenshot_blocks`（截图块仍是 `code` 块，`lang` 为 `screenshot`，由这个函数取出标题、路径、行号，含折叠块里的；和 `output_blocks` 一个写法，比 Plan 写的「独立块类型」改动小）；`check_brief.check_screenshots`：只能在产出清单、要有页面名、路径以 `/` 开头且不含空白与 `..`、最多 8 张。`test_markdown.py` 新增 2 例、`test_check.py` 新增 2 例，实现前 2 例报错 1 例失败，实现后解析与检查 59 例全过。
- [ ] Task 2：截图脚本
- [ ] Task 3：渲染截图
- [ ] Task 4：命令文件与讲解规则
- [ ] Checkpoint 1（report）：完整检查
- [ ] Task 5：真实运行一次
- [ ] Task 6：M2 发版准备
- [ ] Checkpoint 2（gate）：本机升级插件
- [ ] Task 7：端到端一次
- [ ] Checkpoint 3（gate）：最终验收与发版授权
