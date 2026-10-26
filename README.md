# taskboard

**看板不一定要是某个 SaaS。**

`taskboard` 把一个纯文本文件当作任务看板：每行一条任务，按状态自动分组展示。
文件可以用 git 管，可以用任何编辑器改，也可以在服务器上 `cat` 出来看。

- 零依赖，Python 3.10+ 标准库
- 单文件运行，数据就是一个 `.txt`
- 不联网、没有后台服务、没有账号

<!-- ipos:install -->
## 安装

零依赖，Python 3.10+ 即可：

```bash
pip install sureshbart-taskboard
```

装完直接用命令名调用：

```bash
taskboard --help
```

也可以不用安装，直接把 `taskboard.py` 拷走用——它只依赖标准库。

## 用法

看板文件（叫什么都行，比如 `board.txt`）：

```
# 看板文件，# 开头的行是注释

[todo] 写接口文档 @me #doc
[doing] 修登录超时 @ana #bug
[done] 初始化仓库
```

展示：

```bash
python taskboard.py board.txt
```

## 输出

看板按状态分组展示，每组先给出状态名与条数，再列任务：

```
TODO  (1)
  #2    写接口文档  @me #doc

DOING  (1)
  #3    修登录超时  @ana #bug

DONE  (1)
  #4    初始化仓库

共 3 个任务。
```

`#2` 是任务在文件里的行号——后面 `move` 命令就是用它定位的。

## 行格式

```
[状态] 任务描述 @负责人 #标签
```

**状态**中英文都认：

| 中文 | 英文 |
|---|---|
| 待办 / 未开始 | `todo` |
| 进行中 / 在做 | `doing` |
| 完成 / 已完成 | `done` |
| 阻塞 | `blocked` |

不写状态默认是 `todo`。分组顺序固定为 `todo → doing → blocked → done`，
所以"阻塞"永远排在"完成"前面——这通常是你想要的顺序。

**负责人**用 `@名字`，**标签**用 `#标签`，都可以有多个，也可以都没有。

## 三个命令

```bash
# 展示（默认命令就是 show）
python taskboard.py board.txt
python taskboard.py board.txt --json

# 追加一条任务
python taskboard.py board.txt --add "写接口文档 @me #doc"
```

追加时想指定初始状态：

```bash
python taskboard.py board.txt --add "调研新框架" --status doing
```

改状态（第二个参数是**文件行号**，不是任务编号）：

```bash
python taskboard.py board.txt --move 3 done
```

行号可以用 `nl -ba board.txt` 查，或者直接用 `show` 输出里每行前面的 `#3`。

## 几个设计选择

**为什么不用 JSON 存？**
JSON 写起来啰嗦，而且手改的时候容易破坏结构。纯文本的代价是解析简单，收益是任何编辑器、
`vim`、`notepad`、甚至一条 `echo` 命令都能改。

**为什么 `move` 按行号而不是任务 ID？**
加 ID 意味着文件里每行要写两遍标识，重复且容易不同步。行号天然唯一，改动位置时也不用维护。
代价是插入行会让后面的行号偏移——所以建议**只在末尾追加**（`--add` 就是这么做的）。

**为什么状态只有四种？**
这个工具的价值在于"一眼看到全貌"，状态一多就退化成列表了。四种状态刚好覆盖
"还没开始 / 在做 / 卡住了 / 做完了"。

## 已知局限

- **不做排序**。同一状态内按文件里的原始顺序展示。
- **不检测重复任务**。同一个描述写两遍就是两条。
- **状态写在方括号里**，写成 `状态: xxx` 这种格式会被当成普通文本，状态回落到 `todo`。
- **不处理转义**。描述里的 `#` 会被当作标签的开头。
- **多行任务不支持**。一条任务必须在一行内。

## 跑测试

```bash
python test_taskboard.py
```

---

## 关于作者

sureshbart 相信最朴素的工具最耐用。这个工具把看板变成一个普通文件——谁都能打开、谁能进 git、谁都能接手。

- 个人主页：<https://sureshbart.github.io>
- 仓库：<https://github.com/sureshbart/taskboard>

## 许可

MIT，见 [LICENSE](LICENSE)。
