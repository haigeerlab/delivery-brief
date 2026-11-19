---
description: "生成模块或一段提交的讲解页：几分钟看懂这次造了什么、怎么串起来、哪里要人判断"
argument-hint: "<模块 id | base..head> [--project <dir>] [--no-open]"
allowed-tools: Bash, Read, Write, Edit
---

用户输入本命令即授权：只读地读取目标项目的代码与 git 历史，在 `~/.claude/delivery-brief/` 下写讲解文件。
**不写目标项目的任何文件，不改它的 git 状态**；要在目标项目目录里跑命令（读 git 除外）、或要联网（`gh` 查链接除外），先问用户。

开始前先读讲解规则，后面每一步都照它做：

```bash
cat "${CLAUDE_PLUGIN_ROOT}/references/brief-rules.md"
```

## 1. 解析参数并收集事实

- 第一个参数含 `..` 时是提交段（`--range`），否则是模块 id（`--module`）。`--project` 缺省为当前目录所在 git 仓库的根目录。
- 输出目录 `OUT=~/.claude/delivery-brief/<项目目录名>`（即 facts 的 `project.name`，仓库根目录的名字），文件名 `NAME` 为模块 id；提交段时为 `<base 前 8 位>..<head 前 8 位>`
  （先用 `git rev-parse` 解析成完整提交号）。

```bash
mkdir -p "$OUT"
python3 -B "${CLAUDE_PLUGIN_ROOT}/scripts/brief_facts.py" --project "$PROJECT" --module <id> > "$OUT/$NAME.facts.json"
# 或：--range <base>..<head>
```

- 退出码非 0 时，删掉空的 facts 文件，原样转述 stderr 那一行并停下：2 是参数错，3 是范围解析不了（不是 spec-guard 项目时提示改用 `<base>..<head>`），4 是 git 出错。
- 记下目标项目的状态，最后一步要比对：

```bash
git -C "$PROJECT" status --porcelain > "$OUT/.$NAME.before"; git -C "$PROJECT" for-each-ref >> "$OUT/.$NAME.before"
```

## 2. 先报给用户，必要时停下

用几行告诉用户：范围（起止提交、几个提交）、来源（`range.source` 为 `inferred-spec-guard` 时说「按 spec-guard 文件约定推断」，并说出
`range.basis` 的起点与终点规则）、`warnings` 逐条、规模（文件数、增删行、diff 约多少 token：`size.diffBytes ÷ 4`）。

- **diff 约超过 5 万 token（`size.diffBytes` 超过 200000）时停下问用户是否继续**，说明大致会读多少；用户同意再往下。
- 没超过只报不问，直接继续。不要用 `size.estimatedTokens` 判断（它把被改文件全文算进去，按读取策略并不会整读）。

## 3. 读代码，写讲解源文件

- 按讲解规则的读取策略读，写 `$OUT/$NAME.md`。同名文件已存在时先 `rm -f "$OUT/$NAME.md" "$OUT/$NAME.html"` 再写，不读旧文件。格式、六节各写什么、证据硬规则、选图规则都以讲解规则为准。
- 需要实跑输出时，在临时目录里跑，**不在目标项目里跑**。在导出的临时目录里跑目标项目自己的测试或命令不用先问
  （它不碰项目本身）；为验证边界可以在临时目录里增改文件，讲解里写明输入是构造的。跑完删掉临时目录：

```bash
TMP="$(mktemp -d)"
git -C "$PROJECT" archive <range.head> | tar -x -C "$TMP"
# 在 "$TMP" 里跑测试或命令；跑完 rm -rf "$TMP"
```

  先看项目怎么跑测试（README、Spec 的「命令」一节、CI 配置）。要装依赖（`npm install`、`pip install` 等）或联网才能跑的，不跑，
  在「需要你判断的」里写「没有实跑（原因）」。

## 4. 检查

```bash
python3 -B "${CLAUDE_PLUGIN_ROOT}/scripts/check_brief.py" --facts "$OUT/$NAME.facts.json" --source "$OUT/$NAME.md"
```

- 退出码 1：按报告逐条修改讲解源文件再检查。**最多检查三次**（第一次检查加两轮修改后的复检；第一次检查前你自己的修改不算）。
  检查通过后你自己又改了源文件，要再检查一次，这一次也算在三次里。第三次仍有错误，停下，把报告原样给用户，问是否照样渲染。
- 退出码 2（参数错、输入读不了）：原样转述 stderr 并停下。
- 提醒（`warn`）不挡渲染，但能改就改；图没有标题的提醒要改。

## 5. 渲染并打开

```bash
python3 -B "${CLAUDE_PLUGIN_ROOT}/scripts/render_brief.py" --facts "$OUT/$NAME.facts.json" --source "$OUT/$NAME.md" --out "$OUT/$NAME.html"
```

- 没给 `--no-open` 且有 `open` 命令时，`open "$OUT/$NAME.html"`；否则只给路径。
- 再取一次目标项目的状态，和第 1 步比对，比完删掉记录文件；不一致就如实告诉用户哪里变了：

```bash
{ git -C "$PROJECT" status --porcelain; git -C "$PROJECT" for-each-ref; } | diff "$OUT/.$NAME.before" - && rm "$OUT/.$NAME.before"
```

中途停下（任何一步退出码非 0、等用户答复）时，先删掉 `$OUT/.$NAME.before`，答复后重新开始时再从第 1 步记。

## 6. 回复用户

- 讲解页路径（可点击）；范围来源与 warnings 的一句话；检查结果（几个提醒）；有没有实跑、在哪跑的。
- 讲解页里的数字由脚本生成，叙述由你写：提醒用户叙述没有经过独立核对（`--cross-check` 由 cross-check 模块提供，未装时不提）。
- 同名文件已存在时会被覆盖：讲解页不需要维护，随时可以重生成。
