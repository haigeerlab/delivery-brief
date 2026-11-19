---
description: "生成模块或一段提交的讲解页：几分钟看懂这次造了什么、怎么串起来、哪里要人判断"
argument-hint: "<模块 id | base..head | --milestone <M> [--draft <草案>]> [--project <dir>] [--no-open] [--cross-check] [--no-screenshots] [--base-url <地址>]"
allowed-tools: Bash, Read, Write, Edit
---

用户输入本命令即授权：只读地读取目标项目的代码与 git 历史，在 `~/.claude/delivery-brief/` 下写讲解文件。
**不写目标项目的任何文件，不改它的 git 状态**；要在目标项目目录里跑命令（读 git 除外）、或要联网（`gh` 查链接除外），先问用户。
例外：第 4.6 步截图时，在导出的临时目录里按锁文件装依赖（要联网）、起开发服务器，不另问（第 2 步会先告诉用户）。

开始前先读讲解规则，后面每一步都照它做：

```bash
cat "${CLAUDE_PLUGIN_ROOT}/references/brief-rules.md"
```

删除文件时目标一律写成 `"${变量:?}/…"`：变量为空时 shell 直接报错，不会删到根目录（Claude Code 也会拒绝没有这样写的删除）。

## 1. 解析参数并收集事实

- 第一个参数含 `..` 时是提交段（`--range`）；给了 `--milestone <M>` 时是**里程碑页**（见下面「里程碑页」一节，可带 `--draft <草案>`）；
  否则是模块 id（`--module`）。`--project` 缺省为当前目录所在 git 仓库的根目录。
- 输出目录 `OUT=~/.claude/delivery-brief/<项目目录名>`（即 facts 的 `project.name`，仓库根目录的名字），文件名 `NAME` 为模块 id；提交段时为 `<base 前 8 位>..<head 前 8 位>`
  （先用 `git rev-parse` 解析成完整提交号）。

```bash
mkdir -p "$OUT"
python3 -B "${CLAUDE_PLUGIN_ROOT}/scripts/brief_facts.py" --project "$PROJECT" --module <id> > "$OUT/$NAME.facts.json"
# 或：--range <base>..<head>
# 或：--milestone <M>（有多份用法草案时加 --draft spec/usage/<需求>.md）
```

- 退出码非 0 时，删掉空的 facts 文件，原样转述 stderr 那一行并停下：2 是参数错，3 是范围解析不了（不是 spec-guard 项目时提示改用 `<base>..<head>`），4 是 git 出错。
- 记下目标项目的状态，最后一步要比对：

```bash
git -C "$PROJECT" status --porcelain > "$OUT/.$NAME.before"; git -C "$PROJECT" for-each-ref >> "$OUT/.$NAME.before"
```

### 里程碑页（给了 `--milestone <M>` 时）

和模块页走同一套第 1～6 步，只有这些不同：

- 文件名 `NAME=milestone-$M`（如 `milestone-M1`），和模块页在同一个输出目录，这样里程碑页能用相对链接指向各模块页。
- 第 2 步报告里多说：这一站的典型用法、几个模块、各自状态（`milestone.modules[].status`）、里程碑确认了没有；范围是各模块范围的并集。
- 第 3 步按讲解规则「里程碑页」一节的读取策略与七节写法；先读各模块 Spec 的**成功标准**，再读输出目录里已有的模块页源文件 `"$OUT/<模块 id>.md"`，
  最后读模块之间接口处的代码。
- 缺模块页时**只标出来，不替用户生成**：渲染脚本会在「各模块讲解」表里写「还没生成」和生成命令，回复时也提一句。
- 给了 `--cross-check` 时告诉用户「里程碑页暂不支持交叉核对」，跳过第 4.5 步，照常生成。
- 不截图（截图属于模块页），跳过第 4.6 步。

## 2. 先报给用户，必要时停下

用几行告诉用户：范围（起止提交、几个提交）、来源（`range.source` 为 `inferred-spec-guard` 时说「按 spec-guard 文件约定推断」，并说出
`range.basis` 的起点与终点规则）、`warnings` 逐条、规模（文件数、增删行、diff 约多少 token：`size.diffBytes ÷ 4`）。

- **diff 约超过 5 万 token（`size.diffBytes` 超过 200000）时停下问用户是否继续**，说明大致会读多少；用户同意再往下。
- 没超过只报不问，直接继续。
- 讲解要截图时（第 4.6 步；有界面改动、没给 `--no-screenshots`），写完讲解源文件后再加一句：会在临时目录装依赖、起开发服务器截图，
  约需 1～5 分钟（按依赖多少），不想要可以加 `--no-screenshots` 重跑；给了 `--base-url` 时说用这个地址截图、不起服务。不另问。
- 给了 `--cross-check` 时再加一句：交叉核对经 delegate 另花约 10～25 万输入 token（随材料大小；2026-11-19 对一个 26 文件、约 58 万字节材料的模块实测 22.4 万，花在 delegate 默认后端的额度上），用户写了这个参数就算同意，不另问。不要用 `size.estimatedTokens` 判断（它把被改文件全文算进去，按读取策略并不会整读）。

## 3. 读代码，写讲解源文件

- 按讲解规则的读取策略读，写 `$OUT/$NAME.md`。同名文件已存在时先 `rm -rf "${OUT:?}/${NAME:?}.md" "${OUT:?}/${NAME:?}.html" "${OUT:?}/${NAME:?}.shots"` 再写，不读旧文件。格式、六节各写什么、证据硬规则、选图规则都以讲解规则为准。
- 需要实跑输出时，在临时目录里跑，**不在目标项目里跑**。在导出的临时目录里跑目标项目自己的测试或命令不用先问
  （它不碰项目本身）；为验证边界可以在临时目录里增改文件，讲解里写明输入是构造的。跑完删掉临时目录：

```bash
TMP="$(mktemp -d)"
git -C "$PROJECT" archive <range.head> | tar -x -C "$TMP"
# 在 "$TMP" 里跑测试或命令；跑完 rm -rf "${TMP:?}"
```

  先看项目怎么跑测试（README、Spec 的「命令」一节、CI 配置）。要装依赖（`npm install`、`pip install` 等）或联网才能跑的，不跑，
  在「需要你判断的」里写「没有实跑（原因）」（第 4.6 步截图装依赖是例外，只为起服务，不借机跑测试）。

## 4. 检查

```bash
python3 -B "${CLAUDE_PLUGIN_ROOT}/scripts/check_brief.py" --facts "$OUT/$NAME.facts.json" --source "$OUT/$NAME.md"
```

- 退出码 1：按报告逐条修改讲解源文件再检查。**最多检查三次**（第一次检查加两轮修改后的复检；第一次检查前你自己的修改不算）。
  检查通过后你自己又改了源文件，要再检查一次，这一次也算在三次里。第三次仍有错误，停下，把报告原样给用户，问是否照样渲染。
- 退出码 2（参数错、输入读不了）：原样转述 stderr 并停下。
- 提醒（`warn`）不挡渲染，但能改就改；图没有标题的提醒要改。

## 4.5 交叉核对（只在给了 `--cross-check` 时）

检查通过后、渲染前做。核对记录写到 `$OUT/$NAME.crosscheck.json`，格式：

```json
{"status": "complete", "backend": "codex", "model": "unknown", "reportPath": "<delegate 报告路径>",
 "coverage": {"reviewed": 0, "unreviewed": 0},
 "findings": [{"title": "<发现>", "verdict": "confirmed|rejected|unverified", "note": "<核实依据或原因>"}]}
```

1. **delegate 可用吗**：可用技能里没有 `delegate:review` 时，告诉用户「没装 delegate，跳过交叉核对」，写一份
   `status: incomplete`、`reason: 没装 delegate 插件` 的记录（`backend`、`model` 写 `none`，`coverage` 都是 0，`findings` 为空），直接到第 5 步。
2. **准备材料**：

```bash
python3 -B "${CLAUDE_PLUGIN_ROOT}/scripts/crosscheck_material.py" --facts "$OUT/$NAME.facts.json" --source "$OUT/$NAME.md" --out "$OUT/.crosscheck-$NAME"
```

   退出 3（材料超限）时把 stderr 写进记录的 `reason`，`status: incomplete`，到第 5 步。
3. **调用审查**：读 `"${CLAUDE_PLUGIN_ROOT}/references/cross-check-prompt.md"`，只把 `{{project}}` 换成项目名、`{{subject}}` 换成「模块 <id>」或
   「提交段 <base>..<head>」，**不加任何别的话**（不写你自己的评价、不提示哪里可能有问题）。用 Skill 调 `delegate:review`，参数：

```text
--repo "$OUT/.crosscheck-$NAME" --paths brief.md --paths facts.json --paths range.diff --paths MATERIAL.md --paths source -- "<替换后的模板全文>"
```

   不传后端和模型，用 delegate 的默认值。
4. **读报告**：delegate 输出里有报告 JSON（以及报告文件路径）。`execution_status` 不是 `completed`、`unreviewed` 非空、输出为空或读不到时，
   记 `status: incomplete` 并写明原因；退出 0 不等于核对通过。`backend` 取报告的 `backend`，`model` 取 `observed_models` 的第一个，没有写 `unknown`；
   `coverage` 取 `reviewed` 与 `unreviewed` 的个数。
5. **逐条核实**：审查方的话不是事实。每条 `findings` 回到代码核实（读终点提交上的文件；需要时在导出的临时目录里实跑），标：
   - `confirmed`：成立。按讲解规则改讲解源文件（证据仍只用代码、测试、实跑输出），`note` 写改了什么；
   - `rejected`：不成立。`note` 写证据（文件与行号或实跑输出）；
   - `unverified`：核实不了。`note` 写原因。
6. **复检**：有 `confirmed` 时重跑第 4 步的检查（这一次不计入那三次）；仍有错误就停下问用户。
7. 写好记录文件，删掉材料目录 `"$OUT/.crosscheck-$NAME"`。

## 4.6 截图（讲解源文件里有截图块时）

检查通过后、渲染前做（给了 `--cross-check` 时在 4.5 之后）。截图块怎么写见讲解规则「产出清单」。讲解源文件里没有截图块就跳过这一步，
渲染时不加截图参数。下面的 `SKIP` 是渲染时 `--shots-skipped` 的原因，一旦设了就跳到第 8 小步收尾、再去第 5 步。

1. **给了 `--no-screenshots`**：`SKIP="指定了 --no-screenshots"`。
2. **给了 `--base-url <地址>`**：不导出、不装依赖、不起服务，`BASE=<地址>`、`ORIGIN=base-url`，直接到第 6 小步。截的是用户工作区里跑着的样子，
   页面附录会写「未核对与终点提交一致」。
3. **找启动方式**，按这个顺序，找到一个就停：终点提交上的 `.claude/launch.json`（`configurations` 里的命令、参数、端口）、`package.json` 的
   `dev` 或 `start` 脚本、README 里写的启动命令。都没有：`SKIP="找不到启动方式（没有 .claude/launch.json、dev／start 脚本或 README 说明）"`。
4. **导出终点提交并装依赖**（都在临时目录里，不碰目标项目；记下各步耗时）：

```bash
SHOT_TMP="$(mktemp -d)"
git -C "$PROJECT" archive <range.head> | tar -x -C "$SHOT_TMP"
PORT="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')"  # 空闲端口
```

   按锁文件选装依赖命令，在 `"$SHOT_TMP"` 里跑（Bash 超时给 600000）：`pnpm-lock.yaml` → `pnpm install --frozen-lockfile`；
   `package-lock.json` → `npm ci`；`yarn.lock` → `yarn install --frozen-lockfile`；`bun.lockb`／`bun.lock` → `bun install --frozen-lockfile`。
   没有锁文件：`SKIP="没有锁文件，不装依赖"`。装失败：`SKIP="装依赖失败：<最后一行报错>"`。
   **不复用目标项目的 `node_modules`**（开发服务器会往里写缓存），**不复制 `.env`、`.env.local` 等不在版本库里的文件**；
   要复制它们才能起来时先问用户，用户不同意就照实写原因。
5. **起服务**：在 `"$SHOT_TMP"` 里后台启动，放进新的进程组，输出写日志，记下进程组号：

```bash
cd "$SHOT_TMP" && PORT="$PORT" nohup python3 -c 'import os, sys; os.setsid(); os.execvp(sys.argv[1], sys.argv[1:])' <启动命令与参数> > "$SHOT_TMP/.server.log" 2>&1 &
PGID=$!
BASE="http://127.0.0.1:$PORT"; ORIGIN=export
```

   端口：`launch.json` 写了端口就用它（被占用时 `SKIP="端口 <n> 被占用"`）；Next.js 等读 `PORT` 环境变量的直接用；Vite 类在命令后加
   `--port "$PORT" --strictPort`。不改项目的配置文件来换端口。
6. **截图**：

```bash
python3 -B "${CLAUDE_PLUGIN_ROOT}/scripts/take_screenshots.py" --source "$OUT/$NAME.md" --base-url "$BASE" --out "$OUT/$NAME.shots" --origin export
# 用户给的地址：--origin base-url --wait 10
```

   全部失败且原因是地址不可访问时，看 `"$SHOT_TMP/.server.log"` 最后几行，把真正原因（缺环境变量、端口、编译报错）写进每张的 `reason`。
7. **逐张看截图**：用 Read 打开 `"$OUT/$NAME.shots"` 里每张 `ok` 的 PNG，对照截图块的页面名判断截到的是不是这个页面。
   登录页、报错页、空白页、加载中、和页面名对不上的，把 `shots.json` 里这一张改成 `"status": "failed"`，`reason` 写清楚
   （如「需要登录，截到的是登录页」）。**不替用户登录，不输入任何账号密码**，也不点击页面；截图只反映直接打开地址时的样子。
   不拿别的页面顶替截不到的页面。`httpStatus` ≥ 400 的一般也改成失败。
8. **收尾（无论成败都做）**：停掉服务、删掉导出目录，确认端口上没有残留进程：

```bash
kill -- "-$PGID" 2>/dev/null; sleep 3; kill -9 -- "-$PGID" 2>/dev/null
rm -rf "${SHOT_TMP:?}"
lsof -nP -iTCP:"$PORT" -sTCP:LISTEN || echo "端口已释放"
```

   给了 `--base-url` 时没有起服务，不停任何进程。

## 5. 渲染并打开

```bash
python3 -B "${CLAUDE_PLUGIN_ROOT}/scripts/render_brief.py" --facts "$OUT/$NAME.facts.json" --source "$OUT/$NAME.md" --out "$OUT/$NAME.html"
# 给了 --cross-check 时末尾加：--cross-check "$OUT/$NAME.crosscheck.json"
# 截了图时末尾加：--shots "$OUT/$NAME.shots/shots.json"
# 有截图块但没截（第 4.6 步设了 SKIP）时末尾加：--shots-skipped "$SKIP"
```

- 截了图时，讲解页按相对路径引用 `$NAME.shots/` 里的图片，两者要放在一起；`$OUT/$NAME.shots` 也是输出的一部分，不要删。

- 渲染退出 2 且说「核对记录不能用」时，按提示修好记录文件再渲染。

- 没给 `--no-open` 且有 `open` 命令时，`open "$OUT/$NAME.html"`；否则只给路径。
- 再取一次目标项目的状态，和第 1 步比对，比完删掉记录文件；不一致就如实告诉用户哪里变了：

```bash
{ git -C "$PROJECT" status --porcelain; git -C "$PROJECT" for-each-ref; } | diff "$OUT/.$NAME.before" - && rm "${OUT:?}/.${NAME:?}.before"
```

中途停下（任何一步退出码非 0、等用户答复）时，先删掉 `$OUT/.$NAME.before`，答复后重新开始时再从第 1 步记。

## 6. 回复用户

- 讲解页路径（可点击）；范围来源与 warnings 的一句话；检查结果（几个提醒）；有没有实跑、在哪跑的。
- 有截图块时报截图结果：截了几张、成功几张、失败的原因；起服务用的命令，装依赖与起服务各花了多久；或没截的原因。
- 讲解页里的数字由脚本生成，叙述由你写。没给 `--cross-check` 时提醒用户叙述没有经过独立核对，可以加 `--cross-check` 重跑；
  给了时报核对结果：几条发现、成立几条已改、不成立几条、没核实几条，或没有完成的原因。
- 同名文件已存在时会被覆盖：讲解页不需要维护，随时可以重生成。
