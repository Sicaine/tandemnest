"""Minimal pure-Python QR code encoder that emits inline SVG.

Why this exists: the crypto pages need a scannable receiving address. Using a
third-party QR image service would leak every visitor's page view to that
service and add a network dependency to a static site; shipping a binary PNG
would be opaque. A few hundred lines of stdlib Python gives us deterministic,
inline, themeable SVG instead.

Scope: byte mode, error-correction level L, versions 1-10 (up to 271 bytes).
That covers every cryptocurrency address and BIP-21 style URI we publish.
Anything longer raises, rather than silently truncating.

Spec reference: ISO/IEC 18004. Implementation cross-checked against
``qrencode`` and the ``qrcode`` Python package during development.
"""

from __future__ import annotations

__all__ = ["encode", "svg", "QRError"]


class QRError(ValueError):
    """Raised when the payload cannot be encoded within the supported range."""


# (ec_codewords_per_block, [(block_count, data_codewords_per_block), ...]) for level L
_EC_TABLE_L = {
    1: (7, [(1, 19)]),
    2: (10, [(1, 34)]),
    3: (15, [(1, 55)]),
    4: (20, [(1, 80)]),
    5: (26, [(1, 108)]),
    6: (18, [(2, 68)]),
    7: (20, [(2, 78)]),
    8: (24, [(2, 97)]),
    9: (30, [(2, 116)]),
    10: (18, [(2, 68), (2, 69)]),
}

_ALIGNMENT = {
    1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30],
    6: [6, 34], 7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50],
}

_ECL_L_BITS = 0b01  # error correction level L, as encoded in the format string


# --------------------------------------------------------------------------
# GF(256) arithmetic for Reed-Solomon
# --------------------------------------------------------------------------

_EXP = [0] * 512
_LOG = [0] * 256
_x = 1
for _i in range(255):
    _EXP[_i] = _x
    _LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= 0x11D
for _i in range(255, 512):
    _EXP[_i] = _EXP[_i - 255]


def _gf_mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return _EXP[_LOG[a] + _LOG[b]]


_GENERATOR_CACHE: dict[int, list[int]] = {}


def _rs_divisor(degree: int) -> list[int]:
    """Reed-Solomon generator polynomial, shaped for synthetic division.

    Builds ``(x - a^0)(x - a^1)...(x - a^(degree-1))`` with coefficients in
    ascending order, then returns them in descending order with the leading
    ``1`` dropped -- the form the remainder loop below consumes.
    """
    cached = _GENERATOR_CACHE.get(degree)
    if cached is not None:
        return cached
    poly = [1]
    for i in range(degree):
        poly.append(0)
        for j in range(len(poly) - 1, 0, -1):
            poly[j] = poly[j - 1] ^ _gf_mul(poly[j], _EXP[i])
        poly[0] = _gf_mul(poly[0], _EXP[i])
    divisor = poly[-2::-1]
    _GENERATOR_CACHE[degree] = divisor
    return divisor


def _rs_remainder(data: list[int], degree: int) -> list[int]:
    """Return the ``degree`` error-correction codewords for ``data``."""
    divisor = _rs_divisor(degree)
    remainder = [0] * degree
    for byte in data:
        factor = byte ^ remainder.pop(0)
        remainder.append(0)
        for i, coef in enumerate(divisor):
            remainder[i] ^= _gf_mul(coef, factor)
    return remainder


def _format_bits(mask: int) -> int:
    data = (_ECL_L_BITS << 3) | mask
    rem = data
    for _ in range(10):
        rem = (rem << 1) ^ (0x537 * ((rem >> 9) & 1))
    return ((data << 10) | rem) ^ 0x5412


def _version_bits(version: int) -> int:
    rem = version
    for _ in range(12):
        rem = (rem << 1) ^ (0x1F25 * ((rem >> 11) & 1))
    return (version << 12) | rem


# --------------------------------------------------------------------------
# Data encoding
# --------------------------------------------------------------------------

def _capacity(version: int) -> int:
    ec_per_block, groups = _EC_TABLE_L[version]
    data_codewords = sum(count * size for count, size in groups)
    count_bits = 8 if version <= 9 else 16
    return data_codewords * 8 - 4 - count_bits


def _choose_version(length_bytes: int) -> int:
    for version in sorted(_EC_TABLE_L):
        if length_bytes * 8 <= _capacity(version):
            return version
    raise QRError(f"payload of {length_bytes} bytes exceeds the supported QR range (version 10, level L)")


def _encode_data(payload: bytes, version: int) -> list[int]:
    ec_per_block, groups = _EC_TABLE_L[version]
    data_codewords = sum(count * size for count, size in groups)
    count_bits = 8 if version <= 9 else 16

    bits: list[int] = []

    def put(value: int, width: int) -> None:
        for i in range(width - 1, -1, -1):
            bits.append((value >> i) & 1)

    put(0b0100, 4)                    # byte mode
    put(len(payload), count_bits)
    for byte in payload:
        put(byte, 8)

    capacity_bits = data_codewords * 8
    put(0, min(4, capacity_bits - len(bits)))   # terminator
    while len(bits) % 8:
        bits.append(0)
    codewords = [int("".join(str(b) for b in bits[i : i + 8]), 2) for i in range(0, len(bits), 8)]
    pad = (0xEC, 0x11)
    added = 0
    while len(codewords) < data_codewords:
        codewords.append(pad[added % 2])
        added += 1
    return codewords


def _interleave(codewords: list[int], version: int) -> list[int]:
    ec_per_block, groups = _EC_TABLE_L[version]
    blocks: list[list[int]] = []
    ec_blocks: list[list[int]] = []
    offset = 0
    for count, size in groups:
        for _ in range(count):
            block = codewords[offset : offset + size]
            offset += size
            blocks.append(block)
            ec_blocks.append(_rs_remainder(block, ec_per_block))
    out: list[int] = []
    for i in range(max(len(b) for b in blocks)):
        for block in blocks:
            if i < len(block):
                out.append(block[i])
    for i in range(ec_per_block):
        for block in ec_blocks:
            out.append(block[i])
    return out


# --------------------------------------------------------------------------
# Matrix construction
# --------------------------------------------------------------------------

def _new_matrix(size: int):
    return [[None] * size for _ in range(size)]


def _place_function_patterns(matrix, version: int) -> None:
    size = len(matrix)

    def finder(row: int, col: int) -> None:
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                r, c = row + dr, col + dc
                if 0 <= r < size and 0 <= c < size:
                    inside = 0 <= dr <= 6 and 0 <= dc <= 6
                    ring = inside and (dr in (0, 6) or dc in (0, 6) or (2 <= dr <= 4 and 2 <= dc <= 4))
                    matrix[r][c] = 1 if ring else 0

    finder(0, 0)
    finder(0, size - 7)
    finder(size - 7, 0)

    for i in range(8, size - 8):
        bit = 1 - (i % 2)
        matrix[6][i] = bit
        matrix[i][6] = bit

    centers = _ALIGNMENT[version]
    for r in centers:
        for c in centers:
            if (r, c) in ((6, 6), (6, size - 7), (size - 7, 6)):
                continue
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    matrix[r + dr][c + dc] = 1 if max(abs(dr), abs(dc)) != 1 else 0

    matrix[size - 8][8] = 1  # dark module

    for i in range(9):          # reserve format information
        if matrix[8][i] is None:
            matrix[8][i] = 0
        if matrix[i][8] is None:
            matrix[i][8] = 0
    for i in range(8):
        if matrix[8][size - 1 - i] is None:
            matrix[8][size - 1 - i] = 0
        if matrix[size - 1 - i][8] is None:
            matrix[size - 1 - i][8] = 0

    if version >= 7:            # reserve version information
        for i in range(6):
            for j in range(3):
                matrix[size - 11 + j][i] = 0
                matrix[i][size - 11 + j] = 0


def _function_mask(version: int, size: int):
    reserved = _new_matrix(size)
    _place_function_patterns(reserved, version)
    return [[cell is not None for cell in row] for row in reserved]


def _place_data(matrix, reserved, bits: list[int]) -> None:
    size = len(matrix)
    index = 0
    upward = True
    col = size - 1
    while col > 0:
        if col == 6:
            col -= 1
        rows = range(size - 1, -1, -1) if upward else range(size)
        for row in rows:
            for c in (col, col - 1):
                if reserved[row][c]:
                    continue
                matrix[row][c] = bits[index] if index < len(bits) else 0
                index += 1
        upward = not upward
        col -= 2


def _mask_condition(mask: int, row: int, col: int) -> bool:
    if mask == 0:
        return (row + col) % 2 == 0
    if mask == 1:
        return row % 2 == 0
    if mask == 2:
        return col % 3 == 0
    if mask == 3:
        return (row + col) % 3 == 0
    if mask == 4:
        return (row // 2 + col // 3) % 2 == 0
    if mask == 5:
        return (row * col) % 2 + (row * col) % 3 == 0
    if mask == 6:
        return ((row * col) % 2 + (row * col) % 3) % 2 == 0
    return ((row + col) % 2 + (row * col) % 3) % 2 == 0


def _apply_mask(matrix, reserved, mask: int):
    size = len(matrix)
    out = [row[:] for row in matrix]
    for r in range(size):
        for c in range(size):
            if not reserved[r][c] and _mask_condition(mask, r, c):
                out[r][c] ^= 1
    return out


def _place_format(matrix, mask: int) -> None:
    """Write both copies of the 15-bit format information.

    Copy 1 runs up column 8 then left along row 8; copy 2 runs up column 8
    from the bottom-left finder and right along row 8 to the top-right finder.
    """
    size = len(matrix)
    bits = _format_bits(mask)

    def bit(i: int) -> int:
        return (bits >> i) & 1

    for i in range(6):
        matrix[i][8] = bit(i)
    matrix[7][8] = bit(6)
    matrix[8][8] = bit(7)
    matrix[8][7] = bit(8)
    for i in range(9, 15):
        matrix[8][14 - i] = bit(i)

    for i in range(8):
        matrix[8][size - 1 - i] = bit(i)
    for i in range(8, 15):
        matrix[size - 15 + i][8] = bit(i)

    matrix[size - 8][8] = 1  # always-dark module


def _place_version(matrix, version: int) -> None:
    if version < 7:
        return
    size = len(matrix)
    bits = _version_bits(version)
    for i in range(18):
        bit = (bits >> i) & 1
        row, col = i // 3, i % 3
        matrix[size - 11 + col][row] = bit
        matrix[row][size - 11 + col] = bit


def _penalty(matrix) -> int:
    size = len(matrix)
    score = 0

    for line in list(matrix) + [list(col) for col in zip(*matrix)]:
        run_value, run_len = line[0], 1
        for cell in line[1:]:
            if cell == run_value:
                run_len += 1
            else:
                if run_len >= 5:
                    score += 3 + (run_len - 5)
                run_value, run_len = cell, 1
        if run_len >= 5:
            score += 3 + (run_len - 5)

    for r in range(size - 1):
        for c in range(size - 1):
            block = {matrix[r][c], matrix[r][c + 1], matrix[r + 1][c], matrix[r + 1][c + 1]}
            if len(block) == 1:
                score += 3

    patterns = ([1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0], [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1])
    for line in list(matrix) + [list(col) for col in zip(*matrix)]:
        for i in range(size - 10):
            window = line[i : i + 11]
            if window in patterns:
                score += 40

    dark = sum(sum(row) for row in matrix)
    percent = dark * 100 / (size * size)
    score += 10 * int(abs(percent - 50) // 5)
    return score


def encode(payload) -> list[list[int]]:
    """Encode ``payload`` and return the QR matrix as rows of 0/1 ints."""
    data = payload.encode("utf-8") if isinstance(payload, str) else bytes(payload)
    version = _choose_version(len(data))
    codewords = _interleave(_encode_data(data, version), version)
    bits = [(byte >> i) & 1 for byte in codewords for i in range(7, -1, -1)]

    size = version * 4 + 17
    reserved = _function_mask(version, size)
    base = _new_matrix(size)
    _place_function_patterns(base, version)
    for r in range(size):
        for c in range(size):
            if base[r][c] is None:
                base[r][c] = 0
    _place_data(base, reserved, bits)

    best, best_score = None, None
    for mask in range(8):
        candidate = _apply_mask(base, reserved, mask)
        _place_format(candidate, mask)
        _place_version(candidate, version)
        score = _penalty(candidate)
        if best_score is None or score < best_score:
            best, best_score = candidate, score
    return best


def svg(payload, *, quiet_zone: int = 4, title: str = "QR code", css_class: str = "qr") -> str:
    """Return an inline, theme-aware SVG string for ``payload``.

    The SVG uses ``currentColor`` for modules on an explicit light background,
    so it stays scannable in both light and dark page themes (scanners need
    dark-on-light contrast, so the background is always light).
    """
    import html as _html

    matrix = encode(payload)
    size = len(matrix)
    total = size + quiet_zone * 2
    path: list[str] = []
    for r, row in enumerate(matrix):
        c = 0
        while c < size:
            if row[c]:
                run = 1
                while c + run < size and row[c + run]:
                    run += 1
                path.append(f"M{c + quiet_zone} {r + quiet_zone}h{run}v1h-{run}z")
                c += run
            else:
                c += 1
    safe_title = _html.escape(title, quote=True)
    return (
        f'<svg class="{css_class}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total} {total}" '
        f'role="img" aria-label="{safe_title}" shape-rendering="crispEdges">'
        f"<title>{safe_title}</title>"
        f'<rect width="{total}" height="{total}" fill="#ffffff"/>'
        f'<path fill="#000000" d="{"".join(path)}"/>'
        "</svg>"
    )
