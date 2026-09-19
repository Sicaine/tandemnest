"""A small, strict YAML subset parser.

TandemNest builds with the Python standard library only, so that Cloudflare
Pages and GitHub Actions can run the build with no install step. This module
covers the subset of YAML the project actually uses:

  * block mappings and block sequences, nested to any depth
  * sequences of mappings
  * flow sequences on one line: ``key: [a, b, c]``
  * scalars: strings, ints, floats, booleans, null, dates (kept as strings)
  * single and double quoted strings
  * ``|`` and ``>`` block scalars
  * ``#`` comments

Anything outside the subset raises :class:`YamlishError` with a line number
rather than being silently misparsed. That is the whole point: a config typo
should fail the build, not quietly publish a wrong Bitcoin address.
"""

from __future__ import annotations

import re

__all__ = ["YamlishError", "parse", "parse_file"]

_TRUE = {"true", "yes", "on"}
_FALSE = {"false", "no", "off"}
_NULL = {"", "null", "~"}
_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(r"^[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?$")
_KEY_RE = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_.\- ]*|\"[^\"]*\"|'[^']*')\s*:(\s|$)")


class YamlishError(ValueError):
    """Raised when input falls outside the supported YAML subset."""

    def __init__(self, message: str, line: int, source: str = "<string>") -> None:
        super().__init__(f"{source}:{line}: {message}")
        self.line = line
        self.source = source


class _Line:
    __slots__ = ("indent", "text", "no")

    def __init__(self, indent: int, text: str, no: int) -> None:
        self.indent = indent
        self.text = text
        self.no = no

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"_Line({self.indent}, {self.text!r}, {self.no})"


def _strip_comment(text: str) -> str:
    """Remove a trailing ``#`` comment that is not inside quotes."""
    out = []
    quote = None
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            out.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < len(text):
                out.append(text[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#" and (i == 0 or text[i - 1] in " \t"):
            break
        else:
            out.append(ch)
        i += 1
    return "".join(out).rstrip()


def _scan(text: str, source: str) -> list[_Line]:
    lines: list[_Line] = []
    for no, raw in enumerate(text.replace("\r\n", "\n").split("\n"), start=1):
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise YamlishError("tab used for indentation; use spaces", no, source)
        stripped = _strip_comment(raw)
        if not stripped.strip():
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        lines.append(_Line(indent, stripped.strip(), no))
    return lines


def _unquote(token: str) -> str:
    body = token[1:-1]
    if token[0] == "'":
        return body.replace("''", "'")
    out = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body):
            nxt = body[i + 1]
            out.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\", "/": "/"}.get(nxt, "\\" + nxt))
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _scalar(token: str, line: int, source: str):
    token = token.strip()
    if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
        return _unquote(token)
    low = token.lower()
    if low in _NULL:
        return None
    if low in _TRUE:
        return True
    if low in _FALSE:
        return False
    if _INT_RE.match(token):
        return int(token)
    if _FLOAT_RE.match(token) and not _INT_RE.match(token):
        try:
            return float(token)
        except ValueError:  # pragma: no cover - regex already guards this
            pass
    return token


def _flow_sequence(token: str, line: int, source: str) -> list:
    inner = token[1:-1].strip()
    if not inner:
        return []
    items, buf, quote = [], [], None
    for ch in inner:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch == ",":
            items.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    items.append("".join(buf))
    return [_scalar(i, line, source) for i in items if i.strip() != ""]


def _value_token(token: str, line: int, source: str):
    token = token.strip()
    if token.startswith("[") and token.endswith("]"):
        return _flow_sequence(token, line, source)
    if token.startswith("{"):
        raise YamlishError("flow mappings ({...}) are not supported", line, source)
    return _scalar(token, line, source)


class _Parser:
    def __init__(self, lines: list[_Line], source: str) -> None:
        self.lines = lines
        self.source = source
        self.i = 0

    def peek(self) -> _Line | None:
        return self.lines[self.i] if self.i < len(self.lines) else None

    def block(self, indent: int):
        line = self.peek()
        if line is None or line.indent < indent:
            return None
        if line.text.startswith("- ") or line.text == "-":
            return self.sequence(line.indent)
        return self.mapping(line.indent)

    def sequence(self, indent: int) -> list:
        items: list = []
        while True:
            line = self.peek()
            if line is None or line.indent < indent:
                break
            if line.indent > indent:
                raise YamlishError("unexpected indentation in sequence", line.no, self.source)
            if not (line.text.startswith("- ") or line.text == "-"):
                break
            self.i += 1
            rest = line.text[1:].strip()
            if not rest:
                child = self.block(indent + 1)
                items.append(child)
                continue
            if _KEY_RE.match(rest):
                # "- key: value" starts an inline mapping whose remaining keys
                # are indented to the column where `key` begins.
                key_indent = indent + (len(line.text) - len(line.text[1:].lstrip()))
                mapping: dict = {}
                self._mapping_entry(_Line(key_indent, rest, line.no), mapping, key_indent)
                merged = self.mapping(key_indent, into=mapping)
                items.append(merged)
                continue
            items.append(_value_token(rest, line.no, self.source))
        return items

    def mapping(self, indent: int, into: dict | None = None) -> dict:
        out: dict = into if into is not None else {}
        while True:
            line = self.peek()
            if line is None or line.indent < indent:
                break
            if line.indent > indent:
                raise YamlishError("unexpected indentation in mapping", line.no, self.source)
            if line.text.startswith("- "):
                break
            if not _KEY_RE.match(line.text):
                raise YamlishError(f"expected 'key: value', got {line.text!r}", line.no, self.source)
            self.i += 1
            self._mapping_entry(line, out, indent)
        return out

    def _mapping_entry(self, line: _Line, out: dict, indent: int) -> None:
        key_raw, _, rest = line.text.partition(":")
        key = key_raw.strip()
        if len(key) >= 2 and key[0] == key[-1] and key[0] in "\"'":
            key = _unquote(key)
        if key in out:
            raise YamlishError(f"duplicate key {key!r}", line.no, self.source)
        rest = rest.strip()
        if rest in ("|", "|-", ">", ">-"):
            out[key] = self._block_scalar(rest, indent)
            return
        if rest == "":
            child = self.block(indent + 1)
            out[key] = child if child is not None else None
            return
        out[key] = _value_token(rest, line.no, self.source)

    def _block_scalar(self, marker: str, indent: int) -> str:
        parts: list[str] = []
        base = None
        while True:
            line = self.peek()
            if line is None or line.indent <= indent:
                break
            if base is None:
                base = line.indent
            parts.append(" " * (line.indent - base) + line.text)
            self.i += 1
        if marker.startswith(">"):
            text = " ".join(p.strip() for p in parts)
        else:
            text = "\n".join(parts)
        return text if marker.endswith("-") else (text + "\n" if text else "")


def parse(text: str, source: str = "<string>"):
    """Parse a YAML-subset document and return Python data (or ``{}`` if empty)."""
    lines = _scan(text, source)
    if not lines:
        return {}
    parser = _Parser(lines, source)
    value = parser.block(lines[0].indent)
    if parser.peek() is not None:
        leftover = parser.peek()
        raise YamlishError("could not parse remainder of document", leftover.no, source)
    return value if value is not None else {}


def parse_file(path) -> dict:
    import pathlib

    p = pathlib.Path(path)
    return parse(p.read_text(encoding="utf-8"), str(p))
