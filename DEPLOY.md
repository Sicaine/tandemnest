# Deploying TandemNest

Target architecture:

```text
GitHub → GitHub Actions → GitHub Pages → tandemnest.com
```

`.github/workflows/pages.yml` builds and deploys on every push to `main`. No VPS,
no database, no server-side runtime, no paid service.

## 1. Check locally first

```bash
make validate
```

This runs the unit tests, builds the site, and validates the output. If it fails
locally it will fail in CI and on Cloudflare — fix it here, where the loop is fastest.

```bash
make serve   # http://localhost:8000
```

## 2. Push to GitHub

The repository can be private; Cloudflare Pages works with private repositories.

```bash
git add .
git commit -m "Rebuild TandemNest"
git push -u origin main
```

`public/` is gitignored. Do not commit build output — Cloudflare builds it.

## 3. Enable GitHub Pages

Repository **Settings → Pages → Build and deployment → Source: GitHub Actions**.

That is the only setting required. The workflow does the rest: it builds with
`python3 scripts/build.py --check`, uploads `public/`, and deploys. Nothing to install
and no secrets to configure — the build uses only the Python standard library.

**The `--check` flag is deliberate.** It turns a broken link, an unverifiable crypto
address or a secret-shaped string into a failed deploy rather than a published mistake.

## 4. The custom domain

`Settings → Pages → Custom domain` → `tandemnest.com`, and enable **Enforce HTTPS**
once the certificate is issued.

The build also writes `public/CNAME` from `site.url`, because GitHub Pages reads that
file from the published artifact on every deploy and a deploy without it can drop the
custom domain back to the `github.io` URL. The file and the canonical tags therefore
come from the same source and cannot disagree.

DNS at your registrar: an `ALIAS`/`ANAME` or four `A` records for the apex pointing at
GitHub Pages' addresses, plus a `CNAME` for `www` pointing at `sicaine.github.io`.
GitHub's Pages settings page shows the current addresses to use.

**Note on `_headers`.** The build emits one, but it is a Cloudflare Pages format and
**GitHub Pages ignores it** — GitHub Pages cannot serve custom headers at all. So the
content security policy and cache-control rules described in it are not active on this
host. It is kept because it costs nothing and applies immediately if the site ever moves
behind Cloudflare. Nothing on the site depends on those headers to function.

## 6. Verify the deployment

```bash
curl -sI https://tandemnest.com/ | head -1                    # expect HTTP/2 200
curl -s  https://tandemnest.com/robots.txt | head -5
curl -s  https://tandemnest.com/sitemap.xml | grep -c '<loc>'  # expect 19
curl -s  https://tandemnest.com/agent-index.json | head -5
curl -s  https://tandemnest.com/data/gpu-rental-hourly.csv | head -3
curl -s  https://tandemnest.com/ | grep -o '<link rel="canonical"[^>]*>'
```

Then check that the site is readable with JavaScript disabled. Everything except the
calculator's live updates and the copy buttons must still work — that is a hard
requirement, not an aspiration.

## 7. Search Console

Add a **Domain** property for `tandemnest.com` (not URL-prefix), verify via the TXT
record in Cloudflare DNS, and submit `sitemap.xml`.

The generative-AI performance report shows AI Overviews and AI Mode impressions. It
reports impressions only, with no click data, and does not separate the two surfaces.

## 8. After launch

Do not mass-publish. The site is deliberately small so that a result can be attributed
to a cause. Wait for indexing, see which pages get impressions, and record what happens
in `content/about/experiments.md` — including the negative results.

Re-verification is the recurring cost of this site's whole premise: the prices carry
observation dates, and those dates are only worth anything if someone goes back and
checks them.
