#!/usr/bin/env python3
"""TandemNest static site build.

Usage:
    python3 scripts/build.py            build into public/
    python3 scripts/build.py --check    build, then validate the output
    python3 scripts/build.py --quiet    build with less output

Pure standard library: Cloudflare Pages and GitHub Actions need no install
step. Output is deterministic, so an unchanged source tree produces a
byte-identical site.
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from tnbuild import checks, site  # noqa: E402
from tnbuild.yamlish import YamlishError, parse_file  # noqa: E402

RED, YELLOW, GREEN, DIM, RESET = "\033[31m", "\033[33m", "\033[32m", "\033[2m", "\033[0m"


def fail(message: str) -> "NoReturn":  # type: ignore[valid-type]
    print(f"{RED}build failed{RESET}: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the TandemNest static site.")
    parser.add_argument("--check", action="store_true", help="validate the generated output")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    def log(message: str) -> None:
        if not args.quiet:
            print(message)

    try:
        cfg = parse_file(ROOT / "config.yaml")
    except YamlishError as exc:
        fail(str(exc))

    for section in ("site", "build"):
        if section not in cfg:
            fail(f"config.yaml is missing the '{section}' section")
    for key in ("name", "url", "description"):
        if not cfg["site"].get(key):
            fail(f"config.yaml: site.{key} must be set")
    if not cfg["site"]["url"].startswith("https://"):
        fail("config.yaml: site.url must be an https:// URL")

    out = ROOT / cfg["build"].get("output_dir", "public")
    strict = bool(cfg["build"].get("strict", True))
    base_url = cfg["site"]["url"].rstrip("/")

    # 1. Never publish an unverifiable receiving address.
    try:
        address_info = site.validate_addresses(cfg)
    except site.ContentError as exc:
        fail(str(exc))
    for key, info in address_info.items():
        if info:
            log(f"  {GREEN}verified{RESET} {key} address: {info['asset']} {info['network']} {info['format']}")
        else:
            log(f"  {DIM}no {key} address configured; the page will say so{RESET}")

    # 2. Never publish a secret.
    source_problems = checks.scan_tree_for_secrets(ROOT / "content") \
        + checks.scan_secrets((ROOT / "config.yaml").read_text(encoding="utf-8"), "config.yaml")
    if source_problems:
        for problem in source_problems:
            print(f"{RED}{problem}{RESET}", file=sys.stderr)
        fail("possible secrets found in source; nothing was written")

    # 3. Load content.
    try:
        datasets = site.load_datasets(ROOT / "data")
        pages = site.load_pages(ROOT / "content")
    except (site.ContentError, YamlishError) as exc:
        fail(str(exc))

    if not pages:
        fail("no content pages found under content/")

    slugs: dict[str, pathlib.Path] = {}
    for page in pages:
        if page.slug in slugs:
            fail(f"duplicate slug {page.slug!r} in {page.source} and {slugs[page.slug]}")
        slugs[page.slug] = page.source
    if "" not in slugs:
        fail("no home page: one content file must set 'slug: \"\"'")

    # 4. Render.
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    template = (ROOT / "templates" / "page.html").read_text(encoding="utf-8")
    renderer = site.Renderer(cfg, datasets, pages, address_info)

    for page in pages:
        try:
            rendered = renderer.render(page, template)
        except site.ContentError as exc:
            fail(str(exc))
        dest = out / page.out_file
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(rendered, encoding="utf-8")

    site.copy_static(ROOT / "static", out)
    site.write_datasets(out, cfg, datasets)
    site.write_robots(out, cfg)
    site.write_sitemap(out, cfg, pages)
    site.write_llms_txt(out, cfg, pages)
    site.write_agent_index(out, cfg, pages, datasets)
    site.write_feed(out, cfg, pages)
    site.write_headers(out)

    # 5. The private task file must never reach the output.
    for name in checks.PRIVATE_FILES:
        for stray in out.rglob(name):
            stray.unlink()
            fail(f"{name!r} was found in the build output and removed; it must never be published")

    log(f"{GREEN}built{RESET} {len(pages)} pages and {len(datasets)} datasets into {out.relative_to(ROOT)}/")

    if not args.check:
        return 0

    problems = checks.check_output(out, base_url)
    errors = [p for p in problems if p.level == "error"]
    warnings = [p for p in problems if p.level == "warning"]
    for problem in problems:
        colour = RED if problem.level == "error" else YELLOW
        print(f"{colour}{problem}{RESET}", file=sys.stderr)
    if errors:
        fail(f"{len(errors)} error(s) in generated output")
    if warnings and strict:
        fail(f"{len(warnings)} warning(s) and build.strict is true")
    log(f"{GREEN}checks passed{RESET}: {len(list(out.rglob('*.html')))} HTML files validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
