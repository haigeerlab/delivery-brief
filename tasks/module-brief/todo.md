# Todo: module-brief

- [x] Task 0：提交 Plan 与 todo — 2026-11-19 用户批准 Plan（「批准」）。
- [x] Task 1：Markdown 子集解析 — `brief_markdown.py`：标题、段落（中英文续行拼接）、两层列表（第三层成 `unsupported`）、表格（`\|` 转义）、代码与 mermaid、`<details>` 折叠、其余写法成 `unsupported` 保留原文；行内：行内代码、粗体、链接、引用 `[[path:L起-L止]]` 与写坏的 `badcite`，代码里的引用不算；`citations`、`sections` 帮手。`test_markdown.py` 13 例，实现前模块不存在报错，实现后 49 例全过（两个 Python 版本）。
- [x] Task 2：检查脚本 — `check_brief.py`：六节齐全与顺序；引用在终点提交上存在、行号不越界、写法正确；实跑输出块 ```output O<n>（首行 `$ 命令`）与 `[[out:O<n>]]` 引用；AC 表逐行有证据且覆盖 Spec 的全部编号 AC；「需要你判断的」每条有证据；阅读路线为 3～7 条有序列表且每条有引用；分层 3～7 层；正文提交号须在范围内（允许范围端点、HEAD、终点后的模块提交与 Spec 指纹）；不支持写法、附录内容、多出的节只提醒。范围内补充：Plan 没写实跑输出的标记法，定为 ```output O1 与 `[[out:O1]]`，解析器加 `outref` 与 `output_blocks`（+2 例）。`test_check.py` 18 例，实现前 17 例失败，实现后 69 例全过（两个 Python 版本）。
- [ ] Task 3：渲染脚本
- [ ] Task 4：讲解规则与命令文件
- [ ] Task 5：文档
- [ ] Checkpoint 1（report）：完整检查
- [ ] Task 6：真实生成一：spec-guard usage-draft
- [ ] Task 7：真实生成二：本仓库 brief-facts
- [ ] Checkpoint 2（gate）：最终验收
