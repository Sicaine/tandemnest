---
title: "Compute"
slug: "compute"
type: "index"
topic: "Compute"
order: 10
nav: true
description: "What GPU time actually costs, when renting beats a hosted inference API, and the assumptions that decide the answer."
published: "2026-09-19"
updated: "2026-09-19"
---

# Compute

Cost research on renting machines to run AI workloads. Every price here carries the date
it was observed and a link to the provider's own pricing page.

<ul class="grid">
<li><a class="tile" href="/compute/gpu-rental-vs-inference-api/"><strong>Rent a GPU or call an API?</strong><span>Break-even calculator with the formulas shown, dated prices from both sides, and the throughput problem that decides the result.</span></a></li>
<li><a class="tile" href="/data/"><strong>The raw price data</strong><span>GPU hourly rates and API per-token prices as JSON and CSV, with a source URL per row.</span></a></li>
</ul>

## The short version

For most workloads a hosted API is cheaper, and the reason is utilisation rather than
the hourly rate. A rented GPU bills whether or not it is busy, so a machine kept 40%
busy costs 2.5 times as much per token as the same machine kept fully loaded. Batching
matters even more: the same model on the same hardware can differ by nearly 19x in
throughput between a single request stream and roughly 100 concurrent ones.

Before comparing infrastructure at all, compare models. The published API prices span
more than two orders of magnitude, which is a bigger lever than any hosting decision.

## How these pages are kept honest

- Prices come from the provider's own pricing page, never from a third-party aggregator or a previous version of this page.
- Every table shows its observation date, and every row links its source.
- Marketplace prices are published as observed ranges, not as if they were fixed rates.
- Figures that could not be verified from a primary source were left out rather than estimated.
- Throughput numbers are cited from published benchmarks with their batch size stated, and are explicitly not presented as measurements made here.

## What is not published here

No "top 10 cheapest GPU providers" list. Several well-funded aggregators already run
continuous price-scraping pipelines across dozens of providers and maintain that data
far better than a static page could. Duplicating them badly would help nobody.

What is missing from those aggregators is not the prices — it is the reasoning that
turns prices into a decision. That is the gap these pages aim at.
