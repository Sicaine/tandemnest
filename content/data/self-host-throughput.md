---
title: "Dataset: self-host throughput"
slug: "data/self-host-throughput"
type: "article"
topic: "Data"
order: 53
description: "Cited throughput benchmarks for open-weight models on rented GPUs, each with its batch size, serving stack and an assessment of how much to trust it."
published: "2026-09-19"
updated: "2026-09-19"
verified: "2026-09-19"
datasets:
  - "self-host-throughput"
summary: |
  Published output-token throughput figures for self-hosted open-weight models. This is
  the weakest and most consequential input in any GPU-versus-API comparison, so every
  row records hardware, batch size, serving stack, and how much weight the number
  deserves. These are other people's measurements, cited, not reproduced here.
---

# Dataset: self-host throughput

{{summary}}

{{dataset:self-host-throughput}}

## Why this dataset is unusual

Most datasets try to look authoritative. This one is published mainly to show how weak
the available evidence is, because that weakness is the real finding.

To compare a GPU's hourly price against an API's per-token price, you need tokens per
second. Everyone doing that comparison needs the same number, almost nobody states where
theirs came from, and the published measurements that do disclose their conditions span
roughly two orders of magnitude.

## The batching effect, isolated

The two DeepSeek-V3 rows are the most useful thing in the table. Same model, same
quantisation, same hardware, same serving stack, same author, same run — differing only
in concurrency:

- **33 output tokens/sec** at a single request stream
- **620 output tokens/sec** at roughly 100 concurrent requests

Nearly 19x, from batching alone. That single comparison explains most of the
disagreement between published break-even claims, and it has a direct practical
consequence: self-hosting is competitive only under sustained concurrent load. A bursty
or low-traffic workload never gets near the throughput that makes the economics work,
and pays for an idle GPU in the meantime.

## What is missing

There is no clean, stated-batch-size, full-precision throughput figure for a 70B-class
model on a single H100 or A100 — the single most useful data point for this comparison
does not appear to exist in a citable form. Its absence is recorded here rather than
papered over with an estimate.

## What was rejected

A figure of "16,200 tokens/sec with SGLang versus 12,500 with vLLM on an H100" is widely
repeated online. It traces only to content-farm pages with no disclosed methodology, no
batch size and no reproducible setup. It is excluded entirely rather than included with
a caveat, because a number that specific lends false precision to anything it touches.

## Trust ratings

The quality column reflects both the source and the disclosure:

- **Strong** — official project or vendor benchmark with methodology published.
- **Moderate** — smaller or individual source, but batch size and conditions fully disclosed. Disclosure counts for more here than the publisher's size.
- **Weak as a planning number** — reputable source, but a critical parameter such as batch size is missing, so it cannot be transferred to your own workload.

## Not measured here

Every row is someone else's measurement, cited with a link. TandemNest has not
reproduced any of them and does not imply otherwise. A first-hand measurement with a
published harness is listed in the [experiment log](/about/experiments/) as planned
work.

Licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); the underlying
measurements belong to their original authors, linked per row.
