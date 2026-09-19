---
title: "Monero receiving address"
slug: "crypto/monero"
type: "article"
topic: "Crypto"
order: 32
description: "TandemNest's public Monero receiving address, and why validating one requires original Keccak-256 rather than the SHA-3 in your standard library."
published: "2026-09-19"
updated: "2026-09-19"
summary: |
  A public Monero receiving address for voluntary support. If you are implementing
  validation: Monero uses original Keccak-256, not NIST SHA-3, so `hashlib.sha3_256`
  will never reproduce the checksum. It also uses a block-based Base58 variant that is
  not interchangeable with Bitcoin's.
sources:
  - title: "Standard address"
    publisher: "Monero documentation"
    url: "https://docs.getmonero.org/public-address/standard-address/"
    accessed: "2026-09-19"
  - title: "Integrated address"
    publisher: "Monero documentation"
    url: "https://docs.getmonero.org/public-address/integrated-address/"
    accessed: "2026-09-19"
  - title: "Subaddress"
    publisher: "Monero documentation"
    url: "https://docs.getmonero.org/public-address/subaddress/"
    accessed: "2026-09-19"
---

# Monero receiving address

{{summary}}

{{crypto:monero}}

{{toc}}

## Why Monero is published alongside Bitcoin

Bitcoin's ledger is public and permanently linkable: anyone with the address above can
see every amount ever sent to it and often connect those payments to each other. Monero
is here so that supporting this site does not require publishing that.

Neither is better; they make different trade-offs, and both addresses are offered so the
choice is yours.

## Address anatomy

A Monero mainnet address is not one opaque string. It decodes to a structure:

| Address type | Leading character | Length | Contents |
| --- | --- | --- | --- |
| Standard | `4` | 95 characters | network byte, public spend key, public view key, checksum |
| Integrated | `4` | 106 characters | as standard, plus an 8-byte payment ID |
| Subaddress | `8` | 95 characters | network byte, spend key, view key, checksum |

The network prefixes are 18 for a standard address, 19 for an integrated address and 42
for a subaddress. The checksum is the first four bytes of a Keccak-256 hash over
everything preceding it.

## The two things that catch implementers

### It is Keccak-256, not SHA-3

Monero's checksum uses **original Keccak-256**, the pre-standardisation version. NIST
changed the padding byte from `0x01` to `0x06` when finalising SHA-3, which produces
completely different digests from identical input.

The practical consequence: `hashlib.sha3_256` in Python, and every other standard
library's SHA-3, will *never* reproduce a Monero checksum. There is no flag to switch.
Validating a Monero address without a dependency means implementing Keccak-f[1600]
yourself, which is why many "validators" check only the length and the leading
character and call it done.

This site's build implements Keccak-256 properly and verifies the address above on every
build, the same way it verifies the Bitcoin address. A quick way to confirm any
implementation is correct: Keccak-256 of the empty string is
`c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470`, which differs
entirely from SHA3-256 of the same input.

### The Base58 variant is not Bitcoin's

Monero uses the same 58-character alphabet as Bitcoin but encodes differently. Bitcoin
treats the whole payload as one big integer. Monero splits it into 8-byte blocks, each
encoded to exactly 11 characters, with a fixed shorter mapping for a final partial
block.

A Bitcoin Base58 decoder pointed at a Monero address produces garbage rather than an
error, so the failure is silent. The two are not interchangeable in either direction.

## Before you send anything

- **Verify the address independently.** Paste it into your wallet and let the wallet check it. Never rely on a single web page for an address.
- **Transactions are irreversible.** There is no recovery path for a payment sent to the wrong address.
- **Never share a view key, spend key, seed phrase or wallet file.** A view key exposes your incoming transaction history; a spend key or seed loses the funds entirely. This site will never ask for any of them.
- **This is a donation address.** It buys nothing and unlocks nothing. Everything here is free to read.

## No mining content, on purpose

This site publishes no Monero mining profitability material. Monero's RandomX proof of
work is designed to run well on ordinary CPUs and to resist GPUs and ASICs, so the
common "rent a cloud GPU and mine XMR" framing is wrong at the premise. Live-difficulty
calculators maintained by others answer the real question better than a static page can,
and volatile-asset profitability projections are not something this site wants to be
responsible for.

{{sources}}
