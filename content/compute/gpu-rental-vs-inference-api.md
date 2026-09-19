---
title: "Rent a GPU or call an API?"
slug: "compute/gpu-rental-vs-inference-api"
type: "article"
topic: "Compute"
order: 11
description: "A break-even calculator with the formulas shown, built on dated GPU and API prices, and an honest account of the one number that decides the answer."
published: "2026-09-19"
updated: "2026-09-19"
verified: "2026-09-19"
datasets:
  - "gpu-rental-hourly"
  - "inference-api-pricing"
  - "self-host-throughput"
summary: |
  **For almost everyone, the hosted API is cheaper, and the reason is not the GPU price.**
  A rented GPU only beats per-token pricing if you keep it genuinely busy. The deciding
  input is throughput under batching, and published measurements for it span two orders
  of magnitude, which is why most comparisons reach whatever conclusion their author
  wanted. There is also no single "break-even volume": under per-second billing the two
  costs are both linear, so one option wins at every volume. A break-even volume only
  exists if you keep an endpoint running 24/7.
sources:
  - title: "RunPod pricing"
    publisher: "RunPod"
    url: "https://www.runpod.io/pricing"
    accessed: "2026-09-19"
  - title: "RunPod pod pricing and storage billing"
    publisher: "RunPod"
    url: "https://docs.runpod.io/pods/pricing"
    accessed: "2026-09-19"
  - title: "Vast.ai pricing"
    publisher: "Vast.ai"
    url: "https://vast.ai/pricing"
    accessed: "2026-09-19"
  - title: "Lambda GPU cloud pricing"
    publisher: "Lambda"
    url: "https://lambda.ai/service/gpu-cloud/pricing"
    accessed: "2026-09-19"
  - title: "DigitalOcean GPU Droplet pricing"
    publisher: "DigitalOcean"
    url: "https://www.digitalocean.com/pricing/gpu-droplets"
    accessed: "2026-09-19"
  - title: "Modal pricing"
    publisher: "Modal"
    url: "https://modal.com/pricing"
    accessed: "2026-09-19"
  - title: "Anthropic pricing"
    publisher: "Anthropic"
    url: "https://claude.com/pricing"
    accessed: "2026-09-19"
  - title: "OpenAI API pricing"
    publisher: "OpenAI"
    url: "https://developers.openai.com/api/docs/pricing"
    accessed: "2026-09-19"
  - title: "Gemini API pricing"
    publisher: "Google"
    url: "https://ai.google.dev/gemini-api/docs/pricing"
    accessed: "2026-09-19"
  - title: "DeepSeek API pricing"
    publisher: "DeepSeek"
    url: "https://api-docs.deepseek.com/quick_start/pricing"
    accessed: "2026-09-19"
actions:
  - id: "rent_gpu_vastai"
    label: "Rent a GPU on Vast.ai"
    description: "Marketplace pricing, usually the cheapest per hour, with the variability that implies. Worth checking if the calculator above says renting wins for your workload."
    referral: "vastai"
    cost: "variable, roughly 0.14 to 3.50 USD per GPU-hour observed 2026-09-19"
    requires_user_authorization: true
    link_text: "Open Vast.ai"
  - id: "rent_gpu_runpod"
    label: "Rent a GPU on RunPod"
    description: "Fixed published pricing with a cheaper Community Cloud tier. Remember that stopped pods still bill for storage even while they are not running."
    referral: "runpod"
    cost: "0.34 to 6.79 USD per GPU-hour observed 2026-09-19"
    requires_user_authorization: true
    link_text: "Open RunPod"
---

# Rent a GPU or call an API?

{{summary}}

{{toc}}

## Why most answers to this are wrong

Search this question and you will find two kinds of page. The first is published by a
company that sells GPU time. The second is published by a company that sells inference
by the token. Both contain a calculator, and the calculators disagree, because the
assumption that decides the result is buried in each one.

Published break-even claims currently range from about 2 million tokens per day to over
a billion tokens per month. That is not disagreement about arithmetic. It is
disagreement about throughput, utilisation and billing model, none of which those
calculators let you see.

This page shows all three.

## The arithmetic

Renting a GPU gives you a machine for an hour. An API gives you tokens. To compare them
you have to convert one into the other, and that conversion is where the honesty gets
lost.

**Cost per million tokens, self-hosted:**

```text
effective_tps = tokens_per_sec_per_gpu × gpu_count × utilisation

cost_per_1M   = (hourly_price × gpu_count ÷ 3600)
                × (1,000,000 ÷ effective_tps)
```

**Cost per million tokens, hosted API:**

```text
cost_per_1M   = output_share × price_per_1M_output
                + (1 − output_share) × price_per_1M_input
```

Three things fall out of this that the vendor calculators tend not to mention.

**Utilisation is a direct multiplier on your cost.** A GPU at 40% useful utilisation
costs 2.5 times as much per token as the same GPU at 100%. Real traffic is bursty, and
you pay for the idle time. This single factor moves the answer more than the difference
between the cheapest and most expensive provider in the table below.

**There is usually no break-even volume at all.** If you rent per second and shut the
GPU down when idle, both sides of the comparison are linear in volume: cost per token is
constant. One option is cheaper at every volume, and "break-even volume" is the wrong
question. A genuine break-even volume only exists when you keep an endpoint up 24/7, in
which case the fixed monthly cost is `hourly_price × 730` and break-even is that divided
by the blended API rate.

**Idle GPUs are not free even when stopped.** RunPod bills volume storage at $0.10 per
GB per month while a pod runs and **$0.20 per GB per month while it is stopped** —
stopping a pod doubles the storage rate. A model checkpoint of a few hundred gigabytes
therefore carries a standing monthly cost that a hosted API, which bills nothing when
idle, does not have.

{{tool:gpu-vs-api}}

## Try it against a real case

Take a workload of 500 million tokens a month, a quarter of them output, and compare an
H100 on RunPod Community Cloud at $2.69/hour against DeepSeek's off-peak API at
$0.15/$0.60 per million.

At **1,500 output tokens/sec and 40% utilisation**, self-hosting works out near $1.24
per million tokens against roughly $0.26 blended for the API. The API wins by a wide
margin.

At **5,000 tokens/sec and 90% utilisation** — a small model, well batched, kept busy —
self-hosting falls to around $0.17 per million and starts to win.

Same hardware, same prices, opposite conclusion. The throughput and utilisation
assumptions decided it, not the GPU rate. That is the actual finding on this page, and
it is why the calculator above makes those two fields inputs rather than constants.

## What GPUs currently cost

{{dataset:gpu-rental-hourly}}

Reading the table:

- **Marketplace prices are not list prices.** Vast.ai figures are medians of live listings on the observation date with wide spreads — the RTX 4090 listings ranged from $0.14 to $2.70 per hour. Treat them as an indication, not a quote.
- **The managed premium is real.** Replicate's H100 at $5.49/hour against RunPod Community Cloud at $2.69 is not the same product: one is a fully managed endpoint, the other is a machine you have to operate.
- **Hyperscaler list pricing is the ceiling.** AWS's p5.48xlarge works out to $6.88 per H100-hour at list, roughly 2.5 times RunPod's Community Cloud rate.
- **Hetzner is not in the table** because it has no hourly GPU cloud product. Its GPU machines are monthly dedicated servers, which is a different purchase and does not belong in an hourly comparison.

## What hosted inference currently costs

{{dataset:inference-api-pricing}}

The spread between the cheapest and most expensive option here is over two orders of
magnitude, which matters more than any hosting decision. Before optimising infrastructure,
check whether a cheaper model does your job: moving from a flagship model to a small one
saves more than self-hosting ever will.

Note also that these are standard rates. Prompt caching, batch discounts and off-peak
pricing routinely cut the effective price by half or more and are not modelled here.

## The number that actually decides it

{{dataset:self-host-throughput}}

This is the weakest data on the page and the most important, so it gets stated plainly:
**no source gives a clean, stated-batch-size throughput figure for a 70B-class model on
a single H100 at full precision** — the exact number a clean comparison needs.

The rows above span from 33 to 5,000 output tokens per second. That spread is not
measurement noise. The two DeepSeek rows are the most instructive precisely because they
are the same model, the same hardware and the same serving stack, differing only in
concurrency: **33 tokens/sec at a single stream, 620 tokens/sec at around 100 concurrent
requests.** Nearly a 19x difference from batching alone.

The implication is uncomfortable for self-hosting: the throughput that makes renting
competitive requires steady concurrent load. A workload with bursty or low traffic never
reaches it, and pays for a GPU that spends most of its life idle. A widely-repeated
"16,200 tokens/sec on an H100" figure was deliberately excluded here because it traces
only to content-farm pages with no disclosed methodology.

## When renting a GPU genuinely wins

Not never — but the cases are specific:

- **Sustained high volume with steady concurrency.** Enough traffic to keep batches full around the clock.
- **A model no API hosts**, or a fine-tune of your own.
- **Data that cannot leave your control**, where the comparison is not really about price.
- **Batch workloads with no latency requirement**, where you can run at 100% utilisation until the queue drains.
- **Training or fine-tuning**, which is not this comparison at all — there is no per-token API equivalent.

If your situation is none of these, the calculator will almost certainly tell you to use
an API, and it will be right.

If it is one of these, the marketplace prices in the table above were the lowest observed,
with the caveat that a marketplace quote is not a list price:

{{referral:vastai|Check current Vast.ai marketplace prices}}

## What this page does not cover

Being explicit about the gaps, because they would change the numbers:

- **Engineering time is excluded.** Running a serving stack, handling failures and managing deployments is real recurring cost, and it is not in any figure here.
- **Cold starts and model load time are excluded.** Loading a large checkpoint takes minutes of paid GPU time.
- **Spot and preemptible pricing is excluded.** It is cheaper and can be interrupted; modelling it needs an interruption rate this site has not measured.
- **Egress, networking and inter-GPU bandwidth are excluded.**
- **No provider was benchmarked here.** Every throughput figure is cited from someone else's published measurement, and the page says which.

A first-hand measured comparison across providers is the obvious next step and is listed
in the [experiment log](/about/experiments/) as a planned, not completed, experiment.

{{actions}}

{{sources}}
