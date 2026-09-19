---
title: "Bitcoin address checker"
slug: "tools/bitcoin-address-check"
type: "tool"
topic: "Tools"
order: 41
description: "Validate a Bitcoin address in your browser: Base58Check, bech32 and bech32m, with an explanation of exactly which rule failed."
published: "2026-09-19"
updated: "2026-09-19"
sources:
  - title: "BIP-173: Base32 address format for native v0-16 witness outputs"
    publisher: "Bitcoin Improvement Proposals"
    url: "https://github.com/bitcoin/bips/blob/master/bip-0173.mediawiki"
    accessed: "2026-09-19"
  - title: "BIP-350: Bech32m format for v1+ witness addresses"
    publisher: "Bitcoin Improvement Proposals"
    url: "https://github.com/bitcoin/bips/blob/master/bip-0350.mediawiki"
    accessed: "2026-09-19"
summary: |
  Paste a Bitcoin mainnet address to check its checksum and format. Everything runs in
  your browser; the address is never transmitted. When an address fails, the tool names
  the specific rule it broke, including the BIP-350 case where a Taproot address carries
  a valid bech32 checksum where bech32m is required.
---

# Bitcoin address checker

{{summary}}

{{tool:bitcoin-address-check}}

## What is being checked

**Addresses starting with 1 or 3** are decoded as Base58Check: 25 bytes made of a
version byte, a 20-byte hash and a four-byte checksum which must equal the first four
bytes of a double SHA-256 over the rest. The version byte must be `0x00` for a legacy
pay-to-public-key-hash address or `0x05` for pay-to-script-hash.

**Addresses starting with bc1** are decoded as bech32 or bech32m. The tool checks the
90-character limit, rejects mixed case, verifies every character is in the bech32
alphabet, confirms the human-readable part is `bc`, validates the checksum against the
scheme required by the witness version, and checks that the witness program has a legal
length.

## The failure this tool exists to explain

BIP-350 changed the bech32 checksum constant for witness version 1 and above from `1` to
`0x2bc830a3`. Witness v0 addresses still use the old constant. The two address types
look identical apart from one character after `bc1`.

The result is a class of bug that produces confidently wrong answers in both directions:
a validator that never learned about BIP-350 rejects every valid Taproot address, and
also *accepts* a corrupted v1 address that happens to carry a valid old-style checksum.

Rather than reporting "invalid checksum", this tool distinguishes the cases. If an
address carries a checksum that is valid under the wrong scheme, it says so explicitly,
because that tells you the address is probably fine and your other software is not.

The **bech32m trap** button above loads exactly that case so you can see the difference.

## What a valid checksum does not tell you

A passing check means the address is well formed and has not been mistyped or corrupted
in transit. That is all.

It does not tell you who controls the address, whether the recipient is who you think,
or whether you should send anything. Address substitution — malware or a compromised
page swapping in an attacker's address — produces a perfectly valid address. Always
confirm the destination through a second channel for any amount you would mind losing.

## Reusing this

The same validation rules run at build time on this site, in Python with no
dependencies, to verify the [published receiving address](/crypto/bitcoin/) on every
build. If you are implementing your own validator, the official test vectors on the
[Bitcoin page](/crypto/bitcoin/) cover both directions of the bech32m mistake and are
the fastest way to find out whether your implementation has the bug.

{{sources}}
