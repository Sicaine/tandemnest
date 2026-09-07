# TandemNest

**TandemNest** is an experiment in building useful, machine-readable technical resources that can monetize high-intent traffic from humans and autonomous agents.

The project is intentionally static-first and costs almost nothing to operate.

## Architecture

```text
GitHub → Cloudflare Pages → tandemnest.com
                         ↓
                    static HTML
                         ↓
              humans + search + agents
                         ↓
          referrals / tools / data / services
```

No VPS, database, server-side runtime, or paid analytics is required for the initial experiment.

## Build

Requires Python 3.10+ and no third-party packages:

```bash
make build
make serve
```

## Configure

Edit `config.yaml` with:

- the production URL (`https://tandemnest.com`)
- a public XMR receiving address for the crypto experiment
- RunPod referral URL when available
- DigitalOcean referral URL when available

Never commit credentials, private wallet material, API tokens, or passwords.

## Content philosophy

This is **not** an AI-content-volume experiment. Publish fewer pages that contain original calculations, current source links, useful comparisons, executable examples, or other information worth visiting.

The monetization must be obvious and disclosed. Referral links use `nofollow sponsored`.

## Agent-facing resources

The build generates:

- `/llms.txt` — compact model-readable site index
- `/agent-index.json` — machine-readable page index
- `/robots.txt`
- `/sitemap.xml`

These are experimental conveniences, not a claim that any particular crawler will use them.

## Deployment

See [`DEPLOY.md`](DEPLOY.md) for the first deployment.
