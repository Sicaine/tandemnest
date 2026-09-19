"""Build toolchain for the TandemNest static site.

Standard library only, by design: Cloudflare Pages and GitHub Actions both run
the build with no install step, and the output is deterministic.

    yamlish      strict YAML-subset parser that fails loudly
    markdown     Markdown to semantic HTML, with tables and stable heading ids
    qr           pure-Python QR encoder emitting inline SVG
    crypto_addr  Bitcoin and Monero address validation, including Keccak-256
    components   shortcodes and reusable page furniture
    site         content model, rendering, and generated machine-readable files
    checks       secret scanning and output validation
"""

__all__ = ["yamlish", "markdown", "qr", "crypto_addr", "components", "site", "checks"]
