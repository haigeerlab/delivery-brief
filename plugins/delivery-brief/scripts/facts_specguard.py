"""Parse spec-guard's documented files from text: capability map, module Spec, todo, usage drafts.

Works on file contents (the caller reads them at the right revision with git show) and never calls
spec-guard's own scripts: only the file formats spec-guard publishes are relied on.
"""
import re

FENCE = re.compile(r"^\s*(```|~~~)")
MARKER = re.compile(r"<!--\s*spec-guard:\s*review\s+(pending|approved(?:\s+[0-9a-f]+)?)\s*-->")
AC_LINE = re.compile(r"^\s*[-*]\s*\**(AC\d+)\**\s*(?:[（(][^）)]*[）)]\s*)?[:：]\s*(.*)$")
TODO_LINE = re.compile(r"^[-*]\s+\[([ xX])\]\s+(.*)$")
GATE = re.compile(r"[（(]\s*gate\s*[)）]")
REPORT = re.compile(r"[（(]\s*report\s*[)）]")
SPLIT = re.compile(r"[,，、]")


def visible_lines(text):
    """Lines outside fenced code blocks."""
    lines, fenced = [], False
    for line in text.splitlines():
        if FENCE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            lines.append(line)
    return lines


def _cells(line):
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def _names(value):
    return [item.strip().strip("`").strip() for item in SPLIT.split(value)
            if item.strip().strip("`").strip() not in ("", "—", "-", "–")]


def _unquote(cell):
    """Drop the backticks only when the whole cell is one code span."""
    return cell[1:-1] if re.match(r"^`[^`]+`$", cell) else cell


def _table_after(lines, header):
    """Rows of the first table whose header matches (case-insensitive)."""
    wanted = [h.lower() for h in header]
    for index, line in enumerate(lines):
        if line.lstrip().startswith("|") and [c.lower() for c in _cells(line)] == wanted:
            rows = []
            for row in lines[index + 2:]:
                if not row.lstrip().startswith("|"):
                    break
                cells = _cells(row)
                if len(cells) == len(header):
                    rows.append(cells)
            return rows
    return None


def _section(lines, title):
    out, inside = [], False
    for line in lines:
        if line.startswith("## "):
            inside = line[3:].strip() == title
            continue
        if inside:
            out.append(line)
    return out


def parse_map(text):
    lines = visible_lines(text)
    modules = {}
    for module_id, responsibility, depends in _table_after(lines, ("Module id", "Responsibility", "Depends on")) or []:
        modules[module_id.strip("`")] = {"responsibility": responsibility, "dependsOn": _names(depends)}
    order = []
    for line in lines:
        if line.startswith("Build order:"):
            for group in line[len("Build order:"):].split("→"):
                order.extend(_names(group))
    return {"modules": modules, "buildOrder": order}


def parse_spec(text):
    marker = None
    for line in text.splitlines():
        match = MARKER.search(line)
        if match:
            marker = " ".join(match.group(1).split())
            break
    acs, open_ac = [], False
    for line in visible_lines(text):
        match = AC_LINE.match(line)
        if match:
            acs.append({"id": match.group(1), "text": match.group(2).strip()})
            open_ac = True
        elif open_ac and line.startswith((" ", "\t")) and line.strip() and not line.strip().startswith(("-", "*")):
            acs[-1]["text"] += line.strip()
        else:
            open_ac = False
    numbered = bool(acs)
    if not acs:
        lines = visible_lines(text)
        section = _section(lines, "成功标准") or _section(lines, "Success Criteria")
        for line in section:
            bullet = re.match(r"^[-*]\s+(.*)$", line)
            if bullet:
                acs.append({"id": None, "text": bullet.group(1).strip()})
            elif acs and line.startswith((" ", "\t")) and line.strip():
                acs[-1]["text"] += line.strip()
    return {"marker": marker, "acs": acs, "numbered": numbered}


def parse_todo(text):
    items = []
    for line in visible_lines(text):
        match = TODO_LINE.match(line)
        if not match:
            continue
        body = match.group(2).strip()
        kind = "gate" if GATE.search(body) else "report" if REPORT.search(body) else "task"
        items.append({"text": body, "checked": match.group(1) != " ", "kind": kind,
                      "deferred": body.startswith("延期：")})
    return items


USAGE_HEADING = re.compile(r"^###\s+(U\d+)\s*[:：]\s*(.*)$")


def milestone_row(text, milestone):
    """One Milestones row of a usage draft with its usage titles, or None when the draft has no such row.

    confirmed: the draft carries spec-guard's `<!-- spec-guard: milestone <M> confirmed ...` line (written by
    milestone_mark after the user passed the milestone).
    """
    lines = visible_lines(text)
    rows = _table_after(_section(lines, "Milestones"), ("Milestone", "Usage", "Modules"))
    for name, usage, modules in rows or []:
        if name.strip("`") != milestone:
            continue
        titles = {}
        for line in _section(lines, "Typical usage"):
            match = USAGE_HEADING.match(line.strip())
            if match:
                titles[match.group(1)] = match.group(2).strip()
        confirmed = re.compile(r"<!--\s*spec-guard:\s*milestone\s+%s\s+confirmed\b" % re.escape(milestone))
        return {"milestone": milestone,
                "usages": [{"id": u, "title": titles.get(u, "")} for u in _names(usage)],
                "modules": _names(modules),
                "confirmed": any(confirmed.search(line) for line in text.splitlines())}
    return None


def usage_for_module(drafts, module_id, warnings=None):
    """Which draft and milestone the module belongs to, with its entries; None when it is in none."""
    for label in sorted(drafts):
        lines = visible_lines(drafts[label])
        milestones = _table_after(_section(lines, "Milestones"), ("Milestone", "Usage", "Modules"))
        entries = _table_after(_section(lines, "Entry points"), ("Entry", "Does", "Module"))
        if milestones is None or entries is None:
            if warnings is not None:
                warnings.append("%s: 用法草案缺少 Entry points 或 Milestones 表，没有读取" % label)
            continue
        for milestone, usage, modules in milestones:
            if module_id in _names(modules):
                return {
                    "file": label,
                    "milestone": milestone.strip("`"),
                    "usages": _names(usage),
                    "entries": [{"entry": _unquote(entry), "does": does}
                                for entry, does, owners in entries if module_id in _names(owners)],
                }
    return None
