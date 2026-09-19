"""Unit tests for the TandemNest build toolchain. Standard library only.

Run with:  make test   (or  python3 -m unittest discover -s tests)
"""

import hashlib
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from tnbuild import crypto_addr, markdown, qr, yamlish  # noqa: E402


class TestYamlish(unittest.TestCase):
    def test_nested_mappings_and_types(self):
        data = yamlish.parse(
            """
site:
  name: "TandemNest"
  port: 8000
  ratio: 1.5
  live: true
  off: false
  empty:
  note: 'it''s fine'
tags: [a, b, "c d"]
"""
        )
        self.assertEqual(data["site"]["name"], "TandemNest")
        self.assertEqual(data["site"]["port"], 8000)
        self.assertEqual(data["site"]["ratio"], 1.5)
        self.assertIs(data["site"]["live"], True)
        self.assertIs(data["site"]["off"], False)
        self.assertIsNone(data["site"]["empty"])
        self.assertEqual(data["site"]["note"], "it's fine")
        self.assertEqual(data["tags"], ["a", "b", "c d"])

    def test_sequence_of_mappings(self):
        data = yamlish.parse(
            """
rows:
  - provider: RunPod
    gpu: H100
    usd_per_hour: 2.99
  - provider: Vast.ai
    gpu: H100
    usd_per_hour: 1.8
"""
        )
        self.assertEqual(len(data["rows"]), 2)
        self.assertEqual(data["rows"][0]["provider"], "RunPod")
        self.assertEqual(data["rows"][1]["usd_per_hour"], 1.8)

    def test_comments_and_hash_inside_quotes(self):
        data = yamlish.parse('a: 1  # trailing\nb: "has # hash"\n')
        self.assertEqual(data["a"], 1)
        self.assertEqual(data["b"], "has # hash")

    def test_block_scalar(self):
        data = yamlish.parse("text: |\n  line one\n  line two\n")
        self.assertEqual(data["text"], "line one\nline two\n")

    def test_duplicate_key_rejected(self):
        with self.assertRaises(yamlish.YamlishError):
            yamlish.parse("a: 1\na: 2\n")

    def test_tab_indentation_rejected(self):
        with self.assertRaises(yamlish.YamlishError):
            yamlish.parse("a:\n\tb: 1\n")

    def test_error_reports_line_number(self):
        with self.assertRaises(yamlish.YamlishError) as ctx:
            yamlish.parse("a: 1\nthis is not yaml\n")
        self.assertIn(":2:", str(ctx.exception))


class TestMarkdown(unittest.TestCase):
    def test_escapes_html_in_text(self):
        out = markdown.render("A <script>alert(1)</script> tag")
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_table_with_caption_and_alignment(self):
        out = markdown.render("Table: Prices\n| A | B |\n| --- | ---: |\n| x | 1 |\n")
        self.assertIn("<caption>Prices</caption>", out)
        self.assertIn('style="text-align:right"', out)
        self.assertIn("<thead>", out)

    def test_nested_list_is_inside_parent_li(self):
        out = markdown.render("- one\n- two\n  - child\n")
        self.assertIn("<li>two\n<ul>", out)
        self.assertNotIn("</li>\n<ul>", out)

    def test_heading_ids_are_stable(self):
        out = markdown.render("## Quick answer\n")
        self.assertIn('<h2 id="quick-answer">', out)
        self.assertEqual(markdown.slugify("What to do (now)"), "what-to-do-now")

    def test_code_block_not_treated_as_markup(self):
        out = markdown.render("```python\n# not a heading\n**not bold**\n```\n")
        self.assertIn("# not a heading", out)
        self.assertNotIn("<strong>", out)

    def test_headings_skips_code_fences(self):
        found = markdown.headings("## Real\n\n```\n## Fake\n```\n")
        self.assertEqual([h[1] for h in found], ["Real"])

    def test_links_and_bare_urls(self):
        out = markdown.render("See [docs](https://example.com/a) and https://example.com/b")
        self.assertIn('<a href="https://example.com/a">docs</a>', out)
        self.assertIn('<a href="https://example.com/b">', out)


class TestBitcoinAddresses(unittest.TestCase):
    """Vectors from BIP-173 and BIP-350."""

    VALID = [
        ("BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4", "P2WPKH (SegWit v0)"),
        ("bc1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3qccfmv3", "P2WSH (SegWit v0)"),
        ("bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0", "P2TR (Taproot)"),
        ("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "P2PKH (legacy)"),
        ("3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy", "P2SH"),
    ]

    INVALID = [
        ("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t5", "bech32 checksum mutated"),
        ("bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqh2y7hd", "v1 signed with bech32 not bech32m"),
        ("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kemeawh", "v0 signed with bech32m not bech32"),
        ("tc1qw508d6qejxtdg4y5r3zarvary0c5xw7kg3g4ty", "wrong human-readable part"),
        ("BC13W508D6QEJXTDG4Y5R3ZARVARY0C5XW7KN40WF2", "invalid witness version"),
        ("bc1rw5uspcuh", "invalid program length"),
        ("bc1zw508d6qejxtdg4y5r3zarvaryvqyzf3du", "non-zero padding bits"),
        ("tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sL5k7", "mixed case"),
        ("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNb", "base58 checksum mutated"),
        ("tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx", "testnet"),
        ("", "empty"),
        ("1A1zP1eP5QGefi2DMPTfTL5SLmv7Div fNa", "contains whitespace"),
    ]

    def test_valid_addresses(self):
        for address, expected_format in self.VALID:
            with self.subTest(address=address):
                info = crypto_addr.validate(address, "btc")
                self.assertEqual(info["asset"], "BTC")
                self.assertEqual(info["network"], "mainnet")
                self.assertEqual(info["format"], expected_format)

    def test_invalid_addresses_rejected(self):
        for address, why in self.INVALID:
            with self.subTest(reason=why):
                with self.assertRaises(crypto_addr.AddressError):
                    crypto_addr.validate(address, "btc")

    def test_wrong_asset_is_rejected(self):
        with self.assertRaises(crypto_addr.AddressError):
            crypto_addr.validate("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "xmr")


class TestMoneroAddresses(unittest.TestCase):
    # The Monero project's own documentation example address.
    VALID = "4AdUndXHHZ6cfufTMvppY6JwXNouMBzSkbLYfpAV5Usx3skxNgYeYTRj5UzqtReoS44qo9mtmXCqY45DJ852K5Jv2684Rge"

    def test_keccak256_known_vectors(self):
        self.assertEqual(
            crypto_addr.keccak256(b"").hex(),
            "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470",
        )
        self.assertEqual(
            crypto_addr.keccak256(b"abc").hex(),
            "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45",
        )

    def test_keccak_is_not_nist_sha3(self):
        self.assertNotEqual(crypto_addr.keccak256(b""), hashlib.sha3_256(b"").digest())

    def test_valid_standard_address(self):
        info = crypto_addr.validate(self.VALID, "xmr")
        self.assertEqual(info["asset"], "XMR")
        self.assertEqual(info["format"], "standard address")

    def test_checksum_mutation_rejected(self):
        broken = self.VALID[:-1] + ("f" if self.VALID[-1] != "f" else "g")
        with self.assertRaises(crypto_addr.AddressError):
            crypto_addr.validate(broken, "xmr")

    def test_wrong_prefix_rejected(self):
        with self.assertRaises(crypto_addr.AddressError):
            crypto_addr.validate("9" + self.VALID[1:], "xmr")


class TestQR(unittest.TestCase):
    """Golden hashes. The matrices were verified by decoding them with OpenCV
    (see docs/experiments.md); these tests lock in that verified behaviour."""

    GOLDEN = {
        "a": "56bb324cb2e86a133cd29ca6f0f5d1cbd8846616406dea144628a3815cc19271",
    }

    @staticmethod
    def digest(payload: str) -> str:
        matrix = qr.encode(payload)
        return hashlib.sha256("\n".join("".join(str(c) for c in row) for row in matrix).encode()).hexdigest()

    def test_sizes_match_expected_versions(self):
        cases = {"a": 21, "x" * 60: 33, "x" * 200: 53, "x" * 271: 57}
        for payload, size in cases.items():
            with self.subTest(length=len(payload)):
                self.assertEqual(len(qr.encode(payload)), size)

    def test_over_capacity_raises(self):
        with self.assertRaises(qr.QRError):
            qr.encode("y" * 272)

    def test_deterministic(self):
        self.assertEqual(self.digest("tandemnest"), self.digest("tandemnest"))

    def test_svg_is_wellformed_and_accessible(self):
        out = qr.svg("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4", title="Bitcoin address")
        self.assertTrue(out.startswith("<svg"))
        self.assertTrue(out.endswith("</svg>"))
        self.assertIn('role="img"', out)
        self.assertIn('aria-label="Bitcoin address"', out)
        self.assertIn("<title>Bitcoin address</title>", out)
        self.assertEqual(out.count("<svg"), 1)

    def test_finder_patterns_present(self):
        matrix = qr.encode("tandemnest")
        size = len(matrix)
        for row, col in ((0, 0), (0, size - 7), (size - 7, 0)):
            with self.subTest(corner=(row, col)):
                self.assertEqual(matrix[row][col], 1)
                self.assertEqual(matrix[row + 1][col + 1], 0)
                self.assertEqual(matrix[row + 3][col + 3], 1)

    def test_golden_matrix_unchanged(self):
        for payload, expected in self.GOLDEN.items():
            with self.subTest(payload=payload):
                self.assertEqual(self.digest(payload), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestSiteRendering(unittest.TestCase):
    """Regression tests for bugs found while building the site."""

    def setUp(self):
        from tnbuild import site as site_mod
        self.site = site_mod
        self.cfg = {
            "site": {"name": "T", "url": "https://example.com", "description": "d",
                     "language": "en", "locale": "en_US"},
            "seo": {"title_suffix": " · T", "default_robots": "index,follow"},
            "disclosure": {"short": "s", "long": "l"},
            "referrals": {
                "demo": {"name": "Demo", "enabled": False, "plain_url": "https://demo.example/",
                         "payout": "none", "payout_kind": "none", "terms": "https://demo.example/terms"},
                "paid": {"name": "Paid", "enabled": True, "url": "https://paid.example/?ref=1",
                         "payout": "3% cash", "payout_kind": "cash", "terms": "https://paid.example/t"},
            },
            "crypto": {"bitcoin": {"enabled": False, "asset": "BTC", "receiving_address": ""}},
        }

    def make(self, body, meta=None):
        import pathlib as _p
        base = {"title": "T", "description": "d", "slug": "x"}
        base.update(meta or {})
        page = self.site.Page(_p.Path("test.md"), base, body)
        renderer = self.site.Renderer(self.cfg, {}, [page], {"bitcoin": None})
        text, blocks = renderer.expand_shortcodes(page.body, page)
        from tnbuild.markdown import render as md
        out = md(text)
        for i, block in enumerate(blocks):
            token = f"@@TNBLOCK{i}@@"
            out = out.replace(f"<p>{token}</p>", block).replace(token, block)
        return out

    def test_component_html_is_not_escaped_by_markdown(self):
        """A tool's <fieldset>/<output> markup must survive the Markdown pass.

        Regression: shortcodes were expanded before rendering, so component
        tags were treated as paragraph text and escaped into visible markup.
        """
        html_out = self.make("{{referral:paid}}")
        self.assertIn('<a class="btn btn--primary"', html_out)
        self.assertNotIn("&lt;a", html_out)
        self.assertNotIn("<p>@@TNBLOCK", html_out)
        self.assertNotIn("@@TNBLOCK", html_out)

    def test_referral_link_is_disclosed_and_nofollowed(self):
        html_out = self.make("{{referral:paid}}")
        self.assertIn('rel="sponsored nofollow noopener"', html_out)
        self.assertIn("referral link", html_out)
        self.assertIn("3% cash", html_out)

    def test_unconfigured_referral_falls_back_to_the_plain_url(self):
        """Every page must stay correct with monetisation switched off."""
        html_out = self.make("{{referral:demo}}")
        self.assertIn("https://demo.example/", html_out)
        self.assertNotIn("sponsored", html_out)
        self.assertIn("no referral", html_out)

    def test_unconfigured_crypto_address_degrades_honestly(self):
        html_out = self.make("{{crypto:bitcoin}}")
        self.assertIn("No public Bitcoin address is published yet", html_out)
        self.assertNotIn("<svg", html_out)

    def test_unknown_shortcode_fails_the_build(self):
        with self.assertRaises(self.site.ContentError):
            self.make("{{nonsense:thing}}")

    def test_bad_date_fails_the_build(self):
        import pathlib as _p
        with self.assertRaises(self.site.ContentError):
            self.site.Page(_p.Path("t.md"),
                           {"title": "T", "description": "d", "slug": "x", "published": "19-09-2026"}, "")
        with self.assertRaises(self.site.ContentError):
            self.site.Page(_p.Path("t.md"),
                           {"title": "T", "description": "d", "slug": "x", "published": "2026-02-31"}, "")

    def test_missing_required_front_matter_fails(self):
        import pathlib as _p
        with self.assertRaises(self.site.ContentError):
            self.site.Page(_p.Path("t.md"), {"title": "T"}, "")

    def test_unverifiable_address_stops_the_build(self):
        cfg = {"crypto": {"bitcoin": {"enabled": True, "asset": "BTC",
                                      "receiving_address": "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t5"}}}
        with self.assertRaises(self.site.ContentError):
            self.site.validate_addresses(cfg)

    def test_valid_address_is_accepted_and_described(self):
        cfg = {"crypto": {"bitcoin": {"enabled": True, "asset": "BTC",
                                      "receiving_address": "bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0"}}}
        info = self.site.validate_addresses(cfg)
        self.assertEqual(info["bitcoin"]["format"], "P2TR (Taproot)")


class TestChecks(unittest.TestCase):
    def test_detects_credential_shapes(self):
        from tnbuild import checks
        for sample in ("sk-proj-abcdefghijklmnopqrstuvwxyz012345",
                       "-----BEGIN OPENSSH PRIVATE KEY-----",
                       "AKIAIOSFODNN7EXAMPLE",
                       "password: correct-horse-battery",
                       "abandon ability able about above absent absorb abstract absurd abuse access accident"):
            with self.subTest(sample=sample[:20]):
                self.assertTrue(checks.scan_secrets(sample, "t"), f"missed: {sample[:24]}")

    def test_does_not_flag_our_own_published_values(self):
        from tnbuild import checks
        clean = [
            "Never share a private key, seed phrase, view key or wallet file with anyone.",
            'receiving_address: "bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0"',
            'receiving_address: "4AdUndXHHZ6cfufTMvppY6JwXNouMBzSkbLYfpAV5Usx3skxNgYeYTRj5UzqtReoS44qo9mtmXCqY45DJ852K5Jv2684Rge"',
            'url: "https://vast.ai/?ref=abc123"',
            "the cat sat on the mat and then it ran away very fast today, ok.",
        ]
        for sample in clean:
            with self.subTest(sample=sample[:28]):
                self.assertEqual(checks.scan_secrets(sample, "t"), [], f"false positive: {sample[:40]}")


class TestReferralResolution(unittest.TestCase):
    """An action names a provider; the build decides the link and the label.

    This keeps content free of hard-coded referral URLs, so switching a
    programme on or off can never leave a page claiming the wrong relationship.
    """

    REFERRALS = {
        "live": {"name": "Live", "enabled": True, "url": "https://live.example/?ref=9",
                 "plain_url": "https://live.example/", "payout": "3% recurring"},
        "off": {"name": "Off", "enabled": False, "url": "",
                "plain_url": "https://off.example/", "payout": "3% recurring"},
    }

    def resolve(self, action):
        from tnbuild.site import resolve_action
        return resolve_action(action, self.REFERRALS)

    def test_enabled_programme_produces_a_disclosed_referral(self):
        out = self.resolve({"id": "a", "referral": "live"})
        self.assertEqual(out["url"], "https://live.example/?ref=9")
        self.assertEqual(out["publisher_relationship"], "referral")
        self.assertEqual(out["publisher_receives"], "3% recurring")

    def test_disabled_programme_falls_back_to_the_plain_url(self):
        out = self.resolve({"id": "a", "referral": "off"})
        self.assertEqual(out["url"], "https://off.example/")
        self.assertEqual(out["publisher_relationship"], "none")
        self.assertNotIn("publisher_receives", out)

    def test_action_without_a_referral_is_untouched(self):
        out = self.resolve({"id": "a", "url": "https://plain.example/"})
        self.assertEqual(out["url"], "https://plain.example/")
        self.assertNotIn("publisher_relationship", out)

    def test_unknown_provider_fails_the_build(self):
        from tnbuild.site import ContentError
        with self.assertRaises(ContentError):
            self.resolve({"id": "a", "referral": "nope"})
