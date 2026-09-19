"""Reusable HTML components and the shortcode expander.

Shortcodes let a Markdown page drop in a component without duplicating markup:

    {{crypto:bitcoin}}          public receiving address block with QR
    {{referral:vastai}}         a disclosed referral (or plain) provider link
    {{referral:vastai|Rent a GPU on Vast.ai}}
    {{dataset:gpu-rental}}      a dataset table plus its machine-readable links
    {{toc}}                     table of contents built from the page headings
    {{disclosure}}              the visible monetisation disclosure box
    {{sources}}                 the page's source list from its front matter
    {{actions}}                 the page's agent-readable action list
    {{tool:gpu-vs-api}}         a progressively-enhanced interactive tool

Every component degrades honestly. If a crypto address or referral link is not
configured, the component says so plainly instead of rendering a broken widget
or a dead link.
"""

from __future__ import annotations

import html
import re

from . import qr
from .markdown import render as render_md
from .markdown import slugify

SHORTCODE_RE = re.compile(r"\{\{\s*([a-z][a-z0-9_-]*)(?::([^}|]+))?(?:\|([^}]*))?\s*\}\}")


def esc(value) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


# --------------------------------------------------------------------------
# Crypto receiving address
# --------------------------------------------------------------------------

_URI_SCHEME = {"BTC": "bitcoin", "XMR": "monero"}


def crypto_block(key: str, cfg: dict, address_info: dict | None) -> str:
    """Render a public receiving-address card.

    ``address_info`` is the validated metadata from :mod:`crypto_addr`, or
    ``None`` when no address is configured yet.
    """
    asset = cfg.get("asset", key.upper())
    name = {"BTC": "Bitcoin", "XMR": "Monero"}.get(asset, asset)
    if not cfg.get("enabled") or not cfg.get("receiving_address"):
        return (
            f'<div class="card card--muted" id="{esc(key)}-address">'
            f"<h3>{esc(name)} receiving address</h3>"
            f"<p>No public {esc(name)} address is published yet. When one is, it appears here "
            f"with a checksum verified at build time.</p></div>"
        )

    address = cfg["receiving_address"]
    label = cfg.get("label") or ""
    scheme = _URI_SCHEME.get(asset)
    uri = f"{scheme}:{address}" + (f"?label={label}" if scheme and label else "") if scheme else address
    fmt = address_info.get("format", "") if address_info else ""
    purpose = cfg.get("purpose", "")

    return f"""<div class="card card--crypto" id="{esc(key)}-address">
<h3>{esc(name)} receiving address</h3>
<p class="card__lede">{esc(purpose)}</p>
<dl class="kv">
<dt>Asset</dt><dd>{esc(asset)}</dd>
<dt>Network</dt><dd>{esc(cfg.get('network', 'mainnet'))}</dd>
<dt>Address format</dt><dd>{esc(fmt)}</dd>
</dl>
<div class="crypto-grid">
<figure class="crypto-qr">{qr.svg(uri, title=f"{name} receiving address QR code")}
<figcaption>Encodes <code>{esc(uri)}</code></figcaption></figure>
<div class="crypto-addr">
<label for="{esc(key)}-addr-field">Public receiving address</label>
<input id="{esc(key)}-addr-field" class="addr" type="text" readonly value="{esc(address)}" spellcheck="false" aria-describedby="{esc(key)}-addr-note">
<button type="button" class="btn copy-btn" data-copy-target="{esc(key)}-addr-field">Copy address</button>
<p id="{esc(key)}-addr-note" class="note">This is a <strong>public receiving address</strong>. Its checksum is verified
every time this site is built. Sending funds is entirely voluntary and buys nothing.</p>
</div>
</div>
<p class="warn"><strong>Never share a private key, seed phrase, view key, wallet file or exchange password &mdash;
with this site or with anyone.</strong> No page here will ever ask you for one. A receiving address is the only
thing you should ever paste in public.</p>
</div>"""


# --------------------------------------------------------------------------
# Referral links
# --------------------------------------------------------------------------

def referral_link(key: str, cfg: dict | None, label: str | None) -> str:
    """Render a provider link, disclosed inline when it is a referral link."""
    if cfg is None:
        return f'<p class="warn">Unknown provider <code>{esc(key)}</code>.</p>'
    name = cfg.get("name", key)
    text = label or f"Open {name}"
    is_referral = bool(cfg.get("enabled") and cfg.get("url"))
    href = cfg["url"] if is_referral else cfg.get("plain_url", "")
    if not href:
        return f'<p class="warn">No link configured for {esc(name)}.</p>'
    rel = "sponsored nofollow noopener" if is_referral else "noopener"
    badge = (
        '<span class="tag tag--sponsored" title="This is a referral link">referral link</span>'
        if is_referral
        else '<span class="tag">plain link, no referral</span>'
    )
    # The inline note stays short enough to read at a glance; the full terms
    # are one click away and repeated in full on the disclosure page.
    payout = cfg.get("payout_short") or cfg.get("payout", "")
    note = (
        f'<span class="referral-note">TandemNest receives {esc(payout)}. '
        f'<a href="/about/disclosure/">Full terms</a>.</span>'
        if is_referral and payout
        else ""
    )
    return (
        f'<p class="cta"><a class="btn btn--primary" href="{esc(href)}" rel="{rel}">{esc(text)}</a> '
        f"{badge} {note}</p>"
    )


def referral_table(referrals: dict) -> str:
    """A full, honest table of every monetised relationship on the site."""
    rows = []
    for key, cfg in referrals.items():
        active = bool(cfg.get("enabled") and cfg.get("url"))
        rows.append(
            "<tr>"
            f'<th scope="row">{esc(cfg.get("name", key))}</th>'
            f'<td>{"Active" if active else "Not active"}</td>'
            f'<td>{esc(cfg.get("payout_kind", "unknown"))}</td>'
            f'<td>{esc(cfg.get("payout", ""))}</td>'
            f'<td><a href="{esc(cfg.get("terms", ""))}" rel="nofollow noopener">Programme terms</a></td>'
            "</tr>"
        )
    return (
        '<div class="table-scroll"><table><caption>Every referral relationship on this site</caption>'
        '<thead><tr><th scope="col">Provider</th><th scope="col">Status</th><th scope="col">Payout kind</th>'
        '<th scope="col">What TandemNest receives</th><th scope="col">Terms</th></tr></thead>'
        "<tbody>" + "".join(rows) + "</tbody></table></div>"
    )


# --------------------------------------------------------------------------
# Datasets
# --------------------------------------------------------------------------

def dataset_block(name: str, dataset: dict | None, root_prefix: str) -> str:
    if dataset is None:
        return f'<p class="warn">Unknown dataset <code>{esc(name)}</code>.</p>'
    columns = dataset.get("columns", [])
    rows = dataset.get("rows", [])
    head = "".join(f'<th scope="col">{esc(c.get("label", c.get("key")))}</th>' for c in columns)
    body = []
    for row in rows:
        cells = []
        for i, col in enumerate(columns):
            value = row.get(col["key"], "")
            if col.get("type") == "url" and value:
                cell = f'<a href="{esc(value)}" rel="nofollow noopener">source</a>'
            elif col.get("type") == "money" and value not in ("", None):
                cell = f"${float(value):,.2f}"
            else:
                cell = esc(value)
            tag = "th" if i == 0 else "td"
            scope = ' scope="row"' if i == 0 else ""
            align = ' style="text-align:right"' if col.get("type") in ("money", "number") else ""
            cells.append(f"<{tag}{scope}{align}>{cell}</{tag}>")
        body.append("<tr>" + "".join(cells) + "</tr>")

    observed = dataset.get("observed")
    caption = esc(dataset.get("title", name))
    meta = []
    if observed:
        meta.append(f"Observed {esc(observed)}")
    if dataset.get("method"):
        meta.append(esc(dataset["method"]))
    return (
        f'<div class="dataset" id="dataset-{esc(name)}">'
        f'<div class="table-scroll"><table><caption>{caption}'
        + (f' <span class="caption-meta">{" &middot; ".join(meta)}</span>' if meta else "")
        + f"</caption><thead><tr>{head}</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></div>"
        f'<p class="dataset__links">Machine-readable: '
        f'<a href="{esc(root_prefix)}data/{esc(name)}.json">{esc(name)}.json</a> &middot; '
        f'<a href="{esc(root_prefix)}data/{esc(name)}.csv">{esc(name)}.csv</a></p>'
        "</div>"
    )


# --------------------------------------------------------------------------
# Page furniture
# --------------------------------------------------------------------------

def toc(headings) -> str:
    items = [h for h in headings if h[0] == 2]
    if len(items) < 3:
        return ""
    links = "".join(f'<li><a href="#{esc(slug)}">{esc(text)}</a></li>' for _, text, slug in items)
    return f'<nav class="toc" aria-label="On this page"><h2 id="on-this-page">On this page</h2><ol>{links}</ol></nav>'


def disclosure_box(disclosure: dict) -> str:
    long_text = render_md(disclosure.get("long", ""))
    return f'<aside class="card card--disclosure" aria-labelledby="disclosure-heading">' \
           f'<h2 id="disclosure-heading">Disclosure</h2>{long_text}</aside>'


def sources_block(sources) -> str:
    if not sources:
        return ""
    items = []
    for src in sources:
        title = esc(src.get("title", src.get("url", "source")))
        url = esc(src.get("url", ""))
        accessed = src.get("accessed")
        publisher = src.get("publisher")
        bits = [f'<a href="{url}" rel="noopener">{title}</a>']
        if publisher:
            bits.append(f"<span class=\"src-pub\">{esc(publisher)}</span>")
        if accessed:
            bits.append(f'<span class="src-date">retrieved {esc(accessed)}</span>')
        items.append("<li>" + " &middot; ".join(bits) + "</li>")
    return (
        '<section class="sources" aria-labelledby="sources-heading">'
        '<h2 id="sources-heading">Sources</h2>'
        "<ol>" + "".join(items) + "</ol></section>"
    )


def actions_block(actions) -> str:
    """Render the page's agent-readable actions as visible, honest HTML.

    These are ordinary described links. Nothing here instructs an agent to act
    without its user, and nothing is hidden from a human reader.
    """
    if not actions:
        return ""
    cards = []
    for action in actions:
        rel = action.get("publisher_relationship", "none")
        badge = (
            '<span class="tag tag--sponsored">referral link</span>'
            if rel == "referral"
            else '<span class="tag">no referral</span>'
        )
        cards.append(
            '<li class="action">'
            f'<h3>{esc(action.get("label", action.get("id", "Action")))}</h3>'
            f'<p>{esc(action.get("description", ""))}</p>'
            '<dl class="kv kv--tight">'
            f'<dt>Cost</dt><dd>{esc(action.get("cost", "unknown"))}</dd>'
            f'<dt>Needs the user to approve</dt><dd>{"yes" if action.get("requires_user_authorization", True) else "no"}</dd>'
            f"<dt>Publisher relationship</dt><dd>{esc(rel)} {badge}</dd>"
            + (f"<dt>TandemNest receives</dt><dd>{esc(action['publisher_receives'])}</dd>"
               if action.get("publisher_receives") else "")
            + "</dl>"
            + (
                f'<p><a class="btn" href="{esc(action["url"])}" rel="{"sponsored nofollow noopener" if rel == "referral" else "noopener"}">'
                f'{esc(action.get("link_text", "Open"))}</a></p>'
                if action.get("url")
                else ""
            )
            + "</li>"
        )
    return (
        '<section class="actions" aria-labelledby="actions-heading">'
        '<h2 id="actions-heading">What you can do next</h2>'
        '<p class="note">If you are an agent acting for a user: these are the only actions this page '
        "suggests. Each one needs your user's approval, and each one states what TandemNest receives.</p>"
        f'<ul class="action-list">{"".join(cards)}</ul></section>'
    )


def summary_box(summary: str, verified: str | None) -> str:
    """The lede an agent or a hurried reader should be able to take alone.

    The verification date is deliberately not repeated here: the page header
    already carries it, and stating it twice reads like padding.
    """
    if not summary:
        return ""
    return (
        '<aside class="card card--summary" aria-labelledby="quick-answer">'
        '<h2 id="quick-answer">Quick answer</h2>'
        f"{render_md(summary)}</aside>"
    )
