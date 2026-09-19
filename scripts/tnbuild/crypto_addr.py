"""Build-time validation of public cryptocurrency receiving addresses.

A typo in a receiving address publishes money into a black hole, so the build
refuses to ship an address it cannot verify. Everything here is pure standard
library.

Supported:

  * Bitcoin P2PKH ``1...`` and P2SH ``3...``  — Base58Check (BIP-13 era rules)
  * Bitcoin SegWit v0 ``bc1q...``             — bech32   (BIP-173)
  * Bitcoin Taproot / v1+ ``bc1p...``         — bech32m  (BIP-350)
  * Monero standard / integrated / subaddress — Base58 + Keccak-256 checksum

References:
  BIP-173  https://github.com/bitcoin/bips/blob/master/bip-0173.mediawiki
  BIP-350  https://github.com/bitcoin/bips/blob/master/bip-0350.mediawiki
"""

from __future__ import annotations

import hashlib

__all__ = ["validate", "AddressError", "describe"]

B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
BECH32_CONST = 1
BECH32M_CONST = 0x2BC830A3


class AddressError(ValueError):
    """Raised when an address fails structural or checksum validation."""


# --------------------------------------------------------------------------
# Base58 / Base58Check
# --------------------------------------------------------------------------

def _b58_decode_int(text: str) -> int:
    value = 0
    for ch in text:
        idx = B58_ALPHABET.find(ch)
        if idx < 0:
            raise AddressError(f"invalid base58 character {ch!r}")
        value = value * 58 + idx
    return value


def _b58check_decode(text: str) -> bytes:
    if not text:
        raise AddressError("empty address")
    num = _b58_decode_int(text)
    raw = num.to_bytes((num.bit_length() + 7) // 8, "big") if num else b""
    pad = len(text) - len(text.lstrip("1"))
    raw = b"\x00" * pad + raw
    if len(raw) < 5:
        raise AddressError("base58check payload too short")
    payload, checksum = raw[:-4], raw[-4:]
    expected = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if checksum != expected:
        raise AddressError("base58check checksum mismatch")
    return payload


# --------------------------------------------------------------------------
# bech32 / bech32m  (BIP-173 / BIP-350)
# --------------------------------------------------------------------------

def _bech32_polymod(values) -> int:
    generator = (0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3)
    chk = 1
    for value in values:
        top = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ value
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk


def _bech32_hrp_expand(hrp: str) -> list[int]:
    return [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]


def _bech32_decode(address: str) -> tuple[str, list[int], int]:
    if len(address) > 90:
        raise AddressError("bech32 address longer than the 90 character limit")
    if address.lower() != address and address.upper() != address:
        raise AddressError("bech32 address mixes upper and lower case")
    lowered = address.lower()
    pos = lowered.rfind("1")
    if pos < 1 or pos + 7 > len(lowered):
        raise AddressError("bech32 address has no valid separator")
    hrp, data_part = lowered[:pos], lowered[pos + 1 :]
    data = []
    for ch in data_part:
        idx = BECH32_CHARSET.find(ch)
        if idx < 0:
            raise AddressError(f"invalid bech32 character {ch!r}")
        data.append(idx)
    const = _bech32_polymod(_bech32_hrp_expand(hrp) + data)
    return hrp, data[:-6], const


def _convertbits(data, frombits, tobits, pad=True):
    acc = bits = 0
    out = []
    maxv = (1 << tobits) - 1
    for value in data:
        acc = (acc << frombits) | value
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            out.append((acc >> bits) & maxv)
    if pad:
        if bits:
            out.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        raise AddressError("invalid padding in bech32 witness program")
    return out


def _validate_segwit(address: str, hrp_expected: str = "bc") -> dict:
    hrp, data, const = _bech32_decode(address)
    if hrp != hrp_expected:
        raise AddressError(f"unexpected human-readable part {hrp!r} (expected {hrp_expected!r})")
    if not data:
        raise AddressError("bech32 address has no witness version")
    version = data[0]
    if version > 16:
        raise AddressError(f"invalid witness version {version}")
    # BIP-350: v0 uses bech32, v1 and above use bech32m.
    wanted = BECH32_CONST if version == 0 else BECH32M_CONST
    if const != wanted:
        scheme = "bech32" if version == 0 else "bech32m"
        raise AddressError(f"{scheme} checksum mismatch for witness v{version} address")
    program = _convertbits(data[1:], 5, 8, pad=False)
    if not 2 <= len(program) <= 40:
        raise AddressError("witness program must be 2-40 bytes")
    if version == 0 and len(program) not in (20, 32):
        raise AddressError("witness v0 program must be 20 (P2WPKH) or 32 (P2WSH) bytes")
    if version == 1 and len(program) != 32:
        raise AddressError("witness v1 (Taproot) program must be 32 bytes")
    kind = {0: {20: "P2WPKH (SegWit v0)", 32: "P2WSH (SegWit v0)"}.get(len(program), "SegWit v0"),
            1: "P2TR (Taproot)"}.get(version, f"SegWit v{version}")
    return {"asset": "BTC", "network": "mainnet", "format": kind, "witness_version": version}


# --------------------------------------------------------------------------
# Keccak-256 (Monero uses original Keccak padding, not NIST SHA3)
# --------------------------------------------------------------------------

_KECCAK_ROUND_CONSTANTS = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]
_KECCAK_ROTATIONS = [
    [0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56], [27, 20, 39, 8, 14],
]
_MASK = (1 << 64) - 1


def _rotl64(value: int, shift: int) -> int:
    return ((value << shift) | (value >> (64 - shift))) & _MASK


def _keccak_f1600(state: list[list[int]]) -> None:
    for rnd in range(24):
        c = [state[x][0] ^ state[x][1] ^ state[x][2] ^ state[x][3] ^ state[x][4] for x in range(5)]
        d = [c[(x - 1) % 5] ^ _rotl64(c[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                state[x][y] ^= d[x]
        b = [[0] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                b[y][(2 * x + 3 * y) % 5] = _rotl64(state[x][y], _KECCAK_ROTATIONS[x][y])
        for x in range(5):
            for y in range(5):
                state[x][y] = b[x][y] ^ ((~b[(x + 1) % 5][y] & _MASK) & b[(x + 2) % 5][y])
        state[0][0] ^= _KECCAK_ROUND_CONSTANTS[rnd]


def keccak256(data: bytes) -> bytes:
    """Original Keccak-256 (padding byte 0x01), as used by Monero and Ethereum."""
    rate = 136
    state = [[0] * 5 for _ in range(5)]
    padded = bytearray(data)
    padded.append(0x01)
    while len(padded) % rate != 0:
        padded.append(0x00)
    padded[-1] |= 0x80
    for offset in range(0, len(padded), rate):
        block = padded[offset : offset + rate]
        for i in range(rate // 8):
            lane = int.from_bytes(block[i * 8 : i * 8 + 8], "little")
            state[i % 5][i // 5] ^= lane
        _keccak_f1600(state)
    out = bytearray()
    for i in range(4):
        out += state[i % 5][i // 5].to_bytes(8, "little")
    return bytes(out)


# --------------------------------------------------------------------------
# Monero
# --------------------------------------------------------------------------

_XMR_BLOCK_SIZES = {0: 0, 2: 1, 3: 2, 5: 3, 6: 4, 7: 5, 9: 6, 10: 7, 11: 8}
_XMR_PREFIXES = {
    18: ("standard address", 95),
    19: ("integrated address", 106),
    42: ("subaddress", 95),
}


def _xmr_b58_decode(text: str) -> bytes:
    out = bytearray()
    for offset in range(0, len(text), 11):
        chunk = text[offset : offset + 11]
        size = _XMR_BLOCK_SIZES.get(len(chunk))
        if size is None:
            raise AddressError(f"invalid Monero base58 block length {len(chunk)}")
        value = _b58_decode_int(chunk)
        if value >= 1 << (8 * size):
            raise AddressError("Monero base58 block overflows its byte width")
        out += value.to_bytes(size, "big")
    return bytes(out)


def _read_varint(data: bytes) -> tuple[int, int]:
    value = shift = index = 0
    while index < len(data):
        byte = data[index]
        value |= (byte & 0x7F) << shift
        index += 1
        if not byte & 0x80:
            return value, index
        shift += 7
    raise AddressError("truncated varint prefix")


def _validate_monero(address: str) -> dict:
    raw = _xmr_b58_decode(address)
    if len(raw) < 5:
        raise AddressError("Monero address too short")
    payload, checksum = raw[:-4], raw[-4:]
    if keccak256(payload)[:4] != checksum:
        raise AddressError("Monero Keccak-256 checksum mismatch")
    prefix, _ = _read_varint(payload)
    if prefix not in _XMR_PREFIXES:
        raise AddressError(f"unknown Monero network prefix {prefix} (not a mainnet address)")
    kind, expected_len = _XMR_PREFIXES[prefix]
    if len(address) != expected_len:
        raise AddressError(f"Monero {kind} should be {expected_len} characters, got {len(address)}")
    return {"asset": "XMR", "network": "mainnet", "format": kind, "witness_version": None}


# --------------------------------------------------------------------------
# Public entry point
# --------------------------------------------------------------------------

def validate(address: str, asset: str) -> dict:
    """Validate ``address`` for ``asset`` ("btc" or "xmr").

    Returns a metadata dict on success and raises :class:`AddressError`
    otherwise. Never infers the asset from the prefix alone: the caller states
    which asset it configured, and the address must match it.
    """
    address = (address or "").strip()
    asset = asset.lower()
    if not address:
        raise AddressError("address is empty")
    if any(ch.isspace() for ch in address):
        raise AddressError("address contains whitespace")

    if asset == "btc":
        if address[:1] in "13":
            payload = _b58check_decode(address)
            if len(payload) != 21:
                raise AddressError("base58 Bitcoin payload must be 21 bytes")
            version = payload[0]
            if version == 0x00:
                fmt = "P2PKH (legacy)"
            elif version == 0x05:
                fmt = "P2SH"
            else:
                raise AddressError(f"version byte {version:#04x} is not a Bitcoin mainnet address")
            return {"asset": "BTC", "network": "mainnet", "format": fmt, "witness_version": None}
        if address.lower().startswith("bc1"):
            return _validate_segwit(address)
        if address.lower().startswith(("tb1", "bcrt1")) or address[:1] in "mn2":
            raise AddressError("this looks like a testnet/regtest address; mainnet is required")
        raise AddressError("unrecognised Bitcoin address format")

    if asset == "xmr":
        if address[:1] not in "48":
            raise AddressError("Monero mainnet addresses start with 4 or 8")
        return _validate_monero(address)

    raise AddressError(f"unsupported asset {asset!r}")


def describe(address: str, asset: str) -> str:
    """Human-readable one-line description, for build logs and page copy."""
    info = validate(address, asset)
    return f"{info['asset']} {info['network']} {info['format']}"
