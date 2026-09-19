---
title: "How AI agents actually pay for things"
slug: "crypto/agent-payments"
type: "article"
topic: "Crypto"
order: 33
description: "A maturity assessment of x402, L402, AP2 and ACP: which agent payment protocols run in production today, what each one requires, and why a fully static site cannot accept any of them."
published: "2026-09-19"
updated: "2026-09-19"
verified: "2026-09-19"
summary: |
  Four serious protocols now exist for letting software pay software: **x402**
  (stablecoin over HTTP 402), **L402** (Lightning over HTTP 402), **AP2** (Google's
  authorisation mandates) and **ACP** (Stripe and OpenAI's card-rail checkout). Only
  x402 and L402 are running payment traffic today; AP2 and ACP are authorisation
  frameworks with partner ecosystems rather than rails you can point at a URL.
  The finding most people want and rarely get stated: **every one of them needs a
  server.** A purely static site cannot sell anything through any of these, because
  something must issue the 402 challenge and verify the payment before serving content.
sources:
  - title: "x402 protocol"
    publisher: "Coinbase / x402 Foundation"
    url: "https://github.com/coinbase/x402"
    accessed: "2026-09-19"
  - title: "x402.org"
    publisher: "x402 Foundation"
    url: "https://x402.org/"
    accessed: "2026-09-19"
  - title: "L402 protocol"
    publisher: "Lightning Labs"
    url: "https://github.com/lightninglabs/L402"
    accessed: "2026-09-19"
  - title: "L402 documentation"
    publisher: "Lightning Labs"
    url: "https://docs.lightning.engineering/the-lightning-network/l402"
    accessed: "2026-09-19"
  - title: "Announcing the Agent Payments Protocol (AP2)"
    publisher: "Google Cloud"
    url: "https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol"
    accessed: "2026-09-19"
  - title: "Agentic Commerce Protocol"
    publisher: "Stripe"
    url: "https://docs.stripe.com/agentic-commerce/acp"
    accessed: "2026-09-19"
  - title: "AgentKit"
    publisher: "Coinbase"
    url: "https://github.com/coinbase/agentkit"
    accessed: "2026-09-19"
  - title: "Model Context Protocol"
    publisher: "Anthropic"
    url: "https://www.anthropic.com/news/model-context-protocol"
    accessed: "2026-09-19"
---

# How AI agents actually pay for things

{{summary}}

{{toc}}

## The comparison

Table: Agent payment protocols, assessed 2026-09-19
| Protocol | Backed by | Rail | Maturity | Works on a static site? |
| --- | --- | --- | --- | --- |
| **x402** | Coinbase, Cloudflare; spec donated to the Linux Foundation | Stablecoin (USDC) on Base, Solana and others | Live, carrying real transaction volume | No — needs a server or worker to issue and verify |
| **L402** | Lightning Labs | Bitcoin Lightning plus macaroons | Live since around 2020, narrow adoption | No — needs a Lightning node and a proxy |
| **AP2** | Google, with a large partner list | Rail-agnostic authorisation layer | Specification and partner ecosystem | Not applicable — it authorises, it does not settle |
| **ACP** | Stripe with OpenAI; Shopify, Etsy | Card rails through Stripe | Live for merchants on Stripe | No — needs a Stripe merchant backend |

## What each one actually is

### x402 — the one with real traffic

x402 revives HTTP status code 402 "Payment Required", which has sat unused in the spec
since 1997. The flow is genuinely simple: a client requests a resource, the server
responds `402` with machine-readable payment instructions, the client signs a stablecoin
payment, and retries the request with proof attached. The server verifies and serves.

It suits agents well because there is no account, no API key issuance, no subscription
and no human in the loop — which is exactly the friction that makes conventional
payments unusable for software buying small amounts of something.

The reference implementation is server-side middleware with adapters for the usual
frameworks. That is the constraint: x402 is a *server* protocol. A static host serving
files cannot return a conditional 402, cannot verify a payment proof, and cannot gate a
response.

### L402 — older, narrower, still running

L402 combines Lightning invoices with macaroons, also over HTTP 402. It predates the
current agent-payments wave by years and has a working reference implementation in
Lightning Labs' Aperture reverse proxy.

It needs strictly more infrastructure than x402: a Lightning node with channels and
liquidity, plus a proxy to mint macaroons and verify preimages. For a small publisher
that is a real operational burden, and running a node is not a static-site activity by
any definition.

### AP2 — an authorisation layer, not a rail

Google's Agent Payments Protocol addresses a different question: not *how* money moves,
but how an agent proves it was authorised to spend it. It defines cryptographically
signed mandates — an Intent Mandate for what the user asked for, a Cart Mandate for what
is actually being bought — so a merchant can verify that an agent had permission.

That is a real problem worth solving, and it is orthogonal to x402 and L402 rather than
competing with them. But AP2 does not give you an endpoint that accepts money. Reading
it as "a payment rail we could accept" is a category error.

### ACP — card rails, not crypto

The Agentic Commerce Protocol from Stripe and OpenAI lets agents drive a checkout using
shared payment tokens, with Shopify and Etsy among the early adopters. It is a serious
piece of infrastructure for agent-driven retail.

It is also conventional card payments, requiring a Stripe merchant account and a
backend integration. Relevant if you sell products; not relevant to accepting a small
payment for a dataset.

### What MCP does not do

Anthropic's Model Context Protocol comes up constantly in this conversation and does not
belong in it. MCP is a transport for tool calls. It contains no payment primitive and
moves no money. Payment protocols are being layered alongside it by third parties, but
MCP itself is not one.

## The conclusion a static site has to accept

Every protocol above requires a server that can inspect a request, decide it has not
been paid for, return a challenge, verify a payment, and only then serve content.
Static file hosting does none of those things by definition.

The cheapest honest path is a single edge function — a Cloudflare Worker or equivalent —
in front of otherwise-static content. That is a real backend, however small, and it
carries real obligations: keys to hold, failures to handle, and a service that can now
break in ways a file server cannot.

So this site has not built one. The deciding argument is not technical difficulty, it is
demand: there is currently no paid resource here that anyone has asked to buy. Building
payment infrastructure before there is something to sell means maintaining a liability
that earns nothing. If that changes, the protocol to reach for first is x402, because it
has the lowest integration cost and the least infrastructure behind it.

## What a static site can genuinely do

- **Publish a receiving address** for voluntary support. Zero infrastructure, and it works. Realistic revenue at low traffic is approximately nothing, which is worth saying plainly rather than dressing up.
- **Give away the data** and let the usefulness compound. Every dataset here is free JSON and CSV.
- **Link out to paid things elsewhere**, disclosed, with the transaction happening on someone else's infrastructure.

What a static site cannot do is meter, gate or charge. Any guide claiming otherwise is
describing a setup with a server in it that has not been mentioned.

## An honest note on the economics

The payment mechanism is almost never what blocks a small technical site from earning
money. Traffic and trust are. It is far more tempting to spend a weekend integrating a
payment protocol than to spend it producing something worth paying for, because the
first has a clear finish line. The order that works is the other way round.

{{sources}}
