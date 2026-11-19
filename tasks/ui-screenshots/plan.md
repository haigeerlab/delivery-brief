# Plan: ui-screenshots

<!-- spec-guard: review approved -->

依据 [`spec/ui-screenshots.md`](../../spec/ui-screenshots.md)（2026-11-19 用户在本会话批准：「批准；Q1 A；Q2 A」）。
分支 `main`，串行，在本会话做。本模块完成即 M2，版本 0.2.0。

## Overview

先做三个确定性部分，各自先写失败的测试：讲解源文件里的截图块（解析与检查）、截图脚本、渲染截图。再改命令文件与讲解规则，写明
导出终点提交、装依赖、起服务、逐张看图、收尾的流程。然后对 `next-shadcn-dashboard-starter` 真实跑一次。之后做 M2 发版准备
（README、0.2.0），在本机升级插件前停下问你；升级后由你在新会话里端到端跑一次，我核对产物；最后验收，并逐项问你推送、打标签。

## Architecture Decisions

1. **截图块是一种带标题的代码块**：```` ```screenshot <页面名> ```` 里第一行是路径。`brief_markdown.py` 把它解析成独立的块类型
   `screenshot`（标题、路径、行号），和 `mermaid`、`output` 并列；它不是正文文字，所以不参与引用检查。
2. **检查规则放在 `check_brief.py`**：截图块只能在「产出清单」一节；路径以 `/` 开头、不含空白与 `..`；全文最多 8 个；页面名不能为空。都是错误。
3. **截图脚本只依赖标准库与本机 Chrome**：`take_screenshots.py --source --base-url --out [--chrome <路径>] [--width 1280 --height 800] [--wait 120]`。
   - 先等 `--base-url` 可访问（每秒一次 HTTP GET，任何 HTTP 状态都算服务起来了），超时则全部记失败。
   - 每张：`<Chrome> --headless=new --disable-gpu --hide-scrollbars --no-first-run --user-data-dir=<临时目录> --window-size=W,H --screenshot=<文件> <地址>`，
     单张 60 秒超时；文件不存在或不是 PNG 即失败。截图前先用一次 HTTP GET 记下状态码与跳转后的最终地址，状态码 ≥ 400 时照样截图但记在原因里，供 agent 判断。
   - 浏览器配置目录用 `tempfile.mkdtemp`，`finally` 里删除。
   - 输出 `shots.json`：`{"baseUrl", "chrome", "viewport": [W, H], "shots": [{"title", "path", "file", "status", "reason", "httpStatus", "finalUrl"}]}`；
     文件名按顺序 `01.png`、`02.png`……；每次运行先清空 `--out` 里的旧 PNG。始终退出 0，只有参数错误退出 2。
4. **agent 改判写回 `shots.json`**：看图后发现截到的不是要的页面，把那一项的 `status` 改成 `failed`、`reason` 写清楚。渲染脚本只认 `status`。
5. **渲染**：`render_brief.py --shots <shots.json>` 按「页面路径＋出现顺序」把截图块配到记录：`ok` 的画成 `<figure><img src="<名字>.shots/01.png" alt="页面名"><figcaption>`；
   其余画成「截图未生成：原因」的提示块。`--shots` 写坏退出 2 并点名字段。命令文件给了 `--no-screenshots` 时传 `--shots-skipped "指定了 --no-screenshots"`，统一出这句原因。
   附录加一行「截图来源」：终点提交的导出目录，或 `--base-url` 给的地址（附「未核对与终点提交一致」）。
6. **起服务的流程在命令文件里**，脚本不做：找启动方式（`.claude/launch.json` → `package.json` 的 `dev`／`start` → README）、`git archive` 导出终点提交到临时目录、
   按锁文件选装依赖命令、用 Python 找一个空闲端口、后台起服务并把进程组号记下、跑截图脚本、看图改判、`kill -- -<进程组>` 停服务、删导出目录。
   端口按框架传：有 `PORT` 环境变量的照传，Vite 类加 `--port`，`launch.json` 的端口优先。每一步的耗时记下来给第 6 步的回复。

## Task List

### Task 0：提交 Plan 与 todo

- 本 Plan 与 `tasks/ui-screenshots/todo.md`，批准标记 `pending`，等你批准。

### Task 1：截图块的解析与检查（AC2）

- 文件：`scripts/brief_markdown.py`、`scripts/check_brief.py`、`tests/test_markdown.py`、`tests/test_check.py`。
- 用例：截图块解析出标题、路径、行号；放在别的节、路径不以 `/` 开头或含 `..`、标题为空、第 9 个都报错；产出清单里 1～8 个合法的不报错。
- 验证：先红后绿；全部旧用例仍过。

### Task 2：截图脚本（AC1、AC5 的测试部分）

- 文件：`scripts/take_screenshots.py`、`tests/test_screenshots.py`。
- 用例（`http.server` 在临时目录起静态页面，端口取空闲端口）：
  - 两个页面都成功：`01.png`、`02.png` 存在、是 PNG、宽高为 1280×800（读 PNG 头）；`shots.json` 字段齐全。
  - 一个路径 404：照样截图，`httpStatus` 为 404；另一张不受影响。
  - 地址不可访问（`--wait 2`）：全部 `failed`，原因写「地址 … 在 2 秒内不可访问」。
  - `--chrome` 指向不存在的文件、或 `DELIVERY_BRIEF_CHROME` 指向不存在的文件：全部 `failed`，原因写「没有找到 Chrome」，退出 0、无堆栈。
  - 浏览器配置目录不残留（运行前后比对临时目录下 `delivery-brief-chrome-*`）。
  - 旧 PNG 被清掉。
  - 本机找不到 Chrome 时，要真截图的用例 `skipTest` 并写明原因。
- 验证：先红后绿；两个 Python 版本。

### Task 3：渲染截图（AC3）

- 文件：`scripts/render_brief.py`、`tests/test_render.py`。
- 用例：`ok` 出 `<img>` 与标题、相对路径正确；`failed` 出「截图未生成：原因」；不给 `--shots` 出「截图未生成：没有截图」；`--shots-skipped` 出给定原因；
  `shots.json` 写坏退出 2 并点名字段；不含截图块的讲解两次渲染（去掉时间）与加本功能前的期望片段相同；附录有截图来源一行。
- 验证：先红后绿。

### Task 4：命令文件与讲解规则（AC4）

- 文件：`commands/brief.md`、`references/brief-rules.md`、`tests/test_rules_doc.py`。
- 命令文件：参数 `--no-screenshots`、`--base-url`；第 2 步规模报告加预计耗时；新增「4.6 截图」一步，写明决策 6 的流程、逐张看图改判、不替用户登录、不输入凭据、
  缺不在版本库的文件时照实写原因不复制、`--base-url` 的说明、收尾必做；第 5 步渲染时传 `--shots`；第 6 步回复里报截图张数与耗时。
- 讲解规则：产出清单里有界面的页面写截图块（最多 8 个，挑这次新增或明显改动的页面），没界面写「本模块无界面」。
- 用例：命令文件的新参数出现在 `take_screenshots.py --help` 与 `render_brief.py --help` 里；命令文件含「不替用户登录」「停掉服务」「删掉导出目录」；规则里的截图块写法能被解析器认出。
- 验证：先红后绿。

### Checkpoint 1（report）：完整检查

- 两个 Python 版本全部测试；`claude plugin validate .`。结果记进 todo。

### Task 5：真实运行一次（AC5、AC6）

- 对 `~/Documents/gs/next-shadcn-dashboard-starter` 选一段改了页面的提交（选出后在 todo 写明范围与理由），照命令文件第 1～6 步做（在本会话里按命令文件手工执行，插件本机版本仍是 0.1.1）。
- 记录：启动命令、装依赖与起服务各花多久、截了几张、成功与失败张数及原因（预计碰到登录）；运行前后被讲解项目的 `git status`、ref 与工作区文件摘要不变；
  浏览器打开讲解页自验截图显示正常（截一张讲解页给你看）；导出目录、浏览器配置目录、服务进程都已清理（`ps` 核对）。
- 偏离：如果起不来，照实写原因，页面照常生成，也算完成（AC6）。

### Task 6：M2 发版准备（AC7 的文件部分）

- README：用法加两个参数与截图说明（临时目录、装依赖、几分钟、不替你登录）；后续计划去掉 ui-screenshots。`plugin.json` 版本 0.2.0。`claude plugin validate .`。

### Checkpoint 2（gate）：本机升级插件

- 停下问你：`claude plugin marketplace update delivery-brief-marketplace` 与 `claude plugin update delivery-brief@delivery-brief-marketplace --scope user`；
  升级后读回 `installed_plugins.json` 的版本与提交号，并逐文件比对缓存与仓库。

### Task 7：端到端一次（AC7 的运行部分）

- 你在新会话里运行 `/delivery-brief:brief <Task 5 的范围> --project ~/Documents/gs/next-shadcn-dashboard-starter`；我核对产物（截图文件、`shots.json`、讲解页、
  被讲解项目不变、没有残留进程与目录）。

### Checkpoint 3（gate）：最终验收与发版授权

- 呈现：AC1–AC7 的证据、改动表、提交表、偏离计划处、拟回告 ecosystem-lead 的原文；然后逐项问：推送 `main`、打 `v0.2.0` 并推送。
- 通过后 M2 的模块都完成了，按 spec-guard 的里程碑停点问你 M2 是否通过。

## Files likely touched

- 新增：`plugins/delivery-brief/scripts/take_screenshots.py`、`plugins/delivery-brief/tests/test_screenshots.py`。
- 修改：`scripts/{brief_markdown,check_brief,render_brief}.py`、`commands/brief.md`、`references/brief-rules.md`、
  `tests/{test_markdown,test_check,test_render,test_rules_doc}.py`、`README.md`、`plugins/delivery-brief/.claude-plugin/plugin.json`。
- 记录：本 Plan、`tasks/ui-screenshots/todo.md`。
- 新增依赖、锁文件：无（本仓库）。Task 5 会在临时目录里按被讲解项目的锁文件装它的依赖，不进本仓库、不进被讲解项目。

## 风险

- **页面要登录**：实测项目大概率只截到登录页。缓解：agent 看图改判、照实写原因；不替用户登录（Spec 边界）。
- **装依赖慢或要网络**：pnpm 有本机仓库缓存，通常一两分钟；没网时装不上，照实记失败。规模报告预告耗时。
- **起服务要不在版本库里的环境变量**：起不来时写清缺什么，不复制 `.env.local`（Spec 边界，要复制先问）。
- **服务进程没停干净**：起服务时用新进程组，收尾按进程组停；Task 5 用 `ps` 核对。
- **Chrome 无界面模式的输出变化**：只依赖「写出 PNG 文件」这一结果，不解析它的输出文字。

## 预先声明

- Public paths: 无
- Dependencies: 无
- Configs: 无
- Patches: 无
