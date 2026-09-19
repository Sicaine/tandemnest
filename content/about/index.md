---
title: "About"
slug: "about"
type: "page"
topic: "About"
order: 90
nav: true
description: "Who runs TandemNest, how its research is produced and checked, and the limits of what a one-person site can verify."
published: "2026-09-19"
updated: "2026-09-19"
---

# About TandemNest

TandemNest is an independent, one-person project. It is not a company, not a research
lab, and not a team. Treating it as any of those would be a mistake, so the pages are
written to let you check them rather than to ask you to trust them.

## What it publishes

Dated cost research on three subjects that change fast enough that most published
answers are quietly wrong:

- **Compute economics** — what GPU time actually costs and when renting beats a hosted API.
- **Inference pricing** — what the model providers charge, tracked with observation dates.
- **Agent payment rails** — how autonomous software can pay and be paid, sorted by real maturity.

## How a page gets made

1. Find a question where the existing answers are vendor-published, undated, or both.
2. Collect the current numbers from primary sources, recording the URL and the date.
3. Do the arithmetic in the open and publish the inputs as JSON and CSV.
4. State plainly what is uncertain, and what would change the conclusion.
5. Publish only if the page would still be worth reading with every referral link removed.

Step 5 removes more page ideas than the other four combined. The
[methodology page](/about/methodology/) describes the rules in more detail, and the
[experiment log](/about/experiments/) records what has been tried and what failed.

## Limits worth knowing

- **Prices move.** A page verified in September may be wrong in November. Check the verification date at the top of every page before relying on a number.
- **Throughput figures are the weakest link.** Comparing GPU rental to per-token API pricing requires a tokens-per-second figure, and published measurements vary enormously with batch size, sequence length and serving stack. Where a page depends on one, it says so and gives a range.
- **Not everything has been measured first-hand.** Where a number comes from someone else's benchmark, the page cites it rather than implying it was reproduced here.
- **No provider relationship confers access.** Referral programmes do not give this site special pricing, early information, or a review copy of anything.

## Contact and corrections

If a number here is wrong, it is worth correcting, and correcting it publicly. Factual
corrections are applied to the page along with a new verification date rather than
quietly edited.

## The crypto addresses

The Bitcoin and Monero addresses published in the [crypto section](/crypto/) are public
receiving addresses controlled by the site's operator. Their checksums are verified
automatically every time the site is built, which is the only guarantee worth making
about an address on a web page. Sending to them is voluntary and buys nothing.

This site will never ask anyone for a private key, a seed phrase, a view key or a wallet
file, and no legitimate site ever will.
