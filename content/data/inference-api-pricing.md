---
title: "Dataset: inference API prices"
slug: "data/inference-api-pricing"
type: "article"
topic: "Data"
order: 52
description: "Per-million-token input and output prices for hosted language model APIs, observed 19 September 2026, as JSON and CSV with a source per row."
published: "2026-09-19"
updated: "2026-09-19"
verified: "2026-09-19"
datasets:
  - "inference-api-pricing"
summary: |
  Published per-token prices for hosted language model APIs, read from each provider's
  own pricing page on 19 September 2026. Input and output are listed separately because
  output typically costs four to five times more and the ratio drives the total.
---

# Dataset: inference API prices

{{summary}}

{{dataset:inference-api-pricing}}

## Reading this correctly

**Output dominates.** Most providers charge four to five times more for output than
input. A workload's input/output ratio therefore affects its bill more than the headline
input price does. Any comparison quoting a single "price per million tokens" without
stating the mix is hiding the most important variable.

**These are list prices.** Excluded, because they all change the effective rate
substantially and none of them are comparable across providers:

- prompt caching discounts, which are large — cached input can be an order of magnitude cheaper
- batch processing discounts
- off-peak pricing, which DeepSeek publishes as a formal two-tier schedule
- negotiated or enterprise pricing
- provider-specific surcharges, such as fast-mode or region-restricted inference multipliers

**Aggregator rows are not first-party.** The OpenRouter row is that aggregator's listed
rate, which routes to third-party hosts and can differ from the model author's own
pricing.

## The range is the finding

The prices in this table span more than two orders of magnitude for the input side
alone. For a large class of tasks, the difference between a flagship model and a small
one is the single largest cost lever available — larger than self-hosting, larger than
switching provider, and free to test.

Worth checking before optimising anything else.

## What was left out

One row was deliberately excluded: Together AI's DeepSeek V4 Flash pricing returned two
materially different figures on two separate reads of the same page on the same day.
Rather than pick one, or average them, it is omitted until it can be resolved. Exclusion
beats publishing a number that might be wrong by 4x.

## Using it

```bash
curl -s https://tandemnest.com/data/inference-api-pricing.json \
  | jq -r '.rows[] | [.provider, .model, .usd_per_m_input, .usd_per_m_output] | @tsv'
```

Licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quote the
observation date with any figure: model pricing changes frequently, and a dateless price
is how stale numbers spread.
