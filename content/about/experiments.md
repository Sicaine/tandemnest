---
title: "Experiment log"
slug: "about/experiments"
type: "article"
topic: "About"
order: 94
description: "What TandemNest has tried, what it decided not to try, and why. Including the ideas that were killed before any code was written."
published: "2026-09-19"
updated: "2026-09-19"
---

# Experiment log

A public record of what has been tried here, what it cost, and what happened. Failures
and abandoned ideas are included, because a log that only records successes is
marketing.

Each entry states a hypothesis, what it cost, the result, and a decision: **continue**,
**pause**, **kill**, or **planned**.

{{toc}}

## Killed before building: Monero mining economics

**Hypothesis.** A Monero mining profitability page would attract search traffic and fit
a site with a crypto section.

**Cost.** About an hour of research. No code written.

**Result: killed.** Three independent reasons, any one of which was sufficient:

1. **The premise is technically wrong.** Monero's RandomX proof of work is deliberately CPU-friendly and hostile to GPUs and ASICs. "Mine Monero on a rented cloud GPU" — the framing that connects mining to this site's actual subject — does not make sense.
2. **The competition is entrenched and genuinely better.** WhatToMine, CoinWarz and others drive their calculators from live network difficulty. A static page cannot match that and would be worse the day it was published.
3. **It is a profitability claim about a volatile asset.** That is a category of content this site does not want to publish, regardless of traffic.

**What was learned.** Checking whether a page's *premise* is coherent belongs before
keyword research, not after. This idea survived two rounds of planning purely because
"crypto section needs crypto content" sounded reasonable.

## Killed before building: browser-based mining

**Hypothesis.** A consent-based, clearly-disclosed in-browser miner could monetise
visitor CPU time without advertising.

**Cost.** Research only.

**Result: killed.** Coinhive shut down in 2019, and the infrastructure built to kill it
is still fully in place: browser blocklists, ad-blocker filters, antivirus signatures
and Safe Browsing flags. None of it distinguishes a consented miner from a malicious
one, so the realistic outcome is being flagged as malware. Most hosting terms, including
the platforms this site could run on, prohibit it outright. Monero's RandomX is also far
less suited to WebAssembly than the Coinhive-era algorithm was.

**What was learned.** "Technically possible" and "will not get the site blocklisted" are
different tests. This one fails the second.

## Killed before building: a "cheapest GPU" aggregator page

**Hypothesis.** A page targeting "cheapest cloud GPU" would capture high-intent traffic
with obvious monetisation.

**Cost.** Research only.

**Result: killed.** Several well-funded aggregators already run continuous scraping
across dozens of providers with thousands of live prices. Competing means maintaining a
scraper forever just to draw level, and a zero-authority site will not outrank them on
the generic query regardless.

**What was learned.** The gap was never the prices — it is the reasoning that turns
prices into a decision. That reframing produced the
[break-even page](/compute/gpu-rental-vs-inference-api/), which is defensible in a way a
price list would not be.

## Continue: dated, sourced datasets as the core asset

**Hypothesis.** Publishing prices with an observation date, a per-row source and a
machine-readable download is more defensible than prose, and more likely to be cited by
both people and AI systems, than an undated comparison.

**Cost.** Build tooling, since the datasets are generated into the pages, and recurring
effort to re-verify.

**Status: continue.** Too early for results. The reasoning: vendor calculators and
undated blog posts dominate this subject, and the one thing neither does is let you
check the number. The [data section](/data/) is the bet.

**How it will be judged.** Whether anyone cites or downloads the datasets, and whether
re-verification stays cheap enough to actually happen. If the data goes stale and nobody
notices, the hypothesis was wrong.

## Continue: build-time verification instead of manual care

**Hypothesis.** Correctness rules enforced by the build catch the mistakes that
carefulness does not.

**Cost.** Part of the build tooling.

**Status: continue.** Already working. The build refuses to publish if a Bitcoin or
Monero address fails its checksum, if anything credential-shaped appears in the source
or output, if an internal link does not resolve, if two pages share a canonical URL or
title, if a page has no `h1`, if an image lacks alt text, or if a placeholder was left
unexpanded.

**What was learned during implementation.** Verification earns its keep immediately. The
QR encoder written for the crypto pages was cross-checked against two independent
implementations, and the comparison found two real bugs — a transposed format-information
block and a Reed-Solomon generator polynomial in the wrong coefficient order. Both
produced QR codes that looked plausible and would not have scanned. Neither would have
been caught by reading the code.

## Planned: measured cost of an autonomous coding task

**Hypothesis.** Published figures for "what does an agent coding task cost" are all
estimates, and they disagree by roughly 10x. Real logged runs would be genuinely new.

**Cost.** Model usage for the runs, plus a harness.

**Status: planned, not started.** Deliberately not written up as a page yet, because the
page needs measurements and the measurements do not exist. Publishing a cost estimate
dressed as research would be exactly the thing this site was built to avoid.

**Method, when it runs.** A fixed set of defined tasks, each run several times, logging
token counts by type, model version, wall-clock time, and whether the result actually
passed. Raw data published as CSV alongside the harness.

## Planned: first-hand GPU provider benchmark

**Hypothesis.** Nobody appears to rent the same workload on RunPod and Vast.ai and
publish measured spin-up time, achieved throughput, interruption rate and real cost per
completed job. Everyone republishes price tables.

**Cost.** Real money — GPU hours on at least two providers.

**Status: planned, not started.** This is the most defensible page available to this
site and the only one that requires spending. It is deliberately queued behind the
free work.

**Why it matters more than another price table.** The
[throughput dataset](/data/self-host-throughput/) shows that the number deciding the
whole comparison is the one nobody publishes properly. Measuring it first-hand, once,
with a published harness, is worth more than any amount of re-aggregated pricing.

## Not doing: an llms.txt optimisation strategy

**Hypothesis.** An `llms.txt` file improves visibility in AI answer systems.

**Result: rejected on the evidence.** Google states plainly that Search ignores
`llms.txt` and that having one neither helps nor harms visibility. Neither OpenAI nor
Anthropic has published any statement that they consume other sites' `llms.txt` files.
The absence of evidence runs in both directions, which is itself the finding.

This site [generates one](/llms.txt) because it costs nothing, keeps it short and
accurate, and spends no further effort on it. The reasoning is on the
[crawler policy page](/about/crawler-policy/).

## Not doing: payment infrastructure before demand

**Hypothesis.** Accepting agent-native payments — x402 or similar — would open a
revenue channel.

**Result: deferred deliberately.** The [research](/crypto/agent-payments/) is published
because it was genuinely hard to assemble and is useful on its own. The infrastructure
is not built, for one reason: there is nothing here anyone has asked to buy. Every one
of these protocols also requires a server, so building it would add an operational
liability to a site that currently has none.

**What would change it.** Somebody asking to pay for something. Not a moment sooner.
