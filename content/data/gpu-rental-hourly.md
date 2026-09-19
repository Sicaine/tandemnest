---
title: "Dataset: GPU rental prices"
slug: "data/gpu-rental-hourly"
type: "article"
topic: "Data"
order: 51
description: "On-demand hourly GPU rental prices across nine providers, observed 19 September 2026, published as JSON and CSV with a source URL per row."
published: "2026-09-19"
updated: "2026-09-19"
verified: "2026-09-19"
datasets:
  - "gpu-rental-hourly"
summary: |
  Advertised on-demand price for a single GPU-hour across nine providers, read from each
  provider's own pricing page on 19 September 2026. Available as JSON and CSV. Prices
  are per GPU, not per instance, and marketplace listings are recorded as ranges.
---

# Dataset: GPU rental prices

{{summary}}

{{dataset:gpu-rental-hourly}}

## Reading this correctly

**Per GPU, not per instance.** Several providers sell only multi-GPU machines. Where a
figure was derived by dividing an instance price by its GPU count, the tier column says
so — the AWS row is the clearest example.

**Not all hours are the same product.** A RunPod Community Cloud H100 at $2.69 and a
Replicate H100 at $5.49 are not the same purchase. One is a machine you operate
yourself on community-supplied hardware; the other is a managed endpoint with the
operational work removed. The price gap is largely that difference.

**Marketplace rows are ranges.** Vast.ai is a marketplace, so there is no list price.
Those rows record the median of live listings at the observation time with the spread in
the tier column — the RTX 4090 listings ranged from $0.14 to $2.70 per hour on the same
day. Treat them as an indication of where the market sat, not as a quote.

**Storage is not included, and stopped is not free.** RunPod bills volume storage at
$0.10 per GB per month while running and $0.20 per GB per month while stopped. Keeping a
large checkpoint on disk between runs carries a standing cost that does not appear in
any hourly rate.

## Why some providers are absent

**Hetzner** has no hourly GPU cloud. Its GPU machines are monthly dedicated servers,
which is a different product and would be misleading in an hourly table.

**Google Cloud and Azure** publish H100 pricing through JavaScript-rendered calculators
that could not be read reliably from a primary source. Rather than copy their numbers
from a third-party aggregator, they are omitted; AWS serves as the hyperscaler anchor
because its machine-readable price list could be verified directly.

## Confidence

The confidence column is per row, not decorative:

- **high** — read directly from the provider's own pricing page and independently re-checked.
- **high, derived** — the source figure is solid, but the per-GPU number is our own arithmetic on an instance price.
- **medium** — read from the provider's own page in a single pass, not independently re-checked.
- **low, marketplace** — a snapshot of a live marketplace that will have moved by the time you read this.

## Using it

```bash
curl -s https://tandemnest.com/data/gpu-rental-hourly.csv
curl -s https://tandemnest.com/data/gpu-rental-hourly.json | jq '.rows | sort_by(.usd_per_hour)'
```

To turn these into a cost per token, use the
[break-even calculator](/compute/gpu-rental-vs-inference-api/) — the hourly price alone
does not determine cost per token, and the conversion is where most comparisons go
wrong.

Licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Please keep the
observation date attached when you quote a figure.
