# TandemNest — tomorrow's rollout

## 0. Prerequisites

- GitHub account/repository
- Cloudflare account
- `tandemnest.com` purchased
- Python 3 installed locally

No VPS is required.

## 1. Configure the public identifiers

Edit `config.yaml`:

```yaml
site:
  url: "https://tandemnest.com"

monetization:
  xmr_mining:
    enabled: true
    wallet_address: "YOUR_PUBLIC_XMR_ADDRESS"
  runpod:
    enabled: true
    referral_url: "YOUR_RUNPOD_REFERRAL_URL"
  digitalocean:
    enabled: true
    referral_url: "YOUR_DIGITALOCEAN_REFERRAL_URL"
```

Only publish public receiving addresses and referral URLs. Never put private keys, wallet seeds, API tokens or passwords in this repository.

## 2. Test locally

```bash
python3 scripts/build.py
python3 -m http.server 8000 --directory public
```

Open http://localhost:8000 and check every link.

## 3. Create the GitHub repo

Create an empty repository named `tandemnest` (public is preferable for this experiment), then:

```bash
git remote add origin git@github.com:YOUR_GITHUB_USER/tandemnest.git
git add .
git commit -m "Initial TandemNest site"
git push -u origin main
```

If you use HTTPS instead of SSH, use the equivalent GitHub remote.

## 4. Cloudflare Pages

In Cloudflare: Workers & Pages → Create application → Pages → Connect to Git.

Select the `tandemnest` repository.

Build settings:

- Framework preset: None
- Build command: `python3 scripts/build.py`
- Build output directory: `public`
- Root directory: `/`

Deploy.

## 5. Attach tandemnest.com

In the Pages project, add `tandemnest.com` and follow Cloudflare's DNS/nameserver instructions.

Do not add a VPS or origin server yet.

## 6. Verify

Check:

- `https://tandemnest.com/`
- `https://tandemnest.com/robots.txt`
- `https://tandemnest.com/sitemap.xml`
- `https://tandemnest.com/llms.txt`
- `https://tandemnest.com/agent-index.json`
- `/crypto/`
- `/compute/`
- `/ai/`

## 7. First 48 hours

Do not mass-publish. Get the first pages genuinely useful, then submit the sitemap in Google Search Console and watch:

- impressions
- indexed pages
- referral clicks
- direct agent/bot traffic
- conversions

Keep the first experiment small enough that we can tell what actually caused a result.
