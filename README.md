# delivery-brief（交付讲解）

AI 写的代码越来越多，人看代码的时间越来越少：测试都过了，但这次到底造了什么、为什么这样造、怎么串起来、哪里要人判断，
往往说不清。delivery-brief 是一个 Claude Code 插件，在你需要的时候用一个命令生成一份**本机讲解网页**，几分钟看懂一个模块、一段提交，或一个里程碑的几个模块怎么串起来。

![讲解页示例](docs/images/brief-example.jpg)

讲解页回答固定的六个问题，讲法随内容和项目类型变化：

1. **为什么改**：对应哪几条验收标准（AC），每条的证据是测试断言、代码行或实跑输出；有用法草案时对照计划与实际。
2. **产出清单**：按项目类型分组（前端的页面、组件、hooks；后端的模块、公开函数；插件的命令、脚本、规则……），每项写新增还是修改、做什么、怎么用、代码位置。
3. **分层讲改动**：按意图分 3～7 层，值得画图的才画。
4. **阅读路线**：看哪 3～7 处代码、按什么顺序。
5. **需要你判断的**：偏离计划、取舍、没测到的部分、出错时不会如实报告的边界。只摆事实，不打分。
6. **附录**：逐文件的改动表与提交表。

页头和附录里的数字（提交数、文件数、增删行）由脚本直接从 git 生成，不经模型；正文里每条证据都带引用，生成后由检查脚本核对引用真实存在。

## 安装

需要 Claude Code、`git`、`python3`（3.9 及以上，只用标准库）。`gh` 可选（用来判断能不能生成 GitHub 行号链接）；
[delegate](https://github.com/haigeerlab/delegate-plugin) 插件可选（`--cross-check` 要用）；Google Chrome 或 Chromium 可选（给界面截图要用）。

```text
/plugin marketplace add haigeerlab/delivery-brief
/plugin install delivery-brief@delivery-brief-marketplace
```

## 用法

```text
/delivery-brief:brief <模块 id>          # spec-guard 项目里讲一个模块，提交范围自动推断
/delivery-brief:brief <base>..<head>     # 讲任意一段提交，任何 git 项目都行
/delivery-brief:brief --milestone M1     # spec-guard 项目里讲用法草案的一个里程碑（见「里程碑讲解页」）
```

| 参数 | 作用 |
|---|---|
| `--project <dir>` | 被讲解的项目，缺省为当前目录所在的 git 仓库 |
| `--no-open` | 生成后不自动用浏览器打开 |
| `--draft <草案>` | 和 `--milestone` 一起用：项目有多份用法草案时指定读哪一份 |
| `--no-screenshots` | 有界面改动也不截图（不装依赖、不起服务），截图处写「截图未生成」 |
| `--base-url <地址>` | 用你已经在跑的开发服务器截图，不另起；截的是你工作区的样子，页面上会注明未核对与终点提交一致 |
| `--cross-check` | 讲解生成后，经 delegate 交给另一个模型只读核对：说法与代码是否相符、有没有漏掉的事实；每条发现回到代码核实后再改讲解，附录留核对记录。另花约 10～25 万输入 token（delegate 默认后端的额度） |

生成前会先告诉你范围、来源和规模；diff 超过约 5 万 token 时先停下问你。

**输出位置**：`~/.claude/delivery-brief/<项目目录名>/<模块 id>.html`，旁边是讲解源文件（`.md`）、事实（`.facts.json`），有截图时还有 `<模块 id>.shots/`。
**不写被讲解项目的任何文件**；需要实跑测试时，只在 `git archive` 导出的临时目录里跑。讲解页不需要维护，随时可以重生成，同名会覆盖。

## 里程碑讲解页

模块页讲一个模块的细节，里程碑页讲 spec-guard 用法草案里一个里程碑的几个模块**怎么串起来**，固定七节：

1. **这一站做成了什么**：逐条对照草案里这一站的典型用法，每条带代码、测试或实跑输出的证据；
2. **代码地图**：终点提交上的目录（取前两层），标出这一站新增、修改、删除的文件数，由脚本从 git 生成；
3. **沿典型用法走一遍**：选一个典型用法，按实际发生的顺序走 3～10 步，每步引用代码、标出属于哪个模块；
4. **跨模块约定**：这一站新出现的、多个模块都遵守的约定（每条至少引用两个文件），没有就写「没有新约定」；
5. **各模块讲解**：每个模块的职责、范围、状态，链到它的模块页；还没生成的写出生成命令（不替你生成）；
6. **需要你判断的**；7. **附录**。

范围是各模块推断范围的并集（起点取最早的模块、终点取最晚的模块）；有模块没做完、里程碑还没确认时页头会标出。
输出 `milestone-<M>.html`，和模块页放在同一个目录。里程碑页暂不支持 `--cross-check`，也不截图。

## 界面截图

讲解里有界面的页面时，命令会在产出清单的这些页面旁边各附一张截图（桌面宽度一屏，1280×800，最多 8 张）：

- 把终点提交 `git archive` 导出到临时目录，按锁文件装依赖（`pnpm install --frozen-lockfile`、`npm ci` 等，要联网），
  按 `.claude/launch.json`、`package.json` 的 `dev`／`start`、README 的顺序找启动方式，在空闲端口上起开发服务器；
- 用本机 Chrome 的无界面模式截图，每张都由 agent 看过：截到登录页、报错页、空白页时如实写「截图未生成：原因」；
- **不替你登录，不输入任何账号密码，也不点击页面**；不复制 `.env` 等不在版本库里的文件（要复制会先问你）；
- 结束时停掉服务、删掉临时目录。一般多花一到几分钟（实测一个 Next.js 项目：装依赖 11 秒、起服务 12 秒、截两张 5 秒）。

截图放在讲解页旁边的 `<名字>.shots/` 目录里，和讲解页一起移动才能显示。

## 模块范围怎么来的

在 [spec-guard](https://github.com/haigeerlab/spec-guard-plugin) 项目里，按它公开的文件约定推断：起点是第一个改动
`spec/<id>.md` 或 `tasks/<id>/` 的提交，终点是把 todo 里最后一个「（gate）」检查点勾上的提交。页头会标「推断」，
可疑的地方（终点之后还有改模块文件的提交、混入别的模块的提交）列在页头提示里。推断不准时用 `<base>..<head>` 指定。
规则与已知局限见 [docs/facts-schema.md](docs/facts-schema.md)。

## 不做什么

- 不给代码质量打分，判断留给人；讲解只负责把要判断的地方摆出来。
- 不替代独立的代码审查（`--cross-check` 核对的是讲解是否属实，不是代码好不好）。
- 讲解页不进被讲解项目的仓库。

## 版本记录

**0.3.0**：里程碑讲解页（`--milestone <M>`、`--draft`）。能力图上的五个模块全部完成。

**0.2.0**：有界面改动时自动截图（见「界面截图」），新增 `--no-screenshots`、`--base-url`；命令里的删除一律防空变量，避免被 Claude Code 拦下。
已知局限：路径里含 `[[`（如 Next.js 的可选捕获路由目录 `[[...slug]]`）的文件没法写成引用，讲解里只能写成代码文字。

**0.1.1**：0.1.0 用 `--cross-check` 给 brief-facts 自己生成讲解时查出的问题：

- 仓库里有不是 UTF-8 的文件路径时，不再抛 Python 堆栈：照常收集，不能识别的字节显示成 �，并在页头提示里列出。
- 查终点提交是否在远端时，分开报「不在远端」和「gh 查询失败（网络、权限、限流）」。
- 模块的 todo 或用法草案读不到时，写进页头提示，不再静默跳过。
- 验收之后只改了代码、没改 spec／tasks 文件的提交，在页头提示里列出（不算进范围）。

## 开发

```text
python3 -B -m unittest discover -s plugins/delivery-brief/tests
claude plugin validate .
```

讲法的规格在 [`plugins/delivery-brief/references/brief-rules.md`](plugins/delivery-brief/references/brief-rules.md)，
流程在 [`plugins/delivery-brief/commands/brief.md`](plugins/delivery-brief/commands/brief.md)。
本仓库用 spec-guard 开发，需求与计划在 `spec/` 和 `tasks/`。

当前状态：能力图上的五个模块（事实收集、模块讲解、交叉核对、界面截图、里程碑讲解）都已完成。已知局限见「版本记录」与
[docs/facts-schema.md](docs/facts-schema.md)：含 `[[` 的路径没法写成引用；模块范围是按文件约定推断的；里程碑页不支持交叉核对。

## 许可证

MIT，见 [LICENSE](LICENSE)。
