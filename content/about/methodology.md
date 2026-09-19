---
title: "Methodology"
slug: "about/methodology"
type: "page"
topic: "About"
order: 92
description: "How prices are collected, how dates are recorded, how uncertainty is handled, and what would have to be true for a page here to be wrong."
published: "2026-09-19"
updated: "2026-09-19"
---

# Methodology

{{summary}}

{{toc}}

## Where numbers come from

In descending order of preference:

1. The provider's own published pricing page.
2. The provider's own product or API documentation.
3. The provider's own programme terms, for anything about referral payouts.
4. A primary technical source: a specification, a paper, or a maintained benchmark suite.
5. An independent measurement with a stated method that can be inspected.

Secondary reporting is used only to locate a primary source, never as the source itself.
Provider marketing copy is never reproduced as a finding.

## How dates work

Three dates can appear on a page, and they mean different things:

- **Published** — when the page first went up. It never changes.
- **Updated** — when the page's text last changed meaningfully. Fixing a typo does not move it.
- **Data verified** — when the numbers on the page were last checked against their sources. This is the one that matters for anything price-related.

The publication date is never refreshed to make a page look current. If the data is
three months old, the verification date says three months old, and you can decide what
to do about that. Every dataset also carries its own observation date, independent of
the page that displays it, because the same dataset can appear on more than one page.

## How uncertainty is handled

A number here is presented in one of three ways, and the page always says which:

- **Observed** — copied from a primary source on a stated date. The source is linked per row.
- **Derived** — computed from observed numbers using arithmetic that is printed on the page.
- **Estimated** — a range, with the reason for the range stated.

Throughput figures deserve a specific warning. Tokens per second for a self-hosted model
varies by an order of magnitude depending on batch size, sequence length, quantisation,
serving stack and hardware. Any page that gives you a single confident tokens-per-second
number without those parameters is guessing. Where this site needs such a figure, it is
treated as an input you supply rather than a constant, and the calculators are built so
that you can see how much the answer moves when it changes.

## What is not done

- No page is generated in bulk from a keyword list.
- No metric is invented to create a ranking, and no provider is scored on an unexplained scale.
- No benchmark result is published that was not actually run or actually cited.
- No FAQ or review structured data is emitted, because Google no longer produces rich results from FAQ markup and this site has no genuine reviews to mark up.
- No page claims a measurement was reproduced here when it was not.

## How to check a page

Every data table on this site is also published as JSON and CSV under [`/data/`](/data/),
with a source URL and an observation date per row. To check a conclusion:

1. Download the CSV behind the table.
2. Open the source URL in the row you doubt and compare it against the recorded value.
3. Redo the arithmetic with the formula printed on the page.

If step 2 disagrees with the file, the page is stale or wrong and worth reporting.

## What would make a page here wrong

Stated plainly, because it is the useful thing to know:

- **Prices changed.** The most common failure. Check the verification date first.
- **A provider changed its billing model.** Per-second versus hourly billing changes GPU conclusions more than the headline rate does.
- **The throughput assumption was unrepresentative.** This is the largest source of error in any GPU-versus-API comparison, including the one on this site.
- **A referral programme changed its terms.** The payout descriptions on the [disclosure page](/about/disclosure/) are read from the programme's own terms on a stated date and can go out of date like any other price.
