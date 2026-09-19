---
title: "Bitcoin receiving address"
slug: "crypto/bitcoin"
type: "article"
topic: "Crypto"
order: 31
description: "TandemNest's public Bitcoin receiving address, plus a practical explanation of Base58Check, bech32 and the bech32m change that quietly breaks Taproot support."
published: "2026-09-19"
updated: "2026-09-19"
summary: |
  A Bitcoin address is safe to publish; a private key or seed phrase never is. The
  address below is public, and its checksum is re-verified automatically every time this
  site is rebuilt. If you are implementing address validation, the section on bech32
  versus bech32m is the part that catches people: Taproot addresses use a different
  checksum constant, and validators that missed the change accept invalid addresses and
  reject valid ones.
sources:
  - title: "BIP-173: Base32 address format for native v0-16 witness outputs"
    publisher: "Bitcoin Improvement Proposals"
    url: "https://github.com/bitcoin/bips/blob/master/bip-0173.mediawiki"
    accessed: "2026-09-19"
  - title: "BIP-350: Bech32m format for v1+ witness addresses"
    publisher: "Bitcoin Improvement Proposals"
    url: "https://github.com/bitcoin/bips/blob/master/bip-0350.mediawiki"
    accessed: "2026-09-19"
  - title: "Base58Check encoding"
    publisher: "Bitcoin Wiki"
    url: "https://en.bitcoin.it/wiki/Base58Check_encoding"
    accessed: "2026-09-19"
actions:
  - id: "verify_bitcoin_address"
    label: "Check a Bitcoin address before sending to it"
    description: "Validate any Bitcoin address's checksum and format in your browser. Nothing is transmitted or stored."
    url: "https://tandemnest.com/tools/bitcoin-address-check/"
    cost: "free"
    requires_user_authorization: false
    publisher_relationship: "none"
    link_text: "Open the address checker"
---

# Bitcoin receiving address

{{summary}}

{{crypto:bitcoin}}

{{toc}}

## What this address is and is not

It is a public receiving address for voluntary support of the research published here.
Sending to it buys nothing, unlocks nothing, and creates no obligation in either
direction. Nothing on this site is paywalled, so there is nothing to purchase.

It is not an investment, a token sale, a presale, or a yield product, and no service is
being offered in exchange.

## How this address is verified

Publishing a mistyped address means publishing a hole that money falls into, and the
mistake is invisible to a reader. So the address is not simply pasted into a template.
Every time this site is built, the build re-derives the address's checksum and refuses
to produce any output at all if it does not match. A typo breaks the build rather than
the reader's transaction.

That is worth doing because Bitcoin's address formats are specifically designed to make
this check possible, and it costs nothing to actually perform it.

## The three checksum schemes

Bitcoin mainnet addresses come in three families, and each protects itself differently.

### Base58Check: addresses starting with 1 or 3

Legacy pay-to-public-key-hash (`1...`) and pay-to-script-hash (`3...`) addresses encode
25 bytes: a one-byte version, a 20-byte hash, and a four-byte checksum. The checksum is
the first four bytes of a double SHA-256 over the version and hash.

The alphabet omits `0`, `O`, `I` and `l` to reduce transcription errors. A single
mistyped character changes the decoded payload, so the recomputed checksum disagrees and
the address is rejected.

### bech32: addresses starting with bc1q

SegWit v0 addresses use bech32, defined in BIP-173. The checksum is a BCH code over the
human-readable part (`bc`) and the data, validated by checking that a polynomial
remainder equals a fixed constant. For bech32 that constant is **1**.

bech32 is deliberately case-insensitive, and mixing cases within one address is invalid
rather than merely ugly. A witness v0 program must be exactly 20 bytes (pay-to-witness
public key hash) or 32 bytes (pay-to-witness script hash). Any other length is invalid.

### bech32m: addresses starting with bc1p

This is the part that breaks implementations. Taproot arrived with SegWit v1, and
BIP-350 changed the checksum constant for witness versions 1 and above from **1** to
**0x2bc830a3**. Everything else is identical: same alphabet, same polynomial, same
human-readable part, same visual appearance.

The rule is exact:

- Witness version **0** must use bech32, constant **1**.
- Witness versions **1 through 16** must use bech32m, constant **0x2bc830a3**.

A validator that never learned about BIP-350 will therefore reject every valid Taproot
address, and, worse, accept a v1 address that was checksummed with the old scheme —
which is precisely the corrupted case the checksum exists to catch. Both directions are
real failures, and BIP-350 publishes test vectors for each.

## Test vectors worth using

If you are writing a validator, these are the cases that matter. The first three must be
accepted, the rest must be rejected.

| Address | Expected result |
| --- | --- |
| `BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4` | Valid, witness v0, 20-byte program |
| `bc1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3qccfmv3` | Valid, witness v0, 32-byte program |
| `bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0` | Valid, witness v1 Taproot, bech32m |
| `bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqh2y7hd` | Invalid: v1 signed with bech32, not bech32m |
| `bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kemeawh` | Invalid: v0 signed with bech32m, not bech32 |
| `bc1rw5uspcuh` | Invalid: witness v3 carrying a bech32 checksum, and a program length out of range |
| `bc1zw508d6qejxtdg4y5r3zarvaryvqyzf3du` | Invalid: non-zero padding bits |
| `tc1qw508d6qejxtdg4y5r3zarvary0c5xw7kg3g4ty` | Invalid: wrong human-readable part |

The [address checker](/tools/bitcoin-address-check/) on this site implements all of the
above and runs entirely in your browser.

## Before you send anything

- **Check the checksum yourself.** Paste the address into the [checker](/tools/bitcoin-address-check/), or any wallet, before sending. Do not trust a web page — including this one — as the sole source of an address.
- **Bitcoin transactions do not reverse.** An address sent to in error is gone. There is no support queue.
- **Only send from a wallet you control.** Sending from an exchange account you do not hold the keys to introduces the exchange's rules into a transaction that does not need them.
- **Amounts are public.** Bitcoin's ledger is public and permanently linkable. If that matters to you, [Monero](/crypto/monero/) is the alternative published here.

{{actions}}

{{sources}}
