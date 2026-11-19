"""Parse the Markdown subset a brief source is written in. check_brief and render_brief both read this tree.

Blocks: heading, paragraph, list (two levels), table, code (lang "mermaid" for diagrams), details, unsupported.
Inline tokens: ("text", s), ("code", s), ("bold", s), ("link", text, url), ("cite", path, start, end),
("badcite", raw). A citation is [[path]], [[path:L12]] or [[path:L12-L30]]; inside code it is plain text.
Anything else is kept verbatim as an `unsupported` block so the checker can name it and the page still shows it.
"""
import re

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^(```|~~~)\s*([\w-]*)\s*$")
LIST_ITEM = re.compile(r"^( *)([-*+]|\d+[.)])\s+(.*)$")
INLINE = re.compile(r"`([^`]+)`|\[\[(.*?)\]\]|\[([^\]]+)\]\(([^)\s]+)\)|\*\*(.+?)\*\*")
CITE = re.compile(r"^([^\s:\[\]]+)(?::L(\d+)(?:-L(\d+))?)?$")
PIPE = "\x00PIPE\x00"


def inlines(text):
    tokens, pos = [], 0
    for match in INLINE.finditer(text):
        if match.start() > pos:
            tokens.append(("text", text[pos:match.start()]))
        code, cite, link_text, link_url, bold = match.groups()
        if code is not None:
            tokens.append(("code", code))
        elif cite is not None:
            parsed = CITE.match(cite)
            start = int(parsed.group(2)) if parsed and parsed.group(2) else None
            end = int(parsed.group(3)) if parsed and parsed.group(3) else start
            if parsed and (start is None or 1 <= start <= end):
                tokens.append(("cite", parsed.group(1), start, end))
            else:
                tokens.append(("badcite", match.group(0)))
        elif link_text is not None:
            tokens.append(("link", link_text, link_url))
        else:
            tokens.append(("bold", bold))
        pos = match.end()
    if pos < len(text):
        tokens.append(("text", text[pos:]))
    return tokens


def plain(tokens):
    return "".join(token[1] for token in tokens)


def _join(left, right):
    if left and right and left[-1].isascii() and left[-1].isalnum() and right[0].isascii() and right[0].isalnum():
        return left + " " + right
    return left + right


def _cells(line):
    stripped = line.strip().replace("\\|", PIPE)
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [inlines(cell.strip().replace(PIPE, "|")) for cell in stripped.split("|")]


def _is_separator(line):
    return bool(re.match(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$", line.strip()))


def _starts_block(line):
    stripped = line.strip()
    return (not stripped or HEADING.match(line) or FENCE.match(stripped) or LIST_ITEM.match(line)
            or stripped.startswith(("|", ">", "<")) or re.match(r"^(-{3,}|\*{3,})$", stripped))


def _list_level(indent):
    return 0 if indent < 2 else 1 if indent < 5 else 2


def _parse_list(lines, i):
    """Parse a list starting at lines[i]; return (block, next index)."""
    first = LIST_ITEM.match(lines[i])
    block = {"type": "list", "ordered": first.group(2)[0].isdigit(), "items": [], "line": i + 1}
    current, child = None, None
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            nxt = next((l for l in lines[i + 1:] if l.strip()), "")
            if LIST_ITEM.match(nxt) or (nxt.startswith("  ") and current is not None):
                i += 1
                continue
            break
        match = LIST_ITEM.match(line)
        if match:
            level = _list_level(len(match.group(1)))
            item = {"raw": match.group(3), "children": None, "extra": [], "line": i + 1}
            if level == 0:
                block["items"].append(item)
                current, child = item, None
            elif level == 1 and current is not None:
                if current["children"] is None:
                    current["children"] = {"type": "list", "ordered": match.group(2)[0].isdigit(), "items": [],
                                           "line": i + 1}
                current["children"]["items"].append(item)
                child = item
            else:
                owner = child or current
                owner["extra"].append({"type": "unsupported", "text": line.strip(), "line": i + 1,
                                       "reason": "列表最多两层"})
        elif line.startswith("  ") and current is not None:
            owner = child or current
            owner["raw"] = _join(owner["raw"], line.strip())
        else:
            break
        i += 1
    for item in block["items"]:
        item["inlines"] = inlines(item.pop("raw"))
        if item["children"]:
            for sub in item["children"]["items"]:
                sub["inlines"] = inlines(sub.pop("raw"))
    return block, i


def parse(text, offset=0):
    lines = text.splitlines()
    blocks, i = [], 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        lineno = i + 1 + offset
        if not stripped:
            i += 1
            continue
        fence = FENCE.match(stripped)
        if fence:
            body, j = [], i + 1
            while j < len(lines) and lines[j].strip() != fence.group(1):
                body.append(lines[j])
                j += 1
            blocks.append({"type": "code", "lang": fence.group(2), "text": "\n".join(body), "line": lineno})
            i = j + 1
            continue
        if stripped == "<details>":
            j = i + 1
            summary_match = re.match(r"^<summary>(.*)</summary>$", lines[j].strip()) if j < len(lines) else None
            summary = summary_match.group(1) if summary_match else ""
            if summary_match:
                j += 1
            start = j
            while j < len(lines) and lines[j].strip() != "</details>":
                j += 1
            inner = parse("\n".join(lines[start:j]), offset=start + offset)
            blocks.append({"type": "details", "summary": summary, "blocks": inner, "line": lineno})
            i = j + 1
            continue
        heading = HEADING.match(line)
        if heading:
            blocks.append({"type": "heading", "level": len(heading.group(1)), "inlines": inlines(heading.group(2)),
                           "line": lineno})
            i += 1
            continue
        if stripped.startswith("|") and i + 1 < len(lines) and _is_separator(lines[i + 1]):
            header = _cells(line)
            rows, j = [], i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(_cells(lines[j]))
                j += 1
            blocks.append({"type": "table", "header": header, "rows": rows, "line": lineno})
            i = j
            continue
        if LIST_ITEM.match(line) and _list_level(len(LIST_ITEM.match(line).group(1))) == 0:
            block, i = _parse_list(lines, i)
            block["line"] += offset
            blocks.append(block)
            continue
        if _starts_block(line):
            blocks.append({"type": "unsupported", "text": stripped, "line": lineno, "reason": "不支持的写法"})
            i += 1
            continue
        text_acc, j = stripped, i + 1
        while j < len(lines) and not _starts_block(lines[j]):
            text_acc = _join(text_acc, lines[j].strip())
            j += 1
        blocks.append({"type": "paragraph", "inlines": inlines(text_acc), "line": lineno})
        i = j
    return blocks


def _walk_inlines(blocks):
    for block in blocks:
        kind = block["type"]
        if kind in ("heading", "paragraph"):
            yield block, block["inlines"]
        elif kind == "list":
            for item in block["items"]:
                yield block, item["inlines"]
                if item["children"]:
                    for sub in item["children"]["items"]:
                        yield block, sub["inlines"]
        elif kind == "table":
            for cell in block["header"]:
                yield block, cell
            for row in block["rows"]:
                for cell in row:
                    yield block, cell
        elif kind == "details":
            for pair in _walk_inlines(block["blocks"]):
                yield pair


def citations(blocks):
    return [token for _, tokens in _walk_inlines(blocks) for token in tokens if token[0] == "cite"]


def tokens_of(blocks, kind):
    return [token for _, tokens in _walk_inlines(blocks) for token in tokens if token[0] == kind]


def sections(blocks):
    """Split top-level blocks on level-2 headings: [(title or None, blocks)]."""
    out = [(None, [])]
    for block in blocks:
        if block["type"] == "heading" and block["level"] == 2:
            out.append((plain(block["inlines"]).strip(), []))
        else:
            out[-1][1].append(block)
    return out
