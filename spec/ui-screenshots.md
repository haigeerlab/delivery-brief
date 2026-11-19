# Spec: ui-screenshots

<!-- spec-guard: review approved 7c0cf63cc589 -->

## 目标

讲一个改了界面的模块时，讲解页「产出清单」里的页面各附一张截图，读者不用自己起项目就能看到这次做出来的样子。
起不来、截不到、截到的不是要的页面时，页面照常生成，在该页面的位置写明「截图未生成：原因」。

对外接口与用法草案 `spec/usage/delivery-brief.md` 一致：入口表「截图（自动）」一行（M2），U2「命令按项目的启动方式起开发服务器，
产出清单里的页面各附一张截图；服务起不来时页面照样生成，写明『截图未生成』和原因」。
与草案的差异：多了两个参数——`--no-screenshots`（跳过截图）和 `--base-url <地址>`（用你已经在跑的服务，不另起）。草案没写，属于补充。

给谁用：讲前端（或任何有网页界面的）模块的用户。

## 假设

1. **截图用本机 Chrome 的无界面模式**：`--headless=new --screenshot`，不装 Playwright 这类新依赖。实测本机 Chrome 157 截一张本机页面约 4 秒。
   找浏览器的顺序：环境变量 `DELIVERY_BRIEF_CHROME`、macOS 的 Google Chrome 与 Chromium、PATH 上的 `google-chrome`／`chromium`。都没有时整页写「截图未生成：没有找到 Chrome」。
   只截一屏（默认 1280×800），不截整页长图；每张用独立的临时浏览器配置目录，用完删掉。
2. **在终点提交上起服务，不碰被讲解项目**：沿用 module-brief「实跑只在 `git archive` 导出的临时目录里跑」。导出终点提交后，在临时目录里
   按锁文件装依赖（`pnpm install --frozen-lockfile`、`npm ci`、`yarn install --frozen-lockfile`，按锁文件种类选），再起开发服务器。
   不复用项目自己的 `node_modules`：开发服务器会往里面写缓存（如 Vite 的 `node_modules/.vite`），复用就写了被讲解项目。
3. **启动方式由生成讲解的 agent 判断，脚本只做机械的部分**：agent 按这个顺序找启动方式——项目的 `.claude/launch.json`、`package.json` 的
   `dev`／`start` 脚本、README 写的启动命令；找到后在导出目录里后台启动，用空闲端口。脚本负责：等地址可访问（超时 120 秒）、截图、写记录。
   起服务要的环境变量（`.env.local` 之类不在版本库里的文件）不复制进导出目录；缺了起不来就照实写原因。
4. **讲解源文件里怎么写截图**：在「产出清单」里用代码块标出要截的页面，第一行是路径，标题是页面名：

   ````text
   ```screenshot 登录页
   /login
   ```
   ````

   一份讲解最多 8 张。只能出现在「产出清单」里，检查脚本核对（路径要以 `/` 开头、数量、位置）。
5. **新脚本 `take_screenshots.py --source <brief.md> --base-url <地址> --out <名字>.shots/`**：逐个截图，写 `<名字>.shots/shots.json`
   （每张：页面名、路径、文件名、状态 `ok`／`failed`、失败原因、截图时的最终地址）。失败一张不影响其他张；地址不可访问时全部记失败。
6. **agent 要看每张截图**：截完后逐张打开图片看，截到的不是要的页面（登录页、报错页、空白页）时，把这一张改成失败，原因写清楚
   （如「需要登录，未截到」）。**不替用户登录、不输入任何账号密码**；项目自带假数据或假登录（mock）且不用填凭据就能进的，可以用。
7. **渲染**：`render_brief.py --shots <shots.json>`：截图块渲染成带标题的图，图片按相对路径引用 `<名字>.shots/` 里的文件；失败的渲染成
   「截图未生成：原因」。不给 `--shots` 时截图块一律渲染成「截图未生成：没有截图」。附录加一行截图来源（终点提交，或你给的地址）。
8. **什么时候截**：默认自动——讲解里有截图块就截；没有界面的模块不写截图块，产出清单写「本模块无界面」。`--no-screenshots` 跳过，截图块渲染成「截图未生成：指定了 --no-screenshots」。
   第 2 步的规模报告里加一句「会在临时目录装依赖、起开发服务器截图，约需 N 分钟」，见待定问题 Q1。
9. **`--base-url <地址>`**：用你已经在跑的服务截图，不导出、不装依赖、不起服务。截的是你工作区的样子，不一定等于终点提交；
   页面上写明「截图取自你给的地址，未核对与终点提交一致」。
10. **收尾**：无论成败，停掉起的服务（整个进程组）、删掉导出目录与浏览器配置目录；截图文件留在输出目录，和讲解页放在一起，重生成时覆盖。

## 命令

```text
python3 -B -m unittest discover -s plugins/delivery-brief/tests
python3 -B plugins/delivery-brief/scripts/take_screenshots.py --source <brief.md> --base-url http://127.0.0.1:<端口> --out <名字>.shots
python3 -B plugins/delivery-brief/scripts/render_brief.py --facts <facts.json> --source <brief.md> --out <brief.html> --shots <名字>.shots/shots.json
/delivery-brief:brief <base>..<head> --project ~/Documents/gs/next-shadcn-dashboard-starter
claude plugin validate .
```

## 项目结构

```text
plugins/delivery-brief/scripts/take_screenshots.py   # 等地址可访问、逐张截图、写 shots.json（新）
plugins/delivery-brief/scripts/brief_markdown.py     # 认 screenshot 代码块
plugins/delivery-brief/scripts/check_brief.py        # 截图块的位置、路径、数量
plugins/delivery-brief/scripts/render_brief.py       # --shots
plugins/delivery-brief/commands/brief.md             # 截图一步、--no-screenshots、--base-url
plugins/delivery-brief/references/brief-rules.md     # 产出清单里什么时候写截图块
plugins/delivery-brief/tests/                        # 截图脚本（用本机静态页面）、解析、检查、渲染
```

## 测试策略

- 截图脚本先写测试：用 Python 自带的 `http.server` 在临时目录起一个静态页面服务，截图文件存在、是 PNG、尺寸对；地址不可访问时全部记失败、
  原因写明；一张路径 404 不影响别的；没有 Chrome（环境变量指向不存在的文件）时全部记失败、退出 0；浏览器配置目录用完被删。
  机器上没有 Chrome 时跳过需要真截图的用例，并在输出里说明跳过。
- 解析与检查：截图块被认出；放在产出清单以外、路径不以 `/` 开头、超过 8 张都报错。
- 渲染：有 `--shots` 时出图与标题、相对路径；失败与不给 `--shots` 时出「截图未生成：原因」；不含截图块的讲解，渲染结果与之前逐字相同（除生成时间）。
- 规则一致性：命令文件里的新参数在脚本 `--help` 里；命令文件写明不替用户登录、收尾要停服务删目录。
- 真实运行：对 `next-shadcn-dashboard-starter` 一段改了页面的提交跑一次，记录：起服务用了什么命令、装依赖与起服务各花多久、
  截了几张、几张成功、失败的原因（预计会碰到登录）；被讲解项目运行前后的工作区与 ref 不变；浏览器打开讲解页自验截图显示正常。

## 边界

- Always：服务只在导出的临时目录里起；收尾停服务、删临时目录；每张截图都看过再用；截不到照实写原因，页面照常生成。
- Ask first：要往被讲解项目写任何文件、或复制不在版本库里的文件（如 `.env.local`）进导出目录时；起服务要访问外部真实服务（非本机、非 mock）时。
- Never：替用户登录或输入账号密码；在被讲解项目的目录里起服务或装依赖；把截不到的页面换成别的页面冒充；改 spec-guard。

## 成功标准

- AC1：`take_screenshots.py` 按假设 5 截图并写 `shots.json`；地址不可访问、单张失败、没有 Chrome 时都照实记失败，退出 0、不抛堆栈；临时浏览器配置目录不残留。
- AC2：解析与检查脚本认出截图块；位置不在产出清单、路径不以 `/` 开头、超过 8 张时报错。
- AC3：`render_brief.py --shots` 渲染截图与标题（相对路径）；失败、不给 `--shots`、`--no-screenshots` 时渲染「截图未生成：原因」；不含截图块的讲解与之前逐字相同（除生成时间）。
- AC4：命令文件写明截图流程：找启动方式的顺序、导出终点提交并按锁文件装依赖、空闲端口与等待、逐张看图并改判、不替用户登录、`--base-url` 与 `--no-screenshots`、收尾停服务删目录。
- AC5：被讲解项目在整个截图流程前后不变（工作区文件内容与 ref，测试与真实运行都核对）。
- AC6：对 `next-shadcn-dashboard-starter` 真实跑一次，结果（命令、耗时、成功与失败张数及原因、浏览器自验）写进验收材料；起不来也算完成，只要页面照常生成且原因属实。
- AC7：M2 发版准备：README 加截图的说明与两个新参数；版本 0.2.0；`claude plugin validate .` 通过；本机升级插件后在新会话里端到端跑一次。推送、打标签、本机升级各自先问用户。

## 文档建议

- README 的「用法」加 `--no-screenshots`、`--base-url`，写明截图在临时目录起服务、要装依赖、可能要几分钟、不替你登录；「后续计划」去掉 ui-screenshots。
- `docs/facts-schema.md` 不变（截图不进 facts）；`shots.json` 的字段写在脚本的文档字符串和命令文件里。

## 待定问题

- 无。2026-11-19 用户定为「批准；Q1 A；Q2 A」：要装依赖、起服务时不先问，规模报告写明预计耗时，`--no-screenshots` 可跳过（假设 8）；
  只截桌面宽度一屏 1280×800（假设 1）。
