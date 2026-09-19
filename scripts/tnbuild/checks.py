"""Build-time quality gates.

These run on every build (``make build``) and again over the generated output
(``make check``). The philosophy is that it should be hard to publish a
mistake: a bad link, a stale placeholder, an unverifiable crypto address or an
accidental secret should fail the build rather than reach the web.
"""

from __future__ import annotations

import pathlib
import re
import urllib.parse

__all__ = ["Problem", "scan_secrets", "check_output", "PRIVATE_FILES"]

# Files that must never be committed, and never appear in build output.
PRIVATE_FILES = ("TODO STEP BY STEP.html",)


class Problem:
    __slots__ = ("level", "where", "message")

    def __init__(self, level: str, where: str, message: str):
        self.level = level
        self.where = where
        self.message = message

    def __str__(self) -> str:
        return f"[{self.level}] {self.where}: {self.message}"


# --------------------------------------------------------------------------
# Secret detection
# --------------------------------------------------------------------------

# Each pattern is chosen for precision. A false positive fails a build, so
# these deliberately match credential *shapes*, not merely the words for them.
SECRET_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("PEM private key", re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")),
    ("PGP private key", re.compile(r"-----BEGIN PGP PRIVATE KEY BLOCK-----")),
    ("SSH private key", re.compile(r"-----BEGIN OPENSSH PRIVATE KEY-----")),
    ("Bitcoin WIF private key", re.compile(r"\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b")),
    ("BIP32 extended private key", re.compile(r"\b(?:xprv|yprv|zprv|tprv|uprv|vprv)[1-9A-HJ-NP-Za-km-z]{50,}\b")),
    ("OpenAI-style API key", re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("AWS access key id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("JSON Web Token", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
    ("Bearer token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{24,}={0,2}")),
    ("Private key hex (64 hex chars)", re.compile(r"(?i)\b(?:priv(?:ate)?[_-]?key|spend[_-]?key|view[_-]?key|secret[_-]?key)\W{0,4}\b[0-9a-f]{64}\b")),
    ("Credential assignment", re.compile(
        r"(?i)\b(?:password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token|"
        r"private[_-]?key|seed[_-]?phrase|mnemonic|wallet[_-]?seed)\s*[:=]\s*[\"']?[^\s\"'#<>]{8,}")),
]

# A mnemonic is 12/15/18/21/24 short lowercase words. Requiring a whole line of
# nothing but such words keeps ordinary prose (which has capitals, commas and
# longer words) from tripping it. This is a heuristic, not a BIP-39 dictionary
# check, and it is documented as such.
MNEMONIC_RE = re.compile(r"^\s*(?:[a-z]{3,8}\s+){11,23}[a-z]{3,8}\s*$", re.M)

# Values we deliberately publish, so the scanner does not flag our own copy.
ALLOWLIST = re.compile(
    r"(?i)(?:seed[_-]?phrase|private[_-]?key|mnemonic|password)\s*[:=]?\s*$"
)


def scan_secrets(text: str, where: str) -> list[Problem]:
    problems = []
    for name, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            snippet = match.group(0)
            if ALLOWLIST.search(snippet):
                continue
            line = text.count("\n", 0, match.start()) + 1
            redacted = snippet[:12] + "..." if len(snippet) > 16 else snippet
            problems.append(Problem("error", f"{where}:{line}",
                                    f"looks like a {name} ({redacted!r}) - refusing to publish"))
    for match in MNEMONIC_RE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        words = len(match.group(0).split())
        problems.append(Problem("error", f"{where}:{line}",
                                f"a line of {words} short lowercase words looks like a recovery phrase"))
    return problems


def scan_tree_for_secrets(root: pathlib.Path, patterns=("*.md", "*.yaml", "*.yml", "*.html", "*.json", "*.txt", "*.py", "*.css", "*.js")) -> list[Problem]:
    problems = []
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv"}
    for pattern in patterns:
        for path in sorted(root.rglob(pattern)):
            if any(part in skip_dirs for part in path.parts):
                continue
            if path.name in PRIVATE_FILES:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            problems += scan_secrets(text, str(path.relative_to(root)))
    return problems


# --------------------------------------------------------------------------
# Output validation
# --------------------------------------------------------------------------

HREF_RE = re.compile(r'(?:href|src)="([^"]+)"')
CANONICAL_RE = re.compile(r'<link rel="canonical" href="([^"]+)"')
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r'<meta name="description" content="([^"]*)"')
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
IMG_NOALT_RE = re.compile(r"<img(?![^>]*\balt=)[^>]*>")
PLACEHOLDER_RE = re.compile(r"(TODO|FIXME|XXX|Lorem ipsum|\{\{\s*[a-z_]+\s*\}\})")


def check_output(out: pathlib.Path, base_url: str) -> list[Problem]:
    problems: list[Problem] = []
    html_files = sorted(out.rglob("*.html"))
    if not html_files:
        return [Problem("error", str(out), "no HTML was generated")]

    existing = {("/" + p.relative_to(out).as_posix()) for p in out.rglob("*") if p.is_file()}
    # A directory with an index.html is addressable as "/dir/".
    for path in html_files:
        rel = "/" + path.relative_to(out).as_posix()
        if rel.endswith("/index.html"):
            existing.add(rel[: -len("index.html")])
    existing.add("/")

    seen_canonicals: dict[str, str] = {}
    seen_titles: dict[str, str] = {}

    for path in html_files:
        rel = "/" + path.relative_to(out).as_posix()
        where = rel
        text = path.read_text(encoding="utf-8")

        problems += scan_secrets(text, where)

        for name in PRIVATE_FILES:
            if name in text:
                problems.append(Problem("error", where, f"references the private file {name!r}"))

        canonical = CANONICAL_RE.search(text)
        if not canonical:
            problems.append(Problem("error", where, "missing a canonical link"))
        else:
            href = canonical.group(1)
            if not href.startswith(base_url):
                problems.append(Problem("error", where, f"canonical {href!r} is not under {base_url!r}"))
            if href in seen_canonicals:
                problems.append(Problem("error", where,
                                        f"duplicate canonical {href!r}, also used by {seen_canonicals[href]}"))
            seen_canonicals[href] = where

        title = TITLE_RE.search(text)
        if not title or not title.group(1).strip():
            problems.append(Problem("error", where, "missing a <title>"))
        else:
            value = title.group(1).strip()
            if len(value) > 70:
                problems.append(Problem("warning", where, f"<title> is {len(value)} characters (over 70)"))
            if value in seen_titles:
                problems.append(Problem("error", where,
                                        f"duplicate <title> {value!r}, also used by {seen_titles[value]}"))
            seen_titles[value] = where

        desc = DESC_RE.search(text)
        if not desc or not desc.group(1).strip():
            problems.append(Problem("error", where, "missing a meta description"))
        elif not 50 <= len(desc.group(1)) <= 200:
            problems.append(Problem("warning", where,
                                    f"meta description is {len(desc.group(1))} characters (want 50-200)"))

        h1s = H1_RE.findall(text)
        if len(h1s) != 1:
            problems.append(Problem("error", where, f"page has {len(h1s)} <h1> elements, expected exactly 1"))

        for img in IMG_NOALT_RE.findall(text):
            problems.append(Problem("error", where, f"<img> without alt text: {img[:60]}"))

        for match in PLACEHOLDER_RE.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            problems.append(Problem("error", f"{where}:{line}",
                                    f"unresolved placeholder {match.group(0)!r} in published output"))

        if 'lang="' not in text[:200]:
            problems.append(Problem("error", where, "<html> is missing a lang attribute"))

        for href in HREF_RE.findall(text):
            if href.startswith(("http://", "https://", "mailto:", "#", "data:", "bitcoin:", "monero:")):
                continue
            target = urllib.parse.urlparse(href).path
            if not target:
                continue
            if not target.startswith("/"):
                problems.append(Problem("error", where,
                                        f"relative link {href!r}; use a root-relative path so it works everywhere"))
                continue
            if target not in existing and target.rstrip("/") + "/" not in existing:
                problems.append(Problem("error", where, f"internal link {href!r} does not resolve"))

    for required in ("robots.txt", "sitemap.xml", "llms.txt", "agent-index.json", "index.html"):
        if not (out / required).exists():
            problems.append(Problem("error", str(out), f"missing generated file {required}"))

    sitemap = (out / "sitemap.xml").read_text(encoding="utf-8") if (out / "sitemap.xml").exists() else ""
    for url in re.findall(r"<loc>(.*?)</loc>", sitemap):
        rel = url[len(base_url):] or "/"
        if rel not in existing:
            problems.append(Problem("error", "sitemap.xml", f"lists {url!r}, which was not generated"))
    for canonical in seen_canonicals:
        if canonical not in sitemap and not canonical.endswith("#"):
            problems.append(Problem("warning", "sitemap.xml", f"does not list {canonical!r}"))

    return problems
