---
title: "AI"
slug: "ai"
type: "index"
topic: "AI"
order: 20
nav: true
description: "Inference pricing tracked with observation dates, and cost research on running AI workloads without overspending."
published: "2026-09-19"
updated: "2026-09-19"
---

# AI

Cost research on model inference: what providers charge, how the prices move, and where
the money actually goes in an agent workload.

<ul class="grid">
<li><a class="tile" href="/compute/gpu-rental-vs-inference-api/"><strong>Rent a GPU or call an API?</strong><span>The comparison, with a calculator and the throughput caveats stated in full.</span></a></li>
<li><a class="tile" href="/data/inference-api-pricing/"><strong>Inference price dataset</strong><span>Per-token prices from every major provider, dated and sourced, as JSON and CSV.</span></a></li>
</ul>

## The single most useful cost fact

Published per-token prices currently span more than two orders of magnitude, from
roughly $0.05 to $10 per million input tokens. Choosing the right model for a task saves
far more than any infrastructure change, and costs nothing to try.

Two further levers are larger than most infrastructure decisions and easy to overlook:

- **Output tokens cost several times more than input.** Most providers charge four to five times as much. A workload's input/output ratio therefore changes its cost more than the headline input price suggests.
- **Prompt caching and off-peak pricing routinely halve the effective rate.** DeepSeek publishes a two-tier schedule by time of day; most providers discount cached input heavily. None of that is reflected in a list price comparison.

## What is coming

The obvious missing page is a measured account of what an autonomous coding task
actually costs — real runs, real token counts, real outcomes, published as data rather
than as an estimate. Every published figure found so far is a guess, and they disagree
by roughly 10x.

That page is not up yet, because it requires the measurements to exist first, and this
site does not publish a number it has not got. It is tracked in the
[experiment log](/about/experiments/) as a planned experiment with a defined method.
