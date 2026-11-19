"""Count what one /delivery-brief:brief run cost in a Claude Code transcript (.jsonl).

A run starts at the user message that invokes the command and ends before the next invocation or at the end of the
transcript, so answers to the command's own stops (e.g. "continue?" at the size stop) stay in the run. Run each brief in a
fresh session so nothing unrelated follows it.
Usage: python3 -B dev/run_cost.py <transcript.jsonl> [...]
"""
import json
import re
import sys

COMMAND = "<command-name>/delivery-brief:brief"
ARGS = re.compile(r"<command-args>(.*?)</command-args>", re.S)


def _text(content):
    if isinstance(content, str):
        return content
    return " ".join(c.get("text", "") for c in content if isinstance(c, dict))


def _is_prompt(record):
    """A real user prompt, not a tool result."""
    if record.get("type") != "user" or record.get("isMeta"):
        return False
    content = record["message"]["content"]
    return isinstance(content, str) or not any(c.get("type") == "tool_result" for c in content if isinstance(c, dict))


def _result_chars(content):
    if isinstance(content, list):
        return sum(len(c.get("text", "")) for c in content if c.get("type") == "text")
    return len(content or "")


def runs(path):
    with open(path, encoding="utf-8") as fh:
        records = [json.loads(line) for line in fh if line.strip()]
    found, current = [], None
    for record in records:
        if _is_prompt(record):
            text = _text(record["message"]["content"])
            if COMMAND in text:
                if current is not None:
                    found.append(current)
                match = ARGS.search(text)
                current = {"args": match.group(1).strip() if match else "", "replies": {}, "toolCalls": 0,
                           "toolResultChars": 0}
                continue
        if current is None:
            continue
        message = record.get("message", {})
        if record.get("type") == "assistant":
            current["replies"][message.get("id")] = message.get("usage") or {}
            current["toolCalls"] += sum(1 for c in message.get("content", []) if c.get("type") == "tool_use")
        elif record.get("type") == "user" and isinstance(message.get("content"), list):
            for c in message["content"]:
                if c.get("type") == "tool_result":
                    current["toolResultChars"] += _result_chars(c.get("content"))
    if current is not None:
        found.append(current)
    return [_summary(r) for r in found]


def _summary(run):
    usages = list(run["replies"].values())
    tool_calls = run["toolCalls"]
    first = usages[0] if usages else {}
    return {
        "args": run["args"],
        "turns": len(usages),
        "firstContext": sum(first.get(k, 0) or 0 for k in
                            ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")),
        "cacheRead": sum(u.get("cache_read_input_tokens", 0) or 0 for u in usages),
        "cacheWrite": sum(u.get("cache_creation_input_tokens", 0) or 0 for u in usages),
        "output": sum(u.get("output_tokens", 0) or 0 for u in usages),
        "toolCalls": tool_calls,
        "toolResultChars": run["toolResultChars"],
    }


def main(argv):
    if not argv:
        print("用法：run_cost.py <会话记录.jsonl> [...]", file=sys.stderr)
        return 2
    for path in argv:
        for r in runs(path):
            print("%s | 轮数 %d | 首轮上下文 %d | 缓存读 %d | 缓存写 %d | 输出 %d | 工具调用 %d | 工具结果 %d 字符"
                  % (r["args"], r["turns"], r["firstContext"], r["cacheRead"], r["cacheWrite"], r["output"],
                     r["toolCalls"], r["toolResultChars"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
