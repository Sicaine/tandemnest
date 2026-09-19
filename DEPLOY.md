# Deploying TandemNest

Target architecture, unchanged:

```text
GitHub → Cloudflare Pages → tandemnest.com
```

No VPS, no database, no server-side runtime, no paid service.

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

## 3. Create the Cloudflare Pages project

Cloudflare dashboard → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**.

| Setting | Value |
| --- | --- |
| Framework preset | None |
| Build command | `python3 scripts/build.py --check` |
| Build output directory | `public` |
| Root directory | `/` |

No environment variables are needed, and there is nothing to install: the build uses
only the Python standard library.

**Use `--check`.** It turns a broken link, an unverifiable crypto address or a
secret-shaped string into a failed deploy instead of a published mistake.

## 4. Attach the domain

In the Pages project → **Custom domains** → add `tandemnest.com`, then add
`www.tandemnest.com` and let Cloudflare redirect it to the apex. Two hostnames serving
the same content is a genuine duplicate-content problem; one must redirect.

Every page declares `https://tandemnest.com/…` as its canonical URL, so until the domain
is attached those canonicals point at a host that does not serve the site.

## 5. Leave the security settings alone

This matters more than it sounds.

**Do not enable** Bot Fight Mode, an aggressive WAF ruleset, or "I'm Under Attack" mode.
They serve JavaScript challenges that crawlers cannot pass, which would make the site
invisible to Google, to AI search crawlers, and to the user-directed fetchers that
retrieve a page when someone asks an assistant about it — the entire audience this site
was built for.

A static site with no forms, no database and no server-side code has nothing for those
features to protect. Cloudflare's defaults are already appropriate.

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
