# Todo: ui-screenshots

- [x] Task 0：提交 Plan 与 todo — 2026-11-19 用户批准 Plan（「批准」）。
- [x] Task 1：截图块的解析与检查 — `brief_markdown.screenshot_blocks`（截图块仍是 `code` 块，`lang` 为 `screenshot`，由这个函数取出标题、路径、行号，含折叠块里的；和 `output_blocks` 一个写法，比 Plan 写的「独立块类型」改动小）；`check_brief.check_screenshots`：只能在产出清单、要有页面名、路径以 `/` 开头且不含空白与 `..`、最多 8 张。`test_markdown.py` 新增 2 例、`test_check.py` 新增 2 例，实现前 2 例报错 1 例失败，实现后解析与检查 59 例全过。
- [x] Task 2：截图脚本 — `take_screenshots.py`：按 `--chrome`→`DELIVERY_BRIEF_CHROME`→本机安装→PATH 找 Chrome（指定了就不再往下找）；等地址可访问；每张先 HTTP GET 记状态码与最终地址，再 `--headless=new --screenshot`（缩放固定 1、单张 60 秒、新进程组，超时整组杀掉），配置目录 `delivery-brief-chrome-*` 用完即删；先清旧 PNG；写 `shots.json`；始终退出 0，参数错误退出 2。`test_screenshots.py` 7 例（`http.server` 静态页面：两页成功且 1280×800、404 照截并记原因且不影响另一张、清旧 PNG、地址不可访问、`--chrome` 与环境变量指向不存在、没有截图块、参数错误），实现前模块不存在全部报错，实现后 Homebrew 3.10.7 与系统 3.9.6 都过（约 9 秒）。另实截一张含中文的本机页面，打开图片看过：标题与中文正常。
- [ ] Task 3：渲染截图
- [ ] Task 4：命令文件与讲解规则
- [ ] Checkpoint 1（report）：完整检查
- [ ] Task 5：真实运行一次
- [ ] Task 6：M2 发版准备
- [ ] Checkpoint 2（gate）：本机升级插件
- [ ] Task 7：端到端一次
- [ ] Checkpoint 3（gate）：最终验收与发版授权
