"""Markdown subset parser shared by check_brief and render_brief."""
import unittest

import fixtures  # noqa: F401  (puts scripts/ on sys.path)
import brief_markdown as md

SOURCE = """# 标题不支持一级以外的用途

<details>
<summary>先懂这几个词</summary>

- **能力图**：模块表

</details>

## 为什么改

一段话，含 `code`、**粗体**、[链接](https://example.com) 与引用 [[src/a.py:L3-L9]]。
第二行接着同一段。

| AC | 证据 |
|---|---|
| AC1 | [[tests/t.py:L10]] 与 `a \\| b` |

```python
x = "[[not/a/cite.py:L1]]"
```

```mermaid
flowchart LR
  A --> B
```

1. 第一步 [[a.md]]
2. 第二步
   续行
   - 子项
     - 第三层不支持

> 引用块不支持

<div>HTML 不支持</div>
"""


class BlocksTest(unittest.TestCase):
    def setUp(self):
        self.blocks = md.parse(SOURCE)
        self.types = [b["type"] for b in self.blocks]

    def test_block_sequence(self):
        self.assertEqual(self.types, ["heading", "details", "heading", "paragraph", "table", "code", "code",
                                      "list", "unsupported", "unsupported"])

    def test_heading_levels(self):
        self.assertEqual(self.blocks[0]["level"], 1)
        self.assertEqual(md.plain(self.blocks[2]["inlines"]), "为什么改")
        self.assertEqual(self.blocks[2]["level"], 2)

    def test_details(self):
        details = self.blocks[1]
        self.assertEqual(details["summary"], "先懂这几个词")
        self.assertEqual([b["type"] for b in details["blocks"]], ["list"])

    def test_paragraph_inlines(self):
        kinds = [token[0] for token in self.blocks[3]["inlines"]]
        for kind in ("text", "code", "bold", "link", "cite"):
            self.assertIn(kind, kinds)
        cite = [t for t in self.blocks[3]["inlines"] if t[0] == "cite"][0]
        self.assertEqual(cite, ("cite", "src/a.py", 3, 9))
        self.assertIn("第二行接着同一段", md.plain(self.blocks[3]["inlines"]))

    def test_table_with_escaped_pipe(self):
        table = self.blocks[4]
        self.assertEqual([md.plain(c) for c in table["header"]], ["AC", "证据"])
        self.assertEqual(len(table["rows"]), 1)
        cell = table["rows"][0][1]
        self.assertIn(("cite", "tests/t.py", 10, 10), cell)
        self.assertIn(("code", "a | b"), cell)

    def test_code_blocks_keep_text_and_no_cites(self):
        code, mermaid = self.blocks[5], self.blocks[6]
        self.assertEqual(code["lang"], "python")
        self.assertIn("[[not/a/cite.py:L1]]", code["text"])
        self.assertEqual(mermaid["lang"], "mermaid")
        self.assertEqual(mermaid["text"], "flowchart LR\n  A --> B")
        self.assertEqual(md.citations([code, mermaid]), [])

    def test_list_nesting_and_continuation(self):
        lst = self.blocks[7]
        self.assertTrue(lst["ordered"])
        self.assertEqual(len(lst["items"]), 2)
        second = lst["items"][1]
        self.assertIn("续行", md.plain(second["inlines"]))
        self.assertFalse(second["children"]["ordered"])
        self.assertEqual(md.plain(second["children"]["items"][0]["inlines"]), "子项")
        self.assertTrue(any(b["type"] == "unsupported" for b in second["children"]["items"][0]["extra"]))

    def test_unsupported_keeps_text_and_line(self):
        quote, html = self.blocks[8], self.blocks[9]
        self.assertEqual(quote["text"], "> 引用块不支持")
        self.assertEqual(html["text"], "<div>HTML 不支持</div>")
        self.assertTrue(quote["line"] > 0)

    def test_citations_collects_everywhere_outside_code(self):
        cites = [c[1:] for c in md.citations(self.blocks)]
        self.assertEqual(cites, [("src/a.py", 3, 9), ("tests/t.py", 10, 10), ("a.md", None, None)])


class InlineTest(unittest.TestCase):
    def test_bad_citation(self):
        tokens = md.inlines("看 [[src/a.py:L9-L3]] 和 [[有 空格.py]] 和 [[a.py:Lx]]")
        self.assertEqual([t[0] for t in tokens if t[0] != "text"], ["badcite", "badcite", "badcite"])

    def test_single_line_citation(self):
        self.assertEqual(md.inlines("[[a/b.py:L7]]"), [("cite", "a/b.py", 7, 7)])

    def test_code_span_hides_citation(self):
        self.assertEqual(md.inlines("`[[a.py]]`"), [("code", "[[a.py]]")])


class OutputTest(unittest.TestCase):
    def test_output_block_and_reference(self):
        blocks = md.parse("见 [[out:O1]]。\n\n```output O1\n$ python3 x.py\nok 1\n```\n")
        self.assertEqual(md.tokens_of(blocks, "outref"), [("outref", "O1")])
        outputs = md.output_blocks(blocks)
        self.assertEqual(list(outputs), ["O1"])
        self.assertTrue(outputs["O1"]["text"].startswith("$ python3 x.py"))

    def test_bad_output_reference_is_badcite(self):
        self.assertEqual(md.inlines("[[out:x]]")[0][0], "badcite")


class SectionsTest(unittest.TestCase):
    def test_sections_split_on_h2(self):
        sections = md.sections(md.parse("前言\n\n## 甲\n\n内容\n\n### 子\n\n## 乙\n"))
        self.assertEqual([title for title, _ in sections], [None, "甲", "乙"])
        self.assertEqual([b["type"] for b in sections[1][1]], ["paragraph", "heading"])


if __name__ == "__main__":
    unittest.main()
