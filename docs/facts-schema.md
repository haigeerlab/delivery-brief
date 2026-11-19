# brief_facts.py 输出说明（schemaVersion 1）

`plugins/delivery-brief/scripts/brief_facts.py` 只读收集一段代码交付的事实，输出一个 JSON 对象。讲解页里的数字、文件、提交、
AC、勾选状态都从这里取，不靠模型回忆。本文件是字段的唯一说明；字段表由测试 `tests/test_schema_doc.py` 与真实输出逐一比对。

## 用法

```text
python3 -B plugins/delivery-brief/scripts/brief_facts.py --project <dir> (--module <id> | --range <base>..<head>) [--offline]
```

| 退出码 | 含义 |
|---|---|
| 0 | 成功，stdout 是 JSON |
| 2 | 参数错（缺参数、`--range` 写法不对、模块 id 不是 kebab-case、`--module` 与 `--range` 同时给） |
| 3 | 解析不出范围：提交不存在；没有 `spec/CAPABILITY-MAP.md`；模块不在能力图上；模块还没有任何提交 |
| 4 | git 出错，或 `--project` 不是 git 仓库 |

出错时 stderr 只有一行中文说明。脚本不写被讲解项目的任何文件和 git 状态；唯一的网络访问是 `gh api`（见 `links`），`--offline` 关掉。

## 模块范围怎么推断（`range.source` 为 `inferred-spec-guard`）

spec-guard 现有的只读接口给不出模块的提交列表，所以按它公开的文件约定推断：

1. **起点**：沿 HEAD 的历史，第一个改动 `spec/<id>.md` 或 `tasks/<id>/` 的非合并提交。`range.base` 是它的父提交（根提交时为 `null`）。
2. **终点**：逐个看改过 `tasks/<id>/todo.md` 的提交，取最后一个把某个「（gate）」检查点从未勾改成已勾、并且这个检查点在 HEAD 上
   仍是已勾的提交。检查点按「第一个冒号之前的文字」识别（如 `Checkpoint 2（gate）`），所以勾选时在后面追加说明不影响识别。
3. 一个 gate 都没勾时按进行中处理（`inProgress: true`），终点取最后一个改动模块文件的提交。
4. 范围是 `base..head` 之间的非合并提交。

**已知局限**（都会写进 `warnings`，讲解页页头要标「范围是推断的」）：

- 终点之后还改了模块文件的提交（`range.basis.laterModuleCommits`）可能是验收后的发版收尾，也可能是中途 gate 之后接着开发；
  单看 todo 分不开，所以只列出来，不自动算进范围。需要时用 `--range` 指定。
- 并行开发时，范围里可能混进别的模块的提交：只能发现改了别的模块 `spec/<id>.md`、`tasks/<id>/` 的提交，改共用代码的发现不了。
- 不按 spec-guard 格式写「（gate）」的 todo，会落到进行中的兜底。

spec-guard 若提供权威的模块提交接口，改用接口，本规则留作后备。

## 渲染脚本读哪些字段

`render_brief.py` 只从 facts 取这些，生成页头、提示框与附录，讲解源文件里不写这些数字：

- 页头：`project.name`、`range.base`、`range.head`、`range.source`（「推断」或「指定」标签）、`commits` 的个数、
  `totals.files`／`added`／`deleted`、`range.inProgress`（「进行中」）、`module.todo.atHead` 里已勾且含「发版」的项（「已发版」）。
- 提示框：`warnings` 逐条；`links.kind` 为 `local` 且 `links.workingTreeMatchesEnd` 为 `false` 时加一条「本机工作区与终点提交不一致」。
- 引用链接：`links.kind`、`links.base`、`links.lineFormat`。
- 附录：`files`（路径、原路径、状态、增删或二进制）、`commits`（短号、标题、日期）、`totals`。
- 页脚：`range` 与 `links.reason`。

`check_brief.py` 另读：`project.root` 与 `range.head`（用 `git show` 核对引用）、`module.spec.acs` 与 `acsNumbered`（AC 表是否齐全）、
`commits`、`range.basis.laterModuleCommits`、`project.head` 与 `module.spec.marker`（正文里允许出现的提交号）。

## 字段

### 顶层

| 字段 | 类型 | 说明 |
|---|---|---|
| `schemaVersion` | int | 固定为 1 |
| `project` | object | 被讲解的项目 |
| `project.root` | string | 仓库根目录（`git rev-parse --show-toplevel`） |
| `project.name` | string | 根目录名 |
| `project.head` | string | 运行时的 HEAD 提交 |
| `warnings` | string[] | 推断范围、混入提交、读不到的文件等，逐条中文 |

### range

| 字段 | 类型 | 说明 |
|---|---|---|
| `range` | object | 讲解的提交范围 |
| `range.base` | string \| null | 范围起点之前的提交（不含）；`null` 表示从根提交开始 |
| `range.head` | string | 范围终点（含） |
| `range.source` | string | `explicit`（`--range`）或 `inferred-spec-guard`（`--module`） |
| `range.inProgress` | bool | 推断时一个 gate 都没勾上；`--range` 时恒为 `false` |
| `range.basis` | object \| null | 推断依据；`--range` 时为 `null` |
| `range.basis.start` | object | 起点 |
| `range.basis.start.sha` | string | 起点提交 |
| `range.basis.start.rule` | string | 起点规则的中文说明 |
| `range.basis.end` | object | 终点 |
| `range.basis.end.sha` | string | 终点提交（与 `range.head` 相同） |
| `range.basis.end.gate` | string \| null | 终点勾上的 gate（冒号前的文字）；进行中时为 `null` |
| `range.basis.end.rule` | string | 终点规则的中文说明 |
| `range.basis.laterModuleCommits` | string[] | 终点之后仍改动模块文件的非合并提交 |
| `range.basis.openItemsAtHead` | object[] | HEAD 上 todo 里未勾、且不是延期写法的项，字段同 `module.todo.atHead[]` |
| `range.basis.openItemsAtHead[].text` | string | 同 todo 项 |
| `range.basis.openItemsAtHead[].checked` | bool | 同 todo 项 |
| `range.basis.openItemsAtHead[].kind` | string | 同 todo 项 |
| `range.basis.openItemsAtHead[].deferred` | bool | 同 todo 项 |

### commits、files、totals、size

| 字段 | 类型 | 说明 |
|---|---|---|
| `commits` | object[] | 范围内的非合并提交，从旧到新 |
| `commits[].sha` | string | 完整提交号 |
| `commits[].short` | string | 前 8 位 |
| `commits[].subject` | string | 提交标题 |
| `commits[].date` | string | 提交时间（ISO 8601） |
| `commits[].files` | string[] | 该提交改动的文件（重命名取新路径） |
| `files` | object[] | `git diff -M base head` 的逐文件结果 |
| `files[].path` | string | 文件路径（重命名为新路径） |
| `files[].oldPath` | string | 只在重命名（R）或复制（C）时出现：原路径 |
| `files[].status` | string | `A` 新增、`M` 修改、`D` 删除、`R` 重命名、`C` 复制、`T` 类型变化 |
| `files[].added` | int \| null | 新增行数；二进制文件为 `null` |
| `files[].deleted` | int \| null | 删除行数；二进制文件为 `null` |
| `files[].binary` | bool | 是否二进制 |
| `totals` | object | 合计 |
| `totals.files` | int | 文件数 |
| `totals.added` | int | 新增行数（二进制不计） |
| `totals.deleted` | int | 删除行数（二进制不计） |
| `size` | object | 规模，用于生成前提示 |
| `size.files` | int | 同 `totals.files` |
| `size.added` | int | 同 `totals.added` |
| `size.deleted` | int | 同 `totals.deleted` |
| `size.diffBytes` | int | 整段 diff 的字节数 |
| `size.changedFileBytes` | int | 范围终点上被改文件（不含删除的）的总字节数 |
| `size.estimatedTokens` | int | `(diffBytes + changedFileBytes) ÷ 4`，只是量级 |

### module（只在 `--module` 时；`--range` 时为 `null`）

| 字段 | 类型 | 说明 |
|---|---|---|
| `module` | object \| null | 模块事实 |
| `module.id` | string | 模块 id |
| `module.responsibility` | string | 能力图里的职责（原文） |
| `module.dependsOn` | string[] | 能力图里的依赖 |
| `module.spec` | object | Spec（读终点提交上的版本，没有时读 HEAD） |
| `module.spec.path` | string | `spec/<id>.md` |
| `module.spec.marker` | string \| null | 批准标记：`pending`、`approved <digest>`、`approved` 或 `null` |
| `module.spec.acs` | object[] | 验收标准，按出现顺序 |
| `module.spec.acs[].id` | string \| null | `AC1` 等；Spec 没有 AC 编号时为 `null` |
| `module.spec.acs[].text` | string | 原文（续行拼接） |
| `module.spec.acsNumbered` | bool | AC 是否带编号；`false` 时按「成功标准」一节的条目列出，并有一条 warning |
| `module.plan` | object | Plan |
| `module.plan.path` | string | `tasks/<id>/plan.md` |
| `module.plan.exists` | bool | HEAD 上是否存在 |
| `module.todo` | object | todo，两份 |
| `module.todo.path` | string | `tasks/<id>/todo.md` |
| `module.todo.atEnd` | object[] | 范围终点上的 todo 项 |
| `module.todo.atEnd[].text` | string | 勾选框之后的原文 |
| `module.todo.atEnd[].checked` | bool | 是否已勾 |
| `module.todo.atEnd[].kind` | string | `gate`、`report` 或 `task` |
| `module.todo.atEnd[].deferred` | bool | 是否是 `延期：…` 写法 |
| `module.todo.atHead` | object[] | HEAD 上的 todo 项（验收后的发版勾选只在这一份里） |
| `module.todo.atHead[].text` | string | 同上 |
| `module.todo.atHead[].checked` | bool | 同上 |
| `module.todo.atHead[].kind` | string | 同上 |
| `module.todo.atHead[].deferred` | bool | 同上 |

### usageDraft（只在 `--module` 且模块在某份用法草案的里程碑里时；否则为 `null`）

| 字段 | 类型 | 说明 |
|---|---|---|
| `usageDraft` | object \| null | 模块所属的用法草案（读 HEAD 上的 `spec/usage/*.md`） |
| `usageDraft.file` | string | 草案路径 |
| `usageDraft.milestone` | string | 里程碑编号，如 `M1` |
| `usageDraft.usages` | string[] | 该里程碑对应的典型用法编号 |
| `usageDraft.entries` | object[] | 归本模块的入口 |
| `usageDraft.entries[].entry` | string | 入口（去掉反引号） |
| `usageDraft.entries[].does` | string | 做什么 |

### links

| 字段 | 类型 | 说明 |
|---|---|---|
| `links` | object | 讲解页里代码链接怎么生成 |
| `links.kind` | string | `github` 或 `local` |
| `links.base` | string | `github`：`https://github.com/<repo>/blob/<终点 sha>/`；`local`：仓库根目录加 `/` |
| `links.lineFormat` | string \| null | `github` 时为 `#L{start}-L{end}`；`local` 时为 `null` |
| `links.repo` | string \| null | `owner/repo`；`local` 时为 `null` |
| `links.workingTreeMatchesEnd` | bool \| null | `local` 时：本机工作区（已跟踪文件）是否与终点提交一致；`github` 时为 `null` |
| `links.reason` | string | 为什么选这种链接 |

只有 origin 是 GitHub、`gh api` 查得仓库公开、并且终点提交在远端时才用 `github`；`--offline`、没有 `gh`、查询失败、私有仓库、
终点未推送都退回 `local` 并写明原因。
