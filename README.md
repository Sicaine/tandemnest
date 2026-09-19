# TandemNest

Source for [tandemnest.com](https://tandemnest.com) — dated, sourced cost research on GPU
rental, LLM inference pricing and agent payment rails.

The site is static HTML built by a small Python program with **no third-party
dependencies**, so it builds identically on a laptop, in CI, and on Cloudflare Pages
with no install step.

```text
content/*.md  +  data/*.yaml  +  config.yaml
                     │
              scripts/build.py          (stdlib only)
                     │
                  public/               (deterministic output)
                     │
   GitHub Actions → GitHub Pages → tandemnest.com
```

## Quick start

```bash
make serve      # build and serve on http://localhost:8000
make validate   # unit tests + build + output validation — run before pushing
```

| Target | What it does |
| --- | --- |
| `make build` | Build into `public/` |
| `make check` | Build, then validate the generated output |
| `make test` | Unit tests for the build toolchain |
| `make validate` | `test` + `check`; the full gate |
| `make clean` | Remove `public/` |

Requires Python 3.10+. Nothing else.

## What the build refuses to publish

`make check` is a real gate, not a formality. The build fails — writing nothing — if:

- a configured **Bitcoin or Monero address fails its checksum** (Base58Check, bech32 per BIP-173, bech32m per BIP-350, or Monero's Keccak-256)
- anything **credential-shaped** appears in the source or the output (private keys, API tokens, JWTs, recovery-phrase-shaped lines)
- an **internal link does not resolve**
- two pages share a **canonical URL** or a **`<title>`**
- a page has no `h1`, more than one `h1`, no meta description, or an `img` with no `alt`
- a **shortcode or template placeholder was left unexpanded**
- the **sitemap** lists a page that was not generated
- the **private task file** reaches the output directory

CI additionally asserts the build is byte-for-byte reproducible and that
`TODO STEP BY STEP.html` is not tracked by git.

## Generated output

Alongside the pages, every build emits `robots.txt`, `sitemap.xml`, `llms.txt`,
`agent-index.json`, `feed.xml`, a JSON and CSV file per dataset, and a Cloudflare Pages
`CNAME` file (so GitHub Pages keeps the custom domain across deploys), and a `_headers`
file. The latter is a Cloudflare Pages format that GitHub Pages ignores — it is kept
only so the policy travels with the site if it ever moves hosts.

### Regenerating the social image

`static/og-default.png` is committed so the build stays dependency-free. Rebuild it from
its source after changing the wording:

```bash
chromium --headless --screenshot=static/og-default.png \
         --window-size=1200,630 design/og-default.svg
```

## Layout

```text
config.yaml              Site config. PUBLIC VALUES ONLY — it is all published.
content/**/*.md          Pages: YAML front matter + Markdown + shortcodes.
data/*.yaml              Datasets, rendered into tables and published as JSON + CSV.
templates/page.html      The page shell.
templates/tools/*.html   Interactive tools, embedded with {{tool:name}}.
static/                  CSS, JS, icons → copied to /assets/.
design/                  Design sources (the OG image SVG); not published.
scripts/build.py         Orchestrator.
scripts/tnbuild/         yamlish · markdown · qr · crypto_addr · components · site · checks
tests/                   Unit tests (stdlib unittest).
docs/                    Internal research notes, not published.
```

### The `tnbuild` modules

| Module | Why it exists |
| --- | --- |
| `yamlish.py` | Strict YAML-subset parser. Fails loudly with a line number rather than misparsing. |
| `markdown.py` | Markdown → semantic HTML, including GFM tables with captions and stable heading ids. |
| `qr.py` | Pure-Python QR encoder emitting inline SVG, so crypto pages need no third-party image service. Cross-validated against two independent implementations and decode-verified. |
| `crypto_addr.py` | Address validation including a hand-rolled Keccak-256 (Monero uses original Keccak, not NIST SHA-3, so `hashlib.sha3_256` cannot be used). |
| `components.py` | Shortcode expansion and reusable page furniture. |
| `checks.py` | Secret scanning and output validation. |

## Writing a page

```markdown
---
title: "Page title"
slug: "section/page-name"
type: "article"          # page | article | index | tool | home
topic: "Compute"
description: "50–200 characters; validated."
published: "2026-09-19"
updated: "2026-09-19"
verified: "2026-09-19"   # when the data was last checked against sources
datasets: ["gpu-rental-hourly"]
sources:
  - title: "Provider pricing"
    url: "https://example.com/pricing"
    accessed: "2026-09-19"
---

# Page title

{{summary}}   {{toc}}   {{dataset:gpu-rental-hourly}}   {{sources}}
{{actions}}   {{referral:vastai|Rent a GPU}}   {{crypto:bitcoin}}
{{tool:gpu-vs-api}}   {{disclosure}}   {{referral_table}}
```

Anything under `content/` with `slug: ""` becomes the home page; exactly one page must
have it.

## Editorial rules

These are what the site is for, and they are load-bearing:

- Every changing number carries an **observation date** and a **primary source**.
- Arithmetic is **shown**, and datasets ship as JSON and CSV so conclusions can be recomputed.
- Uncertainty is **stated** — ranges stay ranges, weak data is labelled weak.
- Referral links are disclosed **inline**, and every page must remain worth reading with all of them removed.
- No invented benchmarks, no review markup, no FAQ schema, no content generated in bulk from keyword lists.

Full versions: [`/about/methodology/`](content/about/methodology.md) and
[`/about/disclosure/`](content/about/disclosure.md).

## Configuration

`config.yaml` holds public values only — site metadata, crawler policy, public receiving
addresses, and referral URLs. Every referral entry has a `plain_url` fallback, so
disabling a programme leaves the pages correct and linking to the provider's ordinary
URL.

Never commit: private keys, seed phrases, API tokens, passwords, `.env` files.

## Deployment

`.github/workflows/pages.yml` builds and deploys to GitHub Pages on every push to
`main`. See [`DEPLOY.md`](DEPLOY.md).

`public/` is gitignored on purpose: the workflow builds it, so committing the output
would only create drift between source and what is served.
