---
title: "Crawler and AI access policy"
slug: "about/crawler-policy"
type: "article"
topic: "About"
order: 93
description: "Which crawlers TandemNest allows and why, with each user-agent token sourced from its operator's own documentation rather than an SEO blog."
published: "2026-09-19"
updated: "2026-09-19"
verified: "2026-09-19"
summary: |
  TandemNest allows every documented crawler, including AI training crawlers. Nothing
  public here is behind a login, a CAPTCHA, or a JavaScript challenge. The user-agent
  tokens in `/robots.txt` come from each operator's own documentation, which matters
  because a large share of the crawler lists circulating online contain tokens that no
  vendor has ever published.
sources:
  - title: "Google crawlers and fetchers overview"
    publisher: "Google Search Central"
    url: "https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers"
    accessed: "2026-09-19"
  - title: "AI features and your website"
    publisher: "Google Search Central"
    url: "https://developers.google.com/search/docs/appearance/ai-features"
    accessed: "2026-09-19"
  - title: "OpenAI bots"
    publisher: "OpenAI"
    url: "https://developers.openai.com/api/docs/bots"
    accessed: "2026-09-19"
  - title: "Does Anthropic crawl data from the web?"
    publisher: "Anthropic"
    url: "https://support.claude.com/en/articles/8896518"
    accessed: "2026-09-19"
  - title: "Perplexity crawlers"
    publisher: "Perplexity"
    url: "https://docs.perplexity.ai/docs/resources/perplexity-crawlers"
    accessed: "2026-09-19"
  - title: "About Applebot"
    publisher: "Apple"
    url: "https://support.apple.com/en-us/119829"
    accessed: "2026-09-19"
  - title: "CCBot"
    publisher: "Common Crawl"
    url: "https://commoncrawl.org/ccbot"
    accessed: "2026-09-19"
---

# Crawler and AI access policy

{{summary}}

{{toc}}

## The policy

Everything public on this site is crawlable by anything that asks. There is no login, no
CAPTCHA, no JavaScript challenge, no rate limiting beyond the hosting platform's
defaults, and no content that renders only after a script runs. A crawler that fetches a
URL here gets the complete page as text.

That includes crawlers used for AI model training. The research on this site is
published to be read and cited; excluding the systems most likely to surface it would
defeat the point.

## Two kinds of fetcher, which is the part people get wrong

Vendors run two categories of automated fetch, and they behave differently:

- **Indexing crawlers** discover and store pages ahead of time. These follow `robots.txt`. `Googlebot`, `GPTBot`, `OAI-SearchBot`, `ClaudeBot`, `Claude-SearchBot` and `PerplexityBot` are all in this category.
- **User-directed fetchers** retrieve one page because a person just asked about it. OpenAI documents that `robots.txt` rules **may not apply** to `ChatGPT-User`, and Perplexity documents that `Perplexity-User` generally ignores `robots.txt` entirely.

The practical consequence: blocking AI crawlers in `robots.txt` does not stop a person
from pasting your URL into an assistant and having it read the page. It only removes you
from the index that gets consulted when nobody has named your site.

## Two tokens that are not crawlers at all

`Google-Extended` and `Applebot-Extended` do not fetch anything. They are opt-out
signals expressed through `robots.txt` that control whether already-collected content may
be used for generative model training. Blocking `Google-Extended` has no effect on
Search ranking, and no effect on eligibility for AI Overviews or AI Mode, because those
features draw on the ordinary Googlebot index.

This trips people up constantly: there is currently no way to appear in Google Search
while opting out of AI Overviews, short of blocking `Googlebot` and leaving Search
altogether.

## What Google says actually matters

Google's own guidance is that there are no additional requirements to appear in AI
Overviews or AI Mode, and no special structured data for it. The qualifying criteria are
the ordinary ones: the page is crawlable, indexable, useful, and fast.

Two specific consequences for this site:

- **No `llms.txt` optimisation effort.** Google states that Search ignores `llms.txt` entirely, and that having one neither helps nor harms visibility. Neither OpenAI nor Anthropic has published a statement that they consume other sites' `llms.txt` files either way. This site [generates one](/llms.txt) because it costs nothing to generate, and keeps it short, accurate and unoptimised. Anyone selling `llms.txt` as an AI-search growth tactic is selling something Google has explicitly said it ignores.
- **No deprecated structured data.** Google retired FAQ rich results in 2026 and the sitelinks search box in 2024. This site emits `Article`, `WebPage`, `BreadcrumbList`, `Organization`, `WebSite`, `Dataset` and `SoftwareApplication` markup, each describing content actually visible on the page, and nothing else.

## The tokens in robots.txt

Each entry in [`/robots.txt`](/robots.txt) carries a comment naming the operator and
linking its documentation. Tokens were taken from those pages on 19 September 2026 and
are listed below with what each one actually does.

| Token | Operator | What it does | Honours robots.txt |
| --- | --- | --- | --- |
| `Googlebot` | Google | Search indexing, which is what feeds AI Overviews and AI Mode | Yes |
| `Google-Extended` | Google | Opt-out signal for Gemini and Vertex training; no ranking effect | Yes, as a signal |
| `GPTBot` | OpenAI | Training data collection | Yes |
| `OAI-SearchBot` | OpenAI | Indexing for ChatGPT search results | Yes |
| `ChatGPT-User` | OpenAI | Fetches a page because a user asked | Documented as may not apply |
| `ClaudeBot` | Anthropic | Training data collection | Yes |
| `Claude-User` | Anthropic | Fetches a page because a Claude user asked | Yes |
| `Claude-SearchBot` | Anthropic | Crawling to improve Claude search quality | Yes |
| `PerplexityBot` | Perplexity | Answer-engine index | Yes |
| `Perplexity-User` | Perplexity | Live fetch for a user query | Documented as generally ignored |
| `Applebot` | Apple | Siri, Spotlight and Safari search | Yes |
| `Applebot-Extended` | Apple | Opt-out signal for Apple model training | Yes, as a signal |
| `CCBot` | Common Crawl | Open web corpus used by many datasets | Yes |
| `Amazonbot` | Amazon | Indexing for Amazon assistants | Yes |

Two older Anthropic tokens, `anthropic-ai` and `Claude-Web`, appear in many published
crawler lists. Anthropic's current documentation does not mention either, so they are
not listed here as active.

## Tokens deliberately not listed

Lists of "AI bots to block" circulate widely and are frequently wrong. A token only
appears in this site's `robots.txt` if its operator publishes it. `Bytespider` is widely
cited but has no ByteDance documentation that could be located; Mistral and Cohere have
no published crawler token at all; Meta's `meta-externalagent` could not be confirmed
from a Meta-owned page. None of them are listed, because a made-up rule is worse than no
rule: it implies a policy the site cannot actually enforce.

Since the policy here is to allow everything anyway, an unlisted crawler is covered by
the `User-agent: *` block and is welcome.

{{sources}}
