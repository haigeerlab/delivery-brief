# Todo: ui-screenshots

- [x] Task 0：提交 Plan 与 todo — 2026-11-19 用户批准 Plan（「批准」）。
- [x] Task 1：截图块的解析与检查 — `brief_markdown.screenshot_blocks`（截图块仍是 `code` 块，`lang` 为 `screenshot`，由这个函数取出标题、路径、行号，含折叠块里的；和 `output_blocks` 一个写法，比 Plan 写的「独立块类型」改动小）；`check_brief.check_screenshots`：只能在产出清单、要有页面名、路径以 `/` 开头且不含空白与 `..`、最多 8 张。`test_markdown.py` 新增 2 例、`test_check.py` 新增 2 例，实现前 2 例报错 1 例失败，实现后解析与检查 59 例全过。
- [x] Task 2：截图脚本 — `take_screenshots.py`：按 `--chrome`→`DELIVERY_BRIEF_CHROME`→本机安装→PATH 找 Chrome（指定了就不再往下找）；等地址可访问；每张先 HTTP GET 记状态码与最终地址，再 `--headless=new --screenshot`（缩放固定 1、单张 60 秒、新进程组，超时整组杀掉），配置目录 `delivery-brief-chrome-*` 用完即删；先清旧 PNG；写 `shots.json`；始终退出 0，参数错误退出 2。`test_screenshots.py` 7 例（`http.server` 静态页面：两页成功且 1280×800、404 照截并记原因且不影响另一张、清旧 PNG、地址不可访问、`--chrome` 与环境变量指向不存在、没有截图块、参数错误），实现前模块不存在全部报错，实现后 Homebrew 3.10.7 与系统 3.9.6 都过（约 9 秒）。另实截一张含中文的本机页面，打开图片看过：标题与中文正常。
- [x] Task 3：渲染截图 — `render_brief.py --shots`（校验 `shots.json`：`baseUrl`、`origin`、每张的 `title`／`path`／`file`／`status`／`reason`，写坏退出 2 点名字段）与 `--shots-skipped`；第 n 个截图块配第 n 条记录且路径要一致，否则写「截图记录和讲解对不上」；`ok` 出带标题的图（相对路径，写死宽高，不懒加载），其余出「截图未生成：原因」；附录加截图来源与成功张数（导出目录或你给的地址，后者注明未核对）。截图脚本加 `--origin`。`test_render.py` 新增 6 例，实现前 6 例失败，实现后 60 例（渲染＋截图）全过。
  - 改动前后对照：用改动前（`5b6eca9`）与改动后的渲染脚本渲染同一份真实讲解（brief-facts，含交叉核对），去掉生成时间后逐字相同（83390 字节）。
  - UI 自验：在 brief-facts 讲解的产出清单里加两个截图块（静态页 `/` 与 404 的 `/admin`），截图、检查（0 错误 0 提醒）、模拟看图改判 `/admin` 为失败后渲染，用本机静态服务在浏览器打开：桌面宽度图片 918px 宽、提示框写「后台（/admin）：截图未生成：页面返回 HTTP 404，截到的是报错页」、附录有截图来源；手机宽度 375 下图片 313×196、无横向溢出。自验中发现 `loading="lazy"` 时图片未加载前宽度只有 2px，改为写死宽高、去掉懒加载后复验正常。
- [x] Task 4：命令文件与讲解规则 — `commands/brief.md`：参数提示加 `--no-screenshots`、`--base-url`；开头的授权写明截图装依赖、起服务的例外；第 2 步加截图的预计耗时；第 3 步重生成时连 `$NAME.shots` 一起删；新增「4.6 截图」八小步（两个参数、找启动方式的顺序、导出与按锁文件装依赖、不复用 `node_modules` 不复制 `.env`、新进程组后台起服务与端口规则、截图、逐张看图改判且不替用户登录不输入账号密码不点击、收尾停进程组删目录查端口）；第 5 步渲染加 `--shots`／`--shots-skipped`；第 6 步报截图结果与耗时。`references/brief-rules.md`：产出清单的截图块写法与示例、最多 8 个、没界面写「本模块无界面」、要登录也照写不改路径。`test_rules_doc.py` 新增 2 例并把 `take_screenshots.py` 纳入「命令里的参数都在 `--help` 里」，实现前 2 失败 1 报错，实现后 11 例全过。
- [ ] Checkpoint 1（report）：完整检查
- [ ] Task 5：真实运行一次
- [ ] Task 6：M2 发版准备
- [ ] Checkpoint 2（gate）：本机升级插件
- [ ] Task 7：端到端一次
- [ ] Checkpoint 3（gate）：最终验收与发版授权
