---
title: "Crypto"
slug: "crypto"
type: "index"
topic: "Crypto"
order: 30
nav: true
description: "Public receiving addresses, how address checksums actually work, and an honest maturity assessment of the payment rails built for autonomous agents."
published: "2026-09-19"
updated: "2026-09-19"
---

# Crypto

Two things live in this section: the public receiving addresses for this site, and
research on how autonomous software can pay and be paid.

<ul class="grid">
<li><a class="tile" href="/crypto/agent-payments/"><strong>How agents pay for things</strong><span>x402, L402, AP2 and ACP sorted by what actually runs in production. Plus the thing none of them can do without a server.</span></a></li>
<li><a class="tile" href="/crypto/bitcoin/"><strong>Bitcoin receiving address</strong><span>The address, plus why bech32 and bech32m use different checksums and how that silently breaks Taproot support.</span></a></li>
<li><a class="tile" href="/crypto/monero/"><strong>Monero receiving address</strong><span>The address, and how its Keccak-256 checksum differs from the SHA-3 in your standard library.</span></a></li>
<li><a class="tile" href="/tools/bitcoin-address-check/"><strong>Address checker</strong><span>Validate a Bitcoin address in your browser. Nothing is transmitted.</span></a></li>
</ul>

## The safety rule that covers all of it

A **receiving address** is public by design. Publishing one is safe; it is what an
address is for.

A **private key**, **seed phrase**, **mnemonic**, **view key**, **spend key** or
**wallet file** is the opposite. Anyone holding one can spend the funds.

TandemNest will never ask for any of the second group, and neither will any legitimate
site, wallet, exchange, support agent or airdrop. There is no situation in which a web
page needs your seed phrase. If something asks, it is stealing from you.

This site also runs no wallet code. There is no browser mining, no wallet connection, no
transaction signing and no JavaScript that touches a wallet extension. The crypto pages
here are text, a QR image generated at build time, and a copy button.

## What is deliberately not here

There is no mining profitability content on this site. Monero's RandomX algorithm is
designed to favour ordinary CPUs and resist GPUs and ASICs, which makes "mine Monero on
a rented cloud GPU" a technically incoherent premise regardless of how often it is
written up. The established calculators driven by live network difficulty answer the
real version of that question far better than a static page could, and profitability
claims tied to a volatile asset price are not something this site wants to publish.

Browser-based mining is also treated as dead rather than as an opportunity: the
blocklists, antivirus signatures and hosting terms built in response to Coinhive-era
cryptojacking are still in force, and they do not distinguish a consent-based miner from
a malicious one. The reasoning is recorded in the [experiment log](/about/experiments/).
