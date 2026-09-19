"""A small deterministic Markdown renderer.

Deliberately not CommonMark. It supports exactly what TandemNest pages need,
and it emits semantic, accessible HTML that reads correctly with JavaScript
disabled:

  * ATX headings (``#``..``####``) with stable slug ids
  * paragraphs, ``---`` rules, blockquotes
  * unordered and ordered lists with one level of nesting
  * fenced code blocks with a language class
  * GitHub-style pipe tables with alignment and a ``<caption>`` from a
    preceding ``Table: ...`` line
  * inline bold, italic, code, links, images, autolinked bare URLs
  * raw HTML blocks passed through untouched

Links are post-processed so that off-site links get ``rel`` and the build can
mark disclosed referral links as ``sponsored``.
"""

from __future__ import annotations

import html
import re
import unicodedata

__all__ = ["render", "slugify", "headings"]

_CODE_FENCE = re.compile(r"^```([A-Za-z0-9_+-]*)\s*$")
_TABLE_DELIM = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?$")
_OL_ITEM = re.compile(r"^(\d+)[.)]\s+(.*)$")
_UL_ITEM = re.compile(r"^[-*]\s+(.*)$")
_BARE_URL = re.compile(r"(?<![\"'=(\w])(https?://[^\s<>\"')]+[^\s<>\"').,;:])")
_RAW_HTML_START = re.compile(r"^<(/?)(div|section|table|figure|details|aside|nav|ul|ol|p|script|style|form|iframe)\b", re.I)


def slugify(text: str) -> str:
    """Stable, ASCII, URL-safe anchor id for a heading."""
    text = re.sub(r"`|\*\*|\*|_", "", text)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9\s-]", "", text).strip().lower()
    return re.sub(r"[\s-]+", "-", text) or "section"


def _inline(text: str) -> str:
    """Render inline markup. Escapes first, so page text can never inject HTML."""
    placeholders: list[str] = []

    def stash(fragment: str) -> str:
        placeholders.append(fragment)
        return f"\x00{len(placeholders) - 1}\x00"

    # Pull out code spans before escaping so backticked text stays literal.
    def code_span(m: re.Match) -> str:
        return stash("<code>" + html.escape(m.group(1)) + "</code>")

    text = re.sub(r"`([^`]+)`", code_span, text)
    text = html.escape(text, quote=False)

    def image(m: re.Match) -> str:
        alt, src = m.group(1), m.group(2)
        return stash(f'<img src="{html.escape(src, quote=True)}" alt="{html.escape(alt, quote=True)}" loading="lazy">')

    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", image, text)

    def link(m: re.Match) -> str:
        label, href = m.group(1), m.group(2)
        return stash(f'<a href="{html.escape(href, quote=True)}">{_inline_light(label)}</a>')

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)
    text = _BARE_URL.sub(lambda m: stash(f'<a href="{html.escape(m.group(1), quote=True)}">{html.escape(m.group(1))}</a>'), text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", text)
    for i, frag in enumerate(placeholders):
        text = text.replace(f"\x00{i}\x00", frag)
    return text


def _inline_light(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return text


def _table(rows: list[str], caption: str | None) -> str:
    def cells(line: str) -> list[str]:
        line = line.strip()
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]
        return [c.strip() for c in line.split("|")]

    header = cells(rows[0])
    aligns = []
    for spec in cells(rows[1]):
        left, right = spec.startswith(":"), spec.endswith(":")
        aligns.append("center" if left and right else "right" if right else "left" if left else "")
    out = ['<div class="table-scroll">', "<table>"]
    if caption:
        out.append("<caption>" + _inline(caption) + "</caption>")
    out.append("<thead><tr>")
    for i, cell in enumerate(header):
        style = f' style="text-align:{aligns[i]}"' if i < len(aligns) and aligns[i] else ""
        out.append(f'<th scope="col"{style}>' + _inline(cell) + "</th>")
    out.append("</tr></thead><tbody>")
    for row in rows[2:]:
        values = cells(row)
        out.append("<tr>")
        for i, cell in enumerate(values):
            style = f' style="text-align:{aligns[i]}"' if i < len(aligns) and aligns[i] else ""
            tag = "th" if i == 0 and len(values) > 1 and cell and not cell[0].isdigit() and len(header) > 2 else "td"
            scope = ' scope="row"' if tag == "th" else ""
            out.append(f"<{tag}{scope}{style}>" + _inline(cell) + f"</{tag}>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def _list_block(items: list[tuple[int, str, str]]) -> str:
    """Render collected list items as valid nested HTML.

    Items are ``(indent, marker, text)``. Anything indented by two spaces or
    more becomes a child list of the preceding item, so the nested ``<ul>``
    lives inside its parent ``<li>`` as the HTML spec requires.
    """
    tree: list[list] = []
    for indent, marker, text in items:
        if indent >= 2 and tree:
            tree[-1][2].append((marker, text))
        else:
            tree.append([marker, text, []])

    def render_nodes(nodes) -> str:
        out: list[str] = []
        idx = 0
        while idx < len(nodes):
            marker = nodes[idx][0]
            run = []
            while idx < len(nodes) and nodes[idx][0] == marker:
                run.append(nodes[idx])
                idx += 1
            tag = "ol" if marker == "ol" else "ul"
            out.append(f"<{tag}>")
            for node in run:
                children = node[2]
                inner = _inline(node[1])
                if children:
                    inner += "\n" + render_nodes([[m, t, []] for m, t in children])
                out.append("<li>" + inner + "</li>")
            out.append(f"</{tag}>")
        return "\n".join(out)

    return render_nodes(tree)


def render(md: str) -> str:
    """Render Markdown source to an HTML fragment."""
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    pending_caption: str | None = None

    def flush_list(buf):
        if buf:
            out.append(_list_block(buf))
            buf.clear()

    list_buf: list[tuple[int, str, str]] = []

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_list(list_buf)
            i += 1
            continue

        fence = _CODE_FENCE.match(stripped)
        if fence:
            flush_list(list_buf)
            lang = fence.group(1)
            body: list[str] = []
            i += 1
            while i < len(lines) and not _CODE_FENCE.match(lines[i].strip()):
                body.append(lines[i])
                i += 1
            i += 1
            cls = f' class="language-{lang}"' if lang else ""
            out.append("<pre><code" + cls + ">" + html.escape("\n".join(body)) + "</code></pre>")
            continue

        if _RAW_HTML_START.match(stripped):
            flush_list(list_buf)
            block = [line]
            i += 1
            while i < len(lines) and lines[i].strip():
                block.append(lines[i].rstrip())
                i += 1
            out.append("\n".join(block))
            continue

        if stripped.startswith("Table:"):
            flush_list(list_buf)
            pending_caption = stripped[len("Table:") :].strip()
            i += 1
            continue

        if "|" in stripped and i + 1 < len(lines) and _TABLE_DELIM.match(lines[i + 1].strip()):
            flush_list(list_buf)
            rows = [stripped, lines[i + 1].strip()]
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(lines[i].strip())
                i += 1
            out.append(_table(rows, pending_caption))
            pending_caption = None
            continue

        if stripped in ("---", "***", "___"):
            flush_list(list_buf)
            out.append("<hr>")
            i += 1
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            flush_list(list_buf)
            level = len(m.group(1))
            text = m.group(2).strip()
            sid = slugify(text)
            if level == 1:
                out.append(f"<h1>{_inline(text)}</h1>")
            else:
                out.append(f'<h{level} id="{sid}">{_inline(text)}</h{level}>')
            i += 1
            continue

        if stripped.startswith(">"):
            flush_list(list_buf)
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            out.append("<blockquote><p>" + _inline(" ".join(quote)) + "</p></blockquote>")
            continue

        indent = len(line) - len(line.lstrip(" "))
        ul = _UL_ITEM.match(stripped)
        ol = _OL_ITEM.match(stripped)
        if ul:
            list_buf.append((indent, "ul", ul.group(1)))
            i += 1
            continue
        if ol:
            list_buf.append((indent, "ol", ol.group(2)))
            i += 1
            continue

        flush_list(list_buf)
        para = [stripped]
        i += 1
        while i < len(lines) and lines[i].strip() and not _looks_like_block(lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append("<p>" + _inline(" ".join(para)) + "</p>")

    flush_list(list_buf)
    return "\n".join(out)


def _looks_like_block(line: str) -> bool:
    s = line.strip()
    return bool(
        _CODE_FENCE.match(s)
        or re.match(r"^#{1,4}\s", s)
        or _UL_ITEM.match(s)
        or _OL_ITEM.match(s)
        or s.startswith(">")
        or s in ("---", "***", "___")
        or s.startswith("Table:")
        or _RAW_HTML_START.match(s)
        or "|" in s
    )


def headings(md: str) -> list[tuple[int, str, str]]:
    """Return ``(level, text, slug)`` for h2..h4 headings, skipping code blocks."""
    found = []
    in_fence = False
    for line in md.replace("\r\n", "\n").split("\n"):
        s = line.strip()
        if _CODE_FENCE.match(s):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{2,4})\s+(.*)$", s)
        if m:
            text = m.group(2).strip()
            found.append((len(m.group(1)), text, slugify(text)))
    return found
