---
title: "Data"
slug: "data"
type: "index"
topic: "Data"
order: 50
nav: true
description: "Every table on this site published as JSON and CSV, with an observation date and a source URL for every row. Free to reuse with attribution."
published: "2026-09-19"
updated: "2026-09-19"
---

# Data

Every table on this site is generated from a dataset file, and every dataset is
published in full as JSON and CSV. Nothing is gated, rate limited, or behind an account.

Each dataset carries an observation date, a written method, and a source URL per row, so
you can check any individual number against its origin rather than trusting the table.

<ul class="grid">
<li><a class="tile" href="/data/gpu-rental-hourly/"><strong>GPU rental prices</strong><span>On-demand hourly price per GPU across nine providers, with tier and confidence noted per row.</span></a></li>
<li><a class="tile" href="/data/inference-api-pricing/"><strong>Inference API prices</strong><span>Per-million-token input and output pricing across the major hosted providers.</span></a></li>
<li><a class="tile" href="/data/self-host-throughput/"><strong>Self-host throughput</strong><span>Cited benchmark figures for open-weight models, with batch size and a trust assessment for each.</span></a></li>
</ul>

## Format

Each dataset is available at two stable URLs:

```text
/data/<name>.json
/data/<name>.csv
```

The JSON carries the full metadata — title, description, observation date, method,
licence, per-column units and the rows. The CSV is the rows alone, for loading straight
into a spreadsheet or a dataframe.

```bash
curl -s https://tandemnest.com/data/gpu-rental-hourly.json | jq '.rows[] | select(.gpu=="H100 SXM")'
```

## Licence and reuse

Published under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Use it,
republish it, build on it; please credit TandemNest and link back so readers can check
the observation date.

If you are quoting a price, **quote the observation date with it**. A GPU price without
a date is close to worthless, and stripping the date is the single most common way this
kind of data gets turned into misinformation.

## Accuracy and what to do about errors

These are hand-collected figures read from provider pricing pages on a stated date.
Prices change without notice, and a price here can be out of date the week after it was
recorded. Confidence is marked per row where it varies, and rows that could not be
verified from a primary source were omitted rather than estimated.

If a figure disagrees with the provider's current page, the provider is right and this
site is stale. Corrections are applied along with a new observation date.

## Provenance is part of the data

Two deliberate choices worth noting:

- **Ranges stay ranges.** Marketplace prices from Vast.ai are recorded as observed medians with their spread, not flattened into a single number that would look more authoritative than it is.
- **Weak data is labelled weak.** The throughput dataset carries a per-row assessment of how much each figure should be trusted, including the rows where the batch size was not disclosed. Publishing that honestly is more useful than quietly dropping it or quietly averaging it in.
