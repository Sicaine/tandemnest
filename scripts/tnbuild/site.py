"""Content model and site generation."""

from __future__ import annotations

import csv
import datetime as dt
import html
import io
import json
import pathlib
import re
import shutil

from . import components, crypto_addr
from .markdown import headings as md_headings
from .markdown import render as render_md
from .yamlish import YamlishError, parse as parse_yaml

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EXTERNAL_LINK = re.compile(r'<a href="(https?://[^"]+)"(?![^>]*\brel=)')


class ContentError(ValueError):
    pass


# --------------------------------------------------------------------------
# Page model
# --------------------------------------------------------------------------

def resolve_action(action: dict, referrals: dict) -> dict:
    """Fill an action's link and relationship from the referral config.

    An action may name a provider with ``referral: vastai`` instead of hard
    coding a URL. When that programme is enabled the action points at the
    referral link and is labelled as one; when it is not, the action points at
    the provider's ordinary URL and is labelled as earning nothing. Content
    never has to be edited to switch monetisation on or off.
    """
    key = action.get("referral")
    if not key:
        return dict(action)
    cfg = referrals.get(key)
    if cfg is None:
        raise ContentError(f"action {action.get('id')!r} names unknown referral provider {key!r}")
    resolved = dict(action)
    active = bool(cfg.get("enabled") and cfg.get("url"))
    resolved["url"] = cfg["url"] if active else cfg.get("plain_url", "")
    resolved["publisher_relationship"] = "referral" if active else "none"
    resolved.setdefault("link_text", f"Open {cfg.get('name', key)}")
    if active and cfg.get("payout"):
        resolved["publisher_receives"] = cfg["payout"]
    return resolved


class Page:
    """One content page, parsed from a Markdown file with YAML front matter."""

    REQUIRED = ("title", "description", "slug")

    def __init__(self, source: pathlib.Path, meta: dict, body: str):
        self.source = source
        self.meta = meta
        self.body = body
        for field in self.REQUIRED:
            if field not in meta:
                raise ContentError(f"{source}: front matter is missing required field '{field}'")
        self.slug = str(meta["slug"]).strip("/")
        self.title = str(meta["title"])
        self.description = str(meta["description"])
        self.type = meta.get("type", "page")
        self.summary = meta.get("summary", "")
        self.topic = meta.get("topic", "")
        self.order = int(meta.get("order", 100))
        self.nav = bool(meta.get("nav", False))
        self.noindex = bool(meta.get("noindex", False))
        self.sources = meta.get("sources") or []
        self.actions = meta.get("actions") or []
        self.datasets = meta.get("datasets") or []
        self.published = self._date(meta.get("published"), "published")
        self.updated = self._date(meta.get("updated"), "updated") or self.published
        self.verified = self._date(meta.get("verified"), "verified")
        self.headings = md_headings(body)

    def _date(self, value, field):
        if value in (None, ""):
            return None
        text = str(value).strip()
        if not ISO_DATE.match(text):
            raise ContentError(f"{self.source}: '{field}' must be an ISO date (YYYY-MM-DD), got {text!r}")
        try:
            dt.date.fromisoformat(text)
        except ValueError as exc:
            raise ContentError(f"{self.source}: '{field}' is not a real date: {exc}") from exc
        return text

    @property
    def path(self) -> str:
        return "/" if self.slug == "" else f"/{self.slug}/"

    def canonical(self, base_url: str) -> str:
        return base_url + self.path

    @property
    def out_file(self) -> pathlib.Path:
        return pathlib.Path("index.html") if self.slug == "" else pathlib.Path(self.slug) / "index.html"

    @property
    def breadcrumbs(self):
        """(label, href) pairs from the site root to this page, exclusive of home."""
        crumbs = []
        parts = self.slug.split("/") if self.slug else []
        for i, part in enumerate(parts):
            crumbs.append((part.replace("-", " "), "/" + "/".join(parts[: i + 1]) + "/"))
        return crumbs


def parse_front_matter(text: str, source: pathlib.Path) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise ContentError(f"{source}: file must start with a '---' front matter block")
    end = text.find("\n---", 3)
    if end == -1:
        raise ContentError(f"{source}: front matter block is never closed")
    raw = text[text.index("\n", 3) + 1 : end]
    body = text[end + 4 :].lstrip("\n")
    try:
        meta = parse_yaml(raw, str(source))
    except YamlishError as exc:
        raise ContentError(f"invalid front matter: {exc}") from exc
    if not isinstance(meta, dict):
        raise ContentError(f"{source}: front matter must be a mapping")
    return meta, body


def load_pages(content_dir: pathlib.Path) -> list[Page]:
    pages = []
    for path in sorted(content_dir.rglob("*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"), path)
        pages.append(Page(path, meta, body))
    return pages


def load_datasets(data_dir: pathlib.Path) -> dict:
    datasets = {}
    if not data_dir.exists():
        return datasets
    for path in sorted(data_dir.glob("*.yaml")):
        data = parse_yaml(path.read_text(encoding="utf-8"), str(path))
        name = data.get("name") or path.stem
        data["name"] = name
        datasets[name] = data
    return datasets


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

class Renderer:
    def __init__(self, cfg: dict, datasets: dict, pages: list[Page], address_info: dict):
        self.cfg = cfg
        self.datasets = datasets
        self.pages = pages
        self.address_info = address_info
        self.base_url = cfg["site"]["url"].rstrip("/")

    def expand_shortcodes(self, text: str, page: Page) -> tuple[str, list[str]]:
        """Replace shortcodes with opaque tokens and return the HTML separately.

        Component HTML is deliberately NOT handed to the Markdown renderer.
        A ``<fieldset>`` or ``<output>`` element inside a tool would otherwise
        be treated as a paragraph and escaped into visible tag text. The
        tokens are substituted back after Markdown has run.
        """
        blocks: list[str] = []

        def replace(match: re.Match) -> str:
            name = match.group(1)
            arg = (match.group(2) or "").strip()
            label = (match.group(3) or "").strip() or None

            if name == "crypto":
                cfg = self.cfg.get("crypto", {}).get(arg)
                if cfg is None:
                    raise ContentError(f"{page.source}: unknown crypto asset '{arg}'")
                html_out = components.crypto_block(arg, cfg, self.address_info.get(arg))
            elif name == "referral":
                html_out = components.referral_link(arg, self.cfg.get("referrals", {}).get(arg), label)
            elif name == "referral_table":
                html_out = components.referral_table(self.cfg.get("referrals", {}))
            elif name == "dataset":
                dataset = self.datasets.get(arg)
                if dataset is None:
                    raise ContentError(f"{page.source}: unknown dataset '{arg}'")
                html_out = components.dataset_block(arg, dataset, "/")
            elif name == "toc":
                html_out = components.toc(page.headings)
            elif name == "disclosure":
                html_out = components.disclosure_box(self.cfg.get("disclosure", {}))
            elif name == "sources":
                html_out = components.sources_block(page.sources)
            elif name == "actions":
                referrals = self.cfg.get("referrals", {})
                html_out = components.actions_block(
                    [resolve_action(a, referrals) for a in page.actions])
            elif name == "summary":
                html_out = components.summary_box(page.summary, page.verified)
            elif name == "tool":
                html_out = self.tool(arg, page)
            else:
                raise ContentError(f"{page.source}: unknown shortcode '{{{{{name}}}}}'")

            if not html_out:
                return ""
            blocks.append(html_out)
            return f"@@TNBLOCK{len(blocks) - 1}@@"

        return components.SHORTCODE_RE.sub(replace, text), blocks

    def tool(self, name: str, page: Page) -> str:
        path = pathlib.Path(__file__).resolve().parents[2] / "templates" / "tools" / f"{name}.html"
        if not path.exists():
            raise ContentError(f"{page.source}: unknown tool '{name}' (expected templates/tools/{name}.html)")
        return path.read_text(encoding="utf-8")

    def json_ld(self, page: Page) -> str:
        site = self.cfg["site"]
        base = self.base_url
        graph = []
        org_id = f"{base}/#organization"
        site_id = f"{base}/#website"

        if page.slug == "":
            organization = {
                "@type": "Organization", "@id": org_id, "name": site["name"],
                "url": base + "/", "description": site["description"],
            }
            if site.get("repository"):
                organization["sameAs"] = [site["repository"]]
            graph.append(organization)
            graph.append({
                "@type": "WebSite", "@id": site_id, "name": site["name"],
                "url": base + "/", "publisher": {"@id": org_id},
                "inLanguage": site.get("language", "en"),
            })

        node = {
            "@type": "Article" if page.type == "article" else "WebPage",
            "@id": page.canonical(base) + "#page",
            "name": page.title,
            "headline": page.title,
            "description": page.description,
            "url": page.canonical(base),
            "inLanguage": site.get("language", "en"),
            "isPartOf": {"@id": site_id},
            "publisher": {"@id": org_id},
        }
        if page.published:
            node["datePublished"] = page.published
        if page.updated:
            node["dateModified"] = page.updated
        if page.type == "article":
            node["author"] = {"@id": org_id}
        graph.append(node)

        if page.breadcrumbs:
            items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": base + "/"}]
            for i, (label, href) in enumerate(page.breadcrumbs, start=2):
                items.append({"@type": "ListItem", "position": i, "name": label.title(), "item": base + href})
            graph.append({"@type": "BreadcrumbList", "@id": page.canonical(base) + "#breadcrumbs",
                          "itemListElement": items})

        for name in page.datasets:
            dataset = self.datasets.get(name)
            if not dataset:
                continue
            node = {
                "@type": "Dataset",
                "@id": f"{base}/data/{name}.json#dataset",
                "name": dataset.get("title", name),
                "description": dataset.get("description", ""),
                "url": page.canonical(base),
                "creator": {"@id": org_id},
                "isAccessibleForFree": True,
                "distribution": [
                    {"@type": "DataDownload", "encodingFormat": "application/json",
                     "contentUrl": f"{base}/data/{name}.json"},
                    {"@type": "DataDownload", "encodingFormat": "text/csv",
                     "contentUrl": f"{base}/data/{name}.csv"},
                ],
            }
            if dataset.get("license_url"):
                node["license"] = dataset["license_url"]
            if dataset.get("observed"):
                node["temporalCoverage"] = dataset["observed"]
                node["dateModified"] = dataset["observed"]
            graph.append(node)

        if page.type == "tool":
            graph.append({
                "@type": "SoftwareApplication",
                "@id": page.canonical(base) + "#app",
                "name": page.title,
                "description": page.description,
                "url": page.canonical(base),
                "applicationCategory": "UtilitiesApplication",
                "operatingSystem": "Any modern web browser",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            })

        payload = {"@context": "https://schema.org", "@graph": graph}
        return ('<script type="application/ld+json">'
                + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
                + "</script>")

    def nav_html(self, page: Page) -> str:
        items = sorted([p for p in self.pages if p.nav], key=lambda p: (p.order, p.slug))
        links = []
        for item in items:
            current = ' aria-current="page"' if item.slug == page.slug else ""
            links.append(f'<a href="{item.path}"{current}>{html.escape(item.title)}</a>')
        return "".join(links)

    def breadcrumb_html(self, page: Page) -> str:
        if not page.breadcrumbs:
            return ""
        parts = ['<a href="/">Home</a>']
        crumbs = page.breadcrumbs
        for label, href in crumbs[:-1]:
            parts.append(f'<a href="{href}">{html.escape(label.title())}</a>')
        parts.append(f"<span aria-current=\"page\">{html.escape(page.title)}</span>")
        return ('<nav class="breadcrumbs" aria-label="Breadcrumb"><ol>'
                + "".join(f"<li>{p}</li>" for p in parts)
                + "</ol></nav>")

    def site_meta_html(self) -> str:
        """Optional trust signals for the footer: who runs the site, where the
        source lives, how to reach them. Each appears only when configured."""
        site = self.cfg["site"]
        parts = []
        if site.get("operator"):
            parts.append(f"<span>{html.escape(site['operator'])}</span>")
        if site.get("repository"):
            parts.append(f'<a href="{html.escape(site["repository"], quote=True)}" rel="noopener">Source code</a>')
        if site.get("contact"):
            parts.append(f'<a href="{html.escape(site["contact"], quote=True)}">Contact</a>')
        return f'<p class="sitemeta">{" &middot; ".join(parts)}</p>' if parts else ""

    def dates_html(self, page: Page) -> str:
        if page.type == "home":
            return ""
        bits = []
        if page.published:
            bits.append(f'<span>Published <time datetime="{page.published}">{page.published}</time></span>')
        if page.updated and page.updated != page.published:
            bits.append(f'<span>Updated <time datetime="{page.updated}">{page.updated}</time></span>')
        if page.verified:
            bits.append(f'<span class="verified">Data verified '
                        f'<time datetime="{page.verified}">{page.verified}</time></span>')
        return f'<p class="pagedates">{" · ".join(bits)}</p>' if bits else ""

    def render(self, page: Page, template: str) -> str:
        body, blocks = self.expand_shortcodes(page.body, page)
        content = render_md(body)
        content = EXTERNAL_LINK.sub(r'<a href="\1" rel="noopener"', content)
        # Put component HTML back now that Markdown and the rel pass are done,
        # so components keep the rel attributes they chose for themselves.
        for i, block in enumerate(blocks):
            token = f"@@TNBLOCK{i}@@"
            content = content.replace(f"<p>{token}</p>", block).replace(token, block)

        site = self.cfg["site"]
        seo = self.cfg.get("seo", {})
        suffix = seo.get("title_suffix", "")
        title = page.title if page.slug == "" else page.title + suffix
        robots = "noindex,follow" if page.noindex else seo.get("default_robots", "index,follow")

        values = {
            "lang": site.get("language", "en"),
            "locale": site.get("locale", "en_US"),
            "title": html.escape(title, quote=True),
            "description": html.escape(page.description, quote=True),
            "robots": robots,
            "canonical": page.canonical(self.base_url),
            "og_image": f"{self.base_url}/assets/og-default.png",
            "og_type": "article" if page.type == "article" else "website",
            "site_name": html.escape(site["name"], quote=True),
            "tagline": html.escape(site.get("tagline", ""), quote=True),
            "nav": self.nav_html(page),
            "breadcrumbs": self.breadcrumb_html(page),
            "dates": self.dates_html(page),
            "content": content,
            "schema": self.json_ld(page),
            "disclosure_short": html.escape(self.cfg.get("disclosure", {}).get("short", "")),
            "site_meta": self.site_meta_html(),
            "year": str(dt.date.today().year),
            "body_class": f"page--{page.type}",
        }
        out = template
        for key, value in values.items():
            out = out.replace("{{ " + key + " }}", value)
        leftover = re.findall(r"\{\{ [a-z_]+ \}\}", out)
        if leftover:
            raise ContentError(f"{page.source}: template placeholders left unfilled: {sorted(set(leftover))}")
        return out


# --------------------------------------------------------------------------
# Generated machine-readable files
# --------------------------------------------------------------------------

def write_robots(out: pathlib.Path, cfg: dict) -> None:
    base = cfg["site"]["url"].rstrip("/")
    crawlers = cfg.get("crawlers", {})
    disallow = crawlers.get("disallow_paths") or []
    lines = [
        "# TandemNest robots.txt",
        "# Policy: this site exists to be read, indexed and cited. Everything",
        "# public is crawlable, with no JavaScript, login or CAPTCHA required.",
        "# Named crawlers below are listed so the intent stays explicit.",
        "",
        "User-agent: *",
        "Allow: /",
    ]
    lines += [f"Disallow: {path}" for path in disallow]
    for entry in crawlers.get("named", []):
        lines += ["", f"# {entry['vendor']}: {entry['purpose']}", f"# docs: {entry['docs']}",
                  f"User-agent: {entry['token']}", "Allow: /"]
        lines += [f"Disallow: {path}" for path in disallow]
    lines += ["", f"Sitemap: {base}/sitemap.xml", ""]
    (out / "robots.txt").write_text("\n".join(lines), encoding="utf-8")


def write_sitemap(out: pathlib.Path, cfg: dict, pages: list[Page]) -> None:
    base = cfg["site"]["url"].rstrip("/")
    entries = []
    for page in sorted((p for p in pages if not p.noindex), key=lambda p: p.slug):
        lastmod = f"    <lastmod>{page.updated}</lastmod>\n" if page.updated else ""
        entries.append(f"  <url>\n    <loc>{html.escape(page.canonical(base))}</loc>\n{lastmod}  </url>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(entries) + "\n</urlset>\n")
    (out / "sitemap.xml").write_text(xml, encoding="utf-8")


def write_llms_txt(out: pathlib.Path, cfg: dict, pages: list[Page]) -> None:
    """A deliberately small llms.txt.

    Google states it ignores llms.txt, and no other major vendor documents
    consuming it. It is generated because it costs nothing, and kept short on
    purpose: the HTML is the real interface.
    """
    site = cfg["site"]
    base = site["url"].rstrip("/")
    lines = [f"# {site['name']}", "", f"> {site['description']}", "",
             "Every page states when its data was observed and links its primary sources.",
             "The HTML is the canonical version of everything below; nothing here is gated,",
             "and no page requires JavaScript to read.", ""]
    by_topic: dict[str, list[Page]] = {}
    for page in pages:
        if page.noindex or page.slug == "":
            continue
        by_topic.setdefault(page.topic or "Pages", []).append(page)
    for topic in sorted(by_topic):
        lines.append(f"## {topic}")
        lines.append("")
        for page in sorted(by_topic[topic], key=lambda p: (p.order, p.slug)):
            stamp = f" (verified {page.verified})" if page.verified else ""
            lines.append(f"- [{page.title}]({base}{page.path}): {page.description}{stamp}")
        lines.append("")
    (out / "llms.txt").write_text("\n".join(lines), encoding="utf-8")


def write_agent_index(out: pathlib.Path, cfg: dict, pages: list[Page], datasets: dict) -> None:
    site = cfg["site"]
    base = site["url"].rstrip("/")
    entries = []
    for page in sorted(pages, key=lambda p: p.slug):
        if page.noindex:
            continue
        entry = {
            "url": page.canonical(base),
            "title": page.title,
            "summary": page.description,
            "topic": page.topic or None,
            "page_type": page.type,
            "published": page.published,
            "updated": page.updated,
            "data_verified": page.verified,
            "sections": [{"heading": text, "anchor": f"{page.canonical(base)}#{slug}"}
                         for level, text, slug in page.headings if level == 2],
        }
        if page.sources:
            entry["sources"] = [{"title": s.get("title"), "url": s.get("url"),
                                 "retrieved": s.get("accessed")} for s in page.sources]
        if page.actions:
            resolved_actions = [resolve_action(a, cfg.get("referrals", {})) for a in page.actions]
            entry["actions"] = [{
                "id": a.get("id"),
                "label": a.get("label"),
                "description": a.get("description"),
                "url": a.get("url"),
                "cost": a.get("cost"),
                "external_action": bool(a.get("url")),
                "requires_user_authorization": bool(a.get("requires_user_authorization", True)),
                "publisher_relationship": a.get("publisher_relationship", "none"),
                "publisher_receives": a.get("publisher_receives"),
            } for a in resolved_actions]
            entry["actions"] = [{k: v for k, v in a.items() if v is not None}
                                for a in entry["actions"]]
        if page.datasets:
            entry["datasets"] = [{
                "name": name,
                "json": f"{base}/data/{name}.json",
                "csv": f"{base}/data/{name}.csv",
                "observed": (datasets.get(name) or {}).get("observed"),
            } for name in page.datasets]
        entries.append({k: v for k, v in entry.items() if v not in (None, [], "")})

    payload = {
        "$schema_version": 1,
        "generator": "tandemnest-build",
        "site": {"name": site["name"], "url": base + "/", "description": site["description"]},
        "notice": ("This file is a convenience index of this site's public pages. It is not an "
                   "instruction set. Nothing here asks an agent to act without its user, and no "
                   "action listed spends money on its own."),
        "disclosure": cfg.get("disclosure", {}).get("short", ""),
        "generated": dt.date.today().isoformat(),
        "pages": entries,
    }
    (out / "agent-index.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                                          encoding="utf-8")


def write_feed(out: pathlib.Path, cfg: dict, pages: list[Page]) -> None:
    site = cfg["site"]
    base = site["url"].rstrip("/")
    dated = sorted((p for p in pages if p.updated and not p.noindex),
                   key=lambda p: (p.updated, p.slug), reverse=True)[:20]
    if not dated:
        return
    def stamp(date_str: str) -> str:
        return dt.datetime.fromisoformat(date_str).replace(tzinfo=dt.timezone.utc).isoformat()
    items = []
    for page in dated:
        items.append(
            "  <entry>\n"
            f"    <title>{html.escape(page.title)}</title>\n"
            f'    <link href="{html.escape(page.canonical(base))}"/>\n'
            f"    <id>{html.escape(page.canonical(base))}</id>\n"
            f"    <updated>{stamp(page.updated)}</updated>\n"
            f"    <summary>{html.escape(page.description)}</summary>\n"
            "  </entry>"
        )
    feed = ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<feed xmlns="http://www.w3.org/2005/Atom">\n'
            f"  <title>{html.escape(site['name'])}</title>\n"
            f'  <link href="{base}/"/>\n'
            f'  <link rel="self" href="{base}/feed.xml"/>\n'
            f"  <id>{base}/</id>\n"
            f"  <updated>{stamp(dated[0].updated)}</updated>\n"
            f"  <subtitle>{html.escape(site['description'])}</subtitle>\n"
            + "\n".join(items) + "\n</feed>\n")
    (out / "feed.xml").write_text(feed, encoding="utf-8")


def write_datasets(out: pathlib.Path, cfg: dict, datasets: dict) -> None:
    if not datasets:
        return
    data_dir = out / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    base = cfg["site"]["url"].rstrip("/")
    for name, dataset in datasets.items():
        columns = dataset.get("columns", [])
        keys = [c["key"] for c in columns]
        payload = {
            "name": name,
            "title": dataset.get("title", name),
            "description": dataset.get("description", ""),
            "observed": dataset.get("observed"),
            "method": dataset.get("method"),
            "license": dataset.get("license", "CC BY 4.0"),
            "license_url": dataset.get("license_url"),
            "source": f"{base}/data/{name}.json",
            "units": {c["key"]: c.get("unit") for c in columns if c.get("unit")},
            "columns": columns,
            "rows": dataset.get("rows", []),
        }
        (data_dir / f"{name}.json").write_text(
            json.dumps({k: v for k, v in payload.items() if v not in (None, {}, "")},
                       indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=keys, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in dataset.get("rows", []):
            writer.writerow({k: row.get(k, "") for k in keys})
        (data_dir / f"{name}.csv").write_text(buf.getvalue(), encoding="utf-8")


def write_headers(out: pathlib.Path) -> None:
    """Emit a Cloudflare Pages `_headers` file.

    The content security policy can be this strict because the site loads
    nothing from anywhere else: no fonts, no analytics, no CDN, no embeds.
    `form-action 'none'` is safe because the only forms here are calculators
    that compute in the page and never submit.
    """
    csp = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'none'; "
        "form-action 'none'; "
        "frame-ancestors 'none'; "
        "base-uri 'none'; "
        "object-src 'none'"
    )
    (out / "_headers").write_text(
        "/*\n"
        f"  Content-Security-Policy: {csp}\n"
        "  X-Content-Type-Options: nosniff\n"
        "  Referrer-Policy: strict-origin-when-cross-origin\n"
        "  Permissions-Policy: geolocation=(), camera=(), microphone=(), payment=(), usb=()\n"
        "  Cross-Origin-Opener-Policy: same-origin\n"
        "\n"
        "/assets/*\n"
        "  Cache-Control: public, max-age=3600, must-revalidate\n"
        "\n"
        "/data/*\n"
        "  Cache-Control: public, max-age=3600\n"
        "  Access-Control-Allow-Origin: *\n"
        "\n"
        "/agent-index.json\n"
        "  Cache-Control: public, max-age=3600\n"
        "  Access-Control-Allow-Origin: *\n",
        encoding="utf-8",
    )


def copy_static(static_dir: pathlib.Path, out: pathlib.Path) -> None:
    target = out / "assets"
    target.mkdir(parents=True, exist_ok=True)
    for path in sorted(static_dir.rglob("*")):
        if path.is_file():
            dest = target / path.relative_to(static_dir)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)


def validate_addresses(cfg: dict) -> dict:
    """Validate every configured receiving address. Raises on a bad address."""
    info = {}
    for key, entry in (cfg.get("crypto") or {}).items():
        address = (entry or {}).get("receiving_address") or ""
        if not entry.get("enabled") or not address:
            info[key] = None
            continue
        asset = (entry.get("asset") or key).lower()
        asset = {"bitcoin": "btc", "monero": "xmr"}.get(asset, asset)
        try:
            info[key] = crypto_addr.validate(address, asset)
        except crypto_addr.AddressError as exc:
            raise ContentError(
                f"config.yaml: crypto.{key}.receiving_address failed validation: {exc}. "
                f"Refusing to publish an address that does not verify."
            ) from exc
    return info
